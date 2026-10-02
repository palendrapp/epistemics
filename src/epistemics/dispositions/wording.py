"""Confident wording across families (design 0.29; exploration log idea 28).

Without a record, Terra took an analyst's "definitely... confirmed" call at face value: about
twice the other configurations' weight, in two urn collections. Is that a trait of confident
wording, or of the urn family and that phrase? Three families, each a single claim from one
person without a record, against a stated prior:

  urn      an analyst's call on an urn (the original family)
  policy   an economist's note on whether a central bank's committee lowers its rate
  report   an inspector's report on whether a batch meets its standard

The claim is worded in one of four ways: "I think...", plain, "definitely..." and the original
"definitely... confirmed", so the urn family also splits confidence from a claim of
verification. Each family takes four forms, a Latin square: every item appears at every wording
across the forms, six items at each wording in a form, their directions and priors balanced.

  weight = (logit(answer) - logit(prior)) * direction    (log-odds, toward the claim)
"""

import functools

import numpy as np

from epistemics.dispositions.screen import logit

FAMILIES = ("urn", "policy", "report")
FORMS = ("a", "b", "c", "d")
MODULES = tuple(f"wording-{family}-{form}" for family in FAMILIES for form in FORMS)
WORDINGS = ("I think", "plain", "definitely", "confirmed")
PRIORS = (40, 50, 60)


def parse(module):
    _, family, form = module.split("-")
    return family, form


@functools.cache
def items_spec():
    """24 items per family (the same skeleton in each): a prior and the claim's direction."""
    return tuple(
        {
            "id": 401 + k,
            "prior": PRIORS[k % len(PRIORS)],
            "direction": 1 if (k // 4) % 2 == 0 else -1,
        }
        for k in range(24)
    )


def wording_of(k, form):
    return (k + FORMS.index(form)) % len(WORDINGS)


def design(module):
    return {k: v.copy() for k, v in _design(module).items()}


@functools.cache
def _design(module):
    family, form = parse(module)
    rows = []
    for k, spec in enumerate(items_spec()):
        rows.append({"kind": "claim", "item": k, "family": family, "form": form,
                     "wording": wording_of(k, form), "direction": spec["direction"],
                     "prior": spec["prior"], "response": "probability"})  # fmt: skip
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}


def respond(items, truth, rng):
    """A simulated respondent: the log-odds move w[wording] toward the claim; log-odds noise tau;
    whole percentages."""
    out = np.zeros(len(items["kind"]))
    for i in range(len(out)):
        step = truth["w"][int(items["wording"][i])] * int(items["direction"][i])
        z = float(logit(int(items["prior"][i]) / 100)) + step + rng.normal(0, truth["tau"])
        out[i] = float(np.clip(np.round(1 / (1 + np.exp(-z)), 2), 0, 1))
    return out


def session(items, responses):
    """Per case: the weight given to the claim (log-odds toward it); per wording, the mean."""
    responses = np.asarray(responses, dtype=float)
    rows = []
    for i in range(len(responses)):
        prior = int(items["prior"][i])
        weight = (float(logit(responses[i])) - float(logit(prior / 100))) * int(
            items["direction"][i]
        )
        rows.append({"item": int(items["item"][i]), "wording": WORDINGS[int(items["wording"][i])],
                     "direction": int(items["direction"][i]), "prior": prior,
                     "answer": float(responses[i]), "weight": weight})  # fmt: skip
    means = {w: float(np.mean([r["weight"] for r in rows if r["wording"] == w])) for w in WORDINGS}
    return {"family": str(items["family"][0]), "form": str(items["form"][0]), "cases": rows,
            "mean_weight": means, "responses": [float(v) for v in responses]}  # fmt: skip
