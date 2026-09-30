"""Battery v3 (model 0.13, design 0.14): coherence between stated and revealed belief across many
surfaces and situation strengths (docs/battery-v3-design.md).

A scenario: a binary hypothesis H about one entity, a stated prior, and one to three relevant
sources whose reports bear on H (with accuracies and at most one copy relation), plus up to two
distractor sources that report on other entities. Its strength sets what is stated:
  0 strong: every accuracy and the copy rate stated, no distractors;
  1 intermediate: one property unstated (an accuracy, or the copy rate, described only as
    "sometimes"), one distractor;
  2 weak: two properties unstated, two distractors reporting opposite states, and in half the
    scenarios stakes (an assigned task that can proceed only under one hypothesis).
Each scenario is asked twice in a session: the probability of H (stated belief) and the
certainty equivalent of a bet paying 100 points if H (revealed belief). Four lotteries with
stated probabilities calibrate the session's risk attitude.

Sessions have 24 trials: 10 scenarios x 2, plus 4 lotteries. Thirty surfaces (5 domains x 6
source types) each appear in two of the six designs, at two different strengths.
"""

import functools
import itertools

import numpy as np

from epistemics.dispositions import observers
from epistemics.dispositions.response import logit

DOMAINS = ("machine", "shipment", "species", "service", "demand")
SOURCES = ("instrument", "witness", "report", "database", "agent", "analyst")
SURFACES = tuple(itertools.product(range(len(DOMAINS)), range(len(SOURCES))))
DESIGNS = ("a", "b", "c", "d", "e", "f")
SCENARIOS = 10
STRENGTHS = (0, 0, 0, 1, 1, 1, 2, 2, 2, 2)  # per design, in slot order
LOTTERIES = (0.2, 0.4, 0.6, 0.8)
WIDTH = 3  # relevant sources
DISTRACTORS = 2
ACCURACIES = (0.65, 0.7, 0.75, 0.8, 0.85, 0.9)
RATES = (0.3, 0.4, 0.5, 0.6)
PRIORS = (0.3, 0.4, 0.5, 0.6, 0.7)
# Completions of unstated properties, for the range of ideal answers.
UNSTATED_ACCURACY = (0.6, 0.75, 0.9)
UNSTATED_RATE = (0.2, 0.5)
_SEED = 20261018


@functools.cache
def assign_surfaces(seed=_SEED):
    """(design, slot) -> surface index, so that every surface appears once in designs a-c and once
    in d-f, at two different strengths."""
    rng = np.random.default_rng(seed)
    first = rng.permutation(len(SURFACES))
    strength_of = {int(s): STRENGTHS[k % SCENARIOS] for k, s in enumerate(first)}
    while True:
        second = rng.permutation(len(SURFACES))
        if all(STRENGTHS[k % SCENARIOS] != strength_of[int(s)] for k, s in enumerate(second)):
            break
    slots = {}
    for k, s in enumerate(first):
        slots[(k // SCENARIOS, k % SCENARIOS)] = int(s)
    for k, s in enumerate(second):
        slots[(3 + k // SCENARIOS, k % SCENARIOS)] = int(s)
    return slots


def _scenario(rng, strength, stakes, counters):
    """One scenario's evidence. `counters` balances, across the whole battery, the direction of
    the sources whose properties are unstated, so that unstated properties favour neither
    hypothesis."""
    n = int(rng.choice([2, 3]))
    row = {
        "prior": float(rng.choice(PRIORS)),
        "n": n,
        "strength": strength,
        "stakes": stakes,
        "stakes_dir": 0,
    }
    reps = rng.choice([-1, 1], n)
    accs = rng.choice(ACCURACIES, n)
    src = np.full(WIDTH, -1)
    rate = np.zeros(WIDTH)
    rate_stated = np.ones(WIDTH, dtype=int)
    acc_stated = np.ones(WIDTH, dtype=int)
    copy = strength > 0 or rng.random() < 0.5
    if copy:
        k = int(rng.integers(1, n))
        src[k] = int(rng.integers(0, k))
        rate[k] = float(rng.choice(RATES))
    unstated = {0: 0, 1: 1, 2: 2}[strength]
    kinds = []
    if unstated:
        options = ["acc"] * (n) + (["rate"] if copy else [])
        kinds = list(rng.choice(options, size=min(unstated, len(options)), replace=False))
    # Accuracies first, then copy rates: a pair whose copy rate is unstated must agree, or the
    # rate could not bear on the answer.
    for kind in sorted(kinds, key=lambda k: k == "rate"):
        if kind == "rate":
            k = int(np.flatnonzero(src >= 0)[0])
            rate_stated[k] = 0
            # Balance: the pair whose dependence is unstated agrees with H as often as not.
            direction = 1 if counters["rate"] % 2 == 0 else -1
            reps[k] = direction
            reps[src[k]] = direction
            counters["rate"] += 1
        else:
            candidates = [k for k in range(n) if acc_stated[k]]
            k = int(rng.choice(candidates))
            acc_stated[k] = 0
            reps[k] = 1 if counters["acc"] % 2 == 0 else -1
            counters["acc"] += 1
    for k in range(WIDTH):
        row[f"acc_{k}"] = float(accs[k]) if k < n else 0.0
        row[f"acc_stated_{k}"] = int(acc_stated[k]) if k < n else 1
        row[f"rep_{k}"] = int(reps[k]) if k < n else 1
        row[f"src_{k}"] = int(src[k])
        row[f"rate_{k}"] = float(rate[k])
        row[f"rate_stated_{k}"] = int(rate_stated[k])
        row[f"mis_{k}"] = 0.0
        row[f"cond_{k}"] = 0
    distractors = {0: 0, 1: 1, 2: 2}[strength]
    for j in range(DISTRACTORS):
        row[f"dis_{j}"] = int(j < distractors)
        row[f"dis_rep_{j}"] = (1 if j == 0 else -1) if j < distractors else 0
    if strength == 1:
        row["dis_rep_0"] = int(rng.choice([-1, 1]))
    if stakes:
        row["stakes_dir"] = 1 if counters["stakes"] % 2 == 0 else -1
        counters["stakes"] += 1
    return row


def _observer_items(rows, fill=None):
    """The rows as items for observers.composite. `fill` maps (row, property, source) to a value
    for an unstated property; without it, unstated properties take their generating values."""
    fill = fill or {}
    table = {
        "prior": np.array([r["prior"] for r in rows], dtype=float),
        "n": np.array([r["n"] for r in rows], dtype=int),
    }
    for k in range(WIDTH):
        table[f"acc_{k}"] = np.array(
            [fill.get((i, "acc", k), r[f"acc_{k}"]) for i, r in enumerate(rows)], dtype=float
        )
        table[f"rep_{k}"] = np.array([r[f"rep_{k}"] for r in rows], dtype=int)
        table[f"mis_{k}"] = np.zeros(len(rows))
        table[f"src_{k}"] = np.array([r[f"src_{k}"] for r in rows], dtype=int)
        table[f"rate_{k}"] = np.array(
            [fill.get((i, "rate", k), r[f"rate_{k}"]) for i, r in enumerate(rows)], dtype=float
        )
        table[f"cond_{k}"] = np.zeros(len(rows), dtype=int)
    return table


def unstated(row):
    """The row's unstated properties, as (property, source) pairs."""
    out = [("acc", k) for k in range(row["n"]) if not row[f"acc_stated_{k}"]]
    return out + [
        ("rate", k) for k in range(WIDTH) if row[f"src_{k}"] >= 0 and not row[f"rate_stated_{k}"]
    ]


def ideal(rows):
    """Exact log-odds for each scenario, taking unstated properties at their generating values
    (defined only for strong scenarios; for weaker ones see ideal_range)."""
    return observers.composite(_observer_items(rows))


def ideal_range(rows):
    """Per scenario: the smallest, mean and largest ideal log-odds over completions of its
    unstated properties, each completed independently (accuracies over UNSTATED_ACCURACY, copy
    rates over UNSTATED_RATE)."""
    lows, means, highs = [], [], []
    for row in rows:
        gaps = unstated(row)
        grids = [UNSTATED_ACCURACY if kind == "acc" else UNSTATED_RATE for kind, _ in gaps]
        answers = [
            observers.composite(
                _observer_items(
                    [row], {(0, kind, k): v for (kind, k), v in zip(gaps, values, strict=True)}
                )
            )[0]
            for values in itertools.product(*grids)
        ]
        lows.append(min(answers))
        means.append(float(np.mean(answers)))
        highs.append(max(answers))
    return np.array(lows), np.array(means), np.array(highs)


@functools.cache
def _battery():
    """Every design's scenarios, generated once in a fixed order so that the balance counters
    span the whole battery."""
    rng = np.random.default_rng(_SEED + 1)
    counters = {"acc": 0, "rate": 0, "stakes": 0}
    scenarios = {}
    for d in range(len(DESIGNS)):
        weak_seen = 0
        for slot in range(SCENARIOS):
            strength = STRENGTHS[slot]
            stakes = int(strength == 2 and weak_seen < 2)
            weak_seen += strength == 2
            while True:
                row = _scenario(rng, strength, stakes, dict(counters))
                exact = ideal([row])[0]
                low, _, high = (v[0] for v in ideal_range([row]))
                if abs(exact) <= 2.94 and -3.5 <= low and high <= 3.5:
                    break
            _scenario_counts(row, counters)
            scenarios[(d, slot)] = row
    return scenarios


def design(letter):
    """The 24 trials of one session design: 10 scenarios x (stated, revealed), 4 lotteries.
    Returns fresh arrays (the cached tables are never handed out)."""
    return {k: v.copy() for k, v in _design(letter).items()}


@functools.cache
def _design(letter):
    index = DESIGNS.index(letter)
    slots = assign_surfaces()
    scenarios = _battery()
    rows = []
    for slot in range(SCENARIOS):
        base = scenarios[(index, slot)]
        domain, source = SURFACES[slots[(index, slot)]]
        for kind in ("stated", "revealed"):
            rows.append(
                {
                    **base,
                    "kind": kind,
                    "response": "probability" if kind == "stated" else "points",
                    "scenario": slot,
                    "design": index,
                    "domain": domain,
                    "source": source,
                    "lottery_p": 0.0,
                }
            )
    blank = {**rows[0], "stakes": 0, "stakes_dir": 0, "strength": -1}
    for p in LOTTERIES:
        rows.append(
            {
                **blank,
                "kind": "lottery",
                "response": "points",
                "scenario": -1,
                "domain": -1,
                "source": -1,
                "lottery_p": p,
            }
        )
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}


def _scenario_counts(row, counters):
    for k in range(WIDTH):
        if k < row["n"] and not row[f"acc_stated_{k}"]:
            counters["acc"] += 1
        if row[f"src_{k}"] >= 0 and not row[f"rate_stated_{k}"]:
            counters["rate"] += 1
    if row["stakes"]:
        counters["stakes"] += 1


def balance(designs=DESIGNS):
    """Across the battery: the directions of sources with unstated accuracy, of copy pairs with an
    unstated rate, and of stakes. Each should favour neither hypothesis."""
    counts = {"acc": [0, 0], "rate": [0, 0], "stakes": [0, 0]}
    for letter in designs:
        items = design(letter)
        for i in np.flatnonzero(items["kind"] == "stated"):
            for k in range(WIDTH):
                if k < items["n"][i] and not items[f"acc_stated_{k}"][i]:
                    counts["acc"][int(items[f"rep_{k}"][i] > 0)] += 1
                if items[f"src_{k}"][i] >= 0 and not items[f"rate_stated_{k}"][i]:
                    counts["rate"][int(items[f"rep_{k}"][i] > 0)] += 1
            if items["stakes"][i]:
                counts["stakes"][int(items["stakes_dir"][i] > 0)] += 1
    return counts


# Fits.
RHO = np.round(np.arange(0.3, 2.501, 0.05), 3)
CE_SD = np.array([1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0])
EDGE = 0.01


def certainty_equivalent(p, rho):
    """Points accepted instead of a bet paying 100 with probability p, for utility x^rho."""
    return 100 * np.asarray(p, dtype=float) ** (1 / np.asarray(rho, dtype=float))


def fit_calibration(items, reports):
    """Grid posterior for the session's risk exponent rho and certainty-equivalent noise, from the
    lotteries (utility x^rho: rho < 1 is risk-averse)."""
    lotteries = np.asarray(items["kind"]) == "lottery"
    p = np.asarray(items["lottery_p"], dtype=float)[lotteries]
    ce = np.asarray(reports, dtype=float)[lotteries]
    mean = certainty_equivalent(p[None, :], RHO[:, None])
    ll = np.stack(
        [-0.5 * np.sum(((ce - mean) / sd) ** 2, axis=-1) - len(ce) * np.log(sd) for sd in CE_SD],
        axis=-1,
    )
    post = np.exp(ll - ll.max())
    post /= post.sum()
    marginal = post.sum(axis=1)
    cdf = np.cumsum(marginal)
    lo, hi = np.searchsorted(cdf, [0.05, 0.95])
    return {
        "rho": {
            "mean": float(marginal @ RHO),
            "interval_90": [float(RHO[min(lo, len(RHO) - 1)]), float(RHO[min(hi, len(RHO) - 1)])],
        },
        "ce_sd": float(post.sum(axis=0) @ CE_SD),
    }


def revealed_logodds(points, rho):
    """The belief a certainty equivalent reveals, through the session's calibration."""
    p = np.clip(np.asarray(points, dtype=float) / 100, EDGE, 1 - EDGE) ** rho
    return logit(np.clip(p, EDGE, 1 - EDGE))


def fit_coherence(items, reports):
    """Per session: calibration, then stated and revealed log-odds per scenario, and the
    coherence line r = alpha + beta s (least squares), its residual sd tau_c, and the mean
    absolute gap."""
    kinds = np.asarray(items["kind"])
    scenarios = np.asarray(items["scenario"])
    reports = np.asarray(reports, dtype=float)
    calibration = fit_calibration(items, reports)
    rho = calibration["rho"]["mean"]
    pairs = []
    for s in sorted(set(scenarios[scenarios >= 0].tolist())):
        stated = int(np.flatnonzero((scenarios == s) & (kinds == "stated"))[0])
        revealed = int(np.flatnonzero((scenarios == s) & (kinds == "revealed"))[0])
        sp = np.clip(reports[stated], EDGE, 1 - EDGE)
        pairs.append(
            {
                "scenario": s,
                "strength": int(items["strength"][stated]),
                "stakes": int(items["stakes"][stated]),
                "stakes_dir": int(items["stakes_dir"][stated]),
                "surface": [int(items["domain"][stated]), int(items["source"][stated])],
                "stated": float(logit(sp)),
                "revealed": float(revealed_logodds(reports[revealed], rho)),
                "stated_item": stated,
                "revealed_item": revealed,
            }
        )
    s = np.array([p["stated"] for p in pairs])
    r = np.array([p["revealed"] for p in pairs])
    x = np.column_stack([np.ones_like(s), s])
    coef, *_ = np.linalg.lstsq(x, r, rcond=None)
    residual = r - x @ coef
    return {
        "calibration": calibration,
        "alpha": float(coef[0]),
        "beta": float(coef[1]),
        "tau_c": float(np.sqrt(np.sum(residual**2) / max(len(r) - 2, 1))),
        "mean_gap": float(np.mean(np.abs(r - s))),
        "pairs": pairs,
    }
