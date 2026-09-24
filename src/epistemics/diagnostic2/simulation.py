"""Declared recovery checks for an authored model family; no real respondents."""

import numpy as np

from epistemics.diagnostic2.battery import schedule
from epistemics.diagnostic2.inference import GRID, PARAMETERS, SD, fit, predictions
from epistemics.diagnostic2.models import Answer
from epistemics.investigation.inference import report_log_likelihood, simulate_reports

GENERATORS = {
    "reference": (1, 1, 1, 1, 1),
    "records_attenuation": (1, 0.5, 1, 1, 1),
    "signal_attenuation": (1, 1, 0.5, 1, 1),
    "selective_propagation": (1, 1, 1, 0.5, 1),
    "auxiliary_smoothing": (1, 1, 1, 1, 0.5),
    "combined": (1.25, 0.75, 1.5, 0.5, 0.75),
}
GATES = {
    "parameter_mae_max": 0.20,
    "new_collection_mean_prediction_rmse_max_pp": 5.0,
    "out_of_family_repeat_reversal_rmse_min_pp": 8.0,
}


def answers(a, parameters=(1, 1, 1, 1, 1)):
    p = np.round(predictions([a], parameters)[0], 2)
    return [
        Answer(
            growth_probability=0.5,
            auxiliary_probability=0.5,
            auxiliary_if_growth=p[0],
            auxiliary_if_no_growth=p[1],
        ),
        Answer(growth_probability=p[2], auxiliary_probability=p[3]),
        Answer(growth_probability=p[4], auxiliary_probability=p[5]),
        Answer(growth_probability=int(a.growth_outcome), auxiliary_probability=p[6]),
    ]


def recovery(seed=20260924, repetitions=16):
    from epistemics.diagnostic2.service import fingerprint

    if repetitions < 1:
        raise ValueError("At least one repetition is required")
    rng = np.random.default_rng(seed)
    train, test = schedule(seed), schedule(seed + 1)
    means = predictions(train)
    errors, prediction_errors, comparisons, by_generator = [], [], [], {}
    for generator, parameters in GENERATORS.items():
        local_errors = []
        for _ in range(repetitions):
            values = simulate_reports(predictions(train, parameters)[0], rng, sd=SD)
            fits = fit(values, train, means=means)
            estimate = [fits["full"]["parameters"][p] for p in PARAMETERS]
            error = np.abs(np.array(parameters) - estimate)
            errors.append(error)
            local_errors.append(error)
            truth = predictions(test, parameters)[0]
            prediction_errors.append(
                float(np.sqrt(np.mean((predictions(test, estimate)[0] - truth) ** 2)) * 100)
            )
            # New noise/order/resolutions, SAME templates; no domain-generalization claim.
            future = simulate_reports(truth, rng, sd=SD)
            scores = {}
            for name, fitted in fits.items():
                p = [fitted["parameters"][k] for k in PARAMETERS]
                scores[name] = float(
                    report_log_likelihood(future, predictions(test, p)[0], sd=SD).sum()
                )
            comparisons.append({"generator": generator, "heldout_log_scores": scores})
        by_generator[generator] = dict(
            zip(PARAMETERS, np.mean(local_errors, axis=0).tolist(), strict=True)
        )
    mae = np.mean(errors, axis=0)
    zero = fit(np.round(predictions(train, (0, 0, 1, 1, 1))[0], 2), train, means=means)["full"]
    stationary = fit(np.round(predictions(train, (1, 1, 1, 0.5, 0))[0], 2), train, means=means)[
        "full"
    ]
    negative = predictions(train, (1, 1, 1, 1, 1))[0].reshape(16, 7).copy()
    for i, a in enumerate(train):
        if a.evidence == "signal":
            negative[i, 4] = 1 - negative[i, 2]
    negative_fit = fit(np.round(negative.ravel(), 2), train, means=means)["full"]
    degeneracy = all(
        "propagation_fraction" in f["parameters_varying_across_grid_ties"]
        for f in (zero, stationary)
    )
    return {
        "schema_version": "epistemics.auxiliary-recovery.v2",
        "implementation_sha256": fingerprint(),
        "seed": seed,
        "repetitions_per_generator": repetitions,
        "datasets": len(errors),
        "gates": GATES,
        "noise_logit_sd": SD,
        "grid_size": len(GRID),
        "parameter_mae": dict(zip(PARAMETERS, mae.tolist(), strict=True)),
        "parameter_mae_by_generator": by_generator,
        "new_collection_mean_prediction_rmse_pp": float(np.mean(prediction_errors)),
        "restricted_family_comparisons": comparisons,
        "degenerate_propagation_flagged": degeneracy,
        "out_of_family_repeat_reversal_rmse_pp": negative_fit["rmse_pp"],
        "passed": bool(
            max(mae) <= GATES["parameter_mae_max"]
            and np.mean(prediction_errors) <= GATES["new_collection_mean_prediction_rmse_max_pp"]
            and negative_fit["rmse_pp"] >= GATES["out_of_family_repeat_reversal_rmse_min_pp"]
            and degeneracy
        ),
        "scope": (
            "Synthetic recovery on separated grid profiles with fixed independent noise and "
            "the same archive templates. Nested model ties are not unique model recovery; "
            "unknown noise, heterogeneous strategies and empirical usefulness are unvalidated."
        ),
    }


def simulate(directory, seed=20260924):
    from epistemics.diagnostic2.service import DiagnosticService, create, export

    manifest = create(
        directory,
        {
            "kind": "agent",
            "subject_id": "synthetic:auxiliary2-preview",
            "configuration": {
                "model": "synthetic",
                "model_version": "reference/0.2",
                "configuration_sha256": "0" * 64,
            },
        },
        seed=seed,
        synthetic=True,
    )
    for a in manifest.assignments:
        service = DiagnosticService(directory, a.assignment_id)
        for index, answer in enumerate(answers(a)):
            service.submit(f"{a.assignment_id}:{index}", answer)
        service.finish()
    return export(directory)
