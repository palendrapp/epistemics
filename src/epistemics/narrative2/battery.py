"""Matched corroboration contrasts; prospective predictions precede the dashboard."""

import random
from uuid import UUID

from epistemics.narrative2.models import STAGES, Assignment, Trial

INSTRUCTIONS = (
    "Evaluate one fictional company and the SAME reporting period throughout four checkpoints. "
    "D means the defined real customer demand change; S means the defined reporting artifact. "
    "Allocate probability across four mutually exclusive combinations: demand_only (D and not S), "
    "artifact_only (S and not D), both (D and S), neither (not D and not S). These are event "
    "combinations, not an exhaustive list of causes: neither can include noise or other causes. "
    "Before the dashboard arrives, also predict the probability of its specified signal under "
    "EACH combination. Those four forecasts are separate conditional probabilities and need "
    "not sum to one. No numerical likelihoods or population base rates are supplied. Use your "
    'interpretation of the documents. At "Dashboard arrives", report your joint probabilities and choose '
    "one free, definitive check: demand_audit checks D only; pipeline_audit checks S only; stop "
    "provides no new evidence. Your research objective is to reduce uncertainty about the joint "
    "D/S state. Each check reveals only whether its event occurred, with no extra narrative clues. "
    "The final audit will resolve both. Treat audits as conclusive within this fictional task. "
    "Cases are authored contrasts, not random draws from a portfolio. Report probabilities from "
    "0 to 1 in increments of 0.01 (whole percentages in the browser). Joint probabilities must "
    "sum to 1. Accepted answers and research choices cannot be edited. Each checkpoint presents "
    "only its new documents; earlier accepted evidence remains available in history."
)


def schedule(seed):
    rng = random.Random(seed)

    def identifier():
        return str(UUID(int=rng.getrandbits(128), version=4))

    truths = [(False, False), (False, True), (True, False), (True, True)]
    rng.shuffle(truths)
    assignments = []
    for domain in ("subscriptions", "distributor"):
        for direction in ("rise", "fall"):
            d, s = truths.pop()
            pair = identifier()
            for corroboration in ("demand", "artifact"):
                assignments.append(
                    Assignment(
                        assignment_id=identifier(),
                        pair_id=pair,
                        domain=domain,
                        direction=direction,
                        corroboration=corroboration,
                        demand_outcome=d,
                        artifact_outcome=s,
                    )
                )
    rng.shuffle(assignments)
    return assignments


def events(a):
    quantity = "paid subscription seats" if a.domain == "subscriptions" else "customer order units"
    change = "increased" if a.direction == "rise" else "decreased"
    return {
        "demand_event": f"D: independently reconciled {quantity} {change} by more than 10% versus "
        "the previous comparable period, using the same customer cohort and accounting window",
        "artifact_event": f"S: a reporting-pipeline error exaggerated the dashboard's {a.direction} "
        "by at least 5 percentage points versus the independently reconciled change, with the "
        "same cohort and window",
        "signal_event": f"E: the preliminary dashboard says {quantity} {change} by more "
        "than 10% versus the previous comparable period",
    }


def background_facts(a):
    """Both formats contain exactly these sentences, without extra prose cues."""
    if a.domain == "subscriptions":
        business = (
            "Sales managers report stronger renewals after the company introduced a bundle."
            if a.direction == "rise"
            else "Sales managers report weaker renewals after the company raised subscription prices."
        )
        reporting = (
            "Engineers are checking whether the migration duplicates some renewal records."
            if a.direction == "rise"
            else "Engineers are checking whether the migration drops some renewal records."
        )
        setup = "A software company is migrating its subscription dashboard to a new reporting pipeline."
    else:
        business = (
            "Account managers report stronger orders after the distributor expanded delivery coverage."
            if a.direction == "rise"
            else "Account managers report weaker orders after the distributor reduced delivery coverage."
        )
        reporting = (
            "Engineers are checking whether the migration counts some order records twice."
            if a.direction == "rise"
            else "Engineers are checking whether the migration omits some order records."
        )
        setup = "A distributor is migrating its order dashboard to a new reporting pipeline."
    return [
        setup,
        business,
        "The managers' impression is anecdotal and has not been reconciled to customer records.",
        reporting,
        "At the time of the initial engineers' note, the suspected reporting problem had not been confirmed or quantified.",
        "Business changes and reporting errors can occur together; neither automatically rules "
        "out the other. Their statistical dependence is unknown.",
        "The dashboard has not arrived. No numerical base rates, error frequencies or earlier "
        "dashboard result are available.",
    ]


def corroborating_document(a):
    quantity = "paid subscription seats" if a.domain == "subscriptions" else "customer order units"
    change = "increase" if a.direction == "rise" else "decrease"
    if a.corroboration == "demand":
        finding = (
            "Independent customer-record check: an external reviewer obtained customer "
            f"confirmations and underlying account records for a substantial subset of the same "
            f"cohort and period. Most reviewed accounts show an actual {change} of more than "
            f"10% in {quantity}. The reviewer worked from customer records, separately from "
            "both the managers' anecdotes and the dashboard pipeline. This check supplies "
            "corroboration of real demand change but does not inspect the reporting pipeline. "
        )
    else:
        problem = "duplicate" if a.direction == "rise" else "missing"
        finding = (
            "Independent pipeline reproduction: an external reviewer traced original records "
            "through the reporting pipeline for a substantial subset of the same cohort and "
            f"period. The reviewer reproduced {problem} records. Reconstructing the reviewed "
            f"subset shows that this error exaggerates its apparent {change} by at least five "
            "percentage points. The review is an independent technical check, not a repeat of "
            "the engineers' suspicion. It supplies corroboration of a reporting artifact but "
            "does not determine the independently reconciled demand change. "
        )
    return finding + (
        "The reviewer has checked only a subset, not a complete or guaranteed-representative "
        "reconciliation. The result is fallible evidence and does not conclusively resolve D "
        "or S for the full cohort. The preliminary dashboard has not yet arrived. No numerical "
        "likelihood or population frequency is supplied."
    )


def public_trial(a, index, query=None):
    if index not in range(4):
        raise ValueError("Unknown checkpoint")
    if index >= 2 and query not in ("demand_audit", "pipeline_audit", "stop"):
        raise ValueError("Accepted research choice required")
    if index < 2 and query is not None:
        raise ValueError('No research choice before "Dashboard arrives" is accepted')
    d = s = None
    if index == 0:
        facts = background_facts(a)
        documents = [" ".join(facts), corroborating_document(a)]
    elif index == 1:
        documents = [
            "The preliminary dashboard has arrived: the specified signal E DID occur. This is "
            "the dashboard described earlier, not an independent corroborating source. It has "
            "not been audited and does not directly resolve D or S."
        ]
    elif index == 2:
        documents = ["You chose to stop. There is no new evidence or additional hint."]
        if query == "demand_audit":
            d = a.demand_outcome
            documents = [
                "A definitive demand audit establishes that D "
                + ("DID occur." if d else "DID NOT occur.")
                + " It does not check S and supplies no other information."
            ]
        elif query == "pipeline_audit":
            s = a.artifact_outcome
            documents = [
                "A definitive pipeline audit establishes that S "
                + ("DID occur." if s else "DID NOT occur.")
                + " It does not check D and supplies no other information."
            ]
    else:
        d, s = a.demand_outcome, a.artifact_outcome
        documents = [
            "The final definitive audit resolves both events: D "
            + ("DID occur; " if d else "DID NOT occur; ")
            + "S "
            + ("DID occur." if s else "DID NOT occur.")
            + " This concerns the same original company and period."
        ]
    return Trial(
        trial_id=f"{a.assignment_id}:{('background', 'dashboard', 'research', 'resolution')[index]}",
        checkpoint=index + 1,
        stage=STAGES[index],
        company=f"Company {a.assignment_id[:6]}",
        instructions=INSTRUCTIONS,
        **events(a),
        new_documents=documents,
        request_signal_forecasts=index == 0,
        request_query=index == 1,
        selected_query=query,
        demand_resolved=d,
        artifact_resolved=s,
    )
