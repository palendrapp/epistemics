import copy
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from epistemics.baselines import answer_trial as numeric_answer
from epistemics.discovery.simulation import answer_trial as discovery_answer
from epistemics.live.analysis import analyze_calibration
from epistemics.live.battery import generate
from epistemics.live.models import CoreReport, CoreTrial
from epistemics.live.service import LiveService, SessionConflict
from epistemics.models import Observation
from epistemics.passport.build import verify_derivation
from epistemics.passport.models import read_passport
from epistemics.passport.render import render_html

HUMAN = {"kind": "human", "subject_id": "synthetic:human-adapter"}
AGENT = {
    "kind": "agent",
    "subject_id": "synthetic:agent-adapter",
    "configuration": {
        "model": "analytic-reference",
        "model_version": "test",
        "configuration_sha256": "0" * 64,
    },
}


def response(trial, *, weight=1):
    trial = CoreTrial.model_validate(trial)
    answer = (
        discovery_answer(trial.payload)
        if trial.module == "discovery"
        else numeric_answer(trial.payload, evidence_weight=weight)
    )
    return answer.model_dump()


def start(service, participant=None, **kwargs):
    return service.start(
        participant or HUMAN,
        request_id=kwargs.pop("request_id", "idempotency-test-001"),
        instructions_accepted=True,
        response_origin="synthetic",
        **kwargs,
    )["session_id"]


def complete(service, sid, *, weight=1):
    while not (current := service.get_trial(sid))["complete"]:
        trial = current["trial"]
        service.submit(sid, trial["trial_id"], response(trial, weight=weight))
    return CoreReport.model_validate_json(service.report_bytes(sid))


def test_shared_materials_scores_and_passport_preserve_participant_kind(tmp_path):
    service = LiveService(tmp_path / "core.db")
    human = start(service, seed=17, conditions={"interface": "browser"})
    agent = start(
        service, AGENT, seed=17, request_id="idempotency-test-002", conditions={"interface": "mcp"}
    )
    for _ in range(34):
        a, b = service.get_trial(human), service.get_trial(agent)
        assert a["trial"] == b["trial"]
        answer = response(a["trial"], weight=0.4)
        for sid in [human, agent]:
            service.submit(sid, a["trial"]["trial_id"], answer)
    reports = [CoreReport.model_validate_json(service.report_bytes(s)) for s in [human, agent]]
    assert reports[0].calibration.parameters == reports[1].calibration.parameters
    assert reports[0].discovery.metrics == reports[1].discovery.metrics
    assert reports[0].discovery.observer_models == reports[1].discovery.observer_models
    passports = [read_passport(service.passport_bytes(s)) for s in [human, agent]]
    assert passports[0].dimensions == passports[1].dimensions
    assert passports[0].support_candidates == passports[1].support_candidates
    assert passports[0].context.participant.kind == "human"
    assert passports[1].context.participant.kind == "agent"
    assert passports[0].context.conditions.interface == "browser"
    assert passports[1].context.conditions.interface == "mcp"
    assert "configuration" not in passports[0].context.participant.model_dump()
    assert len(passports[0].dimensions) == 6
    assert passports[0].support_candidates[0].status == "untested"
    assert passports[0].context.conditions.elapsed_seconds > 0
    assert "SYNTHETIC" in render_html(passports[0])
    for sid, passport in zip([human, agent], passports, strict=True):
        raw = service.report_bytes(sid)
        assert passport.source.sha256 == hashlib.sha256(raw).hexdigest()
        verify_derivation(passport, raw)
        restarted = LiveService(tmp_path / "core.db")
        assert restarted.report_bytes(sid) == raw
        assert restarted.passport_bytes(sid) == service.passport_bytes(sid)
    with pytest.raises(ValueError, match="relabeled"):
        from epistemics.passport.build import build_passport

        build_passport(service.report_bytes(human), response_origin="human")
    with pytest.raises(ValueError, match="bytes"):
        verify_derivation(passports[0], service.report_bytes(human) + b" ")


def test_public_boundary_and_no_early_results(tmp_path):
    service = LiveService(tmp_path / "core.db")
    sid = start(service, seed=7)
    for index in range(34):
        current = service.get_trial(sid)
        encoded = json.dumps(current)
        assert not any(
            f'"{key}"' in encoded
            for key in [
                "seed",
                "truth",
                "private_case",
                "reference",
                "claim_ledger",
                "observer_models",
            ]
        )
        assert current["answered"] == index
        assert len(current["history"]) == index
        trial = current["trial"]
        assert trial["index"] == index
        if index < 10:
            assert len(trial["payload"]["documents"]) == index
        for method in [service.report_bytes, service.passport_bytes]:
            with pytest.raises(SessionConflict, match="34"):
                method(sid)
        service.submit(sid, trial["trial_id"], response(trial))
    assert service.get_trial(sid)["trial"] is None
    assert '"seed"' in service.report_bytes(sid).decode()


def test_transactional_retry_resume_immutable_answers(tmp_path):
    service = LiveService(tmp_path / "core.db")
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(lambda _: start(service, seed=7), range(4)))
    assert len(set(ids)) == 1
    sid = ids[0]
    with pytest.raises(SessionConflict, match="metadata"):
        start(service, seed=8)
    current = service.get_trial(sid)
    trial = current["trial"]
    answer = response(trial)
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(
            pool.map(lambda _: service.submit(sid, trial["trial_id"], answer), range(4))
        )
    assert all(r == receipts[0] for r in receipts)
    assert service.get_trial(sid)["answered"] == 1
    with pytest.raises(SessionConflict, match="cannot be changed"):
        service.submit(sid, trial["trial_id"], answer | {"target_probability": 0.001})
    with pytest.raises(SessionConflict, match="current trial"):
        service.submit(sid, "core-33", {"probability": 0.5})
    restarted = LiveService(tmp_path / "core.db")
    assert restarted.get_trial(sid) == service.get_trial(sid)
    assert restarted.submit(sid, trial["trial_id"], answer) == receipts[0]


@pytest.mark.parametrize(
    "change",
    [
        {"source_accuracy": {}},
        {"evidence_ids": ["d9"]},
        {"conditional_growth_probability": 0.5},
        {"extracted_values": {"extra": 2}},
        {"target_probability": 1.1},
        {"growth_quantiles_pct": {"p10": 3, "p50": 2, "p90": 1}},
    ],
)
def test_invalid_answer_does_not_advance(tmp_path, change):
    service = LiveService(tmp_path / "core.db")
    sid = start(service, seed=7)
    trial = service.get_trial(sid)["trial"]
    with pytest.raises(ValueError):
        service.submit(sid, trial["trial_id"], response(trial) | change)
    assert service.get_trial(sid)["answered"] == 0


def test_version_guard_and_consent(tmp_path, monkeypatch):
    service = LiveService(tmp_path / "core.db")
    with pytest.raises(ValueError, match="accept"):
        service.start(HUMAN, request_id="idempotency-test-001")
    with pytest.raises(ValueError, match="continuous"):
        start(service, conditions={"context_policy": "reset_per_trial"})
    sid = start(service, seed=7)
    trial = service.get_trial(sid)["trial"]
    answer = response(trial)
    receipt = service.submit(sid, trial["trial_id"], answer)
    monkeypatch.setattr("epistemics.live.service.protocol_digest", lambda: "f" * 64)
    with pytest.raises(SessionConflict, match="original evaluator"):
        service.get_trial(sid)
    with pytest.raises(SessionConflict, match="restart"):
        start(service, request_id="a-different-start-id")
    with pytest.raises(SessionConflict, match="restart"):
        service.describe()
    assert service.submit(sid, trial["trial_id"], answer) == receipt


@pytest.mark.parametrize("seed", [1, 17, 92])
@pytest.mark.parametrize("prior,evidence,bias", [(1, 1, 0), (0.4, 1.5, 0.2), (1.3, 0.3, -0.4)])
def test_core_calibration_parameter_recovery(seed, prior, evidence, bias):
    import math

    from epistemics.battery import logit

    observations = []
    for row in generate(seed)[10:]:
        trial = CoreTrial.model_validate(row["trial"]).payload
        s = trial.stimulus
        z = (
            bias
            + prior * logit(s["prior_h"])
            + evidence * (2 * s["signal"] - 1) * logit(s["sensor_accuracy"])
        )
        observations.append(
            Observation(
                trial=trial,
                answer={"probability": 1 / (1 + math.exp(-z))},
                truth=row["truth"],
                answered_at="2026-09-19T00:00:00Z",
            )
        )
    result = analyze_calibration(observations)
    for key, value in [
        ("prior_weight", prior),
        ("evidence_weight", evidence),
        ("response_bias", bias),
    ]:
        assert result.parameters[key].estimate == pytest.approx(value, abs=1e-8)


def test_core_discovery_reference_and_report_contract(tmp_path):
    service = LiveService(tmp_path / "core.db")
    sid = start(service, seed=92)
    report = complete(service, sid)
    assert report.discovery.observer_models["joint_learning"].growth_report_rmse < 1e-10
    assert report.calibration.metrics.reference_rmse < 1e-10
    broken = copy.deepcopy(report.model_dump())
    broken["calibration"]["observations"].reverse()
    with pytest.raises(ValueError, match="order"):
        CoreReport.model_validate(broken)
