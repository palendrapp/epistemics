"""Explicit run, resource and empirical acceptance contracts."""

from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from epistemics.models import Model
from epistemics.participants import Digest


class Configuration(Model):
    configuration_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    model: str = Field(min_length=1)
    reasoning_effort: Literal["low", "medium", "high"]
    model_revision: str = "provider alias; immutable revision not independently verified"
    # Actual prompt, flags and CLI version are additionally bound by the runner fingerprint.


class ResourceBudget(Model):
    max_attempts: int = Field(gt=0, strict=True)
    max_processed_tokens: int = Field(gt=0, strict=True)
    max_wall_seconds: int = Field(gt=0, strict=True)
    episode_timeout_seconds: int = Field(default=180, ge=30, le=600, strict=True)
    accounting: Literal["input_including_cached_plus_output"] = "input_including_cached_plus_output"
    enforcement: Literal["admission_between_episodes_one_episode_may_overshoot"] = (
        "admission_between_episodes_one_episode_may_overshoot"
    )
    billing: Literal["existing_codex_account_unknown_marginal_usd"] = (
        "existing_codex_account_unknown_marginal_usd"
    )


class Acceptance(Model):
    primary_endpoint: Literal["macro_configuration_post_evidence_probability_rmse"] = (
        "macro_configuration_post_evidence_probability_rmse"
    )
    min_absolute_rmse_gain: float = Field(default=0.01, gt=0, lt=1)
    max_individual_rmse: float = Field(default=0.05, gt=0, lt=1)
    bootstrap_draws: int = Field(default=2000, ge=100, le=10000, strict=True)
    bootstrap_seed: int = Field(default=920, ge=0, strict=True)
    uncertainty_rule: Literal[
        "paired_group_bootstrap_lower_95_bound_above_zero_each_comparator"
    ] = "paired_group_bootstrap_lower_95_bound_above_zero_each_comparator"
    threshold_basis: Literal["pragmatic_pilot_targets_not_power_validated"] = (
        "pragmatic_pilot_targets_not_power_validated"
    )
    completeness_rule: Literal["all_planned_cases_no_exclusions_no_imputation"] = (
        "all_planned_cases_no_exclusions_no_imputation"
    )


class BenchmarkSpec(Model):
    purpose: Literal["development_costing", "prediction_pilot"]
    configurations: list[Configuration] = Field(min_length=2, max_length=6)
    # Development costing is a separate retired design, never reused for final scores.
    budget: ResourceBudget
    acceptance: Acceptance = Field(default_factory=Acceptance)
    cost_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def unique_configurations(self):
        ids = [c.configuration_id for c in self.configurations]
        settings = [(c.model, c.reasoning_effort) for c in self.configurations]
        if len(ids) != len(set(ids)) or len(settings) != len(set(settings)):
            raise ValueError("Use distinct configuration IDs and model/effort combinations")
        return self


class BenchmarkManifest(BenchmarkSpec):
    schema_version: Literal["epistemics.prediction-benchmark.v1"] = (
        "epistemics.prediction-benchmark.v1"
    )
    benchmark_version: Literal["provenance-benchmark/0.1.0"] = "provenance-benchmark/0.1.0"
    design_sha256: Digest
    implementation_sha256: Digest
    runner_sha256: Digest
    codex_version: str = Field(min_length=1)
    collection_hashes: dict[str, Digest]
    response_origin: Literal["agent", "synthetic"]
    created_at: AwareDatetime


class BenchmarkReport(Model):
    schema_version: Literal["epistemics.prediction-benchmark-report.v1"] = (
        "epistemics.prediction-benchmark-report.v1"
    )
    benchmark_version: Literal["provenance-benchmark/0.1.0"] = "provenance-benchmark/0.1.0"
    benchmark_sha256: Digest
    lock_sha256: Digest
    source_hashes: dict[str, Digest]
    response_origin: Literal["agent", "synthetic"]
    complete: Literal[True] = True
    result: Literal["criteria_met", "criteria_not_met"]
    cohort: dict
    configurations: dict[str, dict]
    accounting: dict
    limitations: list[str]
