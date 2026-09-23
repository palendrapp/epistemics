import random
from uuid import uuid4

from epistemics.diagnostic.models import STAGES, Assignment, Trial

INSTRUCTIONS = (
    "Evaluate one fictional company. Infer relationships from a complete archive of 40 comparable "
    "companies; exact population probabilities and causal mechanisms are not supplied. Cases are "
    "authored diagnostic contrasts, not random portfolio draws. Each checkpoint concerns the SAME "
    "company and reporting period. Audits definitively establish the stated event without changing "
    "the underlying company. No information is implied by a question being repeated. Report "
    "probabilities from 0 to 1 in increments of 0.01 (whole percentages in the browser). At the "
    "first checkpoint also predict the auxiliary event conditional on each possible growth audit "
    "result, with no other new information. Earlier accepted answers cannot be edited."
)


def schedule(seed):
    rng = random.Random(seed)
    assignments = []
    for target in ("backlog", "source"):
        # Direct resolutions balance yes/no within each target, independently of the archive.
        outcomes = [False, True]
        rng.shuffle(outcomes)
        for growth, auxiliary in zip((False, True), outcomes, strict=True):
            pair = str(uuid4())
            for relationship in ("associated", "independent"):
                assignments.append(
                    Assignment(
                        assignment_id=str(uuid4()),
                        pair_id=pair,
                        target=target,
                        relationship=relationship,
                        growth_outcome=growth,
                        auxiliary_outcome=auxiliary,
                    )
                )
    rng.shuffle(assignments)
    return assignments


def association(assignment):
    if assignment.relationship == "independent":
        return 0.0
    return 0.3 if assignment.target == "backlog" else -0.3


def public_trial(assignment, index):
    d = association(assignment)
    archive = [
        {
            "growth_above_10_percent": growth,
            "auxiliary_event": auxiliary,
            "companies": round(20 * (0.5 + (1 if growth else -1) * (1 if auxiliary else -1) * d)),
        }
        for growth in (False, True)
        for auxiliary in (False, True)
    ]
    event = (
        "Backlog at the start of this reporting period exceeded 100 million credits"
        if assignment.target == "backlog"
        else "The company's initial revenue bulletin understated its final audited revenue by at least 5%"
    )
    documents = [
        "The archive counts all 40 comparable companies, including all combinations of the two "
        "events. The current company is separate from that archive. There are no additional "
        "company-specific facts at entry. Growth means audited revenue growth above 10%."
    ]
    if index >= 1:
        documents.append(
            "The definitive growth audit is complete: revenue growth was "
            + ("above 10%." if assignment.growth_outcome else "10% or less.")
            + " The audit has not directly checked the auxiliary event."
        )
    if index == 2:
        documents.append(
            "This is a second elicitation with exactly the same information. "
            "There is no new document, observation, elapsed business period or hint."
        )
    if index == 3:
        documents.append(
            "A separate definitive records audit now establishes that the auxiliary "
            "event " + ("DID occur." if assignment.auxiliary_outcome else "DID NOT occur.")
        )
    return Trial(
        trial_id=f"{assignment.assignment_id}:{index}",
        index=index,
        stage=STAGES[index],
        company=f"Company {assignment.assignment_id[:6]}",
        instructions=INSTRUCTIONS,
        auxiliary_event=event,
        archive=archive,
        documents=documents,
        growth_resolved=assignment.growth_outcome if index >= 1 else None,
        auxiliary_resolved=assignment.auxiliary_outcome if index == 3 else None,
        request_conditionals=index == 0,
    )
