"""One transactional session engine for browser and MCP adapters."""

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from epistemics.discovery.models import DiscoveryAnswer
from epistemics.live import EVALUATOR_VERSION, PROTOCOL_VERSION
from epistemics.live.analysis import LIMITATIONS, analyze
from epistemics.live.battery import describe, generate, instructions_digest, protocol_digest
from epistemics.live.models import CoreReport, CoreTrial
from epistemics.models import Answer
from epistemics.participants import EvaluationConditions, ParticipantDescriptor, SessionContext


class UnknownSession(ValueError):
    pass


class SessionConflict(ValueError):
    pass


def now():
    return datetime.now(UTC).isoformat()


class LiveService:
    def __init__(self, database: str | Path):
        self.protocol_sha256 = protocol_digest()
        self.database = Path(database)
        self.database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        new_database = not self.database.exists()
        with sqlite3.connect(self.database) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS live_sessions ("
                "id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL, "
                "request_sha256 TEXT NOT NULL, payload TEXT NOT NULL)"
            )
        if new_database:
            self.database.chmod(0o600)

    def _running_version(self):
        if protocol_digest() != self.protocol_sha256:
            raise SessionConflict(
                "Evaluator files changed; restart the service before starting a new run"
            )

    def describe(self):
        self._running_version()
        return describe()

    @contextmanager
    def _session(self, session_id):
        with sqlite3.connect(self.database, timeout=30) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload FROM live_sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                raise UnknownSession("Unknown session")
            session = json.loads(row[0])
            yield session
            db.execute(
                "UPDATE live_sessions SET payload = ? WHERE id = ?",
                (
                    json.dumps(session, allow_nan=False),
                    session_id,
                ),
            )

    def start(
        self,
        participant,
        *,
        request_id,
        conditions=None,
        instructions_accepted=False,
        response_origin=None,
        seed=None,
    ):
        self._running_version()
        participant = ParticipantDescriptor.model_validate(participant).root
        conditions = EvaluationConditions.model_validate(conditions or {})
        if instructions_accepted is not True:
            raise ValueError("Read and accept the instructions before starting")
        if not isinstance(request_id, str) or not 16 <= len(request_id) <= 128:
            raise ValueError("Use a random request ID of 16–128 characters for idempotent start")
        expected_instructions = instructions_digest()
        if conditions.instructions_sha256 not in {None, expected_instructions}:
            raise ValueError("Instructions do not match this protocol")
        if conditions.time_limit_seconds is not None or conditions.elapsed_seconds is not None:
            raise ValueError("Core 0.1 has no time limit; elapsed time is measured by the service")
        conditions.instructions_sha256 = expected_instructions
        if conditions.context_policy not in {None, "continuous"}:
            raise ValueError("Core 0.1 requires continuous session context")
        conditions.context_policy = "continuous"
        origin = response_origin or participant.kind
        started = now()
        context = SessionContext(
            session_id=str(uuid4()),
            participant=participant,
            response_origin=origin,
            protocol_version=PROTOCOL_VERSION,
            protocol_sha256=self.protocol_sha256,
            evaluator_version=EVALUATOR_VERSION,
            conditions=conditions,
            started_at=started,
            completion="not_started",
            accepted_answers=0,
            planned_answers=34,
        )
        request = json.dumps(
            {
                "participant": participant.model_dump(mode="json"),
                "conditions": conditions.model_dump(),
                "origin": origin,
                "instructions_accepted": True,
                "seed_override": seed,
            },
            sort_keys=True,
            allow_nan=False,
        ).encode()
        request_sha = hashlib.sha256(request).hexdigest()
        request_key = hashlib.sha256(request_id.encode()).hexdigest()
        with sqlite3.connect(self.database, timeout=30) as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT request_sha256, payload FROM live_sessions WHERE request_key = ?",
                (request_key,),
            ).fetchone()
            if existing:
                if existing[0] != request_sha:
                    raise SessionConflict(
                        "Start request ID was already used with different metadata"
                    )
                return self._start_receipt(json.loads(existing[1]))
            private_seed = secrets.randbits(52) if seed is None else seed
            session = {
                "context": context.model_dump(mode="json"),
                "seed": private_seed,
                "trials": generate(private_seed),
                "answers": [],
                "report_json": None,
                "passport_json": None,
                "instructions_accepted": True,
            }
            db.execute(
                "INSERT INTO live_sessions VALUES (?, ?, ?, ?)",
                (
                    context.session_id,
                    request_key,
                    request_sha,
                    json.dumps(session, allow_nan=False),
                ),
            )
        return self._start_receipt(session)

    @staticmethod
    def _start_receipt(session):
        return {
            "session_id": session["context"]["session_id"],
            "total_trials": 34,
            "protocol_version": session["context"]["protocol_version"],
            "protocol_sha256": session["context"]["protocol_sha256"],
        }

    def _current_version(self, session):
        context = session["context"]
        if (
            context["protocol_sha256"] != protocol_digest()
            or context["protocol_sha256"] != self.protocol_sha256
            or context["evaluator_version"] != EVALUATOR_VERSION
        ):
            raise SessionConflict("Continue this session with its original evaluator version")

    def get_trial(self, session_id):
        with self._session(session_id) as session:
            position = len(session["answers"])
            if position < 34:
                self._current_version(session)
            return {
                "context": session["context"],
                "complete": position == 34,
                "answered": position,
                "total_trials": 34,
                "trial": session["trials"][position]["trial"] if position < 34 else None,
                "history": [
                    {
                        "trial_id": session["trials"][i]["trial"]["trial_id"],
                        "module": session["trials"][i]["trial"]["module"],
                        "answer": a["answer"],
                        "answered_at": a["answered_at"],
                    }
                    for i, a in enumerate(session["answers"])
                ],
            }

    @staticmethod
    def _validate_answer(trial, answer):
        if trial.module == "calibration":
            result = Answer.model_validate(answer)
            if result.source_probability is not None:
                raise ValueError("Calibration requests only a hypothesis probability")
            return result.model_dump()
        result = DiscoveryAnswer.model_validate(answer)
        payload = trial.payload
        available = {d.document_id for d in payload.documents}
        if (
            len(set(result.evidence_ids)) != len(result.evidence_ids)
            or not set(result.evidence_ids) <= available
        ):
            raise ValueError("Citations must be unique, already available document IDs")
        if set(result.source_accuracy) != set(payload.source_probe_ids):
            raise ValueError("Answer exactly the requested source-accuracy questions")
        if (result.conditional_growth_probability is not None) != payload.conditional_probe:
            raise ValueError("Answer the conditional probability only when requested")
        if set(result.extracted_values) != set(payload.extraction_keys):
            raise ValueError("Answer exactly the requested extraction questions")
        return result.model_dump()

    def submit(self, session_id, trial_id, answer):
        with self._session(session_id) as session:
            rows, answers = session["trials"], session["answers"]
            index = next(
                (i for i, row in enumerate(rows) if row["trial"]["trial_id"] == trial_id), None
            )
            if index is None or index > len(answers):
                raise SessionConflict("Answer must reference the current trial")
            trial = CoreTrial.model_validate(rows[index]["trial"])
            accepted = self._validate_answer(trial, answer)
            if index < len(answers):
                if accepted != answers[index]["answer"]:
                    raise SessionConflict("An accepted answer cannot be changed")
                return answers[index]["receipt"]
            self._current_version(session)
            timestamp = now()
            receipt = {
                "accepted": True,
                "trial_id": trial_id,
                "answered": index + 1,
                "complete": index + 1 == 34,
            }
            answers.append({"answer": accepted, "answered_at": timestamp, "receipt": receipt})
            context = session["context"]
            context["accepted_answers"] = len(answers)
            context["completion"] = "complete" if receipt["complete"] else "partial"
            if receipt["complete"]:
                context["completed_at"] = timestamp
                context["conditions"]["elapsed_seconds"] = (
                    datetime.fromisoformat(timestamp)
                    - datetime.fromisoformat(context["started_at"])
                ).total_seconds()
            return receipt

    def report_bytes(self, session_id):
        with self._session(session_id) as session:
            if session["report_json"] is None:
                if len(session["answers"]) != 34:
                    raise SessionConflict("Complete all 34 checkpoints before viewing results")
                self._current_version(session)
                discovery, calibration = analyze(session["trials"], session["answers"])
                report = CoreReport(
                    context=session["context"],
                    seed=session["seed"],
                    instructions_accepted=True,
                    discovery=discovery,
                    calibration=calibration,
                    limitations=LIMITATIONS,
                )
                session["report_json"] = report.model_dump_json(indent=2) + "\n"
            return session["report_json"].encode()

    def passport_bytes(self, session_id):
        from epistemics.passport.build import build_passport

        raw = self.report_bytes(session_id)
        with self._session(session_id) as session:
            if session["passport_json"] is None:
                self._current_version(session)
                passport = build_passport(raw, created_at=session["context"]["completed_at"])
                session["passport_json"] = passport.model_dump_json(indent=2) + "\n"
            return session["passport_json"].encode()
