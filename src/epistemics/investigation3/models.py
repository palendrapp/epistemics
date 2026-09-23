"""Separate v2 contracts, including prospective research expectations."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from epistemics.company.models import Finite, Probability
from epistemics.discovery.models import Analogue, ArchiveRow
from epistemics.investigation.models import Mode, Query, QueryOption
from epistemics.investigation3 import ANALYSIS_VERSION, BATTERY_VERSION, EVALUATOR_VERSION
from epistemics.models import Model
from epistemics.participants import Digest, Participant

MEASUREMENTS = ("source_audit", "operations_check", "segment_check")
STAGES = ("Background", "Evidence and research", "Result and commitment", "Transcription review")


class Expectation(Model):
    yes_probability: Probability
    growth_if_yes: Probability
    growth_if_no: Probability


class Answer(Model):
    growth_probability: Probability
    audit_understatement_probability: Probability
    backlog_high_probability: Probability
    decision: Literal["invest", "hold"]
    query: Query | None = None
    expectations: (
        dict[Literal["source_audit", "operations_check", "segment_check"], Expectation] | None
    ) = None
    explanation: str | None = Field(default=None, max_length=1200)


class Assignment(Model):
    assignment_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    seed: int = Field(ge=0, strict=True)
    mode: Mode = "discovery"
    family: Literal["review", "research"]
    offset: Literal[-6, 0, 6]
    focused_query: Literal["source_audit", "operations_check", "segment_check"] | None = None
    price_condition: Literal["standard", "low", "high"] = "standard"
    pair_id: str | None = None
    selection_attempts: int = Field(default=1, ge=1)
    gain: Finite = Field(default=1, gt=0)
    loss: Finite = Field(default=1, gt=0)

    @model_validator(mode="after")
    def design(self):
        if self.family == "review":
            if self.focused_query is not None or self.pair_id or self.price_condition != "standard":
                raise ValueError("Review cases have no research matching condition")
        elif (
            self.offset != 0
            or self.focused_query is None
            or not self.pair_id
            or self.price_condition == "standard"
        ):
            raise ValueError(
                "Research cases require a pair, query and low/high price; offset is known zero"
            )
        return self


class Trial(Model):
    schema_version: Literal["epistemics.investigation-trial.v3"] = (
        "epistemics.investigation-trial.v3"
    )
    battery_version: Literal["company-investigation/0.3.0"] = BATTERY_VERSION
    trial_id: str
    index: Annotated[int, Field(ge=0, le=3, strict=True)]
    stage: str
    mode: Mode
    company: str = "Alder Systems"
    instructions: str
    source_archive: list[ArchiveRow]
    analogues: list[Analogue]
    transcription_verified_at_start: bool
    transcription_reviewed: bool
    reported_growth_pct: Finite | None = None
    correction_offset_pct: Finite | None = None
    selected_query: Query | None = None
    query_result: bool | None = None
    documents: list[dict[str, str]]
    options: list[QueryOption]
    expectation_queries: list[str]
    gain: Finite = Field(gt=0)
    loss: Finite = Field(gt=0)
    reference_assumptions: dict | None = None

    @property
    def transcription_checked(self):
        """Compatibility accessor for the frozen world observer: verified at entry."""
        return self.transcription_verified_at_start

    @model_validator(mode="after")
    def public_stage(self):
        if self.transcription_reviewed != (self.index == 3):
            raise ValueError("Review status must match the current stage")
        if self.stage != STAGES[self.index]:
            raise ValueError("Stage name must match index")
        if (self.reported_growth_pct is not None) != (self.index >= 1):
            raise ValueError("Measurement must match stage")
        if (self.correction_offset_pct is not None) != (self.index == 3):
            raise ValueError("Review must match stage")
        if self.transcription_verified_at_start and self.correction_offset_pct not in (None, 0):
            raise ValueError("Previously checked transcription stays zero")
        if (self.selected_query is not None) != (self.index >= 2):
            raise ValueError("Research choice must match stage")
        if (self.query_result is not None) != (self.selected_query in MEASUREMENTS):
            raise ValueError("Only the purchased measurement has a result")
        if [o.query for o in self.options] != (
            [*MEASUREMENTS, "calculation", "stop"] if self.index == 1 else []
        ):
            raise ValueError("Only the evidence stage offers research")
        if self.expectation_queries != (
            list(MEASUREMENTS) if self.index == 1 and self.transcription_verified_at_start else []
        ):
            raise ValueError("Prospective expectations belong to research cases only")
        if (self.reference_assumptions is not None) != (self.mode == "calibration"):
            raise ValueError("Only calibration discloses likelihoods")
        return self


class Manifest(Model):
    schema_version: Literal["epistemics.investigation.v3"] = "epistemics.investigation.v3"
    battery_version: Literal["company-investigation/0.3.0"] = BATTERY_VERSION
    evaluator_version: Literal["investigation-evaluator/0.3.0"] = EVALUATOR_VERSION
    analysis_version: Literal["investigation-analysis/0.3.0"] = ANALYSIS_VERSION
    study_id: str
    created_at: str
    implementation_sha256: Digest
    participant: Participant
    response_origin: Literal["agent", "human", "synthetic"]
    purpose: Literal["development_only"] = "development_only"
    context_policy: Literal[
        "independent_episode_no_cross_case_history", "human_continuous_separate_company_cases"
    ]
    execution_verification: Literal["operator_asserted"] = "operator_asserted"
    assignments: list[Assignment] = Field(min_length=12, max_length=12)

    @model_validator(mode="after")
    def balanced(self):
        if self.response_origin != "synthetic" and self.response_origin != self.participant.kind:
            raise ValueError("Origin must match participant")
        expected_context = (
            "human_continuous_separate_company_cases"
            if self.participant.kind == "human"
            else "independent_episode_no_cross_case_history"
        )
        if self.context_policy != expected_context:
            raise ValueError("Context policy must describe the participant interface")
        if len({a.assignment_id for a in self.assignments}) != 12:
            raise ValueError("Assignment identifiers must be unique")
        review = [a for a in self.assignments if a.family == "review"]
        if sorted(a.offset for a in review) != [-6, -6, 0, 0, 6, 6]:
            raise ValueError("Review cases must balance all three offsets")
        for query in MEASUREMENTS:
            pair = [a for a in self.assignments if a.focused_query == query]
            if len(pair) != 2 or {a.price_condition for a in pair} != {"low", "high"}:
                raise ValueError("Each research option needs a low/high matched pair")
            if any(
                getattr(pair[0], k) != getattr(pair[1], k)
                for k in ("seed", "pair_id", "mode", "gain", "loss")
            ):
                raise ValueError("Matched cases differ only in price and assignment identifier")
        return self


class Observation(Model):
    trial: Trial
    answer: Answer
    answered_at: str


class Report(Model):
    schema_version: Literal["epistemics.investigation-report.v3"] = (
        "epistemics.investigation-report.v3"
    )
    manifest: Manifest
    manifest_sha256: Digest
    assignment: Assignment
    observations: list[Observation] = Field(min_length=4, max_length=4)
    completed_at: str
    private_world: dict
    analysis: dict
    limitations: list[str]
