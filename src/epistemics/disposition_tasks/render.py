"""Templated case text for each module under two cover stories with identical structure.

Markets cases concern company demand; ecology cases concern a lake's fish stock. Names are
fixed by item, so a retest with the same cover shows identical text in a new order.
"""

import math

import numpy as np

from epistemics.dispositions import design

MODULES = (
    "corroboration",
    "disclosure",
    "checks",
    "corroboration-cues",
    "disclosure-cues",
    "corroboration-range",
    "corroboration-dossier",
    "disclosure-dossier",
    "corroboration-unprompted",
    "disclosure-unprompted",
    "corroboration-asked",
    "disclosure-asked",
    "corroboration-probed",
    "copying-urn",
    "selection-urn",
    "mismatch-urn",
    "copying-urn-asked",
    "selection-urn-asked",
    "mismatch-urn-asked",
    "copying-urn-probed",
    "selection-urn-probed",
    "mismatch-urn-probed",
    "echo-urn",
    "hub-urn",
    "stale-urn",
    "echo-urn-asked",
    "hub-urn-asked",
    "stale-urn-asked",
    "echo-urn-probed",
    "hub-urn-probed",
    "stale-urn-probed",
    "copying-load",
    "mismatch-load",
    "copying-long-load",
    "mismatch-long-load",
)
CUE_MODULES = ("corroboration-cues", "disclosure-cues")
# Transfer: the description modules' items rendered as realistic document dossiers.
DOSSIER_MODULES = ("corroboration-dossier", "disclosure-dossier")
DOSSIER_VARIANTS = ("dossier-a",)
# Noticing: dossiers that never state the mechanism, forecasts only (same description set A).
UNPROMPTED_MODULES = ("corroboration-unprompted", "disclosure-unprompted")
# Salience: "named-a" adds one sentence naming the mechanism, without its rate, to every brief.
UNPROMPTED_VARIANTS = ("dossier-a", "named-a")
# Default induction: the named dossiers plus each description's base-rate question.
ASKED_MODULES = ("corroboration-asked", "disclosure-asked")
ASKED_VARIANTS = ("named-a",)
# The asked relay dossiers with each description's structure probe.
PROBED_MODULES = ("corroboration-probed",)
# Abstract urn tasks (transfer of the second layer): three structures on the salience ladder.
# Base modules take "urn-plain" (never named) or "urn-named"; asked and probed take "urn-named".
URN_MODULES = ("copying-urn", "selection-urn", "mismatch-urn")
URN_ASKED_MODULES = ("copying-urn-asked", "selection-urn-asked", "mismatch-urn-asked")
URN_PROBED_MODULES = ("copying-urn-probed", "selection-urn-probed", "mismatch-urn-probed")
URN_VARIANTS = ("urn-plain", "urn-named")
# Corrected urn texts (tasks 0.11): per-round structures and what stated accuracies cover.
URN2_VARIANTS = ("urn2-plain", "urn2-named")
# Mismatch reworded (tasks 0.12): the corrected accuracy clause was read as already covering
# misfiling. Named only; its plain text is urn2-plain's.
URN3_VARIANTS = ("urn3-named",)
URN3_MODULES = ("mismatch-urn", "mismatch-urn-asked", "mismatch-urn-probed")
# Rate stated per record (tasks 0.13): the forecast-only mismatch module only.
URN3_RATED_VARIANTS = ("urn3-rated",)
URN3_RATED_MODULES = ("mismatch-urn",)
# Battery v2 (tasks 0.14): a second surface story for each formal core, on the same designs as
# its twin (urn.TWIN), with urn2-plain and urn2-named.
V2_MODULES = ("echo-urn", "hub-urn", "stale-urn")
V2_ASKED_MODULES = ("echo-urn-asked", "hub-urn-asked", "stale-urn-asked")
V2_PROBED_MODULES = ("echo-urn-probed", "hub-urn-probed", "stale-urn-probed")
V2_TWINS = {"echo": "copying", "hub": "selection", "stale": "mismatch"}
# Capacity battery (tasks 0.15). Part A: fully specified load cases. Part B: the unprompted urn
# tasks with audit records of matched likelihood ratio ("urn2-vig").
# Tasks 0.17 (after pilot 2): four-level ladders reaching 16 (copying) and 12 (misfiling)
# readings, misfiling balanced for per-reading difficulty (design.long_load_design).
LONG_LOAD_MODULES = ("copying-long-load", "mismatch-long-load")
LOAD_MODULES = ("copying-load", "mismatch-load") + LONG_LOAD_MODULES
LOAD_VARIANTS = ("load-a",)
LOAD_DESIGNS = {
    "copying-load": "dependence",
    "mismatch-load": "mismatch",
    "copying-long-load": "dependence",
    "mismatch-long-load": "mismatch",
}
VIG_VARIANTS = ("urn2-vig", "urn2-vig2")
URN_DESIGNS = {
    "copying-urn": design.corroboration_unprompted,
    "copying-urn-asked": design.corroboration_asked,
    "copying-urn-probed": design.corroboration_probed,
    "selection-urn": design.disclosure_unprompted,
    "selection-urn-asked": design.disclosure_asked,
    "selection-urn-probed": design.disclosure_cues,
    "mismatch-urn": design.mismatch_urn,
    "mismatch-urn-asked": design.mismatch_urn_asked,
    "mismatch-urn-probed": design.mismatch_urn_probed,
}
URN_DESIGNS |= {
    module: URN_DESIGNS[module.replace(family, twin, 1)]
    for family, twin in V2_TWINS.items()
    for module in V2_MODULES + V2_ASKED_MODULES + V2_PROBED_MODULES
    if module.startswith(family)
}


def urn_family(module):
    return module.split("-", 1)[0]


RANGE_MODULES = ("corroboration-range",)
COVERS = ("markets", "ecology")
# paired: the unknown is posed as an explicit two-way possibility (0.1 wording). open: that
# sentence is removed. suggestive / reassuring: open, plus a qualitative sentence making a relay
# or a selective sender more / less plausible. learning-*: open, and each checkpoint reveals how
# the previous case was produced, from a world with the given relay or selective rate.
VARIANTS = ("paired", "open", "suggestive", "reassuring", "learning-high", "learning-low")
# Cue modules (markets only): two paraphrase sets of five graded descriptions each.
CUE_VARIANTS = ("cues-a", "cues-b")
# Relative-judgement module (markets only): the comparison outlets are all strongly reassuring or
# all strongly suggestive; the five target descriptions are the same in both.
RANGE_VARIANTS = ("range-reassuring", "range-suggestive")
LEARNING_RATES = {"learning-high": 0.8, "learning-low": 0.2}

_PREFIXES = [
    "Alder",
    "Brightwater",
    "Cobalt",
    "Dunmore",
    "Everline",
    "Fernhill",
    "Granite Row",
    "Halcyon",
    "Ironbark",
    "Juniper",
    "Kestrel",
    "Larkspur",
    "Marrow Bay",
    "Northfield",
    "Oakhurst",
    "Pellam",
    "Quarry Lane",
    "Redfern",
    "Saltmarsh",
    "Thistle",
    "Umberly",
    "Valewood",
    "Westcombe",
    "Yarrow",
]
_TRADES = ["Mills", "Cable", "Foods", "Freight", "Textiles", "Robotics", "Glass", "Optics"]
COMPANIES = [f"{p} {_TRADES[i % len(_TRADES)]}" for i, p in enumerate(_PREFIXES)]
CONTRACTORS = [f"{p} Field Services" for p in _PREFIXES]
OUTLETS_A = [
    "Harbor Ledger",
    "Meridian Wire",
    "Copperline Daily",
    "Tidewater Post",
    "Summit Dispatch",
    "Lantern Review",
    "Crossroads Journal",
    "Beacon Markets",
    "Keystone Bulletin",
    "Riverside Times",
    "Northgate Herald",
    "Clearview Digest",
    "Ashford Gazette",
    "Stonebridge Report",
    "Windmere Chronicle",
    "Highpoint Brief",
    "Foxglove Monitor",
    "Parkside Observer",
    "Canal Street News",
    "Evergreen Courier",
    "Bluestone Weekly",
    "Silverlake Record",
    "Hollow Oak Tribune",
    "Driftwood Sentinel",
]
OUTLETS_B = [
    "Pinecrest Wire",
    "Oriel Business",
    "Marlow Street Daily",
    "Kingsway Ledger",
    "Glenmoor Post",
    "Fairhaven Dispatch",
    "Ravenswood Review",
    "Brookline Journal",
    "Coral Bay Markets",
    "Larchmont Bulletin",
    "Westbrook Times",
    "Elmstead Herald",
    "Ridgeway Digest",
    "Thornbury Gazette",
    "Seacliff Report",
    "Maplewood Chronicle",
    "Orchard Brief",
    "Heathfield Monitor",
    "Linden Observer",
    "Garnet Hill News",
    "Willowby Courier",
    "Birchmoor Weekly",
    "Cloudbank Record",
    "Sandpiper Tribune",
]
LAKES = [
    "Lake Varden",
    "Lake Ostry",
    "Tarn Hollow",
    "Lake Meriel",
    "Coldwater Loch",
    "Lake Brannock",
    "Lake Sedley",
    "Fenwater",
    "Lake Aurin",
    "Lake Talvi",
    "Mossmere",
    "Lake Corrin",
    "Lake Pellow",
    "Lake Isolde",
    "Lake Hartle",
    "Lake Druin",
    "Stillwater Tarn",
    "Lake Kerrow",
    "Lake Emberly",
    "Lake Norrin",
    "Lake Gavell",
    "Lake Rushby",
    "Lake Toller",
    "Lake Wendle",
]
# Relay (forwarding) and independent rates for each cue strength, as displayed.
CUE_WORDS = {
    "strong": ("90% of the time", "10% of the time"),
    "moderate": ("80% of the time", "20% of the time"),
    "weak": ("2 times in 3", "1 time in 3"),
}
DESCRIPTORS = {
    ("corroboration", "markets"): {
        "suggestive": [
            "{name} is a two-person newsletter with no research staff.",
            "{name} is an aggregator site that posts dozens of market calls a day.",
            "{name} usually publishes within minutes of larger outlets.",
        ],
        "reassuring": [
            "{name} runs its own monthly survey of retailers.",
            "{name} has a research desk of twelve analysts who visit suppliers.",
            "{name} is known for calls based on its own interviews with customers.",
        ],
    },
    ("corroboration", "ecology"): {
        "suggestive": [
            "{name} has been short of staff all season.",
            "{name} has been waiting weeks for replacement sampling equipment.",
            "{name} usually files its log within minutes of a neighbouring station.",
        ],
        "reassuring": [
            "{name} has a full-time crew that sampled from its own boat that week.",
            "{name} uses a different sampling method from the other stations.",
            "{name} sampled in a separate bay of the lake.",
        ],
    },
    ("disclosure", "markets"): {
        "suggestive": [
            "{own} management is under pressure after missing its targets last quarter.",
            "{name} is about to ask investors for new financing.",
            "{own} executive bonuses depend on these indicators.",
        ],
        "reassuring": [
            "{own} updates are prepared by an outside auditor using a fixed template.",
            "{name} publishes the full indicator data in its annual report a month later.",
            "{name} is a cooperative owned by its customers.",
        ],
    },
    ("disclosure", "ecology"): {
        "suggestive": [
            "{name} is paid a bonus if the lake reopens to fishing.",
            "{name} was hired by the fishing association that wants the lake reopened.",
            "{name} will lose its contract if the lake stays closed.",
        ],
        "reassuring": [
            "{name} was hired by the regional environment agency, which audits its reports.",
            "{name} is a university laboratory that later publishes all its raw data.",
            "{name} is paid the same whatever the survey finds.",
        ],
    },
}
# Slots follow design.CUE_LEVELS: strongly reassuring, mildly reassuring, irrelevant, mildly
# suggestive, strongly suggestive. None states or implies a numeric rate.
CUE_DESCRIPTORS = {
    ("corroboration", "cues-a"): [
        "{name} employs twenty reporters who interview the company's customers and suppliers "
        "before every call.",
        "{name} sometimes runs its own surveys of retailers.",
        "{name} is based in a city on the coast.",
        "{name} is a small newsletter with two analysts.",
        "{name} is an aggregator site with no reporters that posts dozens of market calls a day.",
    ],
    ("corroboration", "cues-b"): [
        "{name} has a research desk that visits the company's factories before every call.",
        "{name} has a few analysts who occasionally speak to suppliers.",
        "{name} prints its stories in a blue-and-white layout.",
        "{name} usually publishes shortly after larger outlets.",
        "{name} is a one-person blog that posts within minutes of larger outlets.",
    ],
    ("disclosure", "cues-a"): [
        "{own} updates are checked by an independent auditor before release.",
        "{name} has a reputation among investors for plain, complete reporting.",
        "{name} moved its headquarters to a new building last year.",
        "{name} is hoping to raise new financing later this year.",
        "{own} chief executive will lose a large bonus unless these indicators look good this "
        "quarter.",
    ],
    ("disclosure", "cues-b"): [
        "{name} is owned by a customer cooperative that publishes all its data a month later.",
        "{own} finance team has worked with the same outside accountants for twenty years.",
        "{name} sponsors a local football team.",
        "{own} share price has fallen for three quarters in a row.",
        "{name} is in talks to be sold, and the buyer's price depends on these indicators.",
    ],
}
RANGE_TARGETS = [
    "{name} sometimes runs its own surveys of retailers.",
    "{name} has a few analysts who occasionally speak to suppliers.",
    "{name} is based in a city on the coast.",
    "{name} is a small newsletter with two analysts.",
    "{name} usually publishes shortly after larger outlets.",
]
RANGE_COMPARISONS = {
    "range-reassuring": [
        "{name} employs twenty reporters who interview the company's customers and suppliers "
        "before every call.",
        "{name} has a research desk that visits the company's factories before every call.",
        "{name} runs a monthly survey of two thousand retailers and publishes its method.",
    ],
    "range-suggestive": [
        "{name} is an aggregator site with no reporters that posts dozens of market calls a day.",
        "{name} is a one-person blog that posts within minutes of larger outlets.",
        "{name} is an automated feed with no staff that rewrites other outlets' stories.",
    ],
}
TERMS = {
    "markets": {
        "state": "demand",
        "good": "high",
        "bad": "low",
        "question": "What is the probability that {subject} demand is high?",
    },
    "ecology": {
        "state": "fish stock",
        "good": "healthy",
        "bad": "depleted",
        "question": "What is the probability that {subject} fish stock is healthy?",
    },
}


def items_for(module):
    if module == "corroboration":
        return design.corroboration(probes=True)
    if module == "disclosure":
        return design.disclosure(probes=True)
    if module == "checks":
        return design.checks()
    if module == "corroboration-cues":
        return design.corroboration_cues()
    if module == "disclosure-cues":
        return design.disclosure_cues()
    if module == "corroboration-range":
        return design.corroboration_range()
    if module == "corroboration-dossier":
        return design.corroboration_cues()
    if module == "disclosure-dossier":
        return design.disclosure_cues()
    if module == "corroboration-unprompted":
        return design.corroboration_unprompted()
    if module == "disclosure-unprompted":
        return design.disclosure_unprompted()
    if module == "corroboration-asked":
        return design.corroboration_asked()
    if module == "disclosure-asked":
        return design.disclosure_asked()
    if module == "corroboration-probed":
        return design.corroboration_probed()
    if module in URN_DESIGNS:
        return URN_DESIGNS[module]()
    if module in LONG_LOAD_MODULES:
        return design.long_load_design(LOAD_DESIGNS[module])
    if module in LOAD_DESIGNS:
        return design.load_design(LOAD_DESIGNS[module])
    raise ValueError(f"Unknown module: {module}")


def percent(p):
    value = float(p) * 100
    if abs(value - round(value)) > 1e-6:
        raise ValueError("Displayed probabilities must be whole percentages")
    return f"{round(value)}%"


def cue_name(llr):
    names = [name for name, value in design.CUES.items() if math.isclose(value, llr, abs_tol=1e-9)]
    if len(names) != 1:
        raise ValueError("Unknown cue")
    return names[0]


def own(name):
    return name + ("'" if name.endswith("s") else "'s")


def plural(count, singular, plural_form=None):
    return f"{count} {singular if count == 1 else (plural_form or singular + 's')}"


def descriptor(module, cover, variant, i, name):
    if variant not in ("suggestive", "reassuring"):
        return []
    options = DESCRIPTORS[(module, cover)][variant]
    return [options[i % len(options)].format(name=name, own=own(name))]


def _corroboration(items, i, cover, variant):
    t = TERMS[cover]
    subject = COMPANIES[i] if cover == "markets" else LAKES[i]
    a = OUTLETS_A[i] if cover == "markets" else f"Station N{i + 11}"
    b = OUTLETS_B[i] if cover == "markets" else f"Station S{i + 41}"

    def call(report):
        return t["good"] if report > 0 else t["bad"]

    if cover == "markets":
        lines = [
            f"{own(subject)} quarterly demand is either high or low. Before any reports, the "
            f"probability that demand is high is {percent(items['prior'][i])}.",
            f"{a} reports that demand is {call(items['report_a'][i])}. {own(a)} demand calls are "
            f"correct {percent(items['accuracy_a'][i])} of the time.",
        ]
    else:
        lines = [
            f"{own(subject)} fish stock this season is either healthy or depleted. Before any "
            f"readings, the probability that it is healthy is {percent(items['prior'][i])}.",
            f"{a}, a monitoring station, reports that the stock is {call(items['report_a'][i])}. "
            f"{own(a)} reports are correct {percent(items['accuracy_a'][i])} of the time.",
        ]
    kind = items["kind"][i]
    if kind != "single":
        cue = cue_name(items["cue"][i])
        accuracy = percent(items["accuracy_b"][i])
        if cover == "markets":
            mechanics = (
                "Some outlets relay another outlet's call instead of checking for themselves; a "
                "relayed call simply repeats the original call."
            )
            if variant == "paired":
                mechanics += f" {b} may have checked for itself or relayed {own(a)} call."
            lines += [
                f"{b} also reports on {subject}: it says demand is {call(items['report_b'][i])}. "
                f"When {b} checks for itself, its calls are correct {accuracy} of the time.",
                mechanics,
                *descriptor("corroboration", cover, variant, i, b),
            ]
            if cue == "none":
                lines.append("The two stories' wording cannot be compared.")
            else:
                strength, observed = cue.split("_")
                relay_rate, own_rate = CUE_WORDS[strength]
                same = (
                    "the same wording as" if observed == "identical" else "different wording from"
                )
                lines.append(
                    f"Relayed stories reuse the original story's wording {relay_rate}; stories by "
                    f"outlets that checked for themselves match another outlet's wording {own_rate}. "
                    f"{own(b)} story uses {same} {own(a)}."
                )
        else:
            mechanics = (
                "Some stations forward another station's report instead of sampling for "
                "themselves; a forwarded report simply repeats the original report."
            )
            if variant == "paired":
                mechanics += f" {b} may have sampled for itself or forwarded {own(a)} report."
            lines += [
                f"{b}, another station, also reports on {subject}: it says the stock is "
                f"{call(items['report_b'][i])}. When {b} samples for itself, its reports are "
                f"correct {accuracy} of the time.",
                mechanics,
                *descriptor("corroboration", cover, variant, i, b),
            ]
            if cue == "none":
                lines.append("The two reports' log formats cannot be compared.")
            else:
                strength, observed = cue.split("_")
                relay_rate, own_rate = CUE_WORDS[strength]
                same = (
                    "the same log format as"
                    if observed == "identical"
                    else "a different log format from"
                )
                lines.append(
                    f"Forwarded reports reuse the original report's log format {relay_rate}; reports "
                    f"from stations that sampled for themselves match another station's format "
                    f"{own_rate}. {own(b)} report uses {same} {own(a)}."
                )
    if kind == "probe":
        question = (
            f"What is the probability that {b} relayed {own(a)} call rather than checking for itself?"
            if cover == "markets"
            else f"What is the probability that {b} forwarded {own(a)} report rather than sampling for itself?"
        )
    else:
        question = t["question"].format(subject=own(subject))
    return lines, question


def _disclosure(items, i, cover, variant):
    m, j, k = (int(items[f][i]) for f in ("shared_good", "shared_bad", "withheld"))
    n = m + j + k
    good, bad = percent(items["good"][i]), percent(1 - items["good"][i])
    rate = percent(items["omission"][i])
    if cover == "markets":
        subject = COMPANIES[i]
        lines = [
            f"{own(subject)} quarterly demand is either high or low. Before its update, the "
            f"probability that demand is high is {percent(items['prior'][i])}.",
            f"{subject} tracks {n} operating indicators. When demand is high, each indicator "
            f"independently lands on target with probability {good}; when demand is low, with "
            f"probability {bad}.",
            "Some companies share every on-target indicator and withhold every off-target one. "
            "Others leave indicators out of their updates at random: each indicator is left out "
            f"with probability {rate}, whether or not it was on target."
            + (f" {subject} could be either kind." if variant == "paired" else ""),
            *descriptor("disclosure", cover, variant, i, subject),
        ]
        if m + j == 0:
            lines.append(f"{own(subject)} update does not mention any of its {n} indicators.")
        else:
            shown = f"{plural(m, 'indicator')} on target and {j} off target"
            rest = f", and does not mention the other {k}." if k else f"; it covers all {n}."
            lines.append(f"{own(subject)} update reports {shown}{rest}")
        question = (
            f"What is the probability that {subject} is the kind of company that withholds "
            "every off-target indicator?"
            if items["kind"][i] == "probe"
            else TERMS[cover]["question"].format(subject=own(subject))
        )
    else:
        subject, contractor = LAKES[i], CONTRACTORS[i]
        lines = [
            f"{own(subject)} fish stock this season is either healthy or depleted. Before the "
            f"survey report, the probability that it is healthy is {percent(items['prior'][i])}.",
            f"{contractor} checked {n} fish-health markers at {subject}. When the stock is "
            f"healthy, each marker independently passes with probability {good}; when it is "
            f"depleted, with probability {bad}.",
            "Some contractors report every passing marker and withhold every failing one. "
            "Others leave markers out of their reports at random: each marker is left out with "
            f"probability {rate}, whether or not it passed."
            + (f" {contractor} could be either kind." if variant == "paired" else ""),
            *descriptor("disclosure", cover, variant, i, contractor),
        ]
        if m + j == 0:
            lines.append(f"{own(contractor)} report does not mention any of the {n} markers.")
        else:
            shown = f"{plural(m, 'marker')} passing and {j} failing"
            rest = f", and does not mention the other {k}." if k else f"; it covers all {n}."
            lines.append(f"{own(contractor)} report lists {shown}{rest}")
        question = (
            f"What is the probability that {contractor} is the kind of contractor that "
            "withholds every failing marker?"
            if items["kind"][i] == "probe"
            else TERMS[cover]["question"].format(subject=own(subject))
        )
    return lines, question


def _checks(items, i, cover, variant):
    prior, high, low = items["prior"][i], items["high"][i], items["low"][i]
    positive = percent((prior - low) / (high - low))
    gain, loss = int(items["gain"][i]), int(items["loss"][i])
    if cover == "markets":
        subject = COMPANIES[i]
        lines = [
            f"You are deciding whether to invest in {subject}. Investing gains {gain} points if "
            f"its demand is high and loses {loss} points if demand is low; not investing scores "
            "0 points.",
            f"Take the probability that demand is high to be {percent(prior)}.",
            f"A market check is available. It comes back positive with probability {positive}. "
            f"If it is positive, the probability that demand is high becomes {percent(high)}; "
            f"if it is negative, it becomes {percent(low)}.",
            "If you buy the check, you decide after seeing its result; otherwise you decide now.",
        ]
        question = "What is the most you would pay for this check, in whole points?"
    else:
        subject = LAKES[i]
        lines = [
            f"You are deciding whether to open {subject} to fishing this season. Opening gains "
            f"{gain} points if its fish stock is healthy and loses {loss} points if the stock is "
            "depleted; keeping it closed scores 0 points.",
            f"Take the probability that the stock is healthy to be {percent(prior)}.",
            "A laboratory test of fish samples is available. It comes back positive with "
            f"probability {positive}. If it is positive, the probability that the stock is "
            f"healthy becomes {percent(high)}; if it is negative, it becomes {percent(low)}.",
            "If you buy the test, you decide after seeing its result; otherwise you decide now.",
        ]
        question = "What is the most you would pay for this test, in whole points?"
    return lines, question


def cue_sentence(base, variant, slot, name):
    return CUE_DESCRIPTORS[(base, variant)][slot].format(name=name, own=own(name))


def range_sentence(variant, slot, name):
    if slot < len(RANGE_TARGETS):
        template = RANGE_TARGETS[slot]
    else:
        template = RANGE_COMPARISONS[variant][slot - len(RANGE_TARGETS)]
    return template.format(name=name, own=own(name))


def _corroboration_range(items, i, cover, variant):
    return _relay_described(items, i, cover, lambda slot, name: range_sentence(variant, slot, name))


def _corroboration_cues(items, i, cover, variant):
    return _relay_described(
        items, i, cover, lambda slot, name: cue_sentence("corroboration", variant, slot, name)
    )


def _relay_described(items, i, cover, sentence):
    slot = int(items["slot"][i])
    b = OUTLETS_B[i]
    if items["kind"][i] == "rate":
        lines = [
            f"{b} is a news outlet that covers companies' demand. " + sentence(slot, b),
            "Some outlets relay another outlet's call instead of checking for themselves; a "
            "relayed call simply repeats the original call.",
        ]
        question = (
            f"Among outlets like {b}, what proportion relay another outlet's call instead of "
            "checking for themselves?"
        )
        return lines, question
    lines, question = _corroboration(items, i, cover, "open")
    if slot >= 0:
        lines.insert(4, sentence(slot, b))
    return lines, question


def _disclosure_cues(items, i, cover, variant):
    slot = int(items["slot"][i])
    subject = COMPANIES[i]
    if items["kind"][i] == "rate":
        rate = percent(items["omission"][i])
        lines = [
            f"{subject} tracks 4 operating indicators. "
            + cue_sentence("disclosure", variant, slot, subject),
            "Some companies share every on-target indicator and withhold every off-target one. "
            "Others leave indicators out of their updates at random: each indicator is left out "
            f"with probability {rate}, whether or not it was on target.",
        ]
        question = (
            f"Among companies like {subject}, what proportion share every on-target indicator "
            "and withhold every off-target one, rather than leaving indicators out at random?"
        )
        return lines, question
    lines, question = _disclosure(items, i, cover, "open")
    if slot >= 0:
        lines.insert(3, cue_sentence("disclosure", variant, slot, subject))
    return lines, question


RENDERERS = {
    "corroboration": _corroboration,
    "disclosure": _disclosure,
    "checks": _checks,
    "corroboration-cues": _corroboration_cues,
    "disclosure-cues": _disclosure_cues,
    "corroboration-range": _corroboration_range,
    "corroboration-dossier": lambda *a: _dossier("relay", *a),
    "disclosure-dossier": lambda *a: _dossier("disclosure", *a),
    "corroboration-unprompted": lambda *a: _dossier("relay_unprompted", *a),
    "disclosure-unprompted": lambda *a: _dossier("disclosure_unprompted", *a),
    "corroboration-asked": lambda *a: _dossier("relay_asked", *a),
    "disclosure-asked": lambda *a: _dossier("disclosure_asked", *a),
    "corroboration-probed": lambda *a: _dossier("relay_probed", *a),
    **{m: (lambda family: lambda *a: _urn(family, *a))(m.split("-", 1)[0]) for m in URN_DESIGNS},
    "copying-load": lambda *a: _urn("copying_load", *a),
    "mismatch-load": lambda *a: _urn("mismatch_load", *a),
    "copying-long-load": lambda *a: _urn("copying_load", *a),
    "mismatch-long-load": lambda *a: _urn("mismatch_load", *a),
}


def _urn(family, items, i, cover, variant):
    from epistemics.disposition_tasks import urn

    return getattr(urn, family)(items, i, cover, variant)


def _dossier(kind, items, i, cover, variant):
    from epistemics.disposition_tasks import dossier

    return getattr(dossier, kind)(items, i, cover, variant)


def allowed(module, cover, variant):
    if module in CUE_MODULES:
        return cover == "markets" and variant in CUE_VARIANTS
    if module in RANGE_MODULES:
        return cover == "markets" and variant in RANGE_VARIANTS
    if module in DOSSIER_MODULES:
        return cover == "markets" and variant in DOSSIER_VARIANTS
    if module in UNPROMPTED_MODULES:
        return cover == "markets" and variant in UNPROMPTED_VARIANTS
    if module in ASKED_MODULES + PROBED_MODULES:
        return cover == "markets" and variant in ASKED_VARIANTS
    if module in URN3_MODULES and variant in URN3_VARIANTS:
        return cover == "markets"
    if module in URN3_RATED_MODULES and variant in URN3_RATED_VARIANTS:
        return cover == "markets"
    if module in LOAD_MODULES:
        return cover == "markets" and variant in LOAD_VARIANTS
    if module in URN_MODULES and variant in VIG_VARIANTS:
        return cover == "markets"
    if module in V2_MODULES:
        return cover == "markets" and variant in URN2_VARIANTS
    if module in V2_ASKED_MODULES + V2_PROBED_MODULES:
        return cover == "markets" and variant == "urn2-named"
    if module in URN_MODULES:
        return cover == "markets" and variant in URN_VARIANTS + URN2_VARIANTS
    if module in URN_ASKED_MODULES + URN_PROBED_MODULES:
        return cover == "markets" and variant in ("urn-named", "urn2-named")
    if module == "checks":
        return variant == "paired"
    return variant in VARIANTS


def render(module, cover, index, variant="paired"):
    if cover not in COVERS:
        raise ValueError(f"Unknown cover: {cover}")
    if module not in RENDERERS or not allowed(module, cover, variant):
        raise ValueError(f"Unknown variant for {module}: {variant}")
    items = items_for(module)
    if not 0 <= index < len(items["prior"]):
        raise ValueError("Item index outside the design")
    lines, question = RENDERERS[module](items, index, cover, variant)
    return {
        "case": "\n\n".join(lines),
        "question": question,
        "response": "points" if module == "checks" else "probability",
    }


def stated_percentages(module, index):
    """Every probability the case must display, for the rendering audit."""
    items = items_for(module)
    if module in LOAD_DESIGNS:
        from epistemics.disposition_tasks.urn import load_percentages

        return load_percentages(urn_family(module), items, index)
    if module in URN_DESIGNS:
        return urn_percentages(urn_family(module), items, index)
    described = CUE_MODULES + RANGE_MODULES + DOSSIER_MODULES + ASKED_MODULES + PROBED_MODULES
    if module in described and items["kind"][index] == "rate":
        disclosure = module in ("disclosure-cues", "disclosure-dossier", "disclosure-asked")
        return [percent(items["omission"][index])] if disclosure else []
    if module == "checks":
        prior, high, low = (items[f][index] for f in ("prior", "high", "low"))
        values = [prior, high, low, (prior - low) / (high - low)]
    elif module in (
        "corroboration",
        "corroboration-cues",
        "corroboration-range",
        "corroboration-dossier",
        "corroboration-unprompted",
        "corroboration-asked",
        "corroboration-probed",
    ):
        values = [items["prior"][index], items["accuracy_a"][index]]
        if items["kind"][index] != "single":
            values.append(items["accuracy_b"][index])
    else:
        g = items["good"][index]
        values = [items["prior"][index], g, 1 - g, items["omission"][index]]
    return sorted({percent(v) for v in np.asarray(values, dtype=float)})


def urn_percentages(family, items, index):
    family = V2_TWINS.get(family, family)
    kind = items["kind"][index]
    if family == "selection":
        g = items["good"][index]
        values = [items["omission"][index]]
        if kind != "rate":
            values += [items["prior"][index], g, 1 - g]
    elif kind == "rate":
        values = []
    elif family == "copying":
        values = [items["prior"][index], items["accuracy_a"][index]]
        if kind != "single":
            values.append(items["accuracy_b"][index])
    else:
        values = [items["prior"][index], items["accuracy_a"][index]]
        if kind == "own":
            values.append(1 - items["accuracy_a"][index])
    return sorted({percent(v) for v in np.asarray(values, dtype=float)})


def reveal(module, cover, index, case_number, structure):
    """What a learning variant shows about an answered case: relay or not, selective or not."""
    if structure is None:
        return f"Case {case_number} had only one report, so there is nothing to reveal."
    if module == "corroboration":
        a = OUTLETS_A[index] if cover == "markets" else f"Station N{index + 11}"
        b = OUTLETS_B[index] if cover == "markets" else f"Station S{index + 41}"
        if cover == "markets":
            done = f"had relayed {own(a)} call" if structure else "had checked for itself"
        else:
            done = f"had forwarded {own(a)} report" if structure else "had sampled for itself"
        return f"Revealed after case {case_number}: {b} {done}."
    if cover == "markets":
        kind = (
            "shares every on-target indicator and withholds every off-target one"
            if structure
            else "leaves indicators out at random"
        )
        return f"Revealed after case {case_number}: {COMPANIES[index]} is a company that {kind}."
    kind = (
        "reports every passing marker and withholds every failing one"
        if structure
        else "leaves markers out at random"
    )
    return f"Revealed after case {case_number}: {CONTRACTORS[index]} is a contractor that {kind}."
