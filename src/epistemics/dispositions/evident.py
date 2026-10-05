"""Evident structures: held-out finance dossiers for the passport adapter (design 0.32;
docs/passport-adapter-design.md).

The structure checks that set each configuration's adapter were measured on dossier set A, where
a hidden structure is suggested by a description and its correct weight depends on an assumed
rate. These modules are new cases (new companies, outlets and documents) in which the structure is
settled by the documents themselves, without anything naming the mechanism:

  relay-evident       a second outlet's matching call is evidently repeated from the first (its
                      story credits the first outlet, or its profile says it has no reporters and
                      republishes others' calls), evidently independent (its story reports its own
                      survey of the company's retailers), or not in play (one call, or two calls
                      that conflict, which a repeat cannot)
  disclosure-evident  a company's update evidently omits what was bad (its investor FAQ says
                      updates report only indicators that met target, or every indicator it left
                      out was later disclosed as below target), evidently omits at random (an
                      auditor's fixed template; a gap means data arrived late), or omits nothing

The correct forecast is the Bayesian observer's (dispositions.observers) with the structure's
prior set to 1 where present and 0 where absent, and stated likelihoods taken at face value.
24 cases per module, eight of each type, directions and priors balanced.
"""

import functools

import numpy as np

from epistemics.dispositions import observers
from epistemics.dispositions.screen import logit

MODULES = ("relay-evident", "disclosure-evident")
TYPES = ("present", "absent", "control")
PRIORS = (0.3, 0.5, 0.7)
ACCURACY_A = (0.7, 0.75, 0.8)
ACCURACY_B = (0.85, 0.9, 0.75)
CLIP = 0.01


@functools.cache
def _relay():
    rows = []
    for k in range(24):
        kind_of, j = TYPES[k % 3], k // 3
        call = 1 if j % 2 == 0 else -1
        if kind_of == "present":
            style, kind, second = ("attribution", "profile")[j % 2], "pair", call
        elif kind_of == "absent":
            style, kind, second = "survey", "pair", call
        else:
            style = ("single", "conflict")[j % 2]
            kind, second = ("single", call) if style == "single" else ("pair", -call)
        rows.append({"kind": kind, "item": k, "type": kind_of, "style": style,
                     "prior": PRIORS[j % 3], "accuracy_a": ACCURACY_A[j % 3],
                     "accuracy_b": ACCURACY_B[(j + 1) % 3], "report_a": call,
                     "report_b": second, "cue": 0.0, "response": "probability"})  # fmt: skip
    return rows


@functools.cache
def _disclosure():
    rows = []
    for k in range(24):
        kind_of, j = TYPES[k % 3], k // 3
        if kind_of == "present":
            shared_good, shared_bad = (1, 2, 3, 2)[j % 4], 0
            style = ("policy", "history")[j % 2]
        elif kind_of == "absent":
            # Nothing below target is shared, so a selective company could have sent this update:
            # the structure is in play, and only the template rules it out.
            withheld, shared_bad = (1, 2)[j % 2], 0
            shared_good, style = 4 - withheld, "template"
        else:
            shared_bad = (0, 1, 2, 1)[j % 4]
            shared_good, style = 4 - shared_bad, "complete"
        withheld = 4 - shared_good - shared_bad
        rows.append({"kind": "forecast", "item": k, "type": kind_of, "style": style,
                     "prior": PRIORS[j % 3], "good": 0.75, "omission": (0.3, 0.5)[j % 2],
                     "shared_good": shared_good, "shared_bad": shared_bad, "withheld": withheld,
                     "response": "probability"})  # fmt: skip
    return rows


def design(module):
    rows = _relay() if module == "relay-evident" else _disclosure()
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}


def structure_prior(items, present=1.0, absent=0.0):
    """Per case: the prior the observer gives the structure (present cases `present`, absent cases
    `absent`, controls 0, where it cannot matter)."""
    return np.where(items["type"] == "present", present,
                    np.where(items["type"] == "absent", absent, 0.0))  # fmt: skip


def observe(module, items, present=1.0, absent=0.0):
    prior = structure_prior(items, present, absent)
    if module == "relay-evident":
        return observers.corroboration(items, prior, 1.0)
    return observers.disclosure(items, prior, 1.0)


def correct(module, items):
    """The correct forecast (log-odds of high demand) for every case."""
    return observe(module, items, 1.0, 0.0)


def respond(module, items, truth, rng):
    """A simulated respondent who gives the structure prior `use` where it is present and `false`
    where it is absent; log-odds noise tau; whole percentages."""
    z = observe(module, items, truth["use"], truth["false"]) + rng.normal(
        0, truth["tau"], len(items["kind"])
    )
    return np.clip(np.round(1 / (1 + np.exp(-z)), 2), 0, 1)


GRID = np.round(np.arange(0, 1.0001, 0.05), 2)


def _fit(module, items, answers, which):
    """The structure prior that best explains the answers on one type of case (least squares in
    log-odds)."""
    mask = items["type"] == which
    z = logit(np.clip(answers, CLIP, 1 - CLIP))
    best, err = None, np.inf
    for g in GRID:
        pred = (
            observe(module, items, g, 0.0) if which == "present" else observe(module, items, 1.0, g)
        )
        e = float(np.mean((z[mask] - pred[mask]) ** 2))
        if e < err:
            best, err = float(g), e
    return best


def session(module, items, responses):
    """Per case: the correct and given probability and the absolute log-odds error; per type, the
    mean error; and the fitted structure use on present cases and false structure on absent ones."""
    responses = np.asarray(responses, dtype=float)
    target = correct(module, items)
    z = logit(np.clip(responses, CLIP, 1 - CLIP))
    error = np.abs(z - target)
    cases = [{"item": int(items["item"][i]), "type": str(items["type"][i]),
              "style": str(items["style"][i]), "answer": float(responses[i]),
              "correct": float(1 / (1 + np.exp(-target[i]))), "error": float(error[i])}
             for i in range(len(responses))]  # fmt: skip
    by_type = {t: float(error[items["type"] == t].mean()) for t in TYPES}
    return {
        "module": module,
        "cases": cases,
        "error": float(error.mean()),
        "error_by_type": by_type,
        "structure_use": _fit(module, items, responses, "present"),
        "false_structure": _fit(module, items, responses, "absent"),
        "responses": [float(v) for v in responses],
    }
