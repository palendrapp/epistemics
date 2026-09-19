"""Separate study contracts; existing single-case reports remain readable."""

from itertools import product
from typing import Literal

from pydantic import Field, model_validator

from epistemics.discovery.models import DiscoveryAnswer, DiscoveryTrial, PrivateCase
from epistemics.models import AgentDescriptor, Model
from epistemics.study import ANALYSIS_VERSION, STUDY_VERSION


class StudyTrial(DiscoveryTrial):
    index: int = Field(ge=0, le=10)


class Assignment(Model):
    assignment_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    world_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    seed: int
    split: Literal["train", "heldout"]
    replicate: int = Field(ge=0)
    variant: dict[str, str]


class AnalysisPlan(Model):
    source_frame_grid: list[float] = [-2, -1, 0, 1, 2]
    archive_weight_grid: list[float] = [0, 0.5, 1, 1.5, 2]
    relationship_prior_grid: list[float] = [-2, -1, 0, 1, 2]
    fundamentals_prior_grid: list[float] = [-1, 0, 1]
    probability_logit_sd: float = Field(default=0.35, gt=0)
    quantile_sd: float = Field(default=1.5, gt=0)
    within_episode_correlation: float = Field(default=0.15, ge=0, lt=0.4)
    within_checkpoint_correlation: float = Field(default=0.2, ge=0, lt=0.4)
    output_prior_sd: float = Field(default=0.75, gt=0)
    probability_clip: float = Field(default=0.000001, gt=0, lt=0.05)
    adequacy_max_standardized_rmse: float = Field(default=2.0, gt=0)
    max_mean_extraction_error_pp: float = Field(default=0.1, ge=0)
    min_train_worlds_for_profile: int = Field(default=8, ge=2)

    @model_validator(mode="after")
    def grids(self):
        for name, baseline in [
            ("source_frame_grid", 0),
            ("archive_weight_grid", 1),
            ("relationship_prior_grid", 0),
            ("fundamentals_prior_grid", 0),
        ]:
            values = getattr(self, name)
            if len(values) < 3 or values != sorted(set(values)) or baseline not in values:
                raise ValueError(f"{name} needs >=3 ordered unique values including {baseline}")
        if min(self.archive_weight_grid) < 0:
            raise ValueError("Archive weights cannot be negative")
        return self


class StudyManifest(Model):
    schema_version: Literal["epistemics.study.v1"] = "epistemics.study.v1"
    study_version: str = STUDY_VERSION
    analysis_version: str = ANALYSIS_VERSION
    study_id: str
    created_at: str
    implementation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    agent: AgentDescriptor
    response_origin: Literal["agent", "synthetic"] = "agent"
    analysis_plan: AnalysisPlan = Field(default_factory=AnalysisPlan)
    assignments: list[Assignment]
    context_policy: Literal["fresh_per_assignment_continuous_within"] = (
        "fresh_per_assignment_continuous_within"
    )
    execution_verification: Literal["operator_asserted"] = "operator_asserted"

    @model_validator(mode="after")
    def assignments_valid(self):
        if self.agent.context_policy != "continuous":
            raise ValueError("Study episodes require continuous within-episode context")
        ids = [a.assignment_id for a in self.assignments]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate assignment IDs")
        groups = {}
        seeds = {}
        for a in self.assignments:
            groups.setdefault(a.world_id, set()).add((a.seed, a.split))
            seeds.setdefault(a.seed, set()).add(a.world_id)
        if any(len(x) != 1 for x in groups.values()) or any(len(x) != 1 for x in seeds.values()):
            raise ValueError("Every matched world must remain in one partition")
        if {a.split for a in self.assignments} != {"train", "heldout"}:
            raise ValueError("Both train and heldout worlds are required")
        for world in groups:
            rows = [a for a in self.assignments if a.world_id == world]
            repeats = {a.replicate for a in rows}
            if repeats != set(range(max(repeats) + 1)):
                raise ValueError("Replicates must be consecutive from zero")
            combinations = {
                (
                    a.variant.get("framing"),
                    a.variant.get("history"),
                    a.variant.get("response"),
                    a.replicate,
                )
                for a in rows
            }
            expected = set(
                product(
                    ("skeptical", "optimistic"), ("short", "long"), ("growth", "failure"), repeats
                )
            )
            if combinations != expected or len(rows) != len(expected):
                raise ValueError("Every world requires all eight matched assignments per replicate")
            if any(set(a.variant) != {"framing", "history", "response", "lineage"} for a in rows):
                raise ValueError("Unexpected variant fields")
            lineage = {a.variant["lineage"] for a in rows}
            if len(lineage) != 1 or not lineage <= {"shared", "independent"}:
                raise ValueError("Provenance must stay fixed within a matched world")
        return self


class StudyObservation(Model):
    trial: StudyTrial
    answer: DiscoveryAnswer
    answered_at: str


class EpisodeReport(Model):
    schema_version: Literal["epistemics.study-episode.v1"] = "epistemics.study-episode.v1"
    study_id: str
    manifest_sha256: str
    implementation_sha256: str
    agent: AgentDescriptor
    response_origin: Literal["agent", "synthetic"]
    assignment: Assignment
    observations: list[StudyObservation] = Field(min_length=11, max_length=11)
    private_case: PrivateCase
    completed_at: str


class ParameterEstimate(Model):
    estimate: float
    interval_95: tuple[float, float]
    baseline: float
    boundary_mass: float
    grid_resolution: float | None = None
    status: Literal["resolved_under_model", "unidentified"]
    explanation: str
    effect: dict[str, float]


class StudyProfile(Model):
    schema_version: Literal["epistemics.study-profile.v1"] = "epistemics.study-profile.v1"
    study_id: str
    analysis_version: str = ANALYSIS_VERSION
    manifest_sha256: str
    implementation_sha256: str
    response_origin: Literal["agent", "synthetic"]
    agent: AgentDescriptor
    report_hashes: dict[str, str]
    train_worlds: int
    heldout_worlds: int
    parameters: dict[str, ParameterEstimate]
    model_comparisons: dict[str, dict]
    diagnostics: dict
    experimental_contrasts: dict
    predictions: list[dict]
    limitations: list[str]
