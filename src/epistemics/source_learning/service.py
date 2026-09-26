"""One continuous, transactional collection shared by human and MCP adapters."""

import json
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from epistemics.participants import ParticipantDescriptor
from epistemics.service import now
from epistemics.source_learning.battery import (
    INSTRUCTIONS,
    generate,
    public_trial,
    resolved_history,
)
from epistemics.source_learning.inference import (
    analyze,
    calibrate,
    forecast,
    raw_predictions,
    research_values,
)
from epistemics.source_learning.models import Answer, Manifest, Observation, Report
from epistemics.source_learning.storage import digest, encoded, fingerprint, save


def create(directory, participant, *, seed=None, condition=None, synthetic=False):
    participant = ParticipantDescriptor.model_validate(participant).root
    design_seed = secrets.randbits(64) if seed is None else seed
    if not isinstance(design_seed, int) or isinstance(design_seed, bool) or design_seed < 0:
        raise ValueError("Seed must be a nonnegative integer")
    providers, archive, companies = generate(design_seed)
    manifest = Manifest(
        study_id=str(uuid4()),
        created_at=now(),
        design_seed=design_seed,
        implementation_sha256=fingerprint(),
        participant=participant,
        response_origin="synthetic" if synthetic else participant.kind,
        condition=condition if condition is not None else secrets.choice(("sparse", "dense")),
        condition_assignment="operator_selected" if condition is not None else "randomized",
        sources=providers,
        archive=archive,
        companies=companies,
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
    return manifest, digest(raw)


class SourceLearningService:
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
                (json.dumps({"answers": [], "locks": [], "fit_lock": None, "completed_at": None}),),
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
        return {
            "battery_version": self.manifest.battery_version,
            "condition": self.manifest.condition,
            "total_trials": 36,
            "companies": 24,
            "instructions": INSTRUCTIONS,
            "diagnostics": "This assignment also asks for source measurement accuracy and the chance of random panel selection."
            if self.manifest.condition == "dense"
            else "This assignment asks for company forecasts and actions.",
            "answer_schema": Answer.model_json_schema(),
            "context_policy": self.manifest.context_policy,
            "response_origin": self.manifest.response_origin,
        }

    def _prepare(self, state):
        index = len(state["answers"])
        if index == 36:
            return None
        answers = [Answer.model_validate(row["answer"]) for row in state["answers"]]
        trial = public_trial(self.manifest, index, answers)
        if len(state["locks"]) == index:
            raw = raw_predictions(self.manifest, index, answers)
            lock = {
                "trial_sha256": digest(encoded(trial)),
                "locked_at": now(),
                "raw": raw,
                "forecast": forecast(raw, state["fit_lock"]["fit"]) if index >= 12 else None,
                "fit_sha256": digest(encoded(state["fit_lock"])) if index >= 12 else None,
                "myopic_research_values": research_values(
                    self.manifest, index, answers, trial.research_costs
                )
                if trial.stage == "research"
                else None,
            }
            state["locks"].append(lock)
        elif digest(encoded(trial)) != state["locks"][index]["trial_sha256"]:
            raise ValueError("Frozen trial binding changed")
        return trial

    def get_trial(self):
        with self.state() as state:
            trial = self._prepare(state)
            return {
                "complete": trial is None,
                "finished": state["completed_at"] is not None,
                "answered": len(state["answers"]),
                "trial": trial.model_dump(mode="json") if trial else None,
            }

    def get_history(self):
        with self.state() as state:
            answers = [Answer.model_validate(row["answer"]) for row in state["answers"]]
            return {"history": resolved_history(self.manifest, answers)}

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
            if n == 36 or len(state["locks"]) != n + 1:
                raise ValueError("Read the current checkpoint before answering")
            answers = [Answer.model_validate(row["answer"]) for row in state["answers"]]
            trial = public_trial(self.manifest, n, answers)
            if trial.trial_id != trial_id:
                raise ValueError("Submit only the current checkpoint")
            answer.validate_trial(trial)
            receipt = {
                "accepted": True,
                "trial_id": trial_id,
                "answered": n + 1,
                "complete": n == 35,
                "prediction_sha256": digest(encoded(state["locks"][n])),
            }
            state["answers"].append({"answer": data, "answered_at": now(), "receipt": receipt})
            if n == 11:
                state["fit_lock"] = {
                    "locked_at": now(),
                    "calibration_answers_sha256": digest(encoded(state["answers"])),
                    "fit": calibrate(state["locks"], [*answers, answer]),
                }
                # The fit is committed in the same transaction as the final calibration answer.
            return receipt

    def finish(self):
        with self.state() as state:
            if len(state["answers"]) != 36:
                raise ValueError("Complete every checkpoint first")
            if state["completed_at"] is None:
                state["completed_at"] = now()
            return {"complete": True, "answered": 36, "answers_stored": True}


def export(directory):
    service = SourceLearningService(directory)
    with service.state() as state:
        if state["completed_at"] is None:
            raise ValueError("Finish the whole collection before export")
        answers = [Answer.model_validate(row["answer"]) for row in state["answers"]]
        fit_lock = state["fit_lock"]
        if fit_lock["calibration_answers_sha256"] != digest(encoded(state["answers"][:12])):
            raise ValueError("Calibration answer binding changed")
        if fit_lock["fit"] != calibrate(state["locks"][:12], answers[:12]):
            raise ValueError("Frozen calibration fit changed")
        observations = []
        for i, row in enumerate(state["answers"]):
            trial = public_trial(service.manifest, i, answers[:i])
            lock = state["locks"][i]
            expected_raw = raw_predictions(service.manifest, i, answers[:i])
            if lock["trial_sha256"] != digest(encoded(trial)) or lock["raw"] != expected_raw:
                raise ValueError("Frozen public-history predictions changed")
            if i >= 12 and (
                lock["forecast"] != forecast(expected_raw, fit_lock["fit"])
                or lock["fit_sha256"] != digest(encoded(fit_lock))
            ):
                raise ValueError("Heldout predictions must use the original calibration fit")
            observations.append(
                Observation(
                    trial=trial,
                    answer=answers[i],
                    answered_at=row["answered_at"],
                    prediction_sha256=row["receipt"]["prediction_sha256"],
                )
            )
        report = Report(
            manifest=service.manifest,
            manifest_sha256=service.manifest_hash,
            completed_at=state["completed_at"],
            observations=observations,
            prediction_locks=state["locks"],
            fit_lock=fit_lock,
            analysis=analyze(service.manifest, observations, state["locks"], fit_lock["fit"]),
            limitations=[
                "Business expansion rates are disclosed; discovery concerns static source measurement and selection.",
                "Sparse/dense assignments differ in prompting and reporting burden together; one collection cannot estimate the treatment effect.",
                "Probability reports are observations, not internal beliefs. Reporting gain is a nuisance parameter, not a cognitive trait.",
                "The three observer families and fixed noise model are limited candidates; every candidate may fail the conditional adequacy screen.",
                "Response noise is modeled as independent between companies with within-company correlation; persistent source-level report error is unmodeled.",
                "Heldout report likelihood treats the public research path as given; it ignores selection by the participant's research policy and is not a joint likelihood of forecasts and choices.",
                "Research comparisons are one-company myopic predictions; actual audits may also benefit later companies.",
                "Dense source estimates are descriptive reports and never free inputs to the primary forecast model.",
                "Six recurring sources create dependence. Outcome scores describe this generated distribution, not real portfolio returns.",
                "Private local files and operator-asserted metadata are not execution isolation or model identity attestation.",
                "No passport trait issuance, validated individualized benefit or human usability established by implementation alone.",
            ],
        )
    raw = encoded(report)
    save(Path(directory) / "report.json", raw)
    save(Path(directory) / "report.sha256", (digest(raw) + "\n").encode())
    save(Path(directory) / "fit-lock.json", encoded(report.fit_lock))
    save(Path(directory) / "prediction-locks.json", encoded(report.prediction_locks))
    a = report.analysis
    lines = [
        "# Source-learning collection",
        "",
        f"Origin: **{report.manifest.response_origin}**. Condition: **{report.manifest.condition}**.",
        "24 companies, 36 forecasts/decisions, 12 research choices. No passport trait issued.",
        "",
        "| Frozen prediction | Heldout response RMSE (points) |",
        "| --- | ---: |",
        *[f"| {key} | {value:.3f} |" for key, value in a["heldout_behavior_rmse_pp"].items()],
        "",
        f"All candidate models outside their conditional adequacy envelope: **{a['all_candidates_inadequate']}**.",
        f"Decisions consistent with reported probabilities: {a['decision_consistency']['consistent']}/36.",
        "",
        "These errors concern predicting reports; outcome scores and realized payoffs are separate in the JSON.",
        "",
        *[f"- {line}" for line in report.limitations],
        "",
        f"Exact report SHA-256: `{digest(raw)}`",
        "",
    ]
    save(Path(directory) / "report.md", "\n".join(lines).encode())
    return report
