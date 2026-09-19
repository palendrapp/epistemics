"""Core passport adapter; keeps human identity and each task's measurement scope."""

import hashlib
import json
from datetime import UTC, datetime

from epistemics.live.models import CoreReport
from epistemics.passport.build import (
    dimension,
    discovery_dimensions,
    example,
    metric,
    parameter,
    pointer_value,
    refs,
    weight_description,
)
from epistemics.passport.models import CandidateSupport, CorePassport, CoreSourceArtifact


def prefix_references(dimension, prefix):
    for item in [*dimension.measurements, *dimension.examples]:
        for reference in item.evidence:
            reference.json_pointer = prefix + reference.json_pointer


def build_core_passport(raw, *, response_origin="unspecified", created_at=None):
    report = CoreReport.model_validate_json(raw)
    if response_origin not in {"unspecified", report.context.response_origin}:
        raise ValueError("Core response origin is recorded at collection and cannot be relabeled")
    data = report.model_dump(mode="json")
    dimensions = discovery_dimensions(report.discovery, data["discovery"])
    dimensions["belief_revision"].summary = (
        "The trajectory records responses to a source audit and a provenance reveal. "
        "Observer errors describe candidate explanations of these reports."
    )
    for value in dimensions.values():
        prefix_references(value, "/discovery")
    calibration = report.calibration
    index = max(
        range(24),
        key=lambda i: abs(
            calibration.observations[i].answer.probability
            - calibration.observations[i].truth["reference"]
        ),
    )
    observation = calibration.observations[index]
    evidence = dimension(
        "evidence_weighting",
        weight_description(calibration.parameters["evidence_weight"], "New evidence")
        + " "
        + weight_description(calibration.parameters["prior_weight"], "Prior information"),
        measurements=[
            parameter(calibration, "evidence_weight", "New evidence weight"),
            parameter(calibration, "prior_weight", "Prior information weight"),
        ],
        examples=[
            example(
                f"The largest calibration discrepancy: starting probability {observation.trial.stimulus['prior_h']:.0%}, "
                f"reported {observation.answer.probability:.1%}, disclosed-model reference {observation.truth['reference']:.1%}.",
                f"/observations/{index}",
            )
        ],
        limits=[
            "These weights concern the 24 disclosed-likelihood questions, not the discovery case.",
            "Arithmetic and comprehension can influence these estimates; within-run intervals are not human or agent population norms.",
        ],
    )
    prefix_references(evidence, "/calibration")
    dimensions["evidence_weighting"] = evidence
    uncertainty = dimensions["uncertainty_and_calibration"]
    uncertainty.summary = (
        "Calibration scores describe 24 numeric cases; the discovery score concerns one company outcome. "
        "These are separate task distributions, not a pooled calibration diagnosis."
    )
    uncertainty.measurements.insert(
        0,
        metric(
            data,
            "/calibration/metrics/brier",
            "Numeric-task Brier score",
            "Brier",
            reference=0,
        ),
    )
    uncertainty.measurements.insert(
        1,
        metric(
            data,
            "/calibration/metrics/reference_rmse",
            "Numeric-task reference RMSE",
            "pp",
            scale=100,
        ),
    )
    supports = []
    weight = calibration.parameters["evidence_weight"]
    if weight.estimate < 0.9995 and weight.interval_95 is not None and weight.interval_95[1] < 1:
        supports.append(
            CandidateSupport(
                dimension_id="evidence_weighting",
                hypothesis="Structured review may help integrate independent evidence; the fitted weight does not identify the cause.",
                support="Try an evidence ledger separating prior assumptions, new observations, reliability and dependencies.",
                evaluation_needed="Compare this support with baseline and generic review on fresh cases, including weak evidence and copied coverage. No benefit has been measured yet.",
                evidence=refs("/calibration/parameters/evidence_weight"),
            )
        )
    digest = hashlib.sha256(raw).hexdigest()
    identifier = hashlib.sha256(
        json.dumps(
            ["passport/0.2.0", "passport-interpretation/0.2.0", digest], separators=(",", ":")
        ).encode()
    ).hexdigest()
    result = CorePassport(
        passport_id=identifier,
        created_at=created_at or datetime.now(UTC),
        context=report.context,
        source=CoreSourceArtifact(sha256=digest),
        dimensions=list(dimensions.values()),
        support_candidates=supports,
        limitations=[
            "All core checkpoints are complete; the profile remains provisional and unsigned.",
            "Reported probabilities are behavioral observations, not direct access to internal beliefs.",
            "This import validates structure and exact source bytes, not execution or scientific correctness.",
        ]
        + report.limitations,
    )
    for value in result.dimensions:
        for item in [*value.measurements, *value.examples]:
            for reference in item.evidence:
                pointer_value(data, reference.json_pointer)
    return result
