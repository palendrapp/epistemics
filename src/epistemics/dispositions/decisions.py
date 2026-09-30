"""Batteries v3.1 and v3.2: implicit threshold decisions with consequences described in words
(docs/battery-v3-1-design.md, docs/battery-v3-2-design.md).

Each design reuses battery v3's ten scenarios and surfaces (coherence._battery). Every scenario is
asked twice: the probability of its hypothesis (stated belief), and a binary decision in the
domain whose consequences are described in words only, in one of the scheme's classes. Four
decision-only anchors per design (one source with a stated accuracy, fixed ideal beliefs) add
decisions at known beliefs. Sessions have 24 trials.

Schemes:
  v31 (model 0.14): cheap / balanced / costly. The pilot found the cheap and costly texts so
      asymmetric that they acted as rules at every belief.
  v32 (model 0.15): mildly cheap / balanced / mildly costly (graded wording), and two classes
      whose mistakes cost different kinds of thing: acting protects people or nature at a
      commercial cost (welfare_act), or acting costs people or nature while holding costs
      commercially (welfare_hold). The welfare classes have no normative threshold.

The threshold model: P(act) = lapse/2 + (1 - lapse) Phi(kappa (s - theta_class)), with s the
stated log-odds (the ideal log-odds for anchors).
"""

import functools
import math

import numpy as np

from epistemics.dispositions import coherence
from epistemics.dispositions.response import logit

DESIGNS = coherence.DESIGNS
LAPSE = 0.02
SCHEMES = {
    "v31": {
        "classes": ("cheap", "balanced", "costly"),
        # (accuracy, report): ideal beliefs 85, 65, 35 and 15%.
        "anchors": ((0.85, 1), (0.65, 1), (0.65, -1), (0.85, -1)),
        "anchor_classes": "balanced",
        # Contrasts: name -> (plus class, minus class, scale).
        "contrasts": {"sensitivity": ("costly", "cheap", 1.0)},
    },
    "v32": {
        "classes": ("mild_cheap", "balanced", "mild_costly", "welfare_act", "welfare_hold"),
        # Ideal beliefs 80, 60, 40 and 20%.
        "anchors": ((0.8, 1), (0.6, 1), (0.6, -1), (0.8, -1)),
        "anchor_classes": "rotate",
        "contrasts": {
            "sensitivity": ("mild_costly", "mild_cheap", 1.0),
            # Half the difference: the log of the implicit ratio of the harm to people or nature
            # to the commercial harm (positive weighs people or nature more).
            "welfare_weight": ("welfare_hold", "welfare_act", 0.5),
        },
    },
}
# Battery v3.1 names, kept for its analyses.
CLASSES = SCHEMES["v31"]["classes"]
ANCHORS = SCHEMES["v31"]["anchors"]


def consequence_class(design_index, rank, classes=3):
    """Classes rotate over the scenarios ranked by ideal belief (the mean over completions for
    weaker scenarios), so each class spans the range of beliefs in every design (crossed with
    the evidence); the classes with an extra scenario rotate across designs."""
    return (rank + design_index) % classes


def design(letter, scheme="v31"):
    return {k: v.copy() for k, v in _design(letter, scheme).items()}


@functools.cache
def _design(letter, scheme="v31"):
    spec = SCHEMES[scheme]
    classes = len(spec["classes"])
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
                "cls": consequence_class(index, int(rank), classes),
                "act_first": slot % 2,
                "anchor_p": 0.0,
            }
        )
        rows.append({**row, "kind": "stated", "response": "probability"})
        rows.append({**row, "kind": "decision", "response": "choice"})
    template = rows[0]
    balanced = spec["classes"].index("balanced")
    for k, (accuracy, report) in enumerate(spec["anchors"]):
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
                "cls": balanced if spec["anchor_classes"] == "balanced" else (index + k) % classes,
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
# Model 0.15: step 0.125 (0.25 before); intervals run to the edges of their grid cells, since a
# sharp posterior otherwise sits on one grid point that the truth lies between.
THETA = np.round(np.arange(-3.0, 3.001, 0.125), 3)
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


def _summary(weights, grid, cell=0.0):
    """Posterior mean and 90% interval; with `cell`, the interval runs to the edges of the grid
    cells (half a step either side of the grid points)."""
    cdf = np.cumsum(weights)
    lo, hi = np.searchsorted(cdf, [0.05, 0.95])
    return {
        "mean": float(weights @ grid),
        "interval_90": [
            float(grid[min(lo, len(grid) - 1)] - cell / 2),
            float(grid[min(hi, len(grid) - 1)] + cell / 2),
        ],
    }


def fit_thresholds(rows, stakes=False, scheme="v31"):
    """Grid posterior over the scheme's class thresholds and kappa, uniform priors, and with
    `stakes` a stakes shift delta. Given kappa (and delta) the classes are independent, so the
    posterior is computed class by class. Returns each threshold (theta_<class>), kappa, and the
    scheme's contrasts (for example consequence sensitivity, theta_costly - theta_cheap) with
    90% intervals."""
    spec = SCHEMES[scheme]
    names = spec["classes"]
    s = np.array([r["stated"] for r in rows], dtype=float)
    act = np.array([r["act"] for r in rows])
    cls = np.array([r["cls"] for r in rows])
    signed = np.array([r["stakes"] * r["stakes_dir"] for r in rows], dtype=float)
    deltas = DELTA if stakes else np.zeros(1)
    step = float(THETA[1] - THETA[0])
    # Per class: log-likelihood over (delta, theta, kappa).
    ll = []
    for k in range(len(names)):
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
        f"theta_{name}": _summary(np.einsum("dtk,dk->t", conditional[k], w), THETA, step)
        for k, name in enumerate(names)
    }
    out["kappa"] = _summary(w.sum(axis=0), KAPPA)
    n = len(THETA)
    if stakes:
        out["stakes_shift"] = _summary(w.sum(axis=1), deltas)
        out["stakes_decisions"] = int(np.sum(signed != 0))
    # Contrasts: theta_plus - theta_minus (scaled), independent given (delta, kappa).
    for contrast, (plus, minus, scale) in spec["contrasts"].items():
        grid = np.round((np.arange(2 * n - 1) - (n - 1)) * step * scale, 3)
        weights = np.zeros(len(grid))
        a, b = conditional[names.index(plus)], conditional[names.index(minus)]
        for d in range(len(deltas)):
            for j in range(len(KAPPA)):
                if w[d, j] > 1e-12:
                    weights += w[d, j] * np.convolve(a[d, :, j], b[d, ::-1, j])
        out[contrast] = _summary(weights, grid, step * scale)
    out["scheme"] = scheme
    out["decisions"] = len(rows)
    out["act_share"] = float(act.mean()) if len(act) else None
    return out
