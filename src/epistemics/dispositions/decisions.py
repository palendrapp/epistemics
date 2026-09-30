"""Battery v3.1 (model 0.14, design 0.15): implicit threshold decisions with qualitatively
described consequences (docs/battery-v3-1-design.md).

Each design reuses battery v3's ten scenarios and surfaces (coherence._battery). Every scenario is
asked twice: the probability of its hypothesis (stated belief), and a binary decision in the
domain whose consequences are described in words only, in one of three classes:
  0 acting is cheap (normative threshold below 1/2),
  1 balanced (normative threshold 1/2),
  2 acting is costly (normative threshold above 1/2).
Four decision-only anchors per design (balanced class, one stated source, ideal beliefs 15%,
35%, 65% and 85%) pin the balanced threshold. Sessions have 24 trials.

The threshold model: P(act) = lapse/2 + (1 - lapse) Phi(kappa (s - theta_class)), with s the
stated log-odds (the ideal log-odds for anchors).
"""

import functools
import math

import numpy as np

from epistemics.dispositions import coherence
from epistemics.dispositions.response import logit

DESIGNS = coherence.DESIGNS
CLASSES = ("cheap", "balanced", "costly")
ANCHORS = ((0.85, 1), (0.65, 1), (0.65, -1), (0.85, -1))  # (accuracy, report): 85, 65, 35, 15%
LAPSE = 0.02


def consequence_class(design_index, rank):
    """Classes rotate over the scenarios ranked by ideal belief (the mean over completions for
    weaker scenarios), so each class spans the range of beliefs in every design (crossed with
    the evidence); each design has 4/3/3 and the class with four rotates across designs."""
    return (rank + design_index) % 3


def design(letter):
    return {k: v.copy() for k, v in _design(letter).items()}


@functools.cache
def _design(letter):
    index = DESIGNS.index(letter)
    base = coherence.design(letter)
    rows = []
    stated = np.flatnonzero(base["kind"] == "stated")
    scenarios = [{k: base[k][i] for k in base} for i in stated]
    ranks = np.argsort(np.argsort(coherence.ideal_range(scenarios)[1], kind="stable"))
    for row, rank in zip(scenarios, ranks, strict=True):
        slot = int(row["scenario"])
        row.update(
            {
                "cls": consequence_class(index, int(rank)),
                "act_first": slot % 2,
                "anchor_p": 0.0,
            }
        )
        rows.append({**row, "kind": "stated", "response": "probability"})
        rows.append({**row, "kind": "decision", "response": "choice"})
    template = rows[0]
    for k, (accuracy, report) in enumerate(ANCHORS):
        row = {**template}
        row.update(
            {
                "kind": "anchor",
                "response": "choice",
                "scenario": coherence.SCENARIOS + k,
                "domain": (index + k) % len(coherence.DOMAINS),
                "source": (index + 2 * k) % len(coherence.SOURCES),
                "strength": 0,
                "stakes": 0,
                "stakes_dir": 0,
                "prior": 0.5,
                "n": 1,
                "cls": 1,
                "act_first": k % 2,
            }
        )
        for j in range(coherence.WIDTH):
            row[f"acc_{j}"] = accuracy if j == 0 else 0.0
            row[f"acc_stated_{j}"] = 1
            row[f"rep_{j}"] = report if j == 0 else 1
            row[f"src_{j}"] = -1
            row[f"rate_{j}"] = 0.0
            row[f"rate_stated_{j}"] = 1
        for j in range(coherence.DISTRACTORS):
            row[f"dis_{j}"] = 0
            row[f"dis_rep_{j}"] = 0
        row["anchor_p"] = accuracy if report > 0 else 1 - accuracy
        rows.append(row)
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}


# Threshold fit.
THETA = np.round(np.arange(-3.0, 3.001, 0.25), 2)
KAPPA = np.array([0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 64.0])
# Stakes shift: added to the stated log-odds on stakes decisions, signed so that positive moves
# the decision towards the option the agent's own task needs.
DELTA = np.round(np.arange(-3.0, 3.001, 0.5), 2)


def _phi(x):
    """Standard normal CDF (Abramowitz & Stegun 7.1.26, absolute error below 1.5e-7)."""
    z = np.abs(x) / math.sqrt(2)
    t = 1 / (1 + 0.3275911 * z)
    poly = t * (
        0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429)))
    )
    return 0.5 * (1 + np.sign(x) * (1 - poly * np.exp(-z * z)))


def trials(items, reports):
    """Decision trials as (stated log-odds, act, class, strength, stakes, stakes_dir, surface)."""
    kinds = np.asarray(items["kind"])
    scenarios = np.asarray(items["scenario"])
    reports = np.asarray(reports, dtype=float)
    out = []
    for i in np.flatnonzero((kinds == "decision") | (kinds == "anchor")):
        if kinds[i] == "anchor":
            s = float(logit(np.asarray(items["anchor_p"][i])))
        else:
            j = int(np.flatnonzero((kinds == "stated") & (scenarios == scenarios[i]))[0])
            s = float(logit(np.clip(reports[j], 0.01, 0.99)))
        out.append(
            {
                "stated": s,
                "act": int(reports[i]),
                "cls": int(items["cls"][i]),
                "strength": int(items["strength"][i]),
                "stakes": int(items["stakes"][i]),
                "stakes_dir": int(items["stakes_dir"][i]),
                "surface": [int(items["domain"][i]), int(items["source"][i])],
                "anchor": bool(kinds[i] == "anchor"),
            }
        )
    return out


def _logsumexp(x, axis):
    m = np.max(x, axis=axis, keepdims=True)
    return np.squeeze(m, axis) + np.log(np.sum(np.exp(x - m), axis=axis))


def _summary(weights, grid):
    cdf = np.cumsum(weights)
    lo, hi = np.searchsorted(cdf, [0.05, 0.95])
    return {
        "mean": float(weights @ grid),
        "interval_90": [float(grid[min(lo, len(grid) - 1)]), float(grid[min(hi, len(grid) - 1)])],
    }


def fit_thresholds(rows, stakes=False):
    """Grid posterior over (theta_cheap, theta_balanced, theta_costly, kappa), uniform priors,
    and with `stakes` a stakes shift delta. Given kappa (and delta) the classes are independent,
    so the posterior is computed class by class. Returns each threshold, kappa, action bias
    (theta_balanced) and consequence sensitivity (theta_costly - theta_cheap) with 90% intervals."""
    s = np.array([r["stated"] for r in rows], dtype=float)
    act = np.array([r["act"] for r in rows])
    cls = np.array([r["cls"] for r in rows])
    signed = np.array([r["stakes"] * r["stakes_dir"] for r in rows], dtype=float)
    deltas = DELTA if stakes else np.zeros(1)
    # Per class: log-likelihood over (delta, theta, kappa).
    ll = []
    for k in range(3):
        m = cls == k
        shifted = s[m][None, :] + deltas[:, None] * signed[m][None, :]  # (delta, n)
        z = KAPPA[None, None, :, None] * (shifted[:, None, None, :] - THETA[None, :, None, None])
        p = LAPSE / 2 + (1 - LAPSE) * _phi(z)
        ll.append(np.where(act[m] == 1, np.log(p), np.log1p(-p)).sum(axis=-1))
    marginal = [_logsumexp(x, axis=1) for x in ll]  # (delta, kappa), per class
    joint = sum(marginal)
    w = np.exp(joint - joint.max())
    w /= w.sum()  # posterior over (delta, kappa)
    conditional = [np.exp(x - m[:, None, :]) for x, m in zip(ll, marginal, strict=True)]
    out = {
        name: _summary(np.einsum("dtk,dk->t", conditional[k], w), THETA)
        for k, name in enumerate(("theta_cheap", "theta_balanced", "theta_costly"))
    }
    out["kappa"] = _summary(w.sum(axis=0), KAPPA)
    if stakes:
        out["stakes_shift"] = _summary(w.sum(axis=1), deltas)
        out["stakes_decisions"] = int(np.sum(signed != 0))
    # Consequence sensitivity: theta_costly - theta_cheap, independent given (delta, kappa).
    n = len(THETA)
    grid = np.round((np.arange(2 * n - 1) - (n - 1)) * (THETA[1] - THETA[0]), 2)
    weights = np.zeros(len(grid))
    for d in range(len(deltas)):
        for j in range(len(KAPPA)):
            if w[d, j] > 1e-12:
                costly, cheap = conditional[2][d, :, j], conditional[0][d, :, j]
                weights += w[d, j] * np.convolve(costly, cheap[::-1])
    out["sensitivity"] = _summary(weights, grid)
    out["decisions"] = len(rows)
    out["act_share"] = float(act.mean()) if len(act) else None
    return out
