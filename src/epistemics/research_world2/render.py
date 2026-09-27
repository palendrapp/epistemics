"""Deterministic templated rendering (0.2): structure must be inferred, not read.

Relays report a survey without naming who ran it, some with rounded figures; they link to the
original only through sample size, figures and publication date. No document states a
company's disclosure rule: an older initiation note lists the KPIs every letter has covered.
Every case brief carries the same general background facts, whatever its family. Dossiers
have ten documents, mostly distractors, in shuffled order; matched presentations share every
slot except the manipulated ones.
"""

from datetime import date, timedelta

import numpy as np

from epistemics.research_world2.world import CHECK_RATES, World

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
ANALYSTS = (
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
NEWSLETTER = ("Signal & Noise", "The Midcap Memo", "Unit Economics Weekly")
FORUM = ("Allocators Forum", "ValueTalk boards", "The Channel Checks thread")
PODCAST = ("Compounders podcast", "The Buy Side Hour", "Margin Call Radio")
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
    "- Each KPI result and each survey varies independently of the others once demand is known.",
    "- Research firms run reseller surveys themselves; news outlets, newsletters, podcasts and "
    "forums only report surveys run by others.",
    "- Companies sometimes leave a KPI out of a quarterly letter when it misses guidance; they "
    "never leave out a KPI that met or beat guidance.",
)
WORDS = {2: "two", 3: "three", 4: "four"}
KPI_UNITS = {"%": "{:.0f}%", "": "{:.0f}", "x": "{:.1f}x", "$k": "${:.0f}k"}
FRACTIONS = (
    (1 / 4, "one in four"),
    (3 / 10, "three in ten"),
    (1 / 3, "one in three"),
    (2 / 5, "two in five"),
    (1 / 2, "half"),
    (3 / 5, "three in five"),
    (2 / 3, "two-thirds"),
    (7 / 10, "seven in ten"),
    (3 / 4, "three-quarters"),
    (4 / 5, "four in five"),
)
DOCUMENTS = 10


def fmt(atom, key):
    return KPI_UNITS[atom.detail["unit"]].format(atom.detail[key])


def rounded(share):
    return min(FRACTIONS, key=lambda f: abs(f[0] - share))[1]


def company_name(pair_seed, family):
    rng = np.random.default_rng([pair_seed, 10 if family == "disclosure" else 11])
    return (
        f"{PREFIXES[int(rng.integers(len(PREFIXES)))]} "
        f"{SECTORS[int(rng.integers(len(SECTORS)))][0]}"
    )


def names(pair_seed, family):
    rng = np.random.default_rng([pair_seed, 10 if family == "disclosure" else 11])
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
        "analysts": [ANALYSTS[int(i)] for i in rng.permutation(len(ANALYSTS))],
        "outlets": [OUTLETS[int(i)] for i in rng.permutation(len(OUTLETS))],
        "newsletter": NEWSLETTER[int(rng.integers(len(NEWSLETTER)))],
        "forum": FORUM[int(rng.integers(len(FORUM)))],
        "podcast": PODCAST[int(rng.integers(len(PODCAST)))],
        "start": date(2026, 7, 20) + timedelta(days=int(rng.integers(0, 28))),
        "distractors": [DISTRACTORS[int(i)] for i in rng.permutation(len(DISTRACTORS))],
        "variant": int(rng.integers(2)),
        "relay_genres": [int(i) for i in rng.permutation(4)],
        "order": [int(i) for i in rng.permutation(DOCUMENTS)],
        "offsets": [int(rng.integers(1, 9)) for _ in range(DOCUMENTS)],
    }


def brief(world, n):
    lines = [
        f"Company: {n['company']} ({n['sector']}). Question: is end-customer demand strong or weak?",
        f"Before the documents below, the probability of strong demand is {world.prior_strong:.0%}.",
        f"Investing earns {1 - world.threshold:.2f} points if demand is strong and loses "
        f"{world.threshold:.2f} if it is weak. Declining earns zero.",
        "Reference rates from comparable companies:",
    ]
    if world.family == "disclosure":
        for atom in world.atoms:
            lines.append(
                f"- When demand is strong, a company meets or beats its {atom.name} guidance in "
                f"{atom.p_favorable_strong:.0%} of quarters; when weak, in "
                f"{atom.p_favorable_weak:.0%}."
            )
    else:
        lines.append(
            "- A reseller survey comes back positive (more resellers reporting higher reorders "
            f"than lower) {CHECK_RATES[0]:.0%} of the time when demand is strong and "
            f"{CHECK_RATES[1]:.0%} when it is weak."
        )
    lines.append("Background:")
    lines.extend(BACKGROUND)
    return "\n".join(lines)


def document(kind, source, day, title, text):
    return {"kind": kind, "source": source, "date": day.isoformat(), "title": title, "text": text}


def kpi_sentence(atom):
    verb = "ahead of" if atom.favorable else "short of"
    return (
        f"{atom.name.capitalize()} came in at {fmt(atom, 'actual')}, {verb} guidance of "
        f"{fmt(atom, 'guidance')}."
    )


def disclosure_slots(world, n):
    """The letter and the initiation note; everything else is a distractor slot."""
    shown = [world.atom(i) for i in world.shown]
    intro = (
        f"Dear shareholders, the second quarter brought steady execution at {n['short']}.",
        f"To our shareholders: {n['short']} closed the second quarter with continued focus on "
        "customers.",
    )[n["variant"]]
    letter = " ".join([intro, *(kpi_sentence(a) for a in shown)])
    letter += " We remain committed to disciplined growth."
    covered = ", ".join(a.name for a in world.atoms)
    initiation = (
        f"We initiate coverage of {n['company']}. Since listing, each of its quarterly letters "
        f"has covered the same {WORDS[len(world.atoms)]} KPIs: {covered}. We see a long runway "
        "in its core market."
    )
    start = n["start"]
    return {
        0: document("shareholder letter", n["company"], start, "Q2 shareholder letter", letter),
        1: document(
            "analyst note",
            n["analysts"][0],
            start - timedelta(days=120),
            f"Initiating coverage: {n['short']}",
            initiation,
        ),
    }


def own_check(atom, n, day):
    d = atom.detail
    direction = "higher" if atom.favorable else "lower"
    k = d["count"] if atom.favorable else d["sample"] - d["count"]
    return (
        f"Our reseller survey, published {day:%B %-d}: of {d['sample']} resellers of "
        f"{n['company']}, {k} reported {direction} reorders than last quarter, the rest flat or "
        "the other way."
    )


def relay(atom, n, day, genre):
    d = atom.detail
    up = atom.favorable
    k = d["count"] if up else d["sample"] - d["count"]
    direction = "higher" if up else "lower"
    phrase = rounded(k / d["sample"])
    when = f"{day:%B %-d}"
    if genre == 0:
        return document(
            "news brief",
            n["outlets"][0],
            day + timedelta(days=1),
            f"{n['short']} resellers weigh in",
            f"Reorders at {n['company']} resellers are {'rising' if up else 'falling'}, according "
            f"to a survey of {d['sample']} resellers published on {when}: {k} reported "
            f"{direction} reorders than last quarter.",
        )
    if genre == 1:
        return document(
            "newsletter",
            n["newsletter"],
            day + timedelta(days=2),
            "What we're reading",
            f"Channel chatter on {n['company']} is {'upbeat' if up else 'downbeat'}: roughly "
            f"{phrase} of the {d['sample']} resellers in a survey published {when} said reorders "
            f"were {'up' if up else 'down'}.",
        )
    if genre == 2:
        return document(
            "forum post",
            n["forum"],
            day + timedelta(days=3),
            f"{n['short']} reseller survey",
            f"Anyone else see the reseller survey on {n['company']} from {when}? {k}/"
            f"{d['sample']} reporting {direction} reorders.",
        )
    return document(
        "podcast summary",
        n["podcast"],
        day + timedelta(days=4),
        "Episode notes",
        f"The hosts discussed a survey from {when} of {d['sample']} {n['company']} resellers in "
        f"which roughly {phrase} reported {direction} reorders than last quarter.",
    )


def shared_slots(world, n):
    """The analyst's survey note, its relays, or independent firms' surveys."""
    first = world.atoms[0]
    start = n["start"]
    slots = {
        0: document(
            "analyst note",
            n["analysts"][0],
            start,
            f"{n['short']}: reseller survey",
            own_check(first, n, start) + " We surveyed resellers directly over two weeks.",
        )
    }
    if world.presentation == "relayed":
        for slot, genre in enumerate(n["relay_genres"][: world.mentions[first.atom_id] - 1], 1):
            slots[slot] = relay(first, n, start, genre)
    elif world.presentation == "independent":
        for i, atom in enumerate(world.atoms[1:], 1):
            day = start + timedelta(days=2 * i)
            slots[i] = document(
                "analyst note",
                n["analysts"][i],
                day,
                f"{n['short']}: our reseller survey",
                own_check(atom, n, day) + " The survey was designed and fielded by our own team.",
            )
    return slots


def render(world: World):
    n = names(world.pair_seed, world.family)
    slots = (disclosure_slots if world.family == "disclosure" else shared_slots)(world, n)
    docs = []
    for slot in range(DOCUMENTS):
        if slot in slots:
            docs.append(slots[slot])
        else:
            # Distractors are fixed per slot, so matched dossiers differ only in manipulated slots.
            text = n["distractors"][slot].format(rival=n["rival"], other=n["other"])
            day = n["start"] + timedelta(days=n["offsets"][slot] - 4)
            docs.append(document("news brief", n["outlets"][slot % 6], day, "Sector roundup", text))
    ordered = [docs[i] for i in n["order"]]
    for i, doc in enumerate(ordered, 1):
        doc["doc_id"] = f"D{i}"
    return {
        "schema_version": "epistemics.research-dossier.v2",
        "case": brief(world, n),
        "documents": [{"doc_id": d.pop("doc_id"), **d} for d in ordered],
    }


def structure_note(world: World):
    """The explicit arm's statement of provenance or disclosure, generated from the ledger."""
    if world.presentation == "full":
        return (
            f"The letter reports all {WORDS[len(world.atoms)]} KPIs the company has always covered."
        )
    if world.presentation == "selected":
        missing = ", ".join(world.atom(i).name for i in world.implied)
        return (
            f"The letter omits KPIs the company has always covered ({missing}); under the "
            "background facts, omitted KPIs missed guidance."
        )
    if world.presentation == "silent_control":
        return "The letter reports every KPI the company has ever covered; nothing is omitted."
    n = names(world.pair_seed, world.family)
    if world.presentation == "single":
        return (
            f"Only {n['analysts'][0]}'s note reports a reseller survey; the rest is unrelated news."
        )
    if world.presentation == "relayed":
        return (
            f"The news, newsletter, forum or podcast items about a reseller survey all repeat "
            f"{n['analysts'][0]}'s single survey; they are not separate surveys."
        )
    return "Three research firms each report their own separate reseller survey."


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
