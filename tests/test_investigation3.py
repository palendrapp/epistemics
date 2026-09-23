import json
from pathlib import Path

import numpy as np
import pytest

from epistemics.investigation2.inference import prediction_vector as hard_predictions
from epistemics.investigation2.service import fingerprint as old_fingerprint
from epistemics.investigation3.battery import public_trial
from epistemics.investigation3.inference import (
    GRID,
    marginal_log_likelihood,
    prepared,
    report_log_likelihood,
    starting_states,
)
from epistemics.investigation3.models import Assignment, Manifest, Report, Trial
from epistemics.investigation3.simulation import cases, synthetic

PARTICIPANT = {"kind": "human", "subject_id": "private:test-human"}


@pytest.mark.parametrize("offset", [-6, 0, 6])
def test_review_status_is_distinct_from_initial_verification(offset):
    from epistemics.investigation3.world import generate

    a = Assignment(assignment_id="test", seed=23, family="review", offset=offset)
    w = generate(a.seed, offset)
    before = public_trial(a, w, 1)
    after = public_trial(a, w, 3, "stop")
    assert not before.transcription_verified_at_start and not before.transcription_reviewed
    assert not after.transcription_verified_at_start and after.transcription_reviewed
    assert "not yet" not in after.documents[1]["text"]
    assert "transcription_checked" not in after.model_dump()
    assert "separate from the displayed archive" in before.instructions
    assert "0.65 means 65%" in before.instructions


def test_old_implementation_remains_exactly_frozen():
    assert old_fingerprint() == "b1901b04d1bf94b1eddb9318dda199de8e7669c6cd3900745ea601ba170f30be"


def test_noisy_start_preserves_uncertainty_and_valid_endpoints():
    t = cases(23)[0][0]
    for report in ([0, 0, 0], [1, 1, 1], [0.4, 0.3, 0.8]):
        states, weights = starting_states(t, "noisy_report", report)
        assert states.shape == (27, 480)
        assert np.isfinite(states).all() and np.isfinite(weights).all()
        assert weights.sum() == pytest.approx(1)
        assert (weights > 0).sum() > 1
    with pytest.raises(ValueError, match="Unknown"):
        starting_states(t, "unknown", [0.5] * 3)


def test_latent_start_is_marginalized_jointly_across_an_episode():
    observed = np.array([0.9, 0.1])
    components = np.array([[0.9, 0.1], [0.1, 0.9]])
    weights = np.array([0.5, 0.5])
    ll = report_log_likelihood(observed, components)
    expected = np.log(np.sum(weights * np.exp(ll.sum(axis=1))))
    wrong = np.log(np.sum(weights[:, None] * np.exp(ll), axis=0)).sum()
    assert marginal_log_likelihood(observed, components, weights) == pytest.approx(expected)
    assert abs(expected - wrong) > 0.5


def test_future_answers_do_not_change_start_weights_and_hard_model_is_preserved():
    observations = synthetic(cases(23)[0], np.random.default_rng(7))
    _, components, weights = prepared(observations, "noisy_report")
    changed = [o.model_copy(deep=True) for o in observations]
    changed[2].answer.growth_probability = 0.99
    _, new_components, new_weights = prepared(changed, "noisy_report")
    assert new_weights == pytest.approx(weights)
    assert new_components == pytest.approx(components)
    _, hard, w = prepared(observations, "hard_report")
    from epistemics.investigation3.inference import answer_vector

    for index in (0, 45, 98):
        coupling, rate = GRID[index]
        expected = hard_predictions(
            [o.trial for o in observations],
            answer_vector(observations[0].answer),
            coupling=coupling,
            response_rate=rate,
        )
        assert w @ hard[index] == pytest.approx(expected, abs=1e-12)


def test_current_schemas():
    from epistemics.passport.investigation import InvestigationCollection
    from epistemics.passport.models import InvestigationPassport

    for model, name in [
        (Manifest, "investigation.v3.json"),
        (Report, "investigation-report.v3.json"),
        (Trial, "investigation-trial.v3.json"),
        (InvestigationCollection, "investigation-collection.v1.json"),
        (InvestigationPassport, "passport.v3.json"),
    ]:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        assert json.loads((Path("schemas") / name).read_bytes()) == schema
