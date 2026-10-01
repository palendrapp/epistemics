"""Deliberation style: judging against computing (model 0.21, design 0.22;
docs/deliberation-style-design.md).

Four trend series (the screen's F5 surfaces: three readings of a growing quantity) are asked
about in two modules:

  ladder        each series at six nearby thresholds, "the probability that it will be above t
                at x", 24 cases; a series' six questions at least four cases apart ("sets" order).
  anchor-a/b    three of each series' thresholds as a consecutive pair of cases: a comparison
                (choice: above or below an anchor, a number chosen for the exercise and carrying
                no information) and then the estimate; 24 cases. Low anchors are 30 points below
                a broad observer's answer, high anchors 30 above; forms a and b swap them.

Thresholds are spaced so that a broad observer (linear weight 0.55, noise 0.25: a wide
predictive distribution, like the screen's compressed GPT-6 extrapolations) changes by 5 points
per step; the screen's middle observer, bimodal and narrow, changes by 8-14.

Two parameters:
  rho   readout grain: the share of answers reported to the nearest 5 points rather than the
        nearest point, from the share of mid-range answers (0.06-0.94) at multiples of 5 beyond
        the 1 in 5 that a 1-point readout gives by chance (after Manski & Molinari 2010).
  a     anchoring weight: the estimate is (1 - a) z_own + a z_anchor on the log-odds scale, so the
        difference between a threshold's estimates after the high and low anchors is a times the
        anchors' difference (the agent's own answer cancels); 1 - a is the completeness of
        adjustment (Lieder, Griffiths, Huys & Goodman 2018).
"""

import functools

import numpy as np

from epistemics.dispositions import screen

# (surface, readings at 1, 2 and 3, time asked, identifier): tickets, storage, users, orders.
SERIES = (
    (1, (24, 33, 47), 6, 14),
    (2, (120, 166, 232), 5, 27),
    (3, (300, 410, 570), 5, 38),
    (4, (60, 81, 112), 6, 52),
)
# Follow-up (design 0.23): four more series, so that the bare module keeps three thresholds per
# series in 24 cases. Ladders and anchors use SERIES only.
EXTRA = (
    (0, (50, 70, 98), 6, 63),
    (2, (80, 112, 157), 6, 71),
    (3, (200, 280, 392), 5, 86),
    (4, (90, 125, 175), 5, 95),
)
ALL_SERIES = SERIES + EXTRA
BROAD = {"linear_weight": 0.55, "noise": 0.25}
TARGETS = (0.64, 0.59, 0.54, 0.49, 0.44, 0.39)  # the broad observer's answers on each ladder
ANCHORED = (1, 3, 5)  # ladder ranks asked with anchors
SHIFT = 30  # anchor distance from the broad observer's answer, in points
MID = (0.06, 0.94)
MODULES = ("deliberation-ladder", "deliberation-anchor-a", "deliberation-anchor-b")
BARE = "deliberation-bare"  # the anchored thresholds asked directly, with no comparison


def _data(s, t):
    surface, ys, x, ident = ALL_SERIES[s]
    return {"xs": [1, 2, 3], "ys": list(ys), "x": x, "question": "above", "threshold": int(t),
            "surface": surface, "id": ident}  # fmt: skip


def observer(s, t, params):
    return screen._trend_revised(_data(s, t), params)


@functools.cache
def thresholds(s):
    """Six integer thresholds at which the broad observer answers TARGETS."""
    _, ys, _, _ = ALL_SERIES[s]
    grid = np.arange(int(ys[-1]), int(ys[-1] * 8))
    probs = np.array([observer(s, t, BROAD) for t in grid])
    out = tuple(int(grid[np.argmin(np.abs(probs - q))]) for q in TARGETS)
    assert all(b > a for a, b in zip(out, out[1:], strict=False)), (s, out)
    return out


def anchor_value(s, rank, side):
    p = observer(s, thresholds(s)[rank], BROAD)
    value = round(100 * p) + (SHIFT if side == "high" else -SHIFT)
    return int(min(95, max(5, value)))


def _side(s, k, form):
    """Form a: series 0 and 2 start low, 1 and 3 start high, alternating over the three ranks;
    form b swaps every side."""
    low_first = s % 2 == 0
    low = (k % 2 == 0) == low_first
    if form == "b":
        low = not low
    return "low" if low else "high"


def _rows(module):
    rows = []
    if module == BARE:
        for s in range(len(ALL_SERIES)):
            for rank in ANCHORED:
                rows.append({"kind": "bare", "set": -1, "series": s, "rank": rank,
                             "threshold": thresholds(s)[rank], "sequence": -1, "step": 0,
                             "anchor": 0, "side": "", "response": "probability",
                             "form": "bare"})  # fmt: skip
        return rows
    if module == "deliberation-ladder":
        for s in range(len(SERIES)):
            for rank, t in enumerate(thresholds(s)):
                rows.append({"kind": "ladder", "set": s, "series": s, "rank": rank,
                             "threshold": t, "sequence": -1, "step": 0, "anchor": 0, "side": "",
                             "response": "probability", "form": "ladder"})  # fmt: skip
        return rows
    form = module[-1]
    pair = 0
    for s in range(len(SERIES)):
        for k, rank in enumerate(ANCHORED):
            side = _side(s, k, form)
            t = thresholds(s)[rank]
            base = {"set": -1, "series": s, "rank": rank, "threshold": t, "sequence": pair,
                    "anchor": anchor_value(s, rank, side), "side": side, "form": form}  # fmt: skip
            rows.append({**base, "kind": "choice", "step": 0, "response": "choice"})
            rows.append({**base, "kind": "estimate", "step": 1, "response": "probability"})
            pair += 1
    return rows


def design(module):
    return {k: v.copy() for k, v in _design(module).items()}


@functools.cache
def _design(module):
    rows = _rows(module)
    assert len(rows) == 24, module
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}


def ladder_order(items, rng):
    """Every series' six questions exactly four cases apart: the series in a random rotation, each
    series' thresholds in random order. (With four series of six, four apart is only possible
    cyclically.) Uses only shuffle."""
    series = sorted(set(int(v) for v in items["series"]))
    rng.shuffle(series)
    queues = {}
    for s in series:
        idx = [int(i) for i in np.flatnonzero(items["series"] == s)]
        rng.shuffle(idx)
        queues[s] = idx
    return [queues[s][r] for r in range(len(queues[series[0]])) for s in series]


def options(items, i):
    """A comparison case's options; "Above" is option 0 and is coded 1."""
    a = int(items["anchor"][i])
    return [f"Above {a}%", f"Below {a}%"], 0


# Simulated respondents.
def _report(p, rho, rng):
    grain = 0.05 if rng.random() < rho else 0.01
    return float(np.clip(np.round(p / grain) * grain, 0, 1).round(2))


def respond(items, truth, rng):
    """truth: params (the trend observer's), rho, tau (log-odds report noise), a (anchoring
    weight). Ladder and estimate answers in probability; comparison cases 1 (above) or 0."""
    out = np.zeros(len(items["kind"]))
    for i in range(len(out)):
        s, t = int(items["series"][i]), int(items["threshold"][i])
        own = observer(s, t, truth["params"])
        kind = str(items["kind"][i])
        if kind == "choice":
            out[i] = 1.0 if own > items["anchor"][i] / 100 else 0.0
            continue
        z = float(screen.logit(own))
        if kind == "estimate":
            z = (1 - truth["a"]) * z + truth["a"] * float(screen.logit(items["anchor"][i] / 100))
        z += rng.normal(0, truth["tau"])
        out[i] = _report(float(screen._sigmoid(z)), truth["rho"], rng)
    return out


# Session summaries and estimates.
def _mid(v):
    return MID[0] <= v <= MID[1]


def grain(values):
    """rho from the share of mid-range answers at multiples of 5 (Beta posterior, flat prior):
    rho = (share - 0.2) / 0.8."""
    v = [x for x in values if _mid(x)]
    k = sum(round(x * 100) % 5 == 0 for x in v)
    n = len(v)
    draws = np.random.default_rng(20261118).beta(1 + k, 1 + n - k, 4000)
    rho = np.clip((draws - 0.2) / 0.8, 0, 1)
    return {
        "share_5": k / n if n else None,
        "share_10": (sum(round(x * 100) % 10 == 0 for x in v) / n) if n else None,
        "n": n,
        "rho": {
            "mean": float(np.mean(rho)),
            "interval_90": [float(np.percentile(rho, 5)), float(np.percentile(rho, 95))],
        },
    }


def ladders(items, responses):
    out = []
    for s in range(len(SERIES)):
        idx = sorted(np.flatnonzero(items["series"] == s), key=lambda i: int(items["rank"][i]))
        values = [float(responses[i]) for i in idx]
        steps = np.diff(values)
        out.append(
            {
                "series": s,
                "thresholds": [int(items["threshold"][i]) for i in idx],
                "answers": values,
                "violations": int(np.sum(steps > 0)),
                "plateaus": int(np.sum(steps == 0)),
            }
        )
    return out


def pairs(items, responses):
    out = []
    for k in sorted(set(int(v) for v in items["sequence"]) - {-1}):
        idx = sorted(np.flatnonzero(items["sequence"] == k), key=lambda i: int(items["step"][i]))
        choice, estimate = float(responses[idx[0]]), float(responses[idx[1]])
        anchor = int(items["anchor"][idx[0]])
        above = choice >= 0.5
        out.append(
            {
                "series": int(items["series"][idx[0]]),
                "rank": int(items["rank"][idx[0]]),
                "threshold": int(items["threshold"][idx[0]]),
                "anchor": anchor,
                "side": str(items["side"][idx[0]]),
                "above": bool(above),
                "estimate": estimate,
                "consistent": bool(estimate >= anchor / 100 if above else estimate <= anchor / 100),
            }
        )
    return out


def session(items, responses):
    responses = np.asarray(responses, dtype=float)
    form = str(items["form"][0])
    probability = [
        float(responses[i]) for i in range(len(responses)) if items["response"][i] == "probability"
    ]
    module = {"ladder": "ladder", "bare": "bare"}.get(form, "anchor")
    out = {"module": module, "form": form,
           "grain": grain(probability), "responses": [float(v) for v in responses]}  # fmt: skip
    if form == "bare":
        out["bare"] = [
            {
                "series": int(items["series"][i]),
                "threshold": int(items["threshold"][i]),
                "rank": int(items["rank"][i]),
                "answer": float(responses[i]),
            }  # fmt: skip
            for i in range(len(responses))
        ]
    elif form == "ladder":
        rows = ladders(items, responses)
        out["ladders"] = rows
        out["violations"] = sum(r["violations"] for r in rows)
        out["plateau_share"] = sum(r["plateaus"] for r in rows) / (5 * len(rows))
    else:
        rows = pairs(items, responses)
        out["pairs"] = rows
        out["consistency"] = float(np.mean([r["consistent"] for r in rows]))
    return out


def anchoring(pair_rows, seed=20261119):
    """a from each threshold's estimates after the high and the low anchor (forms a and b), on the
    log-odds scale: (z_high - z_low) / (z_anchor_high - z_anchor_low); mean over thresholds,
    bootstrap interval. Also the Jacowitz & Kahneman index in probability points."""
    by = {}
    for r in pair_rows:
        by.setdefault((r["series"], r["rank"]), {})[r["side"]] = r
    ratios, indices = [], []
    for sides in by.values():
        if "low" in sides and "high" in sides:
            lo, hi = sides["low"], sides["high"]
            dz_est = float(screen.logit(hi["estimate"]) - screen.logit(lo["estimate"]))
            dz_anchor = float(screen.logit(hi["anchor"] / 100) - screen.logit(lo["anchor"] / 100))
            ratios.append(dz_est / dz_anchor)
            indices.append(
                (hi["estimate"] - lo["estimate"]) / ((hi["anchor"] - lo["anchor"]) / 100)
            )
    if not ratios:
        return None
    rng = np.random.default_rng(seed)
    ratios = np.array(ratios)
    boot = [np.mean(rng.choice(ratios, len(ratios))) for _ in range(4000)]
    return {
        "a": {
            "mean": float(np.mean(ratios)),
            "interval_90": [float(np.percentile(boot, 5)), float(np.percentile(boot, 95))],
        },
        "index": float(np.mean(indices)),
        "thresholds": len(ratios),
    }


def anchoring_on_own(pair_rows, ladder_rows):
    """Secondary: the slope of (estimate - own ladder answer) on (anchor - own ladder answer), on
    the log-odds scale (biased towards 1 by the noise of the own answer)."""
    own = {}
    for r in ladder_rows:
        for t, v in zip(r["thresholds"], r["answers"], strict=True):
            own[(r["series"], t)] = v
    x, y = [], []
    for r in pair_rows:
        key = (r["series"], r["threshold"])
        if key in own:
            z0 = float(screen.logit(own[key]))
            x.append(float(screen.logit(r["anchor"] / 100)) - z0)
            y.append(float(screen.logit(r["estimate"])) - z0)
    if len(x) < 3:
        return None
    x, y = np.array(x), np.array(y)
    return float(x @ y / (x @ x))
