"""Rounded probability reports with integrated, source-correlated response noise."""

from math import erfc, sqrt

import numpy as np

from epistemics.source_inference.observers import FAMILIES

GAINS = np.linspace(0.7, 1.3, 13)
INDEPENDENT_SD = 0.18
BLOCK_SD = 0.12
NODES, WEIGHTS = np.polynomial.hermite.hermgauss(15)
OFFSETS = sqrt(2) * BLOCK_SD * NODES
LOG_WEIGHTS = np.log(WEIGHTS / sqrt(np.pi))


def logsumexp(values, axis=None):
    values = np.asarray(values)
    maximum = values.max(axis=axis, keepdims=True)
    return np.squeeze(
        maximum + np.log(np.exp(values - maximum).sum(axis=axis, keepdims=True)), axis=axis
    )


def sigmoid(values):
    x = np.asarray(values)
    return np.exp(-np.logaddexp(0, -x))


def bin_edges(reports):
    p = np.asarray(reports, dtype=float)
    if np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError("Probability reports must be finite and between zero and one")
    if not np.allclose(p * 100, np.round(p * 100), atol=1e-8, rtol=0):
        raise ValueError("Reports must use whole percentages")
    lower, upper = np.maximum(p - 0.005, 0), np.minimum(p + 0.005, 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(lower) - np.log1p(-lower), np.log(upper) - np.log1p(-upper)


def normal_bin_probability(lower, upper, mean, sd):
    if not np.isfinite(sd) or sd <= 0:
        raise ValueError("Response standard deviation must be positive")
    lo, hi = np.broadcast_arrays((lower - mean) / (sqrt(2) * sd), (upper - mean) / (sqrt(2) * sd))

    def complementary(x):
        return np.fromiter((erfc(float(v)) for v in x.flat), float, count=x.size).reshape(x.shape)

    # Survival differences in the positive tail avoid cancellation of two values near one.
    positive = lo >= 0
    mass = np.where(
        positive,
        0.5 * (complementary(lo) - complementary(hi)),
        0.5 * (complementary(-hi) - complementary(-lo)),
    )
    return np.maximum(mass, 0)


def log_likelihood(means, reports, blocks, independent_sd=INDEPENDENT_SD):
    """Means can have leading family/gain dimensions; final dimension indexes reports."""
    means = np.asarray(means)
    reports = np.asarray(reports)
    blocks = np.asarray(blocks)
    if means.shape[-1] != len(reports) or blocks.shape != reports.shape or not len(reports):
        raise ValueError("Reports, block ids and predictive means must align and be nonempty")
    lower, upper = bin_edges(reports)
    result = np.zeros(means.shape[:-1])
    for block in dict.fromkeys(blocks.tolist()):
        mask = blocks == block
        conditional = means[..., None, mask] + OFFSETS[:, None]
        probability = normal_bin_probability(lower[mask], upper[mask], conditional, independent_sd)
        # Log floor is purely numerical and only reached far into impossible report tails.
        ll = np.log(np.maximum(probability, 1e-300)).sum(axis=-1)
        result += logsumexp(ll + LOG_WEIGHTS, axis=-1)
    return result


def fit(logits, reports, blocks, independent_sd=INDEPENDENT_SD):
    logits = np.asarray(logits)
    if logits.shape != (len(FAMILIES), len(reports)) or np.any(~np.isfinite(logits)):
        raise ValueError("One finite logit prediction per candidate family and report is required")
    scores = log_likelihood(
        logits[:, None, :] * GAINS[None, :, None], reports, blocks, independent_sd
    )
    evidence = logsumexp(scores, axis=1) - np.log(len(GAINS))
    probabilities = np.exp(evidence - logsumexp(evidence))
    best = int(np.argmax(probabilities))
    rows = {}
    for i, family in enumerate(FAMILIES):
        tied = np.flatnonzero(np.abs(scores[i] - np.max(scores[i])) < 1e-9)
        rows[family] = {
            "log_marginal_likelihood": float(evidence[i]),
            "conditional_model_probability": float(probabilities[i]),
            "maximum_log_likelihood": float(scores[i].max()),
            "best_gain": float(GAINS[int(np.argmax(scores[i]))]),
            "tied_gains": [float(GAINS[j]) for j in tied],
        }
    return {
        "families": rows,
        "best_family": FAMILIES[best],
        "decision": FAMILIES[best] if probabilities[best] >= 0.8 else "ambiguous",
        "scope": "Equal family priors and uniform finite gain priors; probabilities are conditional on these candidate models",
    }


def sample_reports(logits, gain, blocks, rng, independent_sd=INDEPENDENT_SD):
    blocks = np.asarray(blocks)
    offsets = {b: rng.normal(0, BLOCK_SD) for b in dict.fromkeys(blocks.tolist())}
    noisy = np.asarray(logits) * gain + np.array([offsets[b] for b in blocks])
    noisy += rng.normal(0, independent_sd, noisy.shape)
    return np.round(sigmoid(noisy) * 100) / 100


def expected_model_information(logits):
    """One-probe mutual information in bits, marginalizing gain and block offset.

    This is a marginal ranking heuristic, NOT the joint information of a selected battery.
    Correlation within a chosen battery is retained by the recovery likelihood.
    """
    logits = np.asarray(logits)
    lower, upper = bin_edges(np.arange(101) / 100)
    means = logits[:, None, :, None] * GAINS[None, :, None, None]
    probabilities = normal_bin_probability(
        lower, upper, means, sqrt(INDEPENDENT_SD**2 + BLOCK_SD**2)
    ).mean(axis=1)
    probabilities /= probabilities.sum(axis=-1, keepdims=True)
    mixture = probabilities.mean(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        contribution = np.where(
            probabilities > 0, probabilities * (np.log2(probabilities) - np.log2(mixture)), 0
        )
    return contribution.sum(axis=-1).mean(axis=0)
