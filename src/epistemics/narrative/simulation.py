"""Synthetic recovery of conditional report mappings, not human/agent traits."""

import numpy as np

from epistemics.narrative.battery import schedule
from epistemics.narrative.inference import PARAMETERS, fit, predictions
from epistemics.narrative.models import STATES, Answer
from epistemics.narrative.service import NarrativeService, create, export

GENERATORS = {
    "declared_reference": (1, 1, 1),
    "less_signal_weight": (0.5, 1, 1),
    "more_signal_weight": (1.5, 1, 1),
    "less_joint_dependence": (1, 0.5, 1),
    "slower_report_adjustment": (1, 1, 0.5),
    "mixed": (0.5, 0.5, 0.75),
}


def quantize(joint):
    """Largest remainder allocation preserves the simplex, including its boundary."""
    values = np.asarray(joint) * 100
    whole = np.floor(values).astype(int)
    order = np.argsort(-(values - whole), kind="stable")
    whole[order[: 100 - int(whole.sum())]] += 1
    return whole / 100


def synthetic_inputs(assignments, seed):
    rng = np.random.default_rng(seed)
    return [
        (
            quantize(rng.dirichlet([6, 6, 6, 6])),
            np.round(
                [
                    rng.uniform(0.65, 0.9),
                    rng.uniform(0.6, 0.9),
                    1.0,  # D above threshold plus an exaggeration in that direction entails E.
                    rng.uniform(0.02, 0.15),
                ],
                2,
            ),
            "demand_audit" if i % 2 == 0 else "pipeline_audit",
            a,
        )
        for i, a in enumerate(assignments)
    ]


def answers(entry, parameters=(1, 1, 1)):
    prior, likelihoods, query, _ = entry
    reports = [prior, *predictions(*entry, parameters)]
    return [
        Answer(
            joint=dict(zip(STATES, quantize(joint), strict=True)),
            signal_if_state=dict(zip(STATES, likelihoods, strict=True)) if i == 0 else None,
            query=query if i == 1 else None,
        )
        for i, joint in enumerate(reports)
    ]


def simulate(directory, seed=20260924):
    manifest = create(
        directory,
        {
            "kind": "agent",
            "subject_id": "synthetic:narrative-reference",
            "configuration": {
                "model": "synthetic",
                "model_version": "1",
                "configuration_sha256": "0" * 64,
            },
        },
        seed=seed,
        synthetic=True,
    )
    for entry in synthetic_inputs(manifest.assignments, seed):
        a = entry[-1]
        service = NarrativeService(directory, a.assignment_id)
        for i, answer in enumerate(answers(entry)):
            service.submit(f"{a.assignment_id}:{i}", answer)
        service.finish()
    return export(directory)


def recovery(seed=20260924, repetitions=16):
    if repetitions < 1:
        raise ValueError("At least one repetition required")
    assignments = schedule(seed)
    inputs = synthetic_inputs(assignments, seed)
    heldout = synthetic_inputs(schedule(seed + 1), seed + 1)
    rng = np.random.default_rng(seed)
    errors, prediction_errors, exact = [], [], []
    for parameters in GENERATORS.values():
        clean = np.array([predictions(*entry, parameters) for entry in inputs])
        exact_fit = fit(inputs, clean)["families"]["full"]
        exact.append(
            exact_fit["tied_grid_points"] == 1
            and list(exact_fit["minimizers"][0].values()) == list(parameters)
        )
        truth = np.array([predictions(*entry, parameters) for entry in heldout])
        for _ in range(repetitions):
            # Independent checkpoint noise projected to the simplex, then whole percentages.
            noisy = np.maximum(0, clean + rng.normal(0, 0.008, clean.shape))
            noisy /= noisy.sum(axis=-1, keepdims=True)
            noisy = np.array([[quantize(j) for j in case] for case in noisy])
            fitted = fit(inputs, noisy)["families"]["full"]["minimizers"][0]
            estimate = [fitted[p] for p in PARAMETERS]
            errors.append(np.abs(np.array(estimate) - parameters))
            pred = np.array([predictions(*entry, estimate) for entry in heldout])
            prediction_errors.append(float(100 * np.sqrt(np.mean((pred - truth) ** 2))))
    degenerate = fit(inputs, np.array([predictions(*entry, (1, 1, 0)) for entry in inputs]))[
        "families"
    ]["full"]
    # A final report contradicting a definitive audit cannot be represented by this family.
    outside = np.array([predictions(*entry, (1, 1, 1)) for entry in inputs])
    outside[:, 2] = np.roll(outside[:, 2], 1, axis=-1)
    misspecification = fit(inputs, outside)["families"]["full"]["rmse_pp"]
    mae = np.mean(errors, axis=0)
    result = {
        "seed": seed,
        "datasets": repetitions * len(GENERATORS),
        "noise": "SD 0.008 additive independent coordinate noise, truncated at zero, renormalized and quantized",
        "parameter_mean_absolute_errors": dict(zip(PARAMETERS, map(float, mae), strict=True)),
        "all_clean_profiles_uniquely_recovered": all(exact),
        "mean_new_input_latent_prediction_rmse_pp": float(np.mean(prediction_errors)),
        "zero_adjustment_nonidentifiability_flagged": degenerate["tied_grid_points"] == 25,
        "out_of_family_best_rmse_pp": misspecification,
        "scope": "Conditional on known elicited inputs, this grid, noise process and synthetic templates; no empirical predictive validation or internal-belief recovery",
    }
    result["passed"] = bool(
        all(exact)
        and np.max(mae) <= 0.1
        and np.mean(prediction_errors) <= 1
        and degenerate["tied_grid_points"] == 25
        and misspecification >= 8
    )
    return result
