"""Continuous MAP refinement, local posterior curvature and world-cluster uncertainty.

The finite grid initializes the full model. All optimization uses training responses.
Intervals are a local Gaussian (Laplace/Gauss-Newton) approximation, not exact coverage.
"""

import math

import numpy as np

from epistemics.study.inference import covariance, predicted_vector

NAMES = (
    "source_frame",
    "archive_weight",
    "relationship_prior",
    "fundamentals_prior",
    "output_frame",
)
PRIOR_MEAN = np.array([0, 1, 0, 0, 0.0])


class Problem:
    def __init__(self, prepared, plan):
        self.prepared = prepared
        self.plan = plan
        self.public = {}
        self.keys = []
        for p in prepared:
            a = p["report"].assignment
            key = (a.world_id, a.variant["framing"], a.variant["history"], a.variant["lineage"])
            self.keys.append(key)
            self.public.setdefault(key, [o.trial for o in p["report"].observations])
        self.inverse = np.linalg.inv(covariance(next(iter(self.public.values())), plan))
        self.precision = 1 / np.array([1.25, 0.75, 1.5, 1, plan.output_prior_sd]) ** 2
        self.lower = np.array(
            [
                plan.source_frame_grid[0],
                plan.archive_weight_grid[0],
                plan.relationship_prior_grid[0],
                plan.fundamentals_prior_grid[0],
                -np.inf,
            ]
        )
        self.upper = np.array(
            [
                plan.source_frame_grid[-1],
                plan.archive_weight_grid[-1],
                plan.relationship_prior_grid[-1],
                plan.fundamentals_prior_grid[-1],
                np.inf,
            ]
        )

    def predictions(self, parameters):
        parameters = np.atleast_2d(parameters)
        predictions = {
            key: predicted_vector(trials, parameters[:, :4], self.plan)
            for key, trials in self.public.items()
        }
        return [
            predictions[key] + parameters[:, 4, None] * p["w"]
            for key, p in zip(self.keys, self.prepared, strict=True)
        ]

    def score(self, theta):
        pred = self.predictions(theta)
        value = 0.5 * np.sum(self.precision * (theta - PRIOR_MEAN) ** 2)
        for p, z in zip(self.prepared, pred, strict=True):
            residual = p["observed"] - z[0]
            value += 0.5 * residual @ self.inverse @ residual
        return float(value), [z[0] for z in pred]

    def derivatives(self, theta):
        candidates = [theta]
        gaps = []
        for j in range(4):
            plus, minus = theta.copy(), theta.copy()
            plus[j] = min(theta[j] + 0.005, self.upper[j])
            minus[j] = max(theta[j] - 0.005, self.lower[j])
            candidates.extend([plus, minus])
            gaps.append(plus[j] - minus[j])
        predictions = self.predictions(np.array(candidates))
        blocks = []
        objective = 0.5 * np.sum(self.precision * (theta - PRIOR_MEAN) ** 2)
        for p, z in zip(self.prepared, predictions, strict=True):
            jac = np.column_stack(
                [(z[1 + 2 * j] - z[2 + 2 * j]) / gaps[j] for j in range(4)] + [p["w"]]
            )
            residual = p["observed"] - z[0]
            h = jac.T @ self.inverse @ jac
            g = jac.T @ self.inverse @ residual
            objective += 0.5 * residual @ self.inverse @ residual
            blocks.append(
                {
                    "hessian": h,
                    "gradient": g,
                    "prediction": z[0],
                    "jacobian": jac,
                    "world": p["report"].assignment.world_id,
                }
            )
        hessian = np.diag(self.precision) + sum(b["hessian"] for b in blocks)
        gradient = sum(b["gradient"] for b in blocks) - self.precision * (theta - PRIOR_MEAN)
        return float(objective), gradient, hessian, blocks


def refine(train, heldout, grid, post, plan, *, bootstrap=100):
    index = int(np.argmax(post["weights"]))
    theta = np.array([*grid[index], post["beta_mean"][index]])
    problem = Problem(train, plan)
    converged = False
    history = []
    for iteration in range(25):
        objective, gradient, hessian, blocks = problem.derivatives(theta)
        step = np.linalg.solve(hessian, gradient)
        history.append(
            {
                "iteration": iteration,
                "negative_log_posterior_up_to_constant": objective,
                "parameters": theta.tolist(),
            }
        )
        if np.max(np.abs(np.clip(theta + step, problem.lower, problem.upper) - theta)) < 1e-4:
            converged = True
            break
        accepted = False
        for fraction in (1, 0.5, 0.25, 0.125, 0.0625):
            candidate = np.clip(theta + fraction * step, problem.lower, problem.upper)
            value, _ = problem.score(candidate)
            if value < objective:
                theta = candidate
                accepted = True
                break
        if not accepted:
            # Record a stationary or failed line search; do not silently call it identified.
            converged = np.max(np.abs(step)) < 0.002
            break
    objective, gradient, hessian, blocks = problem.derivatives(theta)
    posterior_cov = np.linalg.inv(hessian)
    sd = np.sqrt(np.diag(posterior_cov))
    bounds = np.column_stack(
        [np.maximum(theta - 1.96 * sd, problem.lower), np.minimum(theta + 1.96 * sd, problem.upper)]
    )
    boundary = np.isclose(theta, problem.lower, atol=0.002) | np.isclose(
        theta, problem.upper, atol=0.002
    )
    # Linearized whole-world bootstrap, with all arms/repeats of each world retained.
    worlds = sorted({b["world"] for b in blocks})
    sums = [
        (
            sum(b["hessian"] for b in blocks if b["world"] == w),
            sum(b["gradient"] for b in blocks if b["world"] == w),
        )
        for w in worlds
    ]
    rng = np.random.default_rng(1841)
    draws = []
    for _ in range(bootstrap):
        selected = rng.integers(0, len(worlds), len(worlds))
        h = np.diag(problem.precision) + sum(sums[i][0] for i in selected)
        g = sum(sums[i][1] for i in selected) - problem.precision * (theta - PRIOR_MEAN)
        draws.append(np.clip(theta + np.linalg.solve(h, g), problem.lower, problem.upper))
    bootstrap_bounds = np.quantile(draws, [0.025, 0.975], axis=0).T if draws else None
    held_problem = Problem(heldout, plan)
    _, _, _, held_blocks = held_problem.derivatives(theta)
    residual_quad = 0.0
    projection = np.zeros(5)
    curvature = np.zeros((5, 5))
    for p, b in zip(heldout, held_blocks, strict=True):
        residual = p["observed"] - b["prediction"]
        residual_quad += residual @ held_problem.inverse @ residual
        projection += b["gradient"]
        curvature += b["hessian"]
    total = hessian + curvature

    def logdet(x):
        return float(2 * np.log(np.diag(np.linalg.cholesky(x))).sum())

    held_score = (
        sum(p["constant"] for p in heldout)
        - 0.5 * residual_quad
        + 0.5 * projection @ np.linalg.solve(total, projection)
        - 0.5 * (logdet(total) - logdet(hessian))
    )
    predictions = {
        p["report"].assignment.assignment_id: b["prediction"]
        for p, b in zip(train + heldout, blocks + held_blocks, strict=True)
    }
    correlation = posterior_cov / (sd[:, None] * sd[None, :])
    return {
        "estimate": theta,
        "intervals": bounds,
        "bootstrap_intervals": bootstrap_bounds,
        "boundary": boundary,
        "covariance": posterior_cov,
        "correlations": correlation,
        "converged": bool(converged),
        "history": history,
        "predictions": predictions,
        "heldout_log_predictive_density": float(held_score),
        "method": "Continuous full-model MAP initialized by the training grid posterior; local Gauss-Newton/Laplace intervals. Linearized whole-world bootstrap separately reported.",
    }


def parameter_summary(result, plan, adequate, train_worlds):
    from epistemics.study.models import ParameterEstimate

    descriptions = [
        "Log prior precision-odds shift for skeptical versus neutral source profile; optimistic has the opposite shift.",
        "Weight on resolved archive-error likelihoods; 1 processes each record once. This is not a general learning rate.",
        "Prior log odds of a strong versus weak disruption relationship before the sector analogues.",
        "Prior tilt on (fundamental growth minus 12)/6; positive values favor stronger fundamentals.",
        "Common-growth logit shift for growth wording, with the opposite shift for failure wording.",
    ]
    params = {}
    x = result["estimate"]

    def sigmoid(z):
        return float(1 / (1 + math.exp(-float(z))))

    prior_f = np.exp(x[3] * np.array([-1, -1 / 3, 1 / 3, 1]))
    prior_f /= prior_f.sum()
    effects = [
        {"skeptical_vs_optimistic_prior_precision_odds_ratio": math.exp(2 * x[0])},
        {"effective_archive_cases_per_resolved_case": float(x[1])},
        {"prior_probability_strong_relationship": sigmoid(x[2])},
        {"prior_mean_fundamental_growth_pct": float(prior_f @ np.array([6, 10, 14, 18]))},
        {
            "growth_vs_failure_wording_gap_at_latent_50pct_pp": 100
            * (sigmoid(x[4]) - sigmoid(-x[4]))
        },
    ]
    limits = [
        plan.source_frame_grid,
        plan.archive_weight_grid,
        plan.relationship_prior_grid,
        plan.fundamentals_prior_grid,
    ]
    for j, name in enumerate(NAMES):
        interval = result["intervals"][j]
        width_limit = 0.8 * np.ptp(limits[j]) if j < 4 else plan.output_prior_sd
        stable = (
            result["bootstrap_intervals"] is None
            or np.ptp(result["bootstrap_intervals"][j]) < width_limit
        )
        if j < 4:
            sd = math.sqrt(result["covariance"][j, j])
            outside = 0.5 * math.erfc((x[j] - limits[j][0]) / sd / math.sqrt(2)) + 0.5 * math.erfc(
                (limits[j][-1] - x[j]) / sd / math.sqrt(2)
            )
        else:
            outside = 0.0
        resolved = (
            adequate
            and result["converged"]
            and not result["boundary"][j]
            and outside < 0.25
            and np.ptp(interval) < width_limit
            and stable
            and train_worlds >= plan.min_train_worlds_for_profile
        )
        params[name] = ParameterEstimate(
            estimate=float(x[j]),
            interval_95=tuple(map(float, interval)),
            baseline=float(PRIOR_MEAN[j]),
            boundary_mass=float(outside),
            grid_resolution=None,
            status="resolved_under_model" if resolved else "unidentified",
            explanation=descriptions[j]
            + " Local Gaussian approximation conditional on the full model. "
            + (
                "Convergence, precision and predictive adequacy gates passed."
                if resolved
                else "Convergence, boundary, precision, world count or predictive adequacy is insufficient."
            ),
            effect=effects[j],
        )
    return params
