"""Transactional sequential collection. All design/export functions are operator-only."""

import json
import sqlite3
import uuid
from contextlib import closing, contextmanager
from pathlib import Path

from epistemics.predictive.collection_models import (
    COLLECTOR_VERSION,
    CollectionExport,
    CollectionManifest,
    CollectionSpec,
)
from epistemics.predictive.design import (
    INSTRUCTIONS,
    digest,
    encoded,
    episode,
    load_manifest,
    write_manifest,
)
from epistemics.predictive.models import Response
from epistemics.service import now

PUBLIC_INSTRUCTIONS = (
    INSTRUCTIONS + " Read the current checkpoint, submit one answer, and repeat until complete. "
    "Accepted answers cannot be edited. Exact retries are safe. Accepted history is returned "
    "on every read so you can resume. Then call finish_evaluation. Evaluator feedback remains "
    "withheld after completion."
)


def create_collection(design_directory, directory, spec):
    spec = CollectionSpec.model_validate(spec)
    design = load_manifest(design_directory)
    planned = [a.assignment_id for a in design.assignments]
    if not set(spec.assignment_ids) <= set(planned):
        raise ValueError("Unknown assignment in collection plan")
    if spec.purpose == "full_pilot" and spec.assignment_ids != planned:
        raise ValueError("A full pilot must include the entire ordered design")
    directory = Path(directory)
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    # A self-contained copy preserves the source's exact bytes, including whitespace.
    write_manifest(directory / "design", design)
    design_bytes = (Path(design_directory) / "manifest.json").read_bytes()
    (directory / "design" / "manifest.json").write_bytes(design_bytes)
    (directory / "design" / "manifest.sha256").write_text(digest(design_bytes) + "\n")
    manifest = CollectionManifest(
        **spec.model_dump(mode="json"),
        design_sha256=digest(design_bytes),
        instructions_sha256=digest(PUBLIC_INSTRUCTIONS.encode()),
        created_at=now(),
    )
    data = encoded(manifest)
    (directory / "collection.json").write_bytes(data)
    (directory / "collection.json").chmod(0o600)
    (directory / "collection.sha256").write_text(digest(data) + "\n")
    database = directory / "responses.sqlite3"
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("CREATE TABLE binding (hash TEXT NOT NULL)")
        db.execute("INSERT INTO binding VALUES (?)", (digest(data),))
        db.execute("CREATE TABLE episodes (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        db.execute("CREATE TABLE attempts (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        db.execute("CREATE TABLE exports (id INTEGER PRIMARY KEY, payload BLOB NOT NULL)")
    database.chmod(0o600)
    return manifest


def load_collection(directory):
    directory = Path(directory)
    data = (directory / "collection.json").read_bytes()
    fingerprint = digest(data)
    if fingerprint != (directory / "collection.sha256").read_text().strip():
        raise ValueError("Collection bytes changed after creation")
    manifest = CollectionManifest.model_validate_json(data)
    design = load_manifest(directory / "design")
    if manifest.design_sha256 != digest((directory / "design" / "manifest.json").read_bytes()):
        raise ValueError("Collection design binding changed")
    if manifest.instructions_sha256 != digest(PUBLIC_INSTRUCTIONS.encode()):
        raise ValueError("Collection instructions changed")
    planned = [a.assignment_id for a in design.assignments]
    if not set(manifest.assignment_ids) <= set(planned) or (
        manifest.purpose == "full_pilot" and manifest.assignment_ids != planned
    ):
        raise ValueError("Collection plan does not match design")
    return manifest, design, fingerprint


@contextmanager
def transaction(directory, expected_hash=None):
    manifest, design, fingerprint = load_collection(directory)
    if expected_hash is not None and fingerprint != expected_hash:
        raise ValueError("Collection binding changed during this process")
    # mode=rw prevents a lost database from silently becoming an empty new run.
    uri = (Path(directory).resolve() / "responses.sqlite3").as_uri() + "?mode=rw"
    with closing(sqlite3.connect(uri, uri=True, timeout=30)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT hash FROM binding").fetchall() != [(fingerprint,)]:
            raise ValueError("Stored response binding does not match collection")
        yield db, manifest, design


class CollectionService:
    def __init__(self, directory, assignment_id):
        self.directory = Path(directory)
        self.manifest, design, self.fingerprint = load_collection(directory)
        if assignment_id not in self.manifest.assignment_ids:
            raise ValueError("Assignment not planned for this collection")
        self.assignment = next(a for a in design.assignments if a.assignment_id == assignment_id)
        self.checkpoints = episode(self.assignment)

    @contextmanager
    def state(self):
        with transaction(self.directory, self.fingerprint) as (db, _, _):
            row = db.execute(
                "SELECT payload FROM episodes WHERE id=?", (self.assignment.assignment_id,)
            ).fetchone()
            state = (
                json.loads(row[0])
                if row
                else {"started_at": now(), "answers": [], "completion": None}
            )
            yield state
            db.execute(
                "INSERT OR REPLACE INTO episodes VALUES (?, ?)",
                (self.assignment.assignment_id, json.dumps(state, allow_nan=False)),
            )

    def describe(self):
        with self.state():
            return {
                "protocol_version": self.checkpoints[0].protocol_version,
                "collector_version": COLLECTOR_VERSION,
                "instructions": PUBLIC_INSTRUCTIONS,
                "total_checkpoints": len(self.checkpoints),
                "answer_schema": Response.model_json_schema(),
            }

    def get_trial(self):
        with self.state() as state:
            count = len(state["answers"])
            return {
                "answered": count,
                "complete": count == len(self.checkpoints),
                "checkpoint": self.checkpoints[count].model_dump(mode="json")
                if count < len(self.checkpoints)
                else None,
                "history": [
                    {"checkpoint": self.checkpoints[i].model_dump(mode="json"), **answer}
                    for i, answer in enumerate(state["answers"])
                ],
            }

    def submit(self, checkpoint_id, answer):
        data = Response.model_validate(answer).model_dump(mode="json")
        with self.state() as state:
            for i, old in enumerate(state["answers"]):
                if self.checkpoints[i].checkpoint_id == checkpoint_id:
                    if old["answer"] != data:
                        raise ValueError("An accepted answer cannot be changed")
                    return old["receipt"]
            index = len(state["answers"])
            if index == len(self.checkpoints):
                raise ValueError("Episode complete")
            if checkpoint_id != self.checkpoints[index].checkpoint_id:
                raise ValueError("Answer must reference the current checkpoint")
            receipt = {
                "accepted": True,
                "checkpoint_id": checkpoint_id,
                "accepted_at": now(),
                "answered": index + 1,
                "complete": index + 1 == len(self.checkpoints),
            }
            state["answers"].append({"answer": data, "receipt": receipt})
            return receipt

    def finish(self):
        with self.state() as state:
            if len(state["answers"]) != len(self.checkpoints):
                raise ValueError("Complete every checkpoint before finishing")
            if state["completion"] is None:
                state["completion"] = {
                    "complete": True,
                    "answered": len(self.checkpoints),
                    "completed_at": now(),
                }
            return state["completion"]

    def begin_attempt(self):
        with transaction(self.directory, self.fingerprint) as (db, _, _):
            if db.execute("SELECT 1 FROM exports").fetchone():
                raise ValueError("Collection already exported; no new transport attempts")
            row = db.execute(
                "SELECT payload FROM episodes WHERE id=?", (self.assignment.assignment_id,)
            ).fetchone()
            attempt_id = uuid.uuid4().hex
            payload = {
                "attempt_id": attempt_id,
                "assignment_id": self.assignment.assignment_id,
                "started_at": now(),
                "ended_at": None,
                "restored_answers": len(json.loads(row[0])["answers"]) if row else 0,
                "transport_status": "open",
            }
            db.execute("INSERT INTO attempts VALUES (?, ?)", (attempt_id, json.dumps(payload)))
            return attempt_id

    def end_attempt(self, attempt_id, *, failed=False):
        with transaction(self.directory, self.fingerprint) as (db, _, _):
            if db.execute("SELECT 1 FROM exports").fetchone():
                return  # The export is a frozen snapshot, including then-open transports.
            row = db.execute("SELECT payload FROM attempts WHERE id=?", (attempt_id,)).fetchone()
            if row is None:
                raise ValueError("Unknown transport attempt")
            payload = json.loads(row[0])
            if payload["assignment_id"] != self.assignment.assignment_id:
                raise ValueError("Attempt belongs to another assignment")
            if payload["transport_status"] == "open":
                payload.update(ended_at=now(), transport_status="error" if failed else "closed")
                db.execute(
                    "UPDATE attempts SET payload=? WHERE id=?", (json.dumps(payload), attempt_id)
                )


def collection_status(directory):
    """Operator progress; never fits partial cases or silently removes unattempted ones."""
    with transaction(directory) as (db, manifest, design):
        states = {i: json.loads(p) for i, p in db.execute("SELECT id,payload FROM episodes")}
        assignments = {a.assignment_id: a for a in design.assignments}
        return {
            "purpose": manifest.purpose,
            "response_origin": manifest.response_origin,
            "assignments": [
                {
                    "assignment_id": i,
                    "answered": len(states.get(i, {}).get("answers", [])),
                    "planned": len(episode(assignments[i])),
                    "finished": states.get(i, {}).get("completion") is not None,
                }
                for i in manifest.assignment_ids
            ],
            "attempts": [json.loads(p) for (p,) in db.execute("SELECT payload FROM attempts")],
        }


def export_collection(directory):
    """Private operator snapshot, only after all declared assignments finish; exact bytes stable."""
    with transaction(directory) as (db, manifest, design):
        old = db.execute("SELECT payload FROM exports WHERE id=1").fetchone()
        if old:
            return old[0]
        states = {i: json.loads(p) for i, p in db.execute("SELECT id,payload FROM episodes")}
        if any(states.get(i, {}).get("completion") is None for i in manifest.assignment_ids):
            raise ValueError("Every planned assignment must finish before export")
        assignments = {a.assignment_id: a for a in design.assignments}
        episodes = []
        for i in manifest.assignment_ids:
            state, assignment = states[i], assignments[i]
            observations = [
                {
                    "checkpoint": checkpoint,
                    "answer": answer["answer"],
                    "accepted_at": answer["receipt"]["accepted_at"],
                }
                for checkpoint, answer in zip(episode(assignment), state["answers"], strict=True)
            ]
            episodes.append(
                {
                    "assignment": assignment,
                    "started_at": state["started_at"],
                    "completed_at": state["completion"]["completed_at"],
                    "observations": observations,
                }
            )
        result = CollectionExport(
            collection_sha256=digest((Path(directory) / "collection.json").read_bytes()),
            collection=manifest,
            episodes=episodes,
            attempts=[
                json.loads(p) for (p,) in db.execute("SELECT payload FROM attempts ORDER BY rowid")
            ],
        )
        data = encoded(result)
        db.execute("INSERT INTO exports VALUES (1, ?)", (data,))
        return data
