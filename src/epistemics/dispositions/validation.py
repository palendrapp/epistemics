"""Synthetic parameter and model recovery for modules T2, T3 and T5.

Screens are declared here before any run. They test identifiability under the specified
generative model, with respondents simulated from it; they validate no respondent's behavior.
"""

import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np

from epistemics.dispositions import DESIGN_VERSION, MODEL_VERSION, design, fit, observers
from epistemics.dispositions.response import sample_reports, sample_wtp

GATES = {
    "agent_noise_band": {"report_sd": 0.5, "wtp_sd": 7.0},
    "minimum_disposition_correlation": 0.9,
    "maximum_disposition_mae": 0.1,
    "maximum_certainty_value_mae_fraction_of_range": 0.1,
    # Intervals span whole grid cells, so over-coverage is expected and not screened.
    "minimum_interval_coverage": 0.8,
    "minimum_model_recovery_accuracy": 0.85,
    # Learned base rates: detect learning (prior strength <= 16) against none (strength 1024), and
    # recover the starting disposition where learning is slow enough for it to matter (>= 8).
    "minimum_learning_detection_accuracy": 0.85,
    "minimum_start_correlation": 0.85,
    "maximum_start_mae": 0.12,
}
REPORT_PRIOR = {
    "disposition": (0.0, 1.0),
    "gamma": (0.6, 1.4),
    "bias": (-0.4, 0.4),
    "report_sd": (0.05, 0.8),
}
CHECK_PRIOR = {
    "certainty_value": {"linear": (-20.0, 80.0), "entropy": (-40.0, 160.0)},
    "decision_weight": (0.6, 1.4),
    "wtp_sd": (1.5, 12.0),
}
# Rival models agree near some boundaries (no discount at all, or omissions ignored), so model
# recovery is scored where their predictions differ.
DISTINGUISHABLE = {
    "dependence": (0.25, 1.0),
    "fixed_discount": (0.0, 0.75),
    "disclosure": (0.25, 1.0),
    "linear_skepticism": (0.25, 1.0),
}
# Certainty functions coincide at zero value; recovery between them is scored at material values.
MATERIAL_CERTAINTY_VALUE = {"linear": (30.0, 80.0), "entropy": (60.0, 160.0)}
MODULES = {
    "corroboration": ("dependence", "fixed_discount", design.corroboration),
    "disclosure": ("disclosure", "linear_skepticism", design.disclosure),
}
LEARNING = {
    "world_rates": (0.2, 0.8),
    "no_learning_share": 0.25,
    "no_learning_strength": 1024.0,
    "log2_strength": (-1.0, 6.0),
    "learning_if_strength_at_most": 16.0,
    "start_scored_if_strength_at_least": 8.0,
    # Learning is invisible when the starting disposition already matches the revealed rate.
    "detection_if_start_differs_from_rate_by": 0.25,
}
REPORT_GRIDS = {
    "disposition": fit.DISPOSITION,
    "gamma": fit.GAMMA,
    "bias": fit.BIAS,
    "report_sd": fit.REPORT_SD,
}
CHECK_GRIDS = {
    "certainty_value": fit.CERTAINTY_VALUE,
    "decision_weight": fit.DECISION_WEIGHT,
    "wtp_sd": fit.WTP_SD,
}


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def fingerprint():
    payload = {
        "files": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))
        },
        "dependencies": {"numpy": importlib.metadata.version("numpy")},
    }
    return hashlib.sha256(encoded(payload)).hexdigest()


def cell_edges(grid):
    """Each grid point stands for the cell between midpoints to its neighbours."""
    middle = (grid[1:] + grid[:-1]) / 2
    lower = np.concatenate([[grid[0] - (grid[1] - grid[0]) / 2], middle])
    upper = np.concatenate([middle, [grid[-1] + (grid[-1] - grid[-2]) / 2]])
    return lower, upper


def simulate_reports(model, items, truth, rng):
    latent = fit.REPORT_MODELS[model](items, truth["disposition"], truth["gamma"])
    latent = latent + truth["bias"] * (items["kind"] != "probe")
    return sample_reports(latent, truth["report_sd"], rng)


def simulate_checks(function, items, truth, rng):
    decision, gain = observers.check_values(items, function)
    means = truth["certainty_value"] * gain + truth["decision_weight"] * decision
    return sample_wtp(means, truth["wtp_sd"], rng)


def draw(rng, bounds):
    return {name: float(rng.uniform(*limits)) for name, limits in bounds.items()}


def record(truth, result):
    return {
        "truth": truth,
        "mean": {k: v["mean"] for k, v in result["parameters"].items()},
        "interval": {k: v["interval_90"] for k, v in result["parameters"].items()},
    }


def metrics(records, grids, noise, limit):
    bands = {
        "agent_noise": [r for r in records if r["truth"][noise] <= limit],
        "human_noise": [r for r in records if r["truth"][noise] > limit],
        "all": records,
    }
    summary = {}
    for band, rows in bands.items():
        if len(rows) < 3:
            summary[band] = {"respondents": len(rows)}
            continue
        parameters = {}
        for name, grid in grids.items():
            truth = np.array([r["truth"][name] for r in rows])
            mean = np.array([r["mean"][name] for r in rows])
            lower, upper = cell_edges(grid)
            lo = np.array([lower[np.searchsorted(grid, r["interval"][name][0])] for r in rows])
            hi = np.array([upper[np.searchsorted(grid, r["interval"][name][1])] for r in rows])
            parameters[name] = {
                "correlation": float(np.corrcoef(truth, mean)[0, 1]) if np.std(mean) > 0 else 0.0,
                "mae": float(np.mean(np.abs(mean - truth))),
                "coverage_90": float(np.mean((lo <= truth) & (truth <= hi))),
            }
        first, second = list(grids)[:2]
        errors = [
            np.array([r["mean"][name] - r["truth"][name] for r in rows]) for name in (first, second)
        ]
        summary[band] = {
            "respondents": len(rows),
            "parameters": parameters,
            f"{first}_{second}_error_correlation": float(np.corrcoef(*errors)[0, 1]),
        }
    return summary


def report_recovery(model, items_by_design, truths, rng):
    records = {name: [] for name in items_by_design}
    for truth in truths:
        for name, items in items_by_design.items():
            reports = simulate_reports(model, items, truth, rng)
            records[name].append(record(truth, fit.fit_reports(model, items, reports)))
    limit = GATES["agent_noise_band"]["report_sd"]
    return {name: metrics(rows, REPORT_GRIDS, "report_sd", limit) for name, rows in records.items()}


def model_recovery(models, items, datasets, rng, fitter, simulator, bounds_for):
    rows = []
    for generating in models:
        for _ in range(datasets):
            truth = draw(rng, bounds_for(generating))
            observed = simulator(generating, items, truth, rng)
            evidence = {m: fitter(m, items, observed)["log_evidence"] for m in models}
            rows.append(
                {
                    "generating": generating,
                    "chosen": max(evidence, key=evidence.get),
                    "truth": truth,
                }
            )
    return rows


def recovery_accuracy(rows, models, noise, limit):
    summary = {}
    for band, keep in (
        ("agent_noise", lambda r: r["truth"][noise] <= limit),
        ("all", lambda r: True),
    ):
        summary[band] = {}
        for generating in models:
            chosen = [r["chosen"] for r in rows if r["generating"] == generating and keep(r)]
            summary[band][generating] = {
                "datasets": len(chosen),
                "accuracy": float(np.mean([c == generating for c in chosen])) if chosen else 0.0,
                "chosen": {m: chosen.count(m) for m in models},
            }
    return summary


def boundaries(model, items, repetitions, rng):
    cells = []
    for disposition in (0.0, 0.5, 1.0):
        for report_sd in (0.1, 0.3):
            truth = {"disposition": disposition, "gamma": 1.0, "bias": 0.0, "report_sd": report_sd}
            estimates, covered = [], []
            for _ in range(repetitions):
                result = fit.fit_reports(model, items, simulate_reports(model, items, truth, rng))
                row = result["parameters"]["disposition"]
                estimates.append(row["mean"])
                covered.append(
                    row["interval_90"][0] - 0.025 <= disposition <= row["interval_90"][1] + 0.025
                )
            cells.append(
                {
                    "disposition": disposition,
                    "report_sd": report_sd,
                    "mean_estimate": float(np.mean(estimates)),
                    "mae": float(np.mean(np.abs(np.array(estimates) - disposition))),
                    "coverage_90": float(np.mean(covered)),
                }
            )
    return cells


def learning_recovery(module, model, items, respondents, rng):
    """Respondents who learn the base rate from structures revealed after each case."""
    forecast = items["kind"] != "probe"
    rows = []
    for k in range(respondents):
        rate = LEARNING["world_rates"][k % len(LEARNING["world_rates"])]
        order = rng.permutation(len(forecast))
        posterior = observers.structure_posterior(module, items, rate)
        revealed = [None if np.isnan(p) else bool(rng.random() < p) for p in posterior]
        successes, trials = observers.revealed_counts(order, revealed)
        truth = draw(rng, {k: v for k, v in REPORT_PRIOR.items() if k != "disposition"})
        truth["start"] = float(rng.uniform(0, 1))
        if rng.random() < LEARNING["no_learning_share"]:
            truth["strength"] = LEARNING["no_learning_strength"]
        else:
            truth["strength"] = float(2 ** rng.uniform(*LEARNING["log2_strength"]))
        delta = observers.learned(truth["start"], truth["strength"], successes, trials)
        latent = fit.REPORT_MODELS[model](items, delta, truth["gamma"]) + truth["bias"] * forecast
        reports = sample_reports(latent, truth["report_sd"], rng)
        result = fit.fit_learning(model, items, reports, successes, trials)
        rows.append({"rate": rate, "truth": truth, "result": result})
    return rows


def learning_metrics(rows, limit):
    agent = [r for r in rows if r["truth"]["report_sd"] <= limit]
    detection = {}
    for label, keep in (
        ("learning", lambda s: s <= LEARNING["learning_if_strength_at_most"]),
        ("none", lambda s: s >= LEARNING["no_learning_strength"]),
    ):
        gap = LEARNING["detection_if_start_differs_from_rate_by"]
        chosen = [
            r["result"]["learning_probability"] > 0.5
            for r in agent
            if keep(r["truth"]["strength"]) and abs(r["truth"]["start"] - r["rate"]) >= gap
        ]
        correct = [c == (label == "learning") for c in chosen]
        detection[label] = {"datasets": len(correct), "accuracy": float(np.mean(correct))}
    scored = [
        r for r in agent if r["truth"]["strength"] >= LEARNING["start_scored_if_strength_at_least"]
    ]
    truth = np.array([r["truth"]["start"] for r in scored])
    mean = np.array([r["result"]["parameters"]["start"]["mean"] for r in scored])
    lower, upper = cell_edges(fit.DISPOSITION)
    lo = np.array(
        [
            lower[
                np.searchsorted(
                    fit.DISPOSITION, r["result"]["parameters"]["start"]["interval_90"][0]
                )
            ]
            for r in scored
        ]
    )
    hi = np.array(
        [
            upper[
                np.searchsorted(
                    fit.DISPOSITION, r["result"]["parameters"]["start"]["interval_90"][1]
                )
            ]
            for r in scored
        ]
    )
    finite = [r for r in agent if r["truth"]["strength"] < LEARNING["no_learning_strength"]]
    log_truth = np.log2([r["truth"]["strength"] for r in finite])
    log_mean = np.array([r["result"]["parameters"]["log2_strength"]["mean"] for r in finite])
    return {
        "respondents": len(agent),
        "detection": detection,
        "start": {
            "respondents": len(scored),
            "correlation": float(np.corrcoef(truth, mean)[0, 1]),
            "mae": float(np.mean(np.abs(mean - truth))),
            "coverage_90": float(np.mean((lo <= truth) & (truth <= hi))),
        },
        "log2_strength_correlation": float(np.corrcoef(log_truth, log_mean)[0, 1]),
        "gamma_mae": float(
            np.mean(
                [
                    abs(r["result"]["parameters"]["gamma"]["mean"] - r["truth"]["gamma"])
                    for r in agent
                ]
            )
        ),
    }


def validate(seed, respondents=200, model_datasets=100, boundary_repetitions=25):
    if respondents < 10 or model_datasets < 5 or boundary_repetitions < 1:
        raise ValueError("Use at least 10 respondents, 5 model datasets and 1 boundary repetition")
    results = {}
    for offset, (module, (model, rival, build)) in enumerate(MODULES.items()):
        rng = np.random.default_rng(seed + 10 * offset)
        truths = [draw(rng, REPORT_PRIOR) for _ in range(respondents)]
        designs = {"forecast": build(), "probe": build(probes=True)}
        recovery = report_recovery(model, designs, truths, rng)

        def bounds_for(m):
            return {**REPORT_PRIOR, "disposition": DISTINGUISHABLE[m]}

        rows = model_recovery(
            (model, rival),
            designs["forecast"],
            model_datasets,
            rng,
            fit.fit_reports,
            simulate_reports,
            bounds_for,
        )
        results[module] = {
            "parameter_recovery": recovery,
            "model_recovery": recovery_accuracy(
                rows, (model, rival), "report_sd", GATES["agent_noise_band"]["report_sd"]
            ),
            "boundaries": boundaries(model, designs["forecast"], boundary_repetitions, rng),
            "learning": learning_metrics(
                learning_recovery(
                    module,
                    model,
                    designs["probe"],
                    respondents,
                    np.random.default_rng(seed + 200 + offset),
                ),
                GATES["agent_noise_band"]["report_sd"],
            ),
        }
    rng = np.random.default_rng(seed + 100)
    items = design.checks()
    checks = {"parameter_recovery": {}}
    for function in ("linear", "entropy"):
        prior = {**CHECK_PRIOR, "certainty_value": CHECK_PRIOR["certainty_value"][function]}
        records = []
        for _ in range(respondents):
            truth = draw(rng, prior)
            wtp = simulate_checks(function, items, truth, rng)
            records.append(record(truth, fit.fit_checks(function, items, wtp)))
        checks["parameter_recovery"][function] = metrics(
            records, CHECK_GRIDS, "wtp_sd", GATES["agent_noise_band"]["wtp_sd"]
        )

    def check_bounds(function):
        return {**CHECK_PRIOR, "certainty_value": MATERIAL_CERTAINTY_VALUE[function]}

    rows = model_recovery(
        ("linear", "entropy"),
        items,
        model_datasets,
        rng,
        fit.fit_checks,
        simulate_checks,
        check_bounds,
    )
    checks["certainty_function_recovery"] = recovery_accuracy(
        rows, ("linear", "entropy"), "wtp_sd", GATES["agent_noise_band"]["wtp_sd"]
    )
    results["checks"] = checks
    return results


def check_gates(results):
    low = GATES["minimum_interval_coverage"]
    checks = {}
    for module in MODULES:
        agent = results[module]["parameter_recovery"]["forecast"]["agent_noise"]
        row = agent["parameters"]["disposition"]
        checks[f"{module}_disposition_recovery"] = (
            row["correlation"] >= GATES["minimum_disposition_correlation"]
            and row["mae"] <= GATES["maximum_disposition_mae"]
            and row["coverage_90"] >= low
        )
        learning = results[module]["learning"]
        checks[f"{module}_learning_detection"] = all(
            v["accuracy"] >= GATES["minimum_learning_detection_accuracy"]
            for v in learning["detection"].values()
        )
        checks[f"{module}_learning_start_recovery"] = (
            learning["start"]["correlation"] >= GATES["minimum_start_correlation"]
            and learning["start"]["mae"] <= GATES["maximum_start_mae"]
        )
        accuracy = results[module]["model_recovery"]["agent_noise"]
        checks[f"{module}_model_recovery"] = all(
            v["accuracy"] >= GATES["minimum_model_recovery_accuracy"] for v in accuracy.values()
        )
    for function, limits in CHECK_PRIOR["certainty_value"].items():
        agent = results["checks"]["parameter_recovery"][function]["agent_noise"]
        row = agent["parameters"]["certainty_value"]
        allowed = GATES["maximum_certainty_value_mae_fraction_of_range"] * (limits[1] - limits[0])
        checks[f"certainty_value_recovery_{function}"] = (
            row["correlation"] >= GATES["minimum_disposition_correlation"]
            and row["mae"] <= allowed
            and row["coverage_90"] >= low
        )
    return {"criteria": GATES, "checks": checks, "passed": all(checks.values())}


def plan(seed, respondents, model_datasets, boundary_repetitions):
    def listed(items):
        return {k: v.tolist() for k, v in items.items()}

    return {
        "schema_version": "epistemics.disposition-validation-plan.v2",
        "model_version": MODEL_VERSION,
        "design_version": DESIGN_VERSION,
        "implementation_sha256": fingerprint(),
        "seed": seed,
        "respondents_per_design": respondents,
        "model_recovery_datasets_per_model": model_datasets,
        "boundary_repetitions": boundary_repetitions,
        "generating_priors": {"reports": REPORT_PRIOR, "checks": CHECK_PRIOR},
        "model_recovery_regions": {**DISTINGUISHABLE, **MATERIAL_CERTAINTY_VALUE},
        "learning": {**LEARNING, "fitted_strength": fit.STRENGTH.tolist()},
        "fitted_grids": {
            **{k: v.tolist() for k, v in REPORT_GRIDS.items()},
            **{k: v.tolist() for k, v in CHECK_GRIDS.items()},
        },
        "designs": {
            "corroboration": listed(design.corroboration()),
            "corroboration_probes": listed(design.corroboration(probes=True)),
            "disclosure": listed(design.disclosure()),
            "disclosure_probes": listed(design.disclosure(probes=True)),
            "checks": listed(design.checks()),
        },
        "gates": GATES,
    }


def run(
    directory: Path, seed=20260927, respondents=200, model_datasets=100, boundary_repetitions=25
):
    if not 0 <= seed < 2**32 - 200:
        raise ValueError("Use a nonnegative seed below 2**32-200")
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("Use an empty output directory; validation artifacts are immutable")
    directory.mkdir(parents=True, exist_ok=True)
    results = validate(seed, respondents, model_datasets, boundary_repetitions)
    value = {
        "plan": plan(seed, respondents, model_datasets, boundary_repetitions),
        "results": results,
        "gates": check_gates(results),
        "scope": "Synthetic respondents drawn from the specified observers; identifiability and model discrimination only; no agent or human behavior is validated",
    }
    raw = encoded(value)
    with (directory / "validation.json").open("xb") as stream:
        stream.write(raw)
    return {**value, "sha256": hashlib.sha256(raw).hexdigest()}
