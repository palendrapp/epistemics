"""Named stages and prospective query probes, shared by humans and MCP agents."""

from epistemics.investigation.battery import BACKGROUND, QUERY_DESCRIPTIONS
from epistemics.investigation.models import QueryOption
from epistemics.investigation2.models import MEASUREMENTS, STAGES, Trial
from epistemics.investigation2.world import ASSUMPTIONS

INSTRUCTIONS = (
    "Investigate this fictional company using only its supplied record. Give probabilities "
    "for next-year growth exceeding 12%, a selected historical source report understating its "
    "audit by more than 2 points, and this company's backlog exceeding 22. Use whole percentages "
    "(0 to 100), represented in the API as probabilities in increments of 0.01. A purchased "
    "source or backlog check resolves that exact event: retain the known probability thereafter. "
    "At Evidence and research, select one check or stop. Where requested, also forecast each "
    "check's yes result and growth conditional on yes or no, before seeing a result. "
    "These are predictions, not requests for private reasoning. Research costs are paid once. "
    "Invest earns gain on growth success and minus loss otherwise; hold earns zero. Maximize "
    "expected points with linear utility; hold at ties. Background and Evidence decisions "
    "are provisional. Only Result and commitment determines payoff. Transcription review is "
    "a later unpaid diagnostic; its decision cannot change the committed payoff. Earlier "
    "accepted answers are immutable. No outcomes or analysis are returned during participation."
)


def public_trial(assignment, world, index, selected_query=None):
    checked = assignment.family == "research"
    reported = world["reported_growth_pct"]
    documents = [{"id": "background", "text": BACKGROUND}]
    documents.append(
        {
            "id": "transcription-status",
            "text": (
                "The operating estimate has already been verified against the source original; no transcription error remains."
                if checked
                else "The operating estimate has not yet been checked for transcription. A later review may raise, lower or confirm it."
            ),
        }
    )
    if index >= 1:
        documents.extend(
            [
                {
                    "id": "operating-report",
                    "text": f"Source renewal-supported growth estimate: {reported:.1f}%. This is not an audited outcome.",
                    "status": "superseded" if index == 3 else "current",
                },
                {
                    "id": "broker-headline",
                    "text": f"Broker repeats {reported:.1f}%, derived solely from operating-report; no independent measurement.",
                    "status": "superseded" if index == 3 else "current",
                },
            ]
        )
    if index >= 2:
        if selected_query in MEASUREMENTS:
            documents.append(
                {
                    "id": selected_query,
                    "text": QUERY_DESCRIPTIONS[selected_query]
                    + (" Result: yes." if world["queries"][selected_query] else " Result: no."),
                }
            )
        elif selected_query == "calculation":
            documents.append(
                {
                    "id": "calculation",
                    "text": f"Projection: {reported:.1f} + 2 = {reported + 2:.1f}%. Existing data only.",
                    "status": "superseded" if index == 3 else "current",
                }
            )
        else:
            documents.append(
                {"id": "stop", "text": "No research was purchased. No new evidence is available."}
            )
    if index == 3:
        offset = world["correction_offset_pct"]
        value = reported - offset
        documents.append(
            {
                "id": "transcription-review",
                "text": f"Verified offset (published minus original): {offset:+.1f} points. Replace the operating estimate and its broker copy with {value:.1f}%; any +2 projection becomes {value + 2:.1f}%. This is the same measurement, not an additional sample. Independent checks and archives are unchanged.",
            }
        )
    costs = {
        "source_audit": 0.025,
        "operations_check": 0.025,
        "segment_check": 0.06,
        "calculation": 0.005,
        "stop": 0.0,
    }
    if checked:
        costs = {q: 1.0 for q in MEASUREMENTS} | {"calculation": 0.005, "stop": 0.0}
        costs[assignment.focused_query] = 0.005 if assignment.price_condition == "low" else 1.0
    return Trial(
        trial_id=f"{assignment.assignment_id}:{index}",
        index=index,
        stage=STAGES[index],
        mode=assignment.mode,
        instructions=INSTRUCTIONS,
        source_archive=world["archive"],
        analogues=world["analogues"],
        transcription_checked=checked,
        reported_growth_pct=reported if index >= 1 else None,
        correction_offset_pct=world["correction_offset_pct"] if index == 3 else None,
        selected_query=selected_query,
        query_result=world["queries"].get(selected_query) if index >= 2 else None,
        documents=documents,
        options=[
            QueryOption(query=q, description=description, cost=costs[q])
            for q, description in QUERY_DESCRIPTIONS.items()
        ]
        if index == 1
        else [],
        expectation_queries=list(MEASUREMENTS) if checked and index == 1 else [],
        gain=assignment.gain,
        loss=assignment.loss,
        reference_assumptions=ASSUMPTIONS if assignment.mode == "calibration" else None,
    )
