"""One four-checkpoint investigation. Public rendering has no seed or hidden states."""

from epistemics.investigation.models import InvestigationTrial, QueryOption
from epistemics.investigation.world import ASSUMPTIONS

INSTRUCTIONS = (
    "Investigate a fictional company. Forecast the probability that next-year revenue growth "
    "exceeds 12%. Also forecast whether a new independently selected historical source report "
    "understates its audited value by more than 2 points, and whether the current company's "
    "backlog reading exceeds 22. If a purchased check resolves one of those exact probes, "
    "report that known result thereafter. At checkpoint 1 select exactly one research option; "
    "otherwise omit query. Invest pays gain on target success and minus loss otherwise; hold "
    "pays zero. Maximize expected points with linear utility, holding at ties. The research cost "
    "is paid once regardless of invest/hold. The checkpoint-2 decision is committed before a "
    "later transcription review; buy research for that decision. Checkpoint 3 is a separate, "
    "unpaid revision diagnostic. All earlier decisions are provisional. Keep the same context "
    "within this episode. Explanations are optional and are not scored as internal mechanisms. "
    "Probabilities use increments of 0.01, including 0 and 1. Outcomes remain withheld until "
    "operator export after every planned episode finishes."
)
BACKGROUND = (
    "Underlying demand supports next-year growth. Implementation disruption can temporarily "
    "depress renewal-supported growth without the same fall in underlying demand. Resolved "
    "sector analogues and source reports below help you learn those relationships. Source "
    "bias and noise persist across its reports. Transcription errors can also affect the "
    "current report and all calculations derived from it; historical archive values have "
    "already been checked for transcription. A later review checks transcription, not source "
    "bias or business fundamentals. Cases are simulated; no outside company knowledge is needed."
)
QUERY_DESCRIPTIONS = {
    "source_audit": "Learn whether a new historical report from this source understated its audited value by more than 2 points. Tests the source, not this company's backlog.",
    "operations_check": "Learn whether the company's independently measured implementation backlog exceeds 22. Resolved analogues show how backlog relates to disruption.",
    "segment_check": "Learn whether growth in an unaffected customer cohort exceeds 12%. This cohort is outside the implementation backlog.",
    "calculation": "Compute current reported renewal-supported growth + 2 points. Uses existing data only; buys a calculation, not an independent report.",
    "stop": "Buy no further evidence; proceed to the committed decision with the existing record.",
}
BASE_COSTS = {
    "source_audit": 0.02,
    "operations_check": 0.02,
    "segment_check": 0.12,
    "calculation": 0.005,
    "stop": 0.0,
}


PRICE_MENUS = {
    "balanced": BASE_COSTS,
    "audit_discount": {
        "source_audit": 0.002,
        "operations_check": 0.15,
        "segment_check": 0.45,
        "calculation": 0.005,
        "stop": 0.0,
    },
    "operations_discount": {
        "source_audit": 0.15,
        "operations_check": 0.002,
        "segment_check": 0.45,
        "calculation": 0.005,
        "stop": 0.0,
    },
    "segment_discount": {
        "source_audit": 0.08,
        "operations_check": 0.08,
        "segment_check": 0.02,
        "calculation": 0.005,
        "stop": 0.0,
    },
    "expensive": {
        "source_audit": 1.0,
        "operations_check": 1.0,
        "segment_check": 1.0,
        "calculation": 0.1,
        "stop": 0.0,
    },
}


def public_trial(assignment, world, index, selected_query=None):
    if index not in range(4):
        raise ValueError("Index must be 0..3")
    if (selected_query is not None) != (index >= 2):
        raise ValueError("A branch is required only after the research choice")
    reported = world["reported_growth_pct"]
    offset = world["correction_offset_pct"]
    documents = [{"id": "background", "text": BACKGROUND}]
    if index >= 1:
        documents.extend(
            [
                {
                    "id": "operating-report",
                    "text": f"Source renewal-supported growth estimate: {reported:.1f}%. This is a measurement, not an audited outcome.",
                    "status": "superseded" if index == 3 else "current",
                },
                {
                    "id": "broker-headline",
                    "text": f"Broker repeats the source's {reported:.1f}% estimate. Derived solely from operating-report; no independent measurement.",
                    "status": "superseded" if index == 3 else "current",
                },
            ]
        )
    if index >= 2:
        if selected_query in world["queries"]:
            documents.append(
                {
                    "id": selected_query,
                    "text": QUERY_DESCRIPTIONS[selected_query]
                    + " Result: "
                    + ("yes." if world["queries"][selected_query] else "no."),
                }
            )
        elif selected_query == "calculation":
            documents.append(
                {
                    "id": "calculation",
                    "text": f"Projection = {reported:.1f} + 2 = {reported + 2:.1f}%. Derived solely from operating-report.",
                    "status": "superseded" if index == 3 else "current",
                }
            )
    if index == 3:
        corrected = round(reported - offset, 1)
        documents.append(
            {
                "id": "transcription-review",
                "text": f"Verified transcription offset (published minus source original): {offset:.1f} points. "
                f"Replace operating-report with {corrected:.1f}%. Its broker headline "
                f"also becomes {corrected:.1f}%; any +2 projection becomes {corrected + 2:.1f}%. "
                "This is the same original measurement, not another sample. Purchased independent checks and archives are unaffected.",
            }
        )
    return InvestigationTrial(
        trial_id=f"{assignment.assignment_id}:{index}",
        index=index,
        mode=assignment.mode,
        company="Alder Systems",
        instructions=INSTRUCTIONS,
        source_archive=world["archive"],
        analogues=world["analogues"],
        reported_growth_pct=reported if index >= 1 else None,
        correction_offset_pct=offset if index == 3 else None,
        selected_query=selected_query,
        query_result=world["queries"].get(selected_query) if index >= 2 else None,
        documents=documents,
        gain=assignment.gain,
        loss=assignment.loss,
        options=[
            QueryOption(
                query=q,
                description=description,
                cost=PRICE_MENUS[assignment.price_menu][q] * assignment.cost_scale,
            )
            for q, description in QUERY_DESCRIPTIONS.items()
        ]
        if index == 1
        else [],
        reference_assumptions=ASSUMPTIONS if assignment.mode == "calibration" else None,
    )
