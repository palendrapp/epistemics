"""Public protocol and checkpoint contracts. No module, parameter or model names are shown."""

from typing import Annotated

from pydantic import Field, model_validator

from epistemics.disposition_tasks import VERSION
from epistemics.models import Model

INTRO = (
    "Answer questions about short fictional cases. Each case states the relevant probabilities, "
    "including how reliable each source is. Not every quantity you might want is stated; when "
    "one is missing, use your own best judgment and still answer."
)
SEPARATE = (
    "Each case is separate: names are fictional, nothing carries over between cases, and no "
    "outcomes are revealed during this collection."
)
# Learning variants: cases share one population, and each case's structure is revealed later.
SHARED = {
    ("corroboration", "markets"): (
        "Each case concerns a different fictional company, but all the outlets in this "
        "collection come from the same population. After you answer a case, the next checkpoint "
        "reveals whether that case's second outlet had relayed the first outlet's call. Demand "
        "outcomes are not revealed."
    ),
    ("corroboration", "ecology"): (
        "Each case concerns a different fictional lake, but all the stations in this collection "
        "come from the same network. After you answer a case, the next checkpoint reveals "
        "whether that case's second station had forwarded the first station's report. "
        "Fish-stock outcomes are not revealed."
    ),
    ("disclosure", "markets"): (
        "Each case concerns a different fictional company, but all the companies in this "
        "collection come from the same market. After you answer a case, the next checkpoint "
        "reveals how that company reports its indicators. Demand outcomes are not revealed."
    ),
    ("disclosure", "ecology"): (
        "Each case concerns a different fictional lake, but all the contractors in this "
        "collection come from the same industry. After you answer a case, the next checkpoint "
        "reveals how that contractor reports its markers. Fish-stock outcomes are not revealed."
    ),
}
RULES = (
    "Answers are committed and cannot be edited; identical retries are safe. Do not inspect "
    "evaluator files. This is a private development evaluation, not a certification of internal "
    "beliefs or advice."
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
    # Tasks 0.24: one of the options a choice case lists, copied exactly.
    choice: Annotated[str, Field(min_length=1, max_length=300)] | None = None

    @model_validator(mode="after")
    def one_response(self):
        given = [v is not None for v in (self.probability, self.points, self.choice)]
        if sum(given) != 1:
            raise ValueError(
                "Give exactly one of probability, points or choice, as the case requests"
            )
        if (
            self.probability is not None
            and abs(self.probability * 100 - round(self.probability * 100)) > 1e-8
        ):
            raise ValueError("Use whole percentages (0 to 1 in increments of 0.01)")
        return self

    def validate_trial(self, trial):
        if getattr(self, trial["response"]) is None:
            raise ValueError(f"This case asks for {trial['response']}")
        if trial["response"] == "choice" and self.choice not in trial["options"]:
            raise ValueError("Choose one of the listed options, copied exactly")


# Batteries v3 and v3.1 (tasks 0.24): the general instructions match their trials. (The v3 pilot
# ran with the probability-only instructions above, which conflicted with its points trials,
# with its unknown accuracies, and in the loaded variant with its references to earlier cases.)
INTRO_V3 = (
    "Answer questions about short fictional cases. Each case states what is known about its "
    "evidence. Some quantities, such as a source's accuracy, are unknown by design; when one is, "
    "use your own best judgment and still answer."
)
LOADED_V3 = (
    "Names are fictional and no outcomes are revealed during this collection. Some cases refer "
    "back to a case shown earlier in this session and do not show its evidence again."
)
RESPONSE_V3 = (
    "Some cases ask for a probability (from 0 to 1 in increments of 0.01) and some for a number "
    "of points (a whole number from 0 to 100); each case says which. Points are fictional, but "
    "treat them as your own."
)
# Open-inference screen (tasks 0.26): neutral about whether answers have a key.
INTRO_SCREEN = (
    "Answer questions about short fictional cases. Cases give limited information; answer each "
    "question with your best judgement of the probability."
)
# Central-bank statements (tasks 0.30): sequences of cases about one statement continue each other.
INTRO_STATEMENTS = (
    "Answer questions about policy statements from a central bank's policy committee. The central "
    "bank is not named, and the statements were written for this collection in the style of real "
    "ones. In each case a colleague compares a new statement with the committee's previous one "
    "and reports the changes, either one per case or all at once. Cases about the same statement "
    "are consecutive, and a later case continues the earlier ones: answer using the previous "
    "statement, the market pricing and every change reported so far for that statement. "
    "Different statements are separate, and no outcomes are revealed during this collection."
)
INTRO_STATEMENT_PROBE = (
    "Each case shows two consecutive policy statements from a central bank's policy committee; "
    "the central bank is not named. Judge from the wording when statements like these would most "
    "plausibly have been written. Cases are separate, and no answers are revealed during this "
    "collection."
)
# Deliberation style (tasks 0.32): anchor pairs refer to the comparison just made.
INTRO_ANCHOR = (
    "Answer questions about short fictional cases. Cases give limited information; answer with "
    "your best judgement. Some cases first ask you to compare a probability with a given number; "
    "the next case then asks for that probability. Numbers given for comparison were chosen for "
    "this exercise and carry no information about the case. Names are fictional, and no outcomes "
    "are revealed during this collection."
)
INTRO_FRAMES = (
    "Answer questions about short fictional cases. Cases give limited information; answer with "
    "your best judgement. Some cases first ask a question about a case; the next case then asks "
    "for a probability about the same case. Any number given for comparison was chosen for this "
    "exercise and carries no information about the case. Names are fictional, and no outcomes "
    "are revealed during this collection."
)
INTRO_ANNOUNCED = (
    "Answer questions about policy statements from a central bank's policy committee. The central "
    "bank is not named, and the statements were written for this collection in the style of real "
    "ones. In each case a colleague compares a new statement with the committee's previous one "
    "and reports a change. Each case is separate: nothing carries over between cases, and no "
    "outcomes are revealed during this collection."
)
INTRO_CORRELATED = (
    "Answer questions about policy statements from a central bank's policy committee. The central "
    "bank is not named, and the statements were written for this collection in the style of real "
    "ones. In each case a colleague compares a new statement with the committee's previous one "
    "and reports its changes. Some cases continue the one before: they report the same "
    "statement's changes so far. Different statements are separate, and no outcomes are "
    "revealed during this collection."
)
INTRO_CALLS = (
    "Answer questions about short fictional cases about urns and the calls analysts make on them. "
    "Each case states what is known; when something you might want is not stated, use your own "
    "best judgment and still answer. Some cases continue the one before: they report the same "
    "urn's calls so far. Different urns are separate, and no outcomes are revealed during this "
    "collection."
)
INTRO_WORDING = {
    "urn": "about urns and the calls analysts make on them",
    "policy": "about central banks and the notes economists write on them",
    "report": "about batches of goods and the reports inspectors write on them",
}
WORDING_CONTEXT = (
    "Each case states what is known; when something you might want is not stated, use your own "
    "best judgment and still answer. Every case is separate, and no outcomes are revealed during "
    "this collection."
)
FOLLOWUP_CONTEXT = (
    "Names are fictional, and no outcomes are revealed during this collection. Some cases first "
    "ask whether something is likely or unlikely; the next case then asks for its probability, "
    "about the same case. Other cases are separate."
)
RESPONSE_CHOICE = (
    "Some cases ask for a probability (from 0 to 1 in increments of 0.01) and some ask you to "
    "choose one of two listed options; each case says which. For a choice, answer with one of "
    "the options exactly as written."
)
RESPONSE_V31 = (
    "Some cases ask for a probability (from 0 to 1 in increments of 0.01) and some ask you to "
    "choose one of two listed actions; each case says which. For a choice, answer with one of "
    "the options exactly as written."
)


def instructions(module, variant="paired", cover="markets"):
    if module.startswith("coherence-"):
        context = LOADED_V3 if variant == "v3-loaded" else SEPARATE
        return " ".join([INTRO_V3, context, RULES, RESPONSE_V3])
    if module.startswith("calls-"):
        return " ".join([INTRO_CALLS, RULES, PROBABILITY])
    if module.startswith("wording-"):
        family = module.split("-")[1]
        intro = f"Answer questions about short fictional cases {INTRO_WORDING[family]}."
        return " ".join([intro, WORDING_CONTEXT, RULES, PROBABILITY])
    if module.startswith("correlated-"):
        return " ".join([INTRO_CORRELATED, RULES, PROBABILITY])
    if module.startswith("announced-"):
        return " ".join([INTRO_ANNOUNCED, RULES, PROBABILITY])
    if module.startswith("followup-"):
        return " ".join([INTRO, FOLLOWUP_CONTEXT, RULES, RESPONSE_CHOICE])
    if module.startswith("deliberation-frames-"):
        return " ".join([INTRO_FRAMES, RULES, RESPONSE_CHOICE])
    if module.startswith("deliberation-anchor-"):
        return " ".join([INTRO_ANCHOR, RULES, RESPONSE_CHOICE])
    if module.startswith("deliberation-"):
        return " ".join([INTRO_SCREEN, SEPARATE, RULES, PROBABILITY])
    if module.startswith("statement-probe-"):
        return " ".join([INTRO_STATEMENT_PROBE, RULES, PROBABILITY])
    if module.startswith("statement-"):
        return " ".join([INTRO_STATEMENTS, RULES, PROBABILITY])
    if module.startswith(("screen-", "cohere-")):
        return " ".join([INTRO_SCREEN, SEPARATE, RULES, PROBABILITY])
    if module.startswith(("decision-", "decision2-")):
        return " ".join([INTRO_V3, SEPARATE, RULES, RESPONSE_V31])
    context = SHARED[(module, cover)] if variant.startswith("learning") else SEPARATE
    return " ".join([INTRO, context, RULES, POINTS if module == "checks" else PROBABILITY])


def describe(manifest):
    return {
        "battery_version": VERSION,
        "cases": len(manifest.order),
        "instructions": instructions(manifest.module, manifest.variant, manifest.cover),
        "workflow": WORKFLOW,
        "answer_schema": Answer.model_json_schema(),
        "context_policy": manifest.context_policy,
        "response_origin": manifest.response_origin,
    }


def present(case, cases, rendered, previous=None):
    instruction = {
        "points": "Answer with whole points.",
        "probability": "Answer with a probability.",
        "choice": "Answer with one of the options, copied exactly.",
    }[rendered["response"]]
    trial = {
        "trial_id": f"case-{case:02d}",
        "case_number": case,
        "cases": cases,
        "case": rendered["case"],
        "question": rendered["question"],
        "response": rendered["response"],
        "instruction": instruction,
    }
    if rendered["response"] == "choice":
        trial["options"] = rendered["options"]
    if previous is not None:
        trial["previous_case"] = previous
    return trial
