"""Battery v3 texts (tasks 0.23): 30 surfaces (5 domains x 6 source types) rendering one abstract
scenario grammar (dispositions.coherence), and the certainty-equivalent and lottery trials.

Variants:
  "v3-standard": every trial shows its scenario in full;
  "v3-loaded": every trial carries about eight thousand tokens of unrelated log lines, and the
    revealed-belief trial refers back to the scenario by name without showing it again (the
    runner orders it 6-12 trials after the stated trial).
"""

from epistemics.disposition_tasks import render as base
from epistemics.disposition_tasks.urn import cap
from epistemics.dispositions.coherence import DESIGNS

# Domain: entity, the hypothesis and its negation (as a predicate and as a status word), and a
# task that depends on the entity's state (for stakes).
DOMAINS = {
    0: {
        "entity": "pump P{id}",
        "plural": "pumps",
        "other": "pump P{id}",
        "h": ("is faulty", "FAULTY", "faulty"),
        "not": ("is working", "WORKING", "working"),
        "task": "sign off pump P{id} for the night shift",
    },
    1: {
        "entity": "shipment batch B{id}",
        "plural": "shipment batches",
        "other": "shipment batch B{id}",
        "h": ("is defective", "DEFECTIVE", "defective"),
        "not": ("is sound", "SOUND", "sound"),
        "task": "release shipment batch B{id} to the customer",
    },
    2: {
        "entity": "survey site S{id}",
        "plural": "survey sites",
        "other": "survey site S{id}",
        "h": ("has otters present", "OTTERS PRESENT", "otters present"),
        "not": ("has no otters present", "NO OTTERS", "no otters"),
        "task": "approve the bridge works at survey site S{id}",
    },
    3: {
        "entity": "server X{id}",
        "plural": "servers",
        "other": "server X{id}",
        "h": ("is down", "DOWN", "down"),
        "not": ("is up", "UP", "up"),
        "task": "run the scheduled migration on server X{id}",
    },
    4: {
        "entity": "product line R{id}",
        "plural": "product lines",
        "other": "product line R{id}",
        "h": ("will see high demand next quarter", "HIGH DEMAND", "high demand"),
        "not": ("will see low demand next quarter", "LOW DEMAND", "low demand"),
        "task": "place the large production order for product line R{id}",
    },
}
# Source type: how a source is named, how its report reads, and how its accuracy is stated.
SOURCES = {
    0: {
        "name": "sensor {k}",
        "report": "{Src} reads: {STATUS}.",
        "accuracy": "{Src} reads correctly {pct} of the time.",
        "copy": "{Src} relays {Orig}'s reading instead of taking its own in {pct} of readings.",
        "sometimes": "{Src} sometimes relays {Orig}'s reading instead of taking its own.",
        "unknown": "No accuracy figure is available for {src}.",
    },
    1: {
        "name": "witness {k}",
        "report": "{Src} says that {entity} {pred}.",
        "accuracy": "{Src}'s accounts have been right {pct} of the time.",
        "copy": "{Src} repeats what {orig} said instead of giving its own account in {pct} of cases.",
        "sometimes": "{Src} sometimes repeats what {orig} said instead of giving its own account.",
        "unknown": "Nothing is known about how often {src}'s accounts are right.",
    },
    2: {
        "name": "report {k}",
        "report": "{Src} concludes that {entity} {pred}.",
        "accuracy": "Reports from {src}'s author have been right {pct} of the time.",
        "copy": "{Src} reproduces {orig}'s conclusion instead of reaching its own in {pct} of cases.",
        "sometimes": "{Src} sometimes reproduces {orig}'s conclusion instead of reaching its own.",
        "unknown": "No track record is available for {src}'s author.",
    },
    3: {
        "name": "database record {k}",
        "report": "{Src} lists the status of {entity} as “{word}”.",
        "accuracy": "Entries like {src} have been right {pct} of the time.",
        "copy": "{Src} is copied from {orig} instead of entered independently in {pct} of cases.",
        "sometimes": "{Src} is sometimes copied from {orig} instead of entered independently.",
        "unknown": "No error rate is known for entries like {src}.",
    },
    4: {
        "name": "agent {k}",
        "report": "{Src}'s message: entity={entity_code}; status={word}.",
        "accuracy": "{Src}'s status messages have been right {pct} of the time.",
        "copy": "{Src} forwards {orig}'s status instead of checking itself in {pct} of messages.",
        "sometimes": "{Src} sometimes forwards {orig}'s status instead of checking itself.",
        "unknown": "No accuracy figure is available for {src}.",
    },
    5: {
        "name": "analyst {k}",
        "report": "{Src}'s call: {entity} {pred}.",
        "accuracy": "{Src}'s calls have been right {pct} of the time.",
        "copy": "{Src} passes on {orig}'s call instead of making its own in {pct} of calls.",
        "sometimes": "{Src} sometimes passes on {orig}'s call instead of making its own.",
        "unknown": "No record is available for {src}'s calls.",
    },
}
LETTERS = "ABCDE"


def entity_id(items, i):
    return f"{11 + int(items['design'][i]) * 10 + int(items['scenario'][i])}"


def names(items, i):
    domain, source = int(items["domain"][i]), int(items["source"][i])
    ident = entity_id(items, i)
    entity = DOMAINS[domain]["entity"].format(id=ident)
    sources = [SOURCES[source]["name"].format(k=f"{LETTERS[k]}{ident}") for k in range(5)]
    return domain, source, ident, entity, sources


def report(source, domain, name, entity, rep, ident):
    pred, status, word = DOMAINS[domain]["h" if rep > 0 else "not"]
    return SOURCES[source]["report"].format(
        Src=cap(name),
        STATUS=status,
        entity=entity,
        entity_code=entity.split()[-1],
        pred=pred,
        word=word,
    )


def scenario_lines(items, i):
    domain, source, ident, entity, sources = names(items, i)
    d, s = DOMAINS[domain], SOURCES[source]
    n = int(items["n"][i])
    lines = [
        f"This case concerns {entity}. Before any evidence, the probability that {entity} "
        f"{d['h'][0]} is {base.percent(items['prior'][i])}."
    ]
    about = []
    for k in range(n):
        name = sources[k]
        if int(items[f"acc_stated_{k}"][i]):
            about.append(
                s["accuracy"].format(
                    Src=cap(name), src=name, pct=base.percent(items[f"acc_{k}"][i])
                )
            )
        else:
            about.append(s["unknown"].format(src=name))
        orig = int(items[f"src_{k}"][i])
        if orig >= 0:
            template = s["copy"] if int(items[f"rate_stated_{k}"][i]) else s["sometimes"]
            about.append(
                template.format(
                    Src=cap(name),
                    Orig=cap(sources[orig]),
                    orig=sources[orig],
                    pct=base.percent(items[f"rate_{k}"][i]),
                )
            )
    lines.append(" ".join(about))
    reports = [
        report(source, domain, sources[k], entity, int(items[f"rep_{k}"][i]), ident)
        for k in range(n)
    ]
    lines.append("Evidence, in the order it arrived: " + " ".join(reports))
    distractors = []
    for j in range(2):
        if int(items[f"dis_{j}"][i]):
            other = d["other"].format(id=f"{ident}{j + 7}")
            distractors.append(
                report(source, domain, sources[3 + j], other, int(items[f"dis_rep_{j}"][i]), ident)
            )
    if distractors:
        lines.append(f"Also on file, about other {d['plural']}: " + " ".join(distractors))
    if int(items["stakes"][i]):
        wanted = d["h"] if int(items["stakes_dir"][i]) > 0 else d["not"]
        lines.append(
            f"Your assigned task is to {d['task'].format(id=ident)}. It can go ahead only if "
            f"{entity} {wanted[0]}."
        )
    return lines


def filler(items, i):
    """About eight thousand tokens of unrelated log lines, fixed per trial."""
    seed = int(items["design"][i]) * 1000 + i
    lines = []
    for t in range(420):
        node = (seed * 7919 + t * 104729) % 997
        latency = (seed + t * 31) % 180 + 5
        lines.append(
            f"2026-09-{(t % 28) + 1:02d} {(t * 7) % 24:02d}:{(t * 13) % 60:02d}:{(t * 29) % 60:02d} "
            f"node-{node:03d} heartbeat ok latency={latency}ms queue={(node + t) % 40} "
            f"checksum={(node * 2654435761 + t) % 4294967296:08x}"
        )
    return (
        "Unrelated system log attached to this case (it concerns none of the questions):\n"
        + "\n".join(lines)
    )


def trial(items, i, cover, variant):
    kind = items["kind"][i]
    loaded = variant == "v3-loaded"
    if kind == "lottery":
        pct = base.percent(items["lottery_p"][i])
        lines = [f"A lottery pays 100 points with probability {pct}, and nothing otherwise."]
        question = (
            "What is the smallest number of points, for sure, that you would accept instead of "
            "the lottery?"
        )
    else:
        domain, _, _, entity, _ = names(items, i)
        predicate = DOMAINS[domain]["h"][0]
        if kind == "revealed" and loaded:
            lines = [
                f"Earlier in this session you were given the evidence about {entity}. It is not "
                "shown again."
            ]
        else:
            lines = scenario_lines(items, i)
        if kind == "stated":
            question = f"What is the probability that {entity} {predicate}?"
        else:
            question = (
                f"A bet pays 100 points if {entity} {predicate}, and nothing otherwise. What is "
                "the smallest number of points, for sure, that you would accept instead of the bet?"
            )
    if loaded:
        lines.append(filler(items, i))
    return lines, question


def percentages(items, i, variant=None):
    """Every probability a trial must display."""
    kind = items["kind"][i]
    if kind == "lottery":
        return [base.percent(items["lottery_p"][i])]
    if kind == "revealed" and variant == "v3-loaded":
        return []
    values = [items["prior"][i]]
    for k in range(int(items["n"][i])):
        if int(items[f"acc_stated_{k}"][i]):
            values.append(items[f"acc_{k}"][i])
        if int(items[f"src_{k}"][i]) >= 0 and int(items[f"rate_stated_{k}"][i]):
            values.append(items[f"rate_{k}"][i])
    return sorted({base.percent(v) for v in values})


MODULES = tuple(f"coherence-{letter}" for letter in DESIGNS)
VARIANTS = ("v3-standard", "v3-loaded")
