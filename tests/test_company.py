import hashlib
import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from epistemics.company.analysis import fit_models
from epistemics.company.battery import battery_sha256, generate_battery
from epistemics.company.inference import (
    STATES,
    forecast,
    likelihood,
    posterior,
    quantiles,
)
from epistemics.company.models import CompanyAnswer, CompanyReport, CompanyTrial
from epistemics.company.simulation import answer_trial, demo, synthetic_observations
from epistemics.models import AgentDescriptor, Answer
from epistemics.service import EvaluationService


@pytest.fixture
def records():
    return generate_battery(42)


@pytest.fixture
def agent():
    return AgentDescriptor(
        agent_id="test:company", model="synthetic", model_version="1", configuration_sha256="0" * 64
    )


def test_replay_provenance_and_matched_worlds(records):
    assert records == generate_battery(42)
    assert records != generate_battery(43)
    assert len(records) == 54
    assert len({r["trial"]["trial_id"] for r in records}) == 54
    assert [r["truth"]["arm"] for r in records[::9]].count("copy") == 3
    copies = generate_battery(42, arm_override="copy")
    independents = generate_battery(42, arm_override="independent")
    for copy, independent in zip(copies, independents, strict=True):
        for field in ("growth", "margin", "temporary", "source_validity", "realized_growth_pct"):
            assert copy["truth"][field] == independent["truth"][field]
        assert copy["trial"]["dossier"] == independent["trial"]["dossier"]
        for a, b in zip(copy["trial"]["evidence"], independent["trial"]["evidence"], strict=True):
            if a["document_id"].endswith("d2"):
                continue
            assert a == b
    for record in records:
        trial = CompanyTrial.model_validate(record["trial"])
        assert len(trial.evidence) == trial.step
        seen = set()
        for item in trial.evidence:
            assert set(item.signal.parents) <= seen
            assert hashlib.sha256(item.text.encode()).hexdigest() == item.content_sha256
            seen.add(item.document_id)
        assert record["truth"]["growth"] == (record["truth"]["realized_growth_pct"] > 12)


def test_joint_prior_and_management_update_by_hand(records):
    initial = CompanyTrial.model_validate(records[0]["trial"])
    before = forecast(initial)
    assert before.growth_probability == pytest.approx(0.3)
    assert before.margin_probability == pytest.approx(
        0.3 * (0.85 * 0.75 + 0.15 * 0.4) + 0.7 * (0.85 * 0.35 + 0.15 * 0.15)
    )
    trial = CompanyTrial.model_validate(records[1]["trial"])
    assert trial.evidence[0].signal.value == 1
    # H and V both update from the same evidence: P(E)=.3*.71+.7*.29=.416.
    after = forecast(trial)
    assert after.growth_probability == pytest.approx(0.213 / 0.416)
    assert after.source_probability == pytest.approx(0.216 / 0.416)
    assert posterior(trial).sum() == pytest.approx(1)


@pytest.mark.parametrize(
    "policy",
    [
        {"positive": float("nan")},
        {"negative": 0},
        {"duplicate": 1.1},
        {"positive": 0.5, "auxiliary_shift": 1.2},
    ],
)
def test_synthetic_policy_rejects_invalid_or_unimplemented_combinations(records, policy):
    with pytest.raises(ValueError):
        answer_trial(CompanyTrial.model_validate(records[0]["trial"]), **policy)


def test_copies_and_derived_models_add_no_new_observation():
    records = generate_battery(0, arm_override="copy")
    for start in range(0, 54, 9):
        for before, after in ((1, 2), (3, 4)):
            assert (
                records[start + before]["truth"]["reference"]
                == records[start + after]["truth"]["reference"]
            )
            assert records[start + after]["truth"]["incremental_log_lr"] == pytest.approx(0)
            assert abs(records[start + after]["truth"]["standalone_log_lr"]) > 0.01
    trial = CompanyTrial.model_validate(records[4]["trial"])
    model = trial.evidence[-1]
    # Output 8 uniquely encodes management=0 and operations=0. Check two joint states by hand.
    assert model.signal.value == 8
    standalone = likelihood(model, trial.evidence[:-1], trial.dossier.world, isolated=True)
    assert standalone[STATES.index((1, 1, 0, 1))] == pytest.approx(0.15 * 0.15)
    assert standalone[STATES.index((0, 0, 1, 0))] == pytest.approx(0.5 * 0.9)
    bad = model.model_copy(update={"signal": model.signal.model_copy(update={"value": 30})})
    with pytest.raises(ValueError, match="declared inputs"):
        likelihood(bad, trial.evidence[:-1], trial.dossier.world)


def test_auxiliary_probe_distinguishes_a_temporary_explanation(records):
    base = CompanyTrial.model_validate(records[3]["trial"])
    assert base.evidence[-1].signal.kind == "operations"
    assert base.evidence[-1].signal.value == 0
    check = CompanyTrial.model_validate(records[7]["trial"]).evidence[-1]
    yes = check.model_copy(update={"signal": check.signal.model_copy(update={"value": 1})})
    no = check.model_copy(update={"signal": check.signal.model_copy(update={"value": 0})})
    fp = forecast(base.model_copy(update={"evidence": base.evidence + [yes]}))
    fn = forecast(base.model_copy(update={"evidence": base.evidence + [no]}))
    assert fp.temporary_probability > fn.temporary_probability
    assert fp.growth_probability > fn.growth_probability


def test_source_audit_revises_the_thesis_and_static_evidence_commutes(records):
    trial = CompanyTrial.model_validate(records[6]["trial"])
    assert trial.evidence[0].signal.value == 1
    last = trial.evidence[-1]
    negative_audit = last.model_copy(update={"signal": last.signal.model_copy(update={"value": 0})})
    bad = trial.model_copy(update={"evidence": trial.evidence[:-1] + [negative_audit]})
    assert forecast(trial).source_probability > forecast(bad).source_probability
    assert forecast(trial).growth_probability > forecast(bad).growth_probability
    full = CompanyTrial.model_validate(records[8]["trial"])
    docs = full.evidence.copy()
    docs[5], docs[6] = docs[6], docs[5]
    assert posterior(full.model_copy(update={"evidence": docs})) == pytest.approx(posterior(full))


@pytest.mark.parametrize("p", [0.0, 0.2, 0.5, 0.8, 1.0])
def test_quantiles_invert_the_declared_growth_distribution(p):
    q = quantiles(p)
    for u, y in zip((0.1, 0.5, 0.9), (q.p10, q.p50, q.p90), strict=True):
        cdf = (1 - p) * min(y / 12, 1) + p * max((y - 12) / 12, 0)
        assert cdf == pytest.approx(u)


@pytest.mark.parametrize(
    "policy",
    [
        {},
        {"positive": 0.7, "negative": 1.4, "duplicate": 0.4},
        {"duplicate": 1.0},
        {"positive": 0.5, "negative": 0.5},
    ],
)
def test_parameter_recovery(policy):
    observations = synthetic_observations(12, **policy)
    params, fits = fit_models(observations)
    assert fits["weighted_evidence"].identified
    assert params["positive_weight"].estimate == pytest.approx(policy.get("positive", 1), abs=1e-8)
    assert params["negative_weight"].estimate == pytest.approx(policy.get("negative", 1), abs=1e-8)
    assert params["duplicate_weight"].estimate == pytest.approx(
        policy.get("duplicate", 0), abs=1e-8
    )
    assert fits["weighted_evidence"].heldout_rmse < 1e-8


def test_auxiliary_recovery_noisy_weights_and_heldout_exclusion():
    obs = synthetic_observations(7, auxiliary_shift=1.2)
    _, fits = fit_models(obs)
    assert fits["joint_auxiliary_prior"].parameters["auxiliary_log_odds_shift"] == pytest.approx(
        1.2
    )
    assert fits["joint_auxiliary_prior"].heldout_rmse < 1e-12
    noisy = synthetic_observations(7, positive=0.8, negative=1.6, duplicate=0.3, noise=0.015)
    params, before = fit_models(noisy)
    assert params["negative_weight"].estimate == pytest.approx(1.6, abs=0.08)
    assert params["duplicate_weight"].estimate == pytest.approx(0.3, abs=0.05)
    for o in noisy[36:]:
        o.answer = o.answer.model_copy(update={"growth_probability": 0.99})
    _, after = fit_models(noisy)
    for key in before:
        assert before[key].parameters == after[key].parameters
        assert before[key].train_rmse == after[key].train_rmse
    assert before["weighted_evidence"].heldout_rmse != after["weighted_evidence"].heldout_rmse


def test_reports_metrics_and_schema():
    report = demo()
    assert all(m.reference_rmse < 1e-12 for m in report.metrics.values())
    assert report.diagnostics["decision_report_agreement"] == 1
    assert report.diagnostics["mean_expected_regret_under_public_model"] == pytest.approx(0)
    assert report.diagnostics["mean_absolute_update_on_redundant_items"] == pytest.approx(0)
    end = [o for o in report.observations if o.trial.step == 8]
    brier = sum((o.answer.growth_probability - o.truth.growth) ** 2 for o in end) / 6
    assert report.metrics["growth_probability"].final_brier == pytest.approx(brier)
    expected = CompanyReport.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert json.loads(Path("schemas/report.v2.json").read_text()) == expected


def test_company_session_privacy_retries_resume_and_immutability(tmp_path, agent):
    db = tmp_path / "eval.sqlite3"
    service = EvaluationService(db)
    started = service.start(agent, battery="company", seed=42)
    sid = started["session_id"]
    assert started["total_trials"] == 54 and "seed" not in started
    with pytest.raises(ValueError, match="Complete every"):
        service.finish(sid)
    first = CompanyTrial.model_validate(service.get_trial(sid)["trial"])
    answer = answer_trial(first)
    with pytest.raises(ValueError, match="CompanyAnswer"):
        service.submit(sid, first.trial_id, Answer(probability=0.5))
    with pytest.raises(ValueError, match="already available"):
        service.submit(
            sid, first.trial_id, answer.model_copy(update={"evidence_ids": ["company-01-d8"]})
        )
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(lambda _: service.submit(sid, first.trial_id, answer), range(4)))
    assert all(r == receipts[0] for r in receipts)
    service = EvaluationService(db)
    assert service.get_trial(sid)["answered"] == 1
    with pytest.raises(ValueError, match="cannot be changed"):
        service.submit(sid, first.trial_id, answer.model_copy(update={"growth_probability": 0.9}))
    while not (current := service.get_trial(sid))["complete"]:
        public = json.dumps(current)
        for key in ('"truth"', '"seed"', '"reference"', '"realized_growth_pct"', '"arm"'):
            assert key not in public
        trial = CompanyTrial.model_validate(current["trial"])
        assert len(trial.evidence) == trial.step
        receipt = service.submit(sid, trial.trial_id, answer_trial(trial))
        assert "outcome" not in receipt
    report = service.finish(sid)
    assert report == service.finish(sid)
    assert report.battery_sha256 == battery_sha256()
    assert service.submit(sid, first.trial_id, answer) == receipts[0]


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -0.1, 1.1, True, "0.5"])
def test_invalid_company_probabilities_rejected(records, invalid):
    answer = answer_trial(CompanyTrial.model_validate(records[0]["trial"])).model_dump()
    answer["growth_probability"] = invalid
    with pytest.raises(ValueError):
        CompanyAnswer.model_validate(answer)


def test_rejects_reversed_quantiles(records):
    answer = answer_trial(CompanyTrial.model_validate(records[0]["trial"])).model_dump()
    answer["growth_quantiles_pct"] = {"p10": 10.0, "p50": 5.0, "p90": 20.0}
    with pytest.raises(ValueError, match="p10 <= p50"):
        CompanyAnswer.model_validate(answer)
