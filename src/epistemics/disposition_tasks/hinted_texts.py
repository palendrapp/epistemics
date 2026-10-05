"""Hinted-structure dossiers (tasks 0.45; docs/passport-adapter-design.md, "Redesign").

Held-out cases where the structure must be inferred, as in the dossiers where the passport's
neglect was measured: the unprompted dossier design (dispositions.design), with the evident
modules' new companies and outlets and the second paraphrase set of source descriptions
(cues-b, from a research desk that visits factories to a one-person blog that posts within
minutes of larger outlets). Nothing in a case states the mechanism, except in the reference arm,
which puts the structure fully to the configuration: the case brief states the mechanism (as the
full-mechanism dossiers do) and the instructions carry the generic full-dose guidance. The
reference arm's answers are the configuration's own considered answers, the target the other
arms are scored against.
"""

from epistemics.disposition_tasks import render as base
from epistemics.disposition_tasks.dossier import (
    BACKGROUND_RELAY,
    DATES,
    KPIS,
    arrange,
    distractors,
    document,
)
from epistemics.disposition_tasks.evident_texts import COMPANIES, OUTLETS_A, OUTLETS_B

SET = "cues-b"
REFERENCE = "reference"


def _call(report):
    return "high" if report > 0 else "low"


def relay(items, i, cover, variant):
    slot, kind = int(items["slot"][i]), items["kind"][i]
    subject, a, b = COMPANIES[i], OUTLETS_A[i], OUTLETS_B[i]
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
        + " ".join(records)
        + (f" Background: {BACKGROUND_RELAY}" if variant == REFERENCE else ""),
    )
    call_a = _call(items["report_a"][i])
    documents = [
        document(
            "Markets story",
            a,
            DATES[i % 3],
            f"Demand at {subject} is {call_a} this quarter, on our reading of the market.",
        )
    ]
    if kind != "single":
        call_b = _call(items["report_b"][i])
        story = f"Headline only (full story behind a paywall): “{subject}: demand {call_b} this quarter”."
        if slot >= 0:
            story = f"About {b}: {base.cue_sentence('corroboration', SET, slot, b)}\n{story}"
        documents.append(document("Markets story", b, DATES[3 + i % 3], story))
    lines = arrange(300 + i, brief, [*documents, *distractors(300 + i)])
    return lines, f"What is the probability that {base.own(subject)} demand is high?"


def disclosure(items, i, cover, variant):
    slot = int(items["slot"][i])
    subject = COMPANIES[i]
    m, j = (int(items[f][i]) for f in ("shared_good", "shared_bad"))
    good, bad = base.percent(items["good"][i]), base.percent(1 - items["good"][i])
    rate = base.percent(items["omission"][i])
    order = KPIS[i % 4 :] + KPIS[: i % 4]
    if variant == REFERENCE:
        omission = (
            "Background: some companies share every on-target indicator and withhold every "
            "off-target one. Others leave indicators out of their updates at random: each "
            f"indicator is left out with probability {rate}, whether or not it was on target."
        )
    else:
        omission = f"Across the sector, a given indicator is left out of a quarterly update {rate} of the time."
    brief = document(
        "Case brief",
        "Evaluator",
        "—",
        f"{base.own(subject)} quarterly demand is either high or low. Before its update, the "
        f"probability that demand is high is {base.percent(items['prior'][i])}. Reference rates: "
        f"{subject} tracks four indicators ({', '.join(x.lower() for x in order)}). When demand "
        f"is high, each independently lands on target with probability {good}; when demand is "
        f"low, with probability {bad}. {omission}",
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
    profile = (
        [document("Company profile", "Market Directory", "—", base.cue_sentence("disclosure", SET, slot, subject))]
        if slot >= 0
        else []
    )  # fmt: skip
    lines = arrange(400 + i, brief, [letter, *profile, *distractors(400 + i)])
    return lines, f"What is the probability that {base.own(subject)} demand is high?"


def trial(items, i, cover, variant):
    if "report_a" in items:
        return relay(items, i, cover, variant)
    return disclosure(items, i, cover, variant)
