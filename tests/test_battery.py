import math

import numpy as np
import pytest

from epistemics.analysis import fit_sequence
from epistemics.baselines import answer_trial
from epistemics.battery import (
    delta_predictions,
    generate_battery,
    hmm_predictions,
    source_posterior,
)
from epistemics.cli import demo
from epistemics.models import Answer, Observation


def test_joint_bayes_accounts_for_an_unreliable_source():
    # Enumerated posterior: P(H=1,E=0)=.8*(.75*.1+.25*.5)=.16;
    # P(H=0,E=0)=.2*(.75*.9+.25*.5)=.16.
    hypothesis, validity = source_posterior(0.8, 0.75, 0)
    assert hypothesis == pytest.approx(0.5)
    assert validity == pytest.approx(0.195 / 0.32)
    assert source_posterior(0.8, 0, 0) == pytest.approx((0.8, 0))


def test_hmm_prediction_precedes_outcome_and_switch():
    assert hmm_predictions([1, 0], 0.1) == pytest.approx([0.5, 0.644])
    assert hmm_predictions([0, 1], 0.1) == pytest.approx([0.5, 0.356])
    assert hmm_predictions([1, 1, 0], 0.5) == pytest.approx([0.5] * 3)
    assert delta_predictions([1, 0], 0.2) == pytest.approx([0.5, 0.6])


def test_generation_is_replayable_and_has_balanced_conditions():
    trials = generate_battery(912)
    assert trials == generate_battery(912)
    assert trials != generate_battery(913)
    assert len(trials) == 88
    assert len({t["trial"]["trial_id"] for t in trials}) == 88
    assert [
        sum(t["trial"]["task"] == task for t in trials)
        for task in ["evidence_integration", "source_reliability", "reversal_learning"]
    ] == [24, 16, 48]
    for i, t in enumerate(trials[40:]):
        assert t["trial"]["stimulus"]["past_outcomes"] == [
            a["truth"]["outcome"] for a in trials[40 : 40 + i]
        ]


@pytest.mark.parametrize("prior,evidence", [(1, 1), (0.4, 1.5), (1.7, 0.25)])
def test_recovers_known_behavioral_weights(prior, evidence):
    report = demo(prior_weight=prior, evidence_weight=evidence)
    assert report.parameters["prior_weight"].estimate == pytest.approx(prior)
    assert report.parameters["evidence_weight"].estimate == pytest.approx(evidence)
    assert report.parameters["source_update_weight"].estimate == pytest.approx(1)
    assert report.model_fits["hmm_subjective_hazard"].parameter == pytest.approx(0.1)
    if prior == evidence == 1:
        assert all(m.reference_rmse < 1e-12 for m in report.metrics.values())


def test_recovery_with_report_noise():
    from epistemics.analysis import regression
    from epistemics.battery import logit

    rng = np.random.default_rng(5)
    trials = generate_battery(1)[:24]
    x = [
        [
            1,
            logit(t["trial"]["stimulus"]["prior_h"]),
            (2 * t["trial"]["stimulus"]["signal"] - 1)
            * logit(t["trial"]["stimulus"]["sensor_accuracy"]),
        ]
        for t in trials
    ]
    y = np.asarray(x) @ [0.1, 0.6, 1.4] + rng.normal(0, 0.05, len(x))
    params = regression(x, y, ["bias", "prior", "evidence"])
    assert params["prior"].estimate == pytest.approx(0.6, abs=0.05)
    assert params["evidence"].estimate == pytest.approx(1.4, abs=0.05)


@pytest.mark.parametrize("hazard", [0.02, 0.1, 0.3])
def test_sequential_parameter_recovery_and_no_heldout_fit_leakage(hazard):
    observations = []
    for t in generate_battery(42)[40:]:
        o = Observation(**t, answer=Answer(probability=0.5), answered_at="test")
        o.answer = answer_trial(o.trial, hazard=hazard)
        observations.append(o)
    result = fit_sequence(observations)["hmm_subjective_hazard"]
    assert result.parameter == pytest.approx(hazard)
    assert result.heldout_rmse < 1e-12
    for o in observations[32:]:
        o.answer = Answer(probability=1.0)
    modified = fit_sequence(observations)["hmm_subjective_hazard"]
    assert modified.parameter == result.parameter
    assert modified.heldout_rmse > result.heldout_rmse


@pytest.mark.parametrize("value", [math.nan, math.inf, -0.1, 1.1, "0.5", True])
def test_rejects_invalid_probabilities(value):
    with pytest.raises(ValueError):
        Answer(probability=value)
