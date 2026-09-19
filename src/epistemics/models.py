"""Versioned public experiment and report contracts."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

TaskName = Literal["evidence_integration", "source_reliability", "reversal_learning"]
Probability = float


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class AgentDescriptor(Model):
    agent_id: str = Field(min_length=1, max_length=256)
    model: str = Field(min_length=1, max_length=256)
    model_version: str = Field(min_length=1, max_length=256)
    # Identifies the system prompt/tools/runtime configuration, not model weights.
    configuration_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    context_policy: Literal["continuous", "reset_per_trial", "reset_per_task"] = "continuous"
    temperature: float | None = Field(default=None, ge=0, le=10)


class Answer(Model):
    probability: Probability = Field(ge=0, le=1, strict=True)
    source_probability: Probability | None = Field(default=None, ge=0, le=1, strict=True)


class Trial(Model):
    trial_id: str
    task: TaskName
    index: int
    instructions: str
    stimulus: dict[str, Any]


class Observation(Model):
    trial: Trial
    answer: Answer
    answered_at: str
    truth: dict[str, float]


class Parameter(Model):
    estimate: float
    interval_95: tuple[float, float] | None = None
    method: str
    n: int
    warnings: list[str] = Field(default_factory=list)


class Metrics(Model):
    n: int
    brier: float
    log_loss: float
    reference_rmse: float
    endpoint_reports: int


class ModelFit(Model):
    parameter: float
    train_rmse: float
    heldout_rmse: float
    train_n: int
    heldout_n: int
    near_optimal_range: tuple[float, float]
    range_definition: str = "Grid values with train MSE <= minimum MSE + 0.0001; not a CI"


class Report(Model):
    schema_version: Literal["epistemics.report.v1"] = "epistemics.report.v1"
    evaluator_version: str
    battery_version: str
    battery_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    session_id: str
    agent: AgentDescriptor
    started_at: str
    completed_at: str
    seed: int
    execution_verification: Literal["operator_asserted"] = "operator_asserted"
    metrics: dict[str, Metrics]
    parameters: dict[str, Parameter]
    model_fits: dict[str, ModelFit]
    observations: list[Observation] = Field(min_length=88, max_length=88)
    limitations: list[str]
