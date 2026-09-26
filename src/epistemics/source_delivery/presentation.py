"""Public instructions shared by the browser and MCP; no private-world inputs."""

from epistemics.source_delivery import VERSION
from epistemics.source_learning.battery import INSTRUCTIONS
from epistemics.source_panel.presentation import present as original_present

RESEARCH = {
    "customer_panel": "Buy an accurately recorded, fresh random panel of five customers from this company. It shares no customers or measurement errors with the source's panels. Customer expansion is still uncertain: strong demand gives each customer a 70% expansion chance, weak demand 30%. This check does not reveal demand with certainty.",
    "selection_audit": "Learn this source's exact panel-selection rule: whether it reports one random panel or selects a measured result, and how. The rule applies to its archive and later reports. This audit does not reveal the company's demand or the source's measurement accuracy.",
    "measurement_audit": "Learn this source's exact per-customer measurement accuracy: the probability that expansion or non-expansion is recorded correctly. Measurement errors are independent and occur before panel selection. This accuracy applies to its archive and later reports. This audit does not reveal the company's demand or selection rule.",
    "stop": "Purchase no new evidence and pay zero research cost. A final checkpoint still follows so that you can confirm or revise your forecast and final decision; no new evidence arrives at that checkpoint.",
}
DIAGNOSTICS = {
    "measurement_accuracy": "Your expected probability that this source records an individual customer's expansion status correctly, before panel selection. This concerns the measurement process, not the chance that the company's demand is strong or that the source's reported panel represents all customers.",
    "random_selection_probability": "Your probability that this source reports one randomly drawn panel rather than selecting a panel according to the measured results. Accurate measurement alone does not establish random selection.",
}
STAGES = {
    "forecast": "Submit a probability of strong demand and your final invest/decline decision for this company. Demand is revealed after this answer is committed.",
    "research": "Submit a probability and provisional invest/decline decision using evidence available now, then choose one check or stop. Only your later final decision earns the investment payoff; research costs apply whichever final decision you make. Demand remains hidden until that final answer.",
    "revision": "Use the evidence now available to submit a revised probability and final invest/decline decision. Demand is revealed only after this answer is committed. After stop, this checkpoint contains no new evidence.",
}


def describe(base):
    result = dict(base)
    result.update(
        battery_version=VERSION,
        instructions=INSTRUCTIONS
        + "\n"
        + "\n".join(RESEARCH.values())
        + "\n"
        + "\n".join(STAGES.values()),
        research_options=RESEARCH,
        diagnostic_definitions=DIAGNOSTICS,
        stage_instructions=STAGES,
    )
    return result


def present(trial, presentation):
    # Preserve the declared menu order even after sorted JSON serialization.
    trial = trial.model_copy(
        update={
            "research_costs": {
                q: trial.research_costs[q] for q in RESEARCH if q in trial.research_costs
            }
        }
    )
    result = original_present(trial, presentation)
    result["battery_version"] = VERSION
    result["schema_version"] = "epistemics.source-delivery-trial.v1"
    result["stage_instruction"] = STAGES[trial.stage]
    result["research_options"] = (
        {q: {"description": RESEARCH[q], "cost": cost} for q, cost in trial.research_costs.items()}
        if trial.stage == "research"
        else {}
    )
    result["diagnostic_definitions"] = DIAGNOSTICS if trial.request_diagnostics else {}
    return result


def resolution(report_or_manifest, index):
    from epistemics.source_learning.battery import location

    company, stage = location(index)
    if stage == "research":
        return None
    return {
        "company_id": report_or_manifest.companies[company].company_id,
        "resolved_strong": report_or_manifest.companies[company].record.public.resolved_strong,
        "available_after": "accepted_final_answer",
    }
