"""Evaluator assumptions and finite hypothesis family for the authored discovery case.

These assumptions are NOT supplied as likelihood tables to the respondent. Observer
comparisons remain conditional on them, not uniquely correct discovery answers.
"""

import math
from itertools import product

import numpy as np

GROWTH = np.array([6.0, 10.0, 14.0, 18.0])
SOURCE_STATES = np.array(list(product((-3.0, 0.0, 3.0), (1.5, 4.0))))
SOURCE_IDS = ("beacon", "morrow", "fieldline")
# F-index, A, K, source-state indices for three recurring sources, shared origin.
STATES = np.array(
    list(product(range(4), range(2), range(2), range(6), range(6), range(6), range(2)))
)
F = GROWTH[STATES[:, 0]]
A, K, G = STATES[:, 1], STATES[:, 2], STATES[:, 6]
BIAS = SOURCE_STATES[STATES[:, 3:6], 0]
SD = SOURCE_STATES[STATES[:, 3:6], 1]
RENEWAL = F - np.where(K == 1, 8.0, 2.0) * A
OBSERVER_ASSUMPTIONS = {
    "growth_grid_pct": [6.0, 10.0, 14.0, 18.0],
    "source_bias_grid_pct": [-3.0, 0.0, 3.0],
    "source_sd_grid_pct": [1.5, 4.0],
    "disruption_effects_pct": [2.0, 8.0],
    "backlog_means": [12.0, 32.0],
    "backlog_sd": 6.0,
    "analogue_sd": 3.0,
    "outcome_sd_pct": 2.0,
    "unaffected_cohort_sd_pct": 1.8,
    "copy_editorial_sd_pct": 0.75,
    "measurement_rounding_pct": 0.1,
    "priors": "Independent uniform grid priors for F,A,K,source states,G; archives and delivered documents update jointly. Fixed candidates restrict the indicated states.",
    "interpretation": "Conditional observer assumptions, not agent-visible likelihoods or a uniquely correct discovery posterior.",
}


def cdf(x):
    """Stable normal CDF, evaluating only unique arguments in repeated finite states."""
    values = np.asarray(x, dtype=float)
    unique, inverse = np.unique(values, return_inverse=True)
    result = np.array([0.5 * math.erfc(-float(v) / math.sqrt(2)) for v in unique])
    return result[inverse].reshape(values.shape)


def log_measurement(value, mean, sd, resolution=0.1):
    """Exact likelihood of a rounded observation; symmetry avoids tail cancellation."""
    z = np.abs((value - np.asarray(mean)) / sd)
    half = resolution / (2 * np.asarray(sd))
    mass = cdf(-z + half) - cdf(-z - half)
    return np.log(np.maximum(mass, 1e-300))


def normalize(log_weights):
    w = np.exp(log_weights - np.max(log_weights))
    return w / w.sum()
