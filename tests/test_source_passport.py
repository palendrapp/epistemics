import json
from pathlib import Path

import pytest

from epistemics.passport.build import build_passport, verify_derivation
from epistemics.passport.models import SourcePassport, read_passport
from epistemics.passport.render import render_html, render_markdown
from epistemics.passport.source_learning import SourceCollection, SourceSession, bundle, derive
from epistemics.source_delivery.simulation import simulate
from epistemics.source_learning.simulation import PARTICIPANT
from epistemics.source_learning.storage import digest, encoded


@pytest.fixture(scope="module")
def collections(tmp_path_factory):
    root = tmp_path_factory.mktemp("source-passports")
    for name, seed, condition, presentation in [
        ("a", 31, "sparse", "structured"),
        ("b", 31, "sparse", "structured"),
        ("dense", 31, "dense", "structured"),
        ("packet", 31, "sparse", "packet"),
    ]:
        simulate(root / name, seed, condition, presentation)
    p = json.loads(json.dumps(PARTICIPANT))
    p["subject_id"] = "synthetic:other-session"
    simulate(root / "cohort", 31, participant=p)
    return root


def test_readable_machine_passport_recomputes_exact_evidence(collections):
    before = (collections / "a/report.json").read_bytes()
    source = bundle([collections / "a", collections / "b"])
    raw = encoded(source)
    p = build_passport(raw)
    assert p.coverage["repeat_pairs"] == 1 and p.coverage["unique_worlds"] == 1
    assert source.facts["repeat_rmse_pp"] == 0
    assert p.context.response_origin == "synthetic"
    assert p.presentation == "structured" and p.condition == "sparse"
    assert p.subject_binding == "single_subject"
    verify_derivation(p, raw)
    assert read_passport(p.model_dump_json().encode()) == p
    assert "Matched repeats" in render_html(p) and "Matched repeats" in render_markdown(p)
    assert "Model explanations" in render_markdown(p)
    assert "One run;" not in render_html(p)
    assert "sessions [1, 2]" in render_html(p)
    assert "design_seed" not in p.model_dump_json()
    assert (collections / "a/report.json").read_bytes() == before
    with pytest.raises(ValueError, match="cannot be relabeled"):
        build_passport(raw, response_origin="agent")
    with pytest.raises(ValueError, match="digest"):
        verify_derivation(p, raw + b" ")


def test_single_run_has_missing_repeatability_not_perfect_score(collections):
    s = bundle([collections / "a"])
    p = build_passport(encoded(s))
    assert s.facts["repeat_rmse_pp"] is None and p.coverage["repeat_pairs"] == 0
    assert not any(
        m.evidence[0].json_pointer == "/facts/repeat_rmse_pp"
        for d in p.dimensions
        for m in d.measurements
    )
    assert "repeatability is unmeasured" in render_html(p)


def test_cohort_identity_is_explicit_and_conditions_cannot_be_pooled(collections):
    s = bundle([collections / "a", collections / "cohort"])
    assert s.subject_binding == "configuration_cohort"
    assert len(s.source_subject_ids) == 2
    assert s.context.participant.subject_id.startswith("configuration:")
    assert "How this configuration" in render_html(build_passport(encoded(s)))
    for other in ("dense", "packet", "a"):
        with pytest.raises(ValueError, match="pool|twice"):
            bundle([collections / "a", collections / other])


def test_tampered_facts_answers_transport_or_trait_status_fail(collections):
    s = bundle([collections / "a"])
    raw = encoded(s)
    changed = s.model_copy(deep=True)
    changed.facts["decision_agreement_percent"] = 42
    with pytest.raises(ValueError, match="differ"):
        build_passport(encoded(changed))
    original = s.sessions[0]
    r = json.loads(original.report_json)
    r["analysis"]["mean_final_brier"] = 0
    data = encoded(r)
    item = SourceSession(
        **{**original.model_dump(), "report_json": data.decode(), "report_sha256": digest(data)}
    )
    with pytest.raises(ValueError, match="analysis"):
        derive([item])
    t = json.loads(original.transport_json)
    t["locks"][0]["public_trial"]["stage_instruction"] = "Changed"
    data = encoded(t)
    item = SourceSession(
        **{
            **original.model_dump(),
            "transport_json": data.decode(),
            "transport_sha256": digest(data),
        }
    )
    with pytest.raises(ValueError, match="presentation"):
        derive([item])
    p = build_passport(raw).model_dump(mode="json")
    p["model_diagnostics"]["parameters_are_validated_traits"] = True
    with pytest.raises(ValueError):
        read_passport(encoded(p))


def test_schema_snapshots():
    for name, model in [("passport.v4", SourcePassport), ("source-evidence.v1", SourceCollection)]:
        assert Path("schemas", name + ".json").read_bytes() == encoded(model.model_json_schema())


def test_nonzero_repeat_difference_uses_only_matched_initial_reports(collections, tmp_path):
    from epistemics.source_delivery.service import DeliveryService, create
    from epistemics.source_learning.battery import location
    from epistemics.source_learning.inference import raw_predictions
    from epistemics.source_learning.simulation import synthetic_answer

    directory = tmp_path / "shifted"
    m = create(directory, PARTICIPANT, seed=31, condition="sparse", synthetic=True)
    service = DeliveryService(directory)
    answers = []
    for i in range(36):
        trial = service.get_trial()["trial"]
        c, _ = location(i)
        a = synthetic_answer(
            m,
            i,
            raw_predictions(m, i, answers),
            "joint_process",
            1,
            0,
            ("customer_panel", "selection_audit", "measurement_audit", "stop")[c % 4],
        )
        if i < 12:
            p = round(a.probability + (0.01 if a.probability < 0.5 else -0.01), 2)
            a = a.model_copy(
                update={
                    "probability": p,
                    "decision": "invest" if p > m.companies[c].threshold else "decline",
                }
            )
        service.submit(trial["trial_id"], a)
        answers.append(a)
    service.finish()
    service.evidence()
    source = bundle([collections / "a", directory])
    assert source.facts["repeat_rmse_pp"] == pytest.approx(1.0)
    assert source.coverage["matched_forecasts_per_pair"] == 12
