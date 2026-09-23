"""Conditional observer comparisons with explicit uncertainty in the first report.

The noisy-start observer marginalizes one latent initial state per episode over
all later reports together. Later answers never update the weights used to make
its predictive means. Choice policies are not fitted.
"""

import itertools
import json
import math
from functools import lru_cache

import numpy as np

from epistemics.discovery.world import normalize
from epistemics.investigation.inference import (  # noqa: F401
    answer_vector,
    report_log_likelihood,
)
from epistemics.investigation2 import inference as base
from epistemics.investigation2.inference import (  # noqa: F401
    FEATURES,
    best_query,
    expectation_vector,
    expectations,
    initial,
    observed_vector,
    posterior,
    projected,
    query_values,
    trajectory,
    values_from_expectations,
)
from epistemics.investigation3.models import MEASUREMENTS, Trial

INITIALIZATIONS = ("working_prior", "hard_report", "noisy_report")
INITIAL_REPORT_SD = 0.8
TILTS = np.array(list(itertools.product((-math.log(3), 0.0, math.log(3)), repeat=3)))
TILT_WEIGHTS = np.array([math.prod(0.5 if x == 0 else 0.25 for x in u) for u in TILTS])
GRID = [(float(c), float(a)) for c in np.linspace(0, 1, 11) for a in np.linspace(0.2, 1, 9)]
CANDIDATES = base.CANDIDATES


def starting_states(trial, initialization, reported_start):
    if initialization not in INITIALIZATIONS:
        raise ValueError("Unknown initialization model")
    q0 = initial(trial)
    if initialization == "working_prior":
        return q0[None, :], np.ones(1)
    if initialization == "hard_report":
        return initial(trial, reported_start)[None, :], np.ones(1)
    with np.errstate(divide="ignore"):
        logq = np.log(q0)
    states = np.array([normalize(logq + FEATURES @ u) for u in TILTS])
    ll = report_log_likelihood(reported_start, states @ FEATURES, sd=INITIAL_REPORT_SD).sum(axis=1)
    return states, normalize(np.log(TILT_WEIGHTS) + ll)


def _reports(raw, trials, rate):
    rows = [raw[0]]
    for t, p in zip(trials[1:], raw[1:], strict=True):
        row = rows[-1] + rate * (p - rows[-1])
        if t.selected_query in ("source_audit", "operations_check"):
            row[1 if t.selected_query == "source_audit" else 2] = float(t.query_result)
        rows.append(row)
    return np.array(rows)


def _prediction(raw, future, trials, rate):
    rows = _reports(raw, trials, rate)
    values = rows[1:].flatten().tolist()
    if future is not None:
        e = {}
        for i, query in enumerate(MEASUREMENTS):
            q = future[query]
            e[query] = {
                "yes_probability": float(rows[1, i + 1]) if i < 2 else q["yes_probability"],
                "growth_if_yes": rows[1, 0] + rate * (q["growth_if_yes"] - rows[1, 0]),
                "growth_if_no": rows[1, 0] + rate * (q["growth_if_no"] - rows[1, 0]),
            }
        values.extend(expectation_vector(e))
    return np.array(values)


@lru_cache(maxsize=96)
def _prediction_grid(trial_json, initialization, hard_start, unretracted=False):
    from epistemics.investigation2.models import Trial as LegacyTrial

    trials = [
        (
            LegacyTrial if x.get("schema_version") == "epistemics.investigation-trial.v2" else Trial
        ).model_validate(x)
        for x in json.loads(trial_json)
    ]
    # Noisy-start component states depend on public baseline only. The observed
    # first answer changes mixture weights, never these component predictions.
    states, _ = starting_states(trials[0], initialization, hard_start or (0.5, 0.5, 0.5))
    result = np.empty((len(GRID), len(states), 18 if trials[1].expectation_queries else 9))
    for ci, coupling in enumerate(np.linspace(0, 1, 11)):
        for j, state in enumerate(states):
            raw = trajectory(trials, start=state, coupling=coupling, unretracted=unretracted)
            future = (
                expectations(trials[1], start=state, coupling=coupling)
                if trials[1].expectation_queries
                else None
            )
            for ai, rate in enumerate(np.linspace(0.2, 1, 9)):
                result[ci * 9 + ai, j] = _prediction(raw, future, trials, rate)
    result.setflags(write=False)
    return result


def prepared(observations, initialization, *, unretracted=False):
    trials = [o.trial for o in observations]
    first = tuple(answer_vector(observations[0].answer))
    _, weights = starting_states(trials[0], initialization, first)
    key = json.dumps([t.model_dump(mode="json") for t in trials], sort_keys=True)
    predictions = _prediction_grid(
        key, initialization, first if initialization == "hard_report" else None, unretracted
    )
    return observed_vector(observations), predictions, weights


def marginal_log_likelihood(observed, components, weights):
    ll = report_log_likelihood(observed, components).sum(axis=-1) + np.log(weights)
    maximum = ll.max(axis=-1)
    return maximum + np.log(np.exp(ll - maximum[..., None]).sum(axis=-1))


def fit(observation_sets, *, initialization="noisy_report"):
    data = [prepared(obs, initialization) for obs in observation_sets]
    if not data:
        raise ValueError("At least one completed episode is required")
    likelihood = sum(marginal_log_likelihood(o, p, w) for o, p, w in data)
    means = np.concatenate([np.einsum("gln,l->gn", p, w) for _, p, w in data], axis=1)
    observed = np.concatenate([o for o, _, _ in data])
    best = int(likelihood.argmax())
    masses = normalize(likelihood)
    rmse = float(np.sqrt(np.mean((means[best] - observed) ** 2)) * 100)
    intervals = []
    for column in range(2):
        support = sorted({g[column] for g in GRID})
        weights = [
            sum(w for g, w in zip(GRID, masses, strict=True) if g[column] == s) for s in support
        ]
        intervals.append(
            [
                support[min(np.searchsorted(np.cumsum(weights), p), len(support) - 1)]
                for p in (0.025, 0.975)
            ]
        )
    return {
        "initialization": initialization,
        "status": "conditional_development_fit" if rmse <= 8 else "inadequate_absolute_fit",
        "coupling_grid_estimate": GRID[best][0],
        "response_rate_grid_estimate": GRID[best][1],
        "posterior_grid_means": (masses @ np.array(GRID)).tolist(),
        "conditional_grid_intervals_95": intervals,
        "report_rmse_pp": rmse,
        "report_log_likelihood": float(likelihood[best]),
        "observed_report_count_excluding_starts": len(observed),
        "scope": "Conditional on initial reports and selected branches. Noisy-start states are marginalized jointly over each episode; predictive means use first-report weights only. Fixed start SD .8 and later report SD .3; conditional grid intervals are not calibrated trait uncertainty. No empirical validation or intervention claim.",
    }


def predictions(observation_sets, coupling, response_rate, *, initialization="noisy_report"):
    index = min(
        range(len(GRID)), key=lambda i: abs(GRID[i][0] - coupling) + abs(GRID[i][1] - response_rate)
    )
    if not np.allclose(GRID[index], (coupling, response_rate)):
        raise ValueError("Prediction parameters must belong to the declared grid")
    return np.concatenate(
        [w @ p[index] for _, p, w in (prepared(obs, initialization) for obs in observation_sets)]
    )


def analysis(observations, world):
    result = base.analysis(observations, world)
    comparisons = {}
    for name, (coupling, rate, ignore) in CANDIDATES.items():
        observed, components, weights = prepared(observations, "noisy_report", unretracted=ignore)
        index = min(
            range(len(GRID)), key=lambda i: abs(GRID[i][0] - coupling) + abs(GRID[i][1] - rate)
        )
        prediction = weights @ components[index]
        comparisons[name] = {
            "initialization": "noisy_report",
            "report_rmse_pp": float(np.sqrt(np.mean((observed - prediction) ** 2)) * 100),
            "report_log_likelihood": float(
                marginal_log_likelihood(observed, components[index], weights)
            ),
            "predictions": prediction.tolist(),
        }
    result["candidate_comparisons"] = comparisons
    result["initialization_comparisons"] = {
        m: fit([observations], initialization=m) for m in INITIALIZATIONS
    }
    result["model_parameters_are_passport_traits"] = False
    return result
