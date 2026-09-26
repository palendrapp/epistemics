"""Passport contracts are additive; signed legacy report bytes remain untouched."""

from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from epistemics.models import Model
from epistemics.participants import Digest, SessionContext

DimensionId = Literal[
    "evidence_weighting",
    "source_judgment",
    "belief_revision",
    "dependence_and_causal_reasoning",
    "uncertainty_and_calibration",
    "decision_consistency",
]
DIMENSIONS = {
    "evidence_weighting": "Evidence weighting",
    "source_judgment": "Source judgment",
    "belief_revision": "Belief revision",
    "dependence_and_causal_reasoning": "Dependence and causal reasoning",
    "uncertainty_and_calibration": "Uncertainty and calibration",
    "decision_consistency": "Decision consistency",
}


class EvidenceReference(Model):
    artifact_id: Literal["source-report"] = "source-report"
    json_pointer: str = Field(pattern=r"^/")


class Measurement(Model):
    label: str
    value: float
    unit: str
    reference: float | None = None
    interval_95: tuple[float, float] | None = None
    method: str
    evidence: list[EvidenceReference] = Field(min_length=1)
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def interval_order(self):
        if self.interval_95 is not None and self.interval_95[0] > self.interval_95[1]:
            raise ValueError("Interval endpoints must be ordered")
        return self


class ObservationExample(Model):
    description: str
    evidence: list[EvidenceReference] = Field(min_length=1)


class Dimension(Model):
    dimension_id: DimensionId
    title: str
    evidence_status: Literal["provisional", "insufficient_evidence"]
    summary: str
    measurements: list[Measurement] = Field(default_factory=list)
    examples: list[ObservationExample] = Field(default_factory=list)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def observed(self):
        if self.evidence_status == "provisional" and not (self.measurements or self.examples):
            raise ValueError("A provisional dimension needs observations")
        return self


class CandidateSupport(Model):
    dimension_id: DimensionId
    status: Literal["untested"] = "untested"
    hypothesis: str
    support: str
    evaluation_needed: str
    evidence: list[EvidenceReference] = Field(min_length=1)


class SourceArtifact(Model):
    artifact_id: Literal["source-report"] = "source-report"
    schema_version: Literal["epistemics.report.v1", "epistemics.report.v2", "epistemics.report.v3"]
    sha256: Digest
    access: Literal["private_local"] = "private_local"
    validation: Literal["schema_only_not_execution_verified"] = "schema_only_not_execution_verified"


class Passport(Model):
    schema_version: Literal["epistemics.passport.v1"] = "epistemics.passport.v1"
    passport_version: Literal["passport/0.1.0"] = "passport/0.1.0"
    interpretation_version: Literal["passport-interpretation/0.1.0"] = (
        "passport-interpretation/0.1.0"
    )
    passport_id: Digest
    created_at: AwareDatetime
    issuance_status: Literal["draft_unsigned"] = "draft_unsigned"
    scope: Literal["single_report_partial_profile"] = "single_report_partial_profile"
    context: SessionContext
    source: SourceArtifact
    dimensions: list[Dimension] = Field(min_length=6, max_length=6)
    support_candidates: list[CandidateSupport] = Field(default_factory=list)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_dimensions(self):
        if [d.dimension_id for d in self.dimensions] != list(DIMENSIONS):
            raise ValueError("Include each of the six dimensions once, in canonical order")
        if self.context.completion != "complete":
            raise ValueError("This importer requires a completed source evaluation")
        return self


class CoreSourceArtifact(SourceArtifact):
    schema_version: Literal["epistemics.report.v4"] = "epistemics.report.v4"


class CorePassport(Passport):
    schema_version: Literal["epistemics.passport.v2"] = "epistemics.passport.v2"
    passport_version: Literal["passport/0.2.0"] = "passport/0.2.0"
    interpretation_version: Literal["passport-interpretation/0.2.0"] = (
        "passport-interpretation/0.2.0"
    )
    scope: Literal["core_battery_provisional_profile"] = "core_battery_provisional_profile"
    source: CoreSourceArtifact


class InvestigationSourceArtifact(SourceArtifact):
    schema_version: Literal["epistemics.investigation-collection.v1"] = (
        "epistemics.investigation-collection.v1"
    )


class InvestigationDiagnostics(Model):
    analysis_version: str
    parameters_are_validated_traits: Literal[False] = False
    empirical_predictive_validation: Literal[False] = False
    intervention_benefit_tested: Literal[False] = False
    fits: dict[str, dict]


class InvestigationPassport(Passport):
    schema_version: Literal["epistemics.passport.v3"] = "epistemics.passport.v3"
    passport_version: Literal["passport/0.3.0"] = "passport/0.3.0"
    interpretation_version: Literal["passport-interpretation/0.3.0"] = (
        "passport-interpretation/0.3.0"
    )
    scope: Literal["investigation_battery_provisional_profile"] = (
        "investigation_battery_provisional_profile"
    )
    source: InvestigationSourceArtifact
    evaluation_mode: Literal["discovery", "calibration"]
    coverage: dict[str, int]
    model_diagnostics: InvestigationDiagnostics

    @model_validator(mode="after")
    def investigation_scope(self):
        if self.context.accepted_answers != 48 or self.context.planned_answers != 48:
            raise ValueError("An investigation passport requires all 48 checkpoints")
        return self


def read_passport(raw: bytes) -> Passport:
    import json

    data = json.loads(raw)
    contract = {
        "epistemics.passport.v2": CorePassport,
        "epistemics.passport.v3": InvestigationPassport,
        "epistemics.passport.v4": SourcePassport,
    }.get(data.get("schema_version"), Passport)
    return contract.model_validate(data)


class SourceLearningArtifact(SourceArtifact):
    schema_version: Literal["epistemics.source-evidence.v1"] = "epistemics.source-evidence.v1"


class SourceDiagnostics(Model):
    analysis_version: Literal["source-passport-diagnostics/0.1.0"] = (
        "source-passport-diagnostics/0.1.0"
    )
    parameters_are_validated_traits: Literal[False] = False
    personalized_prediction_validated: Literal[False] = False
    intervention_benefit_tested: Literal[False] = False
    fits: dict[str, dict]


class SourcePassport(Passport):
    schema_version: Literal["epistemics.passport.v4"] = "epistemics.passport.v4"
    passport_version: Literal["passport/0.4.0"] = "passport/0.4.0"
    interpretation_version: Literal["passport-interpretation/0.4.0"] = (
        "passport-interpretation/0.4.0"
    )
    scope: Literal["source_learning_provisional_profile"] = "source_learning_provisional_profile"
    source: SourceLearningArtifact
    subject_binding: Literal["single_subject", "configuration_cohort"]
    source_subject_ids: list[str] = Field(min_length=1, max_length=64)
    presentation: Literal["structured", "packet", "unverified"]
    condition: Literal["sparse", "dense"]
    coverage: dict[str, int]
    repeatability: list[dict]
    model_diagnostics: SourceDiagnostics

    @model_validator(mode="after")
    def source_scope(self):
        n = self.coverage.get("sessions", 0)
        if (
            not 1 <= n <= 64
            or self.context.accepted_answers != 36 * n
            or self.context.planned_answers != 36 * n
        ):
            raise ValueError("Source passport requires complete sessions")
        if self.subject_binding == "single_subject" and self.source_subject_ids != [
            self.context.participant.subject_id
        ]:
            raise ValueError("Single subject binding differs")
        if self.subject_binding == "configuration_cohort" and (
            len(set(self.source_subject_ids)) < 2 or self.context.participant.kind != "agent"
        ):
            raise ValueError("A configuration cohort requires multiple agent session identities")
        return self
