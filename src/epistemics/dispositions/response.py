"""Whole-percentage probability reports and whole-point willingness to pay with Gaussian noise."""

import numpy as np

SQRT2 = np.sqrt(2)
LOG_FLOOR = 1e-300  # Numerical only; reached far into impossible response tails.


def sigmoid(x):
    return np.exp(-np.logaddexp(0, -np.asarray(x, dtype=float)))


def logit(p):
    p = np.asarray(p, dtype=float)
    with np.errstate(divide="ignore"):
        return np.log(p) - np.log1p(-p)


def logsumexp(values, axis=None):
    values = np.asarray(values, dtype=float)
    peak = values.max(axis=axis, keepdims=True)
    peak = np.where(np.isfinite(peak), peak, 0)
    total = np.log(np.exp(values - peak).sum(axis=axis, keepdims=True)) + peak
    return np.squeeze(total, axis=axis)


# Chebyshev fit for erfc (Numerical Recipes erfcc), constant term first.
ERFC_COEFFICIENTS = (
    -1.26551223,
    1.00002368,
    0.37409196,
    0.09678418,
    -0.18628806,
    0.27886807,
    -1.13520398,
    1.48851587,
    -0.82215223,
    0.17087277,
)


def erfc(x):
    """Vectorized complementary error function with fractional error below 1.2e-7."""
    x = np.asarray(x, dtype=float)
    z = np.abs(x)
    t = 1 / (1 + 0.5 * z)
    poly = np.zeros_like(t)
    for coefficient in reversed(ERFC_COEFFICIENTS):
        poly = coefficient + t * poly
    with np.errstate(over="ignore", invalid="ignore"):
        tail = np.where(np.isinf(z), 0.0, t * np.exp(-z * z + poly))
    return np.where(x >= 0, tail, 2 - tail)


def interval_mass(lower, upper, mean, sd):
    """P(lower < mean + sd * Z < upper), taking differences in the tail away from the mean."""
    lo = (lower - mean) / (SQRT2 * sd)
    hi = (upper - mean) / (SQRT2 * sd)
    mass = np.where(lo >= 0, 0.5 * (erfc(lo) - erfc(hi)), 0.5 * (erfc(-hi) - erfc(-lo)))
    return np.maximum(mass, 0)


def report_edges(reports):
    p = np.asarray(reports, dtype=float)
    if np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError("Probability reports must be finite and between zero and one")
    if not np.allclose(p * 100, np.round(p * 100), atol=1e-8, rtol=0):
        raise ValueError("Reports must use whole percentages")
    return logit(np.maximum(p - 0.005, 0)), logit(np.minimum(p + 0.005, 1))


def report_log_likelihood(means, reports, sd):
    """Latent log-odds means carry leading grid axes; the final axis indexes reports."""
    lower, upper = report_edges(reports)
    mass = interval_mass(lower, upper, means, sd)
    return np.log(np.maximum(mass, LOG_FLOOR)).sum(axis=-1)


def sample_reports(means, sd, rng):
    noisy = np.asarray(means, dtype=float) + rng.normal(0, sd, np.shape(means))
    return np.round(sigmoid(noisy) * 100) / 100


def wtp_edges(wtp):
    w = np.asarray(wtp, dtype=float)
    if np.any(~np.isfinite(w)) or np.any(w < 0) or not np.allclose(w, np.round(w)):
        raise ValueError("Willingness to pay must be whole, nonnegative points")
    # A latent value below one half point, including any negative value, is reported as zero.
    return np.where(w == 0, -np.inf, w - 0.5), w + 0.5


def wtp_log_likelihood(means, wtp, sd):
    lower, upper = wtp_edges(wtp)
    mass = interval_mass(lower, upper, means, sd)
    return np.log(np.maximum(mass, LOG_FLOOR)).sum(axis=-1)


def sample_wtp(means, sd, rng):
    noisy = np.asarray(means, dtype=float) + rng.normal(0, sd, np.shape(means))
    return np.maximum(np.round(noisy), 0)
