"""One fresh context over a fixed list of dossier cases (0.2); transactional and immutable.

The manifest binds the implementation fingerprint and the exact bytes of every rendered
dossier. Each public checkpoint is locked before its answer. Company demand never appears in
public output; it is regenerated privately from the pair seed for analysis.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import AwareDatetime, Field, model_validator

from epistemics.models import Model
from epistemics.participants import Digest, Participant, ParticipantDescriptor
from epistemics.research_world2 import VERSION, check
from epistemics.research_world2.presentation import Answer, Arm, describe, present
from epistemics.research_world2.render import company_name, render, structure_note
from epistemics.research_world2.world import Family, Presentation, generate
from epistemics.service import now
from epistemics.source_learning.storage import digest, encoded, save


def fingerprint():
    root = Path(__file__).parent
    return digest(
        encoded(
            {
                str(p.relative_to(root)): digest(p.read_bytes())
                for p in sorted(root.rglob("*"))
                if p.is_file() and (p.suffix == ".py" or "assets" in p.parts)
            }
        )
    )


class Item(Model):
    case: int = Field(ge=1)
    pair_seed: int = Field(ge=0)
    family: Family
    presentation: Presentation
    check_price: float | None = Field(default=None, gt=0, lt=1)


class Manifest(Model):
    schema_version: Literal["epistemics.research-collection.v2"] = (
        "epistemics.research-collection.v2"
    )
    battery_version: Literal["research-world/0.2.0"] = VERSION
    study_id: str
    created_at: AwareDatetime
    implementation_sha256: Digest
    participant: Participant
    response_origin: Literal["human", "agent", "synthetic"]
    arm: Arm
    check_offered: bool
    context_policy: Literal["continuous_within_collection_no_outcome_feedback"] = (
        "continuous_within_collection_no_outcome_feedback"
    )
    execution_verification: Literal["operator_asserted"] = "operator_asserted"
    items: list[Item] = Field(min_length=1, max_length=48)
    dossier_sha256: list[Digest]

    @model_validator(mode="after")
    def consistent(self):
        if self.response_origin != "synthetic" and self.response_origin != self.participant.kind:
            raise ValueError("Response origin must match participant")
        if [i.case for i in self.items] != list(range(1, len(self.items) + 1)):
            raise ValueError("Cases are numbered consecutively from one")
        if any((i.check_price is not None) != self.check_offered for i in self.items):
            raise ValueError("Every case has a check price exactly when checks are offered")
        if len(self.dossier_sha256) != len(self.items):
            raise ValueError("One dossier commitment per case")
        companies = [company_name(i.pair_seed, i.family) for i in self.items]
        if len(set(companies)) != len(companies):
            raise ValueError("Every case in a collection needs a distinct company name")
        return self


def world_for(item):
    return generate(item.pair_seed, item.family)[item.presentation]


def create(directory, participant, *, arm, items, check_offered, synthetic=False):
    participant = ParticipantDescriptor.model_validate(participant).root
    items = [Item.model_validate({"case": i + 1, **dict(item)}) for i, item in enumerate(items)]
    manifest = Manifest(
        study_id=str(uuid4()),
        created_at=now(),
        implementation_sha256=fingerprint(),
        participant=participant,
        response_origin="synthetic" if synthetic else participant.kind,
        arm=arm,
        check_offered=check_offered,
        items=items,
        dossier_sha256=[digest(encoded(render(world_for(i)))) for i in items],
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
    for item, expected in zip(manifest.items, manifest.dossier_sha256, strict=True):
        if digest(encoded(render(world_for(item)))) != expected:
            raise ValueError("A rendered dossier differs from its commitment")
    return manifest, digest(raw)


def position(manifest, answers):
    """The (case index, stage) now awaiting an answer, or None when every case is answered."""
    case, stage = 0, "assessment"
    for row in answers:
        if stage == "assessment" and row["answer"].get("check") == "buy":
            stage = "final"
        else:
            case, stage = case + 1, "assessment"
    return None if case == len(manifest.items) else (case, stage)


def public_trial(manifest, case, stage):
    item = manifest.items[case]
    world = world_for(item)
    return present(
        item.case,
        len(manifest.items),
        stage,
        render(world),
        note=structure_note(world) if manifest.arm == "explicit" else None,
        price=item.check_price,
        extra=check.document(world) if stage == "final" else None,
    )


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
        where = position(self.manifest, state["answers"])
        if where is None:
            return None
        trial = public_trial(self.manifest, *where)
        i = len(state["answers"])
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
            where = position(self.manifest, state["answers"])
            return {
                "complete": trial is None,
                "finished": state["completed_at"] is not None,
                "answered": len(state["answers"]),
                "cases_completed": len(self.manifest.items) if where is None else where[0],
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
                where = position(self.manifest, state["answers"])
                if where is None or len(state["locks"]) != n + 1:
                    raise ValueError("Read the current checkpoint before answering")
                trial = public_trial(self.manifest, *where)
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
            rows, answers = [], state["answers"]
            for i, row in enumerate(answers):
                trial = public_trial(self.manifest, *position(self.manifest, answers[:i]))
                rows.append({"trial": trial, "answer": row["answer"]})
            return {"history": rows}

    def finish(self):
        with self.state() as state:
            if position(self.manifest, state["answers"]) is not None:
                raise ValueError("Answer every case first")
            if state["completed_at"] is None:
                state["completed_at"] = now()
            return {
                "complete": True,
                "answered": len(state["answers"]),
                "completion_questions": [
                    "Were company outcomes revealed during this collection?",
                    "If you bought the independent survey, when was its cost charged?",
                    "Which parts of the dossiers, if any, were confusing or looked unreliable?",
                ],
            }


class Observation(Model):
    trial: dict
    answer: Answer
    answered_at: AwareDatetime
    locked_at: AwareDatetime


class Report(Model):
    schema_version: Literal["epistemics.research-report.v2"] = "epistemics.research-report.v2"
    manifest: Manifest
    manifest_sha256: Digest
    completed_at: AwareDatetime
    observations: list[Observation]
    analysis: dict
    limitations: list[str]

    @model_validator(mode="after")
    def reconstruction(self):
        if digest(encoded(self.manifest)) != self.manifest_sha256:
            raise ValueError("Report manifest binding changed")
        rows, previous = [], self.manifest.created_at
        for o in self.observations:
            where = position(self.manifest, rows)
            if where is None or o.trial != public_trial(self.manifest, *where):
                raise ValueError("Checkpoint differs from the frozen design and accepted answers")
            o.answer.validate_trial(o.trial)
            if not previous <= o.locked_at <= o.answered_at <= self.completed_at:
                raise ValueError("Each checkpoint must be locked before its answer")
            previous = o.answered_at
            rows.append({"answer": o.answer.model_dump(mode="json", exclude_none=True)})
        if position(self.manifest, rows) is not None:
            raise ValueError("A completed report answers every case")
        return self


LIMITATIONS = [
    "Fictional templated dossiers; findings concern this generator, presentation and payoff frame.",
    "Probability reports are observations, not internal beliefs.",
    "Neglect weights compare matched presentations across separate contexts; a single collection cannot estimate them.",
    "No outcome feedback during collection; learning from outcomes is not measured.",
    "Company demand is drawn from the posterior over every evidence item; scores describe the generated distribution only.",
    "Execution metadata is operator-asserted; no model identity attestation.",
]


def export(directory):
    from epistemics.research_world2.analysis import analyze

    service = CollectionService(directory)
    with service.state() as state:
        if state["completed_at"] is None:
            raise ValueError("Finish the collection before export")
        observations = []
        for i, row in enumerate(state["answers"]):
            lock = state["locks"][i]
            trial = public_trial(
                service.manifest, *position(service.manifest, state["answers"][:i])
            )
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
    from epistemics.research_world2.analysis import analyze

    directory = Path(directory)
    raw = (directory / "report.json").read_bytes()
    if digest(raw) != (directory / "report.sha256").read_text().strip():
        raise ValueError("Report byte hash mismatch")
    report = Report.model_validate_json(raw)
    if report.analysis != json.loads(encoded(analyze(report.manifest, report.observations))):
        raise ValueError("Stored analysis differs from recomputation")
    return report
