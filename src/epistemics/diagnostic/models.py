from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from epistemics.models import Model
from epistemics.participants import Digest, Participant

Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
STAGES = (
    "Background and expectations",
    "Growth resolved",
    "Same information",
    "Auxiliary resolved",
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
    pair_id: str
    target: Literal["backlog", "source"]
    relationship: Literal["associated", "independent"]
    growth_outcome: bool
    auxiliary_outcome: bool


class Trial(Model):
    schema_version: Literal["epistemics.auxiliary-trial.v1"] = "epistemics.auxiliary-trial.v1"
    battery_version: Literal["auxiliary-diagnostic/0.1.0"] = "auxiliary-diagnostic/0.1.0"
    trial_id: str
    index: int = Field(ge=0, le=3, strict=True)
    stage: str
    company: str
    instructions: str
    auxiliary_event: str
    archive: list[dict[str, int | bool]]
    documents: list[str]
    growth_resolved: bool | None = None
    auxiliary_resolved: bool | None = None
    request_conditionals: bool

    @model_validator(mode="after")
    def stage_valid(self):
        if self.stage != STAGES[self.index] or self.request_conditionals != (self.index == 0):
            raise ValueError("Stage and requested answers disagree")
        if (self.growth_resolved is not None) != (self.index >= 1):
            raise ValueError("Growth resolution belongs to stages 1 onward")
        if (self.auxiliary_resolved is not None) != (self.index == 3):
            raise ValueError("Auxiliary resolution belongs to the last stage")
        return self


class Manifest(Model):
    schema_version: Literal["epistemics.auxiliary-collection.v1"] = (
        "epistemics.auxiliary-collection.v1"
    )
    battery_version: Literal["auxiliary-diagnostic/0.1.0"] = "auxiliary-diagnostic/0.1.0"
    evaluator_version: Literal["auxiliary-diagnostic-evaluator/0.1.0"] = (
        "auxiliary-diagnostic-evaluator/0.1.0"
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
    assignments: list[Assignment] = Field(min_length=8, max_length=8)

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
        if len({a.assignment_id for a in self.assignments}) != 8:
            raise ValueError("Duplicate assignment")
        if len({a.pair_id for a in self.assignments}) != 4:
            raise ValueError("Expected four matched pairs")
        for target in ("backlog", "source"):
            for growth in (False, True):
                pair = [
                    a for a in self.assignments if a.target == target and a.growth_outcome == growth
                ]
                if len(pair) != 2 or {a.relationship for a in pair} != {
                    "associated",
                    "independent",
                }:
                    raise ValueError("Balance target, relationship and evidence direction")
                if (
                    pair[0].pair_id != pair[1].pair_id
                    or pair[0].auxiliary_outcome != pair[1].auxiliary_outcome
                ):
                    raise ValueError("Matched cases share both resolutions")
        return self


class Observation(Model):
    trial: Trial
    answer: Answer
    answered_at: str


class Report(Model):
    schema_version: Literal["epistemics.auxiliary-report.v1"] = "epistemics.auxiliary-report.v1"
    manifest: Manifest
    manifest_sha256: Digest
    completed_at: str
    cases: dict[str, list[Observation]]
    analysis: dict
    limitations: list[str]

    @model_validator(mode="after")
    def complete_collection(self):
        from epistemics.diagnostic.battery import public_trial

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
