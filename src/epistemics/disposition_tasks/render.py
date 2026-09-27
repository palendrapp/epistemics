"""Templated case text for each module under two cover stories with identical structure.

Markets cases concern company demand; ecology cases concern a lake's fish stock. Names are
fixed by item, so a retest with the same cover shows identical text in a new order.
"""

import math

import numpy as np

from epistemics.dispositions import design

MODULES = ("corroboration", "disclosure", "checks")
COVERS = ("markets", "ecology")

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


def _corroboration(items, i, cover):
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
            lines += [
                f"{b} also reports on {subject}: it says demand is {call(items['report_b'][i])}. "
                f"When {b} checks for itself, its calls are correct {accuracy} of the time.",
                "Some outlets relay another outlet's call instead of checking for themselves; a "
                f"relayed call simply repeats the original call. {b} may have checked for itself "
                f"or relayed {own(a)} call.",
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
            lines += [
                f"{b}, another station, also reports on {subject}: it says the stock is "
                f"{call(items['report_b'][i])}. When {b} samples for itself, its reports are "
                f"correct {accuracy} of the time.",
                "Some stations forward another station's report instead of sampling for "
                f"themselves; a forwarded report simply repeats the original report. {b} may "
                f"have sampled for itself or forwarded {own(a)} report.",
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


def _disclosure(items, i, cover):
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
            f"with probability {rate}, whether or not it was on target. {subject} could be "
            "either kind.",
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
            f"probability {rate}, whether or not it passed. {contractor} could be either kind.",
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


def _checks(items, i, cover):
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


RENDERERS = {"corroboration": _corroboration, "disclosure": _disclosure, "checks": _checks}


def render(module, cover, index):
    if cover not in COVERS:
        raise ValueError(f"Unknown cover: {cover}")
    items = items_for(module)
    if not 0 <= index < len(items["prior"]):
        raise ValueError("Item index outside the design")
    lines, question = RENDERERS[module](items, index, cover)
    return {
        "case": "\n\n".join(lines),
        "question": question,
        "response": "points" if module == "checks" else "probability",
    }


def stated_percentages(module, index):
    """Every probability the case must display, for the rendering audit."""
    items = items_for(module)
    if module == "checks":
        prior, high, low = (items[f][index] for f in ("prior", "high", "low"))
        values = [prior, high, low, (prior - low) / (high - low)]
    elif module == "corroboration":
        values = [items["prior"][index], items["accuracy_a"][index]]
        if items["kind"][index] != "single":
            values.append(items["accuracy_b"][index])
    else:
        g = items["good"][index]
        values = [items["prior"][index], g, 1 - g, items["omission"][index]]
    return sorted({percent(v) for v in np.asarray(values, dtype=float)})
