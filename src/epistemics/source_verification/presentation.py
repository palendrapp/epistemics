from typing import Literal

from pydantic import model_validator

from epistemics.models import Model
from epistemics.source_delivery.presentation import RESEARCH
from epistemics.source_delivery.presentation import present as original_present
from epistemics.source_learning.battery import INSTRUCTIONS, costs
from epistemics.source_learning.models import Probability
from epistemics.source_verification import VERSION

POLICIES = {"none": "stop", "always": "customer_panel"}


class Answer(Model):
    probability: Probability
    decision: Literal["invest", "decline"]

    @model_validator(mode="after")
    def whole_percent(self):
        if abs(self.probability * 100 - round(self.probability * 100)) > 1e-8:
            raise ValueError("Use whole percentages, 0 to 1 in increments of 0.01")
        return self


OLD = """The first twelve companies offer no research. For each of the next twelve, choose one paid check
or stop, then give a revised forecast and final decision. Audits also teach you about future use
of the source."""
NEW = """The first twelve companies offer no check. For each of the next twelve, give a provisional
forecast and decision. The assigned policy then supplies either one independent five-customer
sample or no extra evidence. Give a final forecast and decision in both cases. You do not choose
the check. Only the final decision earns the investment payoff; the assigned check cost is deducted
even if you decline. Source audits are unavailable. The same policy applies to all twelve later
companies and is declared before collection. A final checkpoint still follows when no check is
assigned; you may confirm or revise your answer but receive no new evidence."""
assert OLD in INSTRUCTIONS


def describe(base, policy):
    label = (
        "Always buy the independent customer sample"
        if policy == "always"
        else "No additional check"
    )
    return {
        "battery_version": VERSION,
        "condition": "sparse",
        "total_trials": 36,
        "companies": 24,
        "assigned_policy": policy,
        "instructions": INSTRUCTIONS.replace(OLD, NEW).replace(
            "Earlier resolutions and purchased audits remain available.",
            "Earlier resolutions remain available.",
        )
        + "\nIndependent sample definition: "
        + RESEARCH["customer_panel"]
        + "\nAssigned policy: "
        + label
        + ".",
        "diagnostics": "Report company probabilities and actions only; no research choice or source estimates are requested.",
        "answer_schema": Answer.model_json_schema(),
        "context_policy": base["context_policy"],
        "response_origin": base["response_origin"],
    }


def assignments(manifest, policy):
    return [
        {
            "company_id": c.company_id,
            "query": POLICIES[policy],
            "available_check_cost": costs(c)["customer_panel"],
            "charged_cost": costs(c)[POLICIES[policy]],
        }
        for c in manifest.companies[12:]
    ]


def present(trial, policy):
    result = original_present(trial, "structured")
    result.update(
        schema_version="epistemics.source-verification-trial.v1",
        battery_version=VERSION,
        research_costs={},
        research_options={},
        diagnostic_definitions={},
    )
    result.pop("selected_query", None)
    if trial.stage == "research":
        result["stage"] = "provisional"
        result["stage_instruction"] = (
            "Commit a provisional forecast and decision before the assigned check. Do not submit a research choice. Demand remains hidden until your final answer."
        )
        price = trial.research_costs["customer_panel"]
        result["assigned_verification"] = {
            "policy": policy,
            "available_check_cost": price,
            "charged_cost": price if policy == "always" else 0.0,
            "description": RESEARCH["customer_panel"]
            if policy == "always"
            else "No additional evidence or check cost; a final answer is still required.",
        }
    elif trial.stage == "revision":
        result["stage_instruction"] = (
            "Commit your final forecast and decision. The assigned check cost applies even if you decline. Demand is revealed only after this answer. With no check, no new evidence has arrived."
        )
        result["documents"] = [
            d.replace("You stopped research;", "The assigned policy supplied no check;")
            for d in result["documents"]
        ]
    return result
