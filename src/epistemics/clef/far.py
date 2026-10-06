"""Far transfer for the Clef battery (docs/clef-battery-design.md, "Far transfer"): central-bank
remarks in natural language, with the market price stated but no hit rates and no counts.

  remarks  a market-implied probability of a rate rise (five levels) and a set of remarks from
           named committee members (0 to 5 remarks, each pointing to a rise or a hold). The same
           remarks appear at every price, so the weight on the price (alpha) is identified
           without knowing how much the remarks are worth.
  wait     even odds, remarks heard so far, and the choice: take a position on a rise or a hold
           now, or wait for the next speaker (the beads payoffs).

Speakers are fictional and the institution generic. Three phrasings per item.
"""

import itertools

import numpy as np

from epistemics.clef.battery import BEADS_OPTIONS, COST, MAX_DRAWS, WIN, logit, pct
from epistemics.clef.requests import MODELS, digest

VERSION = "clef-far/0.1.0"
PHRASINGS = (0, 1, 2)
PRICES = (0.2, 0.35, 0.5, 0.65, 0.8)
COMPOSITIONS = ((0, 0), (1, 1), (1, 0), (3, 3), (3, 2), (3, 1), (3, 0),
                (5, 5), (5, 4), (5, 3), (5, 2), (5, 1), (5, 0))  # fmt: skip
SPEAKERS = (
    "Governor Hale", "Deputy Governor Okafor", "Governor Lindqvist", "Governor Marchetti",
    "Governor Adeyemi", "Governor Castellanos", "Governor Brandt", "Governor Whitlock",
    "Governor Ishida", "Governor Novak",
)  # fmt: skip
HAWKISH = (
    "Inflation is still running too hot for comfort, and I see a case for tightening further at "
    "our next meeting.",
    "The labour market remains very tight; another increase at the coming meeting would be prudent.",
    "I would support moving rates up again when we meet.",
    "We haven't finished the job on inflation, and I expect we'll need to raise rates at the "
    "coming meeting.",
    "Recent price data argue for one more increase, and soon.",
)
DOVISH = (
    "Policy is already restrictive enough; I'd prefer to hold steady at the next meeting.",
    "I see value in pausing at the coming meeting to assess the effects of past increases.",
    "There's no urgency to move again; holding rates is the right call for now.",
    "Inflation is cooling, and I'd keep rates where they are when we meet.",
    "I'd be comfortable leaving policy unchanged at the coming meeting.",
)
WAIT_PATTERNS = ("++++", "++-+", "+-++", "-+-+")


def _remarks(n, r, salt):
    """n remarks, r pointing to a rise, in a fixed order; speakers and sentences rotate."""
    rng = np.random.default_rng(1000 + salt)
    signs = [1] * r + [-1] * (n - r)
    rng.shuffle(signs)
    out, h, d = [], 0, 0
    for k, s in enumerate(signs):
        text = HAWKISH[(salt + h) % 5] if s > 0 else DOVISH[(salt + d) % 5]
        h, d = h + (s > 0), d + (s < 0)
        out.append((SPEAKERS[(salt + k) % len(SPEAKERS)], s, text))
    return out


def remarks_items():
    out = []
    for (n, r), p in itertools.product(COMPOSITIONS, PRICES):
        composition = COMPOSITIONS.index((n, r))
        out.append({"price": p, "prior_logodds": logit(p), "n": n, "r": r, "net": 2 * r - n,
                    "composition": composition,
                    "remarks": _remarks(n, r, composition)})  # fmt: skip
    return out


def wait_sequences():
    seqs = {""}
    for pattern in WAIT_PATTERNS:
        for s in (pattern, pattern.translate(str.maketrans("+-", "-+"))):
            seqs.update(s[:k] for k in range(1, len(s) + 1))
    return sorted(seqs, key=lambda s: (len(s), s))


def wait_items():
    out = []
    for seq in wait_sequences():
        heard, h, d = [], 0, 0
        for k, c in enumerate(seq):
            s = 1 if c == "+" else -1
            text = HAWKISH[h % 5] if s > 0 else DOVISH[d % 5]
            h, d = h + (s > 0), d + (s < 0)
            heard.append((SPEAKERS[k % len(SPEAKERS)], s, text))
        out.append({"sequence": seq, "net": seq.count("+") - seq.count("-"), "remarks": heard})
    return out


def items_digest():
    return digest({"remarks": remarks_items(), "wait": wait_items()})


def _lines(remarks, empty):
    if not remarks:
        return empty
    return "\n".join(f'- {who}: "{text}"' for who, _, text in remarks)


def remarks_text(item, phrasing):
    p = pct(item["price"])
    lines = _lines(item["remarks"], "- (no committee member has spoken)")
    states = [
        f"Markets price a {p} chance that the central bank raises rates at next week's meeting. "
        f"Remarks from committee members since the last meeting:\n{lines}",
        f"Ahead of the policy meeting, futures imply a {p} probability of a rate rise. What "
        f"policymakers have said this week:\n{lines}",
        f"Desk note. Pricing: {p} chance of a hike at the coming meeting. Central-bank speakers "
        f"so far:\n{lines}",
    ]
    questions = [
        "Is it true that the central bank will raise rates at next week's meeting?",
        "Will the central bank raise rates at the meeting?",
        "Is it true that the central bank will hike at the coming meeting?",
    ]
    return states[phrasing], {"answer": {"type": "noul", "instructions": questions[phrasing]}}


def wait_text(item, phrasing):
    lines = _lines(item["remarks"], "(no one has spoken yet)")
    states = [
        "Markets see a rate rise and a hold at the central bank's next meeting as equally "
        "likely. Committee members are speaking one at a time before the meeting. Remarks so "
        f"far:\n{lines}\nYou can take a position on the decision now, or wait for the next "
        f"speaker. A correct position earns ${WIN}k and a wrong one loses ${WIN}k; waiting for "
        f"each further speaker costs ${COST}k in worse prices. At most {MAX_DRAWS} members will "
        "speak.",
        "Rise or hold at the next policy meeting: priced at even odds. Committee members are "
        f"speaking in turn. Heard so far:\n{lines}\nA right position pays ${WIN}k, a wrong one "
        f"costs ${WIN}k, and each further speech you wait for costs ${COST}k (up to {MAX_DRAWS} "
        "speeches in all).",
        "A rate rise and a hold are equally likely at the coming meeting. Policymakers are "
        f"speaking before it. So far:\n{lines}\nBeing right earns ${WIN}k and being wrong loses "
        f"${WIN}k; waiting for another speaker costs ${COST}k; no more than {MAX_DRAWS} will "
        "speak.",
    ]
    decision = {"type": "choice", "instructions": "What should the desk do now?",
                "criteria": dict(BEADS_OPTIONS["desk"])}  # fmt: skip
    return states[phrasing], {"decision": decision}


def calls(models=tuple(MODELS)):
    out = []

    def add(model, task, i, phrasing, state, questions):
        kinds = {
            k: ("options" if q["type"] == "choice" else q["type"]) for k, q in questions.items()
        }
        meta = {"model": model, "part": task, "task": task, "domain": "far", "item": i,
                "phrasing": phrasing, "questions": kinds}  # fmt: skip
        out.append((f"{model}/{task}/far/{i}/{phrasing}", meta,
                    {"model": model, "state": state, "questions": questions}))  # fmt: skip

    for model in models:
        for i, item in enumerate(remarks_items()):
            for ph in PHRASINGS:
                add(model, "remarks", i, ph, *remarks_text(item, ph))
        for i, item in enumerate(wait_items()):
            for ph in PHRASINGS:
                add(model, "wait", i, ph, *wait_text(item, ph))
    return out
