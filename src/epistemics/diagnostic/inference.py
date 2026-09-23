"""Small competing report-generating models, never recovered internal beliefs."""

import itertools

import numpy as np

from epistemics.diagnostic.battery import association
from epistemics.investigation.inference import report_log_likelihood

GRID = np.array(
    list(itertools.product(np.linspace(0, 1.5, 7), np.linspace(0, 1, 5), np.linspace(0, 1, 5)))
)
SD = 0.25
PARAMETERS = ("association_scale", "propagation_fraction", "report_rate")
FAMILIES = {
    "full": np.ones(len(GRID), dtype=bool),
    "association_only": (GRID[:, 1] == 1) & (GRID[:, 2] == 1),
    "selective_propagation": GRID[:, 2] == 1,
    "report_smoothing": GRID[:, 1] == 1,
}


def predictions(assignments, parameters=GRID):
    parameters = np.atleast_2d(parameters)
    beta, rho, alpha = parameters.T
    rows = []
    for a in assignments:
        difference = beta * association(a)
        conditional = 0.5 + (1 if a.growth_outcome else -1) * difference
        target = 0.5 + rho * (conditional - 0.5)
        first = 0.5 + alpha * (target - 0.5)
        repeat = first + alpha * (target - first)
        resolved = repeat + alpha * (float(a.auxiliary_outcome) - repeat)
        rows.append(np.stack([0.5 + difference, 0.5 - difference, first, repeat, resolved], axis=1))
    return np.concatenate(rows, axis=1)


def observed(cases, assignments):
    result = []
    for a in assignments:
        rows = cases[a.assignment_id]
        first = rows[0].answer
        result.extend([first.auxiliary_if_growth, first.auxiliary_if_no_growth])
        result.extend(row.answer.auxiliary_probability for row in rows[1:])
    return np.array(result)


def fit(values, assignments):
    values = np.asarray(values)
    means = predictions(assignments)
    if values.shape != means.shape[1:] or not np.isfinite(values).all():
        raise ValueError("Expected five fitted reports per case")
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
            "propagation_identifiable_in_selected_model": bool(
                GRID[best, 0] > 0 and GRID[best, 2] > 0
            ),
            "observations": len(values),
        }
    return output


def analyze(cases, assignments):
    rows = []
    for a in assignments:
        answers = [o.answer for o in cases[a.assignment_id]]
        first = answers[0]
        conditional = (
            first.auxiliary_if_growth if a.growth_outcome else first.auxiliary_if_no_growth
        )
        mixture = (
            first.growth_probability * first.auxiliary_if_growth
            + (1 - first.growth_probability) * first.auxiliary_if_no_growth
        )
        rows.append(
            {
                "assignment_id": a.assignment_id,
                "pair_id": a.pair_id,
                "target": a.target,
                "relationship": a.relationship,
                "conditional_spread_pp": 100
                * (first.auxiliary_if_growth - first.auxiliary_if_no_growth),
                "initial_mixture_gap_pp": 100 * (first.auxiliary_probability - mixture),
                "conditional_transfer_gap_pp": 100
                * (answers[1].auxiliary_probability - conditional),
                "repeat_change_pp": 100
                * (answers[2].auxiliary_probability - answers[1].auxiliary_probability),
                "direct_resolution_error_pp": 100
                * abs(answers[3].auxiliary_probability - a.auxiliary_outcome),
                "growth_resolution_errors_pp": [
                    100 * abs(v.growth_probability - a.growth_outcome) for v in answers[1:]
                ],
                "initial_auxiliary_probability": first.auxiliary_probability,
            }
        )
    fits = fit(observed(cases, assignments), assignments)
    return {
        "analysis_version": "auxiliary-diagnostic-analysis/0.1.0",
        "facts": rows,
        "conditional_model_fits": fits,
        "baseline_max_deviation_from_model_pp": max(
            100 * abs(o.answer.auxiliary_probability - 0.5)
            for obs in cases.values()
            for o in obs[:1]
        ),
        "model_parameters_are_passport_traits": False,
        "empirical_predictive_validation": False,
    }
