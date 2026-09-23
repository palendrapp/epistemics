"""Immutable operator binding and transactional public collection for one assignment."""

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from epistemics.investigation3 import BATTERY_VERSION
from epistemics.investigation3.battery import INSTRUCTIONS, public_trial
from epistemics.investigation3.inference import analysis, answer_vector, report_log_likelihood
from epistemics.investigation3.models import (
    Answer as InvestigationAnswer,
)
from epistemics.investigation3.models import (
    Manifest as InvestigationManifest,
)
from epistemics.investigation3.models import (
    Observation as InvestigationObservation,
)
from epistemics.investigation3.models import (
    Report as InvestigationReport,
)
from epistemics.investigation3.world import generate
from epistemics.service import now


def encoded(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint():
    from epistemics.investigation2.service import fingerprint as original_fingerprint

    root = Path(__file__).resolve().parent
    paths = sorted(root.glob("*.py")) + sorted((root / "assets").glob("*"))
    return digest(
        original_fingerprint().encode()
        + b"".join(
            str(p.relative_to(root)).encode() + b"\0" + p.read_bytes() for p in paths if p.is_file()
        )
        + (root.parent / "live/web.py").read_bytes()
    )


def write_private(path, data):
    # Restrict permissions at creation, not only after bytes have been written.
    import os

    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def create(directory, participant, *, seed=None, mode="discovery", synthetic=False):
    from epistemics.investigation3.design import schedule
    from epistemics.participants import ParticipantDescriptor

    participant = ParticipantDescriptor.model_validate(participant).root
    assignments = schedule(secrets.randbits(64) if seed is None else seed, mode=mode)
    manifest = InvestigationManifest(
        study_id=str(uuid4()),
        created_at=now(),
        implementation_sha256=fingerprint(),
        participant=participant,
        context_policy="human_continuous_separate_company_cases"
        if participant.kind == "human"
        else "independent_episode_no_cross_case_history",
        response_origin="synthetic" if synthetic else participant.kind,
        assignments=assignments,
    )
    directory = Path(directory)
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    data = encoded(manifest)
    write_private(directory / "manifest.json", data)
    write_private(directory / "manifest.sha256", (digest(data) + "\n").encode())
    return manifest


def load(directory):
    directory = Path(directory)
    raw = (directory / "manifest.json").read_bytes()
    expected = (directory / "manifest.sha256").read_text().strip()
    manifest = InvestigationManifest.model_validate_json(raw)
    if digest(raw) != expected:
        raise ValueError("Frozen manifest bytes changed")
    if manifest.implementation_sha256 != fingerprint():
        raise ValueError("The frozen evaluator implementation changed; use its original version")
    return manifest, expected


class InvestigationService:
    def __init__(self, directory, assignment_id):
        self.directory = Path(directory)
        self.manifest, self.manifest_hash = load(directory)
        self.assignment = next(
            (a for a in self.manifest.assignments if a.assignment_id == assignment_id), None
        )
        if self.assignment is None:
            raise ValueError("Unknown assignment")
        self.world = generate(self.assignment.seed, self.assignment.offset)
        self.database = self.directory / "responses.sqlite3"
        # The containing directory is private; serialize initialization and writes.
        with sqlite3.connect(self.database) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS episodes (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            db.execute(
                "INSERT OR IGNORE INTO episodes VALUES (?, ?)",
                (assignment_id, json.dumps({"answers": [], "completed_at": None})),
            )
        self.database.chmod(0o600)

    @contextmanager
    def state(self):
        _, current_hash = load(self.directory)
        if current_hash != self.manifest_hash:
            raise ValueError("Assignment binding changed")
        with sqlite3.connect(self.database, timeout=30) as db:
            db.execute("BEGIN IMMEDIATE")
            state = json.loads(
                db.execute(
                    "SELECT payload FROM episodes WHERE id=?", (self.assignment.assignment_id,)
                ).fetchone()[0]
            )
            yield state
            db.execute(
                "UPDATE episodes SET payload=? WHERE id=?",
                (json.dumps(state, allow_nan=False), self.assignment.assignment_id),
            )

    def trial(self, state, index):
        branch = state["answers"][1]["answer"]["query"] if index >= 2 else None
        return public_trial(self.assignment, self.world, index, branch)

    def describe(self):
        return {
            "battery_version": BATTERY_VERSION,
            "total_trials": 4,
            "mode": self.assignment.mode,
            "instructions": INSTRUCTIONS,
            "answer_schema": InvestigationAnswer.model_json_schema(),
            "use": "Development module; results are conditional descriptive measurements.",
        }

    def get_trial(self):
        with self.state() as state:
            index = len(state["answers"])
            return {
                "complete": index == 4,
                "answered": index,
                "trial": self.trial(state, index).model_dump(mode="json") if index < 4 else None,
            }

    def get_history(self):
        with self.state() as state:
            return {
                "history": [
                    {
                        "trial": self.trial(state, i).model_dump(mode="json"),
                        "answer": row["answer"],
                        "receipt": row["receipt"],
                    }
                    for i, row in enumerate(state["answers"])
                ]
            }

    def submit(self, trial_id, answer):
        answer = InvestigationAnswer.model_validate(answer)
        # This also validates the declared 0.01 increments and finite endpoint reports.
        report_log_likelihood(answer_vector(answer), [0.5] * 3)
        data = answer.model_dump(mode="json")
        with self.state() as state:
            for row in state["answers"]:
                if row["receipt"]["trial_id"] == trial_id:
                    if row["answer"] != data:
                        raise ValueError("An accepted answer cannot be changed")
                    return row["receipt"]
            index = len(state["answers"])
            if index == 4:
                raise ValueError("Episode complete")
            trial = self.trial(state, index)
            if trial_id != trial.trial_id:
                raise ValueError("Submit only the current trial")
            if (answer.query is not None) != (index == 1):
                raise ValueError("Choose research only at Evidence and research")
            if set(answer.expectations or {}) != set(trial.expectation_queries):
                raise ValueError("Submit all requested research expectations at this stage only")
            for row in (answer.expectations or {}).values():
                report_log_likelihood(list(row.model_dump().values()), [0.5] * 3)
            receipt = {
                "accepted": True,
                "trial_id": trial_id,
                "answered": index + 1,
                "complete": index == 3,
            }
            state["answers"].append({"answer": data, "answered_at": now(), "receipt": receipt})
            return receipt

    def finish(self):
        with self.state() as state:
            if len(state["answers"]) != 4:
                raise ValueError("Complete every checkpoint first")
            if state["completed_at"] is None:
                state["completed_at"] = now()
            return {"complete": True, "answered": 4, "report_stored": True}


def status(directory):
    manifest, _ = load(directory)
    database = Path(directory) / "responses.sqlite3"
    rows = {}
    if database.exists():
        with sqlite3.connect(database) as db:
            rows = {
                sid: json.loads(payload)
                for sid, payload in db.execute("SELECT id,payload FROM episodes")
            }
    return {
        "planned": len(manifest.assignments),
        "completed": sum(
            bool(rows.get(a.assignment_id, {}).get("completed_at")) for a in manifest.assignments
        ),
        "assignments": [
            {
                "assignment_id": a.assignment_id,
                "accepted_answers": len(rows.get(a.assignment_id, {}).get("answers", [])),
                "complete": bool(rows.get(a.assignment_id, {}).get("completed_at")),
            }
            for a in manifest.assignments
        ],
    }


def export(directory):
    from epistemics.investigation3.render import collection_analysis, render

    manifest, manifest_hash = load(directory)
    progress = status(directory)
    if progress["completed"] != progress["planned"]:
        raise ValueError("All planned assignments must finish before private export")
    directory = Path(directory)
    report_directory = directory / "reports"
    report_directory.mkdir(mode=0o700, exist_ok=True)
    hashes = {}
    reports = []
    for assignment in manifest.assignments:
        service = InvestigationService(directory, assignment.assignment_id)
        with service.state() as state:
            observations = [
                InvestigationObservation(
                    trial=service.trial(state, i),
                    answer=row["answer"],
                    answered_at=row["answered_at"],
                )
                for i, row in enumerate(state["answers"])
            ]
            report = InvestigationReport(
                manifest=manifest,
                manifest_sha256=manifest_hash,
                assignment=assignment,
                observations=observations,
                private_world=service.world,
                completed_at=state["completed_at"],
                analysis=analysis(observations, service.world),
                limitations=[
                    "Development-only measurements in one authored mechanism, not a validated passport dimension.",
                    "Probabilities are reports, not access to internal beliefs; source/auxiliary hypotheses are scaffolded, not unrestricted hypothesis generation.",
                    "Observer predictions and research value are conditional on its assumptions; only calibration discloses those assumptions.",
                    "Initialization alternatives condition on reported starts and chosen branches; noisy-start states are integrated across each episode. Fits do not establish stable traits, real-participant parameter recovery, transfer or intervention benefit.",
                    "Report-implied research values require coherent prospective answers; they do not reveal internal utilities. Research cases are selected on the full visible operating record; background reference values are working baselines, not selection-adjusted priors.",
                    "Operator-asserted identity and execution; private local files are not OS isolation.",
                ],
            )
        raw = encoded(report)
        reports.append(report)
        path = report_directory / f"{assignment.assignment_id}.json"
        if path.exists():
            if path.read_bytes() != raw:
                raise ValueError("Existing report bytes disagree; never overwrite")
        else:
            write_private(path, raw)
        hashes[path.name] = digest(raw)
    aggregate = collection_analysis(reports, hashes)
    aggregate_raw = encoded(aggregate)
    aggregate_path = directory / "analysis.json"
    if aggregate_path.exists():
        if aggregate_path.read_bytes() != aggregate_raw:
            raise ValueError("Existing collection analysis changed")
    else:
        write_private(aggregate_path, aggregate_raw)
    summary = render(reports, aggregate).encode()
    summary_path = directory / "summary.md"
    if summary_path.exists():
        if summary_path.read_bytes() != summary:
            raise ValueError("Existing readable summary changed")
    else:
        write_private(summary_path, summary)
    raw_hashes = encoded(hashes)
    hash_path = directory / "report-hashes.json"
    if hash_path.exists():
        if hash_path.read_bytes() != raw_hashes:
            raise ValueError("Export hashes changed")
    else:
        write_private(hash_path, raw_hashes)
    return hashes
