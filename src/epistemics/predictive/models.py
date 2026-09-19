"""Operator design and public checkpoint contracts have separate types."""

from itertools import product
from typing import Literal

from pydantic import Field, model_validator

from epistemics.models import Model
from epistemics.participants import Digest
from epistemics.predictive import ANALYSIS_VERSION, PROTOCOL_VERSION

Split = Literal["profile", "policy", "heldout"]
SPLIT_FAMILIES = {
    "profile": "paired_reports",
    "policy": "repeated_chain",
    "heldout": "interleaved_chains",
}
PRIORS = (0.2, 0.5, 0.8)


class Assignment(Model):
    assignment_id: str = Field(pattern=r"^[0-9a-f]{20}$")
    matched_group: str = Field(pattern=r"^[0-9a-f]{20}$")
    split: Split
    family: Literal["paired_reports", "repeated_chain", "interleaved_chains"]
    seed: int = Field(ge=0, lt=2**52, strict=True)
    replicate: int = Field(ge=0, strict=True)
    prior: Literal[0.2, 0.5, 0.8]
    strength: Literal["weak", "strong"]
    direction: Literal[-1, 1]
    provenance: Literal["independent", "copied"]


class AnalysisPlan(Model):
    model: Literal["linear_report_log_odds"] = "linear_report_log_odds"
    parameters: tuple[str, ...] = ("intercept", "prior_weight", "evidence_weight", "copy_weight")
    probability_clip: float = Field(default=1e-6, gt=0, lt=0.01)
    synthetic_logit_noise_sd: float = Field(default=0.12, gt=0)
    noiseless_max_error: float = Field(default=1e-8, gt=0)
    noisy_max_parameter_error: float = Field(default=0.12, gt=0)
    heldout_probability_rmse_limit: float = Field(default=0.06, gt=0, lt=1)
    bootstrap_draws: int = Field(default=100, ge=20, le=1000, strict=True)
    thresholds_scope: Literal["synthetic_engineering_checks_only"] = (
        "synthetic_engineering_checks_only"
    )
    real_run_budget_status: Literal["not_costed"] = "not_costed"

    @model_validator(mode="after")
    def parameter_order(self):
        if self.parameters != ("intercept", "prior_weight", "evidence_weight", "copy_weight"):
            raise ValueError("Parameter order is fixed in analysis 0.1")
        return self


class DesignManifest(Model):
    schema_version: Literal["epistemics.predictive-design.v1"] = "epistemics.predictive-design.v1"
    protocol_version: Literal["provenance-pilot/0.1.0"] = PROTOCOL_VERSION
    analysis_version: Literal["provenance-analysis/0.1.0"] = ANALYSIS_VERSION
    implementation_sha256: Digest
    use: Literal["operator_owned_design_and_synthetic_validation"] = (
        "operator_owned_design_and_synthetic_validation"
    )
    replicates: int = Field(default=1, ge=1, le=8, strict=True)
    context_policy: Literal["fresh_per_assignment_continuous_within"] = (
        "fresh_per_assignment_continuous_within"
    )
    assignments: list[Assignment]
    analysis_plan: AnalysisPlan = Field(default_factory=AnalysisPlan)

    @model_validator(mode="after")
    def balanced_and_disjoint(self):
        ids = [a.assignment_id for a in self.assignments]
        if len(ids) != len(set(ids)):
            raise ValueError("Assignment IDs must be unique")
        groups, seeds, cells = {}, {}, set()
        for a in self.assignments:
            if a.family != SPLIT_FAMILIES[a.split]:
                raise ValueError("Dependency families must remain in their assigned partition")
            cell = (a.split, a.prior, a.strength, a.direction, a.replicate)
            groups.setdefault(a.matched_group, []).append(a)
            seeds.setdefault(a.seed, set()).add(a.matched_group)
            cells.add(cell)
        expected = set(
            product(SPLIT_FAMILIES, PRIORS, ("weak", "strong"), (-1, 1), range(self.replicates))
        )
        if cells != expected or len(groups) != len(expected):
            raise ValueError("Every partition requires the full balanced factor design")
        if any(len(v) != 1 for v in seeds.values()):
            raise ValueError("World seeds cannot cross matched groups or partitions")
        for rows in groups.values():
            keys = {(a.split, a.seed, a.prior, a.strength, a.direction, a.replicate) for a in rows}
            if (
                len(rows) != 2
                or len(keys) != 1
                or {a.provenance for a in rows} != {"copied", "independent"}
            ):
                raise ValueError("Keep both provenance twins in one matched group and partition")
        return self


class TrackRecord(Model):
    correct: int = Field(ge=0, le=18, strict=True)
    total: Literal[18] = 18
    description: str = "Resolved original assessments of comparable company targets."


class EvidenceCard(Model):
    document_id: str
    publisher: str
    assessment: Literal["meets_target", "misses_target"]
    text: str
    based_on: str | None
    provenance_note: str
    original_assessment_history: TrackRecord


class DecisionPayoffs(Model):
    act_if_target_met: Literal[1.0] = 1.0
    act_if_target_missed: Literal[-1.0] = -1.0
    defer: Literal[0.0] = 0.0
    unit: Literal["hypothetical_task_points"] = "hypothetical_task_points"


class PublicCheckpoint(Model):
    schema_version: Literal["epistemics.predictive-checkpoint.v1"] = (
        "epistemics.predictive-checkpoint.v1"
    )
    protocol_version: Literal["provenance-pilot/0.1.0"] = PROTOCOL_VERSION
    checkpoint_id: str = Field(pattern=r"^[0-9a-f]{20}:[0-5]$")
    index: int = Field(ge=0, le=5, strict=True)
    company: str
    question: str
    prior_probability: float = Field(gt=0, lt=1)
    instructions: str
    evidence: list[EvidenceCard]
    payoffs: DecisionPayoffs = Field(default_factory=DecisionPayoffs)

    @model_validator(mode="after")
    def causal_prefix(self):
        if self.checkpoint_id.rsplit(":", 1)[1] != str(self.index):
            raise ValueError("Checkpoint ID must match its index")
        if len(self.evidence) != self.index:
            raise ValueError("Only the current evidence prefix belongs in a checkpoint")
        seen = {}
        for card in self.evidence:
            if card.document_id in seen:
                raise ValueError("Document IDs must be unique")
            if card.based_on is not None:
                parent = seen.get(card.based_on)
                if parent is None or parent.assessment != card.assessment:
                    raise ValueError("A copy must reference an earlier agreeing document")
                if parent.original_assessment_history != card.original_assessment_history:
                    raise ValueError("Matched copies preserve the track-record condition")
            seen[card.document_id] = card
        return self


class Response(Model):
    probability: float = Field(ge=0, le=1, strict=True)
    decision: Literal["act", "defer"]


class Parameters(Model):
    intercept: float = 0
    prior_weight: float = 1
    evidence_weight: float = 1
    copy_weight: float = 0


class SyntheticValidation(Model):
    schema_version: Literal["epistemics.predictive-validation.v1"] = (
        "epistemics.predictive-validation.v1"
    )
    protocol_version: Literal["provenance-pilot/0.1.0"] = PROTOCOL_VERSION
    analysis_version: Literal["provenance-analysis/0.1.0"] = ANALYSIS_VERSION
    manifest_sha256: Digest
    response_origin: Literal["synthetic"] = "synthetic"
    validation_seed: int
    passed: bool
    checks: dict[str, bool]
    budget: dict[str, int]
    recovery: list[dict]
    prediction: list[dict]
    misspecification: dict
    limitations: list[str]

    @model_validator(mode="after")
    def consistent_result(self):
        if not self.checks or self.passed != all(self.checks.values()):
            raise ValueError("Passed status must agree with nonempty validation checks")
        return self
