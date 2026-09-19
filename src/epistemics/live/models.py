"""Versioned core protocol and completed report contracts."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from epistemics.discovery.models import (
    DiscoveryObservation,
    DiscoveryTrial,
    ObserverComparison,
    PrivateCase,
)
from epistemics.models import Metrics, Model, Observation, Parameter, Trial
from epistemics.participants import SessionContext


class CalibrationTrial(Trial):
    task: Literal["evidence_integration"] = "evidence_integration"
    index: int = Field(ge=0, le=23)


class CoreTrial(Model):
    trial_id: str = Field(pattern=r"^core-[0-9]{2}$")
    index: int = Field(ge=0, le=33)
    module: Literal["discovery", "calibration"]
    module_index: int = Field(ge=0, le=23)
    payload: Annotated[DiscoveryTrial | CalibrationTrial, Field(discriminator="task")]

    @model_validator(mode="after")
    def aligned(self):
        discovery = self.index < 10
        if self.module != ("discovery" if discovery else "calibration"):
            raise ValueError("Module does not match protocol order")
        expected = self.index if discovery else self.index - 10
        if self.module_index != expected or self.payload.index != expected:
            raise ValueError("Module index does not match protocol order")
        if self.trial_id != f"core-{self.index:02d}":
            raise ValueError("Trial ID does not match position")
        if isinstance(self.payload, DiscoveryTrial) != discovery:
            raise ValueError("Payload does not match module")
        return self


class CalibrationResult(Model):
    observations: list[Observation] = Field(min_length=24, max_length=24)
    metrics: Metrics
    parameters: dict[str, Parameter]


class DiscoveryResult(Model):
    observations: list[DiscoveryObservation] = Field(min_length=10, max_length=10)
    private_case: PrivateCase
    metrics: dict[str, float]
    observer_models: dict[str, ObserverComparison]
    observer_assumptions: dict[str, str | float | list[float]]


class CoreReport(Model):
    schema_version: Literal["epistemics.report.v4"] = "epistemics.report.v4"
    context: SessionContext
    seed: int = Field(ge=0, lt=2**52, strict=True)
    protocol_version: Literal["passport-core/0.1.0"] = "passport-core/0.1.0"
    instructions_accepted: Literal[True]
    discovery: DiscoveryResult
    calibration: CalibrationResult
    limitations: list[str]

    @model_validator(mode="after")
    def completed(self):
        if self.context.completion != "complete" or self.context.accepted_answers != 34:
            raise ValueError("Core reports require all 34 answers")
        if self.context.protocol_version != self.protocol_version:
            raise ValueError("Report and session protocols differ")
        for i, observation in enumerate(self.discovery.observations):
            if observation.trial.index != i:
                raise ValueError("Discovery observations must be in protocol order")
        for i, observation in enumerate(self.calibration.observations):
            if observation.trial.index != i or observation.trial.task != "evidence_integration":
                raise ValueError("Calibration observations must be in protocol order")
        return self
