"""Offline model discrimination, parameter recovery, and deliberately wrong models.

Worlds are sampled before responses. No seeds are cherry-picked for discrimination;
the ablation compares measurements on identical simulated trajectories.
"""

import numpy as np

from epistemics.investigation import ANALYSIS_VERSION, BATTERY_VERSION
from epistemics.investigation.battery import PRICE_MENUS, public_trial
from epistemics.investigation.inference import (
    CANDIDATES,
    REPORT_SD,
    best_query,
    forecasts,
    report_log_likelihood,
    simulate_reports,
    trajectory,
)
from epistemics.investigation.models import QUERIES, Assignment
from epistemics.investigation.world import generate


def cases(seed, count):
    rng = np.random.default_rng(seed)
    result = []
    for i, world_seed in enumerate(rng.choice(2**40, count, replace=False)):
        assignment = Assignment(
            assignment_id=f"synthetic-{i}",
            seed=int(world_seed),
            cost_scale=(0.5, 1.0, 4.0)[i % 3],
            price_menu=list(PRICE_MENUS)[(i // len(QUERIES)) % len(PRICE_MENUS)],
            gain=(1.0, 2.0)[i % 2],
        )
        world = generate(assignment.seed)
        branch = QUERIES[i % len(QUERIES)]
        result.append(
            [public_trial(assignment, world, j, branch if j >= 2 else None) for j in range(4)]
        )
    return result


def predictions(episodes, **kwargs):
    return np.array([trajectory(trials, **kwargs) for trials in episodes])


def matched_forecast_check(episodes, rng, repetitions):
    """Match explanatory priors on growth, without using simulated responses.

    Retain the number of worlds where matching was impossible. This is a local
    diagnostic demonstration, not a population recovery claim.
    """
    pairs = []
    for episode in episodes:
        trial = episode[1]
        source = forecasts(trial, source_bias_prior=1.25)
        lo, hi = -6.0, 6.0
        left = forecasts(trial, disruption_prior=lo)[0]
        right = forecasts(trial, disruption_prior=hi)[0]
        if not left <= source[0] <= right:
            continue
        for _ in range(40):
            mid = (lo + hi) / 2
            if forecasts(trial, disruption_prior=mid)[0] < source[0]:
                lo = mid
            else:
                hi = mid
        auxiliary = forecasts(trial, disruption_prior=(lo + hi) / 2)
        pairs.append(
            {
                "trial_id": trial.trial_id,
                "source_bias_prior": 1.25,
                "matched_disruption_prior": (lo + hi) / 2,
                "source_explanation_predictions": source.tolist(),
                "auxiliary_explanation_predictions": auxiliary.tolist(),
            }
        )
    correct = 0
    if pairs:
        predicted = np.array(
            [
                [p[key] for p in pairs]
                for key in ("source_explanation_predictions", "auxiliary_explanation_predictions")
            ]
        )
        for i in range(2):
            for _ in range(repetitions):
                reports = simulate_reports(predicted[i], rng)
                ll = report_log_likelihood(reports[:, 1:], predicted[:, :, 1:]).sum(axis=(1, 2))
                correct += int(np.argmax(ll) == i)
    return {
        "attempted_worlds": len(episodes),
        "matched_worlds": len(pairs),
        "unmatched_worlds": len(episodes) - len(pairs),
        "max_matched_growth_gap_pp": max(
            (
                abs(
                    p["source_explanation_predictions"][0]
                    - p["auxiliary_explanation_predictions"][0]
                )
                * 100
                for p in pairs
            ),
            default=None,
        ),
        "auxiliary_probe_recovery_rate": correct / (2 * repetitions) if pairs else None,
        "pairs": pairs,
        "interpretation": "Source-bias versus disruption prior explanations can have the same growth forecast. Probes compare their observable predictions under this bounded observer; successful matching is a selected diagnostic subset, not an agent population result.",
    }


def validation(*, seed=20260920, worlds=24, repetitions=20):
    if not 8 <= worlds <= 128 or not 3 <= repetitions <= 100:
        raise ValueError("Validation needs 8..128 worlds and 3..100 repetitions")
    rng = np.random.default_rng(seed)
    train_seed, test_seed = (int(v) for v in rng.choice(2**40, 2, replace=False))
    train = cases(train_seed, worlds)
    heldout = cases(test_seed, worlds)
    expected = np.array([predictions(train, model=m) for m in CANDIDATES])
    validation_expected = np.array([predictions(heldout, model=m) for m in CANDIDATES])
    confusion = {m: {other: 0 for other in CANDIDATES} for m in CANDIDATES}
    final_only = {m: {other: 0 for other in CANDIDATES} for m in CANDIDATES}
    runs = []
    for i, model in enumerate(CANDIDATES):
        for repeat in range(repetitions):
            reports = simulate_reports(expected[i], rng)
            ll = report_log_likelihood(reports, expected).sum(axis=(1, 2, 3))
            narrow_ll = report_log_likelihood(reports[:, 3, 0], expected[:, :, 3, 0]).sum(axis=1)
            recovered = int(np.argmax(ll))
            confusion[model][CANDIDATES[recovered]] += 1
            final_only[model][CANDIDATES[int(np.argmax(narrow_ll))]] += 1
            new_reports = simulate_reports(validation_expected[i], rng)
            rmse = float(np.sqrt(np.mean((new_reports - validation_expected[recovered]) ** 2)))
            runs.append(
                {
                    "generating_model": model,
                    "repeat": repeat,
                    "selected_from_training": CANDIDATES[recovered],
                    "new_world_report_rmse_pp": 100 * rmse,
                }
            )
    # Recover an archive-weight parameter rather than interpreting candidate labels
    # as sufficient validation. Report off-grid and near-baseline cases explicitly.
    grid = np.linspace(0, 2, 41)
    grid_predictions = np.array([predictions(train, archive_weight=float(w)) for w in grid])
    parameters = []
    for weight in (0.37, 0.68, 0.91, 1.0, 1.09, 1.33, 1.73):
        true_train = predictions(train, archive_weight=weight)
        true_heldout = predictions(heldout, archive_weight=weight)
        for repeat in range(repetitions):
            reports = simulate_reports(true_train, rng)
            ll = report_log_likelihood(reports, grid_predictions).sum(axis=(1, 2, 3))
            posterior = np.exp(ll - max(ll))
            posterior /= posterior.sum()
            estimate = float(grid[np.argmax(ll)])
            cumulative = np.cumsum(posterior)
            interval = [
                float(grid[min(np.searchsorted(cumulative, p), len(grid) - 1)])
                for p in (0.025, 0.975)
            ]
            new_prediction = predictions(heldout, archive_weight=estimate)
            new_report = simulate_reports(true_heldout, rng)
            parameters.append(
                {
                    "generating_archive_weight": weight,
                    "repeat": repeat,
                    "estimate": estimate,
                    "absolute_error": abs(estimate - weight),
                    "grid_interval_95": interval,
                    "covered": interval[0] <= weight <= interval[1],
                    "boundary_mass": float(posterior[0] + posterior[-1]),
                    "new_world_report_rmse_pp": float(
                        np.sqrt(np.mean((new_report - new_prediction) ** 2)) * 100
                    ),
                }
            )
    random_reports = np.round(rng.uniform(0, 1, expected.shape[1:]), 2)
    incompatible_rmse = float(
        min(np.sqrt(np.mean((p - random_reports) ** 2)) for p in expected) * 100
    )
    # This stress is outside the fitted independence assumption; retain performance
    # rather than claiming a nominal interval or a new mechanism from residuals.
    biased_reports = simulate_reports(expected[0], rng)
    biased_reports = np.round(
        np.clip(biased_reports + rng.normal(0, 0.12, (worlds, 1, 1)), 0, 1), 2
    )
    stress_ll = report_log_likelihood(biased_reports, expected).sum(axis=(1, 2, 3))
    pairwise = {
        f"{a}__{b}": float(np.sqrt(np.mean((expected[i] - expected[j]) ** 2)) * 100)
        for i, a in enumerate(CANDIDATES)
        for j, b in enumerate(CANDIDATES)
        if i < j
    }
    recovery_rates = {m: confusion[m][m] / repetitions for m in CANDIDATES}
    parameter_mae = float(np.mean([p["absolute_error"] for p in parameters]))
    checks = {
        "each_candidate_recovered_at_least_80_percent": min(recovery_rates.values()) >= 0.8,
        "archive_weight_mean_absolute_error_at_most_025": parameter_mae <= 0.25,
        "new_world_mean_report_rmse_at_most_8pp": np.mean(
            [r["new_world_report_rmse_pp"] for r in runs]
        )
        <= 8,
        "incompatible_reports_exceed_8pp_adequacy_limit": incompatible_rmse > 8,
    }
    matched = matched_forecast_check(train, rng, repetitions)
    checks["matched_forecast_contrast_available_in_at_least_half_the_worlds"] = (
        matched["matched_worlds"] >= worlds / 2
    )
    checks["matched_forecast_auxiliary_probe_recovery_at_least_80_percent"] = (
        matched["auxiliary_probe_recovery_rate"] is not None
        and matched["auxiliary_probe_recovery_rate"] >= 0.8
    )
    return {
        "schema_version": "epistemics.investigation-validation.v1",
        "battery_version": BATTERY_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "response_origin": "synthetic",
        "seed": seed,
        "worlds_per_partition": worlds,
        "repetitions": repetitions,
        "training_generator_seed": train_seed,
        "new_world_generator_seed": test_seed,
        "passed": bool(all(checks.values())),
        "checks": {k: bool(v) for k, v in checks.items()},
        "plan": {
            "report_sd": REPORT_SD,
            "rounding": 0.01,
            "candidate_prior": "Equal, fixed candidates; maximum likelihood selection on training worlds.",
            "archive_grid": grid.tolist(),
            "parameter_prior": "Uniform grid; report gain fixed at 1.",
            "queries": "Balanced preassigned branches for model discrimination, conditioned on observed branch; not a recovery test of a free research-policy parameter.",
            "selection": "Independent randomly sampled whole-world partitions, no outcome-dependent seed selection.",
            "inference_limit": "Conditional synthetic checks; not an empirical agent profile or established interval coverage.",
        },
        "confusion": confusion,
        "final_growth_only_confusion": final_only,
        "recovery_rates": recovery_rates,
        "pairwise_prediction_rmse_pp": pairwise,
        "archive_weight_mean_absolute_error": parameter_mae,
        "runs": runs,
        "parameter_runs": parameters,
        "matched_forecast_attribution_check": matched,
        "reference_research_choices": {
            q: sum(best_query(t[1]) == q for t in train + heldout) for q in QUERIES
        },
        "misspecification": {
            "random_reports_best_rmse_pp": incompatible_rmse,
            "episode_correlated_bias_selected_model": CANDIDATES[int(np.argmax(stress_ll))],
            "episode_correlated_bias_best_rmse_pp": float(
                min(np.sqrt(np.mean((p - biased_reports) ** 2)) for p in expected) * 100
            ),
        },
    }
