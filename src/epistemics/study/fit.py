"""Precommitted joint working-likelihood fits, train-only posteriors and held-out prediction."""

import json
import math
from pathlib import Path

import numpy as np

from epistemics.discovery.inference import extract
from epistemics.study.design import digest, episode, load_manifest
from epistemics.study.inference import (
    PARAMETERS,
    channels,
    covariance,
    logsumexp,
    observed_vector,
    parameter_grid,
    predicted_vector,
    wording_vector,
)
from epistemics.study.models import EpisodeReport, ParameterEstimate, StudyProfile

BASELINES = np.array([0, 1, 0, 0])
MODEL_FREE = {
    "baseline": (),
    "business": (2, 3),
    "archive_learning": (1, 2, 3),
    "source_impression": (0, 1, 2, 3),
    "response_wording": (1, 2, 3, 4),
    "full": (0, 1, 2, 3, 4),
}
LIMITATIONS = [
    "Parameters describe task-conditional responses for this agent configuration, not private beliefs or neural mechanisms.",
    "One authored business mechanism; held-out worlds test new numerical cases, not structural transfer.",
    "The model assumes finite source bias/noise grids, shared uncertainty, and a fixed report gain of one. Business priors vary but do not span all possible explanations.",
    "The likelihood is a correlated Gaussian working model on clipped probability logits and growth quantiles. It is not an exact likelihood for rounded or endpoint reports.",
    "Full-model intervals use a local Gaussian approximation after continuous MAP refinement. They condition on the specified bounds, priors and fixed observation covariance. Multimodal or misspecified models can invalidate these intervals.",
    "Model comparison uses the separate coarse-grid candidates. Full-model refinement is initialized from the best training grid point, not an exhaustive continuous global search. Cluster uncertainty uses a linearized whole-world bootstrap.",
    "Source framing is a precision-prior effect. Archive weight applies only to resolved historical errors, not a general learning rate.",
    "Wording is modeled at the report stage but may also change deliberation. Input/output separation is conditional on this model.",
    "Negative-evidence weighting, confirmation bias, memory effects and risk preferences are not estimated in this version.",
    "Richer probes may affect responses. Cross-company source learning and minimal-probe transfer remain unvalidated.",
    "Context separation and agent identity are operator assertions. Local filesystem restrictions are not OS-level respondent isolation.",
]


def load_reports(directory):
    directory = Path(directory)
    manifest, manifest_hash = load_manifest(directory)
    hashes = json.loads((directory / "report-hashes.json").read_text())
    expected = {f"{a.assignment_id}.json" for a in manifest.assignments}
    if set(hashes) != expected:
        raise ValueError("Missing or extra planned reports")
    reports = []
    for assignment in manifest.assignments:
        data = (directory / "reports" / f"{assignment.assignment_id}.json").read_bytes()
        if digest(data) != hashes[f"{assignment.assignment_id}.json"]:
            raise ValueError("Report bytes do not match the recorded hash")
        report = EpisodeReport.model_validate_json(data)
        if (
            report.assignment != assignment
            or report.study_id != manifest.study_id
            or report.manifest_sha256 != manifest_hash
            or report.agent != manifest.agent
            or report.response_origin != manifest.response_origin
            or report.implementation_sha256 != manifest.implementation_sha256
        ):
            raise ValueError("Report does not belong to this frozen study/configuration")
        generated = episode(assignment)
        if [o.trial.model_dump(mode="json") for o in report.observations] != [
            r["trial"] for r in generated
        ] or report.private_case.model_dump(mode="json") != generated[0]["truth"]:
            raise ValueError("Report materials do not match the precommitted assignment")
        # Revalidate trial-dependent fields even for reports supplied outside the collector.
        for o in report.observations:
            a, t = o.answer, o.trial
            if (
                set(a.source_accuracy) != set(t.source_probe_ids)
                or (a.conditional_growth_probability is not None) != t.conditional_probe
                or set(a.extracted_values) != set(t.extraction_keys)
                or len(set(a.evidence_ids)) != len(a.evidence_ids)
                or not set(a.evidence_ids) <= {d.document_id for d in t.documents}
            ):
                raise ValueError("Report contains invalid probe responses")
        reports.append(report)
    return manifest, manifest_hash, reports, hashes


def prepare(reports, plan):
    grid = parameter_grid(plan)
    trials = [o.trial for o in reports[0].observations]
    cov = covariance(trials, plan)
    inverse = np.linalg.inv(cov)
    logdet = 2 * np.log(np.diag(np.linalg.cholesky(cov))).sum()
    constant = -0.5 * (len(cov) * math.log(2 * math.pi) + logdet)
    cache = {}
    prepared = []
    for report in reports:
        public = [o.trial for o in report.observations]
        # Complementary wording and repeats share inference predictions, never responses.
        key = (
            report.assignment.world_id,
            report.assignment.variant["framing"],
            report.assignment.variant["history"],
            report.assignment.variant["lineage"],
        )
        if key not in cache:
            cache[key] = predicted_vector(public, grid, plan)
        pred = cache[key]
        observed = observed_vector(report.observations, plan)
        w = wording_vector(public)
        residual = observed - pred
        whitened = residual @ inverse
        prepared.append(
            {
                "report": report,
                "pred": pred,
                "observed": observed,
                "w": w,
                "a": np.sum(whitened * residual, axis=1),
                "b": whitened @ w,
                "c": float(w @ inverse @ w),
                "constant": constant,
                "scales": np.sqrt(np.diag(cov)),
            }
        )
    return grid, prepared


def aggregate(prepared):
    return (
        sum(p["a"] for p in prepared),
        sum(p["b"] for p in prepared),
        sum(p["c"] for p in prepared),
        sum(p["constant"] for p in prepared),
    )


def posterior(grid, stats, plan, name="full"):
    a, b, c, constant = stats
    free = MODEL_FREE[name]
    mask = np.ones(len(grid), dtype=bool)
    for index, baseline in enumerate(BASELINES):
        if index not in free:
            mask &= grid[:, index] == baseline
    # Discrete, explicitly normalized priors on each permitted grid.
    prior = (
        -0.5 * (grid[:, 0] / 1.25) ** 2
        - 0.5 * ((grid[:, 1] - 1) / 0.75) ** 2
        - 0.5 * (grid[:, 2] / 1.5) ** 2
        - 0.5 * grid[:, 3] ** 2
    )
    prior[~mask] = -np.inf
    prior -= logsumexp(prior)
    if 4 in free:
        variance = 1 / (c + 1 / plan.output_prior_sd**2)
        mean = b * variance
        ll = constant - 0.5 * (a - b * mean) - 0.5 * math.log1p(c * plan.output_prior_sd**2)
    else:
        mean, variance = np.zeros(len(grid)), 0.0
        ll = constant - 0.5 * a
    logweights = prior + ll
    evidence = float(logsumexp(logweights))
    weights = np.exp(logweights - evidence)
    return {
        "weights": weights,
        "beta_mean": mean,
        "beta_variance": variance,
        "log_evidence": evidence,
    }


def predictive_score(post, stats):
    a, b, c, constant = stats
    mean, variance = post["beta_mean"], post["beta_variance"]
    effective_variance = variance / (1 + c * variance)
    ll = (
        constant
        - 0.5 * (a - 2 * mean * b + mean**2 * c - effective_variance * (b - c * mean) ** 2)
        - 0.5 * math.log1p(c * variance)
    )
    with np.errstate(divide="ignore"):
        return float(logsumexp(np.log(post["weights"]) + ll))


def weighted_interval(values, weights):
    order = np.argsort(values)
    ordered, cumulative = values[order], np.cumsum(weights[order])
    return tuple(
        float(ordered[min(np.searchsorted(cumulative, q), len(ordered) - 1)])
        for q in (0.025, 0.975)
    )


def probability(z):
    return 1 / (1 + np.exp(-np.clip(z, -700, 700)))


def summarize_parameters(grid, post, adequate, n_train, plan):
    weights = post["weights"]
    all_means = np.column_stack([grid, post["beta_mean"]])
    mean = weights @ all_means
    rng = np.random.default_rng(91832)
    indices = rng.choice(len(grid), size=30000, p=weights)
    beta_draws = post["beta_mean"][indices] + rng.normal(
        0, math.sqrt(post["beta_variance"]), len(indices)
    )
    result = {}
    descriptions = [
        "Log prior odds shift toward a precise source for skeptical versus neutral profile; optimistic uses the opposite shift.",
        "Power on resolved archive-error likelihoods; 1 uses each archived measurement once, 0 ignores the archive.",
        "Log prior odds of the strong versus weak disruption-to-renewal relationship, before sector analogues.",
        "Prior tilt on (fundamental growth minus 12)/6; positive values favor higher fundamental growth.",
        "Logit shift for growth-worded reporting; failure wording has the opposite shift after complement conversion.",
    ]
    for j, name in enumerate((*PARAMETERS, "output_frame")):
        if j < 4:
            interval = weighted_interval(grid[:, j], weights)
            boundary = float(
                weights[(grid[:, j] == grid[:, j].min()) | (grid[:, j] == grid[:, j].max())].sum()
            )
            narrow = interval[1] - interval[0] < 0.8 * np.ptp(grid[:, j])
        else:
            interval = tuple(map(float, np.quantile(beta_draws, [0.025, 0.975])))
            boundary = 0.0
            narrow = interval[1] - interval[0] < plan.output_prior_sd
        resolved = (
            adequate and n_train >= plan.min_train_worlds_for_profile and boundary < 0.25 and narrow
        )
        effect = {}
        if j == 0:
            effect = {
                "skeptical_vs_optimistic_prior_precision_odds_ratio": float(math.exp(2 * mean[j]))
            }
        if j == 1:
            effect = {"effective_archive_cases_per_resolved_case": float(mean[j])}
        if j == 2:
            effect = {
                "prior_probability_strong_relationship": float(weights @ probability(grid[:, j]))
            }
        if j == 3:
            prior = np.exp(grid[:, j, None] * np.array([-1, -1 / 3, 1 / 3, 1]))
            prior /= prior.sum(axis=1, keepdims=True)
            effect = {
                "prior_mean_fundamental_growth_pct": float(
                    weights @ (prior @ np.array([6, 10, 14, 18]))
                )
            }
        if j == 4:
            effect = {
                "growth_vs_failure_wording_gap_at_latent_50pct_pp": float(
                    100 * np.mean(probability(beta_draws) - probability(-beta_draws))
                )
            }
        result[name] = ParameterEstimate(
            estimate=float(mean[j]),
            interval_95=interval,
            baseline=float(BASELINES[j]) if j < 4 else 0,
            boundary_mass=boundary,
            grid_resolution=float(np.min(np.diff(np.unique(grid[:, j])))) if j < 4 else None,
            status="resolved_under_model" if resolved else "unidentified",
            explanation=descriptions[j]
            + (
                " Discrete-grid interval; a collapsed interval means grid resolution is exhausted, not zero uncertainty between nodes."
                if j < 4
                else ""
            )
            + (
                " Conditional on this observer and observation model."
                if resolved
                else " Insufficient precision, boundary support, number of worlds, or predictive adequacy."
            ),
            effect=effect,
        )
    centered = all_means - mean
    cov = (centered * weights[:, None]).T @ centered
    cov[-1, -1] += post["beta_variance"]
    scale = np.sqrt(np.diag(cov))
    correlation = cov / np.maximum(scale[:, None] * scale[None, :], 1e-30)
    return result, correlation


def contrasts(reports):
    """Paired public-response contrasts, averaged within world before across-world summaries."""

    def value(report, kind):
        if kind == "source_profile":
            return report.observations[0].answer.source_accuracy["beacon"]
        if kind == "archive_length":
            return report.observations[1].answer.source_accuracy["beacon"]
        answer = report.observations[-1].answer
        return (
            answer.target_probability
            if report.assignment.variant["response"] == "growth"
            else 1 - answer.target_probability
        )

    results = {}
    for kind, factor, positive in [
        ("source_profile", "framing", "skeptical"),
        ("archive_length", "history", "long"),
        ("response_wording", "response", "growth"),
    ]:
        pairs = {}
        for report in reports:
            a = report.assignment
            key = (
                a.world_id,
                a.replicate,
                tuple(sorted((k, v) for k, v in a.variant.items() if k != factor)),
            )
            pairs.setdefault(key, {})[a.variant[factor] == positive] = value(report, kind)
        worlds = {}
        for key, pair in pairs.items():
            if set(pair) != {False, True}:
                raise ValueError("Incomplete matched comparison")
            worlds.setdefault(key[0], []).append(100 * (pair[True] - pair[False]))
        diffs = np.array([np.mean(v) for v in worlds.values()])
        rng = np.random.default_rng(9876)
        samples = np.mean(rng.choice(diffs, size=(2000, len(diffs))), axis=1)
        results[kind] = {
            "mean_difference_pp": float(diffs.mean()),
            "world_bootstrap_interval_95_pp": list(
                map(float, np.quantile(samples, [0.025, 0.975]))
            ),
            "independent_worlds": len(diffs),
            "paired_comparisons": len(pairs),
            "interpretation": "Descriptive matched contrast; archive length has no universally positive expected sign.",
        }
    return results


def fit_reports(manifest, manifest_hash, reports, hashes, *, bootstrap=100, prepared_data=None):
    grid, prepared = (
        prepared_data if prepared_data is not None else prepare(reports, manifest.analysis_plan)
    )
    train = [p for p in prepared if p["report"].assignment.split == "train"]
    held = [p for p in prepared if p["report"].assignment.split == "heldout"]
    train_worlds = sorted({p["report"].assignment.world_id for p in train})
    held_worlds = {p["report"].assignment.world_id for p in held}
    train_stats, held_stats = aggregate(train), aggregate(held)
    fits = {name: posterior(grid, train_stats, manifest.analysis_plan, name) for name in MODEL_FREE}
    evidences = np.array([f["log_evidence"] for f in fits.values()])
    model_weights = np.exp(evidences - logsumexp(evidences))
    comparisons = {
        name: {
            "training_log_evidence": f["log_evidence"],
            "training_model_probability_equal_model_priors": float(weight),
            "heldout_joint_log_predictive_density": predictive_score(f, held_stats),
            "free_parameters": [(*PARAMETERS, "output_frame")[j] for j in MODEL_FREE[name]],
        }
        for (name, f), weight in zip(fits.items(), model_weights, strict=True)
    }
    post = fits["full"]
    from epistemics.study.refinement import parameter_summary, refine

    refined = refine(train, held, grid, post, manifest.analysis_plan, bootstrap=bootstrap)
    predictions, errors = [], []
    extraction, decision_agreement, endpoint_count = [], [], 0
    channel_errors = {}
    for p in prepared:
        report = p["report"]
        mean = refined["predictions"][report.assignment.assignment_id]
        if report.assignment.split == "heldout":
            errors.extend(((p["observed"] - mean) / p["scales"]) ** 2)
        for i, (step, label) in enumerate(channels([o.trial for o in report.observations])):
            is_quantile = label.startswith("p")
            actual = (
                float(p["observed"][i]) if is_quantile else float(probability(p["observed"][i]))
            )
            predicted = float(mean[i]) if is_quantile else float(probability(mean[i]))
            if report.assignment.split == "heldout":
                channel_errors.setdefault(label.split(":")[0], []).append((predicted - actual) ** 2)
            predictions.append(
                {
                    "assignment_id": report.assignment.assignment_id,
                    "split": report.assignment.split,
                    "step": step,
                    "channel": label,
                    "observed_transformed_back": actual,
                    "prediction_transformed_back": predicted,
                }
            )
        for o in report.observations:
            a, t = o.answer, o.trial
            growth = (
                a.target_probability
                if t.target_event == "growth_above_12"
                else 1 - a.target_probability
            )
            decision_agreement.append((a.decision == "invest") == (3 * growth - 1 > 1e-12))
            values, _, _ = extract(t)
            extraction.extend(
                abs(v - values["renewal" if k == "renewal_estimate_pct" else "model"])
                for k, v in a.extracted_values.items()
            )
            probs = [a.target_probability, *a.source_accuracy.values()]
            if a.conditional_growth_probability is not None:
                probs.append(a.conditional_growth_probability)
            endpoint_count += sum(
                x <= manifest.analysis_plan.probability_clip
                or x >= 1 - manifest.analysis_plan.probability_clip
                for x in probs
            )
    rmse = float(np.sqrt(np.mean(errors)))
    adequate = rmse <= manifest.analysis_plan.adequacy_max_standardized_rmse
    extraction_ok = (
        float(np.mean(extraction)) <= manifest.analysis_plan.max_mean_extraction_error_pp
    )
    grid_params, _ = summarize_parameters(
        grid, post, adequate, len(train_worlds), manifest.analysis_plan
    )
    params = parameter_summary(
        refined, manifest.analysis_plan, adequate and extraction_ok, len(train_worlds)
    )
    correlations = refined["correlations"]
    # Resample whole training worlds, keeping all matched arms and repeated contexts together.
    grouped = [
        aggregate([p for p in train if p["report"].assignment.world_id == world])
        for world in train_worlds
    ]
    rng = np.random.default_rng(51039)
    estimates = []
    for _ in range(bootstrap):
        selected = rng.integers(0, len(grouped), len(grouped))
        stats = tuple(sum(grouped[i][j] for i in selected) for j in range(4))
        boot = posterior(grid, stats, manifest.analysis_plan)
        estimates.append([*(boot["weights"] @ grid), float(boot["weights"] @ boot["beta_mean"])])
    bootstrap_intervals = (
        {
            name: list(map(float, np.quantile(np.array(estimates)[:, j], [0.025, 0.975])))
            for j, name in enumerate((*PARAMETERS, "output_frame"))
        }
        if estimates
        else {}
    )
    refined_bootstrap = (
        {
            name: refined["bootstrap_intervals"][j].tolist()
            for j, name in enumerate((*PARAMETERS, "output_frame"))
        }
        if refined["bootstrap_intervals"] is not None
        else {}
    )
    final_probs, outcomes = [], []
    for report in reports:
        a, t = report.observations[-1].answer, report.observations[-1].trial
        final_probs.append(
            a.target_probability
            if t.target_event == "growth_above_12"
            else 1 - a.target_probability
        )
        outcomes.append(float(report.private_case.realized_growth_pct > 12))
    return StudyProfile(
        study_id=manifest.study_id,
        manifest_sha256=manifest_hash,
        implementation_sha256=manifest.implementation_sha256,
        response_origin=manifest.response_origin,
        agent=manifest.agent,
        report_hashes=hashes,
        train_worlds=len(train_worlds),
        heldout_worlds=len(held_worlds),
        parameters=params,
        model_comparisons=comparisons,
        diagnostics={
            "heldout_standardized_rmse": rmse,
            "adequacy_threshold": manifest.analysis_plan.adequacy_max_standardized_rmse,
            "predictive_adequacy_passed": adequate,
            "extraction_checks_passed": extraction_ok,
            "heldout_rmse_by_channel": {
                k: float(np.sqrt(np.mean(v))) for k, v in channel_errors.items()
            },
            "parameter_order": [*PARAMETERS, "output_frame"],
            "posterior_parameter_correlations": correlations.tolist(),
            "world_bootstrap_intervals_95": refined_bootstrap,
            "world_bootstrap_method": "Linearized continuous MAP refit after resampling whole training worlds",
            "coarse_grid_world_bootstrap_intervals_95": bootstrap_intervals,
            "coarse_grid_parameters": {k: v.model_dump() for k, v in grid_params.items()},
            "continuous_refinement_converged": refined["converged"],
            "continuous_refinement_history": refined["history"],
            "continuous_full_model_heldout_log_predictive_density": refined[
                "heldout_log_predictive_density"
            ],
            "bootstrap_replicates": bootstrap,
            "clipped_probability_reports": endpoint_count,
            "mean_extraction_error_pp": float(np.mean(extraction)),
            "decision_report_agreement": float(np.mean(decision_agreement)),
            "final_brier_descriptive": float(np.mean((np.array(final_probs) - outcomes) ** 2)),
            "independent_outcomes": len(train_worlds) + len(held_worlds),
            "preferred_model_by_training_evidence": max(
                fits, key=lambda k: fits[k]["log_evidence"]
            ),
            "parameter_interval_method": refined["method"],
            "recovery_attestation": "Not embedded: review the separately versioned recovery artifact before interpreting agent parameters.",
        },
        experimental_contrasts=contrasts(reports),
        predictions=predictions,
        limitations=LIMITATIONS,
    )


def fit_directory(directory):
    manifest, manifest_hash, reports, hashes = load_reports(directory)
    profile = fit_reports(manifest, manifest_hash, reports, hashes)
    path = Path(directory) / "profile.json"
    data = (profile.model_dump_json(indent=2) + "\n").encode()
    path.write_bytes(data)
    path.with_suffix(".sha256").write_text(digest(data) + "\n")
    write_summary(profile, path.with_suffix(".md"))
    return profile


def write_summary(profile, path):
    lines = [
        "# Discovery study parameter profile",
        "",
        f"Response origin: **{profile.response_origin}**. "
        f"Training worlds: {profile.train_worlds}; held-out worlds: {profile.heldout_worlds}.",
        "",
        "These estimates are conditional on the declared inference and observation models. "
        "A resolved estimate is not evidence of a nonzero bias unless its interval and matched contrast support that interpretation.",
        "",
        "| Parameter | Estimate | Conditional 95% interval | Status |",
        "| --- | ---: | --- | --- |",
    ]
    for name, p in profile.parameters.items():
        lines.append(
            f"| {name} | {p.estimate:.3f} | [{p.interval_95[0]:.3f}, {p.interval_95[1]:.3f}] | {p.status} |"
        )
    lines += [
        "",
        "## Held-out validation",
        "",
        f"Standardized RMSE: {profile.diagnostics['heldout_standardized_rmse']:.3f}. "
        f"Adequacy gate passed: {profile.diagnostics['predictive_adequacy_passed']}.",
        "",
        "| Model | Training model probability | Held-out joint log predictive density |",
        "| --- | ---: | ---: |",
    ]
    for name, model in profile.model_comparisons.items():
        lines.append(
            f"| {name} | {model['training_model_probability_equal_model_priors']:.3f} | {model['heldout_joint_log_predictive_density']:.1f} |"
        )
    lines += ["", "## Matched contrasts", ""]
    for name, c in profile.experimental_contrasts.items():
        lines.append(
            f"- {name}: {c['mean_difference_pp']:.2f} percentage points; "
            f"world-bootstrap 95% interval {c['world_bootstrap_interval_95_pp']}."
        )
    lines += [
        "",
        "## Scope and limitations",
        "",
        *[f"- {v}" for v in profile.limitations],
        "",
        "Full JSON includes practical effect sizes, parameter correlations, cluster bootstrap intervals, "
        "channel-level prediction errors, case predictions and exact episode-report hashes.",
        "",
    ]
    Path(path).write_text("\n".join(lines))
