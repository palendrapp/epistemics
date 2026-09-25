"""Synthetic model discrimination, nuisance recovery and prospective prediction checks."""

from collections import Counter

import numpy as np

from epistemics.source_inference.measurement import (
    BLOCK_SD,
    INDEPENDENT_SD,
    fit,
    sample_reports,
    sigmoid,
)
from epistemics.source_inference.observers import FAMILIES

# These engineering screens are declared in the run plan, not inferred from the results.
GATES = {
    "minimum_primary_pair_best_family_accuracy": 0.9,
    "maximum_joint_gain_mae": 0.15,
    "maximum_joint_new_input_rmse_pp": 5.0,
    "require_ambiguous_neutral_control": True,
    "require_reject_all_on_direction_reversal": True,
    "require_representative_audit_equivalence": True,
}
GENERATING_GAINS = (0.83, 1.0, 1.17)  # Two values lie between fitted grid points.


def experiment(
    calibration,
    heldout,
    blocks,
    heldout_blocks,
    indices,
    repetitions,
    seed,
    independent_sd=INDEPENDENT_SD,
):
    if repetitions < 1:
        raise ValueError("At least one synthetic repetition is required")
    rng = np.random.default_rng(seed)
    summaries = {
        name: {
            "best_family_confusion": {f: Counter() for f in FAMILIES},
            "decisive_confusion": {f: Counter() for f in FAMILIES},
            "conditional_on_generating_family": {
                f: {"gain_errors": [], "prediction_errors": []} for f in FAMILIES
            },
            "selected_family_prediction_errors": {f: [] for f in FAMILIES},
            "primary_pair_correct": {f: 0 for f in FAMILIES[:2]},
        }
        for name in indices
    }
    for family_index, family in enumerate(FAMILIES):
        for repetition in range(repetitions):
            gain = GENERATING_GAINS[repetition % len(GENERATING_GAINS)]
            # Common random responses for shared probes make design comparisons paired.
            observed = sample_reports(calibration[family_index], gain, blocks, rng, independent_sd)
            truth = sigmoid(heldout[family_index] * gain)
            for name, chosen in indices.items():
                result = fit(
                    calibration[:, chosen],
                    observed[chosen],
                    np.asarray(blocks)[chosen],
                    independent_sd,
                )
                summary = summaries[name]
                summary["best_family_confusion"][family][result["best_family"]] += 1
                summary["decisive_confusion"][family][result["decision"]] += 1
                parameters = result["families"][family]
                estimated_gain = parameters["best_gain"]
                error = float(
                    100
                    * np.sqrt(
                        np.mean((sigmoid(heldout[family_index] * estimated_gain) - truth) ** 2)
                    )
                )
                recovered = summary["conditional_on_generating_family"][family]
                recovered["gain_errors"].append(abs(estimated_gain - gain))
                recovered["prediction_errors"].append(error)
                selected = result["best_family"]
                prediction = sigmoid(
                    heldout[FAMILIES.index(selected)] * result["families"][selected]["best_gain"]
                )
                summary["selected_family_prediction_errors"][family].append(
                    float(100 * np.sqrt(np.mean((prediction - truth) ** 2)))
                )
                if family in FAMILIES[:2]:
                    scores = {
                        f: result["families"][f]["log_marginal_likelihood"] for f in FAMILIES[:2]
                    }
                    other = FAMILIES[1 - family_index]
                    summary["primary_pair_correct"][family] += scores[family] > scores[other] + 1e-9
    for summary in summaries.values():
        summary["best_family_confusion"] = {
            f: dict(c) for f, c in summary["best_family_confusion"].items()
        }
        summary["decisive_confusion"] = {
            f: dict(c) for f, c in summary["decisive_confusion"].items()
        }
        summary["primary_pair_accuracy"] = {
            f: float(n / repetitions) for f, n in summary.pop("primary_pair_correct").items()
        }
        for row in summary["conditional_on_generating_family"].values():
            row["gain_mae"] = float(np.mean(row.pop("gain_errors")))
            row["new_input_latent_rmse_pp"] = float(np.mean(row.pop("prediction_errors")))
        summary["selected_family_new_input_latent_rmse_pp"] = {
            f: float(np.mean(v))
            for f, v in summary.pop("selected_family_prediction_errors").items()
        }
    return {
        "repetitions_per_family": repetitions,
        "datasets": repetitions * len(FAMILIES),
        "independent_logit_sd": independent_sd,
        "source_block_logit_sd": BLOCK_SD,
        "generating_gains": GENERATING_GAINS,
        "designs": summaries,
        "heldout_probes": len(heldout_blocks),
        "scope": "Synthetic responses and new public histories; noiseless latent forecasts are the prediction target; no empirical agent validation",
    }


def controls(calibration, heldout, blocks, heldout_blocks, chosen, seed, representative_indices):
    rng = np.random.default_rng(seed)
    neutral = fit(np.zeros((len(FAMILIES), 8)), np.full(8, 0.5), ["neutral"] * 8)
    representative = calibration[:, representative_indices]
    representative_blocks = np.asarray(blocks)[representative_indices]
    representative_answers = sample_reports(representative[0], 1, representative_blocks, rng)
    representative_fit = fit(representative, representative_answers, representative_blocks)
    representative_difference = float(np.max(np.abs(representative[0] - representative[1])))
    # A deliberately excluded response process. Fit first, assess on independent responses.
    train = sample_reports(-calibration[0, chosen], 1, np.asarray(blocks)[chosen], rng)
    fitted = fit(calibration[:, chosen], train, np.asarray(blocks)[chosen])
    test = sample_reports(-heldout[0], 1, heldout_blocks, rng)
    adequacy = {}
    for i, family in enumerate(FAMILIES):
        gain = fitted["families"][family]["best_gain"]
        mean = sigmoid(heldout[i] * gain)
        observed_error = float(100 * np.sqrt(np.mean((test - mean) ** 2)))
        replicated = [
            float(
                100
                * np.sqrt(
                    np.mean((sample_reports(heldout[i], gain, heldout_blocks, rng) - mean) ** 2)
                )
            )
            for _ in range(256)
        ]
        boundary = float(np.quantile(replicated, 0.99))
        adequacy[family] = {
            "observed_new_input_rmse_pp": observed_error,
            "conditional_99_percent_simulation_boundary_pp": boundary,
            "outside_simulation_boundary": observed_error > boundary,
        }
    return {
        "neutral_control": neutral,
        "representative_audit_equivalence": {
            "maximum_joint_flat_logit_difference": representative_difference,
            "joint_flat_log_evidence_difference": abs(
                representative_fit["families"][FAMILIES[0]]["log_marginal_likelihood"]
                - representative_fit["families"][FAMILIES[1]]["log_marginal_likelihood"]
            ),
            "meaning": "Once random sampling is established, the joint and flat models have identical predictions despite informative company evidence",
        },
        "direction_reversal": {
            "selected_training_model": fitted["best_family"],
            "heldout_adequacy": adequacy,
            "all_candidates_inadequate": all(
                r["outside_simulation_boundary"] for r in adequacy.values()
            ),
            "scope": "Conditional simulation screen at fitted parameters; not a calibrated composite-model hypothesis test",
        },
    }


def check_gates(experiment_result, control_result):
    diagnostic = experiment_result["designs"]["diagnostic"]
    joint = diagnostic["conditional_on_generating_family"]["joint_process"]
    checks = {
        "primary_pair_discrimination": min(diagnostic["primary_pair_accuracy"].values())
        >= GATES["minimum_primary_pair_best_family_accuracy"],
        "joint_response_gain_recovery": joint["gain_mae"] <= GATES["maximum_joint_gain_mae"],
        "joint_new_input_prediction": joint["new_input_latent_rmse_pp"]
        <= GATES["maximum_joint_new_input_rmse_pp"],
        "neutral_ambiguity": control_result["neutral_control"]["decision"] == "ambiguous"
        and all(
            len(r["tied_gains"]) == 13
            for r in control_result["neutral_control"]["families"].values()
        ),
        "model_rejection": control_result["direction_reversal"]["all_candidates_inadequate"],
        "representative_equivalence": control_result["representative_audit_equivalence"][
            "maximum_joint_flat_logit_difference"
        ]
        < 1e-9
        and control_result["representative_audit_equivalence"]["joint_flat_log_evidence_difference"]
        < 1e-8,
    }
    return {"criteria": GATES, "checks": checks, "passed": all(checks.values())}
