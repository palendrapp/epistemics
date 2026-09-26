"""Render only the existing public trial; never accept a private world as input."""

from epistemics.source_learning.models import Trial
from epistemics.source_panel import PACKET_VERSION


def packet(trial: Trial) -> dict:
    paragraphs = [
        f"Research note for {trial.company_id}. Reporting source: {trial.source_id}.",
        " ".join(trial.documents),
    ]
    records = []
    for i, row in enumerate(trial.archive, 1):
        w = row.world
        records.append(
            f"Record {i}: {row.source_id} reported {row.count} of {w.panel_size} customers "
            f"expanding; demand later proved {'strong' if row.resolved_strong else 'weak'}. "
            f"For this record, independent customers expand with probability "
            f"{w.strong_rate:g} under strong demand and {w.weak_rate:g} under weak demand."
        )
    paragraphs.append("Resolved source history, in its original order. " + " ".join(records))
    rule = trial.known_selection
    if rule is None:
        paragraphs.append("No selection-process audit for this source is available yet.")
    elif rule.direction == "random":
        paragraphs.append("An available audit establishes that this source uses one random panel.")
    else:
        paragraphs.append(
            f"An available audit establishes that this source selects the {rule.direction} "
            f"measured count among {rule.panels} independent five-customer panels."
        )
    if trial.known_measurement_accuracy is None:
        paragraphs.append("No measurement-accuracy audit for this source is available yet.")
    else:
        paragraphs.append(
            "An available audit establishes an individual-measurement accuracy of "
            f"{trial.known_measurement_accuracy:g}."
        )
    paragraphs.append(
        f"Decision terms: the prior probability of strong demand is {trial.prior_strong:g}; "
        f"the investment threshold is {trial.decision_threshold:g}."
    )
    if trial.research_costs:
        paragraphs.append(
            "Research menu, with costs in fictional points: "
            + "; ".join(f"{q}: {cost:g}" for q, cost in trial.research_costs.items())
            + "."
        )
    if trial.selected_query is not None:
        paragraphs.append(f"Your committed research choice was {trial.selected_query}.")
    paragraphs.append(
        "Submit a company probability and invest/decline decision"
        + (", plus one research choice." if trial.stage == "research" else ".")
    )
    if trial.request_diagnostics:
        paragraphs.append(
            "Also report individual measurement accuracy and the probability of random selection."
        )
    return {
        "schema_version": "epistemics.source-packet-trial.v1",
        "battery_version": PACKET_VERSION,
        "trial_id": trial.trial_id,
        "checkpoint": trial.checkpoint,
        "company_id": trial.company_id,
        "stage": trial.stage,
        "research_packet": "\n\n".join(paragraphs),
    }


def present(trial, presentation):
    if presentation == "structured":
        return trial.model_dump(mode="json")
    if presentation == "packet":
        return packet(trial)
    raise ValueError("Unknown presentation")
