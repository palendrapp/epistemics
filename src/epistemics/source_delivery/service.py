"""Clarified transport with exact public-presentation and post-answer feedback evidence."""

import json
from datetime import datetime
from pathlib import Path

from epistemics.service import now
from epistemics.source_delivery import VERSION
from epistemics.source_delivery.presentation import describe, present, resolution
from epistemics.source_learning.models import Answer, Trial
from epistemics.source_learning.service import SourceLearningService, export
from epistemics.source_learning.service import create as create_base
from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_learning.storage import fingerprint as base_fingerprint
from epistemics.source_panel.service import fingerprint as panel_fingerprint


def fingerprint():
    root = Path(__file__).parent
    return digest(
        encoded(
            {
                "base": base_fingerprint(),
                "panel": panel_fingerprint(),
                "delivery": {
                    str(p.relative_to(root)): digest(p.read_bytes())
                    for p in sorted(root.rglob("*"))
                    if p.is_file() and (p.suffix == ".py" or "assets" in p.parts)
                },
            }
        )
    )


def create(directory, participant, *, presentation="structured", **kwargs):
    if presentation not in ("structured", "packet"):
        raise ValueError("Unknown presentation")
    manifest = create_base(directory, participant, **kwargs)
    base = SourceLearningService(directory)
    binding = {
        "schema_version": "epistemics.source-delivery-binding.v1",
        "version": VERSION,
        "presentation": presentation,
        "base_manifest_sha256": base.manifest_hash,
        "implementation_sha256": fingerprint(),
        "created_at": now(),
        "description": describe(base.describe()),
    }
    save(Path(directory) / "delivery-binding.json", encoded(binding))
    save(Path(directory) / "delivery-binding.sha256", (digest(encoded(binding)) + "\n").encode())
    return manifest


def verify_evidence(report, evidence):
    binding = evidence["binding"]
    if (
        evidence["schema_version"] != "epistemics.source-delivery-evidence.v1"
        or binding["schema_version"] != "epistemics.source-delivery-binding.v1"
        or binding["version"] != VERSION
        or binding["base_manifest_sha256"] != report.manifest_sha256
        or evidence["binding_sha256"] != digest(encoded(binding))
        or datetime.fromisoformat(evidence["completed_at"]) != report.completed_at
        or len(evidence["locks"]) != len(report.observations)
        or len(evidence["resolutions"]) != len(report.observations)
    ):
        raise ValueError("Delivery evidence binding differs from report")
    from epistemics.source_learning.battery import INSTRUCTIONS
    from epistemics.source_learning.models import Answer as BaseAnswer

    expected_description = describe(
        {
            "battery_version": report.manifest.battery_version,
            "condition": report.manifest.condition,
            "total_trials": 36,
            "companies": 24,
            "instructions": INSTRUCTIONS,
            "diagnostics": "This assignment also asks for source measurement accuracy and the chance of random panel selection."
            if report.manifest.condition == "dense"
            else "This assignment asks for company forecasts and actions.",
            "answer_schema": BaseAnswer.model_json_schema(),
            "context_policy": report.manifest.context_policy,
            "response_origin": report.manifest.response_origin,
        }
    )
    if binding["description"] != expected_description:
        raise ValueError("Frozen public instructions differ")
    for i, (observation, lock) in enumerate(
        zip(report.observations, evidence["locks"], strict=True)
    ):
        public = present(observation.trial, binding["presentation"])
        if (
            lock["public_trial"] != public
            or lock["public_trial_sha256"] != digest(encoded(public))
            or lock["binding_sha256"] != evidence["binding_sha256"]
            or not report.manifest.created_at
            <= datetime.fromisoformat(binding["created_at"])
            <= datetime.fromisoformat(lock["locked_at"])
            <= observation.answered_at
            or evidence["resolutions"][i] != resolution(report.manifest, i)
        ):
            raise ValueError("Delivery presentation, feedback or chronology differs")
    return binding


class DeliveryService:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.base = SourceLearningService(directory)
        self.manifest = self.base.manifest
        raw = (self.directory / "delivery-binding.json").read_bytes()
        self.binding, self.binding_hash = json.loads(raw), digest(raw)
        self.guard()

    def guard(self):
        raw = (self.directory / "delivery-binding.json").read_bytes()
        if (
            digest(raw) != self.binding_hash
            or digest(raw) != (self.directory / "delivery-binding.sha256").read_text().strip()
            or self.binding["implementation_sha256"] != fingerprint()
            or self.binding["base_manifest_sha256"] != self.base.manifest_hash
        ):
            raise ValueError("Frozen delivery changed; use its original implementation")

    def describe(self):
        self.guard()
        return self.binding["description"]

    def get_trial(self):
        self.guard()
        with self.base.state() as state:
            trial = self.base._prepare(state)
            public = None
            if trial is not None:
                public = present(trial, self.binding["presentation"])
                i = len(state["answers"])
                locks = state.setdefault("delivery_locks", [])
                if len(locks) == i:
                    locks.append(
                        {
                            "binding_sha256": self.binding_hash,
                            "locked_at": now(),
                            "public_trial": public,
                            "public_trial_sha256": digest(encoded(public)),
                        }
                    )
                elif locks[i]["public_trial_sha256"] != digest(encoded(public)):
                    raise ValueError("Frozen public presentation changed")
            return {
                "complete": trial is None,
                "finished": state["completed_at"] is not None,
                "answered": len(state["answers"]),
                "trial": public,
            }

    def get_history(self):
        self.guard()
        result = self.base.get_history()
        for row in result["history"]:
            row["trial"] = present(Trial.model_validate(row["trial"]), self.binding["presentation"])
        return result

    def submit(self, trial_id, answer):
        self.guard()
        with self.base.state() as state:
            index = next(
                (i for i, r in enumerate(state["answers"]) if r["receipt"]["trial_id"] == trial_id),
                len(state["answers"]),
            )
            if index >= len(state.get("delivery_locks", [])):
                raise ValueError("Read the public checkpoint before answering")
        receipt = self.base.submit(trial_id, Answer.model_validate(answer))
        # The accepted index is immutable. A retry returns the same feedback even after later answers.
        return {**receipt, "resolved_company": resolution(self.manifest, receipt["answered"] - 1)}

    def finish(self):
        self.guard()
        return {
            **self.base.finish(),
            "completion_questions": [
                "When was actual company demand revealed?",
                "Does a source audit apply to later reports from that source?",
                "Does accurate measurement establish random selection?",
                "Does an independent customer panel reveal company demand with certainty?",
            ],
        }

    def evidence(self):
        self.guard()
        report = export(self.directory)
        with self.base.state() as state:
            result = {
                "schema_version": "epistemics.source-delivery-evidence.v1",
                "binding": self.binding,
                "binding_sha256": self.binding_hash,
                "completed_at": state["completed_at"],
                "locks": state.get("delivery_locks", []),
                "resolutions": [resolution(self.manifest, i) for i in range(len(state["answers"]))],
            }
        verify_evidence(report, result)
        save(self.directory / "delivery-evidence.json", encoded(result))
        return result
