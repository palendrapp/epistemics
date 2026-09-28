import json
import math

import numpy as np
import pytest

from epistemics.dispositions import design, fit, observers
from epistemics.dispositions.response import (
    erfc,
    logit,
    report_edges,
    sample_reports,
    sigmoid,
    wtp_log_likelihood,
)
from epistemics.dispositions.validation import check_gates, run, validate


def test_vectorized_erfc_matches_standard_library():
    x = np.linspace(-9, 9, 3601)
    reference = np.array([math.erfc(v) for v in x])
    assert np.max(np.abs(erfc(x) - reference) / reference) < 1.2e-7
    assert erfc(np.array([np.inf, -np.inf])).tolist() == [0.0, 2.0]


def test_independent_observer_ignores_cues_and_adds_evidence():
    items = design.corroboration()
    pair = items["kind"] == "pair"
    expected = (
        logit(items["prior"])
        + items["report_a"] * logit(items["accuracy_a"])
        + items["report_b"] * logit(items["accuracy_b"])
    )
    assert np.allclose(observers.corroboration(items, 0.0, 1.0)[pair], expected[pair], atol=1e-3)
    # With no discount at all the rival is the same observer.
    assert np.allclose(observers.fixed_discount(items, 1.0, 1.0)[pair], expected[pair], atol=1e-3)


def test_relay_prior_discounts_matches_but_not_conflicts():
    items = design.corroboration()
    conflict = (items["kind"] == "pair") & (items["report_a"] != items["report_b"])
    match = (items["kind"] == "pair") & ~conflict
    certain = observers.corroboration(items, 1.0, 1.0)
    none = observers.corroboration(items, 0.0, 1.0)
    first_only = logit(items["prior"]) + items["report_a"] * logit(items["accuracy_a"])
    assert np.allclose(certain[match], first_only[match], atol=1e-2)
    assert np.allclose(certain[conflict], none[conflict], atol=1e-6)
    single = items["kind"] == "single"
    assert np.allclose(certain[single], first_only[single])


def test_relay_probe_rises_with_prior_and_identical_wording():
    items = design.corroboration(probes=True)
    probe = items["kind"] == "probe"
    low, high = (sigmoid(observers.corroboration(items, d, 1.0)[probe]) for d in (0.3, 0.7))
    assert np.all(high > low)
    order = np.argsort(items["cue"][probe])
    assert np.all(np.diff(sigmoid(observers.corroboration(items, 0.5, 1.0)[probe])[order]) >= 0)


def test_disclosure_observer_boundaries_and_revealed_type():
    items = design.disclosure()
    shared = logit(items["prior"]) + logit(items["good"]) * (
        items["shared_good"] - items["shared_bad"]
    )
    assert np.allclose(observers.disclosure(items, 0.0, 1.0), shared, atol=1e-3)
    clean = items["shared_bad"] == 0
    assert np.allclose(
        observers.disclosure(items, 1.0, 1.0)[clean],
        observers.linear_skepticism(items, 1.0, 1.0)[clean],
        atol=1e-2,
    )
    # A shared bad item rules out a selective sender, so the prior on selection stops mattering.
    mixed = (items["shared_bad"] > 0) & (items["withheld"] > 0)
    assert mixed.sum() == 4
    for sigma in (0.2, 0.9):
        assert np.allclose(observers.disclosure(items, sigma, 1.0)[mixed], shared[mixed])
    assert np.all(observers.linear_skepticism(items, 1.0, 1.0)[mixed] < shared[mixed] - 0.5)


def test_check_values_separate_decision_value_and_certainty_functions():
    items = design.checks()
    decision, linear = observers.check_values(items, "linear")
    _, entropy = observers.check_values(items, "entropy")
    assert np.allclose(decision[:12], 0) and np.allclose(decision[18:], 0)
    assert np.all(decision[12:18] > 5)
    # Whole decision values: flooring and rounding agree for a decision-value respondent.
    assert np.allclose(decision, np.round(decision))
    one_sided = ((items["high"] <= 0.5) | (items["low"] >= 0.5)).astype(bool)
    assert one_sided.sum() == 9
    assert np.allclose(linear[one_sided], 0, atol=1e-12)
    assert np.all(linear[~one_sided] > 0.09)
    assert np.all(entropy > 0.05)
    with pytest.raises(ValueError, match="low < prior < high"):
        observers.check_values({**items, "low": items["prior"]}, "linear")
    with pytest.raises(ValueError, match="Unknown certainty"):
        observers.certainty(0.5, "quadratic")


@pytest.mark.parametrize("probes", [False, True])
def test_designs_have_24_measurable_checkpoints(probes):
    for build, model in ((design.corroboration, "dependence"), (design.disclosure, "disclosure")):
        items = build(probes=probes)
        assert len(items["kind"]) == 24
        assert (items["kind"] == "probe").sum() == (6 if probes else 0)
        forecast = items["kind"] != "probe"
        for disposition in (0.0, 0.5, 1.0):
            p = sigmoid(fit.REPORT_MODELS[model](items, disposition, 1.0))[forecast]
            assert np.all((p >= 0.03) & (p <= 0.97))
    assert len(design.checks()["prior"]) == 24


def test_report_and_wtp_likelihood_inputs():
    with pytest.raises(ValueError, match="whole percentages"):
        report_edges([0.555])
    with pytest.raises(ValueError, match="between zero and one"):
        report_edges([1.2])
    lower, upper = report_edges([0.0, 1.0])
    assert lower[0] == -np.inf and upper[1] == np.inf
    # Zero is censored: every nonpositive latent value is reported as zero.
    assert wtp_log_likelihood(np.array([-20.0]), np.array([0.0]), 2.0) > -1e-9
    with pytest.raises(ValueError, match="whole, nonnegative"):
        wtp_log_likelihood(np.array([1.0]), np.array([-1.0]), 2.0)


def test_low_noise_respondent_is_recovered():
    rng = np.random.default_rng(3)
    items = design.corroboration(probes=True)
    latent = observers.corroboration(items, 0.35, 1.2) + 0.15 * (items["kind"] != "probe")
    result = fit.fit_reports("dependence", items, sample_reports(latent, 0.05, rng))
    parameters = result["parameters"]
    assert abs(parameters["disposition"]["mean"] - 0.35) < 0.05
    assert abs(parameters["gamma"]["mean"] - 1.2) < 0.1
    assert abs(parameters["bias"]["mean"] - 0.15) < 0.1


def test_small_validation_run_is_immutable(tmp_path):
    results = validate(7, respondents=10, model_datasets=5, boundary_repetitions=1)
    gates = check_gates(results)
    assert set(gates["checks"]) == {
        "corroboration_disposition_recovery",
        "corroboration_model_recovery",
        "corroboration_learning_detection",
        "corroboration_learning_start_recovery",
        "corroboration_cue_recovery",
        "disclosure_disposition_recovery",
        "disclosure_model_recovery",
        "disclosure_learning_detection",
        "disclosure_learning_start_recovery",
        "disclosure_cue_recovery",
        "certainty_value_recovery_linear",
        "certainty_value_recovery_entropy",
    }
    output = tmp_path / "run"
    value = run(output, seed=7, respondents=10, model_datasets=5, boundary_repetitions=1)
    saved = json.loads((output / "validation.json").read_text())
    assert saved["plan"]["implementation_sha256"] == value["plan"]["implementation_sha256"]
    assert len(saved["plan"]["designs"]["checks"]["prior"]) == 24
    with pytest.raises(ValueError, match="empty output directory"):
        run(output, seed=7, respondents=10, model_datasets=5, boundary_repetitions=1)
    with pytest.raises(ValueError, match="at least 10 respondents"):
        validate(7, respondents=3)


def test_revealed_structures_update_a_learned_base_rate():
    items = design.corroboration(probes=True)
    posterior = observers.structure_posterior("corroboration", items, 0.8)
    single = items["kind"] == "single"
    conflict = (items["kind"] == "pair") & (items["report_a"] != items["report_b"])
    assert np.all(np.isnan(posterior[single])) and np.allclose(posterior[conflict], 0)
    order = [5, 8, 0, 9, 10] + [i for i in range(24) if i not in (5, 8, 0, 9, 10)]
    revealed = [None] * 24
    revealed[5], revealed[8], revealed[9] = False, True, True
    successes, trials = observers.revealed_counts(order, revealed)
    assert (successes[5], trials[5]) == (0, 0)
    assert (successes[0], trials[0]) == (1, 2)  # The single item reveals nothing.
    assert (successes[10], trials[10]) == (2, 3)
    assert observers.learned(0.5, 2.0, 2, 3) == pytest.approx(0.6)
    assert observers.learned(0.5, 1024.0, 2, 3) == pytest.approx(0.5, abs=1e-3)


def test_learning_respondent_is_detected_and_start_recovered():
    rng = np.random.default_rng(5)
    items = design.disclosure(probes=True)
    posterior = observers.structure_posterior("disclosure", items, 0.8)
    revealed = [bool(rng.random() < p) for p in posterior]
    order = rng.permutation(24)
    successes, trials = observers.revealed_counts(order, revealed)
    fits = {}
    for strength in (2.0, 1024.0):
        delta = observers.learned(0.5, strength, successes, trials)
        reports = sample_reports(observers.disclosure(items, delta, 1.0), 0.05, rng)
        fits[strength] = fit.fit_learning("disclosure", items, reports, successes, trials)
    assert fits[2.0]["learning_probability"] > 0.9
    assert fits[1024.0]["learning_probability"] < 0.1
    assert fits[1024.0]["parameters"]["start"]["mean"] == pytest.approx(0.5, abs=0.05)


@pytest.mark.parametrize(
    "build, observer, model",
    [
        (design.corroboration_cues, observers.corroboration, "dependence"),
        (design.disclosure_cues, observers.disclosure, "disclosure"),
    ],
)
def test_cue_modules_recover_a_disposition_per_description(build, observer, model):
    items = build()
    assert len(items["kind"]) == 24
    assert sorted(set(items["slot"].tolist())) == [-1, 0, 1, 2, 3, 4]
    assert all((items["kind"][items["slot"] == s] == "rate").sum() == 1 for s in range(5))
    measured = ~np.isin(items["kind"], ("probe", "rate"))
    for disposition in (0.0, 1.0):
        p = sigmoid(observer(items, disposition, 1.0))[measured]
        assert np.all((p >= 0.03) & (p <= 0.97))
    truth = [0.1, 0.3, 0.5, 0.7, 0.9]
    latent = observers.cue_observer(observer, items, truth, 1.0)
    rate = items["kind"] == "rate"
    assert np.allclose(sigmoid(latent[rate]), truth, atol=1e-6)
    reports = sample_reports(latent, 0.05, np.random.default_rng(1))
    result = fit.fit_cues(model, items, reports)
    implied = [s["implied"]["mean"] for s in result["slots"]]
    assert np.allclose(implied, truth, atol=0.05)
    stated = [s["stated"][0] for s in result["slots"]]
    assert np.allclose(stated, truth, atol=0.02)
