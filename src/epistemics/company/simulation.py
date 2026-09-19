"""Explicit synthetic respondents and parameter recovery; these are not real-agent evaluations."""

import hashlib
import json
import math
import tempfile
from pathlib import Path

import numpy as np

from epistemics.battery import logit, sigmoid
from epistemics.company.analysis import fit_models
from epistemics.company.battery import BATTERY_VERSION, battery_sha256, generate_battery
from epistemics.company.inference import evidence_features, forecast, quantiles
from epistemics.company.models import CompanyAnswer, CompanyObservation, CompanyTrial
from epistemics.models import AgentDescriptor


def answer_trial(
    trial: CompanyTrial, *, positive=1.0, negative=1.0, duplicate=0.0, auxiliary_shift=0.0
) -> CompanyAnswer:
    """Uses only the current public trial. This function must never run on behalf of an LLM subject."""
    if not all(math.isfinite(x) for x in (positive, negative, duplicate, auxiliary_shift)):
        raise ValueError("Synthetic policy parameters must be finite")
    if positive <= 0 or negative <= 0 or not 0 <= duplicate <= 1:
        raise ValueError("Evidence weights must be positive and duplicate weight must be in [0,1]")
    if auxiliary_shift != 0 and (positive, negative, duplicate) != (1.0, 1.0, 0.0):
        raise ValueError(
            "Choose either weighted evidence or an auxiliary-prior shift for this pilot"
        )
    result = forecast(trial, auxiliary_shift).model_dump()
    if (positive, negative, duplicate) != (1.0, 1.0, 0.0):
        z = logit(trial.dossier.world.prior_growth)
        for step in range(1, len(trial.evidence) + 1):
            current = trial.model_copy(update={"evidence": trial.evidence[:step]})
            inc, standalone, is_negative = evidence_features(current)
            z += (negative if is_negative else positive) * (
                (1 - duplicate) * inc + duplicate * standalone
            )
        result["growth_probability"] = sigmoid(z)
        result["growth_quantiles_pct"] = quantiles(sigmoid(z)).model_dump()
    p = result["growth_probability"]
    mandate = trial.dossier.mandate
    ev = p * mandate.gain_if_growth_target_met - (1 - p) * mandate.loss_if_growth_target_missed
    return CompanyAnswer(
        **result,
        decision="invest" if ev > 1e-12 else "hold",
        evidence_ids=[e.document_id for e in trial.evidence],
    )


def demo(seed=42, **policy):
    from epistemics.service import EvaluationService

    configuration = json.dumps(policy, sort_keys=True).encode()
    agent = AgentDescriptor(
        agent_id="demo:company-policy",
        model="synthetic-company-policy",
        model_version="0.2.0",
        configuration_sha256=hashlib.sha256(configuration).hexdigest(),
        context_policy="reset_per_task",
        temperature=0,
    )
    with tempfile.TemporaryDirectory() as directory:
        service = EvaluationService(Path(directory) / "company.sqlite3")
        session = service.start(agent, seed=seed, battery="company")["session_id"]
        while not (current := service.get_trial(session))["complete"]:
            trial = CompanyTrial.model_validate(current["trial"])
            service.submit(session, trial.trial_id, answer_trial(trial, **policy))
        return service.finish(session)


def synthetic_observations(
    seed: int, *, noise=0.0, positive=1.0, negative=1.0, duplicate=0.0, auxiliary_shift=0.0
):
    rng = np.random.default_rng(seed + 1701)
    observations = []
    for record in generate_battery(seed):
        trial = CompanyTrial.model_validate(record["trial"])
        answer = answer_trial(
            trial,
            positive=positive,
            negative=negative,
            duplicate=duplicate,
            auxiliary_shift=auxiliary_shift,
        )
        if noise:
            p = sigmoid(logit(answer.growth_probability) + float(rng.normal(0, noise)))
            answer = answer.model_copy(update={"growth_probability": p})
        observations.append(CompanyObservation(**record, answer=answer, answered_at="simulation"))
    return observations


def recovery_study(seeds: int = 20) -> dict:
    if not 1 <= seeds <= 200:
        raise ValueError("seeds must be between 1 and 200")
    profiles = {
        "reference": {},
        "negative_weighting": {"positive": 0.8, "negative": 1.6, "duplicate": 0.3},
        "duplicate_counting": {"duplicate": 1.0},
        "conservative": {"positive": 0.5, "negative": 0.5},
        "auxiliary_prior": {"auxiliary_shift": 1.2},
    }
    rows = []
    for seed in range(seeds):
        for name, policy in profiles.items():
            observations = synthetic_observations(seed, noise=0.015, **policy)
            parameters, fits = fit_models(observations)
            weighted = fits["weighted_evidence"]
            rows.append(
                {
                    "seed": seed,
                    "profile": name,
                    "generating_parameters": policy,
                    "fitted_parameters": {k: p.estimate for k, p in parameters.items()},
                    "auxiliary_shift": fits["joint_auxiliary_prior"].parameters[
                        "auxiliary_log_odds_shift"
                    ],
                    "identified": weighted.identified,
                    "heldout_rmse": {k: f.heldout_rmse for k, f in fits.items()},
                    "best_heldout_model": min(fits, key=lambda k: fits[k].heldout_rmse),
                }
            )
    summary = {}
    for name, policy in profiles.items():
        group = [r for r in rows if r["profile"] == name]
        expected = {
            "positive_weight": policy.get("positive", 1),
            "negative_weight": policy.get("negative", 1),
            "duplicate_weight": policy.get("duplicate", 0),
        }
        errors = (
            {
                key: float(np.mean([abs(r["fitted_parameters"][key] - value) for r in group]))
                for key, value in expected.items()
            }
            if name != "auxiliary_prior"
            else {}
        )
        summary[name] = {
            "runs": len(group),
            "unidentified_runs": sum(not r["identified"] for r in group),
            "weighted_parameter_mean_absolute_errors": errors,
            "auxiliary_shift_mean_absolute_error": float(
                np.mean(
                    [abs(r["auxiliary_shift"] - policy.get("auxiliary_shift", 0)) for r in group]
                )
            )
            if name in {"reference", "auxiliary_prior"}
            else None,
            "model_selection_counts": {
                key: sum(r["best_heldout_model"] == key for r in group)
                for key in ("reference_joint", "weighted_evidence", "joint_auxiliary_prior")
            },
        }
    # Engineering gates for this declared synthetic range, not population validity claims.
    passed = (
        all(s["unidentified_runs"] == 0 for s in summary.values())
        and all(
            error < (0.08 if key == "duplicate_weight" else 0.12)
            for s in summary.values()
            for key, error in s["weighted_parameter_mean_absolute_errors"].items()
        )
        and summary["auxiliary_prior"]["auxiliary_shift_mean_absolute_error"] < 0.15
    )
    return {
        "kind": "synthetic_parameter_recovery",
        "battery_version": BATTERY_VERSION,
        "battery_sha256": battery_sha256(),
        "simulation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seeds_per_profile": seeds,
        "logit_report_noise_sd": 0.015,
        "passed_recovery_gates": bool(passed),
        "summary": summary,
        "runs": rows,
        "limitations": [
            "Synthetic respondents only; this is not a fresh-agent or psychometric validation run.",
            "Reference is nested in both fitted families, so tied or near-tied model selections are expected.",
            "Model-selection counts use held-out episodes; those episodes are not used to select fitted parameters.",
            "All attempted seeds and profiles, including unidentified fits, are retained.",
        ],
    }


def preview(seed=42) -> str:
    records = generate_battery(seed)
    trial = CompanyTrial.model_validate(records[8]["trial"])
    text = [
        f"# {trial.dossier.company}: sample company episode",
        "",
        "Evaluator preview of the first episode's public materials. Actual MCP play reveals one item at a time.",
        "",
        trial.dossier.background,
        "",
        "## Public calibration",
        "",
        "```json",
        json.dumps(trial.dossier.world.model_dump(), indent=2),
        "```",
        "",
        trial.dossier.assumptions,
        "",
        trial.dossier.mandate.instruction,
        f"Gain: {trial.dossier.mandate.gain_if_growth_target_met}; loss: {trial.dossier.mandate.loss_if_growth_target_missed}.",
        "",
        "## Response after every arrival",
        "",
        trial.instructions,
    ]
    for document in trial.evidence:
        text += [
            "",
            f"## {document.document_id}: {document.source}",
            "",
            document.text,
            "",
            f"Format: {document.format}. Inputs: {', '.join(document.signal.parents) or 'new measurement'}.",
        ]
    return "\n".join(text) + "\n"
