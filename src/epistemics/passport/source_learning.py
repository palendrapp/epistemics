"""Exact-byte, homogeneous source-learning evidence; no inferred deployment identity."""

import json
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from epistemics.models import Model
from epistemics.participants import Digest, EvaluationConditions, SessionContext
from epistemics.source_learning.battery import generate, public_trial
from epistemics.source_learning.inference import analyze, calibrate, forecast, raw_predictions
from epistemics.source_learning.models import Report
from epistemics.source_learning.storage import digest, encoded, save


class SourceSession(Model):
    report_json: str
    report_sha256: Digest
    transport_json: str | None = None
    transport_sha256: Digest | None = None

    @model_validator(mode="after")
    def bytes_match(self):
        if digest(self.report_json.encode()) != self.report_sha256:
            raise ValueError("Embedded report hash mismatch")
        if (self.transport_json is None) != (self.transport_sha256 is None) or (
            self.transport_json is not None
            and digest(self.transport_json.encode()) != self.transport_sha256
        ):
            raise ValueError("Embedded transport hash mismatch")
        return self


class SourceCollection(Model):
    schema_version: Literal["epistemics.source-evidence.v1"] = "epistemics.source-evidence.v1"
    context: SessionContext
    subject_binding: Literal["single_subject", "configuration_cohort"]
    source_subject_ids: list[str]
    presentation: Literal["structured", "packet", "unverified"]
    condition: Literal["sparse", "dense"]
    sessions: list[SourceSession] = Field(min_length=1, max_length=64)
    facts: dict[str, float | None]
    coverage: dict[str, int]
    repeatability: list[dict]
    diagnostics: dict[str, dict]
    limitations: list[str]


def validate_report(source):
    report = Report.model_validate_json(source.report_json)
    m = report.manifest
    if generate(m.design_seed) != (m.sources, m.archive, m.companies):
        raise ValueError("Source world differs from its frozen design")
    answers = [o.answer for o in report.observations]
    for i, lock in enumerate(report.prediction_locks):
        raw = raw_predictions(m, i, answers[:i])
        if lock["raw"] != raw or lock["trial_sha256"] != digest(
            encoded(report.observations[i].trial)
        ):
            raise ValueError("Source predictions differ from public history")
        if i >= 12 and (
            lock["forecast"] != forecast(raw, report.fit_lock["fit"])
            or lock["fit_sha256"] != digest(encoded(report.fit_lock))
        ):
            raise ValueError("Later predictions differ from frozen fit")
    if report.fit_lock["fit"] != calibrate(report.prediction_locks[:12], answers[:12]):
        raise ValueError("Calibration fit changed")
    calibration_rows = []
    for i, observation in enumerate(report.observations[:12]):
        calibration_rows.append(
            {
                "answer": observation.answer.model_dump(mode="json"),
                "answered_at": observation.answered_at.isoformat(),
                "receipt": {
                    "accepted": True,
                    "trial_id": observation.trial.trial_id,
                    "answered": i + 1,
                    "complete": False,
                    "prediction_sha256": observation.prediction_sha256,
                },
            }
        )
    if digest(encoded(calibration_rows)) != report.fit_lock["calibration_answers_sha256"]:
        raise ValueError("Calibration answer bytes changed")
    calculated = analyze(m, report.observations, report.prediction_locks, report.fit_lock["fit"])
    if report.analysis != calculated:
        raise ValueError("Imported analysis differs from reconstructed report")
    return report


def transport_scope(report, source):
    if source.transport_json is None:
        return (
            "unverified",
            "source-delivery-unverified/0.1.0",
            report.manifest.implementation_sha256,
        )
    evidence = json.loads(source.transport_json)
    if evidence.get("schema_version") == "epistemics.source-delivery-evidence.v1":
        from epistemics.source_delivery.service import verify_evidence

        b = verify_evidence(report, evidence)
        return b["presentation"], b["version"], b["implementation_sha256"]
    if evidence.get("schema_version") != "epistemics.source-panel-evidence.v1":
        raise ValueError("Unsupported source transport evidence")
    from epistemics.source_panel.presentation import present
    from epistemics.source_panel.profiles import predictions

    b = evidence["binding"]
    if (
        b["schema_version"] != "epistemics.source-panel-binding.v1"
        or b["version"] != "source-panel/0.1.0"
        or b["base_manifest_sha256"] != report.manifest_sha256
        or evidence["binding_sha256"] != digest(encoded(b))
        or len(evidence["locks"]) != 36
        or datetime.fromisoformat(evidence["completed_at"]) != report.completed_at
    ):
        raise ValueError("Panel evidence binding differs")
    for i, (o, base, lock) in enumerate(
        zip(report.observations, report.prediction_locks, evidence["locks"], strict=True)
    ):
        public = present(
            public_trial(report.manifest, i, [x.answer for x in report.observations[:i]]),
            b["presentation"],
        )
        pred = (
            predictions(base["raw"], b["profiles"], o.trial.prior_strong)
            if b["profiles"] is not None
            else None
        )
        if (
            lock["public_trial"] != public
            or lock["public_trial_sha256"] != digest(encoded(public))
            or lock["binding_sha256"] != evidence["binding_sha256"]
            or lock["prediction"] != pred
            or not report.manifest.created_at
            <= datetime.fromisoformat(b["created_at"])
            <= datetime.fromisoformat(lock["locked_at"])
            <= o.answered_at
            or (
                b["profiles"] is not None
                and (
                    b["profile_frozen_at"] is None
                    or datetime.fromisoformat(b["profile_frozen_at"])
                    > datetime.fromisoformat(b["created_at"])
                )
            )
        ):
            raise ValueError("Panel presentation, prediction or chronology differs")
    version = "source-packets/0.1.0" if b["presentation"] == "packet" else "source-learning/0.1.0"
    if b["presentation_version"] != version:
        raise ValueError("Incorrect panel presentation version")
    return b["presentation"], version, b["implementation_sha256"]


def derive(sessions):
    if not 1 <= len(sessions) <= 64:
        raise ValueError("Provide one to 64 complete sessions")
    reports = [validate_report(s) for s in sessions]
    if len({r.manifest.study_id for r in reports}) != len(reports):
        raise ValueError("A session cannot be counted twice")
    first = reports[0].manifest
    scopes = [transport_scope(r, s) for r, s in zip(reports, sessions, strict=True)]
    subject_ids = sorted({r.manifest.participant.subject_id for r in reports})
    binding = "single_subject" if len(subject_ids) == 1 else "configuration_cohort"
    for r, scope in zip(reports, scopes, strict=True):
        m = r.manifest
        if (
            m.condition != first.condition
            or m.response_origin != first.response_origin
            or m.participant.kind != first.participant.kind
            or scope != scopes[0]
            or m.battery_version != first.battery_version
            or m.evaluator_version != first.evaluator_version
            or m.implementation_sha256 != first.implementation_sha256
            or (
                m.participant.kind == "agent"
                and m.participant.configuration != first.participant.configuration
            )
            or (m.participant.kind == "human" and m.participant != first.participant)
        ):
            raise ValueError(
                "Cannot pool different configurations, humans, origins, protocols or conditions"
            )
    participant = first.participant.model_copy(deep=True)
    if binding == "configuration_cohort":
        participant.subject_id = "configuration:" + digest(encoded(participant.configuration))
    n = len(reports)
    groups = {}
    for i, r in enumerate(reports):
        world = digest(
            encoded(
                [
                    r.manifest.model_dump(mode="json")[key]
                    for key in ("sources", "archive", "companies")
                ]
            )
        )
        groups.setdefault(world, []).append(i)
    differences, repeats = [], []
    for world_number, indices in enumerate(groups.values(), 1):
        errors = []
        for a, b in combinations(indices, 2):
            # Only the twelve unaudited forecasts have identical evidence across paths.
            delta = np.array(
                [o.answer.probability for o in reports[a].observations[:12]]
            ) - np.array([o.answer.probability for o in reports[b].observations[:12]])
            differences.extend(delta.tolist())
            errors.append({"sessions": [a, b], "rmse_pp": float(100 * np.sqrt(np.mean(delta**2)))})
        if errors:
            repeats.append({"world_number": world_number, "pairs": errors})
    analyses = [r.analysis for r in reports]
    brier = [x["brier"] for a in analyses for x in a["final_outcome_scores"]]
    decisions = sum(a["decision_consistency"]["consistent"] for a in analyses)
    research = {
        q: sum(a["research_counts"][q] for a in analyses)
        for q in ("customer_panel", "selection_audit", "measurement_audit", "stop")
    }
    facts = {
        "decision_agreement_percent": 100 * decisions / (36 * n),
        "final_brier": float(np.mean(brier)),
        "mean_payoff_per_company": sum(a["total_realized_payoff"] for a in analyses) / (24 * n),
        "repeat_rmse_pp": float(100 * np.sqrt(np.mean(np.array(differences) ** 2)))
        if differences
        else None,
        **{"research_" + q + "_percent": 100 * value / (12 * n) for q, value in research.items()},
    }
    coverage = {
        "sessions": n,
        "unique_worlds": len(groups),
        "companies": 24 * n,
        "checkpoints": 36 * n,
        "research_choices": 12 * n,
        "source_judgments": 48 * n if first.condition == "dense" else 0,
        "repeat_pairs": len(differences) // 12,
        "repeat_worlds": len(repeats),
        "matched_forecasts_per_pair": 12 if repeats else 0,
    }
    context = SessionContext(
        session_id=digest(encoded([s.report_sha256 for s in sessions])),
        participant=participant,
        response_origin=first.response_origin,
        protocol_version=scopes[0][1],
        protocol_sha256=scopes[0][2],
        evaluator_version=first.evaluator_version,
        conditions=EvaluationConditions(
            interface="unspecified", context_policy=first.context_policy
        ),
        started_at=min(r.manifest.created_at for r in reports),
        completed_at=max(r.completed_at for r in reports),
        completion="complete",
        accepted_answers=36 * n,
        planned_answers=36 * n,
    )
    return SourceCollection(
        context=context,
        subject_binding=binding,
        source_subject_ids=subject_ids,
        presentation=scopes[0][0],
        condition=first.condition,
        sessions=sessions,
        facts=facts,
        coverage=coverage,
        repeatability=repeats,
        diagnostics={
            f"session-{i + 1}": {
                "calibration_family": r.fit_lock["fit"]["decision"],
                "heldout_behavior_rmse_pp": r.analysis["heldout_behavior_rmse_pp"],
                "conditional_adequacy": r.analysis["conditional_adequacy"],
                "all_candidates_inadequate": r.analysis["all_candidates_inadequate"],
            }
            for i, r in enumerate(reports)
        },
        limitations=[
            "Probabilities are elicited reports; no internal mechanism, stable trait or population norm is established.",
            "Configuration-cohort grouping is an operator assertion across the listed source subject IDs; it does not identify a deployed agent or transfer controller authority.",
            "Only same-condition, same-presentation, same-declared-configuration sessions are pooled. Original subject IDs and exact source bytes are retained.",
            "Repeat comparisons use twelve matched unaudited forecasts. Pairs sharing a session or world are dependent; no population confidence interval is claimed.",
            "Final Brier and fictional payoff depend on the generated worlds and selected research; model error is not a decision-quality ranking.",
            "Research frequencies are descriptions, not optimality scores or measured verification benefit. Earlier menus may leave research semantics unclear.",
            "Model diagnostics concern within-session fits and later reports. They do not certify external transfer, personalized prediction or support benefit.",
            "Transport evidence reconstructs served content, not independent execution or model identity. Interface is unspecified because transport type alone cannot attest browser versus MCP use.",
            "Single-session evidence has no repeatability estimate. Unknown presentation remains explicit and is not qualified for machine policy acceptance.",
            "Raw sources contain private evaluator worlds and answers. Keep them private; the passport contains aggregates and evidence references.",
        ],
    )


def bundle(directories):
    sessions = []
    for directory in directories:
        directory = Path(directory)
        raw = (directory / "report.json").read_bytes()
        if (directory / "report.sha256").read_text().strip() != digest(raw):
            raise ValueError("Report byte hash mismatch")
        candidates = [
            directory / name
            for name in ("delivery-evidence.json", "panel-evidence.json")
            if (directory / name).exists()
        ]
        if len(candidates) > 1:
            raise ValueError("Ambiguous transport evidence")
        # A bound collection cannot silently lose its transport evidence during bundling.
        if not candidates and any(
            (directory / name).exists() for name in ("delivery-binding.json", "panel-binding.json")
        ):
            raise ValueError("Export bound transport evidence before bundling")
        transport = candidates[0].read_bytes() if candidates else None
        sessions.append(
            SourceSession(
                report_json=raw.decode(),
                report_sha256=digest(raw),
                transport_json=transport.decode() if transport else None,
                transport_sha256=digest(transport) if transport else None,
            )
        )
    return derive(sessions)


def build_source_passport(raw, *, response_origin="unspecified", created_at=None):
    from epistemics.passport.build import dimension, empty_dimensions, metric
    from epistemics.passport.models import SourceDiagnostics, SourceLearningArtifact, SourcePassport

    source = SourceCollection.model_validate_json(raw)
    if source != derive(source.sessions):
        raise ValueError("Source facts, grouping or context differ from original evidence")
    if response_origin not in ("unspecified", source.context.response_origin):
        raise ValueError("Recorded source origin cannot be relabeled")
    data = source.model_dump(mode="json")
    dims = empty_dimensions()
    for d in dims.values():
        d.limitations = [
            "This source-learning collection does not contain a dedicated contrast that identifies this dimension."
        ]

    def m(key, label, unit):
        return metric(data, "/facts/" + key, label, unit)

    dims["decision_consistency"] = dimension(
        "decision_consistency",
        f"Actions agreed with reported probabilities and payoff thresholds at {source.facts['decision_agreement_percent']:.1f}% of {source.coverage['checkpoints']} checkpoints across {source.coverage['sessions']} sessions.",
        measurements=[
            m("decision_agreement_percent", "Decision/report agreement", "%"),
            m("mean_payoff_per_company", "Mean fictional payoff per company", "points"),
        ]
        + [
            metric(data, "/coverage/" + key, label, "count")
            for key, label in [
                ("checkpoints", "Decision checkpoints"),
                ("companies", "Completed companies"),
                ("sessions", "Recorded sessions"),
                ("unique_worlds", "Distinct generated worlds"),
            ]
        ],
        limits=[
            "Report/action consistency is separate from forecast accuracy, real returns and buyer utility."
        ],
    )
    uncertainty = [m("final_brier", "Final outcome Brier", "Brier")]
    if source.facts["repeat_rmse_pp"] is not None:
        uncertainty.append(m("repeat_rmse_pp", "Matched repeat forecast difference", "pp"))
    uncertainty += [
        metric(data, "/coverage/" + key, label, "count")
        for key, label in [
            ("repeat_pairs", "Matched repeat pairs"),
            ("repeat_worlds", "Worlds with repeats"),
            ("matched_forecasts_per_pair", "Matched forecasts per pair"),
        ]
    ]
    repeat_summary = (
        f"Repeated forecasts differed by {source.facts['repeat_rmse_pp']:.2f} probability points RMS across {source.coverage['repeat_pairs']} matched pairs in {source.coverage['repeat_worlds']} worlds."
        if source.facts["repeat_rmse_pp"] is not None
        else "No matched repeated sessions are available; repeatability is unmeasured."
    )
    dims["uncertainty_and_calibration"] = dimension(
        "uncertainty_and_calibration",
        repeat_summary
        + f" Final forecasts had a Brier score of {source.facts['final_brier']:.3f} across {source.coverage['companies']} company evaluations (lower is better).",
        measurements=uncertainty,
        limits=[
            "No general calibration, confidence trait or population reliability coefficient is inferred. Repeated worlds and overlapping pairs are dependent."
        ],
    )
    dims["source_judgment"] = dimension(
        "source_judgment",
        f"Across {source.coverage['research_choices']} research choices, independent customer checks were selected {source.facts['research_customer_panel_percent']:.1f}% of the time, selection audits {source.facts['research_selection_audit_percent']:.1f}%, measurement audits {source.facts['research_measurement_audit_percent']:.1f}%, and no further research {source.facts['research_stop_percent']:.1f}%.",
        measurements=[
            m("research_" + q + "_percent", label, "%")
            for q, label in [
                ("customer_panel", "Independent customer panel selected"),
                ("selection_audit", "Selection audit selected"),
                ("measurement_audit", "Measurement audit selected"),
                ("stop", "Stopped research"),
            ]
        ]
        + [
            metric(data, "/coverage/research_choices", "Research choices", "count"),
            metric(data, "/coverage/source_judgments", "Explicit source judgments", "count"),
        ],
        limits=[
            "Research frequency does not identify source sensitivity or rationality. Audits may benefit later companies."
        ],
    )
    return SourcePassport(
        passport_id=digest(encoded(["passport/0.4.0", digest(raw)])),
        created_at=created_at or datetime.now(UTC),
        context=source.context,
        source=SourceLearningArtifact(sha256=digest(raw)),
        dimensions=list(dims.values()),
        limitations=source.limitations,
        subject_binding=source.subject_binding,
        source_subject_ids=source.source_subject_ids,
        presentation=source.presentation,
        condition=source.condition,
        coverage=source.coverage,
        repeatability=source.repeatability,
        model_diagnostics=SourceDiagnostics(fits=source.diagnostics),
    )


def export_bundle(directories, output):
    raw = encoded(bundle(directories))
    Path(output).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    save(output, raw)
    return raw
