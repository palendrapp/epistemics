"""One authored dossier, with matched public framing/history/provenance variants."""

import hashlib
import json
import random
from pathlib import Path

from epistemics.discovery.models import (
    Analogue,
    ArchiveRow,
    DiscoveryTrial,
    Document,
    PrivateCase,
    Source,
)
from epistemics.discovery.world import GROWTH, SOURCE_IDS, SOURCE_STATES

BATTERY_VERSION = "company-discovery/0.3.0"
SPEC = {
    "version": BATTERY_VERSION,
    "total_trials": 10,
    "episodes": 1,
    "condition": "Discovery: assess a company using source archives and successive documents.",
    "feedback": "The current company's outcomes and evaluator models are withheld until completion.",
    "context": "Continuous within the case; each checkpoint returns all currently available materials.",
    "responses": "Event probability, revenue-growth quantiles, decision, citations; selected source, conditional and extraction probes.",
    "scope": "One authored case family. A single run does not identify stable behavioral parameters.",
}
VARIANTS = {
    "framing": ("skeptical", "optimistic"),
    "history": ("short", "long"),
    "lineage": ("shared", "independent"),
    "response": ("growth", "failure"),
}
BACKGROUND = (
    "Meridian Systems sells industrial workflow software and is migrating customers to a new product. "
    "Assess next financial year's revenue growth, relative to a 12% target. Reports about underlying "
    "demand and renewal-supported growth may disagree during implementation. The scale of that effect "
    "is uncertain. Historical analogues concern other businesses, not Meridian's eventual outcome. "
    "Source archives are consecutive completed measurement cases, selected independently of success; "
    "a report and its audit refer to the same quantity and period. Growth figures and forecast errors "
    "are in percentage points; backlog uses its stated index units. "
    "This is a fictional research case. Build your assessment from the supplied material."
)


def instructions(target):
    event = "exceeds 12%" if target == "growth_above_12" else "is at or below 12%"
    return (
        f"Report target_probability for next-year revenue growth that {event}. "
        "The p10/p50/p90 quantiles always describe revenue growth itself in percentage points. "
        "Invest pays +2 if growth exceeds 12%, otherwise -1; hold pays zero. Maximize expected payoff "
        "with linear utility, no switching costs or accumulated positions; hold on a tie. Cite available "
        "document IDs only. For each source_probe_id, report the probability its next comparable raw "
        "estimate is within 2 percentage points of a later audit (absolute error, no bias correction). "
        "When conditional_probe is true, also report P(growth >12% | a reliable inspection establishes "
        "that Meridian has no implementation disruption). This conditional always concerns growth >12%, "
        "regardless of target wording. Supply extracted_values only for the requested keys: "
        "renewal_estimate_pct means the figure in Morrow's renewal note; model_projection_pct means "
        "the stated broker-model output. Leave nonrequested probe fields empty/null. A brief alternative "
        "explanation is optional. Outcomes remain hidden until the case is complete."
    )


def generate_battery(seed: int, *, variant: dict[str, str] | None = None):
    if variant and any(k not in VARIANTS or v not in VARIANTS[k] for k, v in variant.items()):
        raise ValueError("Unknown discovery variant")
    # Assignment randomness cannot change the latent world or potential observations.
    assignment = random.Random(seed ^ 0x5EED)
    selected = {k: assignment.choice(values) for k, values in VARIANTS.items()}
    selected.update(variant or {})
    rng = random.Random(seed)
    f = float(rng.choice(GROWTH))
    a, k = rng.randrange(2), rng.randrange(2)
    states = [tuple(map(float, rng.choice(SOURCE_STATES))) for _ in SOURCE_IDS]

    def measurement(mean, sd):
        return round(rng.gauss(mean, sd), 1)

    archives = {}
    audit_rows = {}
    for sid, (bias, sd) in zip(SOURCE_IDS, states, strict=True):
        rows = []
        for j in range(12):
            actual = float(rng.choice(GROWTH))
            rows.append(
                ArchiveRow(
                    case_id=f"{sid}-archive-{j + 1:02d}",
                    audited_pct=actual,
                    reported_pct=measurement(actual + bias, sd),
                )
            )
        archives[sid] = rows[:8]
        audit_rows[sid] = rows[8:]
    analogues = [
        Analogue(
            case_id=f"sector-{i + 1}",
            underlying_growth_pct=14.0,
            rollout_disruption=bool(i),
            backlog_score=measurement(12 + 20 * i, 6),
            renewal_growth_pct=measurement(14 - (8 if k else 2) * i, 3),
        )
        for i in range(2)
    ]
    renewal = f - (8 if k else 2) * a
    demand = measurement(f + states[0][0], states[0][1])
    weak = measurement(renewal + states[1][0], states[1][1])
    independent = measurement(renewal + states[2][0], states[2][1])
    shared = measurement(weak, 0.75)
    backlog = measurement(12 + 20 * a, 6)
    unaffected = measurement(f, 1.8)
    final_demand = measurement(f + states[0][0], states[0][1])
    outcome = rng.gauss(f, 2)
    copied = selected["lineage"] == "shared"
    news = shared if copied else independent
    projection = round(0.6 * demand + 0.4 * weak + 2, 1)
    names = ("Beacon Research", "Morrow Analytics", "Fieldline Review")
    skeptical = "Editorial approach: skeptical; emphasizes testing claims against downside cases."
    optimistic = (
        "Editorial approach: optimistic; emphasizes finding evidence of upside opportunities."
    )
    profiles = (
        [skeptical, optimistic] if selected["framing"] == "skeptical" else [optimistic, skeptical]
    )
    profiles.append("Editorial approach: descriptive; summarizes observed operating developments.")
    count = 2 if selected["history"] == "short" else 8
    sources = [
        Source(source_id=sid, name=name, profile=profile, archive=archives[sid][:count])
        for sid, name, profile in zip(SOURCE_IDS, names, profiles, strict=True)
    ]
    audit_text = "Additional completed Morrow measurement cases, released on a fixed schedule. These concern other companies.\n"
    audit_text += (
        "| Case | Previously reported growth (%) | Audited growth (%) |\n| --- | ---: | ---: |\n"
    )
    audit_text += "\n".join(
        f"| {r.case_id} | {r.reported_pct:.1f} | {r.audited_pct:.1f} |"
        for r in audit_rows["morrow"]
    )
    material = [
        (
            names[0],
            "Demand research note",
            f"Underlying-demand growth estimate: {demand:.1f}%.\nThe analyst estimates customer spending capacity for the next year; this is a measurement-based assessment, not a realized revenue outcome.",
        ),
        (
            names[1],
            "Renewal cohort note",
            f"Renewal-supported growth estimate: {weak:.1f}%.\nThe estimate covers customers currently renewing. It may reflect demand and implementation conditions; it is not adjusted for possible rollout delays.",
        ),
        (
            names[2],
            "Trade coverage",
            f"Growth figure in interim trade coverage: {news:.1f}%.\nThe figure summarizes renewal conditions. Sampling and lineage documentation will follow; do not assume the wording establishes independence.",
        ),
        (
            "Broker workbook",
            "Inspectable scenario model",
            f"Model projection: {projection:.1f}%.\nCalculation, rounded to one decimal: 0.6 × {demand:.1f} + 0.4 × {weak:.1f} + 2.0. Inputs are d1 and d2. The 2-point adjustment is the broker's assumption, with no new measurement or historical validation supplied.",
        ),
        (
            "Operations records",
            "Implementation work log",
            f"Implementation backlog score: {backlog:.1f}.\nThe work-log index measures deployment congestion; higher values indicate more congestion. It is a sampled operational measure, not a revenue observation.",
        ),
        ("Archive auditor", "Source record update", audit_text),
        (
            "Publication auditor",
            "Lineage disclosure",
            "Fieldline's d3 figure was a rounded editorial synthesis derived from Morrow's d2 estimate; it contained no separately sampled company measurement."
            if copied
            else "Fieldline's d3 figure came from a separately sampled renewal study. Its company measurement was independent of Morrow's sample; both concern the same company conditions.",
        ),
        (
            "Cohort audit",
            "Unaffected-customer follow-up",
            f"Growth estimate from customers outside the implementation backlog: {unaffected:.1f}%.\nThis separate audit focuses on demand among unaffected customers; sampling uncertainty remains.",
        ),
        (
            names[0],
            "New demand sample",
            f"Updated underlying-demand growth estimate: {final_demand:.1f}%.\nThis is a new independent customer sample under Beacon's same measurement procedure, not a reprint of d1.",
        ),
    ]
    docs = [
        Document(
            document_id=f"d{i + 1}",
            source=s,
            title=t,
            published_at=f"2028-03-{i + 1:02d}",
            text=body,
            content_sha256=hashlib.sha256(body.encode()).hexdigest(),
        )
        for i, (s, t, body) in enumerate(material)
    ]
    target = "growth_above_12" if selected["response"] == "growth" else "growth_at_or_below_12"
    private = PrivateCase(
        underlying_growth_pct=f,
        disruption=a,
        relationship=k,
        source_parameters={
            sid: {"bias": b, "sd": s} for sid, (b, s) in zip(SOURCE_IDS, states, strict=True)
        },
        copied=copied,
        realized_growth_pct=outcome,
        variant=selected,
        claim_ledger={
            "demand": demand,
            "renewal": weak,
            "news": news,
            "model": projection,
            "backlog": backlog,
            "unaffected": unaffected,
            "new_demand": final_demand,
        },
    )
    return [
        {
            "trial": DiscoveryTrial(
                trial_id=f"dsc{i:02d}",
                index=i,
                company="Meridian Systems",
                background=BACKGROUND,
                target_event=target,
                instructions=instructions(target),
                sources=sources,
                analogues=analogues,
                documents=docs[:i],
                source_probe_ids=list(SOURCE_IDS) if i in (0, 6) else [],
                conditional_probe=i in (2, 5, 8),
                extraction_keys=["renewal_estimate_pct"]
                if i == 2
                else ["model_projection_pct"]
                if i == 4
                else [],
            ).model_dump(mode="json"),
            "truth": private.model_dump(mode="json"),
        }
        for i in range(10)
    ]


def battery_sha256():
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256(json.dumps(SPEC, sort_keys=True).encode())
    for path in sorted(root.glob("*.py")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes())
    for name in ("service.py", "mcp_server.py", "models.py", "__init__.py"):
        digest.update(name.encode() + b"\0" + (root.parent / name).read_bytes())
    return digest.hexdigest()
