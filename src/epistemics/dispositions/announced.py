"""Announced count (design 0.26; docs/statement-updating-design.md, exploration log idea 1).

In statements stage A, the step on a change shrank with the number of changes the case announced,
before any other change was seen (first step 1.93 log-odds with one change announced, 0.51 with
six). Here one substantive change is reported, and only that one, in statements that truly differ
in one, three or six places:

  one          "differs in 1 place": the change alone.
  three        "differs in 3 places": the change and two rewordings, not said to be rewordings.
  three-said   the same statement, with the two rewordings disclosed; the change shown is the one
               that is not a rewording.
  six          "differs in 6 places": the change, two rewordings and three other substantive
               changes.

A fixed budget per statement predicts the same small step for three and three-said; a pragmatic
reading (one deliberate change is the message) predicts three-said as large as one. Each of 24
cases appears under every condition across four forms (a Latin square); the step is measured
against the stated market prior, which every configuration adopted exactly in stage A.
"""

import functools

import numpy as np

from epistemics.dispositions import statements as st
from epistemics.dispositions.screen import logit

CONDITIONS = ("one", "three", "three-said", "six")
DECLARED = {"one": 1, "three": 3, "three-said": 3, "six": 6}
FORMS = ("a", "b", "c", "d")
MODULES = tuple(f"announced-{f}" for f in FORMS)
PRIORS = (30, 50, 70)


@functools.cache
def items_spec():
    """24 cases: a previous statement, a stated prior, the target change, and the other changes
    the statement holds under each condition."""
    out = []
    for k in range(24):
        slot = st.SLOTS[k % len(st.SLOTS)]
        direction = 1 if (k // len(st.SLOTS)) % 2 == 0 else -1
        levels = {}
        for j, s in enumerate(st.SLOTS):
            levels[s] = ((k + 2 * j) % 3) - 1
        # The target slot's level leaves room for its change.
        levels[slot] = (-1 if k % 2 else 0) if direction == 1 else (1 if k % 2 else 0)
        styles = {s: (k >> j) & 1 for j, s in enumerate(st.STYLES)}
        rewordings = [s for j, s in enumerate(st.STYLES) if j != k % len(st.STYLES)]
        others = []
        for s in st.SLOTS:
            if s == slot or len(others) == 3:
                continue
            level = levels[s]
            d = 1 if level < 0 else -1 if level > 0 else (1 if (k + len(others)) % 2 else -1)
            others.append((s, d))
        out.append(
            {
                "id": 101 + k,
                "prior": PRIORS[k % len(PRIORS)],
                "levels": levels,
                "styles": styles,
                "background": (k % 4, (k // 4) % 3),
                "target": (slot, direction),
                "rewordings": rewordings,
                "others": others,
            }
        )
    return tuple(out)


def changes(spec, condition):
    """Every change the new statement holds under a condition (target first)."""
    out = [spec["target"]]
    if condition in ("three", "three-said", "six"):
        out += [(s, 0) for s in spec["rewordings"]]
    if condition == "six":
        out += list(spec["others"])
    assert len(out) == DECLARED[condition]
    return out


def condition_of(k, form):
    return CONDITIONS[(k + FORMS.index(form)) % len(CONDITIONS)]


def design(module):
    return {k: v.copy() for k, v in _design(module).items()}


@functools.cache
def _design(module):
    form = module.split("-")[-1]
    rows = []
    for k, spec in enumerate(items_spec()):
        slot, direction = spec["target"]
        condition = condition_of(k, form)
        rows.append({"kind": "count", "item": k, "condition": condition,
                     "declared": DECLARED[condition], "slot": slot, "direction": direction,
                     "prior": spec["prior"], "form": form,
                     "response": "probability"})  # fmt: skip
    items = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    items["part"] = items.pop("slot")  # not "slot": ledger extraction reads that as integers
    return items


def respond(items, truth, rng):
    """A simulated respondent: the step on the target change is w[slot] * direction divided by
    1 + k (n - 1), where n is the number of changes that count: all declared changes, except in
    three-said, where rewordings count with weight `rewordings` (1: a budget by count; 0: only
    substantive changes count). Log-odds noise tau; whole percentages."""
    out = np.zeros(len(items["kind"]))
    for i in range(len(out)):
        spec = items_spec()[int(items["item"][i])]
        slot, direction = spec["target"]
        condition = str(items["condition"][i])
        n = DECLARED[condition]
        if condition == "three-said":
            n = 1 + (n - 1) * truth["rewordings"]
        step = truth["w"][slot] * direction / (1 + truth["k"] * (n - 1))
        z = float(logit(spec["prior"] / 100)) + step + rng.normal(0, truth["tau"])
        out[i] = float(np.clip(np.round(1 / (1 + np.exp(-z)), 2), 0, 1))
    return out


def session(items, responses):
    """Per case: the signed step from the stated prior (log-odds, positive in the change's
    direction); per condition, the mean step."""
    responses = np.asarray(responses, dtype=float)
    rows = []
    for i in range(len(responses)):
        prior = int(items["prior"][i])
        step = (float(logit(responses[i])) - float(logit(prior / 100))) * int(items["direction"][i])
        rows.append({"item": int(items["item"][i]), "condition": str(items["condition"][i]),
                     "slot": str(items["part"][i]), "prior": prior,
                     "answer": float(responses[i]), "step": step})  # fmt: skip
    means = {
        c: float(np.mean([r["step"] for r in rows if r["condition"] == c])) for c in CONDITIONS
    }
    return {"form": str(items["form"][0]), "cases": rows, "mean_step": means,
            "responses": [float(v) for v in responses]}  # fmt: skip
