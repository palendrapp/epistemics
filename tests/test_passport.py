import hashlib
import html
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from epistemics.cli import demo
from epistemics.company.simulation import demo as company_demo
from epistemics.discovery.analysis import growth_report
from epistemics.discovery.simulation import demo as discovery_demo
from epistemics.participants import HumanParticipant, ParticipantDescriptor, SessionContext
from epistemics.passport.build import build_passport, verify_derivation
from epistemics.passport.models import CandidateSupport, Passport
from epistemics.passport.render import measurement_value, render_html, render_markdown

CREATED = datetime(2026, 9, 19, tzinfo=UTC)


@pytest.fixture(scope="module")
def reports():
    return {
        "belief": demo(evidence_weight=0.4),
        "company": company_demo(positive=0.7, negative=1.4, duplicate=0.4),
        "discovery": discovery_demo(variant={"response": "failure"}),
    }


def raw(report):
    return (report.model_dump_json(indent=2) + "\n").encode()


def passport(report):
    return build_passport(raw(report), response_origin="synthetic", created_at=CREATED)


def by_id(result, key):
    return next(d for d in result.dimensions if d.dimension_id == key)


def test_human_contract_needs_no_model_fields_and_rejects_agent_metadata():
    person = ParticipantDescriptor.model_validate({"kind": "human", "subject_id": "local:person-1"})
    assert isinstance(person.root, HumanParticipant)
    assert "configuration" not in person.model_dump()
    with pytest.raises(ValueError):
        ParticipantDescriptor.model_validate(
            {
                "kind": "human",
                "subject_id": "local:person-1",
                "model": "pretend-agent",
            }
        )
    with pytest.raises(ValueError):
        ParticipantDescriptor.model_validate({"kind": "agent", "subject_id": "missing-config"})


def test_shared_session_boundary_is_private_and_contains_no_answer_key():
    context = SessionContext(
        session_id="example",
        participant=HumanParticipant(subject_id="human:example"),
        response_origin="human",
        protocol_version="example/1",
        protocol_sha256="0" * 64,
        evaluator_version="example",
        started_at=CREATED,
        completion="not_started",
        accepted_answers=0,
        planned_answers=10,
    )
    assert context.sharing == "private"
    assert context.conditions.tools is None  # Unknown does not mean no tools.
    assert not {"truth", "seed", "trials", "answers"} & context.model_dump().keys()
    for changes in [
        {"response_origin": "agent"},
        {"accepted_answers": 11},
        {"completion": "complete"},
        {"accepted_answers": True},
        {"completed_at": CREATED},
        {"seed": 42},
    ]:
        with pytest.raises(ValueError):
            SessionContext.model_validate(context.model_dump() | changes)


@pytest.mark.parametrize("name", ["belief", "company", "discovery"])
def test_import_binds_exact_legacy_bytes_and_keeps_context(reports, name):
    original = raw(reports[name])
    result = build_passport(original, response_origin="synthetic", created_at=CREATED)
    assert result.source.sha256 == hashlib.sha256(original).hexdigest()
    assert result.context.participant.subject_id == reports[name].agent.agent_id
    assert (
        result.context.participant.configuration.configuration_sha256
        == reports[name].agent.configuration_sha256
    )
    assert result.context.conditions.interface == "unspecified"
    assert result.context.accepted_answers == len(reports[name].observations)
    assert result.issuance_status == "draft_unsigned"
    assert result.scope == "single_report_partial_profile"
    assert raw(reports[name]) == original
    assert "private_case" not in result.model_dump()
    assert '"claim_ledger"' not in result.model_dump_json()
    assert all(d.evidence_status != "supported" for d in result.dimensions)
    verify_derivation(result, original)
    changed_whitespace = json.dumps(json.loads(original), separators=(",", ":")).encode()
    with pytest.raises(ValueError, match="bytes"):
        verify_derivation(result, changed_whitespace)
    assert build_passport(changed_whitespace).source.sha256 != result.source.sha256


def test_origin_is_explicit_and_cannot_relabel_agent_as_human(reports):
    result = build_passport(raw(reports["belief"]))
    assert result.context.response_origin == "unspecified"
    assert "RESPONSE ORIGIN UNSPECIFIED" in render_html(result)
    with pytest.raises(ValueError, match="human"):
        build_passport(raw(reports["belief"]), response_origin="human")
    with pytest.raises(ValueError, match="only"):
        build_passport(b'{"schema_version":"epistemics.study-profile.v1"}')


def test_low_evidence_weight_has_traceable_untested_support_and_visible_gaps(reports):
    result = passport(reports["belief"])
    evidence = by_id(result, "evidence_weighting")
    assert "less weight" in evidence.summary
    assert evidence.measurements[0].value == pytest.approx(0.4)
    assert evidence.measurements[0].interval_95 is not None
    assert result.support_candidates[0].status == "untested"
    assert by_id(result, "decision_consistency").evidence_status == "insufficient_evidence"
    assert (
        by_id(result, "dependence_and_causal_reasoning").evidence_status == "insufficient_evidence"
    )
    support_data = result.support_candidates[0].model_dump() | {"status": "effective"}
    with pytest.raises(ValueError):
        CandidateSupport.model_validate(support_data)


def test_interval_spanning_reference_does_not_assign_underweighting(reports):
    report = reports["belief"].model_copy(deep=True)
    report.parameters["evidence_weight"].interval_95 = (0.2, 1.5)
    result = passport(report)
    assert "interval includes reference" in by_id(result, "evidence_weighting").summary
    assert result.support_candidates == []


def test_company_interpretation_recovers_known_weights_without_population_claim(reports):
    result = passport(reports["company"])
    evidence = by_id(result, "evidence_weighting")
    assert evidence.measurements[0].value == pytest.approx(0.7)
    assert evidence.measurements[1].value == pytest.approx(1.4)
    assert "0.700" in evidence.summary and "1.400" in evidence.summary
    calibration = by_id(result, "uncertainty_and_calibration")
    assert "six company outcomes" in calibration.summary
    assert by_id(result, "decision_consistency").measurements[0].value == 100


def test_unidentified_company_fit_suppresses_directional_claims(reports):
    report = reports["company"].model_copy(deep=True)
    report.model_fits["weighted_evidence"].identified = False
    result = passport(report)
    evidence = by_id(result, "evidence_weighting")
    assert evidence.evidence_status == "insufficient_evidence"
    assert "no directional interpretation" in evidence.summary
    dependence = by_id(result, "dependence_and_causal_reasoning")
    assert all(m.label != "Duplicate-counting coefficient" for m in dependence.measurements)


def test_discovery_preserves_complement_and_does_not_invent_traits(reports):
    report = reports["discovery"]
    result = passport(report)
    assert by_id(result, "evidence_weighting").evidence_status == "insufficient_evidence"
    dependence = by_id(result, "dependence_and_causal_reasoning")
    before, after = report.observations[3:5]
    p, q = growth_report(before.trial, before.answer), growth_report(after.trial, after.answer)
    assert f"from {p:.1%} to {q:.1%}" in dependence.examples[0].description
    assert "One resolved company outcome" in by_id(result, "uncertainty_and_calibration").summary
    assert all(
        "other evidence arrived" in x.description for x in by_id(result, "source_judgment").examples
    )
    assert result.support_candidates == []


def test_derivation_check_detects_interpretation_and_identity_tampering(reports):
    result = passport(reports["belief"])
    for field, replacement in [("summary", "Perfect calibration"), ("title", "Certified safe")]:
        changed = result.model_copy(deep=True)
        setattr(changed.dimensions[0], field, replacement)
        with pytest.raises(ValueError, match="interpretation"):
            verify_derivation(changed, raw(reports["belief"]))
    changed = result.model_copy(deep=True)
    changed.context.participant.subject_id = "another-agent"
    with pytest.raises(ValueError, match="interpretation"):
        verify_derivation(changed, raw(reports["belief"]))
    data = result.model_dump()
    data["dimensions"][1] = data["dimensions"][0]
    with pytest.raises(ValueError, match="each of the six"):
        Passport.model_validate(data)


def test_renderers_escape_untrusted_metadata_and_show_same_measurements(reports):
    report = reports["belief"].model_copy(deep=True)
    report.agent.agent_id = '<script>alert("x")</script> [click](https://example.invalid)'
    result = passport(report)
    webpage, markdown = render_html(result), render_markdown(result)
    prose = re.sub(r"```json\n.*?\n```", "", markdown, flags=re.DOTALL)
    assert "<script>" not in webpage and "<script>" not in prose
    assert '<script>alert("x")</script>' not in webpage
    assert "[click](https://example.invalid)" not in prose
    assert "SYNTHETIC DEMONSTRATION" in webpage and "SYNTHETIC DEMONSTRATION" in markdown
    assert result.source.sha256 in webpage and result.source.sha256 in markdown
    for dimension in result.dimensions:
        assert html.escape(dimension.summary) in webpage
        for measurement in dimension.measurements:
            assert html.escape(measurement_value(measurement)) in webpage


def test_cli_create_verify_render_and_refuse_overwrite(tmp_path, reports):
    source = tmp_path / "report.json"
    source.write_bytes(raw(reports["belief"]))
    destination = tmp_path / "passport"

    def cli(*args):
        return subprocess.run(
            [sys.executable, "-m", "epistemics.cli", "passport", *map(str, args)],
            capture_output=True,
            text=True,
        )

    args = ["create", "--report", source, "--response-origin", "synthetic", "--output", destination]
    created = cli(*args)
    assert created.returncode == 0, created.stderr
    profile = destination / "passport.json"
    original = profile.read_bytes()
    assert {p.name for p in destination.iterdir()} == {
        "passport.json",
        "passport.html",
        "passport.md",
    }
    checked = cli("verify", profile, "--report", source)
    assert checked.returncode == 0 and "execution/origin not verified" in checked.stdout
    assert cli(*args).returncode != 0
    assert profile.read_bytes() == original
    out = tmp_path / "render.html"
    assert cli("render", profile, "--output", out).returncode == 0
    assert out.read_text() == (destination / "passport.html").read_text()
    assert cli("render", profile, "--output", out).returncode != 0
    source.write_bytes(source.read_bytes() + b"\n")
    assert cli("verify", profile, "--report", source).returncode != 0


@pytest.mark.parametrize(
    "contract,filename",
    [
        (ParticipantDescriptor, "participant.v1.json"),
        (SessionContext, "session-context.v1.json"),
        (Passport, "passport.v1.json"),
    ],
)
def test_exported_schemas_match(contract, filename):
    expected = contract.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert json.loads((Path("schemas") / filename).read_bytes()) == expected
