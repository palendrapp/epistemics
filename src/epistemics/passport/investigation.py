"""Exact-byte investigation collections and a descriptive passport adapter.

The collection embeds original report bytes, validates their common assignment
schedule, and recomputes behavioral facts. It never relabels old observations or
promotes conditional model parameters to validated traits.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from epistemics.investigation2 import inference as old_inference
from epistemics.investigation2.models import Report as OldReport
from epistemics.investigation2.service import digest, encoded, write_private
from epistemics.investigation3 import inference as new_inference
from epistemics.investigation3.models import Report as NewReport
from epistemics.models import Model
from epistemics.participants import Digest, EvaluationConditions, SessionContext
from epistemics.passport.models import (
    InvestigationDiagnostics,
    InvestigationPassport,
    InvestigationSourceArtifact,
)


class CaseArtifact(Model):
    report_sha256: Digest
    report_json: str

    @model_validator(mode="after")
    def exact_bytes(self):
        if digest(self.report_json.encode()) != self.report_sha256:
            raise ValueError("Embedded report bytes do not match their hash")
        return self


class InvestigationCollection(Model):
    schema_version: Literal["epistemics.investigation-collection.v1"] = (
        "epistemics.investigation-collection.v1"
    )
    context: SessionContext
    manifest_sha256: Digest
    evaluation_mode: Literal["discovery", "calibration"]
    cases: list[CaseArtifact] = Field(min_length=12, max_length=12)
    facts: dict[str, float | None]
    coverage: dict[str, int]
    examples: list[dict]
    model_diagnostics: InvestigationDiagnostics
    limitations: list[str]


def read_case(source):
    data = json.loads(source.report_json)
    if data.get("schema_version") == "epistemics.investigation-report.v2":
        return OldReport.model_validate(data)
    if data.get("schema_version") == "epistemics.investigation-report.v3":
        return NewReport.model_validate(data)
    raise ValueError("Unsupported investigation report schema")


def derive(sources):
    reports = [read_case(s) for s in sources]
    if len(reports) != 12:
        raise ValueError("A full 12-case collection is required")
    manifest = reports[0].manifest
    mh = digest(encoded(manifest))
    modes = {a.mode for a in manifest.assignments}
    if len(modes) != 1:
        raise ValueError("A passport cannot pool discovery and calibration conditions")
    decisions = coherent = policy = selected = correction = resolved = persistent = 0
    resolved_count = correction_count = coherent_count = 0
    gaps, revisions, examples = [], [], []
    engine = old_inference if isinstance(reports[0], OldReport) else new_inference
    if engine is old_inference:
        from epistemics.investigation2.battery import public_trial
        from epistemics.investigation2.world import generate
    else:
        from epistemics.investigation3.battery import public_trial
        from epistemics.investigation3.world import generate
    for ordinal, (r, assignment) in enumerate(zip(reports, manifest.assignments, strict=True), 1):
        if (
            type(r) is not type(reports[0])
            or r.manifest != manifest
            or r.manifest_sha256 != mh
            or r.assignment != assignment
        ):
            raise ValueError("Mixed, missing, reordered or substituted collection reports")
        obs = r.observations
        chosen = obs[1].answer.query
        if chosen is None:
            raise ValueError("Missing research choice")
        world = generate(assignment.seed, assignment.offset)
        for index, o in enumerate(obs):
            if o.trial != public_trial(assignment, world, index, chosen if index >= 2 else None):
                raise ValueError("Public trial differs from its frozen assignment")
            if (o.answer.query is not None) != (index == 1) or set(
                o.answer.expectations or {}
            ) != set(o.trial.expectation_queries):
                raise ValueError("Answer does not match the requested stage")
            engine.report_log_likelihood(engine.answer_vector(o.answer), [0.5] * 3)
            for row in (o.answer.expectations or {}).values():
                engine.report_log_likelihood(list(row.model_dump().values()), [0.5] * 3)
            time = datetime.fromisoformat(o.answered_at)
            if time.tzinfo is None:
                raise ValueError("Answer timestamps must include a timezone")
        times = [datetime.fromisoformat(o.answered_at) for o in obs]
        end = datetime.fromisoformat(r.completed_at)
        beginning = datetime.fromisoformat(manifest.created_at)
        if (
            beginning.tzinfo is None
            or end.tzinfo is None
            or times != sorted(times)
            or times[0] < beginning
            or times[-1] > end
        ):
            raise ValueError("Invalid investigation chronology")
        # Imported analysis and private truth are not trusted as behavioral facts.
        calculated = old_inference.analysis(obs, world)
        decisions += calculated["decision_probability_agreements"]
        persistent += (
            obs[0].answer.audit_understatement_probability
            == obs[1].answer.audit_understatement_probability
        )
        revisions.append(
            abs(
                obs[1].answer.audit_understatement_probability
                - obs[0].answer.audit_understatement_probability
            )
            * 100
        )
        own = calculated["research"]["reported_expectations"]
        if own is not None:
            coherent_count += 1
            is_coherent = own["coherence_within_rounding_tolerance"]
            coherent += is_coherent
            # Preference agreement is only interpreted for coherent forecasts.
            if is_coherent:
                selected += 1
                policy += own["report_implied_regret"] <= 1e-10
            gaps.append(own["max_mixture_gap_pp"])
        revision = calculated["correction_revision_pp"][0]
        if assignment.family == "review" and assignment.offset:
            correction_count += 1
            correction += np.sign(revision) == -np.sign(assignment.offset)
        if chosen in ("source_audit", "operations_check"):
            j = 1 if chosen == "source_audit" else 2
            for o in obs[2:]:
                resolved_count += 1
                resolved += engine.answer_vector(o.answer)[j] == float(o.trial.query_result)
        examples.append(
            {
                "case_number": ordinal,
                "family": assignment.family,
                "query": chosen,
                "price_condition": assignment.price_condition,
                "growth_reports": [o.answer.growth_probability for o in obs],
                "source_reports": [o.answer.audit_understatement_probability for o in obs],
                "growth_review_change_pp": revision,
                "change_to_operating_estimate_pp": -assignment.offset,
                "research_forecasts_coherent": None
                if own is None
                else own["coherence_within_rounding_tolerance"],
            }
        )

    def pct(n, d):
        return float(100 * n / d) if d else None

    facts = {
        "decision_agreement_percent": pct(decisions, 48),
        "research_coherence_percent": pct(coherent, coherent_count),
        "research_policy_agreement_percent": pct(policy, selected),
        "correction_direction_agreement_percent": pct(correction, correction_count),
        "resolved_probe_agreement_percent": pct(resolved, resolved_count),
        "source_persistence_percent": pct(persistent, 12),
        "source_revision_mean_absolute_pp": float(np.mean(revisions)),
        "prospective_max_mixture_gap_pp": max(gaps) if gaps else None,
    }
    context = SessionContext(
        session_id=manifest.study_id,
        participant=manifest.participant,
        response_origin=manifest.response_origin,
        protocol_version=manifest.battery_version,
        protocol_sha256=manifest.implementation_sha256,
        evaluator_version=manifest.evaluator_version,
        conditions=EvaluationConditions(
            interface="unspecified",
            context_policy=manifest.context_policy,
        ),
        started_at=manifest.created_at,
        completed_at=max(datetime.fromisoformat(r.completed_at) for r in reports),
        completion="complete",
        accepted_answers=48,
        planned_answers=48,
    )
    diagnostics = {
        "analysis_version": manifest.analysis_version,
        "parameters_are_validated_traits": False,
        "empirical_predictive_validation": False,
        "intervention_benefit_tested": False,
        "fits": {"hard_report": engine.fit([r.observations for r in reports])}
        if engine is old_inference
        else {
            m: engine.fit([r.observations for r in reports], initialization=m)
            for m in engine.INITIALIZATIONS
        },
    }
    return InvestigationCollection(
        context=context,
        manifest_sha256=mh,
        evaluation_mode=next(iter(modes)),
        cases=sources,
        facts=facts,
        coverage={
            "cases": 12,
            "unique_worlds": len({a.seed for a in manifest.assignments}),
            "checkpoints": 48,
            "probability_reports": 198,
            "research_cases": coherent_count,
            "coherent_research_cases": int(coherent),
            "research_policy_cases": selected,
            "nonzero_review_cases": correction_count,
            "resolved_probe_checks": resolved_count,
        },
        examples=examples,
        model_diagnostics=diagnostics,
        limitations=[
            "One authored company mechanism; repeated stages and matched price twins are dependent observations.",
            "Probabilities are reports, not direct access to internal beliefs. Identity and execution are operator-asserted.",
            "Research uses one query and deliberately large price contrasts; no stable cost-sensitivity parameter is identified.",
            "Direction of correction and decision/report agreement are descriptive consistency measures, not general accuracy or calibration.",
            "Parameter fits and grid intervals are development diagnostics; no validated phenotype, transfer or assistance benefit.",
            "The source manifest does not attest the collection interface; it is left unspecified rather than inferred from participant kind.",
            "Raw reports and detailed findings remain private unless separately authorized for publication.",
        ],
    )


def bundle(directory):
    directory = Path(directory)
    raw_manifest = (directory / "manifest.json").read_bytes()
    mh = digest(raw_manifest)
    if (directory / "manifest.sha256").read_text().strip() != mh:
        raise ValueError("Manifest byte hash mismatch")
    manifest = json.loads(raw_manifest)
    hashes = json.loads((directory / "report-hashes.json").read_bytes())
    sources = []
    for assignment in manifest["assignments"]:
        aid = assignment["assignment_id"]
        if not isinstance(aid, str) or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in aid
        ):
            raise ValueError("Invalid assignment identifier")
        name = f"{aid}.json"
        raw = (directory / "reports" / name).read_bytes()
        sources.append(CaseArtifact(report_sha256=hashes[name], report_json=raw.decode("utf-8")))
    result = derive(sources)
    if result.manifest_sha256 != mh:
        raise ValueError("Report manifest differs from collection")
    return result


def export_bundle(directory, output):
    raw = encoded(bundle(directory))
    Path(output).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    write_private(output, raw)
    return raw


def build_investigation_passport(raw, *, response_origin="unspecified", created_at=None):
    from epistemics.passport.build import dimension, example, metric, pointer_value

    source = InvestigationCollection.model_validate_json(raw)
    expected = derive(source.cases)
    if source != expected:
        raise ValueError(
            "Investigation facts, context or diagnostics differ from the original reports"
        )
    if response_origin not in ("unspecified", source.context.response_origin):
        raise ValueError("Recorded investigation origin cannot be relabeled")
    data = source.model_dump(mode="json")

    def measurement(key, label, unit):
        return [] if source.facts[key] is None else [metric(data, "/facts/" + key, label, unit)]

    dims = [
        dimension(
            "evidence_weighting",
            "The reports show how company forecasts change. No general evidence-weight coefficient is established.",
            identified=False,
            limits=[
                "Initial-response assumptions materially affect cognitive fits; model diagnostics are separate from behavioral measurements."
            ],
        ),
        dimension(
            "source_judgment",
            "Source-report persistence is measured between Background and Evidence within each case.",
            measurements=measurement(
                "source_persistence_percent",
                "Source report unchanged after operating evidence",
                "%",
            )
            + measurement(
                "source_revision_mean_absolute_pp", "Mean absolute source report revision", "pp"
            ),
            limits=[
                "Persistence alone does not identify anchoring, justified stability or inability to learn."
            ],
        ),
        dimension(
            "belief_revision",
            f"The collection includes {source.coverage['nonzero_review_cases']} actual transcription corrections and {source.coverage['resolved_probe_checks']} checks of already resolved events.",
            measurements=measurement(
                "correction_direction_agreement_percent",
                "Growth revision follows correction direction",
                "%",
            )
            + measurement(
                "resolved_probe_agreement_percent", "Resolved event report retained correctly", "%"
            ),
            examples=[
                example(
                    f"Case {e['case_number']}: growth report changed by {e['growth_review_change_pp']:+.0f} points at review.",
                    f"/examples/{i}",
                )
                for i, e in enumerate(source.examples)
                if e["change_to_operating_estimate_pp"]
            ][:4],
            limits=[
                "The expected direction is conditional on this company task; revision magnitude has no universal optimum."
            ],
        ),
        dimension(
            "dependence_and_causal_reasoning",
            "Auxiliary forecasts and research choices are recorded, but broad causal reasoning and independent hypothesis discovery remain unmeasured.",
            identified=False,
            limits=[
                "The mechanism is scaffolded. No independent-versus-copy contrast or unrestricted hypothesis-generation score is issued."
            ],
        ),
        dimension(
            "uncertainty_and_calibration",
            "Prospective coherence describes whether related forecasts agree with one another. Outcome calibration remains unestablished.",
            measurements=measurement(
                "research_coherence_percent", "Coherent prospective forecast sets", "%"
            )
            + measurement(
                "prospective_max_mixture_gap_pp", "Largest total-probability discrepancy", "pp"
            ),
            limits=[
                "Six prospective sets with a 1.5-point rounding tolerance; consistency is distinct from predictive accuracy."
            ],
        ),
        dimension(
            "decision_consistency",
            "Reported probabilities, declared payoffs and research choices can be checked directly.",
            measurements=measurement(
                "decision_agreement_percent", "Decision and reported probability agreement", "%"
            )
            + measurement(
                "research_policy_agreement_percent",
                "Research choice maximizes coherent reported value",
                "%",
            ),
            limits=[
                f"Research-policy agreement uses {source.coverage['research_policy_cases']} coherent cases; incoherent sets are excluded from that preference interpretation and retained in coherence coverage.",
                "No real investment performance, stable utility or subtle price-sensitivity claim.",
            ],
        ),
    ]
    for d, key, label in [
        (dims[2], "nonzero_review_cases", "Actual correction cases"),
        (dims[2], "resolved_probe_checks", "Resolved event checks"),
        (dims[4], "research_cases", "Prospective research cases"),
        (dims[5], "research_policy_cases", "Coherent research policy cases"),
        (dims[5], "checkpoints", "Decision checkpoints"),
        (dims[5], "unique_worlds", "Unique company worlds"),
    ]:
        d.measurements.append(metric(data, "/coverage/" + key, label, "count"))
    sha = digest(raw)
    result = InvestigationPassport(
        passport_id=digest(
            json.dumps(
                ["passport/0.3.0", "passport-interpretation/0.3.0", sha], separators=(",", ":")
            ).encode()
        ),
        created_at=created_at or datetime.now(UTC),
        context=source.context,
        source=InvestigationSourceArtifact(sha256=sha),
        dimensions=dims,
        limitations=source.limitations,
        coverage=source.coverage,
        evaluation_mode=source.evaluation_mode,
        model_diagnostics=source.model_diagnostics,
    )
    for d in result.dimensions:
        for row in [*d.measurements, *d.examples]:
            for reference in row.evidence:
                pointer_value(data, reference.json_pointer)
    return result
