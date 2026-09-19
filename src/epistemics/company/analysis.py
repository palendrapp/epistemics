"""Constrained descriptive fits. Outcomes never enter fitted response parameters."""

import math

import numpy as np

from epistemics.battery import logit, sigmoid
from epistemics.company.inference import STATES, posterior
from epistemics.company.models import CompanyFit, CompanyMetric, CompanyObservation
from epistemics.models import Parameter

FIELDS = {
    "growth_probability": "growth",
    "margin_probability": "margin",
    "temporary_probability": "temporary",
    "source_probability": "source_validity",
}
TRAIN_EPISODES = [f"company-{i:02d}" for i in range(1, 5)]
HELDOUT_EPISODES = ["company-05", "company-06"]
LIMITATIONS = [
    "One authored scenario family, six generated episodes; held-out episodes do not establish transfer to other scenario families.",
    "This is controlled inference with disclosed likelihoods and structured claims; it also measures arithmetic and instruction following.",
    "Repeated checkpoints share one outcome per company; there are six episodes, not 54 independent outcome replications. No population confidence interval is reported.",
    "Output gain and retention are fixed at 1. Input weighting and report extremity are not separately identified by these forecasts.",
    "Negativity is target-relative diagnosticity: incremental likelihood-ratio sign, or standalone sign for redundant items; it is not lexical sentiment.",
    "Source-framing effects, output-framing effects, loss-weight parameters and active information acquisition are not fitted in this first pilot.",
    "Weighted model fits probability-report increments; auxiliary-prior alternative fits growth-probability levels. Both are compared on held-out growth reports.",
    "Quantile width and decision/report agreement are descriptive; they do not identify internal confidence or a utility function.",
    "Rich auxiliary/source probes may affect behavior. Context resets are host-controlled; episode instructions do not erase an agent's context.",
    "Agent identity and execution are operator assertions. Local filesystem access can expose hidden states; use an isolated evaluator for independent studies.",
]


def weighted_predictions(observations, positive=1.0, negative=1.0, duplicate=0.0):
    result = []
    z = 0.0
    for o in observations:
        if o.trial.step == 0:
            z = logit(o.trial.dossier.world.prior_growth)
        else:
            t = o.truth
            evidence = (1 - duplicate) * t.incremental_log_lr + duplicate * t.standalone_log_lr
            z += (negative if t.negative else positive) * evidence
        result.append(sigmoid(z))
    return np.asarray(result)


def fit_models(observations: list[CompanyObservation]):
    train = np.asarray([o.trial.episode_id in TRAIN_EPISODES for o in observations])
    reports = np.asarray([o.answer.growth_probability for o in observations])
    rows, target, signs, gaps = [], [], [], []
    previous = 0.0
    for o, use in zip(observations, train, strict=True):
        current = logit(o.answer.growth_probability)
        if o.trial.step and use:
            rows.append(o.truth.incremental_log_lr)
            gaps.append(o.truth.standalone_log_lr - o.truth.incremental_log_lr)
            signs.append(o.truth.negative)
            target.append(current - previous)
        previous = current
    inc, gap, neg, target = map(np.asarray, (rows, gaps, signs, target))
    best = None
    for duplicate in np.linspace(0, 1, 101):
        x = inc + duplicate * gap
        design = np.column_stack([x * ~neg, x * neg])
        weights = np.asarray(
            [
                np.clip(np.dot(col, target) / np.dot(col, col), 0.05, 4.0)
                if np.dot(col, col) > 1e-12
                else 1.0
                for col in design.T
            ]
        )
        error = float(np.mean((design @ weights - target) ** 2))
        if best is None or error < best[0]:
            best = (error, float(duplicate), weights, design)
    _, duplicate, weights, design = best
    sensitivity = np.column_stack([design, np.where(neg, weights[1], weights[0]) * gap])
    identified = np.linalg.matrix_rank(sensitivity) == 3
    warnings = ["Four training episodes; no population or between-run interval."]
    if not identified:
        warnings.append(
            "Rank-deficient sensitivity: these parameters cannot all be recovered in this run."
        )
    if any(w <= 0.05 or w >= 4 for w in weights):
        warnings.append("An evidence weight is on the fitted bound [0.05,4].")
    if np.any((reports[train] == 0) | (reports[train] == 1)):
        warnings.append(
            "Endpoint reports are clipped to [1e-6,1-1e-6] for descriptive logit fitting."
        )
    params = {
        "positive_weight": float(weights[0]),
        "negative_weight": float(weights[1]),
        "negative_log_multiplier": math.log(weights[1] / weights[0]),
        "duplicate_weight": duplicate,
    }

    def fit(predictions, parameters, method, valid=True, notes=()):
        return CompanyFit(
            parameters=parameters,
            train_rmse=float(np.sqrt(np.mean((predictions[train] - reports[train]) ** 2))),
            heldout_rmse=float(np.sqrt(np.mean((predictions[~train] - reports[~train]) ** 2))),
            train_episodes=TRAIN_EPISODES,
            heldout_episodes=HELDOUT_EPISODES,
            identified=valid,
            method=method,
            warnings=list(notes),
        )

    reference = np.asarray([o.truth.reference.growth_probability for o in observations])
    fits = {"reference_joint": fit(reference, {}, "Fixed joint H,M,A,V model with public priors")}
    fits["weighted_evidence"] = fit(
        weighted_predictions(observations, weights[0], weights[1], duplicate),
        params,
        "Duplicate grid 0..1 by .01; constrained least squares on logit increments; output gain=retention=1",
        identified,
        warnings,
    )
    # Changing only A's prior odds reweights the full posterior by exp(shift*A).
    joints = np.asarray([posterior(o.trial) for o in observations])
    h = np.asarray([s[0] for s in STATES])
    a = np.asarray([s[2] for s in STATES])
    grid = np.linspace(-3, 3, 61)
    alternatives = []
    for shift in grid:
        q = joints * np.exp(shift * a)
        alternatives.append((q @ h) / q.sum(axis=1))
    alternatives = np.asarray(alternatives)
    errors = np.mean((alternatives[:, train] - reports[train]) ** 2, axis=1)
    ix = int(np.argmin(errors))
    near = grid[errors <= errors[ix] + 0.0001]
    fits["joint_auxiliary_prior"] = fit(
        alternatives[ix],
        {
            "auxiliary_log_odds_shift": float(grid[ix]),
            "near_optimal_low": float(near.min()),
            "near_optimal_high": float(near.max()),
        },
        "Auxiliary prior log-odds shift grid -3..3 by .1; near range uses train MSE <= min + .0001, not a CI",
        bool(np.ptp(alternatives[:, train], axis=0).max() > 1e-6),
        [
            "Source priors and output mapping are fixed; this parameter is conditional on those restrictions."
        ]
        + (["Optimum is on the fitted grid boundary."] if ix in (0, len(grid) - 1) else []),
    )
    parameters = {
        name: Parameter(
            estimate=value,
            method=fits["weighted_evidence"].method,
            n=len(target),
            warnings=warnings,
        )
        for name, value in params.items()
    }
    return parameters, fits


def analyze(observations: list[CompanyObservation]):
    final = np.asarray([o.trial.step == 8 for o in observations])
    metrics = {}
    for field, outcome in FIELDS.items():
        p = np.asarray([getattr(o.answer, field) for o in observations])
        y = np.asarray([getattr(o.truth, outcome) for o in observations])
        ref = np.asarray([getattr(o.truth.reference, field) for o in observations])
        clipped = np.clip(p, 1e-6, 1 - 1e-6)
        loss = -y * np.log(clipped) - (1 - y) * np.log(1 - clipped)
        metrics[field] = CompanyMetric(
            checkpoints=len(p),
            episodes=int(final.sum()),
            brier=float(np.mean((p - y) ** 2)),
            log_loss=float(loss.mean()),
            reference_rmse=float(np.sqrt(np.mean((p - ref) ** 2))),
            final_brier=float(np.mean((p[final] - y[final]) ** 2)),
            final_log_loss=float(loss[final].mean()),
        )
    alignment, regrets, interval_scores, coverages, quantile_losses, redundancies = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    previous = 0.0
    for o in observations:
        a, t, mandate = o.answer, o.truth, o.trial.dossier.mandate
        g, loss = mandate.gain_if_growth_target_met, mandate.loss_if_growth_target_missed
        own_ev = a.growth_probability * g - (1 - a.growth_probability) * loss
        ref_ev = t.reference.growth_probability * g - (1 - t.reference.growth_probability) * loss
        alignment.append((a.decision == "invest") == (own_ev > 1e-12))
        regrets.append(max(0.0, ref_ev) - (ref_ev if a.decision == "invest" else 0.0))
        lo, median, hi = (
            a.growth_quantiles_pct.p10,
            a.growth_quantiles_pct.p50,
            a.growth_quantiles_pct.p90,
        )
        y = t.realized_growth_pct
        interval_scores.append(hi - lo + 10 * max(lo - y, 0) + 10 * max(y - hi, 0))
        coverages.append(lo <= y <= hi)
        quantile_losses.append(
            sum(
                (q - (y < x)) * (y - x)
                for q, x in zip((0.1, 0.5, 0.9), (lo, median, hi), strict=True)
            )
            / 3
        )
        if t.redundant:
            redundancies.append(abs(a.growth_probability - previous))
        previous = a.growth_probability
    diagnostics = {
        "decision_report_agreement": float(np.mean(alignment)),
        "mean_expected_regret_under_public_model": float(np.mean(regrets)),
        "mean_absolute_update_on_redundant_items": float(np.mean(redundancies)),
        "mean_80pct_interval_score": float(np.mean(interval_scores)),
        "mean_quantile_pinball_loss": float(np.mean(quantile_losses)),
        "final_80pct_interval_coverage": float(np.asarray(coverages)[final].mean()),
        "independent_episodes": int(final.sum()),
    }
    parameters, fits = fit_models(observations)
    return metrics, diagnostics, parameters, fits
