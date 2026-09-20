"""Offline conditional recovery and new-world checks before empirical collection."""

import numpy as np

from epistemics.investigation.inference import (
    answer_vector,
    report_log_likelihood,
    simulate_reports,
)
from epistemics.investigation2 import ANALYSIS_VERSION, BATTERY_VERSION
from epistemics.investigation2.battery import public_trial
from epistemics.investigation2.design import schedule
from epistemics.investigation2.inference import (
    CANDIDATES,
    best_query,
    expectation_vector,
    expectations,
    fit,
    initial,
    observed_vector,
    posterior,
    prediction_vector,
    projected,
    query_values,
    trajectory,
)
from epistemics.investigation2.models import MEASUREMENTS, Answer, Observation
from epistemics.investigation2.world import generate


def response(trial):
    p = np.round(projected(posterior(trial), trial), 2)
    extra = None
    if trial.expectation_queries:
        extra = {q: {k: round(v, 2) for k, v in e.items()} for q, e in expectations(trial).items()}
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
        for a in schedule(seed + batch):
            w = generate(a.seed, a.offset)
            first = public_trial(a, w, 1)
            # Public reference branches are fixed before generating any responses.
            branch = best_query(query_values(first))
            result.append([public_trial(a, w, i, branch if i >= 2 else None) for i in range(4)])
    return result


def synthetic(trials, rng, coupling=1.0, response_rate=1.0, unretracted=False):
    # Starting reports are observed conditioning variables, not noisy estimates
    # of an identified internal prior. Vary them prospectively across cases.
    baseline = initial(trials[0])
    from epistemics.investigation2.inference import FEATURES

    first = np.round(np.clip(baseline @ FEATURES + rng.uniform(-0.08, 0.08, 3), 0.01, 0.99), 2)
    start = initial(trials[0], first)
    raw = trajectory(
        trials, start=start, coupling=coupling, response_rate=response_rate, unretracted=unretracted
    )
    reports = simulate_reports(raw, rng)
    reports[0] = first
    prospective = None
    if trials[1].expectation_queries:
        expected = expectations(
            trials[1], start=start, coupling=coupling, response_rate=response_rate, current=raw[1]
        )
        v = simulate_reports(expectation_vector(expected), rng).reshape(3, 3)
        prospective = {
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
                expectations=prospective if i == 1 else None,
            ),
            answered_at="synthetic",
        )
        for i, (t, p) in enumerate(zip(trials, reports, strict=True))
    ]


def predictions(observations, coupling=1.0, response_rate=1.0, unretracted=False):
    return np.concatenate(
        [
            prediction_vector(
                [o.trial for o in case],
                answer_vector(case[0].answer),
                coupling=coupling,
                response_rate=response_rate,
                unretracted=unretracted,
            )
            for case in observations
        ]
    )


def validation(*, seed=20260921, worlds=24, repetitions=10):
    if worlds not in (12, 24, 36, 48) or not 2 <= repetitions <= 30:
        raise ValueError("Use 12,24,36 or 48 worlds and 2..30 repetitions")
    train, test = cases(seed, worlds), cases(seed + 100000, worlds)
    rng = np.random.default_rng(seed)
    confusion = {m: {n: 0 for n in CANDIDATES} for m in CANDIDATES}
    parameter_runs = []
    for name, (coupling, rate, ignore) in CANDIDATES.items():
        for _ in range(repetitions):
            obs = [synthetic(ts, rng, coupling, rate, ignore) for ts in train]
            values = np.concatenate([observed_vector(case) for case in obs])
            ll = {
                m: float(report_log_likelihood(values, predictions(obs, c, a, u)).sum())
                for m, (c, a, u) in CANDIDATES.items()
            }
            confusion[name][max(ll, key=ll.get)] += 1
    for coupling, rate in ((0.0, 1.0), (1.0, 1.0), (0.3, 0.7), (0.75, 0.45)):
        for repeat in range(repetitions):
            obs = [synthetic(ts, rng, coupling, rate) for ts in train]
            result = fit(obs)
            new = [synthetic(ts, rng, coupling, rate) for ts in test]
            predicted = predictions(
                new, result["coupling_grid_estimate"], result["response_rate_grid_estimate"]
            )
            actual = np.concatenate([observed_vector(case) for case in new])
            intervals = result["conditional_grid_intervals_95"]
            parameter_runs.append(
                {
                    "generating_coupling": coupling,
                    "generating_response_rate": rate,
                    "repeat": repeat,
                    "estimated_coupling": result["coupling_grid_estimate"],
                    "estimated_response_rate": result["response_rate_grid_estimate"],
                    "conditional_grid_intervals_95": intervals,
                    "coupling_covered": intervals[0][0] <= coupling <= intervals[0][1],
                    "response_rate_covered": intervals[1][0] <= rate <= intervals[1][1],
                    "new_world_report_rmse_pp": float(
                        np.sqrt(np.mean((actual - predicted) ** 2)) * 100
                    ),
                }
            )
    mae = {
        name: float(
            np.mean([abs(r["generating_" + name] - r["estimated_" + name]) for r in parameter_runs])
        )
        for name in ("coupling", "response_rate")
    }
    rates = {m: confusion[m][m] / repetitions for m in CANDIDATES}
    checks = {
        "each_fixed_candidate_recovered_at_least_80_percent": min(rates.values()) >= 0.8,
        "coupling_mean_absolute_error_at_most_020": mae["coupling"] <= 0.2,
        "response_rate_mean_absolute_error_at_most_015": mae["response_rate"] <= 0.15,
        "new_world_rmse_at_most_8pp": np.mean(
            [r["new_world_report_rmse_pp"] for r in parameter_runs]
        )
        <= 8,
    }
    # An explicit outside-family check prevents naming a winner as proof of fit.
    stress = [synthetic(ts, rng) for ts in train]
    pred = predictions(stress)
    random = np.round(rng.uniform(0, 1, len(pred)), 2)
    random_error = min(
        float(np.sqrt(np.mean((random - predictions(stress, c, a, u)) ** 2)) * 100)
        for c, a, u in CANDIDATES.values()
    )
    checks["random_reports_fail_absolute_fit"] = random_error > 8
    return {
        "schema_version": "epistemics.investigation-validation.v2",
        "battery_version": BATTERY_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "response_origin": "synthetic",
        "seed": seed,
        "worlds_per_partition": worlds,
        "repetitions": repetitions,
        "passed": bool(all(checks.values())),
        "checks": {k: bool(v) for k, v in checks.items()},
        "recovery_rates": rates,
        "confusion": confusion,
        "parameter_mean_absolute_errors": mae,
        "parameter_runs": parameter_runs,
        "random_reports_best_rmse_pp": random_error,
        "plan": {
            "starting_reports": "Conditioned observed starting marginals; no internal-prior recovery claim.",
            "partition": "Whole matched pairs remain within a partition; new generator seeds for test cases.",
            "branches": "Public-reference branches fixed before simulating reports; no research-policy recovery claim.",
            "errors": "Independent logistic-normal SD .3, reports rounded to .01; no empirical noise or interval-coverage claim.",
            "scope": "Development simulation, not held-out empirical validation or proof of intervention benefit.",
        },
    }
