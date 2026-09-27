"""Deterministic templated rendering (0.3): register versus validity of survey reports.

Each dossier holds two genuine polished survey reports, one manipulated report slot and
distractors, in shuffled order. A fabricated report is written in the same polished register
as genuine ones but contains exactly one internally impossible figure. An informal report
carries the same valid counts as its polished twin. Every case brief states the same general
background facts, whatever its family.
"""

import math
from datetime import date, timedelta

import numpy as np

from epistemics.research_world3.world import CHECK_RATES, World

PREFIXES = (
    "Corvane", "Tallis", "Brightwell", "Quorra", "Halden", "Mirelle", "Ostrava", "Pellam",
    "Varden", "Keswick", "Lumora", "Draycott", "Averon", "Belmark", "Calloway", "Denholm",
    "Eskar", "Fairlow", "Gantry", "Hollis", "Ivory", "Juniper", "Kestrel", "Larkspur",
)  # fmt: skip
SECTORS = (
    ("Systems", "logistics software"),
    ("Analytics", "retail analytics"),
    ("Health", "clinic scheduling software"),
    ("Robotics", "warehouse automation"),
    ("Networks", "field-service connectivity"),
    ("Labs", "laboratory data management"),
)
FIRMS = (
    "Harlow Research",
    "Pike & Mercer",
    "Castellan Partners",
    "Rowan Street Research",
    "Fenwick Insights",
)
OUTLETS = (
    "Northgate Wire",
    "The Ledger Dispatch",
    "Market Pulse Daily",
    "The Allocator Brief",
    "Sector Watch",
    "The Quarterly Ledger",
)
DISTRACTORS = (
    "{rival} named a new chief financial officer, effective next month. The company said the "
    "appointment was unrelated to its operating results.",
    "A trade association revised the methodology of its quarterly hiring index; the revised "
    "series will not be comparable with earlier releases until next year.",
    "{rival} opened a second office in Lisbon, citing access to engineering talent. It did not "
    "disclose headcount plans.",
    "Freight spot rates on transatlantic lanes were broadly flat in August, according to a "
    "broker index, after a volatile first half.",
    "A regional bank said it would expand lending to small software firms. The program is "
    "limited to companies with fewer than fifty employees.",
    "{other} agreed to acquire a small payments start-up for an undisclosed sum. The deal is "
    "expected to close in the fourth quarter.",
    "Office vacancy in the city's technology district rose slightly, a commercial property "
    "broker said, citing longer lease negotiations.",
    "{other} settled a patent dispute with a former supplier. Terms were not disclosed and "
    "neither company admitted wrongdoing.",
    "A standards body published a draft update to data-retention guidelines for software "
    "vendors; comments are open until November.",
    "{rival} said its annual user conference would move online this year to reduce travel "
    "costs for customers.",
    "Industry hiring of sales engineers slowed in July, according to a recruiting firm's "
    "monthly tracker, after strong growth in the spring.",
    "{other} appointed two independent directors to its board, expanding it to nine members.",
    "A logistics trade publication named its annual list of fastest-growing carriers; no "
    "software vendors were included.",
    "{rival} completed a planned migration of its data centers and reported no customer "
    "disruption during the move.",
)
BACKGROUND = (
    "- Each survey varies independently of the others once demand is known.",
    "- Every research firm's reseller survey has the reliability given above, however it is "
    "written up.",
    "- A survey report whose own figures are impossible taken together has been fabricated or "
    "corrupted and carries no information about demand.",
)
DOCUMENTS = 10
MARGIN_CONSTANT = 98  # 95% margin of error in points for a proportion near one half


def possessive(name):
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def margin(sample):
    return round(MARGIN_CONSTANT / math.sqrt(sample))


def company_name(pair_seed, family):
    rng = np.random.default_rng([pair_seed, 30, 0 if family == "validity" else 1])
    return (
        f"{PREFIXES[int(rng.integers(len(PREFIXES)))]} "
        f"{SECTORS[int(rng.integers(len(SECTORS)))][0]}"
    )


def names(pair_seed, family):
    rng = np.random.default_rng([pair_seed, 30, 0 if family == "validity" else 1])
    prefix = PREFIXES[int(rng.integers(len(PREFIXES)))]
    suffix, sector = SECTORS[int(rng.integers(len(SECTORS)))]
    others = [p for p in PREFIXES if p != prefix]
    picks = [others[int(i)] for i in rng.permutation(len(others))[:2]]
    return {
        "company": f"{prefix} {suffix}",
        "short": prefix,
        "sector": sector,
        "rival": f"{picks[0]} {SECTORS[int(rng.integers(len(SECTORS)))][0]}",
        "other": f"{picks[1]} {SECTORS[int(rng.integers(len(SECTORS)))][0]}",
        "firms": [FIRMS[int(i)] for i in rng.permutation(len(FIRMS))],
        "start": date(2026, 7, 20) + timedelta(days=int(rng.integers(0, 28))),
        "distractors": [DISTRACTORS[int(i)] for i in rng.permutation(len(DISTRACTORS))],
        "order": [int(i) for i in rng.permutation(DOCUMENTS)],
        "offsets": [int(rng.integers(1, 12)) for _ in range(DOCUMENTS)],
    }


def brief(world, n):
    lines = [
        f"Company: {n['company']} ({n['sector']}). Question: is end-customer demand strong or weak?",
        f"Before the documents below, the probability of strong demand is {world.prior_strong:.0%}.",
        f"Investing earns {1 - world.threshold:.2f} points if demand is strong and loses "
        f"{world.threshold:.2f} if it is weak. Declining earns zero.",
        "Reference rates from comparable companies:",
        "- A reseller survey comes back positive (more resellers reporting higher reorders than "
        f"lower) {CHECK_RATES[0]:.0%} of the time when demand is strong and {CHECK_RATES[1]:.0%} "
        "when it is weak.",
        "Background:",
        *BACKGROUND,
    ]
    return "\n".join(lines)


def document(kind, source, day, title, text):
    return {"kind": kind, "source": source, "date": day.isoformat(), "title": title, "text": text}


def field_dates(atom, n):
    d = atom.detail
    first = n["start"] + timedelta(days=d["field_start"])
    last = first + timedelta(days=d["field_days"])
    if d["marker"] == "dates":
        first, last = last, first  # Fieldwork reported as ending before it began.
    return first, last


def polished(atom, firm, n):
    d = atom.detail
    counts = [d["higher"], d["flat"], d["lower"]]
    marker = d["marker"]
    if marker == "counts":
        counts[1] += d["excess"]  # More answers than respondents.
    total = sum(counts)
    percents = [round(100 * c / total) for c in counts]
    if marker == "percentages":
        percents[0] += d["excess"] + 6  # Shares that cannot sum to one hundred.
    moe = 1 if marker == "margin" else margin(d["sample"])
    first, last = field_dates(atom, n)
    text = (
        f"{firm} fielded a reseller survey for {n['company']} from {first:%B %-d} to "
        f"{last:%B %-d}. Of {d['sample']} resellers who responded, {counts[0]} ({percents[0]}%) "
        f"reported higher reorders than last quarter, {counts[1]} ({percents[1]}%) flat and "
        f"{counts[2]} ({percents[2]}%) lower. At this sample size the margin of error is about "
        f"±{moe} points at 95% confidence."
    )
    day = max(first, last) + timedelta(days=2)
    return document("research report", firm, day, f"{n['short']}: reseller survey", text)


def informal(atom, firm, n):
    d = atom.detail
    first, last = field_dates(atom, n)
    text = (
        f"quick one on {n['short'].lower()} - heard back from {d['sample']} resellers between "
        f"{first:%b %-d} and {last:%b %-d}. {d['higher']} say reorders up vs last qtr, "
        f"{d['flat']} flat, {d['lower']} down. writing this up fast from the airport, full deck "
        "next week"
    )
    day = last + timedelta(days=2)
    return document("analyst email", firm, day, f"{n['short']} resellers", text)


def slots(world, n):
    """Two genuine reports, then the manipulated slot when the world includes it."""
    result = {
        0: polished(world.atoms[0], n["firms"][1], n),
        1: polished(world.atoms[1], n["firms"][2], n),
    }
    if len(world.atoms) == 3:
        report = world.atoms[2]
        writer = informal if report.atom_id in world.discounted else polished
        result[2] = writer(report, n["firms"][0], n)
    return result


def render(world: World):
    n = names(world.pair_seed, world.family)
    filled = slots(world, n)
    docs = []
    for slot in range(DOCUMENTS):
        if slot in filled:
            docs.append(filled[slot])
        else:
            # Distractors are fixed per slot, so matched dossiers differ only in the report slot.
            text = n["distractors"][slot].format(rival=n["rival"], other=n["other"])
            day = n["start"] + timedelta(days=n["offsets"][slot])
            docs.append(document("news brief", OUTLETS[slot % 6], day, "Sector roundup", text))
    ordered = [docs[i] for i in n["order"]]
    return {
        "schema_version": "epistemics.research-dossier.v3",
        "case": brief(world, n),
        "documents": [{"doc_id": f"D{i}", **d} for i, d in enumerate(ordered, 1)],
    }


REASONS = {
    "counts": "its answer counts add up to more than the resellers who responded",
    "percentages": "its percentage shares cannot sum to one hundred",
    "dates": "its fieldwork is dated as ending before it began",
    "margin": "its stated margin of error is impossible for so few respondents",
}


def structure_note(world: World):
    """The explicit arm's statement of validity and register, generated from the ledger."""
    n = names(world.pair_seed, world.family)
    if world.presentation in ("omitted", "absent"):
        return "The dossier's two survey reports are internally consistent."
    if world.presentation == "invalid":
        reason = REASONS[world.atom(world.invalid[0]).detail["marker"]]
        return (
            f"{possessive(n['firms'][0])} report is internally impossible ({reason}), so it carries no "
            "information; the other two reports are consistent."
        )
    if world.presentation == "sloppy":
        return (
            f"{possessive(n['firms'][0])} informal email is internally consistent and as reliable as the "
            "polished reports."
        )
    return "All three survey reports are internally consistent."


def check_document(result, sample, count, day):
    """The purchased independent survey, as a new dossier document."""
    return {
        "doc_id": "C1",
        "kind": "commissioned survey",
        "source": "Independent survey commissioned for you",
        "date": day.isoformat(),
        "title": "End-customer spending survey",
        "text": f"Of {sample} end customers surveyed, {count} said they are increasing spend with "
        "the company this year. "
        + (
            "The survey reads positive: a majority are increasing spend."
            if result
            else "The survey reads negative: a majority are not increasing spend."
        ),
    }
