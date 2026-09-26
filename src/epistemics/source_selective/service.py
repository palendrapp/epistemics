"""Rule and offered prices bound before collection; action commits with provisional answer.

The base ledger stores the derived query atomically with its accepted probability.
No intermediate write can reveal a check before the answer is immutable. Evidence
verification reconstructs every query from that probability and the frozen rule.
"""

import json
import secrets
from datetime import datetime
from pathlib import Path

from epistemics.service import now
from epistemics.source_delivery.presentation import resolution
from epistemics.source_delivery.service import fingerprint as delivery_fingerprint
from epistemics.source_learning.models import Answer as LedgerAnswer
from epistemics.source_learning.models import Trial
from epistemics.source_learning.service import SourceLearningService, export
from epistemics.source_learning.service import create as create_base
from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_selective import VERSION
from epistemics.source_selective.analysis import metrics
from epistemics.source_selective.policy import POLICIES, RULE, choose, offers, price_for
from epistemics.source_selective.presentation import (
    Answer,
    describe,
    present,
)


def fingerprint():
    root = Path(__file__).parent
    return digest(
        encoded(
            {
                "delivery": delivery_fingerprint(),
                "verification": {
                    str(p.relative_to(root)): digest(p.read_bytes())
                    for p in sorted(root.rglob("*"))
                    if p.is_file() and (p.suffix == ".py" or "assets" in p.parts)
                },
            }
        )
    )


def create(directory, participant, *, policy, seed=None, price_seed=None, synthetic=False):
    if policy not in POLICIES:
        raise ValueError("Unknown assigned policy")
    price_seed = secrets.randbits(64) if price_seed is None else price_seed
    if not isinstance(price_seed, int) or isinstance(price_seed, bool) or price_seed < 0:
        raise ValueError("Price seed must be a nonnegative integer")
    manifest = create_base(
        directory, participant, seed=seed, condition="sparse", synthetic=synthetic
    )
    base = SourceLearningService(directory)
    binding = {
        "schema_version": "epistemics.source-selective-binding.v1",
        "version": VERSION,
        "base_manifest_sha256": base.manifest_hash,
        "implementation_sha256": fingerprint(),
        "created_at": now(),
        "policy": policy,
        "price_seed": price_seed,
        "offers": offers(manifest, price_seed),
        "rule": RULE,
        "description": describe(base.describe(), policy),
    }
    save(Path(directory) / "verification-binding.json", encoded(binding))
    save(
        Path(directory) / "verification-binding.sha256", (digest(encoded(binding)) + "\n").encode()
    )
    return manifest


def verify_evidence(report, evidence):
    b = evidence["binding"]
    policy = b["policy"]
    if (
        evidence["schema_version"] != "epistemics.source-selective-evidence.v1"
        or b["schema_version"] != "epistemics.source-selective-binding.v1"
        or b["version"] != VERSION
        or policy not in POLICIES
        or report.manifest.condition != "sparse"
        or b["base_manifest_sha256"] != report.manifest_sha256
        or evidence["binding_sha256"] != digest(encoded(b))
        or evidence["canonical_report_sha256"] != digest(encoded(report))
        or b["implementation_sha256"] != fingerprint()
        or b["offers"] != offers(report.manifest, b["price_seed"])
        or b["rule"] != RULE
        or b["description"]
        != describe(
            {
                "context_policy": report.manifest.context_policy,
                "response_origin": report.manifest.response_origin,
            },
            policy,
        )
        or datetime.fromisoformat(evidence["completed_at"]) != report.completed_at
        or len(evidence["locks"]) != 36
        or len(evidence["resolutions"]) != 36
        or evidence["analysis"] != metrics(report, b)
    ):
        raise ValueError("Verification binding, assignment or analysis differs")
    for i, (o, lock) in enumerate(zip(report.observations, evidence["locks"], strict=True)):
        expected_query = (
            choose(
                policy,
                o.answer.probability,
                o.trial.decision_threshold,
                price_for(b, o.trial.company_id),
            )
            if o.trial.stage == "research"
            else None
        )
        public = present(o.trial, b)
        previous = report.manifest.created_at if i == 0 else report.observations[i - 1].answered_at
        if (
            o.answer.query != expected_query
            or lock["public_trial"] != public
            or lock["public_trial_sha256"] != digest(encoded(public))
            or lock["binding_sha256"] != evidence["binding_sha256"]
            or not report.manifest.created_at
            <= datetime.fromisoformat(b["created_at"])
            <= report.observations[0].answered_at
            or not max(previous, datetime.fromisoformat(b["created_at"]))
            <= datetime.fromisoformat(lock["locked_at"])
            <= o.answered_at
            or evidence["resolutions"][i] != resolution(report.manifest, i)
        ):
            raise ValueError("Assigned query, presentation, feedback or chronology differs")
    return b


class VerificationService:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.base = SourceLearningService(directory)
        self.manifest = self.base.manifest
        raw = (self.directory / "verification-binding.json").read_bytes()
        self.binding, self.binding_hash = json.loads(raw), digest(raw)
        self.guard()

    def guard(self):
        raw = (self.directory / "verification-binding.json").read_bytes()
        if (
            digest(raw) != self.binding_hash
            or encoded(self.binding) != raw
            or digest(raw) != (self.directory / "verification-binding.sha256").read_text().strip()
            or self.binding["implementation_sha256"] != fingerprint()
            or self.binding["base_manifest_sha256"] != self.base.manifest_hash
        ):
            raise ValueError("Frozen verification binding changed; use original implementation")

    def describe(self):
        self.guard()
        return self.binding["description"]

    def get_trial(self):
        self.guard()
        with self.base.state() as state:
            trial = self.base._prepare(state)
            public = None
            if trial is not None:
                public = present(trial, self.binding)
                i = len(state["answers"])
                locks = state.setdefault("verification_locks", [])
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
                    raise ValueError("Frozen presentation changed")
            return {
                "complete": trial is None,
                "finished": state["completed_at"] is not None,
                "answered": len(state["answers"]),
                "trial": public,
            }

    def submit(self, trial_id, answer):
        self.guard()
        answer = Answer.model_validate(answer)
        with self.base.state() as state:
            index = next(
                (i for i, r in enumerate(state["answers"]) if r["receipt"]["trial_id"] == trial_id),
                len(state["answers"]),
            )
            locks = state.get("verification_locks", [])
            if index >= len(locks) or locks[index]["public_trial"]["trial_id"] != trial_id:
                raise ValueError("Read the current public checkpoint before answering")
            query = (
                choose(
                    self.binding["policy"],
                    answer.probability,
                    locks[index]["public_trial"]["decision_threshold"],
                    price_for(self.binding, locks[index]["public_trial"]["company_id"]),
                )
                if locks[index]["public_trial"]["stage"] == "provisional"
                else None
            )
        ledger = LedgerAnswer(**answer.model_dump(), query=query)
        receipt = self.base.submit(trial_id, ledger)
        return {**receipt, "resolved_company": resolution(self.manifest, receipt["answered"] - 1)}

    def get_history(self):
        self.guard()
        result = self.base.get_history()
        for row in result["history"]:
            row["trial"] = present(Trial.model_validate(row["trial"]), self.binding)
            row["answer"] = {k: row["answer"][k] for k in ("probability", "decision")}
        return result

    def finish(self):
        self.guard()
        return {
            **self.base.finish(),
            "completion_questions": [
                "Who determined whether you received an independent check, and what rule applied in this collection?",
                "When was actual company demand revealed?",
                "Does an independent customer sample reveal company demand with certainty?",
                "Is an assigned check cost charged if you decline to invest?",
            ],
        }

    def evidence(self):
        self.guard()
        report = export(self.directory)
        with self.base.state() as state:
            result = {
                "schema_version": "epistemics.source-selective-evidence.v1",
                "binding": self.binding,
                "binding_sha256": self.binding_hash,
                "canonical_report_sha256": digest((self.directory / "report.json").read_bytes()),
                "completed_at": state["completed_at"],
                "locks": state.get("verification_locks", []),
                "resolutions": [resolution(self.manifest, i) for i in range(len(state["answers"]))],
                "analysis": metrics(report, self.binding),
            }
        verify_evidence(report, result)
        save(self.directory / "verification-evidence.json", encoded(result))
        a = result["analysis"]
        lines = [
            "# Assigned-verification evidence",
            "",
            f"Protocol: {VERSION}. Policy: {self.binding['policy']}. Origin: {self.manifest.response_origin}.",
            "All 36 checkpoints completed. Outcomes below concern only the twelve later companies.",
            "Checks were assigned by the evaluator; they are not voluntary research preferences.",
            "",
            "| Measurement | Value |",
            "| --- | ---: |",
            *[
                f"| {key} | {a[key]} |"
                for key in (
                    "mean_net_payoff",
                    "mean_gross_payoff",
                    "total_check_cost",
                    "check_count",
                    "mean_final_brier",
                    "decision_changed",
                    "false_acceptance",
                    "missed_opportunity",
                )
            ],
            "",
            "Fictional payoff is separate from prediction of numerical reports. A single trajectory does not establish verification benefit.",
            "The canonical report is a private calculation ledger with injected policy actions and LEGACY PRICES. Its payoff, research-value and choice analyses do not apply to this price design. Use verification-evidence.json and this report for actual offered prices and net outcomes.",
            f"Canonical report SHA-256: `{result['canonical_report_sha256']}`.",
            f"Verification evidence SHA-256: `{digest(encoded(result))}`.",
            "",
        ]
        save(self.directory / "verification-report.md", "\n".join(lines).encode())
        return result


def load_evidence(directory):
    from epistemics.passport.source_learning import SourceSession, validate_report

    directory = Path(directory)
    raw = (directory / "report.json").read_bytes()
    if (directory / "report.sha256").read_text().strip() != digest(raw):
        raise ValueError("Canonical report byte hash mismatch")
    report = validate_report(SourceSession(report_json=raw.decode(), report_sha256=digest(raw)))
    evidence = json.loads((directory / "verification-evidence.json").read_bytes())
    verify_evidence(report, evidence)
    return report, evidence
