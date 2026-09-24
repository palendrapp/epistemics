"""Private manifest and immutable, transactional answers; no operator data in MCP."""

import hashlib
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from epistemics.narrative.battery import INSTRUCTIONS, public_trial, schedule
from epistemics.narrative.models import Answer, Manifest, Observation, Report
from epistemics.participants import ParticipantDescriptor
from epistemics.service import now


def encoded(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, raw):
    path = Path(path)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError("Existing bytes differ; refuse overwrite") from None
    else:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)


def fingerprint():
    root = Path(__file__).parent
    paths = sorted(root.glob("*.py")) + sorted((root / "assets").glob("*"))
    paths += [
        root.parent / p
        for p in (
            "models.py",
            "participants.py",
            "service.py",
            "live/web.py",
        )
    ]
    return digest(
        b"".join(str(p.relative_to(root.parent)).encode() + b"\0" + p.read_bytes() for p in paths)
    )


def create(directory, participant, *, seed=None, synthetic=False):
    participant = ParticipantDescriptor.model_validate(participant).root
    design_seed = secrets.randbits(64) if seed is None else seed
    manifest = Manifest(
        study_id=str(uuid4()),
        created_at=now(),
        design_seed=design_seed,
        implementation_sha256=fingerprint(),
        participant=participant,
        response_origin="synthetic" if synthetic else participant.kind,
        context_policy="human_continuous_separate_company_cases"
        if participant.kind == "human"
        else "independent_episode_no_cross_case_history",
        assignments=schedule(design_seed),
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
        raise ValueError("Frozen evaluator changed; use the original version")
    return manifest, digest(raw)


class NarrativeService:
    def __init__(self, directory, assignment_id):
        self.directory = Path(directory)
        self.manifest, self.manifest_hash = load(directory)
        self.assignment = next(
            (a for a in self.manifest.assignments if a.assignment_id == assignment_id), None
        )
        if self.assignment is None:
            raise ValueError("Unknown assignment")
        self.database = self.directory / "responses.sqlite3"
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
        _, current = load(self.directory)
        if current != self.manifest_hash:
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

    def describe(self):
        return {
            "battery_version": self.manifest.battery_version,
            "total_trials": 4,
            "instructions": INSTRUCTIONS,
            "answer_schema": Answer.model_json_schema(),
            "use": "Development diagnostic; interpreted reports are not internal beliefs.",
        }

    def trial(self, state, index):
        query = state["answers"][1]["answer"]["query"] if index >= 2 else None
        return public_trial(self.assignment, index, query)

    def get_trial(self):
        with self.state() as state:
            n = len(state["answers"])
            return {
                "complete": n == 4,
                "answered": n,
                "trial": self.trial(state, n).model_dump(mode="json") if n < 4 else None,
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
        answer = Answer.model_validate(answer)
        data = answer.model_dump(mode="json")
        with self.state() as state:
            for row in state["answers"]:
                if row["receipt"]["trial_id"] == trial_id:
                    if row["answer"] != data:
                        raise ValueError("An accepted answer cannot be changed")
                    return row["receipt"]
            n = len(state["answers"])
            if n == 4 or trial_id != self.trial(state, n).trial_id:
                raise ValueError("Submit only the current checkpoint")
            answer.validate_stage(n)
            receipt = {
                "accepted": True,
                "trial_id": trial_id,
                "answered": n + 1,
                "complete": n == 3,
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


def export(directory):
    from epistemics.narrative.inference import analyze

    manifest, manifest_hash = load(directory)
    cases, completions = {}, []
    for a in manifest.assignments:
        with NarrativeService(directory, a.assignment_id).state() as state:
            if not state["completed_at"]:
                raise ValueError("All eight cases must finish before export")
            cases[a.assignment_id] = [
                Observation(
                    trial=public_trial(
                        a, i, state["answers"][1]["answer"]["query"] if i >= 2 else None
                    ),
                    answer=row["answer"],
                    answered_at=row["answered_at"],
                )
                for i, row in enumerate(state["answers"])
            ]
            completions.append(state["completed_at"])
    report = Report(
        manifest=manifest,
        manifest_sha256=manifest_hash,
        completed_at=max(completions),
        cases=cases,
        analysis=analyze(cases, manifest.assignments),
        limitations=[
            "Scaffolded event combinations, not unrestricted hypothesis discovery or a validated causal graph.",
            "Declared joint probabilities and forecasts are observations, not internal beliefs or uniquely identified priors.",
            "Own-report comparisons require stable event meanings and unchanged conditional expectations; elicitation can scaffold reasoning.",
            "Research information values concern the stated joint-state uncertainty objective, not profit, utility or general rationality.",
            "Matched presentations share sentences but single contrasts cannot distinguish framing from run-to-run variation.",
            "Authored outcomes are not random draws; no calibration, source reliability or valence trait is estimated.",
            "Point fits are descriptive report-generating comparisons with fixed elicited inputs; no posterior uncertainty or empirical predictive validation.",
            "Boundary inputs can make model fits ineligible or conditional references undefined; these remain in behavioral results.",
            "Human carryover differs from fresh agent contexts. Private files are not execution isolation.",
            "No passport trait issuance or intervention benefit established by this module.",
        ],
    )

    raw = encoded(report)
    save(Path(directory) / "report.json", raw)
    save(Path(directory) / "report.sha256", (digest(raw) + "\n").encode())
    return report
