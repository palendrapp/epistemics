"""Deterministic templated rendering of a private world into a public dossier.

Every choice except the manipulated structure is drawn from the pair seed, so matched
presentations share company, dates, outlets, phrasing and distractors. Nothing private
(demand, atom identifiers, rates beyond the public case brief) enters the rendered text.
"""

from datetime import date, timedelta

import numpy as np

from epistemics.research_world.world import CHECK_RATES, World

PREFIXES = (
    "Corvane", "Tallis", "Brightwell", "Quorra", "Halden", "Mirelle",
    "Ostrava", "Pellam", "Varden", "Keswick", "Lumora", "Draycott",
)  # fmt: skip
SECTORS = (
    ("Systems", "logistics software"),
    ("Analytics", "retail analytics"),
    ("Health", "clinic scheduling software"),
    ("Robotics", "warehouse automation"),
    ("Networks", "field-service connectivity"),
    ("Labs", "laboratory data management"),
)
ANALYSTS = (
    "Harlow Research",
    "Pike & Mercer",
    "Castellan Partners",
    "Rowan Street Research",
    "Fenwick Insights",
)
OUTLETS = ("Northgate Wire", "The Ledger Dispatch", "Market Pulse Daily", "The Allocator Brief")
NEWSLETTERS = ("Signal & Noise", "The Midcap Memo", "Unit Economics Weekly")
DISTRACTORS = (
    "{rival} named a new chief financial officer, effective next month. The company said the "
    "appointment was unrelated to its operating results.",
    "A trade association revised the methodology of its quarterly hiring survey; the revised "
    "series will not be comparable with earlier releases until next year.",
    "{rival} opened a second office in Lisbon, citing access to engineering talent. It did not "
    "disclose headcount plans.",
    "Freight spot rates on transatlantic lanes were broadly flat in August, according to a "
    "broker index, after a volatile first half.",
    "A regional bank said it would expand lending to small software firms. The program is "
    "limited to companies with fewer than fifty employees.",
)
WORDS = {2: "two", 3: "three", 4: "four"}
KPI_UNITS = {"%": "{:.0f}%", "": "{:.0f}", "x": "{:.1f}x", "$k": "${:.0f}k"}


def fmt(atom, key):
    return KPI_UNITS[atom.detail["unit"]].format(atom.detail[key])


def names(pair_seed, family):
    rng = np.random.default_rng([pair_seed, 10 if family == "disclosure" else 11])
    prefix = PREFIXES[int(rng.integers(len(PREFIXES)))]
    suffix, sector = SECTORS[int(rng.integers(len(SECTORS)))]
    rival = PREFIXES[int(rng.integers(len(PREFIXES)))]
    while rival == prefix:
        rival = PREFIXES[int(rng.integers(len(PREFIXES)))]
    analysts = [ANALYSTS[int(i)] for i in rng.permutation(len(ANALYSTS))]
    outlets = [OUTLETS[int(i)] for i in rng.permutation(len(OUTLETS))]
    newsletter = NEWSLETTERS[int(rng.integers(len(NEWSLETTERS)))]
    start = date(2026, 7, 20) + timedelta(days=int(rng.integers(0, 28)))
    distractors = [DISTRACTORS[int(i)] for i in rng.permutation(len(DISTRACTORS))]
    return {
        "company": f"{prefix} {suffix}",
        "short": prefix,
        "sector": sector,
        "rival": f"{rival} {SECTORS[int(rng.integers(len(SECTORS)))][0]}",
        "analysts": analysts,
        "outlets": outlets,
        "newsletter": newsletter,
        "start": start,
        "distractors": distractors,
        "variant": int(rng.integers(2)),
    }


def brief(world, n):
    lines = [
        f"Company: {n['company']} ({n['sector']}). Question: is end-customer demand strong or weak?",
        f"Before the documents below, the probability of strong demand is {world.prior_strong:.0%}.",
        f"Investing earns {1 - world.threshold:.2f} points if demand is strong and loses "
        f"{world.threshold:.2f} if it is weak. Declining earns zero.",
        "Reference rates from comparable companies:",
    ]
    for atom in world.atoms if world.family == "disclosure" else world.atoms[:1]:
        if atom.kind == "kpi":
            lines.append(
                f"- When demand is strong, a company beats its {atom.name} guidance in "
                f"{atom.p_favorable_strong:.0%} of quarters; when weak, in "
                f"{atom.p_favorable_weak:.0%}."
            )
    if world.family == "shared_origin":
        lines.append(
            "- A reseller channel check comes back positive (more resellers reporting higher "
            f"reorders than lower) {CHECK_RATES[0]:.0%} of the time when demand is strong and "
            f"{CHECK_RATES[1]:.0%} when it is weak. Each research firm fields its own survey."
        )
    return "\n".join(lines)


def document(doc_id, kind, source, day, title, text):
    return {
        "doc_id": doc_id,
        "kind": kind,
        "source": source,
        "date": day.isoformat(),
        "title": title,
        "text": text,
    }


def kpi_sentence(atom):
    verb = "ahead of" if atom.favorable else "short of"
    return f"{atom.name.capitalize()} came in at {fmt(atom, 'actual')}, {verb} guidance of {fmt(atom, 'guidance')}."


def disclosure_documents(world, n):
    tracked = [a for a in world.atoms]
    shown = [world.atom(i) for i in world.shown]
    letter_intro = (
        f"Dear shareholders, the second quarter brought steady execution at {n['short']}.",
        f"To our shareholders: {n['short']} closed the second quarter with continued focus on customers.",
    )[n["variant"]]
    letter = " ".join([letter_intro, *(kpi_sentence(a) for a in shown)])
    letter += " We remain committed to disciplined growth."
    analyst = n["analysts"][0]
    tracked_names = ", ".join(a.name for a in tracked)
    if world.presentation == "full":
        note = (
            f"{n['company']} tracks {WORDS[len(tracked)]} operating KPIs ({tracked_names}) and, as in "
            "every quarter since listing, its letter reports all of them against guidance."
        )
    elif world.presentation == "selected":
        note = (
            f"{n['company']} tracks {WORDS[len(tracked)]} operating KPIs ({tracked_names}). As in every "
            "quarter since listing, its letter discusses only the KPIs that met or exceeded "
            "guidance."
        )
    else:
        note = (
            f"{n['company']} tracks {WORDS[len(tracked)]} operating KPIs ({tracked_names}) and, as in "
            "every quarter since listing, its letter reports each of them against guidance."
        )
    note += " We make no change to our rating ahead of the investor day."
    start = n["start"]
    return [
        document("D1", "shareholder letter", n["company"], start, "Q2 shareholder letter", letter),
        document(
            "D2",
            "analyst note",
            analyst,
            start + timedelta(days=1),
            f"{n['short']}: Q2 letter review",
            note,
        ),
        document(
            "D3",
            "news brief",
            n["outlets"][0],
            start + timedelta(days=2),
            "Sector roundup",
            n["distractors"][0].format(rival=n["rival"]),
        ),
        document(
            "D4",
            "news brief",
            n["outlets"][1],
            start + timedelta(days=3),
            "Sector roundup",
            n["distractors"][1].format(rival=n["rival"]),
        ),
    ]


def possessive(name):
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def check_text(atom, n):
    """An analyst's own report of its survey."""
    d = atom.detail
    direction = "higher" if atom.favorable else "lower"
    k = d["count"] if atom.favorable else d["sample"] - d["count"]
    return (
        f"Our channel check of {d['sample']} resellers of {n['company']} found {k} reporting "
        f"{direction} reorders than last quarter, the rest flat or the other way."
    )


def relay_text(atom, firm, n, genre):
    """A third party repeating the analyst's figures, with attribution but its own wording."""
    d = atom.detail
    direction = "higher" if atom.favorable else "lower"
    k = d["count"] if atom.favorable else d["sample"] - d["count"]
    day = n["start"].strftime("%B %-d")
    if genre == "news brief":
        return (
            f"{n['company']} resellers are reordering {'more' if atom.favorable else 'less'}: "
            f"{k} of {d['sample']} surveyed by {firm} reported {direction} reorders than last "
            f"quarter, the firm said in a note on {day}."
        )
    return (
        f"Worth a look: {possessive(firm)} reseller survey for {n['company']} ({k} of "
        f"{d['sample']} reporting {direction} reorders) landed on {day}."
    )


def shared_documents(world, n):
    first = world.atoms[0]
    analyst = n["analysts"][0]
    start = n["start"]
    docs = [
        document(
            "D1",
            "analyst note",
            analyst,
            start,
            f"{n['short']}: reseller channel check",
            check_text(first, n) + " We surveyed resellers directly over two weeks.",
        )
    ]
    if world.presentation == "relayed":
        docs.append(
            document(
                "D2",
                "news brief",
                n["outlets"][0],
                start + timedelta(days=1),
                f"Resellers weigh in on {n['short']}",
                relay_text(first, analyst, n, "news brief"),
            )
        )
        docs.append(
            document(
                "D3",
                "newsletter",
                n["newsletter"],
                start + timedelta(days=2),
                "What we're reading",
                relay_text(first, analyst, n, "newsletter"),
            )
        )
    elif world.presentation == "independent":
        for i, atom in enumerate(world.atoms[1:], 1):
            firm = n["analysts"][i]
            docs.append(
                document(
                    f"D{i + 1}",
                    "analyst note",
                    firm,
                    start + timedelta(days=i),
                    f"{n['short']}: our own reseller survey",
                    check_text(atom, n) + " The survey was designed and fielded by our own team.",
                )
            )
    else:
        for i in (1, 2):
            docs.append(
                document(
                    f"D{i + 1}",
                    "news brief",
                    n["outlets"][i - 1],
                    start + timedelta(days=i),
                    "Sector roundup",
                    n["distractors"][i - 1].format(rival=n["rival"]),
                )
            )
    docs.append(
        document(
            "D4",
            "news brief",
            n["outlets"][2],
            start + timedelta(days=3),
            "Sector roundup",
            n["distractors"][2].format(rival=n["rival"]),
        )
    )
    return docs


def render(world: World):
    n = names(world.pair_seed, world.family)
    docs = (disclosure_documents if world.family == "disclosure" else shared_documents)(world, n)
    return {
        "schema_version": "epistemics.research-dossier.v1",
        "case": brief(world, n),
        "documents": docs,
    }


def structure_note(world: World):
    """The explicit arm's statement of provenance or disclosure, generated from the ledger."""
    n = names(world.pair_seed, world.family)
    if world.presentation == "full":
        return f"The letter reports all {WORDS[len(world.atoms)]} KPIs the company tracks."
    if world.presentation == "selected":
        missing = ", ".join(world.atom(i).name for i in world.implied)
        return (
            "The letter covers only KPIs that met or exceeded guidance, so the tracked KPIs it "
            f"omits ({missing}) missed guidance."
        )
    if world.presentation == "silent_control":
        return "The company tracks only the KPIs its letter reports; nothing is omitted."
    if world.presentation == "single":
        return "Only D1 reports a reseller survey; the other documents concern other companies or the sector."
    if world.presentation == "relayed":
        return (
            f"D2 and D3 repeat the figures from {possessive(n['analysts'][0])} survey in D1; "
            "they are not separate surveys."
        )
    return "D1, D2 and D3 report three separate surveys by different research firms."


def check_document(result, sample, count, day):
    """The purchased independent survey, as a new dossier document."""
    return document(
        "C1",
        "commissioned survey",
        "Independent survey commissioned for you",
        day,
        "End-customer spending survey",
        f"Of {sample} end customers surveyed, {count} said they are increasing spend with the "
        f"company this year. The survey reads {'positive' if result else 'negative'} "
        "(a majority increasing versus not).",
    )
