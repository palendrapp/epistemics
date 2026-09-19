"""One assigned episode per MCP process. No private study state in public receipts."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from epistemics.discovery.models import DiscoveryAnswer
from epistemics.service import now
from epistemics.study import STUDY_VERSION
from epistemics.study.design import digest, episode, load_manifest
from epistemics.study.models import EpisodeReport, StudyObservation


class StudyService:
    def __init__(self, directory, assignment_id):
        self.directory = Path(directory)
        self.manifest, self.manifest_hash = load_manifest(directory)
        self.assignment = next(
            (a for a in self.manifest.assignments if a.assignment_id == assignment_id), None
        )
        if self.assignment is None:
            raise ValueError("Unknown study assignment")
        self.records = episode(self.assignment)
        self.database = self.directory / "responses.sqlite3"
        with sqlite3.connect(self.database) as db:
            db.execute("CREATE TABLE IF NOT EXISTS episodes (id TEXT PRIMARY KEY, payload TEXT)")
            db.execute(
                "INSERT OR IGNORE INTO episodes VALUES (?, ?)",
                (assignment_id, json.dumps({"answers": [], "report": None})),
            )
        self.database.chmod(0o600)

    @contextmanager
    def state(self):
        # Prevent a changed manifest or analysis implementation from entering an active study.
        load_manifest(self.directory)
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
            "battery_version": STUDY_VERSION,
            "total_trials": 11,
            "instructions": "Assess the current company using the public material. Keep context "
            "within this episode. Get the current trial, submit one answer, and repeat. Accepted "
            "answers cannot be edited. Finish after all trials. Outcomes and evaluator analyses "
            "are withheld throughout the study.",
        }

    def get_trial(self):
        with self.state() as state:
            index = len(state["answers"])
            return {
                "complete": index == 11,
                "answered": index,
                "trial": self.records[index]["trial"] if index < 11 else None,
            }

    def submit(self, trial_id, answer):
        answer = DiscoveryAnswer.model_validate(answer)
        data = answer.model_dump(mode="json")
        with self.state() as state:
            answers = state["answers"]
            for index, old in enumerate(answers):
                if self.records[index]["trial"]["trial_id"] == trial_id:
                    if old["answer"] != data:
                        raise ValueError("An accepted answer cannot be changed")
                    return old["receipt"]
            if len(answers) == 11:
                raise ValueError("Episode complete")
            trial = self.records[len(answers)]["trial"]
            if trial_id != trial["trial_id"]:
                raise ValueError("Answer must reference the current trial")
            if len(set(answer.evidence_ids)) != len(answer.evidence_ids) or not set(
                answer.evidence_ids
            ) <= {d["document_id"] for d in trial["documents"]}:
                raise ValueError(
                    "evidence_ids must uniquely reference currently available documents"
                )
            if set(answer.source_accuracy) != set(trial["source_probe_ids"]):
                raise ValueError("source_accuracy must match requested probes")
            if (answer.conditional_growth_probability is not None) != trial["conditional_probe"]:
                raise ValueError("conditional_growth_probability must match requested probe")
            if set(answer.extracted_values) != set(trial["extraction_keys"]):
                raise ValueError("extracted_values must match requested probes")
            receipt = {
                "accepted": True,
                "trial_id": trial_id,
                "answered": len(answers) + 1,
                "complete": len(answers) == 10,
            }
            answers.append({"answer": data, "answered_at": now(), "receipt": receipt})
            return receipt

    def finish(self):
        with self.state() as state:
            if len(state["answers"]) != 11:
                raise ValueError("Complete every trial before finishing")
            if state["report"] is None:
                report = EpisodeReport(
                    study_id=self.manifest.study_id,
                    manifest_sha256=self.manifest_hash,
                    implementation_sha256=self.manifest.implementation_sha256,
                    agent=self.manifest.agent,
                    response_origin=self.manifest.response_origin,
                    assignment=self.assignment,
                    private_case=self.records[0]["truth"],
                    completed_at=now(),
                    observations=[
                        StudyObservation(
                            trial=record["trial"],
                            answer=answer["answer"],
                            answered_at=answer["answered_at"],
                        )
                        for record, answer in zip(self.records, state["answers"], strict=True)
                    ],
                )
                state["report"] = report.model_dump(mode="json")
            # A participant never receives the seed, split, other responses or actual outcome.
            return {"complete": True, "answered": 11, "report_stored": True}


def export_reports(directory):
    """Operator export only after every planned assignment is complete; no silent attrition."""
    directory = Path(directory)
    manifest, _ = load_manifest(directory)
    with sqlite3.connect(directory / "responses.sqlite3") as db:
        rows = {
            sid: json.loads(payload)
            for sid, payload in db.execute("SELECT id,payload FROM episodes")
        }
    if any(
        a.assignment_id not in rows or rows[a.assignment_id]["report"] is None
        for a in manifest.assignments
    ):
        raise ValueError("All planned assignments must finish before exporting or fitting")
    reports = directory / "reports"
    reports.mkdir(exist_ok=True)
    hashes = {}
    for a in manifest.assignments:
        report = EpisodeReport.model_validate(rows[a.assignment_id]["report"])
        data = (report.model_dump_json(indent=2) + "\n").encode()
        path = reports / f"{a.assignment_id}.json"
        if path.exists() and path.read_bytes() != data:
            raise ValueError("Refusing to overwrite different report bytes")
        path.write_bytes(data)
        path.chmod(0o600)
        hashes[path.name] = digest(data)
    (directory / "report-hashes.json").write_text(json.dumps(hashes, indent=2) + "\n")
    return hashes
