"""Discovery v3 contracts keep evaluator states out of public trials."""

from typing import Literal

from pydantic import Field

from epistemics.company.models import Finite, GrowthQuantiles, Probability
from epistemics.models import AgentDescriptor, Model


class ArchiveRow(Model):
    case_id: str
    reported_pct: Finite
    audited_pct: Finite


class Source(Model):
    source_id: str
    name: str
    profile: str
    archive: list[ArchiveRow]


class Analogue(Model):
    case_id: str
    underlying_growth_pct: Finite
    rollout_disruption: bool
    backlog_score: Finite
    renewal_growth_pct: Finite


class Document(Model):
    document_id: str
    source: str
    title: str
    published_at: str
    text: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DiscoveryTrial(Model):
    trial_id: str
    task: Literal["discovery"] = "discovery"
    index: int = Field(ge=0, le=9)
    company: str
    background: str
    target_event: Literal["growth_above_12", "growth_at_or_below_12"]
    instructions: str
    sources: list[Source] = Field(min_length=3, max_length=3)
    analogues: list[Analogue]
    documents: list[Document] = Field(max_length=9)
    source_probe_ids: list[str]
    conditional_probe: bool
    extraction_keys: list[str]
    gain: Finite = 2
    loss: Finite = 1


class DiscoveryAnswer(Model):
    target_probability: Probability
    growth_quantiles_pct: GrowthQuantiles
    decision: Literal["invest", "hold"]
    evidence_ids: list[str] = Field(max_length=9)
    source_accuracy: dict[str, Probability] = Field(default_factory=dict)
    conditional_growth_probability: Probability | None = None
    extracted_values: dict[str, Finite] = Field(default_factory=dict)
    alternative_explanation: str | None = Field(default=None, max_length=1200)


class ObserverForecast(Model):
    growth_probability: Probability
    growth_quantiles_pct: GrowthQuantiles
    source_accuracy: dict[str, Probability]
    conditional_growth_probability: Probability
    disruption_probability: Probability
    strong_disruption_link_probability: Probability
    shared_origin_probability: Probability


class PrivateCase(Model):
    underlying_growth_pct: Finite
    disruption: int = Field(ge=0, le=1)
    relationship: int = Field(ge=0, le=1)
    source_parameters: dict[str, dict[str, Finite]]
    copied: bool
    realized_growth_pct: Finite
    variant: dict[str, str]
    claim_ledger: dict[str, Finite]


class DiscoveryObservation(Model):
    trial: DiscoveryTrial
    answer: DiscoveryAnswer
    answered_at: str


class ObserverComparison(Model):
    forecasts: list[ObserverForecast] = Field(min_length=10, max_length=10)
    growth_report_rmse: Finite
    description: str


class DiscoveryReport(Model):
    schema_version: Literal["epistemics.report.v3"] = "epistemics.report.v3"
    evaluator_version: str
    battery_version: Literal["company-discovery/0.3.0"] = "company-discovery/0.3.0"
    battery_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    session_id: str
    agent: AgentDescriptor
    started_at: str
    completed_at: str
    seed: int
    execution_verification: Literal["operator_asserted"] = "operator_asserted"
    observations: list[DiscoveryObservation] = Field(min_length=10, max_length=10)
    private_case: PrivateCase
    metrics: dict[str, Finite]
    observer_models: dict[str, ObserverComparison]
    observer_assumptions: dict[str, str | float | list[float]]
    limitations: list[str]
