"""Request bodies for the Clef pilot (docs/clef-pilot-design.md, "Elicitation").

The state is the rendered case text the agents saw. A probability question ("What is the
probability that P?") becomes a noul question "Is it true that P?"; a base-rate question becomes a
choice over 21 options, 0% to 100% in steps of 5%. Joint calls ask, on one forecast case's state,
the base rate for sources like this case's source, the structure probe for this source, and the
forecast, in that order (or reversed, as a method check). The probe and base-rate wording is the
cue modules' own (tests check it against their rendered probe and rate items).
"""

import hashlib
import json
import re

import numpy as np

from epistemics.disposition_tasks import evident_texts
from epistemics.disposition_tasks import render as base

VERSION = "clef-pilot/0.1.0"
MODELS = {"clef": "@cf/cloudflare/clef", "clef-flash": "@cf/cloudflare/clef-flash"}
COVER = "markets"
RATE_LEVELS = tuple(range(0, 101, 5))
RATE_KEYS = tuple(f"p{v:02d}" for v in RATE_LEVELS)

EVIDENT = ("relay-evident", "disclosure-evident")
HINTED = ("relay-hinted", "disclosure-hinted")
CUES = ("corroboration-cues", "disclosure-cues")
HINTED_VARIANTS = ("alone", "reference")
CUES_VARIANT = "cues-a"
STRUCTURE = {
    "relay-hinted": "corroboration",
    "corroboration-cues": "corroboration",
    "disclosure-hinted": "disclosure",
    "disclosure-cues": "disclosure",
}
# Method checks: the first twelve cases of each evident module.
CHECK_ITEMS = tuple(range(12))
REPEATS = 2
ORDERS = ("forward", "reverse")
FORWARD = ("rate", "probe", "forecast")

_PROBABILITY = re.compile(r"^What is the probability that (.+)\?$")
_DEMAND = re.compile(r"^(.+) demand is high$")


def digest(value):
    """sha256 of canonical JSON."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def noul(question):
    """'What is the probability that P?' as the noul question 'Is it true that P?'."""
    match = _PROBABILITY.match(question)
    if not match:
        raise ValueError(f"Not a probability question: {question}")
    return {"type": "noul", "instructions": f"Is it true that {match.group(1)}?"}


def paraphrase(question):
    """The forecast 'What is the probability that X's demand is high?' as 'Is X's demand high?'."""
    match = _PROBABILITY.match(question)
    demand = _DEMAND.match(match.group(1)) if match else None
    if not demand:
        raise ValueError(f"Not a demand forecast: {question}")
    return {"type": "noul", "instructions": f"Is {demand.group(1)} demand high?"}


def rate_choice(question):
    """A base-rate question as a choice over 0%, 5%, ..., 100%."""
    if not question.startswith("Among "):
        raise ValueError(f"Not a base-rate question: {question}")
    return {
        "type": "choice",
        "instructions": question,
        "criteria": {k: f"{v}%" for k, v in zip(RATE_KEYS, RATE_LEVELS, strict=True)},
    }


def _names(module, i):
    """(subject, first outlet, second outlet) of a case, as the module's renderer names them."""
    if module in ("relay-hinted", "disclosure-hinted"):
        return evident_texts.COMPANIES[i], evident_texts.OUTLETS_A[i], evident_texts.OUTLETS_B[i]
    return base.COMPANIES[i], base.OUTLETS_A[i], base.OUTLETS_B[i]


def probe_question(module, i):
    subject, a, b = _names(module, i)
    if STRUCTURE[module] == "corroboration":
        return (
            f"What is the probability that {b} relayed {base.own(a)} call rather than checking "
            "for itself?"
        )
    return (
        f"What is the probability that {subject} is the kind of company that withholds every "
        "off-target indicator?"
    )


def rate_question(module, i):
    subject, _, b = _names(module, i)
    if STRUCTURE[module] == "corroboration":
        return (
            f"Among outlets like {b}, what proportion relay another outlet's call instead of "
            "checking for themselves?"
        )
    return (
        f"Among companies like {subject}, what proportion share every on-target indicator and "
        "withhold every off-target one, rather than leaving indicators out at random?"
    )


def case(module, variant, i):
    return base.render(module, COVER, i, variant)


def single(module, variant, i):
    """The case's own question, converted: (state, {question id: question})."""
    rendered = case(module, variant, i)
    question = rendered["question"]
    converted = rate_choice(question) if question.startswith("Among ") else noul(question)
    kind = "rate" if converted["type"] == "choice" else "answer"
    return rendered["case"], {kind: converted}


def joint(module, variant, i, order="forward"):
    """Base rate, probe and forecast on one forecast case's state."""
    rendered = case(module, variant, i)
    questions = {
        "rate": rate_choice(rate_question(module, i)),
        "probe": noul(probe_question(module, i)),
        "forecast": noul(rendered["question"]),
    }
    keys = FORWARD if order == "forward" else tuple(reversed(FORWARD))
    return rendered["case"], {k: questions[k] for k in keys}


def body(model, state, questions):
    return {"model": model, "state": state, "questions": questions}


def described_forecasts(module):
    """Forecast cases with a source description (slot >= 0): the within-state cases."""
    items = base.items_for(module)
    kinds, slots = items["kind"], items["slot"]
    return [i for i in range(len(kinds)) if kinds[i] in ("pair", "forecast") and slots[i] >= 0]


def items_digest(module):
    items = base.items_for(module)
    return digest({k: np.asarray(v).tolist() for k, v in sorted(items.items())})


def calls(models=tuple(MODELS)):
    """Every call of the pilot, in order: (call id, metadata, body)."""
    out = []

    def add(model, part, module, variant, i, state, questions, tag=""):
        call_id = f"{model}/{part}/{module}/{variant}/{i}" + (f"/{tag}" if tag else "")
        meta = {"model": model, "part": part, "module": module, "variant": variant, "item": i,
                "tag": tag, "questions": {k: q["type"] for k, q in questions.items()}}  # fmt: skip
        out.append((call_id, meta, body(model, state, questions)))

    for model in models:
        for module in EVIDENT:
            for i in range(len(base.items_for(module)["kind"])):
                add(model, "q1", module, "alone", i, *single(module, "alone", i))
        for module in HINTED:
            for variant in HINTED_VARIANTS:
                for i in range(len(base.items_for(module)["kind"])):
                    add(model, "q2", module, variant, i, *single(module, variant, i))
        for module in CUES:
            for i in range(len(base.items_for(module)["kind"])):
                add(model, "q3", module, CUES_VARIANT, i, *single(module, CUES_VARIANT, i))
        for module in HINTED + CUES:
            variant = "alone" if module in HINTED else CUES_VARIANT
            for i in described_forecasts(module):
                for order in ORDERS:
                    add(
                        model, "joint", module, variant, i, *joint(module, variant, i, order), order
                    )
        for module in EVIDENT:
            for i in CHECK_ITEMS:
                for r in range(1, REPEATS + 1):
                    add(model, "repeat", module, "alone", i, *single(module, "alone", i), str(r))
        for module in EVIDENT:
            for i in CHECK_ITEMS:
                state, _ = single(module, "alone", i)
                question = paraphrase(case(module, "alone", i)["question"])
                add(model, "paraphrase", module, "alone", i, state, {"answer": question})
    return out
