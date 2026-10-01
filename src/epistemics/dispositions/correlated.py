"""Correlated changes (design 0.27; docs/statement-updating-design.md, exploration log idea 21).

Statements that differ from the previous one in exactly two substantive places, which agree (the
same direction) or disagree. A pair of consecutive cases reports one change, then both; the agent
answers after each. Every item appears in both orders across forms, so each change is seen once
first and once second.

  step 1 = answer after one change - the stated prior   (log-odds)
  step 2 = answer after both - answer after one

How the second step relates to the changes' first steps separates three readings:
  step2(X) = a * step1(X) + b * step1(other)
  independent evidence (log-odds add):        a = 1,   b = 0
  correlated changes (signs of one stance):   a ~ 1,   b < 0 (an agreeing second change was
                                              partly expected; a disagreeing one was not)
  averaging:                                  a = 1/2, b = -1/2
"""

import functools

import numpy as np

from epistemics.dispositions import statements as st
from epistemics.dispositions.screen import logit

FORMS = ("a", "b", "c", "d")
MODULES = tuple(f"correlated-{f}" for f in FORMS)
PAIRS = tuple((a, b) for i, a in enumerate(st.SLOTS) for b in st.SLOTS[i + 1 :])  # ten


@functools.cache
def items_spec():
    """24 items: twelve that agree, twelve that disagree; the stated prior keeps the final answer
    mid-range (30% when both changes are dovish, 70% when both hawkish, 50% when they differ)."""
    out = []
    for k in range(24):
        a, b = PAIRS[k % len(PAIRS)]
        agree = k % 2 == 0
        first = 1 if (k // 2) % 2 == 0 else -1
        second = first if agree else -first
        levels = {s: ((k + j) % 3) - 1 for j, s in enumerate(st.SLOTS)}
        for slot, d in ((a, first), (b, second)):
            levels[slot] = 0 if (k // 4) % 2 == 0 else -d  # room for the move
        prior = 50 if not agree else (30 if first == 1 else 70)
        out.append(
            {
                "id": 201 + k,
                "prior": prior,
                "levels": levels,
                "styles": {s: (k >> j) & 1 for j, s in enumerate(st.STYLES)},
                "background": ((k + 1) % 4, (k // 3) % 3),
                "changes": ((a, first), (b, second)),
                "agree": agree,
            }
        )
    return tuple(out)


def _order(k, form):
    """Items 0-11 in forms a and b, 12-23 in c and d; the second form of each pair reverses the
    order."""
    return 0 if form in ("a", "c") else 1


def design(module):
    return {k: v.copy() for k, v in _design(module).items()}


@functools.cache
def _design(module):
    form = module.split("-")[-1]
    items = range(0, 12) if form in ("a", "b") else range(12, 24)
    rows = []
    for k in items:
        spec = items_spec()[k]
        order = spec["changes"] if _order(k, form) == 0 else spec["changes"][::-1]
        for step in (1, 2):
            rows.append({"kind": "pair", "item": k, "sequence": k, "step": step,
                         "first": order[0][0], "first_direction": order[0][1],
                         "second": order[1][0], "second_direction": order[1][1],
                         "agree": spec["agree"], "prior": spec["prior"], "form": form,
                         "response": "probability"})  # fmt: skip
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}


def respond(items, truth, rng):
    """A simulated respondent: lambda = w[slot] * direction per change; after one change the
    log-odds move by lambda_1; after both, by lambda_1 + (lambda_2 - c * lambda_1) (correlation c),
    or to the mean of the two (averaging); log-odds noise tau; whole percentages."""
    out = np.zeros(len(items["kind"]))
    for i in range(len(out)):
        prior = float(logit(int(items["prior"][i]) / 100))
        l1 = truth["w"][str(items["first"][i])] * int(items["first_direction"][i])
        l2 = truth["w"][str(items["second"][i])] * int(items["second_direction"][i])
        if int(items["step"][i]) == 1:
            z = prior + l1
        elif truth.get("averaging"):
            z = prior + (l1 + l2) / 2
        else:
            z = prior + l1 + l2 - truth["c"] * l1
        z += rng.normal(0, truth["tau"])
        out[i] = float(np.clip(np.round(1 / (1 + np.exp(-z)), 2), 0, 1))
    return out


def session(items, responses):
    """Per item: the order, the answers after one change and after both, and both steps."""
    responses = np.asarray(responses, dtype=float)
    rows = []
    for k in sorted(set(int(v) for v in items["item"])):
        idx = sorted(np.flatnonzero(items["item"] == k), key=lambda i: int(items["step"][i]))
        i1, i2 = idx
        prior = float(logit(int(items["prior"][i1]) / 100))
        z1, z2 = float(logit(responses[i1])), float(logit(responses[i2]))
        rows.append({"item": k, "agree": bool(items["agree"][i1]),
                     "first": [str(items["first"][i1]), int(items["first_direction"][i1])],
                     "second": [str(items["second"][i1]), int(items["second_direction"][i1])],
                     "answers": [float(responses[i1]), float(responses[i2])],
                     "step1": z1 - prior, "step2": z2 - z1, "total": z2 - prior})  # fmt: skip
    return {"form": str(items["form"][0]), "items": rows,
            "responses": [float(v) for v in responses]}  # fmt: skip


def fit(rows):
    """Pool both orders of each item: for each change X, its first step (from the order where it
    came first) and its second step (from the order where it came second), against the other
    change's first step. Least squares for step2(X) = a step1(X) + b step1(other)."""
    by = {}
    for r in rows:
        by.setdefault(r["item"], []).append(r)
    xs, ys, agree = [], [], []
    for orders in by.values():
        if len(orders) != 2:
            continue
        first = {tuple(o["first"]): o["step1"] for o in orders}
        for o in orders:
            x = tuple(o["second"])
            other = tuple(o["first"])
            if x in first and other in first:
                xs.append([first[x], first[other]])
                ys.append(o["step2"])
                agree.append(o["agree"])
    if len(ys) < 3:
        return None
    X, y = np.array(xs), np.array(ys)
    a, b = np.linalg.lstsq(X, y, rcond=None)[0]
    return {"a": float(a), "b": float(b), "n": len(ys), "rows": (X, y, np.array(agree))}
