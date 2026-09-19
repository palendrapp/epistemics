"""Synthetic recovery and structural holdout checks; no real-agent conclusions."""

import numpy as np

from epistemics.predictive.analysis import (
    PARAMETERS,
    Row,
    all_reports_baseline,
    conditional_task_metrics,
    features,
    fit_profile,
    persistence_baseline,
    predict,
    prediction_metrics,
    probability,
)
from epistemics.predictive.design import budget, digest, encoded, episode
from epistemics.predictive.models import Parameters, SyntheticValidation

PROFILES = {
    "reference": Parameters(),
    "counts_copies": Parameters(copy_weight=1),
    "weak_evidence_response": Parameters(evidence_weight=0.45),
    "combined": Parameters(intercept=0.2, prior_weight=1.3, evidence_weight=0.8, copy_weight=0.55),
}


def simulate(manifest, parameters, *, seed=0, noise_sd=0, thresholded_copying=False):
    rng = np.random.default_rng(seed)
    theta = np.array([getattr(parameters, name) for name in PARAMETERS])
    # Matched twins share a group perturbation; bootstrap retains this dependence.
    groups = {
        g: rng.normal(0, noise_sd / 2)
        for g in sorted({a.matched_group for a in manifest.assignments})
    }
    rows = []
    for assignment in manifest.assignments:
        checkpoints = episode(assignment)
        for checkpoint in checkpoints:
            x = features(checkpoint)
            copies = sum(c.based_on is not None for c in checkpoint.evidence)
            extra = 1.2 * x[3] if thresholded_copying and copies >= 2 else 0
            p = float(
                probability(
                    x @ theta + extra + groups[assignment.matched_group] + rng.normal(0, noise_sd)
                )
            )
            rows.append(
                Row(
                    assignment_id=assignment.assignment_id,
                    matched_group=assignment.matched_group,
                    split=assignment.split,
                    index=checkpoint.index,
                    final=checkpoint.index == len(checkpoints) - 1,
                    x=tuple(map(float, x)),
                    response=p,
                    decision="act" if p > 0.5 else "defer",
                )
            )
    return rows


def validation(manifest, *, seed=1909):
    plan = manifest.analysis_plan
    recovery, prediction, datasets = [], [], {}
    checks = {}
    for i, (name, generating) in enumerate(PROFILES.items()):
        exact = simulate(manifest, generating)
        exact_fit = fit_profile([r for r in exact if r.split == "profile"], plan, bootstrap=False)
        exact_error = max(
            abs(exact_fit["parameters"][key] - getattr(generating, key)) for key in PARAMETERS
        )
        rows = simulate(manifest, generating, seed=seed + i, noise_sd=plan.synthetic_logit_noise_sd)
        datasets[name] = rows
        fitted = fit_profile([r for r in rows if r.split == "profile"], plan, seed=seed + i)
        noisy_error = max(
            abs(fitted["parameters"][key] - getattr(generating, key)) for key in PARAMETERS
        )
        recovery.append(
            {
                "profile": name,
                "generating": generating.model_dump(),
                "fitted": fitted,
                "noiseless_max_parameter_error": exact_error,
                "noisy_max_parameter_error": noisy_error,
            }
        )
        checks[f"{name}_noiseless_recovery"] = exact_error <= plan.noiseless_max_error
        checks[f"{name}_noisy_recovery"] = noisy_error <= plan.noisy_max_parameter_error
        checks[f"{name}_bootstrap_available"] = fitted["interval_95"] is not None
    pooled_train = [r for rows in datasets.values() for r in rows if r.split == "profile"]
    pooled_fit = fit_profile(pooled_train, plan, bootstrap=False)
    for row in recovery:
        name = row["profile"]
        train = [r for r in datasets[name] if r.split == "profile"]
        heldout = [r for r in datasets[name] if r.split == "heldout"]
        metrics = {
            "individual": prediction_metrics(heldout, predict(heldout, row["fitted"])),
            "pooled": prediction_metrics(heldout, predict(heldout, pooled_fit)),
            "one_gain_all_reports": prediction_metrics(
                heldout, all_reports_baseline(train, heldout, plan)
            ),
            "persistence": prediction_metrics(heldout, persistence_baseline(heldout)),
        }
        prediction.append(
            {
                "profile": name,
                "heldout": metrics,
                "task_performance": conditional_task_metrics(heldout),
            }
        )
        checks[f"{name}_structural_holdout"] = (
            metrics["individual"]["probability_rmse"] <= plan.heldout_probability_rmse_limit
        )
    means = {
        name: float(np.mean([p["heldout"][name]["probability_rmse"] for p in prediction]))
        for name in ("individual", "pooled", "one_gain_all_reports", "persistence")
    }
    checks["individual_beats_synthetic_baselines_on_average"] = all(
        means["individual"] < means[name]
        for name in ("pooled", "one_gain_all_reports", "persistence")
    )
    # Negative control: a nonlinear policy is identical to reference on profile
    # graphs but changes after two copied reports. Do not call its weights recovered.
    stress = simulate(manifest, Parameters(), seed=seed, thresholded_copying=True)
    stress_fit = fit_profile([r for r in stress if r.split == "profile"], plan, bootstrap=False)
    stress_heldout = [r for r in stress if r.split == "heldout"]
    stress_metrics = prediction_metrics(stress_heldout, predict(stress_heldout, stress_fit))
    checks["thresholded_copying_fails_holdout_adequacy"] = (
        stress_metrics["probability_rmse"] > plan.heldout_probability_rmse_limit
    )
    return SyntheticValidation(
        manifest_sha256=digest(encoded(manifest)),
        validation_seed=seed,
        passed=all(checks.values()),
        checks=checks,
        budget=budget(manifest),
        recovery=recovery,
        prediction=prediction,
        misspecification={
            "generating_policy": "copy effect activates only after two copies",
            "heldout": stress_metrics,
            "detected": checks["thresholded_copying_fails_holdout_adequacy"],
            "mean_in_model_prediction_rmse": means,
        },
        limitations=[
            "Synthetic engineering validation only; no real agent, human, model-provider call or payment.",
            "Recovery under the generating model is not empirical validity; one nonlinear negative control does not cover all misspecification.",
            "Source accuracy uses a symmetric Beta(1,1) model with independent original assessments; these assumptions are not disclosed as likelihoods to participants.",
            "Weights describe reported responses conditional on that source model; source inference and output compression may be confounded.",
            "Holdout changes dependency structure and cover story within one binary-source world; broader mechanism or domain transfer is untested.",
            "Bootstrap intervals resample matched groups and describe this synthetic fit; population coverage is not established.",
            "Task scores are terminal expectations under the evaluator model, not realized outcomes or real-world forecasting evidence.",
            "Policy-development cases are reserved. No intervention effect, personalized support benefit, real-agent collection or passport issuance is implemented here.",
        ],
    )
