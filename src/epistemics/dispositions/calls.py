"""Analysts' calls in order (design 0.28; exploration log idea 24).

Primacy beyond statements: an urn with a stated prior and two analysts' calls, phrased in one of
three ways and given without a record (the agent judges what a call is worth). A pair of
consecutive cases reports one call, then both; every item appears in both orders across forms.
The rows match the correlated-changes rows, so the same analyses apply (ledger.correlated,
ledger.primacy): step2(X) = a step1(X) + b step1(other), and the same call's step second against
first.
"""

import functools

import numpy as np

from epistemics.dispositions.screen import logit

FORMS = ("a", "b", "c", "d")
MODULES = tuple(f"calls-{f}" for f in FORMS)


@functools.cache
def items_spec():
    """24 items: twelve whose calls agree, twelve whose calls disagree; phrases mixed; the stated
    prior keeps the final answer mid-range (40% when both say red, 60% when both say blue, 50%
    when they disagree)."""
    out = []
    for k in range(24):
        agree = k % 2 == 0
        first = 1 if (k // 2) % 2 == 0 else -1  # 1: red
        second = first if agree else -first
        prior = 50 if not agree else (40 if first == 1 else 60)
        out.append(
            {
                "id": 301 + k,
                "prior": prior,
                "calls": (
                    (f"P{41 + k}", first, k % 3),
                    (f"Q{41 + k}", second, (k // 3) % 3),
                ),
                "agree": agree,
            }
        )
    return tuple(out)


def design(module):
    return {k: v.copy() for k, v in _design(module).items()}


@functools.cache
def _design(module):
    form = module.split("-")[-1]
    items = range(0, 12) if form in ("a", "b") else range(12, 24)
    rows = []
    for k in items:
        spec = items_spec()[k]
        order = spec["calls"] if form in ("a", "c") else spec["calls"][::-1]
        for step in (1, 2):
            rows.append({"kind": "pair", "item": k, "sequence": k, "step": step,
                         "first": order[0][0], "first_direction": order[0][1],
                         "first_phrase": order[0][2], "second": order[1][0],
                         "second_direction": order[1][1], "second_phrase": order[1][2],
                         "agree": spec["agree"], "prior": spec["prior"], "form": form,
                         "response": "probability"})  # fmt: skip
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}


def respond(items, truth, rng):
    """A simulated respondent: lambda = w[phrase] * direction (red positive); after one call the
    log-odds move by lambda_1, after both by lambda_1 + p lambda_2 - c lambda_1 (p: the weight of
    the later call; c: correlation); log-odds noise tau; whole percentages."""
    out = np.zeros(len(items["kind"]))
    for i in range(len(out)):
        prior = float(logit(int(items["prior"][i]) / 100))
        l1 = truth["w"][int(items["first_phrase"][i])] * int(items["first_direction"][i])
        l2 = truth["w"][int(items["second_phrase"][i])] * int(items["second_direction"][i])
        if int(items["step"][i]) == 1:
            z = prior + l1
        else:
            z = prior + l1 + truth.get("p", 1.0) * l2 - truth.get("c", 0.0) * l1
        z += rng.normal(0, truth["tau"])
        out[i] = float(np.clip(np.round(1 / (1 + np.exp(-z)), 2), 0, 1))
    return out


def session(items, responses):
    """Rows in the correlated-changes format: a call is identified by its analyst and direction."""
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
