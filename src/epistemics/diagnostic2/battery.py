"""Matched representation and uncertainty contrasts, without narrative-only hints."""

import random
from uuid import UUID

from epistemics.diagnostic2.models import STAGES, Assignment, Trial

INSTRUCTIONS = (
    "Evaluate one fictional company. Infer relationships from a complete archive of 20 comparable "
    "companies, supplied either as records or counts of the same event categories. All monetary "
    "values are in millions of credits. Growth means final audited revenue more than 10% above "
    "prior-period revenue. Exact population probabilities and causal mechanisms are not supplied. "
    "Cases are authored diagnostic contrasts, not random portfolio draws. Each checkpoint concerns "
    "the SAME company and period. Later growth evidence may be a definitive audit or an imperfect "
    "instrument reading. Repetition supplies no new information. Report probabilities from 0 to 1 "
    "in increments of 0.01 (whole percentages in the browser). Initially also predict the related "
    "event conditional on each possible definitive growth audit result, with no other new "
    "information. Earlier accepted answers cannot be edited."
)


def schedule(seed):
    rng = random.Random(seed)

    def identifier():
        return str(UUID(int=rng.getrandbits(128), version=4))

    assignments = []
    for target in ("backlog", "source"):
        directions, resolutions = [False, True], [False, True]
        rng.shuffle(directions)
        rng.shuffle(resolutions)
        for relationship, direction, outcome in zip(
            ("associated", "independent"), directions, resolutions, strict=True
        ):
            quartet, archive_seed = identifier(), rng.getrandbits(64)
            for presentation in ("summary", "records"):
                for evidence in ("audit", "signal"):
                    assignments.append(
                        Assignment(
                            assignment_id=identifier(),
                            quartet_id=quartet,
                            target=target,
                            relationship=relationship,
                            presentation=presentation,
                            evidence=evidence,
                            signal_positive=direction,
                            growth_outcome=direction,
                            auxiliary_outcome=outcome,
                            archive_seed=archive_seed,
                        )
                    )
    rng.shuffle(assignments)
    return assignments


def association(a):
    return (0.3 if a.target == "backlog" else -0.3) if a.relationship == "associated" else 0.0


def archive_counts(a):
    return [
        {
            "growth_above_10_percent": growth,
            "auxiliary_event": auxiliary,
            "companies": round(
                10 * (0.5 + (1 if growth else -1) * (1 if auxiliary else -1) * association(a))
            ),
        }
        for growth in (False, True)
        for auxiliary in (False, True)
    ]


def archive_records(a):
    rng = random.Random(a.archive_seed)
    records = []
    for row in archive_counts(a):
        for _ in range(row["companies"]):
            revenue = rng.choice((1120, 1140) if row["growth_above_10_percent"] else (1060, 1080))
            record = {"prior_revenue": 1000, "audited_revenue": revenue}
            if a.target == "backlog":
                record["opening_backlog"] = 120 if row["auxiliary_event"] else 80
            else:
                record["initial_bulletin_revenue"] = round(
                    revenue * (0.9 if row["auxiliary_event"] else 0.98)
                )
            records.append(record)
    rng.shuffle(records)
    return [{"company": f"Archive {i + 1:02d}", **r} for i, r in enumerate(records)]


def public_trial(a, index):
    if index not in range(4):
        raise ValueError("Unknown checkpoint")
    event = (
        "Backlog at the start of this reporting period exceeded 100 million credits"
        if a.target == "backlog"
        else "The initial revenue bulletin understated final audited revenue by at least 5% of "
        "final audited revenue: (audited revenue − bulletin revenue) / audited revenue ≥ 0.05"
    )
    documents = [
        "The archive includes all 20 comparable companies, not a selected subset. The current "
        "company is separate and has no additional company-specific facts at entry. Record "
        "identifiers have no predictive meaning. Monetary values beyond their defined event "
        "categories have no additional predictive relevance in this task."
    ]
    history = None
    growth = None
    if index >= 1:
        if a.evidence == "audit":
            growth = a.growth_outcome
            documents.append(
                "A definitive audit establishes revenue growth "
                + ("above 10%." if growth else "of 10% or less.")
                + " It did not directly check the related event."
            )
        else:
            history = [
                {"growth_above_10_percent": g, "high_reading": s, "companies": 15 if g == s else 5}
                for g in (False, True)
                for s in (False, True)
            ]
            documents.append(
                "An imperfect instrument returns a "
                + ("HIGH" if a.signal_positive else "LOW")
                + " growth reading. It is not an audit and does not resolve growth. Its attached "
                "complete validation history covers 40 other comparable companies. The instrument "
                "reads only the growth category; conditional on that category its errors are "
                "independent of the related event. Its error process is unchanged for this company. "
                "It has no access to backlog or the initial bulletin."
            )
    if index == 2:
        documents.append(
            "This is a second elicitation with exactly the same information. There is no new "
            "document, reading, business period or hint. Do not count the previous reading twice."
        )
    if index == 3:
        growth = a.growth_outcome
        documents.append(
            "A final definitive records audit now resolves BOTH events: revenue growth was "
            + ("above 10%; " if growth else "10% or less; ")
            + "the related event "
            + ("DID occur." if a.auxiliary_outcome else "DID NOT occur.")
            + " These facts concern the same original reporting period."
        )
    return Trial(
        trial_id=f"{a.assignment_id}:{index}",
        index=index,
        stage=STAGES[index],
        company=f"Company {a.assignment_id[:6]}",
        instructions=INSTRUCTIONS,
        auxiliary_event=event,
        archive_counts=archive_counts(a) if a.presentation == "summary" else None,
        archive_records=archive_records(a) if a.presentation == "records" else None,
        signal_history=history,
        documents=documents,
        growth_resolved=growth,
        auxiliary_resolved=a.auxiliary_outcome if index == 3 else None,
        request_conditionals=index == 0,
    )
