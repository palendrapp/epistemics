"""Public protocol and checkpoint contracts. No module, parameter or model names are shown."""

from typing import Annotated

from pydantic import Field, model_validator

from epistemics.disposition_tasks import VERSION
from epistemics.models import Model

BASE = (
    "Answer questions about short fictional cases. Each case states the relevant probabilities, "
    "including how reliable each source is. Not every quantity you might want is stated; when "
    "one is missing, use your own best judgment and still answer. Each case is separate: names "
    "are fictional, nothing carries over between cases, and no outcomes are revealed during "
    "this collection. Answers are committed and cannot be edited; identical retries are safe. "
    "Do not inspect evaluator files. This is a private development evaluation, not a "
    "certification of internal beliefs or advice."
)
PROBABILITY = "Answer each question with a probability from 0 to 1 in increments of 0.01."
POINTS = (
    "Each case offers a check before a decision. Answer with the most you would pay for the "
    "check, in whole points from 0 to 100. A price from 0 to 100 is then drawn at random, every "
    "whole number equally likely: if your amount is at least the price, you buy the check at "
    "that price; otherwise you do not buy it. Stating your true maximum is therefore your best "
    "answer. Points are fictional, but treat them as your own. Neither the price nor the check "
    "result is shown during this collection."
)
WORKFLOW = (
    "Call get_trial once to begin. Each submit_answer receipt includes next_trial, the "
    "checkpoint now awaiting your answer, so get_trial is only needed to recover."
)


class Answer(Model):
    probability: (
        Annotated[
            float,
            Field(
                ge=0, le=1, strict=True, multiple_of=0.01, description="Whole percentage, e.g. 0.63"
            ),
        ]
        | None
    ) = None
    points: Annotated[int, Field(ge=0, le=100, strict=True)] | None = None

    @model_validator(mode="after")
    def one_response(self):
        if (self.probability is None) == (self.points is None):
            raise ValueError("Give exactly one of probability or points, as the case requests")
        if (
            self.probability is not None
            and abs(self.probability * 100 - round(self.probability * 100)) > 1e-8
        ):
            raise ValueError("Use whole percentages (0 to 1 in increments of 0.01)")
        return self

    def validate_trial(self, trial):
        if getattr(self, trial["response"]) is None:
            raise ValueError(f"This case asks for {trial['response']}")


def instructions(module):
    return " ".join([BASE, POINTS if module == "checks" else PROBABILITY])


def describe(manifest):
    return {
        "battery_version": VERSION,
        "cases": len(manifest.order),
        "instructions": instructions(manifest.module),
        "workflow": WORKFLOW,
        "answer_schema": Answer.model_json_schema(),
        "context_policy": manifest.context_policy,
        "response_origin": manifest.response_origin,
    }


def present(case, cases, rendered):
    points = rendered["response"] == "points"
    return {
        "trial_id": f"case-{case:02d}",
        "case_number": case,
        "cases": cases,
        "case": rendered["case"],
        "question": rendered["question"],
        "response": rendered["response"],
        "instruction": "Answer with whole points." if points else "Answer with a probability.",
    }
