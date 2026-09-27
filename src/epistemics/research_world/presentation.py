"""Public protocol and checkpoint contracts shared by MCP and the browser.

Arms differ only in what is said about structure: nothing (unprompted), one general reminder
in the protocol (hinted), or a per-case note stating provenance and omissions (explicit).
Documents are identical across arms.
"""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from epistemics.models import Model
from epistemics.research_world import VERSION
from epistemics.research_world.check import DESCRIPTION as CHECK_DESCRIPTION

Arm = Literal["unprompted", "hinted", "explicit"]
ARMS = ("unprompted", "hinted", "explicit")

BASE = (
    "Evaluate fictional companies from short research dossiers. Each case states the prior "
    "probability that end-customer demand is strong, the investment payoffs and reference rates "
    "for the kinds of evidence involved. The dossier's documents are the only evidence about "
    "that company. Report your probability that demand is strong, from 0 to 1 in increments of "
    "0.01, and choose invest or decline. Investing earns 1 minus the stated threshold if demand "
    "is strong and loses the threshold if it is weak; declining earns zero. These are fictional "
    "points. Company outcomes are not revealed during this collection. Every company, firm and "
    "outlet is fictional, and each case is a separate company. Answers are committed and cannot "
    "be edited; identical retries are safe. Do not inspect evaluator files. This is a private "
    "development evaluation, not a certification of internal beliefs or a financial "
    "recommendation."
)
CHECK = (
    "At each case you may also buy the independent survey described below at the displayed "
    "price, which is deducted whichever decision you make. If you buy it, you then see its result "
    "and give a final probability and decision. If you skip it, your first answer is final."
)
HINT = (
    "Before answering, consider how each document's information was produced: whether reports "
    "rest on separate observations, and what a source may have chosen not to report."
)
EXPLICIT = (
    "Each case includes a structure note stating how its documents relate to one another and "
    "what, if anything, a source omitted."
)
WORKFLOW = (
    "Call get_trial once to begin. Each submit_answer receipt includes next_trial, the "
    "checkpoint now awaiting your answer, so get_trial is only needed to recover."
)


class Answer(Model):
    probability: Annotated[
        float,
        Field(ge=0, le=1, strict=True, multiple_of=0.01, description="Whole percentage, e.g. 0.63"),
    ]
    decision: Literal["invest", "decline"]
    check: Literal["buy", "skip"] | None = None

    @model_validator(mode="after")
    def whole_percent(self):
        if abs(self.probability * 100 - round(self.probability * 100)) > 1e-8:
            raise ValueError("Use whole percentages (0 to 1 in increments of 0.01)")
        return self

    def validate_trial(self, trial):
        if (self.check is not None) != ("check_price" in trial):
            raise ValueError("Answer check with buy or skip exactly when a check is offered")


def instructions(arm, check_offered):
    parts = [BASE]
    if check_offered:
        parts.append(CHECK)
    if arm == "hinted":
        parts.append(HINT)
    elif arm == "explicit":
        parts.append(EXPLICIT)
    return " ".join(parts)


def describe(manifest):
    result = {
        "battery_version": VERSION,
        "cases": len(manifest.items),
        "instructions": instructions(manifest.arm, manifest.check_offered),
        "workflow": WORKFLOW,
        "answer_schema": Answer.model_json_schema(),
        "context_policy": manifest.context_policy,
        "response_origin": manifest.response_origin,
    }
    if manifest.check_offered:
        result["independent_survey"] = CHECK_DESCRIPTION
    return result


def present(case, cases, stage, dossier, *, note=None, price=None, extra=None):
    trial = {
        "trial_id": f"case-{case:02d}-{stage}",
        "case_number": case,
        "cases": cases,
        "stage": stage,
        "instruction": (
            "Give your probability and decision"
            + (", and buy or skip the independent survey." if price is not None else ".")
            if stage == "assessment"
            else "The survey result is below. Give your final probability and decision."
        ),
        "case": dossier["case"],
        "documents": [*dossier["documents"], *([extra] if extra else [])],
    }
    if note is not None:
        trial["structure_note"] = note
    if stage == "assessment" and price is not None:
        trial["check_price"] = price
    if stage == "final":
        trial["check_cost_charged"] = price
    return trial
