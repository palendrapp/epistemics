"""Bound presentation adapter with transactional prospective prediction locks.

Underlying 0.1 collections are retained as canonical factual ledgers. Packet runs
must be interpreted with this separately versioned transport record, not passed
off as observations of the original structured presentation.
"""

import json
from datetime import datetime
from pathlib import Path

from epistemics.service import now
from epistemics.source_learning.battery import public_trial
from epistemics.source_learning.models import Answer
from epistemics.source_learning.service import SourceLearningService
from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_learning.storage import fingerprint as base_fingerprint
from epistemics.source_panel import PACKET_VERSION, VERSION
from epistemics.source_panel.presentation import present
from epistemics.source_panel.profiles import predictions


def fingerprint():
    return digest(
        encoded(
            {
                "base": base_fingerprint(),
                "panel": {
                    p.name: digest(p.read_bytes())
                    for p in sorted(Path(__file__).parent.glob("*.py"))
                },
            }
        )
    )


def bind(directory, *, presentation="structured", profiles=None, frozen_at=None):
    base = SourceLearningService(directory)
    if presentation not in ("structured", "packet"):
        raise ValueError("Unknown presentation")
    with base.state() as state:
        if state["answers"] or state["locks"]:
            raise ValueError("Bind before any checkpoint is served")
    if profiles is not None and frozen_at is None:
        raise ValueError("Profiles must have a precollection freeze time")
    if frozen_at is not None:
        frozen_time = datetime.fromisoformat(frozen_at)
        if frozen_time.tzinfo is None or frozen_time > datetime.fromisoformat(now()):
            raise ValueError("Profile freeze time must be aware and in the past")
    binding = {
        "schema_version": "epistemics.source-panel-binding.v1",
        "version": VERSION,
        "presentation": presentation,
        "presentation_version": PACKET_VERSION
        if presentation == "packet"
        else "source-learning/0.1.0",
        "base_manifest_sha256": base.manifest_hash,
        "implementation_sha256": fingerprint(),
        "profiles": profiles,
        "profile_frozen_at": frozen_at,
        "created_at": now(),
    }
    save(Path(directory) / "panel-binding.json", encoded(binding))
    save(Path(directory) / "panel-binding.sha256", (digest(encoded(binding)) + "\n").encode())
    return binding


class PanelService:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.base = SourceLearningService(directory)
        raw = (self.directory / "panel-binding.json").read_bytes()
        self.binding = json.loads(raw)
        self.binding_hash = digest(raw)
        self.guard()

    def guard(self):
        raw = (self.directory / "panel-binding.json").read_bytes()
        if (
            digest(raw) != self.binding_hash
            or digest(raw) != (self.directory / "panel-binding.sha256").read_text().strip()
        ):
            raise ValueError("Frozen panel binding changed")
        if self.binding["implementation_sha256"] != fingerprint():
            raise ValueError("Frozen panel implementation changed")
        if self.binding["base_manifest_sha256"] != self.base.manifest_hash:
            raise ValueError("Panel collection binding changed")

    def describe(self):
        self.guard()
        result = self.base.describe()
        result["battery_version"] = self.binding["presentation_version"]
        if self.binding["presentation"] == "packet":
            result["presentation"] = "Read the research packet for each current company."
        return result

    def get_trial(self):
        self.guard()
        with self.base.state() as state:
            trial = self.base._prepare(state)
            rendered = None
            if trial is not None:
                index = len(state["answers"])
                rendered = present(trial, self.binding["presentation"])
                locks = state.setdefault("panel_locks", [])
                if len(locks) == index:
                    models = self.binding["profiles"]
                    locks.append(
                        {
                            "binding_sha256": self.binding_hash,
                            "locked_at": now(),
                            "public_trial": rendered,
                            "public_trial_sha256": digest(encoded(rendered)),
                            "prediction": predictions(
                                state["locks"][index]["raw"], models, trial.prior_strong
                            )
                            if models is not None
                            else None,
                        }
                    )
                elif locks[index]["public_trial_sha256"] != digest(encoded(rendered)):
                    raise ValueError("Frozen presentation changed")
            return {
                "complete": trial is None,
                "finished": state["completed_at"] is not None,
                "answered": len(state["answers"]),
                "trial": rendered,
            }

    def get_history(self):
        self.guard()
        result = self.base.get_history()
        if self.binding["presentation"] == "packet":
            from epistemics.source_learning.models import Trial

            for row in result["history"]:
                row["trial"] = present(Trial.model_validate(row["trial"]), "packet")
        return result

    def submit(self, trial_id, answer):
        self.guard()
        with self.base.state() as state:
            index = next(
                (
                    i
                    for i, row in enumerate(state["answers"])
                    if row["receipt"]["trial_id"] == trial_id
                ),
                len(state["answers"]),
            )
            if index >= len(state.get("panel_locks", [])):
                raise ValueError("Read the current public presentation before answering")
        # Base service owns immutable answers, idempotent retries and atomic calibration.
        return self.base.submit(trial_id, answer)

    def finish(self):
        self.guard()
        return {
            **self.base.finish(),
            "completion_questions": [
                "When was a company's actual demand revealed in this task?",
                "Does an audit of a recurring source also apply to later reports from that source?",
                "Does accurate measurement alone establish that a source's panel was randomly selected?",
            ],
            "request": "Answer these briefly after completion, then mention any confusing instructions.",
        }

    def evidence(self):
        self.guard()
        with self.base.state() as state:
            if state["completed_at"] is None or len(state.get("panel_locks", [])) != 36:
                raise ValueError("Finish the complete panel collection first")
            earlier = []
            for i, (row, lock) in enumerate(
                zip(state["answers"], state["panel_locks"], strict=True)
            ):
                trial = public_trial(self.base.manifest, i, earlier)
                expected = present(trial, self.binding["presentation"])
                models = self.binding["profiles"]
                forecast = (
                    predictions(state["locks"][i]["raw"], models, trial.prior_strong)
                    if models is not None
                    else None
                )
                if (
                    expected != lock["public_trial"]
                    or digest(encoded(expected)) != lock["public_trial_sha256"]
                    or forecast != lock["prediction"]
                    or lock["binding_sha256"] != self.binding_hash
                    or not self.binding["created_at"] <= lock["locked_at"] <= row["answered_at"]
                    or (
                        self.binding["profile_frozen_at"] is not None
                        and self.binding["profile_frozen_at"] > lock["locked_at"]
                    )
                ):
                    raise ValueError(
                        "Panel presentation, prediction or chronology failed verification"
                    )
                earlier.append(Answer.model_validate(row["answer"]))
            result = {
                "schema_version": "epistemics.source-panel-evidence.v1",
                "binding": self.binding,
                "binding_sha256": self.binding_hash,
                "completed_at": state["completed_at"],
                "locks": state["panel_locks"],
            }
        save(self.directory / "panel-evidence.json", encoded(result))
        return result
