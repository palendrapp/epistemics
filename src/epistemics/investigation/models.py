"""Public trials, immutable operator designs, and a separate private report contract."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from epistemics.company.models import Finite, Probability
from epistemics.discovery.models import Analogue, ArchiveRow
from epistemics.investigation import ANALYSIS_VERSION, BATTERY_VERSION, EVALUATOR_VERSION
from epistemics.models import Model
from epistemics.participants import Digest, Participant

Query = Literal["source_audit", "operations_check", "segment_check", "calculation", "stop"]
QUERIES = ("source_audit", "operations_check", "segment_check", "calculation", "stop")
Mode = Literal["discovery", "calibration"]
Index = Annotated[int, Field(ge=0, le=3, strict=True)]


class QueryOption(Model):
    query: Query
    description: str
    cost: Finite = Field(ge=0)


class InvestigationTrial(Model):
    schema_version: Literal["epistemics.investigation-trial.v1"] = (
        "epistemics.investigation-trial.v1"
    )
    battery_version: Literal["company-investigation/0.1.0"] = BATTERY_VERSION
    trial_id: str
    index: Index
    mode: Mode
    company: str
    instructions: str
    source_archive: list[ArchiveRow]
    analogues: list[Analogue]
    reported_growth_pct: Finite | None = None
    correction_offset_pct: Finite | None = None
    selected_query: Query | None = None
    query_result: bool | None = None
    documents: list[dict[str, str]]
    options: list[QueryOption]
    gain: Finite = Field(gt=0)
    loss: Finite = Field(gt=0)
    reference_assumptions: dict | None = None

    @model_validator(mode="after")
    def public_stage(self):
        if (self.reported_growth_pct is not None) != (self.index >= 1):
            raise ValueError("Measurement must match stage")
        if (self.correction_offset_pct is not None) != (self.index == 3):
            raise ValueError("Correction must match stage")
        if (self.selected_query is not None) != (self.index >= 2):
            raise ValueError("Research choice must match stage")
        measured = self.selected_query in QUERIES[:3]
        if (self.query_result is not None) != measured:
            raise ValueError("Only a purchased measurement has a binary result")
        if [o.query for o in self.options] != (list(QUERIES) if self.index == 1 else []):
            raise ValueError("Only stage 1 offers one of every research option")
        if self.options and self.options[-1].cost != 0:
            raise ValueError("Stopping is free")
        if (self.reference_assumptions is not None) != (self.mode == "calibration"):
            raise ValueError("Only calibration discloses observer assumptions")
        return self


class InvestigationAnswer(Model):
    growth_probability: Probability
    audit_understatement_probability: Probability
    backlog_high_probability: Probability
    decision: Literal["invest", "hold"]
    query: Query | None = None
    explanation: str | None = Field(default=None, max_length=1200)


class Assignment(Model):
    assignment_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    seed: int = Field(ge=0, strict=True)
    mode: Mode = "discovery"
    cost_scale: Finite = Field(default=1, gt=0)
    price_menu: Literal[
        "balanced", "audit_discount", "operations_discount", "segment_discount", "expensive"
    ] = "balanced"
    gain: Finite = Field(default=2, gt=0)
    loss: Finite = Field(default=1, gt=0)


class InvestigationManifest(Model):
    schema_version: Literal["epistemics.investigation.v1"] = "epistemics.investigation.v1"
    battery_version: Literal["company-investigation/0.1.0"] = BATTERY_VERSION
    evaluator_version: Literal["investigation-evaluator/0.1.0"] = EVALUATOR_VERSION
    analysis_version: Literal["investigation-analysis/0.1.0"] = ANALYSIS_VERSION
    study_id: str
    created_at: str
    implementation_sha256: Digest
    participant: Participant
    response_origin: Literal["agent", "human", "synthetic"]
    purpose: Literal["development_only"] = "development_only"
    context_policy: Literal["fresh_per_episode_continuous_within"] = (
        "fresh_per_episode_continuous_within"
    )
    execution_verification: Literal["operator_asserted"] = "operator_asserted"
    assignments: list[Assignment] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def consistent(self):
        if self.response_origin != "synthetic" and self.response_origin != self.participant.kind:
            raise ValueError("Origin must agree with participant kind")
        ids = [a.assignment_id for a in self.assignments]
        if len(set(ids)) != len(ids):
            raise ValueError("Assignment identifiers must be unique")
        return self


class InvestigationObservation(Model):
    trial: InvestigationTrial
    answer: InvestigationAnswer
    answered_at: str


class InvestigationReport(Model):
    schema_version: Literal["epistemics.investigation-report.v1"] = (
        "epistemics.investigation-report.v1"
    )
    manifest: InvestigationManifest
    manifest_sha256: Digest
    assignment: Assignment
    observations: list[InvestigationObservation] = Field(min_length=4, max_length=4)
    completed_at: str
    private_world: dict
    analysis: dict
    limitations: list[str]
