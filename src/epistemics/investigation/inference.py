"""Conditional observers, one-step decision value, and rounded report likelihoods.

Every prediction takes public trials only. The generator's truth, seed and unchosen
query outcomes cannot be inputs to this observer or its value-of-information policy.
"""

import math

import numpy as np

from epistemics.discovery.world import cdf, log_measurement, normalize
from epistemics.investigation.world import (
    BIAS,
    EVENTS,
    OFFSET_PRIOR,
    RENEWAL,
    SD,
    STATES,
    TARGET,
    A,
    C,
    K,
)

CANDIDATES = ("joint", "fixed_source", "fixed_weak_link", "fixed_delta", "no_retraction")
DESCRIPTIONS = {
    "joint": "Joint company, disruption, relationship, source and transcription inference.",
    "fixed_source": "Source fixed to zero bias and SD 4; company and transcription inference retained.",
    "fixed_weak_link": "Disruption effect fixed at 2 points; source and transcription inference retained.",
    "fixed_delta": "Reported probabilities move halfway toward each joint forecast; resolved probes remain known. A descriptive smoothing control, not a separately learned generative model.",
    "no_retraction": "Joint observer that keeps the original report interpretation when transcription is corrected.",
}
REPORT_SD = 0.3
REPORT_CLIP = 1e-6


def posterior(
    trial, *, model="joint", archive_weight=1.0, source_bias_prior=0.0, disruption_prior=0.0
):
    if model not in CANDIDATES or not math.isfinite(archive_weight) or archive_weight < 0:
        raise ValueError("Unknown model or invalid archive weight")
    q = np.log(OFFSET_PRIOR[STATES[:, 4]])
    if not math.isfinite(source_bias_prior) or not math.isfinite(disruption_prior):
        raise ValueError("Prior coefficients must be finite")
    # Diagnostic prior contrasts; never fit both from a lone headline forecast.
    q += source_bias_prior * (-BIAS / 3) + disruption_prior * A
    if model == "fixed_source":
        q[(BIAS != 0) | (SD != 4)] = -np.inf
    if model == "fixed_weak_link":
        q[K != 0] = -np.inf
    for row in trial.source_archive:
        q += archive_weight * log_measurement(row.reported_pct - row.audited_pct, BIAS, SD)
    for row in trial.analogues:
        mean = row.underlying_growth_pct - np.where(K == 1, 8, 2) * row.rollout_disruption
        q += log_measurement(row.renewal_growth_pct, mean, 3)
    if trial.reported_growth_pct is not None:
        q += log_measurement(trial.reported_growth_pct, RENEWAL + BIAS + C, SD)
    if trial.correction_offset_pct is not None and model != "no_retraction":
        # Condition the SAME measurement on the verified offset. Never multiply
        # a second measurement likelihood or delete unrelated purchased evidence.
        q[C != trial.correction_offset_pct] = -np.inf
    if trial.query_result is not None:
        p = EVENTS[trial.selected_query]
        q += np.log(np.maximum(p if trial.query_result else 1 - p, 1e-300))
    if not np.isfinite(q).any():
        raise ValueError("Public evidence is outside the observer support")
    return normalize(q)


def forecasts(
    trial,
    *,
    model="joint",
    archive_weight=1.0,
    previous=None,
    delta_rate=0.5,
    source_bias_prior=0.0,
    disruption_prior=0.0,
):
    if not 0 <= delta_rate <= 1:
        raise ValueError("Delta rate must be in 0..1")
    q = posterior(
        trial,
        model=model,
        archive_weight=archive_weight,
        source_bias_prior=source_bias_prior,
        disruption_prior=disruption_prior,
    )
    result = np.array([q @ TARGET, q @ EVENTS["source_audit"], q @ EVENTS["operations_check"]])
    if model == "fixed_delta" and previous is not None:
        result = np.asarray(previous) + delta_rate * (result - previous)
    if trial.selected_query == "source_audit":
        result[1] = float(trial.query_result)
    if trial.selected_query == "operations_check":
        result[2] = float(trial.query_result)
    return np.clip(result, 0, 1)


def trajectory(trials, **kwargs):
    rows = []
    for trial in trials:
        rows.append(forecasts(trial, previous=rows[-1] if rows else None, **kwargs))
    return np.array(rows)


def query_values(trial):
    """Exact enumeration of binary query outcomes for the first committed decision.

    The subsequent unpaid correction diagnostic is outside this utility horizon.
    Positive values are net gains over acting now. This is a conditional reference,
    not an assertion that a discovery participant knows this generative model.
    """
    if trial.index != 1:
        raise ValueError("Research is offered only at checkpoint 1")
    q = posterior(trial)

    def value(weights):
        p = float(weights @ TARGET)
        return max(0.0, (trial.gain + trial.loss) * p - trial.loss)

    base = value(q)
    values = {}
    for option in trial.options:
        gross = 0.0
        if option.query in EVENTS:
            likelihood = EVENTS[option.query]
            for event in (likelihood, 1 - likelihood):
                mass = float(q @ event)
                if mass > 0:
                    gross += mass * value(q * event / mass)
            gross -= base
        values[option.query] = {
            "gross_value": max(0.0, gross),
            "cost": option.cost,
            "net_value": max(0.0, gross) - option.cost,
        }
    return values


def best_query(trial):
    values = query_values(trial)
    # Prefer no purchase in ties, then lower cost, then the stable protocol order.
    return max(values, key=lambda q: (values[q]["net_value"], q == "stop", -values[q]["cost"]))


def logit(p):
    p = np.clip(p, REPORT_CLIP, 1 - REPORT_CLIP)
    return np.log(p / (1 - p))


def report_log_likelihood(reports, predictions, sd=REPORT_SD):
    """Mass of 0.01 rounding bins under logistic-normal reports, including 0 and 1.

    Exact predicted endpoints have latent means logit(1e-6) and logit(1-1e-6).
    No observations are clipped, discarded or silently treated as exact beliefs.
    """
    y = np.asarray(reports)
    if sd <= 0 or not math.isfinite(sd) or not np.isfinite(y).all():
        raise ValueError("Invalid report likelihood arguments")
    if np.any((y < 0) | (y > 1)) or not np.allclose(y * 100, np.round(y * 100), atol=1e-8, rtol=0):
        raise ValueError("Reports must use 0.01 probability increments")
    lo, hi = np.maximum(0, y - 0.005), np.minimum(1, y + 0.005)
    with np.errstate(divide="ignore"):
        lower = (np.log(lo / (1 - lo)) - logit(predictions)) / sd
        upper = (np.log(hi / (1 - hi)) - logit(predictions)) / sd
    # Reflect positive intervals to avoid subtracting two CDFs close to one.
    reflected = lower > 0
    mass = cdf(np.where(reflected, -lower, upper)) - cdf(np.where(reflected, -upper, lower))
    return np.log(np.maximum(mass, 1e-300))


def simulate_reports(predictions, rng, sd=REPORT_SD):
    latent = logit(predictions) + rng.normal(0, sd, np.shape(predictions))
    return np.round(1 / (1 + np.exp(-latent)), 2)


def answer_vector(answer):
    return [
        answer.growth_probability,
        answer.audit_understatement_probability,
        answer.backlog_high_probability,
    ]


def analysis(observations, world):
    trials = [o.trial for o in observations]
    observed = np.array([answer_vector(o.answer) for o in observations])
    predictions = {m: trajectory(trials, model=m) for m in CANDIDATES}
    comparisons = {
        model: {
            "description": DESCRIPTIONS[model],
            "report_rmse_pp": float(np.sqrt(np.mean((p - observed) ** 2)) * 100),
            "report_log_likelihood": float(report_log_likelihood(observed, p).sum()),
            "predictions": p.tolist(),
        }
        for model, p in predictions.items()
    }
    values = query_values(trials[1])
    chosen = observations[1].answer.query
    first = observations[2].answer
    outcome = world["truth"]["growth_event"]
    payoff = (trials[2].gain if outcome else -trials[2].loss) if first.decision == "invest" else 0
    threshold = trials[2].loss / (trials[2].gain + trials[2].loss)
    return {
        "status": "descriptive_development_only",
        "candidate_comparisons": comparisons,
        "candidate_likelihood_scope": "Fixed candidates, independent rounded logistic-normal report errors (SD 0.3); no model posterior, internal-mechanism identification or population inference.",
        "research": {
            "selected": chosen,
            "conditional_reference_values": values,
            "conditional_reference_regret": max(v["net_value"] for v in values.values())
            - values[chosen]["net_value"],
        },
        "committed_decision": {
            "growth_brier": (first.growth_probability - outcome) ** 2,
            "realized_points_net_research": payoff - values[chosen]["cost"],
            "agrees_with_reported_probability": first.decision
            == ("invest" if first.growth_probability > threshold else "hold"),
        },
        "correction_revision_pp": ((observed[3] - observed[2]) * 100).tolist(),
        "conditional_reference_revision_pp": (
            (predictions["joint"][3] - predictions["joint"][2]) * 100
        ).tolist(),
        "query_resolved_probe_errors": [
            abs(
                answer_vector(o.answer)[1 if chosen == "source_audit" else 2]
                - float(o.trial.query_result)
            )
            for o in observations[2:]
            if chosen in {"source_audit", "operations_check"}
        ],
    }
