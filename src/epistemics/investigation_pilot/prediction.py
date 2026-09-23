"""Commit branch-complete predictions before accepting held-out responses."""

import json
from pathlib import Path

import numpy as np

from epistemics.investigation.inference import simulate_reports
from epistemics.investigation3 import inference as model
from epistemics.investigation3.battery import public_trial
from epistemics.investigation3.models import Answer, Report
from epistemics.investigation3.service import digest, encoded, fingerprint, load, write_private
from epistemics.service import now

BRANCHES = ("source_audit", "operations_check", "segment_check", "calculation", "stop")
DRAWS = 1000


def pilot_fingerprint():
    root = Path(__file__).parent
    return digest(
        b"".join(p.name.encode() + b"\0" + p.read_bytes() for p in sorted(root.glob("*.py")))
    )


def bound_json(path):
    path = Path(path)
    raw = path.read_bytes()
    if digest(raw) != path.with_suffix(".sha256").read_text().strip():
        raise ValueError("Frozen artifact changed")
    return json.loads(raw), digest(raw)


def commit(path, value):
    path = Path(path)
    raw = encoded(value)
    write_private(path, raw)
    write_private(path.with_suffix(".sha256"), (digest(raw) + "\n").encode())
    return digest(raw)


def specifications(fits):
    return {
        **{
            "fitted_" + m: {
                "initialization": m,
                "coupling": f["coupling_grid_estimate"],
                "response_rate": f["response_rate_grid_estimate"],
            }
            for m, f in fits.items()
        },
        "fixed_joint": {"initialization": "working_prior", "coupling": 1.0, "response_rate": 1.0},
        "fixed_cut": {"initialization": "working_prior", "coupling": 0.0, "response_rate": 1.0},
        "persistence": {"initialization": "persistence"},
    }


def components(trials, first, spec):
    """No later answers are accepted by this prediction API."""
    if spec["initialization"] == "persistence":
        rows = np.tile(first, (3, 1))
        for i, trial in enumerate(trials[1:]):
            if trial.selected_query in ("source_audit", "operations_check"):
                rows[i, 1 if trial.selected_query == "source_audit" else 2] = float(
                    trial.query_result
                )
        values = rows.ravel().tolist()
        if trials[1].expectation_queries:
            values.extend(
                [
                    first[1],
                    first[0],
                    first[0],
                    first[2],
                    first[0],
                    first[0],
                    0.5,
                    first[0],
                    first[0],
                ]
            )
        return np.array([values]), np.ones(1)
    states, weights = model.starting_states(trials[0], spec["initialization"], first)
    values = []
    for state in states:
        raw = model.trajectory(trials, start=state, coupling=spec["coupling"])
        future = (
            model.expectations(trials[1], start=state, coupling=spec["coupling"])
            if trials[1].expectation_queries
            else None
        )
        values.append(model._prediction(raw, future, trials, spec["response_rate"]))
    return np.array(values), weights


def reference_distribution(values, weights, seed):
    rng = np.random.default_rng(seed)
    simulated = simulate_reports(values[rng.choice(len(weights), size=DRAWS, p=weights)], rng)
    mean = weights @ values
    errors = np.sqrt(np.mean((simulated - mean) ** 2, axis=1)) * 100
    # Joint episode density, not independent marginal mixtures.
    scores = model.marginal_log_likelihood(simulated[:, None, :], values[None, :, :], weights)
    return {"rmse_pp": errors.tolist(), "log_score": scores.tolist()}


def predict_branches(assignment, world, first, specs):
    result = {}
    for branch in BRANCHES:
        trials = [public_trial(assignment, world, i, branch if i >= 2 else None) for i in range(4)]
        entries = {}
        for name, spec in specs.items():
            values, weights = components(trials, first, spec)
            seed = int(digest(encoded([assignment.assignment_id, name, branch]))[:16], 16)
            entries[name] = {
                "components": values.tolist(),
                "weights": weights.tolist(),
                "mean": (weights @ values).tolist(),
                "reference": reference_distribution(values, weights, seed),
            }
        result[branch] = {
            "public_trials_sha256": digest(encoded([t.model_dump(mode="json") for t in trials])),
            "models": entries,
        }
    return result


def ensure_prediction(root, phase, service):
    if phase == "development":
        return
    plan, plan_hash = bound_json(root / "run-manifest.json")
    if service.manifest_hash != plan["manifests"][phase]:
        raise ValueError("Collection is not bound to this pilot")
    if (
        plan["pilot_sha256"] != pilot_fingerprint()
        or plan["implementation_sha256"] != fingerprint()
    ):
        raise ValueError("Frozen implementation changed")
    locked, lock_hash = bound_json(root / "locked-models.json")
    if locked["plan_sha256"] != plan_hash:
        raise ValueError("Locked models belong to another pilot")
    with service.state() as state:
        rows = state["answers"]
        if not rows:
            return
        first = model.answer_vector(Answer.model_validate(rows[0]["answer"]))
        path = root / "predictions" / f"{phase}-{service.assignment.assignment_id}.json"
        if path.exists():
            saved, _ = bound_json(path)
            if (
                saved["first_answer_sha256"] != digest(encoded(rows[0]))
                or saved["locked_models_sha256"] != lock_hash
            ):
                raise ValueError("Prediction binding changed")
            return
        if len(rows) != 1:
            raise ValueError("Cannot create prospective predictions after later answers")
        branches = predict_branches(
            service.assignment, service.world, first, locked["specifications"]
        )
        path.parent.mkdir(mode=0o700, exist_ok=True)
        commit(
            path,
            {
                "schema_version": "epistemics.investigation-prediction.v1",
                "created_at": now(),
                "phase": phase,
                "assignment_id": service.assignment.assignment_id,
                "manifest_sha256": service.manifest_hash,
                "plan_sha256": plan_hash,
                "locked_models_sha256": lock_hash,
                "first_answer_sha256": digest(encoded(rows[0])),
                "branches": branches,
            },
        )


def freeze_models(root):
    plan, plan_hash = bound_json(root / "run-manifest.json")
    manifest, _ = load(root / "development")
    if (
        digest((root / "development/manifest.json").read_bytes())
        != plan["manifests"]["development"]
    ):
        raise ValueError("Development collection changed")
    reports = [
        Report.model_validate_json(
            (root / "development/reports" / f"{a.assignment_id}.json").read_bytes()
        )
        for a in manifest.assignments
    ]
    fits = {
        m: model.fit([r.observations for r in reports], initialization=m)
        for m in model.INITIALIZATIONS
    }
    return commit(
        root / "locked-models.json",
        {
            "created_at": now(),
            "plan_sha256": plan_hash,
            "pilot_sha256": plan["pilot_sha256"],
            "fits": fits,
            "specifications": specifications(fits),
            "development_report_hashes": json.loads(
                (root / "development/report-hashes.json").read_bytes()
            ),
        },
    )


def score(observations, prediction):
    actual = model.observed_vector(observations)
    result = {}
    for name, entry in prediction["models"].items():
        values, weights = np.array(entry["components"]), np.array(entry["weights"])
        error = float(np.sqrt(np.mean((actual - entry["mean"]) ** 2)) * 100)
        ll = float(model.marginal_log_likelihood(actual, values, weights))
        ref = entry["reference"]
        result[name] = {
            "rmse_pp": error,
            "squared_errors": ((actual - entry["mean"]) ** 2).tolist(),
            "log_score": ll,
            "reports": len(actual),
            "reference_rmse_95": np.quantile(ref["rmse_pp"], [0.025, 0.975]).tolist(),
            "reference_log_score_95": np.quantile(ref["log_score"], [0.025, 0.975]).tolist(),
            "rmse_upper_tail": (1 + sum(v >= error for v in ref["rmse_pp"])) / (DRAWS + 1),
            "log_score_lower_tail": (1 + sum(v <= ll for v in ref["log_score"])) / (DRAWS + 1),
        }
    return result
