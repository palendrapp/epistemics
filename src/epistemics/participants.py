"""Shared, versioned metadata contracts; these do not change existing sessions."""

from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, RootModel, model_validator

from epistemics.models import Model

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, Field(min_length=1, max_length=256)]


class AgentConfiguration(Model):
    model: Identifier
    model_version: Identifier
    configuration_sha256: Digest
    temperature: float | None = Field(default=None, ge=0, le=10)


class AgentParticipant(Model):
    schema_version: Literal["epistemics.participant.v1"] = "epistemics.participant.v1"
    kind: Literal["agent"] = "agent"
    subject_id: Identifier
    configuration: AgentConfiguration


class HumanParticipant(Model):
    schema_version: Literal["epistemics.participant.v1"] = "epistemics.participant.v1"
    kind: Literal["human"] = "human"
    # A pseudonym is sufficient; no name, demographic or model metadata is required.
    subject_id: Identifier


Participant = Annotated[AgentParticipant | HumanParticipant, Field(discriminator="kind")]


class ParticipantDescriptor(RootModel[Participant]):
    """Standalone schema/validator for the discriminated participant union."""


class EvaluationConditions(Model):
    interface: Literal["mcp", "browser", "other", "unspecified"] = "unspecified"
    context_policy: str | None = None
    instructions_sha256: Digest | None = None
    tools: list[str] | None = None
    assistance: list[str] | None = None
    time_limit_seconds: int | None = Field(default=None, gt=0, strict=True)
    elapsed_seconds: float | None = Field(default=None, ge=0)


class SessionContext(Model):
    """Public metadata boundary for future shared services; no trial truth or seeds."""

    schema_version: Literal["epistemics.session-context.v1"] = "epistemics.session-context.v1"
    session_id: Identifier
    participant: Participant
    response_origin: Literal["agent", "human", "synthetic", "unspecified"] = "unspecified"
    metadata_verification: Literal["operator_asserted"] = "operator_asserted"
    protocol_version: Identifier
    protocol_sha256: Digest
    evaluator_version: Identifier
    conditions: EvaluationConditions = Field(default_factory=EvaluationConditions)
    started_at: AwareDatetime
    completed_at: AwareDatetime | None = None
    completion: Literal["not_started", "partial", "complete"]
    accepted_answers: int = Field(ge=0, strict=True)
    planned_answers: int = Field(gt=0, strict=True)
    sharing: Literal["private"] = "private"

    @model_validator(mode="after")
    def consistent(self):
        if self.response_origin in {"agent", "human"}:
            if self.response_origin != self.participant.kind:
                raise ValueError("Response origin must match participant kind")
        if self.accepted_answers > self.planned_answers:
            raise ValueError("Accepted answers exceed planned answers")
        expected = (
            "complete"
            if self.accepted_answers == self.planned_answers
            else "partial"
            if self.accepted_answers
            else "not_started"
        )
        if self.completion != expected:
            raise ValueError("Completion must agree with accepted/planned counts")
        if (self.completed_at is not None) != (self.completion == "complete"):
            raise ValueError("Only a complete session has a completion timestamp")
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("Completion cannot precede start")
        return self
