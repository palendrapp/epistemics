"""Capacity battery: pilot summaries and the recovery studies for the revised designs
(docs/capacity-battery-design.md).

Part A (load modules): per configuration, module and load level, the fitted report noise, the
weight on the structure-neglecting answer and the share of answers within 1.5 points of exact,
with the load slope and the model-free noise between repeated cases. Part B (matched-strength
audit records): the implied rate of the never-named structure at each likelihood-ratio level,
beside the rate an ideal observer would infer from the same audit record, and the uptake fit
(model 0.8): the fraction of the ideal revision applied.
"""

import json
from pathlib import Path

import numpy as np

from epistemics.disposition_tasks import urn
from epistemics.disposition_tasks.analysis import CUE_MODELS, LOAD_MODELS
from epistemics.disposition_tasks.render import LOAD_MODULES, LONG_LOAD_MODULES, items_for
from epistemics.disposition_tasks.urn import VIG_SCALES
from epistemics.dispositions import fit, observers
from epistemics.dispositions.response import sample_reports
from epistemics.dispositions.validation import GATES, REPORT_PRIOR, cell_edges, draw
from epistemics.ledger import dispositions

VIG_MODULES = ("copying-urn", "selection-urn", "mismatch-urn")


def ideal(module, variant):
    """Per likelihood-ratio level, the mean over cases of the ideal observer's rate
    (urn.vig_ideal: half the prior on no structure, the rest uniform over the rate)."""
    items = items_for(module)
    values = urn.vig_ideals(module, variant, items)
    has = values > 0
    levels, _ = VIG_SCALES[variant]
    return {
        lr: float(values[has & (items["slot"] == slot)].mean()) for slot, lr in enumerate(levels)
    }


def uptake(record):
    """The uptake fit of a vigilance session: from its collection when the battery fitted it
    (tasks 0.17 on), otherwise refitted from its responses with the current model."""
    if record.get("uptake"):
        return {**record["uptake"], "source": "collection"}
    items = {k: np.asarray(v) for k, v in record["items"].items()}
    values = urn.vig_ideals(record["module"], record["variant"], items)
    result = fit.fit_uptake(CUE_MODELS[record["module"]], items, record["responses"], values)
    return {
        "parameters": result["parameters"],
        "ignores_probability": result["ignores_probability"],
        "source": "reanalysis",
    }


def curve(record):
    """The joint load curve of a load session: from its collection when the battery fitted it
    (tasks 0.17 on), otherwise refitted from its responses with the current model."""
    if record["load"].get("curve"):
        return {**record["load"]["curve"], "source": "collection"}
    items = {k: np.asarray(v) for k, v in record["items"].items()}
    result = fit.fit_load_curve(LOAD_MODELS[record["module"]], items, record["responses"])
    return {"parameters": result["parameters"], "source": "reanalysis"}


def usage(root):
    """Input tokens per run: from the collection log, or from each run's own execution record
    when the collection was interrupted before writing its log."""
    root = Path(root)
    if (root / "execution.json").exists():
        execution = json.loads((root / "execution.json").read_text())
        return {
            e["run_id"]: e["usage"]["input_tokens"]
            for e in execution.get("executions", [])
            if e.get("usage")
        }
    result = {}
    for path in (root / "collections").glob("*/execution.json"):
        run = json.loads(path.read_text())
        if run.get("usage"):
            result[path.parent.name] = run["usage"]["input_tokens"]
    return result


def pilot(roots):
    load_rows, vig_rows = [], []
    for root in roots:
        tokens = usage(root)
        for record in dispositions.extract(root):
            if not record.get("verified"):
                continue
            base = {
                "configuration": record["configuration"],
                "module": record["module"],
                "variant": record["variant"],
                "input_tokens": tokens.get(record["run_id"]),
            }
            if record["module"].endswith("-load"):
                load = record["load"]
                load_rows.append(
                    {
                        **base,
                        "levels": [
                            {
                                "load": lv["load"],
                                "readings": lv["readings"],
                                "report_sd": lv["report_sd"]["mean"],
                                "eta": lv["eta"]["mean"],
                                "exact_share": lv["exact_share"],
                            }
                            for lv in load["levels"]
                        ],
                        "load_slope": load["load_slope"],
                        "eta_slope": load["eta_slope"],
                        "repeat_noise": load["repeat_noise"],
                        "curve": curve(record),
                    }
                )
            elif record["variant"] in VIG_SCALES:
                implied = [s["implied"]["mean"] for s in record["slot_fits"]]
                levels = VIG_SCALES[record["variant"]][0]
                vig_rows.append(
                    {
                        **base,
                        "implied_by_lr": dict(zip(levels, implied, strict=True)),
                        "ideal_by_lr": ideal(record["module"], record["variant"]),
                        "uptake": uptake(record),
                    }
                )
    return {
        "schema_version": "epistemics.capacity-pilot.v2",
        "load": load_rows,
        "vigilance": vig_rows,
    }


def tables(result):
    lines = [
        "| Configuration | Module | Readings | Noise τ | Neglect weight η | Exact within 1.5 points | Tokens |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in result["load"]:
        for lv in r["levels"]:
            lines.append(
                f"| {r['configuration']} | {r['module']} | {lv['readings']} | {lv['report_sd']:.3f} | "
                f"{lv['eta']:.2f} | {lv['exact_share']:.0%} | "
                f"{(r['input_tokens'] or 0) / 1e6:.2f}M |"
            )
        lines.append(
            f"| {r['configuration']} | {r['module']} | slope | {r['load_slope']:.2f} | "
            f"{r['eta_slope']:.2f} | repeat noise {r['repeat_noise']:.3f} | |"
        )
        c = r["curve"]["parameters"]
        k, lam = c["load_slope"], c["eta_slope"]
        lines.append(
            f"| {r['configuration']} | {r['module']} | curve | "
            f"{k['mean']:.2f} ({k['interval_90'][0]:.1f}–{k['interval_90'][1]:.1f}) | "
            f"{lam['mean']:.3f} ({lam['interval_90'][0]:.3f}–{lam['interval_90'][1]:.3f}) | | |"
        )
    lines += [
        "",
        "| Configuration | Module | Variant | Implied rate (ideal) by likelihood ratio | Uptake (90%) "
        "| P(ignores) | Tokens |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in result["vigilance"]:
        values = ", ".join(
            f"{k}: {v:.2f} ({r['ideal_by_lr'][k]:.2f})" for k, v in r["implied_by_lr"].items()
        )
        u = r["uptake"]["parameters"]["uptake"]
        lines.append(
            f"| {r['configuration']} | {r['module']} | {r['variant']} | {values} | "
            f"{u['mean']:.2f} ({u['interval_90'][0]:.2f}–{u['interval_90'][1]:.2f}) | "
            f"{r['uptake']['ignores_probability']:.2f} | "
            f"{(r['input_tokens'] or 0) / 1e6:.2f}M |"
        )
    return "\n".join(lines)


# Recovery studies for the revised designs (model 0.8, design 0.10). Gates are fixed before the
# studies run, at the house standards for a primary parameter: correlation 0.9 and 90% interval
# coverage 0.8 (whole grid cells, so over-coverage is not screened), for respondents in the agent
# noise band. Classification: respondents who ignore the records (uptake 0) and respondents who
# take up at least 0.4 must be told apart by P(ignores) > 0.5 in 85% of cases. Each study is run
# at one, two and three sessions per cell (pooled), which fixes the sessions the battery needs.
UPTAKE_PRIOR = {"baseline": (0.0, 0.15), "uptake": (0.0, 1.2)}
UPTAKE_GATES = {"correlation": 0.9, "mae": 0.15, "coverage_90": 0.8, "classification": 0.85}
# Load: noise log-linear and neglect weight linear in the level. The slopes are the traits; gates
# as for a primary parameter, with the neglect slope as secondary (correlation 0.85).
LOAD_GATES = {"load_slope_correlation": 0.9, "eta_slope_correlation": 0.85, "coverage_90": 0.8}
SESSIONS = (1, 2, 3)
WORKERS = 8


def pooled(items, sessions):
    """A design repeated for several sessions of one cell, fitted as one data set."""
    return {k: np.tile(np.asarray(v), sessions) for k, v in items.items()}


def _uptake_case(job):
    module, variant, truth, seed, sessions = job
    rng = np.random.default_rng(seed)
    items = items_for(module)
    values = urn.vig_ideals(module, variant, items)
    model = CUE_MODELS[module]
    forecast = ~np.isin(items["kind"], ("probe", "rate"))
    delta = np.clip(truth["baseline"] + truth["uptake"] * values, 0.0, 1.0)
    latent = fit.REPORT_MODELS[model](items, delta, truth["gamma"])
    means = latent + truth["bias"] * forecast
    reports = np.concatenate(
        [sample_reports(means, truth["report_sd"], rng) for _ in range(sessions)]
    )
    result = fit.fit_uptake(model, pooled(items, sessions), reports, np.tile(values, sessions))
    return {
        "truth": truth,
        "mean": result["parameters"]["uptake"]["mean"],
        "interval": result["parameters"]["uptake"]["interval_90"],
        "baseline": result["parameters"]["baseline"]["mean"],
        "ignores_probability": result["ignores_probability"],
    }


def _uptake_metrics(rows, classify):
    limit = GATES["agent_noise_band"]["report_sd"]
    agent = [r for r in rows if r["truth"]["report_sd"] <= limit]
    truth = np.array([r["truth"]["uptake"] for r in agent])
    mean = np.array([r["mean"] for r in agent])
    lower, upper = cell_edges(fit.UPTAKE)
    lo = np.array([lower[np.searchsorted(fit.UPTAKE, r["interval"][0])] for r in agent])
    hi = np.array([upper[np.searchsorted(fit.UPTAKE, r["interval"][1])] for r in agent])
    classified = [
        (r["ignores_probability"] > 0.5) == (r["truth"]["uptake"] == 0)
        for r in classify
        if r["truth"]["report_sd"] <= limit
    ]
    metrics = {
        "respondents": len(agent),
        "correlation": float(np.corrcoef(truth, mean)[0, 1]),
        "mae": float(np.mean(np.abs(mean - truth))),
        "coverage_90": float(np.mean((lo <= truth) & (truth <= hi))),
        "baseline_mae": float(
            np.mean([abs(r["baseline"] - r["truth"]["baseline"]) for r in agent])
        ),
        "classification": float(np.mean(classified)),
        "classified": len(classified),
    }
    metrics["passed"] = bool(
        metrics["correlation"] >= UPTAKE_GATES["correlation"]
        and metrics["mae"] <= UPTAKE_GATES["mae"]
        and metrics["coverage_90"] >= UPTAKE_GATES["coverage_90"]
        and metrics["classification"] >= UPTAKE_GATES["classification"]
    )
    return metrics


def _needed(by_sessions):
    passing = [k for k, m in by_sessions.items() if m["passed"]]
    return min(passing) if passing else None


def uptake_recovery(respondents=100, seed=20261007, variant="urn2-vig2", sessions=SESSIONS):
    """Synthetic respondents with known baseline and uptake, through the real audit designs.
    The same respondents are refitted at each number of sessions."""
    from concurrent.futures import ProcessPoolExecutor

    rng = np.random.default_rng(seed)
    base = {k: v for k, v in REPORT_PRIOR.items() if k != "disposition"}
    result = {}
    with ProcessPoolExecutor(WORKERS) as pool:
        for module in VIG_MODULES:
            general = [draw(rng, base) | draw(rng, UPTAKE_PRIOR) for _ in range(respondents)]
            quarter = respondents // 4
            ignoring = [
                draw(rng, base) | draw(rng, UPTAKE_PRIOR) | {"uptake": 0.0} for _ in range(quarter)
            ]
            taking = [
                draw(rng, base) | draw(rng, {**UPTAKE_PRIOR, "uptake": (0.4, 1.2)})
                for _ in range(quarter)
            ]
            truths = general + ignoring + taking
            seeds = rng.integers(2**31, size=len(truths)).tolist()
            by_sessions = {}
            for k in sessions:
                jobs = [(module, variant, t, s, k) for t, s in zip(truths, seeds, strict=True)]
                rows = list(pool.map(_uptake_case, jobs))
                by_sessions[k] = _uptake_metrics(rows[:respondents], rows[respondents:])
            result[module] = {"sessions": by_sessions, "sessions_needed": _needed(by_sessions)}
    return result


def _load_truth(rng, levels):
    low = float(np.exp(rng.uniform(np.log(0.01), np.log(0.2))))
    high = float(np.exp(rng.uniform(np.log(low), np.log(1.0))))
    sd = np.exp(np.linspace(np.log(low), np.log(high), levels))
    eta = np.linspace(0, rng.uniform(0, 0.6), levels)
    return {
        "load_sd": sd.tolist(),
        "load_eta": eta.tolist(),
        "bias": float(rng.uniform(-0.2, 0.2)),
        "load_slope": float((np.log(high) - np.log(low)) / (levels - 1)),
        "eta_slope": float(eta[-1] / (levels - 1)),
    }


def _load_case(job):
    module, truth, seed, sessions = job
    rng = np.random.default_rng(seed)
    model = LOAD_MODELS[module]
    items = items_for(module)
    exact, neglect = observers.load_answers(model, items)
    level = np.asarray(items["load"])
    eta = np.asarray(truth["load_eta"])[level]
    sd = np.asarray(truth["load_sd"])[level]
    means = (1 - eta) * exact + eta * neglect + truth["bias"]
    reports = np.concatenate([sample_reports(means, sd, rng) for _ in range(sessions)])
    both = pooled(items, sessions)
    curve = fit.fit_load_curve(model, both, reports)["parameters"]
    per_level = fit.fit_load(model, both, reports, curve=False)
    return {
        "truth": truth,
        "curve": {n: curve[n] for n in ("load_slope", "eta_slope")},
        "per_level": {n: per_level[n] for n in ("load_slope", "eta_slope")},
    }


def _load_metrics(rows):
    metrics = {}
    for name, grid in (("load_slope", fit.CURVE_SLOPE), ("eta_slope", fit.CURVE_ETA_SLOPE)):
        truth = np.array([r["truth"][name] for r in rows])
        curve = [r["curve"][name] for r in rows]
        mean = np.array([c["mean"] for c in curve])
        lower, upper = cell_edges(grid)
        lo = np.array([lower[np.searchsorted(grid, c["interval_90"][0])] for c in curve])
        hi = np.array([upper[np.searchsorted(grid, c["interval_90"][1])] for c in curve])
        per_level = np.array([r["per_level"][name] for r in rows])
        metrics[name] = {
            "correlation": float(np.corrcoef(truth, mean)[0, 1]),
            "mae": float(np.mean(np.abs(truth - mean))),
            "coverage_90": float(np.mean((lo <= truth) & (truth <= hi))),
            "per_level_correlation": float(np.corrcoef(truth, per_level)[0, 1]),
            "per_level_mae": float(np.mean(np.abs(truth - per_level))),
        }
    metrics["passed"] = bool(
        metrics["load_slope"]["correlation"] >= LOAD_GATES["load_slope_correlation"]
        and metrics["eta_slope"]["correlation"] >= LOAD_GATES["eta_slope_correlation"]
        and metrics["load_slope"]["coverage_90"] >= LOAD_GATES["coverage_90"]
        and metrics["eta_slope"]["coverage_90"] >= LOAD_GATES["coverage_90"]
    )
    return metrics


def load_recovery(respondents=100, seed=20261008, sessions=SESSIONS):
    """Synthetic respondents with known noise and neglect slopes, through each load design (the
    pilot's three-level ladders for comparison, and the four-level ladders). Two estimators: the
    joint curve fit (model 0.8, gated) and the pilot's line through per-level estimates."""
    from concurrent.futures import ProcessPoolExecutor

    rng = np.random.default_rng(seed)
    result = {}
    with ProcessPoolExecutor(WORKERS) as pool:
        for module in LOAD_MODULES:
            levels = int(np.max(items_for(module)["load"])) + 1
            truths = [_load_truth(rng, levels) for _ in range(respondents)]
            seeds = rng.integers(2**31, size=respondents).tolist()
            by_sessions = {}
            for k in sessions:
                jobs = [(module, t, s, k) for t, s in zip(truths, seeds, strict=True)]
                by_sessions[k] = _load_metrics(list(pool.map(_load_case, jobs)))
            result[module] = {
                "levels": levels,
                "respondents": respondents,
                "revised": module in LONG_LOAD_MODULES,
                "sessions": by_sessions,
                "sessions_needed": _needed(by_sessions),
            }
    return result


def recovery(respondents=100, load_respondents=100):
    uptake_part = uptake_recovery(respondents)
    load_part = load_recovery(load_respondents)
    revised = [r for m, r in load_part.items() if m in LONG_LOAD_MODULES]
    return {
        "schema_version": "epistemics.capacity-recovery.v2",
        "uptake_gates": UPTAKE_GATES,
        "load_gates": LOAD_GATES,
        "sessions": list(SESSIONS),
        "uptake": uptake_part,
        "load": load_part,
        # Sessions per cell at which every revised design passes (None: not within those tried).
        "sessions_needed": None
        if any(r["sessions_needed"] is None for r in list(uptake_part.values()) + revised)
        else max(r["sessions_needed"] for r in list(uptake_part.values()) + revised),
    }
