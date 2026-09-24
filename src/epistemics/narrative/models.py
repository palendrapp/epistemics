"""Independent versioned contract; previous evaluations remain frozen."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from epistemics.models import Model
from epistemics.participants import Digest, Participant

Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Query = Literal["demand_audit", "pipeline_audit", "stop"]
STATES = ("demand_only", "artifact_only", "both", "neither")
STAGES = ("Background and predictions", "Dashboard arrives", "Your research result", "Final audit")


class StateValues(Model):
    demand_only: Probability
    artifact_only: Probability
    both: Probability
    neither: Probability

    @field_validator("*")
    @classmethod
    def whole_percent(cls, value):
        if abs(value * 100 - round(value * 100)) > 1e-8:
            raise ValueError("Use probabilities from 0 to 1 in increments of 0.01")
        return value

    def vector(self):
        return [getattr(self, key) for key in STATES]


class Joint(StateValues):
    @model_validator(mode="after")
    def sums_to_one(self):
        if abs(sum(self.vector()) - 1) > 1e-8:
            raise ValueError("Joint state probabilities must sum to 1 (100%)")
        return self


class Answer(Model):
    joint: Joint
    signal_if_state: StateValues | None = None
    query: Query | None = None

    def validate_stage(self, index):
        if (self.signal_if_state is not None) != (index == 0):
            raise ValueError("Four signal forecasts are required at the first checkpoint only")
        if (self.query is not None) != (index == 1):
            raise ValueError("A research choice is required at the second checkpoint only")


class Assignment(Model):
    assignment_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    pair_id: str
    domain: Literal["subscriptions", "distributor"]
    direction: Literal["rise", "fall"]
    presentation: Literal["narrative", "facts"]
    demand_outcome: bool
    artifact_outcome: bool


class Trial(Model):
    schema_version: Literal["epistemics.narrative-trial.v1"] = "epistemics.narrative-trial.v1"
    battery_version: Literal["narrative-inference/0.1.0"] = "narrative-inference/0.1.0"
    trial_id: str
    index: int = Field(ge=0, le=3, strict=True)
    stage: str
    company: str
    instructions: str
    demand_event: str
    artifact_event: str
    signal_event: str
    new_documents: list[str] = Field(min_length=1)
    request_signal_forecasts: bool
    request_query: bool
    selected_query: Query | None = None
    demand_resolved: bool | None = None
    artifact_resolved: bool | None = None

    @model_validator(mode="after")
    def boundaries(self):
        if self.stage != STAGES[self.index]:
            raise ValueError("Invalid stage label")
        if self.request_signal_forecasts != (self.index == 0) or self.request_query != (
            self.index == 1
        ):
            raise ValueError("Requested answers disagree with checkpoint")
        if (self.selected_query is not None) != (self.index >= 2):
            raise ValueError("Research choice appears only after acceptance")
        for event, query in (("demand", "demand_audit"), ("artifact", "pipeline_audit")):
            expected = self.index == 3 or (self.index == 2 and self.selected_query == query)
            if (getattr(self, event + "_resolved") is not None) != expected:
                raise ValueError("Reveal only the selected audit until the final checkpoint")
        return self


class Manifest(Model):
    schema_version: Literal["epistemics.narrative-collection.v1"] = (
        "epistemics.narrative-collection.v1"
    )
    battery_version: Literal["narrative-inference/0.1.0"] = "narrative-inference/0.1.0"
    evaluator_version: Literal["narrative-evaluator/0.1.0"] = "narrative-evaluator/0.1.0"
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
        truths = []
        for domain in ("subscriptions", "distributor"):
            for direction in ("rise", "fall"):
                group = [
                    a for a in self.assignments if (a.domain, a.direction) == (domain, direction)
                ]
                if len(group) != 2 or {a.presentation for a in group} != {"narrative", "facts"}:
                    raise ValueError("Cross domain, direction and presentation")
                for key in ("pair_id", "demand_outcome", "artifact_outcome"):
                    if len({getattr(a, key) for a in group}) != 1:
                        raise ValueError("Matched pairs must share facts and resolutions")
                truths.append((group[0].demand_outcome, group[0].artifact_outcome))
        if len(set(truths)) != 4:
            raise ValueError("Balance the four final event combinations")
        return self


class Observation(Model):
    trial: Trial
    answer: Answer
    answered_at: str


class Report(Model):
    schema_version: Literal["epistemics.narrative-report.v1"] = "epistemics.narrative-report.v1"
    manifest: Manifest
    manifest_sha256: Digest
    completed_at: str
    cases: dict[str, list[Observation]]
    analysis: dict
    limitations: list[str]

    @model_validator(mode="after")
    def complete_collection(self):
        from epistemics.narrative.battery import public_trial

        if set(self.cases) != {a.assignment_id for a in self.manifest.assignments}:
            raise ValueError("Report must contain exactly the planned assignments")
        completed = datetime.fromisoformat(self.completed_at)
        for a in self.manifest.assignments:
            rows = self.cases[a.assignment_id]
            if len(rows) != 4:
                raise ValueError("Every case requires four observations")
            previous = datetime.fromisoformat(self.manifest.created_at)
            for i, row in enumerate(rows):
                query = rows[1].answer.query if i >= 2 else None
                if row.trial != public_trial(a, i, query):
                    raise ValueError(
                        "Report trial differs from frozen assignment and research choice"
                    )
                row.answer.validate_stage(i)
                current = datetime.fromisoformat(row.answered_at)
                if any(t.tzinfo is None for t in (previous, current, completed)):
                    raise ValueError("Timezone required in report chronology")
                if not previous <= current <= completed:
                    raise ValueError("Invalid observation chronology")
                previous = current
        return self
