import importlib
import json

import pytest

from epistemics.investigation2.service import digest, encoded
from epistemics.passport.build import build_passport, verify_derivation
from epistemics.passport.investigation import bundle, derive
from epistemics.passport.models import read_passport
from epistemics.passport.render import render_html, render_markdown


@pytest.fixture(scope="module", params=[2, 3])
def collection(request, tmp_path_factory):
    prefix = f"epistemics.investigation{request.param}"
    service = importlib.import_module(prefix + ".service")
    simulation = importlib.import_module(prefix + ".simulation")
    models = importlib.import_module(prefix + ".models")
    root = tmp_path_factory.mktemp("investigation-passport") / "collection"
    participant = {
        "kind": "agent",
        "subject_id": "synthetic:test",
        "configuration": {
            "model": "analytic",
            "model_version": "test",
            "configuration_sha256": "0" * 64,
        },
    }
    manifest = service.create(root, participant, seed=23, synthetic=True)
    for a in manifest.assignments:
        s = service.InvestigationService(root, a.assignment_id)
        while not (current := s.get_trial())["complete"]:
            trial = models.Trial.model_validate(current["trial"])
            s.submit(trial.trial_id, simulation.response(trial))
        s.finish()
    service.export(root)
    return root


def test_collection_to_readable_and_machine_passport_preserves_original_bytes(collection):
    before = {p.name: p.read_bytes() for p in (collection / "reports").glob("*.json")}
    source = bundle(collection)
    raw = encoded(source)
    p = build_passport(raw)
    assert p.context.response_origin == "synthetic"
    assert p.context.conditions.interface == "unspecified"
    assert p.evaluation_mode == "discovery"
    assert p.source.sha256 == digest(raw)
    assert p.coverage["unique_worlds"] == 9
    assert source.facts["decision_agreement_percent"] == 100
    assert p.model_diagnostics.parameters_are_validated_traits is False
    assert not p.support_candidates
    verify_derivation(p, raw)
    assert read_passport(p.model_dump_json().encode()) == p
    assert "Model explanations" in render_markdown(p)
    assert "development only" in render_html(p)
    assert before == {q.name: q.read_bytes() for q in (collection / "reports").glob("*.json")}
    with pytest.raises(ValueError, match="cannot be relabeled"):
        build_passport(raw, response_origin="agent")


def test_rejects_tampered_facts_mixed_cases_and_changed_source_bytes(collection):
    source = bundle(collection)
    changed = source.model_copy(deep=True)
    changed.facts["decision_agreement_percent"] = 12
    with pytest.raises(ValueError, match="differ"):
        build_passport(encoded(changed))
    wrong = list(source.cases)
    wrong[1] = wrong[0]
    with pytest.raises(ValueError, match="Mixed"):
        derive(wrong)
    data = json.loads(encoded(source))
    data["cases"][0]["report_json"] += " "
    with pytest.raises(ValueError, match="hash"):
        build_passport(encoded(data))
    p = build_passport(encoded(source))
    with pytest.raises(ValueError, match="digest"):
        verify_derivation(p, encoded(source) + b" ")


def test_inadequate_fit_cannot_become_validated_trait_or_consumer_metric(collection):
    p = build_passport(encoded(bundle(collection)))
    assert all(
        "/model_diagnostics" not in r.json_pointer
        for d in p.dimensions
        for m in d.measurements
        for r in m.evidence
    )
    changed = p.model_dump(mode="json")
    changed["model_diagnostics"]["parameters_are_validated_traits"] = True
    with pytest.raises(ValueError):
        read_passport(json.dumps(changed).encode())
