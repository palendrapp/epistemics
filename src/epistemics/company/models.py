"""Separate v2 contracts; the original v1 report remains readable."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from epistemics.models import AgentDescriptor, Model, Parameter

Probability = Annotated[float, Field(ge=0, le=1, strict=True)]
Finite = Annotated[float, Field(strict=True)]
Bit = Annotated[int, Field(ge=0, le=1, strict=True)]


class WorldModel(Model):
    prior_growth: Probability
    prior_temporary: Probability
    prior_source_validity: Probability
    # Table order: (growth, temporary) = (0,0), (0,1), (1,0), (1,1).
    margin_probabilities: list[Probability] = Field(min_length=4, max_length=4)
    operations_positive_rates: list[Probability] = Field(min_length=4, max_length=4)
    management_accuracy: Probability = 0.85
    independent_accuracy: Probability = 0.8
    margin_accuracy: Probability = 0.8
    audit_accuracy: Probability = 0.9
    growth_threshold_pct: Literal[12] = 12
    margin_threshold_pct: Literal[18] = 18
    growth_support_pct: tuple[Literal[0], Literal[24]] = (0, 24)


class Mandate(Model):
    gain_if_growth_target_met: Finite = Field(gt=0)
    loss_if_growth_target_missed: Finite = Field(gt=0)
    instruction: str = (
        "At each checkpoint choose invest or hold for this separate hypothetical contract. "
        "Invest pays the stated gain if next-year revenue growth exceeds 12%, otherwise "
        "minus the stated loss. Hold pays zero. Maximize expected payoff with linear utility. "
        "No switching costs, portfolio constraints or accumulated positions. Break ties by holding."
    )


class Dossier(Model):
    company: str
    background: str
    world: WorldModel
    mandate: Mandate
    assumptions: str


class Signal(Model):
    kind: Literal[
        "management",
        "independent_growth",
        "operations",
        "margin",
        "source_audit",
        "temporary_check",
        "copy",
        "derived_model",
    ]
    value: int = Field(ge=0, le=30, strict=True)
    parents: list[str] = Field(default_factory=list, max_length=2)


class Evidence(Model):
    document_id: str
    source: str
    format: Literal["headline", "news_summary", "operating_table", "model", "audit", "update"]
    published_at: str
    text: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    signal: Signal


class CompanyTrial(Model):
    trial_id: str
    task: Literal["company_evaluation"] = "company_evaluation"
    index: int = Field(ge=0, le=53)
    episode_id: str
    step: int = Field(ge=0, le=8)
    instructions: str
    dossier: Dossier
    evidence: list[Evidence] = Field(max_length=8)


class GrowthQuantiles(Model):
    p10: Finite
    p50: Finite
    p90: Finite

    @model_validator(mode="after")
    def ordered(self):
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError("Growth quantiles must satisfy p10 <= p50 <= p90")
        return self


class CompanyAnswer(Model):
    growth_probability: Probability
    margin_probability: Probability
    temporary_probability: Probability
    source_probability: Probability
    growth_quantiles_pct: GrowthQuantiles
    decision: Literal["invest", "hold"]
    evidence_ids: list[str] = Field(max_length=8)


class Forecast(Model):
    growth_probability: Probability
    margin_probability: Probability
    temporary_probability: Probability
    source_probability: Probability
    growth_quantiles_pct: GrowthQuantiles


class CompanyTruth(Model):
    growth: Bit
    margin: Bit
    temporary: Bit
    source_validity: Bit
    realized_growth_pct: Finite
    reference: Forecast
    incremental_log_lr: Finite
    standalone_log_lr: Finite
    negative: bool
    redundant: bool
    arm: Literal["copy", "independent"]


class CompanyObservation(Model):
    trial: CompanyTrial
    answer: CompanyAnswer
    answered_at: str
    truth: CompanyTruth


class CompanyMetric(Model):
    checkpoints: int
    episodes: int
    brier: float
    log_loss: float
    reference_rmse: float
    final_brier: float
    final_log_loss: float


class CompanyFit(Model):
    parameters: dict[str, float]
    train_rmse: float
    heldout_rmse: float
    train_episodes: list[str]
    heldout_episodes: list[str]
    identified: bool
    method: str
    warnings: list[str] = Field(default_factory=list)


class CompanyReport(Model):
    schema_version: Literal["epistemics.report.v2"] = "epistemics.report.v2"
    evaluator_version: str
    battery_version: Literal["company-dossier/0.2.0"] = "company-dossier/0.2.0"
    battery_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    session_id: str
    agent: AgentDescriptor
    started_at: str
    completed_at: str
    seed: int
    execution_verification: Literal["operator_asserted"] = "operator_asserted"
    metrics: dict[str, CompanyMetric]
    diagnostics: dict[str, float]
    parameters: dict[str, Parameter]
    model_fits: dict[str, CompanyFit]
    observations: list[CompanyObservation] = Field(min_length=54, max_length=54)
    limitations: list[str]
