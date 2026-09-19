"""Reference agents operate exclusively on the public prompt."""

from epistemics.battery import hmm_predictions, logit, sigmoid, source_posterior
from epistemics.models import Answer, Trial


def answer_trial(
    trial: Trial, *, prior_weight: float = 1, evidence_weight: float = 1, hazard: float = 0.1
) -> Answer:
    s = trial.stimulus
    if trial.task == "evidence_integration":
        return Answer(
            probability=sigmoid(
                prior_weight * logit(s["prior_h"])
                + evidence_weight * (2 * s["signal"] - 1) * logit(s["sensor_accuracy"])
            )
        )
    if trial.task == "source_reliability":
        probability, source = source_posterior(s["prior_h"], s["prior_valid"], s["signal"])
        return Answer(probability=probability, source_probability=source)
    # Appending a dummy outcome asks the filter for the next pre-outcome prediction.
    return Answer(probability=hmm_predictions(s["past_outcomes"] + [0], hazard)[-1])
