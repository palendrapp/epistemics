"""Collection metadata is an operator assertion, separate from the design and passport."""

from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from epistemics.models import Model
from epistemics.participants import Digest, Participant
from epistemics.predictive.models import Assignment, PublicCheckpoint, Response

COLLECTOR_VERSION = "provenance-collector/0.1.0"


class CollectionSpec(Model):
    participant: Participant
    response_origin: Literal["agent", "human", "synthetic"]
    purpose: Literal["full_pilot", "transport_smoke"]
    # Full pilots use the entire ordered design; smoke tests declare a subset in advance.
    assignment_ids: list[str] = Field(min_length=1)
    context_policy: Literal["fresh_per_assignment_continuous_within"] = (
        "fresh_per_assignment_continuous_within"
    )
    configuration_scope: str = Field(min_length=1, max_length=4000)
    execution_notes: str = Field(min_length=1, max_length=4000)
    allowed_tools: list[str]
    assistance: list[str]

    @model_validator(mode="after")
    def consistent(self):
        if self.response_origin != "synthetic" and self.response_origin != self.participant.kind:
            raise ValueError("Response origin must match participant kind")
        if len(set(self.assignment_ids)) != len(self.assignment_ids):
            raise ValueError("Assignments cannot repeat")
        return self


class CollectionManifest(CollectionSpec):
    schema_version: Literal["epistemics.predictive-collection.v1"] = (
        "epistemics.predictive-collection.v1"
    )
    collector_version: Literal["provenance-collector/0.1.0"] = COLLECTOR_VERSION
    design_sha256: Digest
    instructions_sha256: Digest
    created_at: AwareDatetime
    metadata_verification: Literal["operator_asserted"] = "operator_asserted"
    execution_verification: Literal["not_independently_verified"] = "not_independently_verified"
    sharing: Literal["private"] = "private"


class Observation(Model):
    checkpoint: PublicCheckpoint
    answer: Response
    accepted_at: AwareDatetime


class CollectedEpisode(Model):
    assignment: Assignment
    started_at: AwareDatetime
    completed_at: AwareDatetime
    observations: list[Observation] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.completed_at < self.started_at:
            raise ValueError("Completion cannot precede start")
        previous = self.started_at
        for index, observation in enumerate(self.observations):
            if observation.checkpoint.checkpoint_id != f"{self.assignment.assignment_id}:{index}":
                raise ValueError("Observations must be ordered within their assignment")
            if not previous <= observation.accepted_at <= self.completed_at:
                raise ValueError("Observation timestamps must be ordered")
            previous = observation.accepted_at
        return self


class CollectionAttempt(Model):
    attempt_id: str
    assignment_id: str
    started_at: AwareDatetime
    ended_at: AwareDatetime | None = None
    restored_answers: int = Field(ge=0)
    transport_status: Literal["open", "closed", "error"]
    # Open attempts can be interrupted processes; transport closure is not task completion.


class CollectionExport(Model):
    schema_version: Literal["epistemics.predictive-responses.v1"] = (
        "epistemics.predictive-responses.v1"
    )
    collection_sha256: Digest
    collection: CollectionManifest
    scope: Literal["complete_planned_collection"] = "complete_planned_collection"
    episodes: list[CollectedEpisode]
    attempts: list[CollectionAttempt]
    interpretation: Literal["reported_responses_not_internal_beliefs"] = (
        "reported_responses_not_internal_beliefs"
    )

    @model_validator(mode="after")
    def matches_plan(self):
        ids = [e.assignment.assignment_id for e in self.episodes]
        if ids != self.collection.assignment_ids:
            raise ValueError("Export must include every planned assignment in order")
        if any(a.assignment_id not in ids for a in self.attempts):
            raise ValueError("Attempts must belong to the collection")
        return self
