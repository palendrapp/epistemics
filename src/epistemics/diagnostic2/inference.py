"""Separate relationship extraction, signal interpretation and auxiliary expression."""

import itertools

import numpy as np

from epistemics.diagnostic2.battery import association
from epistemics.investigation.inference import report_log_likelihood

PARAMETERS = (
    "summary_association_scale",
    "records_association_scale",
    "signal_weight",
    "propagation_fraction",
    "auxiliary_report_rate",
)
GRID = np.array(
    list(
        itertools.product(
            np.linspace(0, 1.5, 7),
            np.linspace(0, 1.5, 7),
            np.linspace(0, 2, 5),
            np.linspace(0, 1, 5),
            np.linspace(0, 1, 5),
        )
    )
)
SD = 0.25
FAMILIES = {
    "full": np.ones(len(GRID), dtype=bool),
    "shared_representation": GRID[:, 0] == GRID[:, 1],
    "full_propagation": GRID[:, 3] == 1,
    "immediate_auxiliary_report": GRID[:, 4] == 1,
}


def predictions(assignments, parameters=GRID):
    parameters = np.atleast_2d(parameters)
    summary, records, weight, rho, alpha = parameters.T
    rows = []
    for a in assignments:
        difference = (summary if a.presentation == "summary" else records) * association(a)
        q = (
            np.full(len(parameters), float(a.growth_outcome))
            if a.evidence == "audit"
            else 1 / (1 + np.exp(-(1 if a.signal_positive else -1) * weight * np.log(3)))
        )
        mixture = 0.5 + (2 * q - 1) * difference
        target = 0.5 + rho * (mixture - 0.5)
        first = 0.5 + alpha * (target - 0.5)
        repeat = first + alpha * (target - first)
        resolved = repeat + alpha * (float(a.auxiliary_outcome) - repeat)
        rows.append(
            np.stack(
                [0.5 + difference, 0.5 - difference, q, first, q, repeat, resolved],
                axis=1,
            )
        )
    return np.concatenate(rows, axis=1)


def observed(cases, assignments):
    result = []
    for a in assignments:
        initial, first, repeat, final = [o.answer for o in cases[a.assignment_id]]
        result.extend(
            [
                initial.auxiliary_if_growth,
                initial.auxiliary_if_no_growth,
                first.growth_probability,
                first.auxiliary_probability,
                repeat.growth_probability,
                repeat.auxiliary_probability,
                final.auxiliary_probability,
            ]
        )
    return np.array(result)


def fit(values, assignments, *, means=None):
    values = np.asarray(values)
    means = predictions(assignments) if means is None else means
    if (
        values.shape != (len(assignments) * 7,)
        or not np.isfinite(values).all()
        or np.any((values < 0) | (values > 1))
    ):
        raise ValueError("Expected seven fitted probabilities per case")
    ll = report_log_likelihood(values, means, sd=SD).sum(axis=1)
    output = {}
    for family, mask in FAMILIES.items():
        candidates = np.flatnonzero(mask)
        best = int(candidates[np.argmax(ll[mask])])
        tied = candidates[np.isclose(ll[mask], ll[best], rtol=0, atol=1e-8)]
        output[family] = {
            "parameters": dict(zip(PARAMETERS, GRID[best].tolist(), strict=True)),
            "log_likelihood": float(ll[best]),
            "rmse_pp": float(np.sqrt(np.mean((values - means[best]) ** 2)) * 100),
            "tied_parameter_sets": len(tied),
            "parameters_varying_across_grid_ties": [
                p for i, p in enumerate(PARAMETERS) if len(set(GRID[tied, i])) > 1
            ],
            "propagation_identifiable_in_selected_model": bool(
                (GRID[best, :2] > 0).any() and GRID[best, 4] > 0
            ),
            "observations": len(values),
        }
    return output


def analyze(cases, assignments):
    facts = []
    for a in assignments:
        initial, first, repeat, final = [o.answer for o in cases[a.assignment_id]]

        def bridge(growth, initial=initial):
            return (
                growth * initial.auxiliary_if_growth + (1 - growth) * initial.auxiliary_if_no_growth
            )

        facts.append(
            {
                "assignment_id": a.assignment_id,
                "quartet_id": a.quartet_id,
                "target": a.target,
                "relationship": a.relationship,
                "presentation": a.presentation,
                "evidence": a.evidence,
                "conditional_spread_pp": 100
                * (initial.auxiliary_if_growth - initial.auxiliary_if_no_growth),
                "initial_mixture_gap_pp": 100
                * (initial.auxiliary_probability - bridge(initial.growth_probability)),
                "growth_after_evidence": first.growth_probability,
                "auxiliary_after_evidence": first.auxiliary_probability,
                "own_conditional_mixture_after_evidence": bridge(first.growth_probability),
                "conditional_mixture_gap_pp": 100
                * (first.auxiliary_probability - bridge(first.growth_probability)),
                "repeat_mixture_gap_pp": 100
                * (repeat.auxiliary_probability - bridge(repeat.growth_probability)),
                "repeat_growth_change_pp": 100
                * (repeat.growth_probability - first.growth_probability),
                "repeat_auxiliary_change_pp": 100
                * (repeat.auxiliary_probability - first.auxiliary_probability),
                "direct_auxiliary_resolution_error_pp": 100
                * abs(final.auxiliary_probability - a.auxiliary_outcome),
                "direct_growth_resolution_error_pp": 100
                * abs(final.growth_probability - a.growth_outcome),
                "early_growth_audit_errors_pp": [
                    100 * abs(v.growth_probability - a.growth_outcome) for v in (first, repeat)
                ]
                if a.evidence == "audit"
                else None,
            }
        )
    contrasts = []
    for quartet in dict.fromkeys(a.quartet_id for a in assignments):
        rows = [r for r in facts if r["quartet_id"] == quartet]
        for evidence in ("audit", "signal"):
            summary = next(
                r for r in rows if r["presentation"] == "summary" and r["evidence"] == evidence
            )
            records = next(
                r for r in rows if r["presentation"] == "records" and r["evidence"] == evidence
            )
            contrasts.append(
                {
                    "quartet_id": quartet,
                    "target": summary["target"],
                    "relationship": summary["relationship"],
                    "evidence": evidence,
                    "records_minus_summary_conditional_spread_pp": (
                        records["conditional_spread_pp"] - summary["conditional_spread_pp"]
                    ),
                    "records_minus_summary_absolute_mixture_gap_pp": (
                        abs(records["conditional_mixture_gap_pp"])
                        - abs(summary["conditional_mixture_gap_pp"])
                    ),
                }
            )
    return {
        "analysis_version": "auxiliary-diagnostic-analysis/0.2.0",
        "facts": facts,
        "matched_presentation_contrasts": contrasts,
        "conditional_model_fits": fit(observed(cases, assignments), assignments),
        "baseline_max_deviation_from_model_pp": {
            name: max(100 * abs(getattr(rows[0].answer, name) - 0.5) for rows in cases.values())
            for name in ("growth_probability", "auxiliary_probability")
        },
        "model_parameters_are_passport_traits": False,
        "empirical_predictive_validation": False,
        "interpretation": (
            "Mixture gaps use the respondent's own reported conditionals and growth forecast. "
            "They assume those conditionals retain their meaning and the stated signal conditional "
            "independence is understood. They do not independently diagnose a bias or causal model."
        ),
    }
