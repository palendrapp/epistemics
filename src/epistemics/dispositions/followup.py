"""Follow-up rounding on another family (design 0.25; docs/deliberation-style-design.md).

The deliberation follow-ups found that any preceding question about the same case switches Astra
to round probabilities on the trend cases. These modules test it on the peer-advice cases
(advice-peer, social), in two variants: open (the analyst's record is not stated; the agent
judges) and stated (the record is stated, so the exact answer can be computed).

Sixteen cases, chosen for exact answers between 0.2 and 0.8, are asked in each session: eight
fresh (a single case) and eight as follow-ups (a first case asks whether the outcome is likely or
unlikely, the next asks for its probability). Fresh and follow-up cases are mixed in one session,
so a switch within the pair can be told from a switch across the session; form b swaps which
cases are fresh, so every case is answered both ways.
"""

import functools

import numpy as np

from epistemics.dispositions import social
from epistemics.dispositions.screen import _sigmoid, logit

BASE = "advice-peer"
VARIANTS = {"open": "peer-open", "stated": "peer-a"}
CASES = (0, 1, 2, 3, 4, 5, 8, 12, 13, 15, 16, 17, 18, 19, 20, 22)  # exact answers 0.23-0.78
MODULES = tuple(f"followup-advice-{v}-{f}" for v in VARIANTS for f in "ab")
OPTIONS = (["Likely", "Unlikely"], 0)
MID = (0.06, 0.94)


def parse(module):
    _, _, variant, form = module.split("-")
    return variant, form


def _rows(module):
    variant, form = parse(module)
    rows, sequence = [], 0
    for k, base in enumerate(CASES):
        follow = (k % 2 == 0) == (form == "a")
        common = {"base": base, "variant": variant, "form": form, "sequence": sequence}
        if follow:
            rows.append({**common, "kind": "first", "step": 0, "response": "choice"})
            rows.append({**common, "kind": "followup", "step": 1, "response": "probability"})
        else:
            rows.append({**common, "kind": "fresh", "step": 0, "response": "probability"})
        sequence += 1
    return rows


def design(module):
    return {k: v.copy() for k, v in _design(module).items()}


@functools.cache
def _design(module):
    rows = _rows(module)
    assert len(rows) == 24, module
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}


def options(items, i):
    shown, act = OPTIONS
    return list(shown), act


@functools.cache
def exact():
    """The stated variant's exact answers (log-odds), by base case."""
    return social.advice_answer(social.advice_design())


def respond(items, truth, rng):
    """A simulated respondent: the exact answer plus log-odds noise tau, rounded to 5 points with
    probability rho_fresh on fresh cases and rho_followup on follow-ups; first cases "Likely"
    (coded 1) when its answer is above 0.5."""
    z_exact = exact()
    out = np.zeros(len(items["kind"]))
    for i, kind in enumerate(items["kind"]):
        z = float(z_exact[int(items["base"][i])])
        if kind == "first":
            out[i] = 1.0 if z > 0 else 0.0
            continue
        p = float(_sigmoid(z + rng.normal(0, truth["tau"])))
        rho = truth["rho_followup"] if kind == "followup" else truth["rho_fresh"]
        grain = 0.05 if rng.random() < rho else 0.01
        out[i] = float(np.clip(np.round(p / grain) * grain, 0, 1).round(2))
    return out


def _share(values):
    v = [x for x in values if MID[0] <= x <= MID[1]]
    return (sum(round(x * 100) % 5 == 0 for x in v) / len(v)) if v else None, len(v)


def session(items, responses):
    responses = np.asarray(responses, dtype=float)
    variant, form = str(items["variant"][0]), str(items["form"][0])
    rows = []
    for i, kind in enumerate(items["kind"]):
        if kind in ("fresh", "followup"):
            base = int(items["base"][i])
            row = {"base": base, "kind": str(kind), "answer": float(responses[i])}
            if variant == "stated":
                row["error"] = abs(float(logit(responses[i])) - float(exact()[base]))
            rows.append(row)
    shares = {}
    for kind in ("fresh", "followup"):
        share, n = _share([r["answer"] for r in rows if r["kind"] == kind])
        shares[kind] = {"share_5": share, "n": n}
    return {"variant": variant, "form": form, "answers": rows, "grain": shares,
            "responses": [float(v) for v in responses]}  # fmt: skip
