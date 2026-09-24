"""Versioned relationship-presentation diagnostic; original contracts stay frozen."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from epistemics.models import Model
from epistemics.participants import Digest, Participant

Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
STAGES = (
    "Background and expectations",
    "Growth evidence",
    "Same information",
    "Both events resolved",
)


class Answer(Model):
    growth_probability: Probability
    auxiliary_probability: Probability
    auxiliary_if_growth: Probability | None = None
    auxiliary_if_no_growth: Probability | None = None

    @field_validator("*")
    @classmethod
    def whole_percent(cls, value):
        if value is not None and abs(value * 100 - round(value * 100)) > 1e-8:
            raise ValueError("Use probabilities from 0 to 1 in increments of 0.01")
        return value


class Assignment(Model):
    assignment_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    quartet_id: str
    target: Literal["backlog", "source"]
    relationship: Literal["associated", "independent"]
    presentation: Literal["summary", "records"]
    evidence: Literal["audit", "signal"]
    signal_positive: bool
    growth_outcome: bool
    auxiliary_outcome: bool
    archive_seed: int = Field(ge=0, strict=True)


class ArchiveCount(Model):
    growth_above_10_percent: bool
    auxiliary_event: bool
    companies: int = Field(ge=0, strict=True)


class CompanyRecord(Model):
    company: str
    prior_revenue: int = Field(gt=0, strict=True)
    audited_revenue: int = Field(gt=0, strict=True)
    opening_backlog: int | None = Field(default=None, ge=0, strict=True)
    initial_bulletin_revenue: int | None = Field(default=None, ge=0, strict=True)

    @model_validator(mode="after")
    def one_related_measure(self):
        if (self.opening_backlog is None) == (self.initial_bulletin_revenue is None):
            raise ValueError("Each record has exactly one related measure")
        return self


class SignalCount(Model):
    growth_above_10_percent: bool
    high_reading: bool
    companies: int = Field(ge=0, strict=True)


class Trial(Model):
    schema_version: Literal["epistemics.auxiliary-trial.v2"] = "epistemics.auxiliary-trial.v2"
    battery_version: Literal["auxiliary-diagnostic/0.2.0"] = "auxiliary-diagnostic/0.2.0"
    trial_id: str
    index: int = Field(ge=0, le=3, strict=True)
    stage: str
    company: str
    instructions: str
    auxiliary_event: str
    archive_counts: list[ArchiveCount] | None = Field(default=None, min_length=4, max_length=4)
    archive_records: list[CompanyRecord] | None = Field(default=None, min_length=20, max_length=20)
    signal_history: list[SignalCount] | None = Field(default=None, min_length=4, max_length=4)
    documents: list[str]
    growth_resolved: bool | None = None
    auxiliary_resolved: bool | None = None
    request_conditionals: bool

    @model_validator(mode="after")
    def stage_valid(self):
        if self.stage != STAGES[self.index] or self.request_conditionals != (self.index == 0):
            raise ValueError("Stage and requested answers disagree")
        if (self.archive_counts is None) == (self.archive_records is None):
            raise ValueError("Expose exactly one archive presentation")
        if self.index == 0 and (
            self.growth_resolved is not None or self.signal_history is not None
        ):
            raise ValueError("No later evidence at entry")
        if (self.auxiliary_resolved is not None) != (self.index == 3):
            raise ValueError("Auxiliary resolution belongs to the last stage")
        if self.index == 3 and self.growth_resolved is None:
            raise ValueError("Final audit must resolve both events")
        if self.index in (1, 2) and (
            (self.growth_resolved is None) == (self.signal_history is None)
        ):
            raise ValueError("Present a definitive audit or an uncertain signal")
        return self


class Manifest(Model):
    schema_version: Literal["epistemics.auxiliary-collection.v2"] = (
        "epistemics.auxiliary-collection.v2"
    )
    battery_version: Literal["auxiliary-diagnostic/0.2.0"] = "auxiliary-diagnostic/0.2.0"
    evaluator_version: Literal["auxiliary-diagnostic-evaluator/0.2.0"] = (
        "auxiliary-diagnostic-evaluator/0.2.0"
    )
    study_id: str
    created_at: str
    design_seed: int = Field(ge=0, strict=True)
    implementation_sha256: Digest
    participant: Participant
    response_origin: Literal["human", "agent", "synthetic"]
    purpose: Literal["development_only"] = "development_only"
    context_policy: Literal[
        "independent_episode_no_cross_case_history", "human_continuous_separate_company_cases"
    ]
    execution_verification: Literal["operator_asserted"] = "operator_asserted"
    assignments: list[Assignment] = Field(min_length=16, max_length=16)

    @model_validator(mode="after")
    def balanced(self):
        if self.response_origin != "synthetic" and self.response_origin != self.participant.kind:
            raise ValueError("Origin must match participant")
        expected = (
            "human_continuous_separate_company_cases"
            if self.participant.kind == "human"
            else "independent_episode_no_cross_case_history"
        )
        if self.context_policy != expected:
            raise ValueError("Context policy must describe participation")
        if len({a.assignment_id for a in self.assignments}) != 16:
            raise ValueError("Duplicate assignment")
        if len({a.quartet_id for a in self.assignments}) != 4:
            raise ValueError("Expected four matched quartets")
        for target in ("backlog", "source"):
            subset = [a for a in self.assignments if a.target == target]
            for field in ("signal_positive", "growth_outcome", "auxiliary_outcome"):
                if sum(getattr(a, field) for a in subset) != 4:
                    raise ValueError("Balance directions and resolutions within each target")
            for relationship in ("associated", "independent"):
                group = [a for a in subset if a.relationship == relationship]
                if len(group) != 4 or {(a.presentation, a.evidence) for a in group} != {
                    (p, e) for p in ("summary", "records") for e in ("audit", "signal")
                }:
                    raise ValueError("Cross presentation and evidence within each world")
                shared = (
                    "quartet_id",
                    "signal_positive",
                    "growth_outcome",
                    "auxiliary_outcome",
                    "archive_seed",
                )
                if any(len({getattr(a, field) for a in group}) != 1 for field in shared):
                    raise ValueError("Matched cases must share archive, direction and resolutions")
        return self


class Observation(Model):
    trial: Trial
    answer: Answer
    answered_at: str


class Report(Model):
    schema_version: Literal["epistemics.auxiliary-report.v2"] = "epistemics.auxiliary-report.v2"
    manifest: Manifest
    manifest_sha256: Digest
    completed_at: str
    cases: dict[str, list[Observation]]
    analysis: dict
    limitations: list[str]

    @model_validator(mode="after")
    def complete_collection(self):
        from epistemics.diagnostic2.battery import public_trial

        if set(self.cases) != {a.assignment_id for a in self.manifest.assignments}:
            raise ValueError("Report must contain exactly the planned assignments")
        for a in self.manifest.assignments:
            rows = self.cases[a.assignment_id]
            if len(rows) != 4:
                raise ValueError("Every case requires four observations")
            previous = datetime.fromisoformat(self.manifest.created_at)
            for i, row in enumerate(rows):
                if row.trial != public_trial(a, i):
                    raise ValueError("Report trial differs from frozen assignment")
                if any(
                    (v is not None) != (i == 0)
                    for v in (row.answer.auxiliary_if_growth, row.answer.auxiliary_if_no_growth)
                ):
                    raise ValueError("Conditional answers do not match the checkpoint")
                current = datetime.fromisoformat(row.answered_at)
                completed = datetime.fromisoformat(self.completed_at)
                if any(t.tzinfo is None for t in (previous, current, completed)):
                    raise ValueError("Timezone required in report chronology")
                if not previous <= current <= completed:
                    raise ValueError("Invalid observation chronology")
                previous = current
        return self
