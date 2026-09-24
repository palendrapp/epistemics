"""Own-report consistency facts and explicitly conditional, descriptive point fits."""

from itertools import product

import numpy as np

PARAMETERS = ("signal_weight", "dependence_retention", "report_adjustment")
GRID = np.array(
    list(product((0, 0.5, 1, 1.5, 2), (0, 0.25, 0.5, 0.75, 1), (0, 0.25, 0.5, 0.75, 1)))
)
DEMAND = np.array([1, 0, 1, 0], dtype=bool)
ARTIFACT = np.array([0, 1, 1, 0], dtype=bool)


def normalize(weights):
    total = float(np.sum(weights))
    return None if total <= 0 else np.asarray(weights, dtype=float) / total


def condition(joint, query, a):
    if query == "stop":
        return np.asarray(joint, dtype=float)
    mask = DEMAND == a.demand_outcome if query == "demand_audit" else ARTIFACT == a.artifact_outcome
    return normalize(np.asarray(joint) * mask)


def final_state(a):
    return ((DEMAND == a.demand_outcome) & (ARTIFACT == a.artifact_outcome)).astype(float)


def independent(joint):
    d, s = np.asarray(joint) @ DEMAND, np.asarray(joint) @ ARTIFACT
    return np.array([d * (1 - s), (1 - d) * s, d * s, (1 - d) * (1 - s)])


def entropy(p):
    return float(-sum(x * np.log2(x) for x in (p, 1 - p) if x > 0))


def total_variation_pp(left, right):
    return None if right is None else float(50 * np.sum(np.abs(np.asarray(left) - right)))


def rounding_compatibility(prior, report, *, likelihoods=None, mask=None):
    """Conservative coordinate bounds; overlap is necessary, not sufficient, for consistency.

    Treat every whole-percent report as a nearest-percent rounding bin. Ignore the
    sum-to-one constraint on its unrounded inputs, widening rather than narrowing
    the bounds. This is a sensitivity check, not a test of a latent belief model.
    """
    lo, hi = np.maximum(0, np.asarray(prior) - 0.005), np.minimum(1, np.asarray(prior) + 0.005)
    if likelihoods is not None:
        lo *= np.maximum(0, np.asarray(likelihoods) - 0.005)
        hi *= np.minimum(1, np.asarray(likelihoods) + 0.005)
    if mask is not None:
        lo *= mask
        hi *= mask
    bounds = []
    for i in range(4):
        other = np.arange(4) != i
        lower_den = lo[i] + hi[other].sum()
        upper_den = hi[i] + lo[other].sum()
        lower = float(lo[i] / lower_den) if lower_den > 0 else 0.0
        upper = float(hi[i] / upper_den) if upper_den > 0 else (0.0 if hi[i] == 0 else 1.0)
        bounds.append([lower, upper])
    overlaps = [
        max(0, p - 0.005) <= upper + 1e-12 and min(1, p + 0.005) >= lower - 1e-12
        for p, (lower, upper) in zip(report, bounds, strict=True)
    ]
    return {
        "conservative_coordinate_bounds": bounds,
        "all_report_bins_overlap": all(overlaps),
        "interpretation": "Overlap does not prove joint consistency; non-overlap cannot be explained by nearest-percent rounding alone",
    }


def predictions(prior, likelihoods, query, assignment, parameters):
    """Conditional inputs fixed to initial reports; no inferred internal prior."""
    prior, likelihoods = np.asarray(prior), np.asarray(likelihoods)
    if np.any(prior <= 0) or np.any(likelihoods <= 0):
        raise ValueError("Point fitting requires strictly positive declared priors and forecasts")
    weight, retention, adjustment = parameters
    posterior = normalize(prior * likelihoods**weight)
    q1 = retention * posterior + (1 - retention) * independent(posterior)
    q2 = condition(q1, query, assignment)
    q3 = final_state(assignment)
    r0 = prior
    reports = []
    for q in (q1, q2, q3):
        r0 = (1 - adjustment) * r0 + adjustment * q
        reports.append(r0)
    return np.asarray(reports)


def fit(inputs, observed):
    """Simplex least squares: no independent-probability likelihood or inferred CI."""
    if not inputs:
        return {"status": "no_eligible_cases", "cases": 0, "families": {}}
    predicted = np.asarray([[predictions(*entry, p) for entry in inputs] for p in GRID])
    errors = np.mean((predicted - np.asarray(observed)) ** 2, axis=(1, 2, 3))
    families = {}
    for name, mask in (
        ("full", np.ones(len(GRID), dtype=bool)),
        ("unit_signal_weight", GRID[:, 0] == 1),
        ("retained_dependence", GRID[:, 1] == 1),
        ("immediate_reporting", GRID[:, 2] == 1),
        ("declared_model_reference", np.all(GRID == 1, axis=1)),
    ):
        loss = float(np.min(errors[mask]))
        tied = GRID[mask & np.isclose(errors, loss, rtol=0, atol=1e-12)]
        families[name] = {
            "rmse_pp": float(100 * np.sqrt(loss)),
            "minimizers": [dict(zip(PARAMETERS, map(float, p), strict=True)) for p in tied],
            "tied_grid_points": len(tied),
            "parameter_ranges": {
                key: [float(tied[:, i].min()), float(tied[:, i].max())]
                for i, key in enumerate(PARAMETERS)
            },
        }
    return {
        "status": "descriptive_point_fit",
        "cases": len(inputs),
        "reported_coordinates": len(inputs) * 12,
        "simplex_degrees_of_freedom": len(inputs) * 9,
        "families": families,
        "method": "Equal checkpoint squared error on four-state simplex; no model-selection significance, posterior or confidence interval",
    }


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
        left = next(r for r in facts if r["pair_id"] == pair and r["presentation"] == "narrative")
        right = next(r for r in facts if r["pair_id"] == pair and r["presentation"] == "facts")
        contrasts.append(
            {
                "pair_id": pair,
                "initial_joint_tv_pp": total_variation_pp(
                    left["initial_joint"], np.array(right["initial_joint"])
                ),
                "signal_forecasts_mean_absolute_gap_pp": float(
                    100
                    * np.mean(
                        np.abs(
                            np.array(left["declared_signal_likelihoods"])
                            - right["declared_signal_likelihoods"]
                        )
                    )
                ),
                "post_signal_joint_tv_pp": total_variation_pp(
                    left["joint_reports"][1], np.array(right["joint_reports"][1])
                ),
                "same_research_choice": left["query"] == right["query"],
                "later_joint_gaps_comparable": left["query"] == right["query"],
                "post_audit_joint_tv_pp": total_variation_pp(
                    left["joint_reports"][2], np.array(right["joint_reports"][2])
                )
                if left["query"] == right["query"]
                else None,
            }
        )
    return {
        "analysis_version": "narrative-analysis/0.1.0",
        "facts": facts,
        "matched_presentation_contrasts": contrasts,
        "conditional_report_model": fit(inputs, observed),
        "fit_exclusions": excluded,
        "model_parameters_are_passport_traits": False,
        "empirical_predictive_validation": False,
    }
