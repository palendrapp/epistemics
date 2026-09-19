"""Factorized joint observer over company, sources and provenance, using public input only.

Archive weighting is a generalized-Bayes behavioral rule; nonunit weights are not
claimed to be a normative sampling model. All source factors enter exactly once.
"""

from itertools import product

import numpy as np

from epistemics.discovery.inference import extract
from epistemics.discovery.world import GROWTH, SOURCE_IDS, SOURCE_STATES, cdf, log_measurement

CORE = np.array(list(product(range(4), range(2), range(2), range(2))))
F = GROWTH[CORE[:, 0]]
A, K, G = CORE[:, 1], CORE[:, 2], CORE[:, 3]
BIAS, SD = SOURCE_STATES[:, 0], SOURCE_STATES[:, 1]
ACCURACY = cdf((2 - BIAS) / SD) - cdf((-2 - BIAS) / SD)
PARAMETERS = ("source_frame", "archive_weight", "relationship_prior", "fundamentals_prior")


def logsumexp(x, axis=-1):
    peak = np.max(x, axis=axis, keepdims=True)
    return np.squeeze(peak, axis=axis) + np.log(np.exp(x - peak).sum(axis=axis))


def parameter_grid(plan):
    return np.array(
        list(
            product(
                plan.source_frame_grid,
                plan.archive_weight_grid,
                plan.relationship_prior_grid,
                plan.fundamentals_prior_grid,
            )
        )
    )


def predict(trial, parameters):
    parameters = np.atleast_2d(parameters)
    alpha, learning, relationship, fundamentals = parameters.T
    values, audit, shared = extract(trial)
    logcore = relationship[:, None] * K + fundamentals[:, None] * ((F - 12) / 6)
    for analogue in trial.analogues:
        mean = analogue.underlying_growth_pct - np.where(K == 1, 8, 2) * analogue.rollout_disruption
        logcore += log_measurement(analogue.renewal_growth_pct, mean, 3)
    if "backlog" in values:
        logcore += log_measurement(values["backlog"], 12 + 20 * A, 6)
    if "unaffected" in values:
        logcore += log_measurement(values["unaffected"], F, 1.8)
    if "news" in values:
        logcore += G * log_measurement(values["news"], values["renewal"], 0.75)
    if shared is not None:
        logcore[:, G != int(shared)] = -np.inf
    if "model" in values:
        expected = round(0.6 * values["demand"] + 0.4 * values["renewal"] + 2, 1)
        if abs(expected - values["model"]) > 1e-8:
            raise ValueError("Derived model inconsistent with public inputs")
    conditional_source = []
    for j, sid in enumerate(SOURCE_IDS):
        source = next(s for s in trial.sources if s.source_id == sid)
        tone = (
            1
            if ": skeptical;" in source.profile
            else -1
            if ": optimistic;" in source.profile
            else 0
        )
        archive = np.zeros(6)
        for row in source.archive:
            archive += log_measurement(row.reported_pct - row.audited_pct, BIAS, SD)
        if sid == "morrow":
            for reported, actual in audit:
                archive += log_measurement(reported - actual, BIAS, SD)
        likelihood = np.zeros((len(CORE), 6))
        if j == 0:
            for key in ("demand", "new_demand"):
                if key in values:
                    likelihood += log_measurement(values[key], F[:, None] + BIAS, SD)
        if j == 1 and "renewal" in values:
            likelihood += log_measurement(
                values["renewal"], (F - np.where(K == 1, 8, 2) * A)[:, None] + BIAS, SD
            )
        if j == 2 and "news" in values:
            likelihood += (G == 0)[:, None] * log_measurement(
                values["news"], (F - np.where(K == 1, 8, 2) * A)[:, None] + BIAS, SD
            )
        ls = (
            alpha[:, None, None] * tone * (SD == 1.5)
            + learning[:, None, None] * archive
            + likelihood
        )
        normalizer = logsumexp(ls)
        conditional_source.append(np.exp(ls - normalizer[:, :, None]) @ ACCURACY)
        logcore += normalizer
    q = np.exp(logcore - logsumexp(logcore)[:, None])
    masses = np.stack([q[:, CORE[:, 0] == i].sum(axis=1) for i in range(4)], axis=1)
    growth = masses @ cdf((GROWTH - 12) / 2)
    # Normalize the A=0 slice in log space, including extremely unlikely inspections.
    conditional_log = logcore[:, A == 0]
    conditional = np.exp(conditional_log - logsumexp(conditional_log)[:, None])
    conditional_growth = conditional @ cdf((F[A == 0] - 12) / 2)
    quantiles = []
    for level in (0.1, 0.5, 0.9):
        lo, hi = np.full(len(q), -20.0), np.full(len(q), 45.0)
        for _ in range(32):
            mid = (lo + hi) / 2
            below = np.sum(masses * cdf((mid[:, None] - GROWTH) / 2), axis=1) < level
            lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
        quantiles.append((lo + hi) / 2)
    return {
        "growth": growth,
        "conditional": conditional_growth,
        "sources": {
            sid: (q * v).sum(axis=1) for sid, v in zip(SOURCE_IDS, conditional_source, strict=True)
        },
        "quantiles": np.array(quantiles).T,
    }


def logit(p, clip):
    p = np.clip(p, clip, 1 - clip)
    return np.log(p / (1 - p))


def channels(trials):
    result = []
    for t in trials:
        result.append((t.index, "growth"))
        result.extend((t.index, f"source:{sid}") for sid in t.source_probe_ids)
        if t.conditional_probe:
            result.append((t.index, "conditional"))
        result.extend((t.index, f"p{level}") for level in (10, 50, 90))
    return result


def predicted_vector(trials, parameters, plan):
    rows = []
    for trial in trials:
        f = predict(trial, parameters)
        rows.append(logit(f["growth"], plan.probability_clip))
        rows.extend(
            logit(f["sources"][sid], plan.probability_clip) for sid in trial.source_probe_ids
        )
        if trial.conditional_probe:
            rows.append(logit(f["conditional"], plan.probability_clip))
        rows.extend(f["quantiles"][:, i] for i in range(3))
    return np.array(rows).T


def observed_vector(observations, plan):
    values = []
    for o in observations:
        answer, trial = o.answer, o.trial
        p = (
            answer.target_probability
            if trial.target_event == "growth_above_12"
            else 1 - answer.target_probability
        )
        values.append(logit(p, plan.probability_clip))
        values.extend(
            logit(answer.source_accuracy[s], plan.probability_clip) for s in trial.source_probe_ids
        )
        if trial.conditional_probe:
            values.append(logit(answer.conditional_growth_probability, plan.probability_clip))
        values.extend(
            [
                answer.growth_quantiles_pct.p10,
                answer.growth_quantiles_pct.p50,
                answer.growth_quantiles_pct.p90,
            ]
        )
    return np.array(values)


def covariance(trials, plan):
    labels = channels(trials)
    scales = np.array(
        [
            plan.quantile_sd if name.startswith("p") else plan.probability_logit_sd
            for _, name in labels
        ]
    )
    same_step = np.array([[a == b for b, _ in labels] for a, _ in labels])
    episode, checkpoint = plan.within_episode_correlation, plan.within_checkpoint_correlation
    correlation = (
        (1 - episode - checkpoint) * np.eye(len(labels)) + episode + checkpoint * same_step
    )
    return correlation * scales[:, None] * scales[None, :]


def wording_vector(trials):
    return np.array(
        [
            (1 if trials[step].target_event == "growth_above_12" else -1) if name == "growth" else 0
            for step, name in channels(trials)
        ]
    )
