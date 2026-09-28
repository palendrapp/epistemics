"""Realistic document dossiers for the description modules (transfer test).

Each dossier renders one item of the relay or disclosure description design as a small bundle:
a case brief with the prior, reference rates and the general mechanism, then the evidence as a
news story, analyst note or shareholder letter, the source description as a masthead or company
profile line, and two distractors about other companies, in a fixed shuffled order. The items,
numbers and questions are those of the formal modules, so the same per-description fit applies.
"""

import random

from epistemics.disposition_tasks import render as base

KPIS = ["Same-store sales", "Gross margin", "New accounts", "Inventory turns"]
DATES = ["3 March", "5 March", "8 March", "10 March", "12 March", "15 March"]
DISTRACTORS = [
    (
        "Sector brief",
        "Industry Wire",
        "Freight rates across consumer goods eased for a second month.",
    ),
    (
        "Company news",
        "Market Ledger",
        "{other} named a new chief financial officer effective next quarter.",
    ),
    (
        "Calendar",
        "Investor Diary",
        "{other} will hold its annual meeting next month; no contested votes are expected.",
    ),
    (
        "Sector brief",
        "Trade Monitor",
        "Analysts expect sector-wide inventories to normalise by year end.",
    ),
    (
        "Company news",
        "Business Daily",
        "{other} opened a second distribution centre in the north of the country.",
    ),
    (
        "Market note",
        "Exchange Notes",
        "Trading volumes in consumer names were close to their five-year average.",
    ),
    (
        "Company news",
        "Regional Post",
        "{other} settled a long-running lease dispute on undisclosed terms.",
    ),
    ("Sector brief", "Supply Chain Review", "Packaging costs were flat quarter on quarter."),
]
# Distractor companies never appear as case subjects.
OTHERS = [
    "Aster Holdings",
    "Bellmore Group",
    "Calder Brands",
    "Dorrit Supply",
    "Elsmere Foods",
    "Fairlow Packaging",
    "Greyling Retail",
    "Hartwell Components",
]
BACKGROUND_RELAY = (
    "Some outlets relay another outlet's call instead of checking for themselves; a relayed call "
    "simply repeats the original call."
)


def document(kind, source, date, body):
    return f"**{kind} · {source} · {date}**\n{body}"


def distractors(i):
    rng = random.Random(1000 + i)
    chosen = rng.sample(DISTRACTORS, 2)
    return [
        document(kind, source, rng.choice(DATES), text.format(other=rng.choice(OTHERS)))
        for kind, source, text in chosen
    ]


def arrange(i, brief, documents):
    """Brief first, then the documents in a fixed order shuffled by item."""
    documents = list(documents)
    random.Random(i).shuffle(documents)
    return [brief, *documents]


def _call(report):
    return "high" if report > 0 else "low"


def relay(items, i, cover, variant):
    slot, kind = int(items["slot"][i]), items["kind"][i]
    subject, a, b = base.COMPANIES[i], base.OUTLETS_A[i], base.OUTLETS_B[i]
    set_name = "cues-" + variant[-1]
    if kind == "rate":
        brief = document(
            "Case brief",
            "Evaluator",
            "—",
            f"This case concerns the news outlet {b}. Background: {BACKGROUND_RELAY}",
        )
        profile = document(
            "About us",
            b,
            "—",
            f"{b} covers companies' demand. "
            + base.cue_sentence("corroboration", set_name, slot, b),
        )
        lines = arrange(i, brief, [profile, *distractors(i)])
        question = (
            f"Among outlets like {b}, what proportion relay another outlet's call instead of "
            "checking for themselves?"
        )
        return lines, question
    rates = [
        f"{base.own(a)} demand calls are correct {base.percent(items['accuracy_a'][i])} of the time."
    ]
    background = ""
    if kind != "single":
        rates.append(
            f"When {b} checks for itself, its calls are correct "
            f"{base.percent(items['accuracy_b'][i])} of the time."
        )
        background = f" Background: {BACKGROUND_RELAY}"
        cue = base.cue_name(items["cue"][i])
        if cue != "none":
            relay_rate, own_rate = base.CUE_WORDS[cue.split("_")[0]]
            background += (
                f" Relayed stories reuse the original story's wording {relay_rate}; stories by "
                f"outlets that checked for themselves match another outlet's wording {own_rate}."
            )
    brief = document(
        "Case brief",
        "Evaluator",
        "—",
        f"{base.own(subject)} quarterly demand is either high or low. Before any reports, the "
        f"probability that demand is high is {base.percent(items['prior'][i])}. Reference rates: "
        + " ".join(rates)
        + background,
    )
    call_a = _call(items["report_a"][i])
    original = f"Demand at {subject} is {call_a} this quarter, on our reading of the market."
    documents = [document("Markets story", a, DATES[i % 3], original)]
    if kind != "single":
        call_b = _call(items["report_b"][i])
        cue = base.cue_name(items["cue"][i])
        if cue == "none":
            story = (
                f"Headline only (full story behind a paywall): “{subject}: demand {call_b} this "
                "quarter”."
            )
        elif cue.endswith("identical"):
            story = f"Demand at {subject} is {call_b} this quarter, on our reading of the market."
        else:
            story = f"{subject} is seeing {'strong' if call_b == 'high' else 'weak'} demand in the current quarter."
        if slot >= 0:
            about = base.cue_sentence("corroboration", set_name, slot, b)
            story = f"About {b}: {about}\n{story}"
        documents.append(document("Markets story", b, DATES[3 + i % 3], story))
    lines = arrange(i, brief, [*documents, *distractors(i)])
    if kind == "probe":
        question = f"What is the probability that {b} relayed {base.own(a)} call rather than checking for itself?"
    else:
        question = f"What is the probability that {base.own(subject)} demand is high?"
    return lines, question


def disclosure(items, i, cover, variant):
    slot, kind = int(items["slot"][i]), items["kind"][i]
    subject = base.COMPANIES[i]
    set_name = "cues-" + variant[-1]
    rate = base.percent(items["omission"][i])
    mechanism = (
        "Background: some companies share every on-target indicator and withhold every off-target "
        "one. Others leave indicators out of their updates at random: each indicator is left out "
        f"with probability {rate}, whether or not it was on target."
    )
    profile_text = base.cue_sentence("disclosure", set_name, slot, subject) if slot >= 0 else None
    profile = (
        [document("Company profile", "Market Directory", "—", profile_text)] if profile_text else []
    )
    if kind == "rate":
        brief = document(
            "Case brief",
            "Evaluator",
            "—",
            f"This case concerns {subject}, which tracks four operating indicators. {mechanism}",
        )
        lines = arrange(i, brief, [*profile, *distractors(i)])
        question = (
            f"Among companies like {subject}, what proportion share every on-target indicator "
            "and withhold every off-target one, rather than leaving indicators out at random?"
        )
        return lines, question
    m, j, k = (int(items[f][i]) for f in ("shared_good", "shared_bad", "withheld"))
    good, bad = base.percent(items["good"][i]), base.percent(1 - items["good"][i])
    order = KPIS[i % 4 :] + KPIS[: i % 4]
    brief = document(
        "Case brief",
        "Evaluator",
        "—",
        f"{base.own(subject)} quarterly demand is either high or low. Before its update, the "
        f"probability that demand is high is {base.percent(items['prior'][i])}. Reference rates: "
        f"{subject} tracks four indicators ({', '.join(k_.lower() for k_ in order)}). When demand "
        f"is high, each independently lands on target with probability {good}; when demand is "
        f"low, with probability {bad}. {mechanism}",
    )
    reported = [f"{name} came in on target." for name in order[:m]]
    reported += [f"{name} came in below target." for name in order[m : m + j]]
    letter_body = " ".join(reported) if reported else "The letter discusses strategy and hiring."
    letter = document(
        "Letter to shareholders",
        subject,
        DATES[i % 6],
        f"Quarterly update. {letter_body} We thank our customers and staff for their work.",
    )
    lines = arrange(i, brief, [letter, *profile, *distractors(i)])
    if kind == "probe":
        question = (
            f"What is the probability that {subject} is the kind of company that withholds "
            "every off-target indicator?"
        )
    else:
        question = f"What is the probability that {base.own(subject)} demand is high?"
    return lines, question


# Unprompted dossiers: the same documents without the mechanism. The brief states only the prior
# and each source's track record (and, for disclosure, how often indicators go unreported); no
# document says that outlets relay one another or that companies withhold selectively. Every second
# outlet's story is a paywalled headline, so wording carries no copying signal.
def relay_unprompted(items, i, cover, variant):
    slot, kind = int(items["slot"][i]), items["kind"][i]
    subject, a, b = base.COMPANIES[i], base.OUTLETS_A[i], base.OUTLETS_B[i]
    set_name = "cues-" + variant[-1]
    rates = [
        f"{base.own(a)} demand calls are correct {base.percent(items['accuracy_a'][i])} of the time."
    ]
    if kind != "single":
        rates.append(
            f"{base.own(b)} demand calls are correct {base.percent(items['accuracy_b'][i])} of "
            "the time."
        )
    brief = document(
        "Case brief",
        "Evaluator",
        "—",
        f"{base.own(subject)} quarterly demand is either high or low. Before any reports, the "
        f"probability that demand is high is {base.percent(items['prior'][i])}. Track records: "
        + " ".join(rates),
    )
    call_a = _call(items["report_a"][i])
    original = f"Demand at {subject} is {call_a} this quarter, on our reading of the market."
    documents = [document("Markets story", a, DATES[i % 3], original)]
    if kind != "single":
        call_b = _call(items["report_b"][i])
        story = f"Headline only (full story behind a paywall): “{subject}: demand {call_b} this quarter”."
        if slot >= 0:
            story = f"About {b}: {base.cue_sentence('corroboration', set_name, slot, b)}\n{story}"
        documents.append(document("Markets story", b, DATES[3 + i % 3], story))
    lines = arrange(i, brief, [*documents, *distractors(i)])
    return lines, f"What is the probability that {base.own(subject)} demand is high?"


def disclosure_unprompted(items, i, cover, variant):
    slot = int(items["slot"][i])
    subject = base.COMPANIES[i]
    set_name = "cues-" + variant[-1]
    m, j = (int(items[f][i]) for f in ("shared_good", "shared_bad"))
    good, bad = base.percent(items["good"][i]), base.percent(1 - items["good"][i])
    order = KPIS[i % 4 :] + KPIS[: i % 4]
    brief = document(
        "Case brief",
        "Evaluator",
        "—",
        f"{base.own(subject)} quarterly demand is either high or low. Before its update, the "
        f"probability that demand is high is {base.percent(items['prior'][i])}. Reference rates: "
        f"{subject} tracks four indicators ({', '.join(k_.lower() for k_ in order)}). When demand "
        f"is high, each independently lands on target with probability {good}; when demand is "
        f"low, with probability {bad}. Across the sector, a given indicator is left out of a "
        f"quarterly update {base.percent(items['omission'][i])} of the time.",
    )
    reported = [f"{name} came in on target." for name in order[:m]]
    reported += [f"{name} came in below target." for name in order[m : m + j]]
    letter_body = " ".join(reported) if reported else "The letter discusses strategy and hiring."
    letter = document(
        "Letter to shareholders",
        subject,
        DATES[i % 6],
        f"Quarterly update. {letter_body} We thank our customers and staff for their work.",
    )
    profile_text = base.cue_sentence("disclosure", set_name, slot, subject) if slot >= 0 else None
    profile = (
        [document("Company profile", "Market Directory", "—", profile_text)] if profile_text else []
    )
    lines = arrange(i, brief, [letter, *profile, *distractors(i)])
    return lines, f"What is the probability that {base.own(subject)} demand is high?"
