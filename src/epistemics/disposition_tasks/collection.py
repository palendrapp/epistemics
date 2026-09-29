"""One fresh context over one module's 24 checkpoints; transactional and immutable.

The manifest binds the implementation fingerprint, the evaluator-chosen case order, the variant,
any structures to be revealed (learning variants) and the exact bytes of every rendered case.
Each public checkpoint is locked before its answer.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import numpy as np
from pydantic import AwareDatetime, Field, model_validator

from epistemics.disposition_tasks import VERSION
from epistemics.disposition_tasks.presentation import Answer, describe, present
from epistemics.disposition_tasks.render import (
    LEARNING_RATES,
    allowed,
    items_for,
    render,
    reveal,
)
from epistemics.dispositions import DESIGN_VERSION, MODEL_VERSION
from epistemics.dispositions.observers import structure_posterior
from epistemics.models import Model
from epistemics.participants import Digest, Participant, ParticipantDescriptor
from epistemics.service import now
from epistemics.source_learning.storage import digest, encoded, save

Module = Literal[
    "corroboration",
    "disclosure",
    "checks",
    "corroboration-cues",
    "disclosure-cues",
    "corroboration-range",
    "corroboration-dossier",
    "disclosure-dossier",
    "corroboration-unprompted",
    "disclosure-unprompted",
    "corroboration-asked",
    "disclosure-asked",
    "corroboration-probed",
    "copying-urn",
    "selection-urn",
    "mismatch-urn",
    "copying-urn-asked",
    "selection-urn-asked",
    "mismatch-urn-asked",
    "copying-urn-probed",
    "selection-urn-probed",
    "mismatch-urn-probed",
]
Cover = Literal["markets", "ecology"]
Variant = Literal[
    "paired",
    "open",
    "suggestive",
    "reassuring",
    "learning-high",
    "learning-low",
    "cues-a",
    "cues-b",
    "range-reassuring",
    "range-suggestive",
    "dossier-a",
    "named-a",
    "urn-plain",
    "urn-named",
    "urn2-plain",
    "urn2-named",
    "urn3-named",
]
CASES = 24


def fingerprint():
    """Binds this package and the observers and designs it renders."""
    root = Path(__file__).parent
    return digest(
        encoded(
            {
                f"{package.name}/{p.name}": digest(p.read_bytes())
                for package in (root, root.parent / "dispositions")
                for p in sorted(package.glob("*.py"))
            }
        )
    )


class Manifest(Model):
    schema_version: Literal["epistemics.disposition-collection.v3"] = (
        "epistemics.disposition-collection.v3"
    )
    battery_version: Literal["disposition-tasks/0.12.0"] = VERSION
    model_version: Literal["disposition-model/0.5.0"] = MODEL_VERSION
    design_version: Literal["disposition-design/0.8.0"] = DESIGN_VERSION
    study_id: str
    created_at: AwareDatetime
    implementation_sha256: Digest
    participant: Participant
    response_origin: Literal["human", "agent", "synthetic"]
    module: Module
    cover: Cover
    variant: Variant = "paired"
    order: list[int] = Field(min_length=CASES, max_length=CASES)
    # Learning variants only: each item's structure (relay or selective sender), aligned with
    # item index and shown after that case is answered; None where there is nothing to reveal.
    revealed: list[bool | None] | None = None
    context_policy: Literal["continuous_within_collection_no_outcome_feedback"] = (
        "continuous_within_collection_no_outcome_feedback"
    )
    execution_verification: Literal["operator_asserted"] = "operator_asserted"
    case_sha256: list[Digest]

    @model_validator(mode="after")
    def consistent(self):
        if self.response_origin != "synthetic" and self.response_origin != self.participant.kind:
            raise ValueError("Response origin must match participant")
        if sorted(self.order) != list(range(CASES)):
            raise ValueError("Case order must be a permutation of the design items")
        if len(self.case_sha256) != CASES:
            raise ValueError("One case commitment per checkpoint")
        if not allowed(self.module, self.cover, self.variant):
            raise ValueError("This module does not offer that variant and cover")
        learning = self.variant in LEARNING_RATES
        if learning != (self.revealed is not None):
            raise ValueError("Revealed structures exist exactly for learning variants")
        if learning:
            nothing = items_for(self.module)["kind"] == "single"
            if len(self.revealed) != CASES or any(
                (r is None) != bool(n) for r, n in zip(self.revealed, nothing, strict=True)
            ):
                raise ValueError("Reveal a structure for every item that has one")
        return self


def rendered(manifest, case_index):
    return render(manifest.module, manifest.cover, manifest.order[case_index], manifest.variant)


def draw_revealed(module, variant, seed):
    """Structures drawn from their posterior given each case's evidence at the world rate."""
    rng = np.random.default_rng(seed)
    posterior = structure_posterior(module, items_for(module), LEARNING_RATES[variant])
    return [None if np.isnan(p) else bool(rng.random() < p) for p in posterior]


def create(
    directory,
    participant,
    *,
    module,
    cover,
    order,
    variant="paired",
    reveal_seed=None,
    synthetic=False,
):
    participant = ParticipantDescriptor.model_validate(participant).root
    order = [int(i) for i in order]
    if (variant in LEARNING_RATES) != (reveal_seed is not None):
        raise ValueError("Learning variants, and only they, need an evaluator reveal seed")
    revealed = draw_revealed(module, variant, reveal_seed) if reveal_seed is not None else None
    manifest = Manifest(
        study_id=str(uuid4()),
        created_at=now(),
        implementation_sha256=fingerprint(),
        participant=participant,
        response_origin="synthetic" if synthetic else participant.kind,
        module=module,
        cover=cover,
        variant=variant,
        order=order,
        revealed=revealed,
        case_sha256=[digest(encoded(render(module, cover, i, variant))) for i in order],
    )
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    raw = encoded(manifest)
    save(directory / "manifest.json", raw)
    save(directory / "manifest.sha256", (digest(raw) + "\n").encode())
    return manifest


def load(directory):
    directory = Path(directory)
    raw = (directory / "manifest.json").read_bytes()
    if digest(raw) != (directory / "manifest.sha256").read_text().strip():
        raise ValueError("Frozen manifest bytes changed")
    manifest = Manifest.model_validate_json(raw)
    if manifest.implementation_sha256 != fingerprint():
        raise ValueError("Frozen evaluator changed; resume with the original implementation")
    for i, expected in enumerate(manifest.case_sha256):
        if digest(encoded(rendered(manifest, i))) != expected:
            raise ValueError("A rendered case differs from its commitment")
    return manifest, digest(raw)


def public_trial(manifest, case_index):
    previous = None
    if manifest.revealed is not None and case_index > 0:
        index = manifest.order[case_index - 1]
        previous = reveal(
            manifest.module, manifest.cover, index, case_index, manifest.revealed[index]
        )
    return present(case_index + 1, CASES, rendered(manifest, case_index), previous)


class CollectionService:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.manifest, self.manifest_hash = load(directory)
        self.database = self.directory / "responses.sqlite3"
        with sqlite3.connect(self.database) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS collection (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)"
            )
            db.execute(
                "INSERT OR IGNORE INTO collection VALUES (1, ?)",
                (json.dumps({"answers": [], "locks": [], "completed_at": None}),),
            )
        self.database.chmod(0o600)

    @contextmanager
    def state(self):
        _, current = load(self.directory)
        if current != self.manifest_hash:
            raise ValueError("Collection binding changed")
        with sqlite3.connect(self.database, timeout=30) as db:
            db.execute("BEGIN IMMEDIATE")
            state = json.loads(
                db.execute("SELECT payload FROM collection WHERE id=1").fetchone()[0]
            )
            yield state
            db.execute(
                "UPDATE collection SET payload=? WHERE id=1", (json.dumps(state, allow_nan=False),)
            )

    def describe(self):
        return describe(self.manifest)

    def _prepare(self, state):
        i = len(state["answers"])
        if i == CASES:
            return None
        trial = public_trial(self.manifest, i)
        if len(state["locks"]) == i:
            state["locks"].append(
                {
                    "trial_id": trial["trial_id"],
                    "public_trial_sha256": digest(encoded(trial)),
                    "locked_at": now(),
                }
            )
        elif state["locks"][i]["public_trial_sha256"] != digest(encoded(trial)):
            raise ValueError("Frozen presentation changed")
        return trial

    def get_trial(self):
        with self.state() as state:
            trial = self._prepare(state)
            return {
                "complete": trial is None,
                "finished": state["completed_at"] is not None,
                "answered": len(state["answers"]),
                "trial": trial,
            }

    def submit(self, trial_id, answer):
        answer = Answer.model_validate(answer)
        data = answer.model_dump(mode="json", exclude_none=True)
        with self.state() as state:
            earlier = next((r for r in state["answers"] if r["trial_id"] == trial_id), None)
            if earlier is not None:
                if earlier["answer"] != data:
                    raise ValueError("An accepted answer cannot be changed")
                receipt = earlier["receipt"]
            else:
                n = len(state["answers"])
                if n == CASES or len(state["locks"]) != n + 1:
                    raise ValueError("Read the current checkpoint before answering")
                trial = public_trial(self.manifest, n)
                if trial["trial_id"] != trial_id or state["locks"][n]["trial_id"] != trial_id:
                    raise ValueError("Submit only the current checkpoint")
                answer.validate_trial(trial)
                receipt = {"accepted": True, "trial_id": trial_id, "answered": n + 1}
                state["answers"].append(
                    {"trial_id": trial_id, "answer": data, "answered_at": now(), "receipt": receipt}
                )
        current = self.get_trial()
        return {
            **receipt,
            "next_trial": current["trial"],
            "all_cases_answered": current["complete"],
        }

    def get_history(self):
        with self.state() as state:
            return {
                "history": [
                    {"trial": public_trial(self.manifest, i), "answer": row["answer"]}
                    for i, row in enumerate(state["answers"])
                ]
            }

    def finish(self):
        with self.state() as state:
            if len(state["answers"]) != CASES:
                raise ValueError("Answer every case first")
            if state["completed_at"] is None:
                state["completed_at"] = now()
            return {
                "complete": True,
                "answered": len(state["answers"]),
                "completion_questions": [
                    "Were any outcomes, prices or check results revealed during this collection?",
                    "When a quantity you wanted was not stated, how did you decide on an answer?",
                    "Which cases or instructions, if any, were confusing?",
                ],
            }


class Observation(Model):
    trial: dict
    answer: Answer
    answered_at: AwareDatetime
    locked_at: AwareDatetime


class Report(Model):
    schema_version: Literal["epistemics.disposition-report.v3"] = "epistemics.disposition-report.v3"
    manifest: Manifest
    manifest_sha256: Digest
    completed_at: AwareDatetime
    observations: list[Observation] = Field(min_length=CASES, max_length=CASES)
    analysis: dict
    limitations: list[str]

    @model_validator(mode="after")
    def reconstruction(self):
        if digest(encoded(self.manifest)) != self.manifest_sha256:
            raise ValueError("Report manifest binding changed")
        previous = self.manifest.created_at
        for i, o in enumerate(self.observations):
            if o.trial != public_trial(self.manifest, i):
                raise ValueError("Checkpoint differs from the frozen design")
            o.answer.validate_trial(o.trial)
            if not previous <= o.locked_at <= o.answered_at <= self.completed_at:
                raise ValueError("Each checkpoint must be locked before its answer")
            previous = o.answered_at
        return self


LIMITATIONS = [
    "Fictional formal cases with stated numeric likelihoods; parameters are conditional on this task, wording and cover story.",
    "Probability reports and stated maximum prices are observations, not internal beliefs or valuations.",
    "Parameters come from one context; stability needs repeated fresh contexts and paraphrase variation.",
    "No outcomes, prices or check results are revealed. Learning variants reveal only how earlier cases were produced, drawn at a fixed world rate given each case's evidence.",
    "Execution metadata is operator-asserted; no model identity attestation.",
]


def export(directory):
    from epistemics.disposition_tasks.analysis import analyze

    service = CollectionService(directory)
    with service.state() as state:
        if state["completed_at"] is None:
            raise ValueError("Finish the collection before export")
        observations = []
        for i, row in enumerate(state["answers"]):
            lock = state["locks"][i]
            trial = public_trial(service.manifest, i)
            if lock["public_trial_sha256"] != digest(encoded(trial)):
                raise ValueError("Locked checkpoint differs from reconstruction")
            observations.append(
                Observation(
                    trial=trial,
                    answer=row["answer"],
                    answered_at=datetime.fromisoformat(row["answered_at"]),
                    locked_at=datetime.fromisoformat(lock["locked_at"]),
                )
            )
        report = Report(
            manifest=service.manifest,
            manifest_sha256=service.manifest_hash,
            completed_at=state["completed_at"],
            observations=observations,
            analysis=analyze(service.manifest, observations),
            limitations=LIMITATIONS,
        )
    raw = encoded(report)
    save(Path(directory) / "report.json", raw)
    save(Path(directory) / "report.sha256", (digest(raw) + "\n").encode())
    return report


def load_report(directory):
    """Re-verify exact report bytes, reconstruction and analysis."""
    from epistemics.disposition_tasks.analysis import analyze

    directory = Path(directory)
    raw = (directory / "report.json").read_bytes()
    if digest(raw) != (directory / "report.sha256").read_text().strip():
        raise ValueError("Report byte hash mismatch")
    report = Report.model_validate_json(raw)
    if report.analysis != json.loads(encoded(analyze(report.manifest, report.observations))):
        raise ValueError("Stored analysis differs from recomputation")
    return report
