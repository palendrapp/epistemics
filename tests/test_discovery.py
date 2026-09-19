import hashlib
import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest

from epistemics.discovery.analysis import analyze, growth_report
from epistemics.discovery.battery import VARIANTS, generate_battery
from epistemics.discovery.inference import forecast, posterior, report_prediction
from epistemics.discovery.models import (
    DiscoveryAnswer,
    DiscoveryReport,
    DiscoveryTrial,
)
from epistemics.discovery.simulation import (
    ALPHA_GRID,
    answer_trial,
    demo,
    fit_candidates,
    logit,
    response_log_likelihood,
)
from epistemics.discovery.world import (
    SOURCE_STATES,
    STATES,
    F,
    cdf,
    log_measurement,
)
from epistemics.models import AgentDescriptor, Answer
from epistemics.service import EvaluationService


@pytest.fixture
def trials():
    return [DiscoveryTrial.model_validate(r["trial"]) for r in generate_battery(7)]


def test_seed_replay_visibility_hashes_and_matched_assignments():
    base = generate_battery(11)
    assert base == generate_battery(11)
    assert base != generate_battery(12)
    assert len(base) == 10
    initial = base[0]["truth"]
    for dimension, values in VARIANTS.items():
        for value in values:
            changed = generate_battery(11, variant={dimension: value})
            for field in (
                "underlying_growth_pct",
                "disruption",
                "relationship",
                "source_parameters",
                "realized_growth_pct",
            ):
                assert changed[0]["truth"][field] == initial[field]
            for a, b in zip(base, changed, strict=True):
                assert a["trial"]["index"] == b["trial"]["index"]
                if dimension != "lineage":
                    assert a["trial"]["documents"] == b["trial"]["documents"]
    short = generate_battery(11, variant={"history": "short"})[0]["trial"]["sources"]
    long = generate_battery(11, variant={"history": "long"})[0]["trial"]["sources"]
    for a, b in zip(short, long, strict=True):
        assert a["archive"] == b["archive"][:2]
    for step, r in enumerate(base):
        t = r["trial"]
        assert len(t["documents"]) == step
        assert len(t["source_probe_ids"]) == (3 if step in (0, 6) else 0)
        assert not {
            "truth",
            "seed",
            "source_parameters",
            "claim_ledger",
            "likelihoods",
            "signal",
        } & set(t)
        for i, d in enumerate(t["documents"]):
            assert d["document_id"] == f"d{i + 1}"
            assert hashlib.sha256(d["text"].encode()).hexdigest() == d["content_sha256"]
    with pytest.raises(ValueError):
        generate_battery(1, variant={"history": "selected_successes"})


def test_rounding_likelihood_and_source_learning_by_hand(trials):
    t = trials[0]
    q = posterior(t)
    source = t.sources[0]
    likelihood = []
    for bias, sd in SOURCE_STATES:
        p = 1.0
        for row in source.archive:
            error = row.reported_pct - row.audited_pct
            hi = 0.5 * math.erfc(-(error + 0.05 - bias) / sd / math.sqrt(2))
            lo = 0.5 * math.erfc(-(error - 0.05 - bias) / sd / math.sqrt(2))
            p *= hi - lo
        likelihood.append(p)
    expected = np.asarray(likelihood) / sum(likelihood)
    actual = np.bincount(STATES[:, 3], weights=q, minlength=6)
    assert actual == pytest.approx(expected, abs=1e-12)
    assert forecast(t).growth_probability == pytest.approx(0.5)
    assert np.exp(log_measurement(0, 0, 1)) == pytest.approx(math.erf(0.05 / math.sqrt(2)))
    assert np.isfinite(log_measurement(100, 0, 1))


def test_observers_only_use_public_inputs_and_reweight_old_evidence(trials, monkeypatch):
    import epistemics.discovery.battery as battery

    monkeypatch.setattr(
        battery,
        "generate_battery",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("private generator read")),
    )
    before = forecast(trials[5])
    after = forecast(trials[6])
    assert abs(before.growth_probability - after.growth_probability) > 1e-6
    assert abs(before.source_accuracy["morrow"] - after.source_accuracy["morrow"]) > 1e-6
    # With source uncertainty removed the unrelated archive update cannot move the company.
    fixed_before = forecast(trials[5], model="fixed_sources").model_dump()
    fixed_after = forecast(trials[6], model="fixed_sources").model_dump()
    # BLAS implementations can differ in the final floating-point bits. Check every
    # field with a tolerance far smaller than the meaningful audit changes above.
    for field, expected in fixed_before.items():
        assert fixed_after[field] == pytest.approx(expected, rel=0, abs=1e-12)
    for step in range(10):
        q = posterior(trials[step])
        assert np.isfinite(q).all() and q.sum() == pytest.approx(1)


def test_model_dependency_lineage_and_mixture_quantiles(trials):
    assert forecast(trials[3]) == forecast(trials[4])
    for arm in ("shared", "independent"):
        records = generate_battery(2, variant={"lineage": arm})
        t = DiscoveryTrial.model_validate(records[7]["trial"])
        assert forecast(t).shared_origin_probability == pytest.approx(float(arm == "shared"))
    for t in (trials[0], trials[5], trials[-1]):
        q = posterior(t)
        f = forecast(t)
        assert f.conditional_growth_probability == pytest.approx(
            float((q * (STATES[:, 1] == 0)) @ cdf((F - 12) / 2) / (q * (STATES[:, 1] == 0)).sum())
        )
        for level, key in ((0.1, "p10"), (0.5, "p50"), (0.9, "p90")):
            value = getattr(f.growth_quantiles_pct, key)
            assert q @ cdf((value - F) / 2) == pytest.approx(level)
    bad = trials[4].model_copy(deep=True)
    bad.documents[-1].text = bad.documents[-1].text.replace(
        "Model projection:", "Model projection: 99.0; original:"
    )
    with pytest.raises(ValueError, match="declared inputs"):
        forecast(bad)


def test_source_and_output_framing_are_distinct_and_complements_align():
    up = DiscoveryTrial.model_validate(
        generate_battery(3, variant={"response": "growth"})[2]["trial"]
    )
    down = DiscoveryTrial.model_validate(
        generate_battery(3, variant={"response": "failure"})[2]["trial"]
    )
    a, b = answer_trial(up), answer_trial(down)
    assert a.target_probability == pytest.approx(1 - b.target_probability)
    assert growth_report(up, a) == pytest.approx(growth_report(down, b))
    assert a.decision == b.decision
    p = report_prediction(up)
    shifted = report_prediction(up, output_frame=0.4)
    assert logit(shifted)[0] - logit(p)[0] == pytest.approx(0.4)
    first = DiscoveryTrial.model_validate(
        generate_battery(3, variant={"history": "short"})[0]["trial"]
    )
    assert report_prediction(first, source_frame=1)[1:] != pytest.approx(
        report_prediction(first)[1:]
    )


def test_fitting_recovers_input_output_and_excludes_heldout_reports():
    # Controlled design spanning source-sensitive and report-wording-sensitive channels.
    x = np.array([-1.0, -0.7, -0.4, 0.0, 0.3, 0.6, 0.9, 1.2] * 2)
    w = np.array([1, 0, -1, 0, 1, 0, -1, 0] * 2)
    z = np.linspace(-1, 1, 16)
    design = {"joint_learning": np.array([z + alpha * x for alpha in ALPHA_GRID])}
    for key in ("fixed_sources", "fixed_weak_link", "fixed_strong_link"):
        design[key] = (z + 2 * x)[None, :]
    train = np.arange(16) < 8
    obs = 1 / (1 + np.exp(-(z + 1.25 * x + 0.4 * w)))
    fit = fit_candidates(design, obs, w, train)["source_and_output"]
    assert fit["source_frame"] == pytest.approx(1.25)
    assert fit["output_frame"] == pytest.approx(0.4)
    changed = obs.copy()
    changed[~train] = 0.2
    again = fit_candidates(design, changed, w, train)["source_and_output"]
    assert (fit["source_frame"], fit["output_frame"], fit["train_logit_mse"]) == (
        again["source_frame"],
        again["output_frame"],
        again["train_logit_mse"],
    )
    assert np.isfinite(
        response_log_likelihood(np.array([0.0, 1.0, 0.5]), np.array([-12.0, 12.0, 0.0]))
    ).all()


def test_persistence_probes_immutability_and_private_finish(tmp_path):
    service = EvaluationService(tmp_path / "sessions.sqlite3")
    agent = AgentDescriptor(
        agent_id="test:discovery",
        model="synthetic",
        model_version="1",
        configuration_sha256="0" * 64,
    )
    started = service.start(agent, seed=7, battery="discovery")
    sid = started["session_id"]
    assert started["total_trials"] == 10 and "seed" not in started
    with pytest.raises(ValueError, match="Complete every"):
        service.finish(sid)
    t = DiscoveryTrial.model_validate(service.get_trial(sid)["trial"])
    with pytest.raises(ValueError, match="DiscoveryAnswer"):
        service.submit(sid, t.trial_id, Answer(probability=0.5))
    answer = answer_trial(t)
    with pytest.raises(ValueError, match="source_accuracy"):
        service.submit(sid, t.trial_id, answer.model_copy(update={"source_accuracy": {}}))
    with pytest.raises(ValueError, match="already available"):
        service.submit(sid, t.trial_id, answer.model_copy(update={"evidence_ids": ["d9"]}))
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(lambda _: service.submit(sid, t.trial_id, answer), range(4)))
    assert all(r == receipts[0] for r in receipts)
    with pytest.raises(ValueError, match="cannot be changed"):
        service.submit(sid, t.trial_id, answer.model_copy(update={"target_probability": 0.7}))
    service = EvaluationService(tmp_path / "sessions.sqlite3")
    while not (current := service.get_trial(sid))["complete"]:
        t = DiscoveryTrial.model_validate(current["trial"])
        a = answer_trial(t)
        if t.conditional_probe:
            with pytest.raises(ValueError, match="conditional_growth_probability"):
                service.submit(
                    sid, t.trial_id, a.model_copy(update={"conditional_growth_probability": None})
                )
        receipt = service.submit(sid, t.trial_id, a)
        assert not {"outcome", "truth", "seed"} & set(receipt)
    report = service.finish(sid)
    assert report == service.finish(sid)
    assert len(report.observations) == 10 and report.schema_version == "epistemics.report.v3"
    assert report.observer_models["joint_learning"].growth_report_rmse < 1e-12
    metrics, models = analyze(report.observations, report.private_case)
    assert report.metrics == metrics and report.observer_models == models
    assert report.metrics["independent_company_outcomes"] == 1
    assert report.metrics["mean_extraction_absolute_error_pct_points"] == 0
    assert report.metrics["final_brier"] == pytest.approx(
        (growth_report(t, a) - (report.private_case.realized_growth_pct > 12)) ** 2
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "0.5", -0.1, 1.1])
def test_invalid_probability_rejected(trials, value):
    data = answer_trial(trials[0]).model_dump()
    data["target_probability"] = value
    with pytest.raises(ValueError):
        DiscoveryAnswer.model_validate(data)


def test_schema_and_report_contract():
    expected = DiscoveryReport.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert json.loads(Path("schemas/report.v3.json").read_text()) == expected
    report = demo(2)
    data = report.model_dump()
    data["observations"].pop()
    with pytest.raises(ValueError):
        DiscoveryReport.model_validate(data)
