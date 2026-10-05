"""Evident-structure dossiers (tasks 0.44; dispositions.evident): held-out cases for the passport
adapter. The layout is that of the unprompted dossiers (a case brief, the reports or the
company's update, and two distractors), with new companies and outlets. No document states that
sources repeat one another or that companies withhold selectively as a general rule; the
evidence about this case's source is in its own documents.
"""

from epistemics.disposition_tasks import render as base
from epistemics.disposition_tasks.dossier import DATES, KPIS, arrange, distractors, document
from epistemics.dispositions import evident

_PREFIXES = [
    "Brackenridge", "Dunmore", "Easterly", "Fenwick", "Gallowmere", "Hawthorn Ridge", "Inverley",
    "Jasperton", "Kilburn", "Lowmoor", "Mistral", "Norwood", "Ormsby", "Penrose", "Quillon",
    "Rosedale", "Sherwin", "Tarrant", "Ulverly", "Vantage Row", "Whitby", "Exmoor", "Yewbank",
    "Zennor",
]  # fmt: skip
_TRADES = ["Apparel", "Ceramics", "Logistics", "Dairy", "Hardware", "Pharma", "Paper", "Audio"]
COMPANIES = [f"{p} {_TRADES[i % len(_TRADES)]}" for i, p in enumerate(_PREFIXES)]
OUTLETS_A = [
    "Granary Ledger", "Mainsail Wire", "Quayside Daily", "Lodestar Post", "Harrowgate Dispatch",
    "Signal Review", "Wharf Street Journal", "Compass Markets", "Anvil Bulletin", "Estuary Times",
    "Bellwether Herald", "Prism Digest", "Cinder Gazette", "Ironside Report", "Fernhill Chronicle",
    "Topsail Brief", "Marigold Monitor", "Lockgate Observer", "Vane Street News",
    "Saffron Courier", "Slate Weekly", "Moorland Record", "Kiln Tribune", "Saltgrass Sentinel",
]  # fmt: skip
OUTLETS_B = [
    "Tallow Wire", "Ember Business", "Copse Street Daily", "Gatehouse Ledger", "Halyard Post",
    "Quill Dispatch", "Rook Review", "Cairn Journal", "Weir Markets", "Spindle Bulletin",
    "Fathom Times", "Larkhill Herald", "Brindle Digest", "Cormorant Gazette", "Sextant Report",
    "Hearth Chronicle", "Pennant Brief", "Thatch Monitor", "Bramble Observer",
    "Lamplight Row News", "Shingle Courier", "Heron Weekly", "Ochre Record", "Burrow Tribune",
]  # fmt: skip


def _call(report):
    return "high" if report > 0 else "low"


def relay(items, i, cover, variant):
    k = int(items["item"][i])
    subject, a, b = COMPANIES[k], OUTLETS_A[k], OUTLETS_B[k]
    style, kind = str(items["style"][i]), str(items["kind"][i])
    records = [
        f"{base.own(a)} demand calls are correct {base.percent(items['accuracy_a'][i])} of the time."
    ]
    if kind != "single":
        records.append(
            f"{base.own(b)} demand calls are correct {base.percent(items['accuracy_b'][i])} of "
            "the time."
        )
    brief = document(
        "Case brief",
        "Evaluator",
        "—",
        f"{base.own(subject)} quarterly demand is either high or low. Before any reports, the "
        f"probability that demand is high is {base.percent(items['prior'][i])}. Track records: "
        + " ".join(records),
    )
    call_a = _call(items["report_a"][i])
    documents = [
        document(
            "Markets story",
            a,
            DATES[k % 3],
            f"Demand at {subject} is {call_a} this quarter, on our reading of the market.",
        )
    ]
    if kind != "single":
        call_b = _call(items["report_b"][i])
        if style == "attribution":
            story = f"According to {a}, demand at {subject} is {call_b} this quarter."
        elif style == "profile":
            story = (
                f"About {b}: {b} has no reporters of its own; it republishes other outlets' market "
                f"calls, usually within minutes.\nHeadline: “{subject}: demand {call_b} this "
                "quarter”."
            )
        elif style == "survey":
            n = 30 + 5 * (k % 4)
            moved = n - 6 - k % 5
            direction = "rising" if call_b == "high" else "falling"
            story = (
                f"Our survey of {n} of {base.own(subject)} retailers this month found {moved} "
                f"reporting {direction} orders. On our reading, demand at {subject} is {call_b} "
                "this quarter."
            )
        else:  # conflict: a second, differing call
            story = (
                f"On our own reading of the market, demand at {subject} is {call_b} this quarter."
            )
        documents.append(document("Markets story", b, DATES[3 + k % 3], story))
    lines = arrange(100 + k, brief, [*documents, *distractors(100 + k)])
    return lines, f"What is the probability that {base.own(subject)} demand is high?"


def disclosure(items, i, cover, variant):
    k = int(items["item"][i])
    subject = COMPANIES[k]
    style = str(items["style"][i])
    m, j = int(items["shared_good"][i]), int(items["shared_bad"][i])
    good, bad = base.percent(items["good"][i]), base.percent(1 - items["good"][i])
    order = KPIS[k % 4 :] + KPIS[: k % 4]
    brief = document(
        "Case brief",
        "Evaluator",
        "—",
        f"{base.own(subject)} quarterly demand is either high or low. Before its update, the "
        f"probability that demand is high is {base.percent(items['prior'][i])}. Reference rates: "
        f"{subject} tracks four indicators ({', '.join(x.lower() for x in order)}). When demand "
        f"is high, each independently lands on target with probability {good}; when demand is "
        f"low, with probability {bad}. Across the sector, a given indicator is left out of a "
        f"quarterly update {base.percent(items['omission'][i])} of the time.",
    )
    reported = [f"{name} came in on target." for name in order[:m]]
    reported += [f"{name} came in below target." for name in order[m : m + j]]
    letter = document(
        "Letter to shareholders",
        subject,
        DATES[k % 6],
        f"Quarterly update. {' '.join(reported)} We thank our customers and staff for their work.",
    )
    if style == "policy":
        evidence = document(
            "Investor FAQ",
            subject,
            "—",
            "Why do some indicators not appear in your quarterly update? Our quarterly updates "
            "report only the indicators that met their targets.",
        )
    elif style == "history":
        evidence = document(
            "Company profile",
            "Market Directory",
            "—",
            f"In each of {base.own(subject)} last twelve quarterly updates, every indicator it "
            "reported was on target, and every indicator it left out was later shown in its annual "
            "report to have been below target.",
        )
    elif style == "template":
        evidence = document(
            "Company profile",
            "Market Directory",
            "—",
            f"{base.own(subject)} quarterly updates follow an independent auditor's fixed template "
            "that lists every indicator. An indicator is left out only when its data arrive after "
            "the update is filed, which happens regardless of the result.",
        )
    else:  # complete: a neutral profile line, so every dossier has the same number of documents
        evidence = document(
            "Company profile",
            "Market Directory",
            "—",
            f"{subject} is a mid-sized company that sells mainly to retailers.",
        )
    lines = arrange(200 + k, brief, [letter, evidence, *distractors(200 + k)])
    return lines, f"What is the probability that {base.own(subject)} demand is high?"


def trial(items, i, cover, variant):
    if "report_a" in items:
        return relay(items, i, cover, variant)
    return disclosure(items, i, cover, variant)


def stated(items, i):
    return [f"{round(float(items['prior'][i]) * 100)}%"]


# The design's evident modules, for the registry of renderers.
MODULES = evident.MODULES
