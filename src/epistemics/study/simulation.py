"""Synthetic validation only; never present these responses as a real agent study."""

import json
from pathlib import Path

import numpy as np

from epistemics.company.models import GrowthQuantiles
from epistemics.discovery.inference import extract
from epistemics.discovery.models import DiscoveryAnswer
from epistemics.models import AgentDescriptor
from epistemics.service import now
from epistemics.study.design import create_manifest, digest, episode, write_manifest
from epistemics.study.fit import fit_reports, prepare, probability
from epistemics.study.inference import covariance, observed_vector, predicted_vector, wording_vector
from epistemics.study.models import EpisodeReport, StudyObservation, StudyTrial
from epistemics.study.service import StudyService, export_reports


def synthetic_agent():
    return AgentDescriptor(
        agent_id="synthetic:study-recovery",
        model="conditional-joint-observer",
        model_version="0.4.0",
        configuration_sha256="0" * 64,
        context_policy="continuous",
    )


def answers_from_vector(trials, vector):
    position = 0
    answers = []
    for t in trials:
        growth = float(probability(vector[position]))
        position += 1
        sources = {
            sid: float(probability(vector[position + i]))
            for i, sid in enumerate(t.source_probe_ids)
        }
        position += len(sources)
        conditional = float(probability(vector[position])) if t.conditional_probe else None
        position += int(t.conditional_probe)
        # The simulation records ordered quantiles, just as the public response contract requires.
        quantiles = sorted(map(float, vector[position : position + 3]))
        position += 3
        values, _, _ = extract(t)
        answers.append(
            DiscoveryAnswer(
                target_probability=round(
                    growth if t.target_event == "growth_above_12" else 1 - growth, 4
                ),
                growth_quantiles_pct=GrowthQuantiles(
                    p10=quantiles[0], p50=quantiles[1], p90=quantiles[2]
                ),
                decision="invest" if growth > 1 / 3 else "hold",
                evidence_ids=[d.document_id for d in t.documents],
                source_accuracy={k: round(v, 4) for k, v in sources.items()},
                conditional_growth_probability=round(conditional, 4)
                if conditional is not None
                else None,
                extracted_values={
                    k: values["renewal" if k == "renewal_estimate_pct" else "model"]
                    for k in t.extraction_keys
                },
            )
        )
    return answers


def make_reports(manifest, params=(0, 1, 0, 0), beta=0, noise_seed=1, noise=True):
    rng = np.random.default_rng(noise_seed)
    reports = []
    cache = {}
    manifest_hash = digest((manifest.model_dump_json(indent=2) + "\n").encode())
    for assignment in manifest.assignments:
        records = episode(assignment)
        trials = [StudyTrial.model_validate(r["trial"]) for r in records]
        key = (assignment.world_id, assignment.variant["framing"], assignment.variant["history"])
        if key not in cache:
            cache[key] = predicted_vector(trials, np.array([params]), manifest.analysis_plan)[0]
        vector = cache[key] + beta * wording_vector(trials)
        if noise:
            vector += rng.multivariate_normal(
                np.zeros(len(vector)), covariance(trials, manifest.analysis_plan)
            )
        answers = answers_from_vector(trials, vector)
        reports.append(
            EpisodeReport(
                study_id=manifest.study_id,
                manifest_sha256=manifest_hash,
                implementation_sha256=manifest.implementation_sha256,
                agent=manifest.agent,
                response_origin="synthetic",
                assignment=assignment,
                private_case=records[0]["truth"],
                observations=[
                    StudyObservation(trial=t, answer=a, answered_at=now())
                    for t, a in zip(trials, answers, strict=True)
                ],
                completed_at=now(),
            )
        )
    return reports


def simulate_study(
    directory, *, worlds=4, replicates=1, seed=1909, params=(1, 0.5, -1, 0), beta=0.4
):
    manifest = create_manifest(
        synthetic_agent(),
        worlds=worlds,
        replicates=replicates,
        seed=seed,
        response_origin="synthetic",
    )
    write_manifest(directory, manifest)
    reports = make_reports(manifest, params, beta, seed)
    for report in reports:
        service = StudyService(directory, report.assignment.assignment_id)
        for o in report.observations:
            service.submit(o.trial.trial_id, o.answer)
        service.finish()
    export_reports(directory)
    return manifest


PROFILES = {
    "zero_effects": ((0, 1, 0, 0), 0),
    "source_impression": ((1, 1, 0, 0), 0),
    "archive_underweight": ((0, 0.5, 0, 0), 0),
    "response_wording": ((0, 1, 0, 0), 0.4),
    "business_prior": ((0, 1, -1, 0), 0),
    "combined": ((-1, 1.5, 1, 0), 0.4),
}


def recovery_study(directory, *, worlds=12, repetitions=3, seed=4821):
    """Full and off-grid recovery, misspecification gate, retained observed response vectors."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = create_manifest(
        synthetic_agent(), worlds=worlds, replicates=1, seed=seed, response_origin="synthetic"
    )
    write_manifest(directory, manifest)
    base_reports = make_reports(manifest, noise=False)
    grid, prepared = prepare(base_reports, manifest.analysis_plan)
    trials = [o.trial for o in base_reports[0].observations]
    cov = covariance(trials, manifest.analysis_plan)
    inv = np.linalg.inv(cov)
    rng = np.random.default_rng(seed)
    profiles = {
        **PROFILES,
        "off_grid": ((0.6, 0.8, -0.6, 0.2), 0.25),
        "misspecified": ((0, 1, 0, 0), 0),
    }
    rows = []
    manifest_hash = digest((manifest.model_dump_json(indent=2) + "\n").encode())
    for name, (theta, beta) in profiles.items():
        if name == "off_grid":
            generating = make_reports(manifest, theta, beta, noise=False)
            means = [observed_vector(r.observations, manifest.analysis_plan) for r in generating]
        else:
            index = np.flatnonzero(np.all(grid == theta, axis=1))[0]
            means = [p["pred"][index] + beta * p["w"] for p in prepared]
        for repeat in range(repetitions):
            altered, reports, raw = [], [], []
            for p, mean in zip(prepared, means, strict=True):
                vector = mean + rng.multivariate_normal(np.zeros(len(mean)), cov)
                if name == "misspecified":
                    # Impossible-for-family predictive growth intervals; should fail absolute fit.
                    vector = vector.copy()
                    from epistemics.study.inference import channels

                    for i, (_, channel) in enumerate(channels(trials)):
                        if channel.startswith("p"):
                            vector[i] += 25
                report = p["report"].model_copy(deep=True)
                public = [o.trial for o in report.observations]
                answers = answers_from_vector(public, vector)
                for o, answer in zip(report.observations, answers, strict=True):
                    o.answer = answer
                observed = observed_vector(report.observations, manifest.analysis_plan)
                residual = observed - p["pred"]
                whitened = residual @ inv
                altered.append(
                    {
                        **p,
                        "report": report,
                        "observed": observed,
                        "a": np.sum(whitened * residual, axis=1),
                        "b": whitened @ p["w"],
                    }
                )
                reports.append(report)
                raw.append(observed.tolist())
            fit = fit_reports(
                manifest, manifest_hash, reports, {}, bootstrap=0, prepared_data=(grid, altered)
            )
            true = dict(zip([*fit.parameters], [*theta, beta], strict=True))
            errors = {k: abs(v.estimate - true[k]) for k, v in fit.parameters.items()}
            coverage = {
                k: v.interval_95[0] - 1e-9 <= true[k] <= v.interval_95[1] + 1e-9
                for k, v in fit.parameters.items()
            }
            rows.append(
                {
                    "profile": name,
                    "repeat": repeat,
                    "truth": true,
                    "absolute_errors": errors,
                    "covered": coverage,
                    "parameters": {k: v.model_dump() for k, v in fit.parameters.items()},
                    "adequate": fit.diagnostics["predictive_adequacy_passed"],
                    "continuous_refinement_converged": fit.diagnostics[
                        "continuous_refinement_converged"
                    ],
                    "heldout_standardized_rmse": fit.diagnostics["heldout_standardized_rmse"],
                    "preferred_training_model": fit.diagnostics[
                        "preferred_model_by_training_evidence"
                    ],
                    "models": fit.model_comparisons,
                    "observed_vectors": raw,
                }
            )
            with (directory / "recovery-runs.jsonl").open("a") as stream:
                stream.write(json.dumps(rows[-1], allow_nan=False) + "\n")
    exact = [r for r in rows if r["profile"] in PROFILES]
    limits = dict(zip(exact[0]["absolute_errors"], [0.4, 0.3, 0.6, 0.4, 0.12], strict=True))
    errors = {k: float(np.mean([r["absolute_errors"][k] for r in exact])) for k in limits}
    coverage = {k: float(np.mean([r["covered"][k] for r in exact])) for k in limits}
    comparisons = {
        "source_impression": ("source_impression", ["archive_learning", "response_wording"]),
        "archive_underweight": ("archive_learning", ["business"]),
        "response_wording": ("response_wording", ["source_impression"]),
        "business_prior": ("business", ["baseline"]),
        "combined": ("full", ["archive_learning", "response_wording", "source_impression"]),
    }
    discrimination = []
    for row in exact:
        if row["profile"] in comparisons:
            own, alternatives = comparisons[row["profile"]]
            discrimination.extend(
                row["models"][own]["heldout_joint_log_predictive_density"]
                > row["models"][other]["heldout_joint_log_predictive_density"]
                for other in alternatives
            )
    # Low-repetition smoke runs cannot certify interval coverage at nominal 95%.
    gates = {
        "mean_absolute_error": all(errors[k] <= limits[k] for k in limits),
        "in_family_predictive_adequacy": all(r["adequate"] for r in exact),
        "misspecification_detected": all(
            not r["adequate"] for r in rows if r["profile"] == "misspecified"
        ),
        "business_alternative_not_misattributed": all(
            r["absolute_errors"]["source_frame"] <= limits["source_frame"]
            and r["absolute_errors"]["output_frame"] <= limits["output_frame"]
            for r in exact
            if r["profile"] in {"zero_effects", "business_prior"}
        ),
        "distinct_candidate_discrimination": all(discrimination),
        "continuous_refinement_converged": all(
            r["continuous_refinement_converged"] for r in rows if r["profile"] != "misspecified"
        ),
        "off_grid_recovery_error": all(
            np.mean([r["absolute_errors"][k] for r in rows if r["profile"] == "off_grid"])
            <= limits[k]
            for k in limits
        ),
    }
    result = {
        "schema_version": "epistemics.study-recovery.v1",
        "response_origin": "synthetic",
        "implementation_sha256": manifest.implementation_sha256,
        "worlds": worlds,
        "episodes_per_repeat": len(prepared),
        "repetitions": repetitions,
        "gates": gates,
        "passed": all(gates.values()),
        "parameter_mae": errors,
        "mae_limits": limits,
        "empirical_interval_coverage": coverage,
        "model_selection_counts": {
            name: {
                model: sum(
                    r["preferred_training_model"] == model for r in rows if r["profile"] == name
                )
                for model in rows[0]["models"]
            }
            for name in profiles
        },
        "interval_coverage_validated": False,
        "limitations": [
            "Finite synthetic checks, not real-agent validation or a proof of identification.",
            "Off-grid continuous recovery is tested separately; coarse-grid model comparison remains an approximation.",
            "This repetition count does not establish nominal 95% interval coverage.",
            "Misspecification test is one deliberately incompatible family; passing does not cover all misspecification.",
        ],
        "runs": rows,
    }
    path = directory / "recovery.json"
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    path.with_suffix(".sha256").write_text(digest(path.read_bytes()) + "\n")
    return result
