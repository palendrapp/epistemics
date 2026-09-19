"""Descriptive fits to reported probabilities, conditional on explicit task assumptions."""

import numpy as np

from epistemics.battery import delta_predictions, hmm_predictions, logit
from epistemics.models import Metrics, ModelFit, Observation, Parameter


def regression(x: list, y: list, names: list[str], seed: int = 0) -> dict[str, Parameter]:
    design, target = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if np.linalg.matrix_rank(design) != design.shape[1]:
        raise ValueError("The design does not identify the requested parameters")
    weights = np.linalg.lstsq(design, target, rcond=None)[0]
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(200):
        ix = rng.integers(0, len(target), len(target))
        if np.linalg.matrix_rank(design[ix]) == design.shape[1]:
            samples.append(np.linalg.lstsq(design[ix], target[ix], rcond=None)[0])
    intervals = np.quantile(samples, [0.025, 0.975], axis=0)
    return {
        name: Parameter(
            estimate=float(weights[i]),
            interval_95=(float(intervals[0, i]), float(intervals[1, i])),
            method="OLS on clipped log-odds; 200 paired bootstrap draws",
            n=len(target),
            warnings=["Within-run descriptive interval; not between-run/model uncertainty"],
        )
        for i, name in enumerate(names)
    }


def fit_sequence(observations: list[Observation]) -> dict[str, ModelFit]:
    outcomes = [int(o.truth["outcome"]) for o in observations]
    reports = np.asarray([o.answer.probability for o in observations])
    split = len(reports) * 2 // 3
    result = {}
    for name, function, maximum in [
        ("delta_learning_rate", delta_predictions, 1.0),
        ("hmm_subjective_hazard", hmm_predictions, 0.5),
    ]:
        grid = np.linspace(0, maximum, 501)
        predictions = np.asarray([function(outcomes, float(p)) for p in grid])
        mse = np.mean((predictions[:, :split] - reports[:split]) ** 2, axis=1)
        best = int(np.argmin(mse))
        near = grid[mse <= mse[best] + 0.0001]
        result[name] = ModelFit(
            parameter=float(grid[best]),
            train_rmse=float(np.sqrt(mse[best])),
            heldout_rmse=float(
                np.sqrt(np.mean((predictions[best, split:] - reports[split:]) ** 2))
            ),
            train_n=split,
            heldout_n=len(reports) - split,
            near_optimal_range=(float(near.min()), float(near.max())),
        )
    return result


def analyze(observations: list[Observation]) -> tuple[dict, dict, dict]:
    metrics, parameters = {}, {}
    groups = {
        task: [o for o in observations if o.trial.task == task]
        for task in ("evidence_integration", "source_reliability", "reversal_learning")
    }
    for task, group in groups.items():
        p = np.asarray([o.answer.probability for o in group])
        y = np.asarray([o.truth["outcome"] for o in group])
        reference = np.asarray([o.truth["reference"] for o in group])
        clipped = np.clip(p, 1e-6, 1 - 1e-6)
        metrics[task] = Metrics(
            n=len(p),
            brier=float(np.mean((p - y) ** 2)),
            log_loss=float(np.mean(-y * np.log(clipped) - (1 - y) * np.log(1 - clipped))),
            reference_rmse=float(np.sqrt(np.mean((p - reference) ** 2))),
            endpoint_reports=int(np.sum((p == 0) | (p == 1))),
        )
    x, y = [], []
    for o in groups["evidence_integration"]:
        s = o.trial.stimulus
        x.append([1, logit(s["prior_h"]), (2 * s["signal"] - 1) * logit(s["sensor_accuracy"])])
        y.append(logit(o.answer.probability))
    parameters.update(regression(x, y, ["response_bias", "prior_weight", "evidence_weight"]))

    # Separate prior and evidence-update weighting for the auxiliary hypothesis.
    x, y = [], []
    for o in groups["source_reliability"]:
        prior = logit(o.trial.stimulus["prior_valid"])
        x.append([1, prior, logit(o.truth["source_reference"]) - prior])
        y.append(logit(o.answer.source_probability))
    parameters.update(
        regression(x, y, ["source_bias", "source_prior_weight", "source_update_weight"])
    )
    source = groups["source_reliability"]
    p = np.asarray([o.answer.source_probability for o in source])
    y = np.asarray([o.truth["source_outcome"] for o in source])
    clipped = np.clip(p, 1e-6, 1 - 1e-6)
    metrics["source_validity"] = Metrics(
        n=len(source),
        brier=float(np.mean((p - y) ** 2)),
        log_loss=float(np.mean(-y * np.log(clipped) - (1 - y) * np.log(1 - clipped))),
        reference_rmse=float(
            np.sqrt(np.mean((p - [o.truth["source_reference"] for o in source]) ** 2))
        ),
        endpoint_reports=int(np.sum((p == 0) | (p == 1))),
    )
    return metrics, parameters, fit_sequence(groups["reversal_learning"])
