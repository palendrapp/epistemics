"""Audit committed forecasts and summarize the bounded pilot without trait promotion."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np

from epistemics.investigation3.inference import answer_vector
from epistemics.investigation3.models import Report
from epistemics.investigation3.service import digest, encoded, load, write_private
from epistemics.investigation_pilot.prediction import bound_json, score


def reports(root, phase):
    directory = root / phase
    manifest, _ = load(directory)
    hashes = json.loads((directory / "report-hashes.json").read_bytes())
    result = []
    for a in manifest.assignments:
        raw = (directory / "reports" / f"{a.assignment_id}.json").read_bytes()
        if digest(raw) != hashes[f"{a.assignment_id}.json"]:
            raise ValueError("Original report hash mismatch")
        result.append(Report.model_validate_json(raw))
    return result


def signature(assignment):
    return (
        assignment.seed,
        assignment.offset,
        assignment.family,
        assignment.price_condition,
        assignment.focused_query,
    )


def aggregate(rows):
    result = {}
    names = list(rows[0]["scores"])
    for name in names:
        estimates = [r["scores"][name] for r in rows]
        total = sum(r["reports"] for r in estimates)
        result[name] = {
            "rmse_pp": float(
                np.sqrt(np.mean([x for r in estimates for x in r["squared_errors"]])) * 100
            ),
            "log_score_per_report": sum(r["log_score"] for r in estimates) / total,
            "rmse_above_reference_97_5": sum(
                r["rmse_pp"] > r["reference_rmse_95"][1] for r in estimates
            ),
            "log_score_below_reference_2_5": sum(
                r["log_score"] < r["reference_log_score_95"][0] for r in estimates
            ),
            "reports": total,
            "cases": len(rows),
        }
    # Matched price cases share a world, so resample whole worlds, not reports.
    groups = sorted({r["world"] for r in rows})
    rng = np.random.default_rng(9232026)
    draws = [rng.choice(groups, size=len(groups), replace=True).tolist() for _ in range(2000)]
    for name in names:
        result[name]["rmse_difference_vs_fixed_joint_95"] = np.quantile(
            [
                np.sqrt(
                    np.mean(
                        [
                            x
                            for g in draw
                            for r in rows
                            if r["world"] == g
                            for x in r["scores"][name]["squared_errors"]
                        ]
                    )
                )
                * 100
                - np.sqrt(
                    np.mean(
                        [
                            x
                            for g in draw
                            for r in rows
                            if r["world"] == g
                            for x in r["scores"]["fixed_joint"]["squared_errors"]
                        ]
                    )
                )
                * 100
                for draw in draws
            ],
            [0.025, 0.975],
        ).tolist()
    return result


def analyze(root):
    root = Path(root)
    plan, plan_hash = bound_json(root / "run-manifest.json")
    locked, locked_hash = bound_json(root / "locked-models.json")
    if locked["plan_sha256"] != plan_hash:
        raise ValueError("Locked model binding mismatch")
    data = {phase: reports(root, phase) for phase in ("development", "repeat", "new")}
    phases = {}
    for phase in ("repeat", "new"):
        rows = []
        for report in data[phase]:
            aid = report.assignment.assignment_id
            prediction, prediction_hash = bound_json(root / "predictions" / f"{phase}-{aid}.json")
            branch = prediction["branches"][report.observations[1].answer.query]
            if (
                prediction["plan_sha256"] != plan_hash
                or prediction["locked_models_sha256"] != locked_hash
                or prediction["manifest_sha256"] != report.manifest_sha256
                or branch["public_trials_sha256"]
                != digest(encoded([o.trial.model_dump(mode="json") for o in report.observations]))
                or not datetime.fromisoformat(report.observations[0].answered_at)
                <= datetime.fromisoformat(prediction["created_at"])
                <= datetime.fromisoformat(report.observations[1].answered_at)
                or datetime.fromisoformat(locked["created_at"])
                > datetime.fromisoformat(report.observations[0].answered_at)
            ):
                raise ValueError("Prospective prediction binding or chronology mismatch")
            rows.append(
                {
                    "assignment_id": aid,
                    "world": str(report.assignment.seed),
                    "prediction_sha256": prediction_hash,
                    "scores": score(report.observations, branch),
                }
            )
        phases[phase] = {"summary": aggregate(rows), "cases": rows}
    original = {signature(r.assignment): r for r in data["development"]}
    early, later, same_choices = [], [], 0
    for r in data["repeat"]:
        a = original[signature(r.assignment)]
        for i in (0, 1):
            early.extend(
                np.array(answer_vector(r.observations[i].answer))
                - answer_vector(a.observations[i].answer)
            )
        if r.observations[1].answer.query == a.observations[1].answer.query:
            same_choices += 1
            for i in (2, 3):
                later.extend(
                    np.array(answer_vector(r.observations[i].answer))
                    - answer_vector(a.observations[i].answer)
                )
    result = {
        "schema_version": "epistemics.investigation-pilot-analysis.v1",
        "plan_sha256": plan_hash,
        "locked_models_sha256": locked_hash,
        "phases": phases,
        "repeatability": {
            "early_report_rmse_pp": float(np.sqrt(np.mean(np.square(early))) * 100),
            "early_report_count": len(early),
            "same_research_choice_cases": same_choices,
            "same_branch_later_rmse_pp": float(np.sqrt(np.mean(np.square(later))) * 100)
            if later
            else None,
            "same_branch_later_report_count": len(later),
        },
        "scope": "One requested configuration; prospective conditional prediction on 12 repeated and 12 new cases. Nine world clusters per collection. No population-pooling comparison, internal-mechanism identification or intervention test. Predictive ranges are model-conditional checks, not calibrated empirical trait intervals.",
        "empirical_predictive_validation": False,
    }
    write_private(root / "pilot-analysis.json", encoded(result))
    return result
