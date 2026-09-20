"""Precommitted predictors, matched-case uncertainty and scoped empirical decisions."""

import json
from pathlib import Path

import numpy as np

from epistemics.benchmark.models import BenchmarkReport
from epistemics.benchmark.recovery import require_execution
from epistemics.benchmark.runner import operator_lock
from epistemics.benchmark.store import (
    accounting,
    complete_split,
    database,
    episode_states,
    json_bytes,
    load,
)
from epistemics.predictive.analysis import (
    PARAMETERS,
    Row,
    arrays,
    conditional_task_metrics,
    features,
    fit_profile,
    logit,
    persistence_baseline,
    prediction_metrics,
    probability,
    solve,
)
from epistemics.predictive.collection import export_collection
from epistemics.predictive.design import digest, encoded, episode
from epistemics.service import now

COMPARATORS = ("pooled", "reference_calibration", "one_gain_all_reports", "persistence")
PREDICTORS = ("individual", *COMPARATORS, "raw_source_sensitivity")


def theta(fitted):
    return np.array([fitted["parameters"][name] for name in PARAMETERS])


def raw_features(checkpoint):
    roots, independent, copied = {}, 0.0, 0.0
    for card in checkpoint.evidence:
        if card.based_on is None:
            record = card.original_assessment_history
            signal = float(logit(record.correct / record.total)) * (
                1 if card.assessment == "meets_target" else -1
            )
            independent += signal
        else:
            signal = roots[card.based_on]
            copied += signal
        roots[card.document_id] = signal
    return (1.0, float(logit(checkpoint.prior_probability)), independent, copied)


def rows(directory, configuration_id, design, split, *, raw=False):
    states = episode_states(directory, configuration_id)
    result = []
    for assignment in design.assignments:
        if assignment.split != split:
            continue
        state = states.get(assignment.assignment_id, {})
        if state.get("completion") is None:
            raise ValueError(f"Incomplete {split} partition; no silent exclusions")
        checkpoints = episode(assignment)
        for checkpoint, answer in zip(checkpoints, state["answers"], strict=True):
            result.append(
                Row(
                    assignment_id=assignment.assignment_id,
                    matched_group=assignment.matched_group,
                    split=split,
                    index=checkpoint.index,
                    final=checkpoint.index == len(checkpoints) - 1,
                    x=tuple(raw_features(checkpoint) if raw else map(float, features(checkpoint))),
                    response=answer["answer"]["probability"],
                    decision=answer["answer"]["decision"],
                )
            )
    return result


def baseline_fit(train, plan):
    x, y = arrays(train, plan)
    calibration, _ = solve(np.column_stack([x[:, 0], x[:, 1] + x[:, 2]]), y)
    one_gain, _ = solve(np.column_stack([x[:, 0], x[:, 1], x[:, 2] + x[:, 3]]), y)
    return {
        "reference_calibration": calibration.tolist(),
        "one_gain_all_reports": one_gain.tolist(),
    }


def lock_predictions(directory):
    root = Path(directory)
    with operator_lock(root):
        return _lock_predictions(root, accounting(root))


def _lock_predictions(root, resources):
    with database(root) as (db, manifest, design):
        if manifest.purpose != "prediction_pilot":
            raise ValueError("Development costing cannot be promoted to a prediction pilot")
        old = db.execute("SELECT payload FROM metadata WHERE id='prediction_lock'").fetchone()
        if old:
            return old[0]
        if not complete_split(root, manifest, design, "profile"):
            raise ValueError("Complete every configuration's profile cases first")
        nonprofile = {a.assignment_id for a in design.assignments if a.split != "profile"}
        for configuration in manifest.configurations:
            if set(episode_states(root, configuration.configuration_id)) & nonprofile:
                raise ValueError("Later cases have already been opened; retire this design")
        require_execution(root, manifest, design, "profile", resources=resources)
        plan = design.analysis_plan.model_copy(
            update={"bootstrap_draws": min(1000, manifest.acceptance.bootstrap_draws)}
        )
        training = {
            c.configuration_id: rows(root, c.configuration_id, design, "profile")
            for c in manifest.configurations
        }
        pooled = fit_profile(
            [r for values in training.values() for r in values], plan, bootstrap=False
        )
        configurations = {}
        for configuration in manifest.configurations:
            cid = configuration.configuration_id
            fit = fit_profile(training[cid], plan, seed=manifest.acceptance.bootstrap_seed)
            raw_fit = fit_profile(
                rows(root, cid, design, "profile", raw=True),
                plan,
                seed=manifest.acceptance.bootstrap_seed,
            )
            baselines = baseline_fit(training[cid], plan)
            predictions = {}
            for assignment in design.assignments:
                if assignment.split != "heldout":
                    continue
                for checkpoint in episode(assignment):
                    x = features(checkpoint)
                    predictions[checkpoint.checkpoint_id] = {
                        "individual": float(probability(x @ theta(fit))),
                        "pooled": float(probability(x @ theta(pooled))),
                        "reference_calibration": float(
                            probability(
                                np.array([1, x[1] + x[2]]) @ baselines["reference_calibration"]
                            )
                        ),
                        "one_gain_all_reports": float(
                            probability(
                                np.array([1, x[1], x[2] + x[3]]) @ baselines["one_gain_all_reports"]
                            )
                        ),
                        "raw_source_sensitivity": float(
                            probability(np.array(raw_features(checkpoint)) @ theta(raw_fit))
                        ),
                    }
            # No held-out answers appear in this artifact; persistence's causal rule is fixed here.
            configurations[cid] = {
                "individual_fit": fit,
                "raw_source_fit": raw_fit,
                "baselines": baselines,
                "profile_responses_sha256": digest(json_bytes([r.__dict__ for r in training[cid]])),
                "heldout_predictions": predictions,
            }
        value = {
            "benchmark_sha256": digest((root / "benchmark.json").read_bytes()),
            "locked_at": now(),
            "configurations": configurations,
            "pooled_fit": pooled,
            "persistence_rule": "previous accepted probability within episode, supplied base rate at index zero",
            "primary_checkpoints": "index > 0",
            "comparators": list(COMPARATORS),
            "acceptance": manifest.acceptance.model_dump(mode="json"),
            "protocol_status": resources["recovery"]["protocol_status"],
            "execution_scope": resources["recovery"]["execution_scope"],
            "recovery_at_lock": resources["recovery"],
            "accounting_complete_at_lock": resources["totals"]["accounting_complete"],
        }
        raw = json_bytes(value)
        db.execute("INSERT INTO metadata VALUES ('prediction_lock', ?)", (raw,))
        return raw


def paired_comparison(datasets, predictions, acceptance):
    ids = sorted(datasets)
    groups = sorted({r.matched_group for r in datasets[ids[0]] if r.index > 0})
    # All configurations receive the same matched groups; resample the same blocks across them.
    group_mse = {}
    for cid in ids:
        group_mse[cid] = {}
        for name in PREDICTORS:
            observed = np.array([r.response for r in datasets[cid]])
            errors = (np.array(predictions[cid][name]) - observed) ** 2
            group_mse[cid][name] = np.array(
                [
                    float(
                        np.mean(
                            errors[
                                [
                                    i
                                    for i, r in enumerate(datasets[cid])
                                    if r.index > 0 and r.matched_group == group
                                ]
                            ]
                        )
                    )
                    for group in groups
                ]
            )
    means = {
        name: float(np.mean([np.sqrt(np.mean(group_mse[cid][name])) for cid in ids]))
        for name in PREDICTORS
    }
    rng = np.random.default_rng(acceptance.bootstrap_seed)
    samples = rng.integers(0, len(groups), size=(acceptance.bootstrap_draws, len(groups)))
    draws = {
        name: np.mean([np.sqrt(group_mse[cid][name][samples].mean(axis=1)) for cid in ids], axis=0)
        for name in PREDICTORS
    }
    comparisons = {}
    for name in COMPARATORS:
        delta = means[name] - means["individual"]
        interval = np.quantile(draws[name] - draws["individual"], [0.025, 0.975]).tolist()
        comparisons[name] = {
            "rmse_improvement": delta,
            "interval_95": interval,
            "minimum_effect_met": delta >= acceptance.min_absolute_rmse_gain,
            "lower_bound_above_zero": interval[0] > 0,
        }
    passed = all(
        v["minimum_effect_met"] and v["lower_bound_above_zero"] for v in comparisons.values()
    )
    adequate = all(
        float(np.sqrt(np.mean(group_mse[cid]["individual"]))) <= acceptance.max_individual_rmse
        for cid in ids
    )
    return {
        "macro_rmse": means,
        "comparisons": comparisons,
        "each_configuration_adequate": adequate,
        "criteria_met": passed and adequate,
        "matched_groups": len(groups),
        "configuration_count": len(ids),
        "uncertainty_scope": "paired percentile bootstrap of matched groups, conditional on fixed configurations and fitted profiles; not population or fit uncertainty",
    }


def analyze(directory):
    root = Path(directory)
    with operator_lock(root):
        manifest, design, manifest_hash = load(root)
        if manifest.purpose != "prediction_pilot":
            raise ValueError("A development-costing run cannot produce a prediction claim")
        with database(root) as (db, _, _):
            prior = db.execute("SELECT payload FROM metadata WHERE id='report'").fetchone()
            if prior:
                return prior[0]
            locked = db.execute(
                "SELECT payload FROM metadata WHERE id='prediction_lock'"
            ).fetchone()
            if locked is None:
                raise ValueError("No frozen predictions")
        lock = json.loads(locked[0])
        resources = accounting(root)
        # Check execution before freezing collection exports: an unresolved final
        # process may still need a finish-only recovery with its existing receipt.
        require_execution(root, manifest, design, resources=resources)
        sources, datasets, predictions, configurations = {}, {}, {}, {}
        for configuration in manifest.configurations:
            cid = configuration.configuration_id
            export = export_collection(root / "collections" / cid)
            sources[cid] = digest(export)
            train = rows(root, cid, design, "profile")
            stored = lock["configurations"][cid]
            if (
                digest(json_bytes([r.__dict__ for r in train]))
                != stored["profile_responses_sha256"]
            ):
                raise ValueError("Profile responses changed after locking")
            heldout = rows(root, cid, design, "heldout")
            predictions[cid] = {
                name: np.array(
                    [
                        stored["heldout_predictions"][f"{r.assignment_id}:{r.index}"][name]
                        for r in heldout
                    ]
                )
                for name in PREDICTORS
                if name != "persistence"
            }
            predictions[cid]["persistence"] = persistence_baseline(heldout)
            datasets[cid] = heldout
            mask = [i for i, r in enumerate(heldout) if r.index > 0]
            configurations[cid] = {
                "profile": stored["individual_fit"],
                "raw_source_sensitivity_profile": stored["raw_source_fit"],
                "post_evidence_prediction": {
                    name: prediction_metrics([heldout[i] for i in mask], values[mask])
                    for name, values in predictions[cid].items()
                },
                "conditional_task_quality": conditional_task_metrics(heldout),
            }
        cohort = paired_comparison(datasets, predictions, manifest.acceptance)
        report = BenchmarkReport(
            benchmark_version=manifest.benchmark_version,
            benchmark_sha256=manifest_hash,
            lock_sha256=digest(locked[0]),
            source_hashes=sources,
            response_origin=manifest.response_origin,
            result="criteria_met" if cohort["criteria_met"] else "criteria_not_met",
            cohort=cohort,
            configurations=configurations,
            accounting=resources,
            protocol_status=resources["recovery"]["protocol_status"],
            execution_scope=resources["recovery"]["execution_scope"],
            accounting_complete=resources["totals"]["accounting_complete"],
            limitations=[
                "Effective reporting weights are conditional on source inference, not internal beliefs or unique cognitive mechanisms.",
                "Explicit provenance, two source strengths and one binary-source task family; no general cognitive-security certification.",
                "Acceptance thresholds are pragmatic pilot targets, not power-validated effect sizes or population norms.",
                "Fixed-configuration matched-group uncertainty excludes uncertainty from fitting; profile intervals are reported separately.",
                "Raw-frequency source inference is a predeclared sensitivity analysis, not a selected replacement for the primary model.",
                "Decision scores are expectations under the evaluator model, not realized financial or forecasting outcomes.",
                "No intervention, personalization benefit, payment, passport issuance or independently verified execution is established.",
                "Recovery, when present, uses a fresh context with accepted public history; results include those cases and do not describe uninterrupted execution alone.",
                "Unknown usage remains unknown. Admission reserves are planning charges, not measured tokens, dollar costs or upper bounds on actual usage.",
                "An amended protocol is labeled explicitly and cannot establish completion of its original no-retry predecessor.",
            ],
        )
        raw = encoded(report)
        with database(root) as (db, _, _):
            db.execute("INSERT INTO metadata VALUES ('report', ?)", (raw,))
        return raw
