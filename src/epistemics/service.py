"""Transactional, resumable local evaluations; one accepted answer per trial."""

import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from epistemics import __version__
from epistemics.analysis import analyze
from epistemics.battery import BATTERY_SHA256, BATTERY_VERSION, generate_battery
from epistemics.models import AgentDescriptor, Answer, Observation, Report


def now() -> str:
    return datetime.now(UTC).isoformat()


class EvaluationService:
    def __init__(self, database: str | Path):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    @contextmanager
    def _session(self, session_id: str):
        with sqlite3.connect(self.database, timeout=30) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT payload FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                raise ValueError("Unknown session")
            session = json.loads(row[0])
            yield session
            connection.execute(
                "UPDATE sessions SET payload = ? WHERE id = ?",
                (json.dumps(session, allow_nan=False), session_id),
            )

    def start(
        self,
        agent: AgentDescriptor,
        *,
        seed: int | None = None,
        battery: str = "belief",
        discovery_variant: dict[str, str] | None = None,
    ) -> dict:
        if battery not in {"belief"}:
            raise ValueError("Unknown battery")
        if discovery_variant is not None and battery != "discovery":
            raise ValueError("discovery_variant applies only to the discovery battery")
        seed = secrets.randbits(52) if seed is None else seed
        module = {}.get(battery)
        version = module.BATTERY_VERSION if module else BATTERY_VERSION
        digest = module.battery_sha256() if module else BATTERY_SHA256
        generate = module.generate_battery if module else generate_battery
        session_id = str(uuid4())
        session = {
            "id": session_id,
            "battery": battery,
            "seed": seed,
            "agent": agent.model_dump(),
            "started_at": now(),
            "trials": generate(seed),
            "answers": [],
            "report": None,
            "battery_version": version,
            "battery_sha256": digest,
            "evaluator_version": __version__,
        }
        with sqlite3.connect(self.database) as connection:
            connection.execute(
                "INSERT INTO sessions VALUES (?, ?)", (session_id, json.dumps(session))
            )
        return {
            "session_id": session_id,
            "total_trials": len(session["trials"]),
            "battery_version": version,
            "battery_sha256": digest,
        }

    def get_trial(self, session_id: str) -> dict:
        with self._session(session_id) as session:
            position = len(session["answers"])
            if position == len(session["trials"]):
                return {"complete": True, "answered": position, "trial": None}
            return {
                "complete": False,
                "answered": position,
                "trial": session["trials"][position]["trial"],
            }

    def submit(self, session_id: str, trial_id: str, answer: Answer | Answer | Answer) -> dict:
        with self._session(session_id) as session:
            expected = Answer
            if not isinstance(answer, expected):
                raise ValueError(f"This session requires {expected.__name__}")
            trials, answers = (session["trials"], session["answers"])
            for i, previous in enumerate(answers):
                if trials[i]["trial"]["trial_id"] == trial_id:
                    if previous["answer"] != answer.model_dump():
                        raise ValueError("An accepted answer cannot be changed")
                    return previous["receipt"]
            if len(answers) == len(trials):
                raise ValueError("Evaluation is complete")
            current = trials[len(answers)]
            if current["trial"]["trial_id"] != trial_id:
                raise ValueError("Answer must reference the current trial")
            requires_source = current["trial"]["task"] == "source_reliability"
            if True and requires_source != (answer.source_probability is not None):
                raise ValueError("source_probability is required only for source_reliability")
            receipt = {
                "accepted": True,
                "trial_id": trial_id,
                "answered": len(answers) + 1,
                "complete": len(answers) + 1 == len(trials),
            }
            if current["trial"]["task"] == "reversal_learning":
                receipt["outcome"] = current["truth"]["outcome"]
            answers.append(
                {"answer": answer.model_dump(), "answered_at": now(), "receipt": receipt}
            )
            return receipt

    def finish(self, session_id: str) -> Report | Report | Report:
        with self._session(session_id) as session:
            report_type = Report
            if session["report"] is not None:
                return report_type.model_validate(session["report"])
            if len(session["answers"]) != len(session["trials"]):
                raise ValueError("Complete every trial before requesting a report")
            module = {}.get(session.get("battery"))
            if (
                session["battery_sha256"] != (module.battery_sha256() if module else BATTERY_SHA256)
                or session["evaluator_version"] != __version__
            ):
                raise ValueError("Finish this session using its original evaluator version")
            observations = [
                Observation(
                    trial=t["trial"],
                    truth=t["truth"],
                    answer=a["answer"],
                    answered_at=a["answered_at"],
                )
                for t, a in zip(session["trials"], session["answers"], strict=True)
            ]
            metrics, parameters, fits = analyze(observations)
            report = Report(
                evaluator_version=__version__,
                battery_version=session["battery_version"],
                battery_sha256=session["battery_sha256"],
                session_id=session_id,
                agent=session["agent"],
                started_at=session["started_at"],
                completed_at=now(),
                seed=session["seed"],
                metrics=metrics,
                parameters=parameters,
                model_fits=fits,
                observations=observations,
                limitations=[
                    "Behavioral reports in synthetic tasks do not establish private beliefs or general rationality.",
                    "Agent identity, model version and configuration are operator assertions, not remote attestation.",
                    "Bootstrap intervals describe this run, not model-family or between-run uncertainty.",
                    "Sequential fits use 32 training and 16 held-out reports; near-optimal ranges are not confidence intervals.",
                    "Explicit probabilities also measure instruction following and arithmetic; replicate with paraphrases and budgets.",
                    "Balanced signal conditions support identification; outcome scores describe this designed sample.",
                    "No task/seed secrecy against agents with evaluator filesystem access; use an isolated evaluator host.",
                ],
            )
            session["report"] = report.model_dump(mode="json")
            return report
