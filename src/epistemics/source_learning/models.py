"""Private design and public response contracts."""

from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, model_validator

from epistemics.models import Model
from epistemics.participants import Digest, Participant
from epistemics.source_inference.world import PrivateRecord, PublicRecord, Rule, Source

Probability = Annotated[float, Field(ge=0, le=1, strict=True)]
Query = Literal["customer_panel", "selection_audit", "measurement_audit", "stop"]
Condition = Literal["sparse", "dense"]


class Company(Model):
    company_id: str
    phase: Literal["calibration", "heldout"]
    prior_strong: float = Field(gt=0, lt=1)
    threshold: float = Field(gt=0, lt=1)
    cost_scale: float = Field(gt=0)
    record: PrivateRecord
    independent_panel: PublicRecord

    @model_validator(mode="after")
    def coherent(self):
        if (
            self.record.public.resolved_strong != self.independent_panel.resolved_strong
            or self.record.public.world != self.independent_panel.world
        ):
            raise ValueError("Independent evidence must describe the same company state and world")
        return self


class Manifest(Model):
    schema_version: Literal["epistemics.source-learning-collection.v1"] = (
        "epistemics.source-learning-collection.v1"
    )
    battery_version: Literal["source-learning/0.1.0"] = "source-learning/0.1.0"
    evaluator_version: Literal["source-learning-evaluator/0.1.0"] = (
        "source-learning-evaluator/0.1.0"
    )
    study_id: str
    created_at: AwareDatetime
    design_seed: int = Field(ge=0, strict=True)
    implementation_sha256: Digest
    participant: Participant
    response_origin: Literal["human", "agent", "synthetic"]
    condition: Condition
    condition_assignment: Literal["operator_selected", "randomized"]
    context_policy: Literal["continuous_with_available_public_history"] = (
        "continuous_with_available_public_history"
    )
    execution_verification: Literal["operator_asserted"] = "operator_asserted"
    sources: list[Source] = Field(min_length=6, max_length=6)
    archive: list[PrivateRecord] = Field(min_length=72, max_length=72)
    companies: list[Company] = Field(min_length=24, max_length=24)

    @model_validator(mode="after")
    def consistent(self):
        if self.response_origin != "synthetic" and self.response_origin != self.participant.kind:
            raise ValueError("Response origin must match participant")
        source_map = {s.source_id: s for s in self.sources}
        if len(source_map) != 6 or len({c.company_id for c in self.companies}) != 24:
            raise ValueError("Unique source and company identifiers required")
        for row in [*self.archive, *(c.record for c in self.companies)]:
            if source_map.get(row.source.source_id) != row.source:
                raise ValueError("A source process must remain consistent throughout its history")
        for i, company in enumerate(self.companies):
            if company.company_id != f"company-{i + 1:02d}":
                raise ValueError("Company order is fixed")
            if company.phase != ("calibration" if i < 12 else "heldout"):
                raise ValueError("Calibration must precede heldout companies")
        for source_id in source_map:
            rows = [r for r in self.archive if r.source.source_id == source_id]
            if len(rows) != 12 or sum(r.public.resolved_strong for r in rows) != 6:
                raise ValueError("Every archive contains six strong and six weak resolved cases")
            for phase in ("calibration", "heldout"):
                if (
                    sum(
                        c.record.source.source_id == source_id and c.phase == phase
                        for c in self.companies
                    )
                    != 2
                ):
                    raise ValueError("Each phase needs two companies per source")
        return self


class Trial(Model):
    schema_version: Literal["epistemics.source-learning-trial.v1"] = (
        "epistemics.source-learning-trial.v1"
    )
    battery_version: Literal["source-learning/0.1.0"] = "source-learning/0.1.0"
    trial_id: str
    checkpoint: int = Field(ge=1, le=36)
    company_id: str
    stage: Literal["forecast", "research", "revision"]
    source_id: str
    prior_strong: Probability
    decision_threshold: Probability
    documents: list[str]
    archive: list[PublicRecord]
    known_selection: Rule | None = None
    known_measurement_accuracy: Probability | None = None
    request_diagnostics: bool
    research_costs: dict[str, float]
    selected_query: Query | None = None


class Answer(Model):
    probability: Probability
    decision: Literal["invest", "decline"]
    query: Query | None = None
    measurement_accuracy: Probability | None = None
    random_selection_probability: Probability | None = None

    @model_validator(mode="after")
    def whole_percent(self):
        for value in (
            self.probability,
            self.measurement_accuracy,
            self.random_selection_probability,
        ):
            if value is not None and abs(value * 100 - round(value * 100)) > 1e-8:
                raise ValueError("Use whole percentages (0 to 1 in increments of 0.01)")
        return self

    def validate_trial(self, trial):
        if (self.query is not None) != (trial.stage == "research"):
            raise ValueError("Choose research only at the research checkpoint")
        if any(
            (value is not None) != trial.request_diagnostics
            for value in (self.measurement_accuracy, self.random_selection_probability)
        ):
            raise ValueError("Answer exactly the diagnostic questions requested at this checkpoint")


class Observation(Model):
    trial: Trial
    answer: Answer
    answered_at: AwareDatetime
    prediction_sha256: Digest


class Report(Model):
    schema_version: Literal["epistemics.source-learning-report.v1"] = (
        "epistemics.source-learning-report.v1"
    )
    manifest: Manifest
    manifest_sha256: Digest
    completed_at: AwareDatetime
    observations: list[Observation] = Field(min_length=36, max_length=36)
    prediction_locks: list[dict] = Field(min_length=36, max_length=36)
    fit_lock: dict
    analysis: dict
    limitations: list[str]

    @model_validator(mode="after")
    def chronology_and_reconstruction(self):
        from datetime import datetime

        from epistemics.source_learning.battery import public_trial
        from epistemics.source_learning.storage import digest, encoded

        if digest(encoded(self.manifest)) != self.manifest_sha256:
            raise ValueError("Report manifest binding changed")
        fit_time = datetime.fromisoformat(self.fit_lock["locked_at"])
        if (
            not self.observations[11].answered_at
            <= fit_time
            <= datetime.fromisoformat(self.prediction_locks[12]["locked_at"])
        ):
            raise ValueError("Parameters must freeze between calibration and heldout collection")
        previous = self.manifest.created_at
        for i, observation in enumerate(self.observations):
            earlier = [r.answer for r in self.observations[:i]]
            if observation.trial != public_trial(self.manifest, i, earlier):
                raise ValueError("Trial differs from frozen design and accepted public history")
            observation.answer.validate_trial(observation.trial)
            lock = self.prediction_locks[i]
            if digest(encoded(lock)) != observation.prediction_sha256:
                raise ValueError("Prediction bytes do not match the accepted receipt")
            if not previous <= datetime.fromisoformat(lock["locked_at"]) <= observation.answered_at:
                raise ValueError("Predictions must be locked before each answer")
            if observation.answered_at > self.completed_at:
                raise ValueError("Invalid completion chronology")
            previous = observation.answered_at
        return self
