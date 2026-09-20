"""Public-data observers with starting-report conditioning and a modular alternative."""

import math

import numpy as np

from epistemics.discovery.world import log_measurement, normalize
from epistemics.investigation.inference import answer_vector, report_log_likelihood
from epistemics.investigation2.models import MEASUREMENTS
from epistemics.investigation2.world import BIAS, EVENTS, RENEWAL, SD, TARGET, C, K, S

FEATURES = np.array([TARGET, EVENTS["source_audit"], EVENTS["operations_check"]]).T
CANDIDATES = {
    "joint": (1.0, 1.0, False),
    "separate_sources": (0.0, 1.0, False),
    "report_inertia": (1.0, 0.5, False),
    "unretracted": (1.0, 1.0, True),
}


def initial(trial, reported_start=None):
    """KL projection onto three starting marginals, not direct belief measurement.

    At background the F, S and A factors are independent. Each one-dimensional
    exponential tilt can therefore be solved separately. Values outside finite
    support remain visibly unsupported; no later reports enter this projection.
    """
    q = np.zeros(len(TARGET))
    if trial.transcription_checked:
        q[C != 0] = -np.inf
    for row in trial.source_archive:
        q += log_measurement(row.reported_pct - row.audited_pct, BIAS, SD)
    for row in trial.analogues:
        q += log_measurement(
            row.renewal_growth_pct,
            row.underlying_growth_pct - np.where(K == 1, 8, 2) * row.rollout_disruption,
            3,
        )
    if reported_start is not None:
        target = np.asarray(reported_start, dtype=float)
        if (
            target.shape != (3,)
            or not np.isfinite(target).all()
            or np.any((target < 0) | (target > 1))
        ):
            raise ValueError("Starting reports must be three finite probabilities")
        for feature, wanted in zip(FEATURES.T, target, strict=True):
            lo, hi = -2000.0, 2000.0
            for _ in range(50):
                mid = (lo + hi) / 2
                if normalize(q + mid * feature) @ feature < wanted:
                    lo = mid
                else:
                    hi = mid
            q += ((lo + hi) / 2) * feature
    return normalize(q)


def posterior(trial, *, coupling=1.0, start=None, unretracted=False):
    if not math.isfinite(coupling) or not 0 <= coupling <= 1:
        raise ValueError("Coupling must be in 0..1")
    base = initial(trial) if start is None else np.asarray(start)
    with np.errstate(divide="ignore"):
        q = np.log(base)
    if trial.reported_growth_pct is not None:
        q += log_measurement(trial.reported_growth_pct, RENEWAL + BIAS + C, SD)
    if trial.correction_offset_pct is not None and not unretracted:
        q[C != trial.correction_offset_pct] = -np.inf
    direct_source = np.ones(len(q))
    if trial.query_result is not None:
        event = EVENTS[trial.selected_query]
        likelihood = event if trial.query_result else 1 - event
        q += np.log(np.maximum(likelihood, 1e-300))
        if trial.selected_query == "source_audit":
            direct_source = likelihood
    if not np.isfinite(q).any():
        raise ValueError("Evidence is outside model support")
    joint = normalize(q)
    if coupling == 1:
        return joint
    # Cut feedback to the source marginal, retaining company|source dependence.
    # Direct source audits still update that source marginal in the cut model.
    source_mass = np.bincount(S, weights=base * direct_source, minlength=10)
    source_mass /= source_mass.sum()
    cut = np.zeros(len(q))
    for s in range(10):
        if source_mass[s] == 0:
            continue
        mask = S == s
        cut[mask] = normalize(q[mask]) * source_mass[s]
    return coupling * joint + (1 - coupling) * cut


def projected(weights, trial):
    result = weights @ FEATURES
    if trial.selected_query in ("source_audit", "operations_check"):
        result[1 if trial.selected_query == "source_audit" else 2] = float(trial.query_result)
    return np.clip(result, 0, 1)


def trajectory(
    trials, *, coupling=1.0, response_rate=1.0, unretracted=False, reported_start=None, start=None
):
    if not math.isfinite(response_rate) or not 0 < response_rate <= 1:
        raise ValueError("Response rate must be in (0,1]")
    start = initial(trials[0], reported_start) if start is None else start
    rows = []
    for trial in trials:
        raw = projected(
            posterior(trial, coupling=coupling, start=start, unretracted=unretracted), trial
        )
        report = raw if not rows else rows[-1] + response_rate * (raw - rows[-1])
        if trial.selected_query in ("source_audit", "operations_check"):
            report[1 if trial.selected_query == "source_audit" else 2] = float(trial.query_result)
        rows.append(report)
    return np.array(rows)


def expectations(trial, *, coupling=1.0, start=None, response_rate=1.0, current=None):
    before = posterior(trial, coupling=coupling, start=start)
    current = projected(before, trial) if current is None else current
    result = {}
    for query in MEASUREMENTS:
        yes = float(before @ EVENTS[query])
        if query in ("source_audit", "operations_check"):
            yes = float(current[1 if query == "source_audit" else 2])
        conditional = {}
        for event, name in ((False, "growth_if_no"), (True, "growth_if_yes")):
            future = trial.model_copy(update={"selected_query": query, "query_result": event})
            p = float(posterior(future, coupling=coupling, start=start) @ TARGET)
            conditional[name] = float(current[0] + response_rate * (p - current[0]))
        result[query] = {"yes_probability": yes, **conditional}
    return result


def utility(p, gain, loss):
    return max(0.0, (gain + loss) * p - loss)


def values_from_expectations(trial, probability, forecasts):
    """Retain incoherence: do not renormalize or repair the respondent's answers."""
    probability = float(probability)
    values = {}
    base = utility(probability, trial.gain, trial.loss)
    for option in trial.options:
        gross, mixture = 0.0, probability
        if option.query in forecasts:
            e = forecasts[option.query]
            if hasattr(e, "model_dump"):
                e = e.model_dump()
            yes = float(e["yes_probability"])
            mixture = yes * e["growth_if_yes"] + (1 - yes) * e["growth_if_no"]
            gross = (
                yes * utility(e["growth_if_yes"], trial.gain, trial.loss)
                + (1 - yes) * utility(e["growth_if_no"], trial.gain, trial.loss)
                - base
            )
        values[option.query] = {
            "gross_value": gross,
            "cost": option.cost,
            "net_value": gross - option.cost,
            "mixture_minus_current_pp": 100 * (mixture - probability),
        }
    return values


def query_values(trial):
    return values_from_expectations(trial, float(posterior(trial) @ TARGET), expectations(trial))


def best_query(values):
    return max(values, key=lambda q: (values[q]["net_value"], q == "stop", -values[q]["cost"]))


def expectation_vector(values):
    return [
        float(values[q][k])
        for q in MEASUREMENTS
        for k in ("yes_probability", "growth_if_yes", "growth_if_no")
    ]


def observed_vector(observations):
    values = [v for o in observations[1:] for v in answer_vector(o.answer)]
    e = observations[1].answer.expectations
    if e is not None:
        values.extend(expectation_vector({q: row.model_dump() for q, row in e.items()}))
    return np.array(values)


def prediction_vector(
    trials, reported_start, *, coupling=1.0, response_rate=1.0, unretracted=False, start=None
):
    start = initial(trials[0], reported_start) if start is None else start
    rows = trajectory(
        trials, start=start, coupling=coupling, response_rate=response_rate, unretracted=unretracted
    )
    values = rows[1:].flatten().tolist()
    if trials[1].expectation_queries:
        values.extend(
            expectation_vector(
                expectations(
                    trials[1],
                    start=start,
                    coupling=coupling,
                    response_rate=response_rate,
                    current=rows[1],
                )
            )
        )
    return np.array(values)


def fit(observation_sets):
    """Two-dimensional conditional grid, reported as development evidence only."""
    prepared = [
        (obs, initial(obs[0].trial, answer_vector(obs[0].answer))) for obs in observation_sets
    ]
    observed = np.concatenate([observed_vector(obs) for obs, _ in prepared])
    grid, predictions = [], []
    for coupling in np.linspace(0, 1, 11):
        for rate in np.linspace(0.2, 1, 9):
            grid.append((float(coupling), float(rate)))
            predictions.append(
                np.concatenate(
                    [
                        prediction_vector(
                            [o.trial for o in obs],
                            None,
                            coupling=coupling,
                            response_rate=rate,
                            start=start,
                        )
                        for obs, start in prepared
                    ]
                )
            )
    predictions = np.array(predictions)
    ll = report_log_likelihood(observed, predictions).sum(axis=1)
    weights = normalize(ll)
    best = int(np.argmax(ll))
    rmse = float(np.sqrt(np.mean((predictions[best] - observed) ** 2)) * 100)
    means = weights @ np.array(grid)
    intervals = []
    for j in range(2):
        support = sorted({row[j] for row in grid})
        masses = np.array(
            [sum(w for g, w in zip(grid, weights, strict=True) if g[j] == v) for v in support]
        )
        intervals.append(
            [
                support[min(np.searchsorted(np.cumsum(masses), p), len(support) - 1)]
                for p in (0.025, 0.975)
            ]
        )
    return {
        "status": "conditional_development_fit" if rmse <= 8 else "inadequate_absolute_fit",
        "coupling_grid_estimate": grid[best][0],
        "response_rate_grid_estimate": grid[best][1],
        "posterior_grid_means": means.tolist(),
        "conditional_grid_intervals_95": intervals,
        "report_rmse_pp": rmse,
        "report_log_likelihood": float(ll[best]),
        "observed_report_count_excluding_starts": len(observed),
        "scope": "Conditions on each episode's first three reports using a minimum-KL projection. Uniform grid prior; independent rounded logistic-normal errors, SD 0.3. Intervals are conditional, not established population coverage. No stable trait or released passport measurement.",
    }


def analysis(observations, world):
    trials = [o.trial for o in observations]
    reported = np.array([answer_vector(o.answer) for o in observations])
    start = initial(trials[0], reported[0])
    comparisons = {}
    for name, (coupling, rate, unretracted) in CANDIDATES.items():
        prediction = prediction_vector(
            trials,
            None,
            coupling=coupling,
            response_rate=rate,
            unretracted=unretracted,
            start=start,
        )
        observed = observed_vector(observations)
        comparisons[name] = {
            "report_rmse_pp": float(np.sqrt(np.mean((observed - prediction) ** 2)) * 100),
            "report_log_likelihood": float(report_log_likelihood(observed, prediction).sum()),
            "predictions": prediction.tolist(),
        }
    values = query_values(trials[1])
    chosen = observations[1].answer.query
    elicited = observations[1].answer.expectations
    subjective = (
        values_from_expectations(trials[1], reported[1, 0], elicited)
        if elicited is not None
        else None
    )
    own = None
    if subjective is not None:
        max_gap = max(abs(v["mixture_minus_current_pp"]) for v in subjective.values())
        event_gaps = {
            q: float(100 * (elicited[q].yes_probability - reported[1, j]))
            for q, j in (("source_audit", 1), ("operations_check", 2))
        }
        own = {
            "values": subjective,
            "event_marginal_gaps_pp": event_gaps,
            "max_mixture_gap_pp": max_gap,
            "coherence_within_rounding_tolerance": max(
                max_gap, *(abs(v) for v in event_gaps.values())
            )
            <= 1.5,
            "best_report_implied_query": best_query(subjective),
            "report_implied_regret": max(v["net_value"] for v in subjective.values())
            - subjective[chosen]["net_value"],
            "interpretation": "Reported-expectation arithmetic, not internal utility or belief access. Treat value comparisons as provisional when coherence fails; raw answers are retained.",
        }
    committed = observations[2].answer
    outcome = world["truth"]["growth_event"]
    payoff = (
        (trials[2].gain if outcome else -trials[2].loss) if committed.decision == "invest" else 0.0
    )
    reference = trajectory(trials)
    return {
        "status": "descriptive_development_only",
        "candidate_comparisons": comparisons,
        "starting_projection_residual_pp": ((start @ FEATURES - reported[0]) * 100).tolist(),
        "conditional_reference_predictions": reference.tolist(),
        "decision_probability_agreements": sum(
            o.answer.decision
            == (
                "invest"
                if (o.trial.gain + o.trial.loss) * o.answer.growth_probability > o.trial.loss
                else "hold"
            )
            for o in observations
        ),
        "research": {
            "selected": chosen,
            "conditional_reference_values": values,
            "conditional_reference_regret": max(v["net_value"] for v in values.values())
            - values[chosen]["net_value"],
            "reported_expectations": own,
        },
        "correction_revision_pp": ((reported[3] - reported[2]) * 100).tolist(),
        "conditional_reference_revision_pp": ((reference[3] - reference[2]) * 100).tolist(),
        "committed_decision": {
            "growth_brier": (committed.growth_probability - outcome) ** 2,
            "realized_points_net_research": payoff - values[chosen]["cost"],
        },
    }
