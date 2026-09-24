"""Own-report updating and research coverage after independent corroboration."""

import numpy as np

from epistemics.narrative.inference import (
    ARTIFACT,
    DEMAND,
    condition,
    entropy,
    final_state,
    fit,
    normalize,
    rounding_compatibility,
    total_variation_pp,
)


def analyze(cases, assignments):
    facts, inputs, observed, excluded = [], [], [], []
    for a in assignments:
        rows = cases[a.assignment_id]
        joints = [np.array(row.answer.joint.vector()) for row in rows]
        likelihoods = np.array(rows[0].answer.signal_if_state.vector())
        query = rows[1].answer.query
        signal_ref = normalize(joints[0] * likelihoods)
        audit_ref = condition(joints[1], query, a)
        information = {
            "demand_audit": entropy(joints[1] @ DEMAND),
            "pipeline_audit": entropy(joints[1] @ ARTIFACT),
            "stop": 0.0,
        }
        eligible = np.all(joints[0] > 0) and np.all(likelihoods > 0)
        if eligible:
            inputs.append((joints[0], likelihoods, query, a))
            observed.append(joints[1:])
        else:
            excluded.append(
                {"assignment_id": a.assignment_id, "reason": "zero_in_declared_prior_or_likelihood"}
            )
        unobserved = ARTIFACT if query == "demand_audit" else DEMAND
        audit_mask = (
            DEMAND == a.demand_outcome
            if query == "demand_audit"
            else ARTIFACT == a.artifact_outcome
            if query == "pipeline_audit"
            else np.ones(4, dtype=bool)
        )
        facts.append(
            {
                "assignment_id": a.assignment_id,
                "pair_id": a.pair_id,
                "domain": a.domain,
                "direction": a.direction,
                "presentation": a.presentation,
                "corroboration": a.corroboration,
                "initial_joint": joints[0].tolist(),
                "declared_signal_likelihoods": likelihoods.tolist(),
                "both_implies_signal_shortfall_pp": float(100 * (1 - likelihoods[2])),
                "joint_reports": [j.tolist() for j in joints],
                "demand_marginals": [float(j @ DEMAND) for j in joints],
                "artifact_marginals": [float(j @ ARTIFACT) for j in joints],
                "dependence_covariance": [
                    float(j[2] - (j @ DEMAND) * (j @ ARTIFACT)) for j in joints
                ],
                "signal_reference": None if signal_ref is None else signal_ref.tolist(),
                "signal_reference_undefined": signal_ref is None,
                "signal_consistency_gap_tv_pp": total_variation_pp(joints[1], signal_ref),
                "signal_rounding_sensitivity": rounding_compatibility(
                    joints[0], joints[1], likelihoods=likelihoods
                ),
                "query": query,
                "query_expected_information_bits": information,
                "query_foregone_information_bits": max(information.values()) - information[query],
                "query_within_0_01_bits_of_best": max(information.values()) - information[query]
                <= 0.01,
                "audit_reference": None if audit_ref is None else audit_ref.tolist(),
                "audit_reference_undefined": audit_ref is None,
                "audit_consistency_gap_tv_pp": total_variation_pp(joints[2], audit_ref),
                "audit_rounding_sensitivity": rounding_compatibility(
                    joints[1], joints[2], mask=audit_mask
                ),
                "unobserved_event_change_pp": None
                if query == "stop"
                else float(100 * (joints[2] - joints[1]) @ unobserved),
                "unobserved_event_reference_change_pp": None
                if query == "stop" or audit_ref is None
                else float(100 * (audit_ref - joints[1]) @ unobserved),
                "final_resolution_error_tv_pp": total_variation_pp(joints[3], final_state(a)),
            }
        )
    contrasts = []
    for pair in sorted({a.pair_id for a in assignments}):
        d = next(r for r in facts if r["pair_id"] == pair and r["corroboration"] == "demand")
        s = next(r for r in facts if r["pair_id"] == pair and r["corroboration"] == "artifact")
        contrasts.append(
            {
                "pair_id": pair,
                "domain": d["domain"],
                "direction": d["direction"],
                "initial_demand_difference_pp": 100
                * (d["demand_marginals"][0] - s["demand_marginals"][0]),
                "initial_artifact_difference_pp": 100
                * (d["artifact_marginals"][0] - s["artifact_marginals"][0]),
                "post_signal_demand_difference_pp": 100
                * (d["demand_marginals"][1] - s["demand_marginals"][1]),
                "post_signal_artifact_difference_pp": 100
                * (d["artifact_marginals"][1] - s["artifact_marginals"][1]),
                "query_with_demand_corroboration": d["query"],
                "query_with_artifact_corroboration": s["query"],
                "research_choice_changed": d["query"] != s["query"],
            }
        )
    best_counts = {"demand_audit": 0, "pipeline_audit": 0, "within_0_01_bits": 0}
    choice_counts = {"demand_audit": 0, "pipeline_audit": 0, "stop": 0}
    for row in facts:
        information = row["query_expected_information_bits"]
        difference = information["demand_audit"] - information["pipeline_audit"]
        best = (
            "within_0_01_bits"
            if abs(difference) <= 0.01
            else "demand_audit"
            if difference > 0
            else "pipeline_audit"
        )
        best_counts[best] += 1
        choice_counts[row["query"]] += 1
    policy_regret = {
        q: float(
            np.mean(
                [
                    max(r["query_expected_information_bits"].values())
                    - r["query_expected_information_bits"][q]
                    for r in facts
                ]
            )
        )
        for q in choice_counts
    }
    return {
        "analysis_version": "narrative-analysis/0.2.0",
        "facts": facts,
        "matched_corroboration_contrasts": contrasts,
        "research_coverage": {
            "strictly_more_informative_counts": best_counts,
            "chosen_counts": choice_counts,
            "both_audits_have_at_least_two_informative_cases": min(
                best_counts["demand_audit"], best_counts["pipeline_audit"]
            )
            >= 2,
            "both_audits_observed": min(
                choice_counts["demand_audit"], choice_counts["pipeline_audit"]
            )
            >= 1,
            "observed_mean_foregone_information_bits": float(
                np.mean([r["query_foregone_information_bits"] for r in facts])
            ),
            "fixed_policy_mean_foregone_information_bits": policy_regret,
            "meaning": "Task coverage and choice consistency under reported uncertainty; no identification of a unique search strategy or decision-value benefit",
        },
        "conditional_report_model": fit(inputs, observed),
        "fit_exclusions": excluded,
        "model_parameters_are_passport_traits": False,
        "empirical_predictive_validation": False,
    }
