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
from epistemics.company import battery as company_battery
from epistemics.company.models import CompanyAnswer, CompanyObservation, CompanyReport
from epistemics.discovery import battery as discovery_battery
from epistemics.discovery.models import (
    DiscoveryAnswer,
    DiscoveryObservation,
    DiscoveryReport,
    PrivateCase,
)
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
        # Serializes changes across threads/processes; rollback leaves a rejected answer untouched.
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
        # Seed override is evaluator-side only, used for recovery studies/tests. MCP never exposes it.
        if battery not in {"belief", "company", "discovery"}:
            raise ValueError("Unknown battery")
        if discovery_variant is not None and battery != "discovery":
            raise ValueError("discovery_variant applies only to the discovery battery")
        seed = secrets.randbits(52) if seed is None else seed
        module = {"company": company_battery, "discovery": discovery_battery}.get(battery)
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
            "trials": generate(seed, variant=discovery_variant)
            if battery == "discovery"
            else generate(seed),
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

    def submit(
        self, session_id: str, trial_id: str, answer: Answer | CompanyAnswer | DiscoveryAnswer
    ) -> dict:
        with self._session(session_id) as session:
            is_company = session.get("battery") == "company"
            is_discovery = session.get("battery") == "discovery"
            expected = DiscoveryAnswer if is_discovery else CompanyAnswer if is_company else Answer
            if not isinstance(answer, expected):
                raise ValueError(f"This session requires {expected.__name__}")
            trials, answers = session["trials"], session["answers"]
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
            if not (is_company or is_discovery) and requires_source != (
                answer.source_probability is not None
            ):
                raise ValueError("source_probability is required only for source_reliability")
            if is_company or is_discovery:
                key = "documents" if is_discovery else "evidence"
                available = {e["document_id"] for e in current["trial"][key]}
                if len(set(answer.evidence_ids)) != len(answer.evidence_ids):
                    raise ValueError("evidence_ids must not contain duplicates")
                if not set(answer.evidence_ids) <= available:
                    raise ValueError("evidence_ids must reference documents already available")
            if is_discovery:
                trial = current["trial"]
                if set(answer.source_accuracy) != set(trial["source_probe_ids"]):
                    raise ValueError(
                        "source_accuracy must contain exactly the requested source probes"
                    )
                if (answer.conditional_growth_probability is not None) != trial[
                    "conditional_probe"
                ]:
                    raise ValueError(
                        "conditional_growth_probability is required only at conditional probes"
                    )
                if set(answer.extracted_values) != set(trial["extraction_keys"]):
                    raise ValueError("extracted_values must contain exactly the requested keys")
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

    def finish(self, session_id: str) -> Report | CompanyReport | DiscoveryReport:
        with self._session(session_id) as session:
            is_company = session.get("battery") == "company"
            is_discovery = session.get("battery") == "discovery"
            report_type = (
                DiscoveryReport if is_discovery else CompanyReport if is_company else Report
            )
            if session["report"] is not None:
                return report_type.model_validate(session["report"])
            if len(session["answers"]) != len(session["trials"]):
                raise ValueError("Complete every trial before requesting a report")
            module = {"company": company_battery, "discovery": discovery_battery}.get(
                session.get("battery")
            )
            if (
                session["battery_sha256"] != (module.battery_sha256() if module else BATTERY_SHA256)
                or session["evaluator_version"] != __version__
            ):
                raise ValueError("Finish this session using its original evaluator version")
            if is_discovery:
                from epistemics.discovery.analysis import LIMITATIONS as DISCOVERY_LIMITATIONS
                from epistemics.discovery.analysis import analyze as analyze_discovery
                from epistemics.discovery.world import OBSERVER_ASSUMPTIONS

                observations = [
                    DiscoveryObservation(
                        trial=t["trial"], answer=a["answer"], answered_at=a["answered_at"]
                    )
                    for t, a in zip(session["trials"], session["answers"], strict=True)
                ]
                private = PrivateCase.model_validate(session["trials"][0]["truth"])
                metrics, models = analyze_discovery(observations, private)
                report = DiscoveryReport(
                    evaluator_version=__version__,
                    battery_sha256=session["battery_sha256"],
                    session_id=session_id,
                    agent=session["agent"],
                    started_at=session["started_at"],
                    completed_at=now(),
                    seed=session["seed"],
                    observations=observations,
                    private_case=private,
                    metrics=metrics,
                    observer_models=models,
                    observer_assumptions=OBSERVER_ASSUMPTIONS,
                    limitations=DISCOVERY_LIMITATIONS,
                )
                session["report"] = report.model_dump(mode="json")
                return report
            if is_company:
                from epistemics.company.analysis import LIMITATIONS
                from epistemics.company.analysis import analyze as analyze_company

                observations = [
                    CompanyObservation(
                        trial=t["trial"],
                        truth=t["truth"],
                        answer=a["answer"],
                        answered_at=a["answered_at"],
                    )
                    for t, a in zip(session["trials"], session["answers"], strict=True)
                ]
                metrics, diagnostics, parameters, fits = analyze_company(observations)
                report = CompanyReport(
                    evaluator_version=__version__,
                    battery_sha256=session["battery_sha256"],
                    session_id=session_id,
                    agent=session["agent"],
                    started_at=session["started_at"],
                    completed_at=now(),
                    seed=session["seed"],
                    metrics=metrics,
                    diagnostics=diagnostics,
                    parameters=parameters,
                    model_fits=fits,
                    observations=observations,
                    limitations=LIMITATIONS,
                )
                session["report"] = report.model_dump(mode="json")
                return report
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
