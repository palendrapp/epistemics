"""Conditional behavioral model; features require only a public checkpoint."""

from dataclasses import dataclass

import numpy as np

from epistemics.predictive.models import AnalysisPlan, PublicCheckpoint

PARAMETERS = ("intercept", "prior_weight", "evidence_weight", "copy_weight")


def logit(p):
    return np.log(p) - np.log1p(-p)


def probability(value):
    return 1 / (1 + np.exp(-np.clip(value, -700, 700)))


def features(checkpoint: PublicCheckpoint):
    """Beta(1,1) source-accuracy reference, one original signal per source.

    This is an explicit evaluator model, not a claim that a participant infers
    the same source model. Copies inherit their original report's likelihood.
    """
    unique, copied, roots = 0.0, 0.0, {}
    for card in checkpoint.evidence:
        if card.based_on is None:
            history = card.original_assessment_history
            accuracy = (history.correct + 1) / (history.total + 2)
            signed = (1 if card.assessment == "meets_target" else -1) * logit(accuracy)
            unique += signed
        else:
            signed = roots[card.based_on]
            copied += signed
        roots[card.document_id] = signed
    return np.array([1.0, logit(checkpoint.prior_probability), unique, copied])


def reference_probability(checkpoint):
    x = features(checkpoint)
    return float(probability(x[1] + x[2]))


@dataclass(frozen=True)
class Row:
    assignment_id: str
    matched_group: str
    split: str
    index: int
    final: bool
    x: tuple[float, ...]
    response: float
    decision: str


def arrays(rows, plan):
    if not rows:
        raise ValueError("No responses to fit")
    x = np.array([r.x for r in rows])
    p = np.array([r.response for r in rows])
    if (
        x.shape != (len(rows), 4)
        or not np.isfinite(x).all()
        or not np.isfinite(p).all()
        or ((p < 0) | (p > 1)).any()
    ):
        raise ValueError("Invalid response or feature values")
    return x, logit(np.clip(p, plan.probability_clip, 1 - plan.probability_clip))


def solve(x, y):
    theta, _, rank, singular = np.linalg.lstsq(x, y, rcond=None)
    if rank != x.shape[1]:
        raise ValueError("Parameters are unidentified: design matrix lacks full rank")
    return theta, float(singular[0] / singular[-1])


def fit_profile(rows: list[Row], plan: AnalysisPlan, *, seed=0, bootstrap=True):
    if {r.split for r in rows} != {"profile"}:
        raise ValueError("Fit only profile-estimation cases; policy and heldout are reserved")
    x, y = arrays(rows, plan)
    theta, condition = solve(x, y)
    intervals, draws = None, []
    if bootstrap:
        rng = np.random.default_rng(seed)
        groups = sorted({r.matched_group for r in rows})
        indices = {g: [i for i, row in enumerate(rows) if row.matched_group == g] for g in groups}
        for _ in range(plan.bootstrap_draws):
            chosen = np.concatenate([indices[g] for g in rng.choice(groups, len(groups))])
            try:
                draws.append(solve(x[chosen], y[chosen])[0])
            except ValueError:
                continue
        if len(draws) >= 0.8 * plan.bootstrap_draws:
            intervals = {
                name: list(map(float, np.quantile(np.array(draws)[:, i], [0.025, 0.975])))
                for i, name in enumerate(PARAMETERS)
            }
    return {
        "parameters": dict(zip(PARAMETERS, map(float, theta), strict=True)),
        "interval_95": intervals,
        "interval_method": "percentile bootstrap of whole matched groups, including both twins",
        "bootstrap_successful_draws": len(draws),
        "condition_number": condition,
        "n_checkpoints": len(rows),
        "n_matched_groups": len({r.matched_group for r in rows}),
        "endpoint_responses_clipped": sum(r.response in (0, 1) for r in rows),
        "identification_scope": "effective reporting weights conditional on the source model",
    }


def predict(rows, fit):
    theta = np.array([fit["parameters"][name] for name in PARAMETERS])
    return probability(np.array([r.x for r in rows]) @ theta)


def all_reports_baseline(train, test, plan):
    """Individual intercept/prior/one evidence gain, ignoring document dependence."""
    if {r.split for r in train} != {"profile"}:
        raise ValueError("Baseline fitting requires profile cases only")
    x, y = arrays(train, plan)
    coarse = np.column_stack([x[:, 0], x[:, 1], x[:, 2] + x[:, 3]])
    theta, _ = solve(coarse, y)
    t = np.array([r.x for r in test])
    return probability(np.column_stack([t[:, 0], t[:, 1], t[:, 2] + t[:, 3]]) @ theta)


def persistence_baseline(rows):
    previous, predictions = {}, []
    for row in rows:
        predictions.append(previous.get(row.assignment_id, float(probability(row.x[1]))))
        previous[row.assignment_id] = row.response
    return np.array(predictions)


def prediction_metrics(rows, predicted):
    observed = np.array([r.response for r in rows])
    actual_decisions = np.array([r.decision == "act" for r in rows])
    return {
        "probability_rmse": float(np.sqrt(np.mean((predicted - observed) ** 2))),
        "probability_mae": float(np.mean(np.abs(predicted - observed))),
        "decision_accuracy": float(np.mean((predicted > 0.5) == actual_decisions)),
    }


def conditional_task_metrics(rows):
    """Expected terminal scores under the stated reference, not empirical outcomes."""
    final = [r for r in rows if r.final]
    if not final:
        raise ValueError("Terminal observations are required")
    q = probability(np.array([r.x[1] + r.x[2] for r in final]))
    p = np.array([r.response for r in final])
    acts = np.array([r.decision == "act" for r in final])
    utility = np.where(acts, 2 * q - 1, 0)
    return {
        "scope": "terminal_expected_scores_conditional_on_evaluator_model",
        "expected_brier": float(np.mean((p - q) ** 2 + q * (1 - q))),
        "excess_brier": float(np.mean((p - q) ** 2)),
        "expected_decision_regret": float(np.mean(np.maximum(2 * q - 1, 0) - utility)),
    }
