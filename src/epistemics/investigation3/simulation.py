"""Recovery and new-case checks for the declared initial-response alternatives."""

import numpy as np

from epistemics.discovery.world import normalize
from epistemics.investigation.inference import simulate_reports
from epistemics.investigation3 import ANALYSIS_VERSION, BATTERY_VERSION
from epistemics.investigation3.battery import public_trial
from epistemics.investigation3.design import schedule
from epistemics.investigation3.inference import (
    FEATURES,
    INITIAL_REPORT_SD,
    INITIALIZATIONS,
    TILT_WEIGHTS,
    TILTS,
    best_query,
    expectation_vector,
    expectations,
    fit,
    initial,
    observed_vector,
    posterior,
    predictions,
    projected,
    query_values,
    trajectory,
)
from epistemics.investigation3.models import MEASUREMENTS, Answer, Observation
from epistemics.investigation3.world import generate


def response(trial):
    p = np.round(projected(posterior(trial), trial), 2)
    extra = (
        {q: {k: round(v, 2) for k, v in e.items()} for q, e in expectations(trial).items()}
        if trial.expectation_queries
        else None
    )
    return Answer(
        growth_probability=float(p[0]),
        audit_understatement_probability=float(p[1]),
        backlog_high_probability=float(p[2]),
        decision="invest" if (trial.gain + trial.loss) * p[0] > trial.loss else "hold",
        query=best_query(query_values(trial)) if trial.index == 1 else None,
        expectations=extra,
    )


def cases(seed, worlds=12):
    result = []
    for batch in range(worlds // 12):
        for assignment in schedule(seed + batch):
            world = generate(assignment.seed, assignment.offset)
            branch = best_query(query_values(public_trial(assignment, world, 1)))
            result.append(
                [public_trial(assignment, world, i, branch if i >= 2 else None) for i in range(4)]
            )
    return result


def synthetic(trials, rng, coupling=1.0, response_rate=1.0, initialization="noisy_report"):
    if initialization not in INITIALIZATIONS:
        raise ValueError("Unknown initialization")
    start = initial(trials[0])
    if initialization == "noisy_report":
        with np.errstate(divide="ignore"):
            start = normalize(
                np.log(start) + FEATURES @ TILTS[rng.choice(len(TILTS), p=TILT_WEIGHTS)]
            )
    first = simulate_reports(start @ FEATURES, rng, sd=INITIAL_REPORT_SD)
    if initialization == "hard_report":
        start = initial(trials[0], first)
    raw = trajectory(trials, start=start, coupling=coupling, response_rate=response_rate)
    values = simulate_reports(raw, rng)
    values[0] = first
    extra = None
    if trials[1].expectation_queries:
        e = expectations(
            trials[1], start=start, coupling=coupling, response_rate=response_rate, current=raw[1]
        )
        v = simulate_reports(expectation_vector(e), rng).reshape(3, 3)
        extra = {
            q: dict(
                zip(("yes_probability", "growth_if_yes", "growth_if_no"), row.tolist(), strict=True)
            )
            for q, row in zip(MEASUREMENTS, v, strict=True)
        }
    return [
        Observation(
            trial=t,
            answer=Answer(
                growth_probability=float(p[0]),
                audit_understatement_probability=float(p[1]),
                backlog_high_probability=float(p[2]),
                decision="invest" if (t.gain + t.loss) * p[0] > t.loss else "hold",
                query=trials[2].selected_query if i == 1 else None,
                expectations=extra if i == 1 else None,
            ),
            answered_at="synthetic",
        )
        for i, (t, p) in enumerate(zip(trials, values, strict=True))
    ]


def validation(*, seed=20260923, worlds=24, repetitions=4):
    if worlds not in (12, 24, 36, 48) or not 2 <= repetitions <= 10:
        raise ValueError("Use 12,24,36 or 48 cases and 2..10 repetitions")
    train, test = cases(seed, worlds), cases(seed + 100000, worlds)
    rng = np.random.default_rng(seed)
    runs = []
    confusion = {m: {n: 0 for n in INITIALIZATIONS} for m in INITIALIZATIONS}
    for mode in INITIALIZATIONS:
        for coupling, rate in ((0.0, 1.0), (1.0, 0.5), (0.3, 0.7), (0.75, 0.45)):
            for repeat in range(repetitions):
                obs = [synthetic(ts, rng, coupling, rate, mode) for ts in train]
                estimates = {m: fit(obs, initialization=m) for m in INITIALIZATIONS}
                winner = max(estimates, key=lambda m: estimates[m]["report_log_likelihood"])
                confusion[mode][winner] += 1
                fitted = estimates[mode]
                new = [synthetic(ts, rng, coupling, rate, mode) for ts in test]
                actual = np.concatenate([observed_vector(case) for case in new])
                predicted = predictions(
                    new,
                    fitted["coupling_grid_estimate"],
                    fitted["response_rate_grid_estimate"],
                    initialization=mode,
                )
                runs.append(
                    {
                        "initialization": mode,
                        "repeat": repeat,
                        "generating_coupling": coupling,
                        "generating_response_rate": rate,
                        "estimated_coupling": fitted["coupling_grid_estimate"],
                        "estimated_response_rate": fitted["response_rate_grid_estimate"],
                        "new_case_rmse_pp": float(
                            np.sqrt(np.mean((predicted - actual) ** 2)) * 100
                        ),
                    }
                )
    maes = {
        m: {
            p: float(
                np.mean(
                    [
                        abs(r["generating_" + p] - r["estimated_" + p])
                        for r in runs
                        if r["initialization"] == m
                    ]
                )
            )
            for p in ("coupling", "response_rate")
        }
        for m in INITIALIZATIONS
    }
    checks = {f"{m}_coupling_mae_at_most_025": v["coupling"] <= 0.25 for m, v in maes.items()} | {
        f"{m}_report_rate_mae_at_most_015": v["response_rate"] <= 0.15 for m, v in maes.items()
    }
    return {
        "schema_version": "epistemics.investigation-validation.v3",
        "battery_version": BATTERY_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "response_origin": "synthetic",
        "seed": seed,
        "cases_per_partition": worlds,
        "repetitions": repetitions,
        "passed": all(checks.values()),
        "checks": checks,
        "parameter_mean_absolute_errors": maes,
        "initialization_confusion": confusion,
        "recovery_rates": {
            m: confusion[m][m] / sum(confusion[m].values()) for m in INITIALIZATIONS
        },
        "parameter_runs": runs,
        "plan": {
            "initial_response": "working baseline, hard constraint, or 27 latent log-linear prior tilts with rounded logistic-normal initial report SD .8; noisy observer integrates per-episode states",
            "later_reports": "rounded independent logistic-normal SD .3; branch fixed by public reference",
            "partition": "Different public worlds by seed; entire matched pairs stay within each partition",
            "gates": "Each initialization's coupling MAE <= .25 and report-rate MAE <= .15; thresholds fixed before simulation",
            "limitations": "Model-family recovery only. Initialization confusion and new-case error are reported, not used to select a winning product model. No empirical prediction, calibrated grid-interval coverage, choice-policy or intervention claim.",
        },
    }
