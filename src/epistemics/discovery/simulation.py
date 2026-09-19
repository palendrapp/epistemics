"""Synthetic observers and multi-run recovery. Never substitute these for an LLM respondent."""

import hashlib
import json
import math
import tempfile
from itertools import product
from pathlib import Path

import numpy as np

from epistemics.discovery.battery import VARIANTS, battery_sha256, generate_battery
from epistemics.discovery.inference import MODEL_DESCRIPTIONS, extract, forecast, report_prediction
from epistemics.discovery.models import DiscoveryAnswer, DiscoveryTrial
from epistemics.discovery.world import cdf
from epistemics.models import AgentDescriptor

ALPHA_GRID = np.linspace(-2, 2, 17)


def answer_trial(
    trial: DiscoveryTrial, *, model="joint_learning", source_frame=0.0, output_frame=0.0
):
    if not math.isfinite(output_frame):
        raise ValueError("Output framing coefficient must be finite")
    f = forecast(trial, model=model, source_frame=source_frame)
    p = float(
        report_prediction(trial, model=model, source_frame=source_frame, output_frame=output_frame)[
            0
        ]
    )
    values, _, _ = extract(trial)
    return DiscoveryAnswer(
        target_probability=p if trial.target_event == "growth_above_12" else 1 - p,
        growth_quantiles_pct=f.growth_quantiles_pct,
        decision="invest" if 3 * p - 1 > 1e-12 else "hold",
        evidence_ids=[d.document_id for d in trial.documents],
        source_accuracy={sid: f.source_accuracy[sid] for sid in trial.source_probe_ids},
        conditional_growth_probability=f.conditional_growth_probability
        if trial.conditional_probe
        else None,
        extracted_values={
            key: values["renewal" if key == "renewal_estimate_pct" else "model"]
            for key in trial.extraction_keys
        },
    )


def demo(seed=7, *, variant=None, **policy):
    from epistemics.service import EvaluationService

    config = json.dumps({"policy": policy, "variant": variant}, sort_keys=True).encode()
    agent = AgentDescriptor(
        agent_id="demo:discovery-observer",
        model="synthetic-conditional-observer",
        model_version="0.3.0",
        configuration_sha256=hashlib.sha256(config).hexdigest(),
        context_policy="continuous",
    )
    with tempfile.TemporaryDirectory() as directory:
        service = EvaluationService(Path(directory) / "discovery.sqlite3")
        session = service.start(agent, seed=seed, battery="discovery", discovery_variant=variant)[
            "session_id"
        ]
        while not (current := service.get_trial(session))["complete"]:
            trial = DiscoveryTrial.model_validate(current["trial"])
            service.submit(session, trial.trial_id, answer_trial(trial, **policy))
        return service.finish(session)


def preview(seed=7, variant=None):
    trial = DiscoveryTrial.model_validate(generate_battery(seed, variant=variant)[-1]["trial"])
    text = [
        f"# {trial.company}: discovery dossier",
        "",
        "Operator preview of all public arrivals; MCP reveals them one at a time.",
        "",
        trial.background,
        "",
        "## Source histories",
        "",
        "Reported and audited values concern the same historical measurement. No accuracy percentages are supplied.",
    ]
    for s in trial.sources:
        text += [
            "",
            f"### {s.name}",
            "",
            s.profile,
            "",
            "| Completed case | Reported (%) | Audited (%) |",
            "| --- | ---: | ---: |",
        ]
        text += [f"| {r.case_id} | {r.reported_pct:.1f} | {r.audited_pct:.1f} |" for r in s.archive]
    text += [
        "",
        "## Historical business analogues",
        "",
        "| Case | Audited underlying growth (%) | Rollout disruption | Backlog score | Renewal-supported growth (%) |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    text += [
        f"| {r.case_id} | {r.underlying_growth_pct:.1f} | {r.rollout_disruption} | {r.backlog_score:.1f} | {r.renewal_growth_pct:.1f} |"
        for r in trial.analogues
    ]
    text += ["", "## Response task", "", trial.instructions]
    for d in trial.documents:
        text += [
            "",
            f"## {d.document_id}: {d.title}",
            "",
            f"{d.source} · {d.published_at}",
            "",
            d.text,
        ]
    return "\n".join(text) + "\n"


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def response_log_likelihood(observed, latent_logits, sigma=0.04):
    """Rounded logistic-normal reports on a 1e-4 grid, including endpoint bins."""
    low = np.maximum(observed - 0.00005, 0)
    high = np.minimum(observed + 0.00005, 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        lo = (np.log(low / (1 - low)) - latent_logits) / sigma
        hi = (np.log(high / (1 - high)) - latent_logits) / sigma
    # Use the closer tail to reduce cancellation.
    mass = np.where(lo >= 0, cdf(-lo) - cdf(-hi), cdf(hi) - cdf(lo))
    return np.log(np.maximum(mass, 1e-300))


def prediction_design(seeds):
    """Matched variants; every prediction receives only public trials."""
    joint = [[] for _ in ALPHA_GRID]
    others = {name: [] for name in MODEL_DESCRIPTIONS if name != "joint_learning"}
    groups = []
    wording = []
    public_cases = []
    for seed in seeds:
        for settings in product(*VARIANTS.values()):
            variant = dict(zip(VARIANTS, settings, strict=True))
            records = generate_battery(seed, variant=variant)
            public_cases.append({"seed": seed, "variant": variant})
            for record in records:
                t = DiscoveryTrial.model_validate(record["trial"])
                for ix, alpha in enumerate(ALPHA_GRID):
                    joint[ix].extend(logit(report_prediction(t, source_frame=float(alpha))))
                for name in others:
                    others[name].extend(logit(report_prediction(t, model=name)))
                groups.extend([seed] * (1 + len(t.source_probe_ids)))
                wording.extend(
                    [1 if t.target_event == "growth_above_12" else -1]
                    + [0] * len(t.source_probe_ids)
                )
    design = {
        "joint_learning": np.array(joint),
        **{k: np.array(v)[None, :] for k, v in others.items()},
    }
    return design, np.array(groups), np.array(wording), public_cases


def fit_candidates(design, observed, wording, train):
    """Constrained logit least squares; evaluate frozen fits with held-out report likelihood."""
    target = logit(observed)
    candidates = {name: (name, False, False) for name in MODEL_DESCRIPTIONS}
    candidates.update(
        {
            "source_framing": ("joint_learning", True, False),
            "output_framing": ("joint_learning", False, True),
            "source_and_output": ("joint_learning", True, True),
        }
    )
    fits = {}
    for name, (base, fit_alpha, fit_beta) in candidates.items():
        matrix = design[base]
        choices = range(len(ALPHA_GRID)) if fit_alpha else [8 if base == "joint_learning" else 0]
        best = None
        for ix in choices:
            pred = matrix[ix]
            beta = (
                float(
                    np.clip(
                        np.dot((target - pred)[train], wording[train])
                        / np.dot(wording[train], wording[train]),
                        -1,
                        1,
                    )
                )
                if fit_beta
                else 0.0
            )
            predicted = pred + beta * wording
            error = float(np.mean((predicted[train] - target[train]) ** 2))
            if best is None or error < best[0]:
                best = (error, ix, beta, predicted)
        error, ix, beta, predicted = best
        likelihood = response_log_likelihood(observed[~train], predicted[~train])
        fits[name] = {
            "source_frame": float(ALPHA_GRID[ix]) if base == "joint_learning" else 0.0,
            "output_frame": beta,
            "train_logit_mse": error,
            "heldout_log_likelihood": float(likelihood.sum()),
            "heldout_logit_rmse": float(
                np.sqrt(np.mean((predicted[~train] - target[~train]) ** 2))
            ),
            "on_parameter_bound": bool((fit_alpha and ix in (0, 16)) or abs(beta) >= 1),
        }
    return fits


def recovery_study(seeds=8, blocks=3):
    if not 4 <= seeds <= 30 or not 1 <= blocks <= 10:
        raise ValueError("Use 4..30 seeds per block and 1..10 blocks")
    profiles = {
        "joint_learning": ("joint_learning", 0.0, 0.0),
        "fixed_sources": ("fixed_sources", 0.0, 0.0),
        "fixed_weak_link": ("fixed_weak_link", 0.0, 0.0),
        "fixed_strong_link": ("fixed_strong_link", 0.0, 0.0),
        "source_framing": ("joint_learning", 1.25, 0.0),
        "output_framing": ("joint_learning", 0.0, 0.4),
        "source_and_output": ("joint_learning", -1.0, 0.3),
    }
    runs = []
    for block in range(blocks):
        world_seeds = list(range(block * seeds, (block + 1) * seeds))
        design, groups, wording, cases = prediction_design(world_seeds)
        train = np.isin(groups, world_seeds[: seeds // 2])
        rng = np.random.default_rng(8101 + block)
        for name, (base, alpha, beta) in profiles.items():
            ix = int(np.argmin(abs(ALPHA_GRID - alpha))) if base == "joint_learning" else 0
            latent = design[base][ix] + beta * wording
            noisy = latent + rng.normal(0, 0.04, len(latent))
            observed = np.round(1 / (1 + np.exp(-noisy)), 4)
            fits = fit_candidates(design, observed, wording, train)
            # Nested zero-coefficient families can tie; all scores are retained.
            best = max(fits, key=lambda k: fits[k]["heldout_log_likelihood"])
            own = fits[name]
            runs.append(
                {
                    "block": block,
                    "profile": name,
                    "generating_source_frame": alpha,
                    "generating_output_frame": beta,
                    "train_seeds": world_seeds[: seeds // 2],
                    "heldout_seeds": world_seeds[seeds // 2 :],
                    "cases": cases,
                    "observed_reports": observed.tolist(),
                    "source_frame_absolute_error": abs(own["source_frame"] - alpha),
                    "output_frame_absolute_error": abs(own["output_frame"] - beta),
                    "best_heldout_model": best,
                    "fits": fits,
                }
            )
    summary = {}
    for name in profiles:
        rows = [r for r in runs if r["profile"] == name]
        summary[name] = {
            "fits": len(rows),
            "source_frame_mae": float(np.mean([r["source_frame_absolute_error"] for r in rows])),
            "output_frame_mae": float(np.mean([r["output_frame_absolute_error"] for r in rows])),
            "heldout_selection_counts": {
                key: sum(r["best_heldout_model"] == key for r in rows) for key in profiles
            },
        }
    parameter_pass = all(
        s["source_frame_mae"] <= 0.25 and s["output_frame_mae"] < 0.08 for s in summary.values()
    )
    # Separate model discrimination from nested model selection: the true generating
    # trajectory must beat each materially different frozen candidate on held-out data.
    discrimination = []
    for r in runs:
        own = r["fits"][r["profile"]]["heldout_log_likelihood"]
        rivals = ("fixed_sources", "fixed_weak_link", "fixed_strong_link", "joint_learning")
        if r["profile"] in {"source_framing", "output_framing", "source_and_output"}:
            rivals = ("joint_learning",)
        discrimination.append(
            all(
                own >= r["fits"][other]["heldout_log_likelihood"]
                for other in rivals
                if other != r["profile"]
            )
        )
    return {
        "kind": "synthetic_discovery_recovery",
        "battery_sha256": battery_sha256(),
        "battery_version": "company-discovery/0.3.0",
        "blocks": blocks,
        "seeds_per_block": seeds,
        "variants_per_seed": 16,
        "logit_noise_sd": 0.04,
        "rounding_grid": 0.0001,
        "synthetic_case_runs": seeds * blocks * 16 * len(profiles),
        "passed_parameter_gates": parameter_pass,
        "passed_discrimination_gates": all(discrimination),
        "passed": parameter_pass and all(discrimination),
        "summary": summary,
        "runs": runs,
        "limitations": [
            "Synthetic observers only; not real-agent or psychometric validation.",
            "Variants sharing a world seed are matched, not independent outcomes. All variants of a seed stay in one split.",
            "One authored case family; new seeds are not held-out business mechanisms.",
            "Input and output recovery fixes all other priors, report gain and source measurement grids.",
            "Least-squares logit fitting is compared using rounded-logistic-normal held-out report likelihood. Nested models may tie.",
            "Archives recur within a case; cases represent fresh contexts, not cross-company learning.",
        ],
    }
