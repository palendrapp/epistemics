"""Small, explicit generative tasks. Hidden values never enter an active MCP prompt."""

import hashlib
import itertools
import json
import math
import random
from pathlib import Path

from epistemics.models import Trial

BATTERY_VERSION = "belief-battery/0.1.0"
SPEC = {
    "version": BATTERY_VERSION,
    "evidence_integration": {"priors": [0.2, 0.5, 0.8], "accuracies": [0.6, 0.85], "repeats": 2},
    "source_reliability": {"priors": [0.2, 0.8], "validities": [0.25, 0.75], "repeats": 2},
    "reversal_learning": {"trials": 48, "hazard": 0.1, "low": 0.2, "high": 0.8},
    "scoring": "brier and log-loss; clip to [1e-6, 1-1e-6] only for logs/logits",
    "fitting": "OLS + 200 paired bootstrap draws; temporal 2/3 split for sequential models",
}


def json_bytes(value: object) -> bytes:
    """Internal deterministic Python encoding; report-file hashes use the actual file bytes."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


BATTERY_SHA256 = hashlib.sha256(
    json_bytes(
        {
            "spec": SPEC,
            "sources": {
                name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                for name in ("battery.py", "analysis.py", "models.py")
            },
        }
    )
).hexdigest()


def logit(p: float) -> float:
    p = min(1 - 1e-6, max(1e-6, p))
    return math.log(p / (1 - p))


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x)) if x >= 0 else math.exp(x) / (1 + math.exp(x))


def source_posterior(prior: float, validity: float, signal: int) -> tuple[float, float]:
    """Marginalize H and V jointly. Valid sources have 90% accuracy; invalid ones toss a coin."""
    masses = {
        (h, v): (prior if h else 1 - prior)
        * (validity if v else 1 - validity)
        * ((0.9 if h == signal else 0.1) if v else 0.5)
        for h, v in itertools.product((0, 1), repeat=2)
    }
    total = sum(masses.values())
    return (
        sum(p for (h, _), p in masses.items() if h) / total,
        sum(p for (_, v), p in masses.items() if v) / total,
    )


def hmm_predictions(outcomes: list[int], hazard: float) -> list[float]:
    """Pre-outcome forecasts for a symmetric two-state Markov process."""
    belief = 0.5
    predictions = []
    for outcome in outcomes:
        prediction = 0.2 + 0.6 * belief
        predictions.append(prediction)
        likelihood_high = 0.8 if outcome else 0.2
        likelihood_low = 0.2 if outcome else 0.8
        posterior = (
            belief * likelihood_high / (belief * likelihood_high + (1 - belief) * likelihood_low)
        )
        belief = posterior * (1 - hazard) + (1 - posterior) * hazard
    return predictions


def delta_predictions(outcomes: list[int], alpha: float) -> list[float]:
    belief = 0.5
    predictions = []
    for outcome in outcomes:
        predictions.append(belief)
        belief += alpha * (outcome - belief)
    return predictions


def generate_battery(seed: int) -> list[dict]:
    rng = random.Random(seed)
    trials: list[dict] = []

    def add(task: str, instructions: str, stimulus: dict, truth: dict) -> None:
        index = len(trials)
        trials.append(
            {
                "trial": Trial(
                    trial_id=f"t{index:03d}",
                    task=task,
                    index=index,
                    instructions=instructions,
                    stimulus=stimulus,
                ).model_dump(),
                "truth": truth,
            }
        )

    conditions = list(itertools.product([0.2, 0.5, 0.8], [0.6, 0.85], [0, 1])) * 2
    rng.shuffle(conditions)
    for prior, accuracy, signal in conditions:
        log_lr = (1 if signal else -1) * logit(accuracy)
        posterior = sigmoid(logit(prior) + log_lr)
        add(
            "evidence_integration",
            "This is an independent case. H is binary with the supplied prior. The sensor "
            "reports H correctly with the supplied accuracy for either value of H. "
            "Observe its signal; report P(H=1 | signal) as probability. No source_probability.",
            {"prior_h": prior, "sensor_accuracy": accuracy, "signal": signal},
            {"reference": posterior, "outcome": int(rng.random() < posterior)},
        )

    conditions = list(itertools.product([0.2, 0.8], [0.25, 0.75], [0, 1])) * 2
    rng.shuffle(conditions)
    for prior, validity, signal in conditions:
        posterior, source = source_posterior(prior, validity, signal)
        # Sample the joint conditional distribution so the revealed truths are coherent.
        masses = [
            (
                h,
                v,
                (prior if h else 1 - prior)
                * (validity if v else 1 - validity)
                * ((0.9 if h == signal else 0.1) if v else 0.5),
            )
            for h, v in itertools.product((0, 1), repeat=2)
        ]
        chosen = rng.choices(masses, weights=[m[2] for m in masses])[0]
        add(
            "source_reliability",
            "This is an independent case. H and source validity V are initially independent "
            "with the supplied priors. If V=1 the sensor reports H correctly 90% of the time "
            "for either H. If V=0 its signal is a fair coin independent of H. "
            "After the signal, report P(H=1 | signal) as probability AND "
            "P(V=1 | signal) as source_probability.",
            {
                "prior_h": prior,
                "prior_valid": validity,
                "signal": signal,
                "valid_sensor_accuracy": 0.9,
                "invalid_sensor_p_one": 0.5,
            },
            {
                "reference": posterior,
                "source_reference": source,
                "outcome": chosen[0],
                "source_outcome": chosen[1],
            },
        )

    state = rng.randrange(2)
    outcomes, states = [], []
    for t in range(48):
        if t and rng.random() < 0.1:
            state = 1 - state
        states.append(state)
        outcomes.append(int(rng.random() < (0.8 if state else 0.2)))
    predictions = hmm_predictions(outcomes, 0.1)
    for t, outcome in enumerate(outcomes):
        add(
            "reversal_learning",
            "Forecast the NEXT outcome in this continuing sequence. A hidden regime has "
            "P(outcome=1) of 0.2 or 0.8, initially equally likely. It switches with "
            "probability 0.1 between trials. Outcomes are independent given the regime. "
            "Use only the supplied past outcomes. Report P(next outcome=1) as probability. "
            "No source_probability. Each outcome is revealed only after its forecast.",
            {
                "past_outcomes": outcomes[:t],
                "sequence_index": t,
                "switch_probability": 0.1,
                "low_p": 0.2,
                "high_p": 0.8,
            },
            {"reference": predictions[t], "outcome": outcome, "regime": states[t]},
        )
    return trials
