"""Both interfaces display the same bound prices and assigned-check semantics."""

from typing import Annotated, Literal

from pydantic import Field

from epistemics.models import Model
from epistemics.source_delivery.presentation import RESEARCH
from epistemics.source_delivery.presentation import present as original_present
from epistemics.source_learning.battery import INSTRUCTIONS
from epistemics.source_learning.models import Probability
from epistemics.source_selective import VERSION
from epistemics.source_selective.policy import RULE, price_for


class Answer(Model):
    probability: Annotated[
        Probability,
        Field(multiple_of=0.01, description="Whole percentage as a fraction: e.g. 0.63, not 0.632"),
    ]
    decision: Literal["invest", "decline"]


OLD = """The first twelve companies offer no research. For each of the next twelve, choose one paid check
or stop, then give a revised forecast and final decision. Audits also teach you about future use
of the source."""
NEW = """The first twelve companies offer no check. For each of the next twelve, give a provisional
forecast and decision. The evaluator then assigns either one independent five-customer sample
or no extra evidence according to the policy below. You do not choose a check. Give a final
forecast and decision in both cases; when no check is assigned there is no new evidence.
Only the final decision earns the investment payoff. Any assigned check cost is deducted even
if you decline. Source audits are unavailable. Offered prices are assigned separately from
company demand and source evidence. The policy is fixed before this collection."""
LABELS = {
    "none": "No additional check for any company; cost is always zero.",
    "always": "Buy the independent sample for every later company at its displayed price.",
    "cost_aware": (
        "After you commit a provisional probability, buy the independent sample only if its "
        "expected improvement in investment payoff exceeds its displayed price. The evaluator "
        "uses your reported probability, the investment threshold, and the stated 70%/30% "
        "customer expansion process to average over all possible five-customer sample results. "
        "It assumes Bayesian updating and a payoff-maximizing decision with and without the "
        "sample. Ties (within 1e-12 points) receive no check. Your provisional invest/decline "
        "choice does not determine the check. Report your best probability; you need not "
        "calculate or submit the check assignment."
    ),
}


def describe(base, policy):
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
        + LABELS[policy],
        "policy_definition": RULE if policy == "cost_aware" else {"id": policy},
        "diagnostics": "Report probabilities and invest/decline only; no research choice or source estimates are requested.",
        "answer_schema": Answer.model_json_schema(),
        "context_policy": base["context_policy"],
        "response_origin": base["response_origin"],
    }


def present(trial, binding):
    result = original_present(trial, "structured")
    result.update(
        schema_version="epistemics.source-selective-trial.v1",
        battery_version=VERSION,
        research_costs={},
        research_options={},
        diagnostic_definitions={},
    )
    result.pop("selected_query", None)
    policy = binding["policy"]
    if trial.stage == "research":
        result["stage"] = "provisional"
        result["stage_instruction"] = (
            "Commit your best provisional forecast and decision before the assigned check. "
            "Do not submit a research choice. Demand remains hidden until your final answer."
        )
        price = price_for(binding, trial.company_id)
        result["assigned_verification"] = {
            "policy": policy,
            "available_check_cost": price,
            "charged_cost": None
            if policy == "cost_aware"
            else price
            if policy == "always"
            else 0.0,
            "description": LABELS[policy],
        }
    elif trial.stage == "revision":
        price = price_for(binding, trial.company_id)
        checked = trial.selected_query == "customer_panel"
        result["stage_instruction"] = (
            "Commit your final forecast and decision. Demand is revealed only after this answer. "
            + (
                f"The assigned sample costs {price:.2f} points, including if you decline."
                if checked
                else "No check was assigned: no new evidence has arrived and the check cost is zero."
            )
        )
        result["assigned_verification"] = {
            "policy": policy,
            "available_check_cost": price,
            "charged_cost": price if checked else 0.0,
            "check_supplied": checked,
            "description": "Independent sample supplied." if checked else "No check supplied.",
        }
        result["documents"] = [
            d.replace("You stopped research;", "The assigned policy supplied no check;")
            for d in result["documents"]
        ]
    return result
