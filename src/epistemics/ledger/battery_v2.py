"""Battery v2: the transfer test for general traits (docs/battery-v2-design.md).

Six abstract tasks, three formal cores in two surface stories each, crossed with six
configurations. For each trait, a cell holds the mean of the configuration's sessions in the task.

Primary test (per trait): a configuration's deviation from the other configurations on a held-out
task is predicted from its mean deviation on the other tasks (leave one task out). Transfer gain =
1 - MSE(prediction) / MSE(no deviation). The null shuffles which configuration is which within
each task, which removes consistency and keeps task effects; p is the share of shuffles whose gain
reaches the observed one. A primary trait passes if its gain is above 0 and its Holm-adjusted p is
below 0.05. Secondary: the same with both surfaces of the held-out task's core left out (far
transfer), and the gain from the twin surface alone (near transfer).
"""

import numpy as np

from epistemics.ledger import traits

# family: (formal core, surface, the named variant whose asked and probed sessions give priors)
TASKS = {
    "copying": ("dependence", "A", "urn2-named"),
    "echo": ("dependence", "B", "urn2-named"),
    "selection": ("withholding", "A", "urn2-named"),
    "hub": ("withholding", "B", "urn2-named"),
    "mismatch": ("uninformative", "A", "urn3-named"),
    "stale": ("uninformative", "B", "urn2-named"),
}
VARIANTS = {family: ("urn2-plain", named) for family, (_, _, named) in TASKS.items()}
CONFIGURATIONS = ("astra", "sol", "astra-low", "sol-low", "luna", "terra")
# Stated-applied fidelity was planned as primary but failed its recovery gate (58% passes against
# 80% at the reanalysis's effect size; docs/battery-v2-preregistration.md), so it is secondary.
PRIMARY = ("precision",)
SECONDARY = ("stated_applied_gap", "noticing_threshold")
# The traits the recovery study simulates, with Holm across both as when it ran.
RECOVERED = ("precision", "stated_applied_gap")
MIN_CONFIGS = MIN_TASKS = 5
PERMUTATIONS = 5000


def family_of(module):
    family = module.split("-", 1)[0]
    return family if family in TASKS and module.split("-", 1)[1].startswith("urn") else None


def session_rows(models):
    """Per-session trait values from the battery's sessions only."""
    rows = []
    for s in models["sessions"]:
        family = family_of(s["module"])
        if family is None or s["variant"] not in VARIANTS[family]:
            continue
        if s["configuration"] not in CONFIGURATIONS:
            continue
        means = s.get("means") or {}
        if means.get("report_sd"):
            rows.append(
                (s["configuration"], family, "precision", float(np.log(means["report_sd"])))
            )
        asked = s["module"].endswith(("-asked", "-probed")) and s["variant"] == TASKS[family][2]
        slots, stated = s.get("slot_means"), s.get("stated")
        if asked and slots and stated and all(stated[level] for level in (1, 2, 3)):
            gap = np.mean([abs(np.mean(stated[level]) - slots[level]) for level in (1, 2, 3)])
            rows.append((s["configuration"], family, "stated_applied_gap", float(gap)))
    return rows


def check_rows(checks):
    """Noticing thresholds from the per-structure fits (valid fits in the battery's format)."""
    from epistemics.structure_check import CATALOGUE

    rows = []
    for config, by_structure in ((checks or {}).get("checks") or {}).items():
        for family, check in by_structure.items():
            if family not in TASKS or config not in CONFIGURATIONS or not check.get("valid"):
                continue
            if check.get("format") != CATALOGUE[family]["format"]:
                continue
            rows.append((config, family, "noticing_threshold", float(check["theta"]["mean"])))
    return rows


def matrix(rows, trait):
    """Configurations × tasks cell means (NaN where missing)."""
    y = np.full((len(CONFIGURATIONS), len(TASKS)), np.nan)
    cells = {}
    for config, family, t, value in rows:
        if t == trait:
            cells.setdefault((config, family), []).append(value)
    for (config, family), values in cells.items():
        y[CONFIGURATIONS.index(config), list(TASKS).index(family)] = np.mean(values)
    return y


CORES = np.array([TASKS[f][0] for f in TASKS])
TWIN = np.array(
    [next(j for j, g in enumerate(TASKS) if g != f and TASKS[g][0] == TASKS[f][0]) for f in TASKS]
)


def deviations(y):
    """Each cell minus the mean of the other configurations in its task (NaN if none)."""
    present = ~np.isnan(y)
    total = np.nansum(y, axis=0, keepdims=True)
    count = present.sum(axis=0, keepdims=True)
    others = (total - np.where(present, y, 0)) / np.maximum(count - present, 1)
    d = y - others
    d[~present | (count - present < 1)] = np.nan
    return d


def gains(y):
    """Leave-one-task-out, leave-one-core-out and twin-only transfer gains."""
    d = deviations(y)
    out = {}
    for name in ("task", "core", "twin"):
        pred = np.full_like(d, np.nan)
        for t in range(d.shape[1]):
            if name == "task":
                train = [u for u in range(d.shape[1]) if u != t]
            elif name == "core":
                train = [u for u in range(d.shape[1]) if CORES[u] != CORES[t]]
            else:
                train = [TWIN[t]]
            block = d[:, train]
            has = ~np.isnan(block)
            pred[:, t] = np.where(
                has.any(axis=1), np.nansum(block, axis=1) / np.maximum(has.sum(axis=1), 1), np.nan
            )
        ok = ~np.isnan(d) & ~np.isnan(pred)
        denom = float(np.sum(d[ok] ** 2))
        out[name] = {
            "gain": float(1 - np.sum((d[ok] - pred[ok]) ** 2) / denom) if denom > 0 else None,
            "cells": int(ok.sum()),
            "sign_agreement": float(np.mean(np.sign(d[ok]) == np.sign(pred[ok])))
            if ok.any()
            else None,
        }
    return out


def shuffled(y, rng):
    """Within each task, permute the present values among the configurations that have them."""
    z = y.copy()
    for t in range(y.shape[1]):
        rows = np.flatnonzero(~np.isnan(y[:, t]))
        z[rows, t] = y[rng.permutation(rows), t]
    return z


def test(y, rng, permutations=PERMUTATIONS):
    observed = gains(y)
    null = {k: [] for k in observed}
    for _ in range(permutations):
        g = gains(shuffled(y, rng))
        for k in observed:
            null[k].append(g[k]["gain"])
    result = {}
    for k, v in observed.items():
        if v["gain"] is None:
            result[k] = {**v, "p": None}
            continue
        values = np.array([x for x in null[k] if x is not None])
        result[k] = {**v, "p": float((1 + np.sum(values >= v["gain"])) / (1 + len(values)))}
    return result


def holm(p_values):
    """Holm-adjusted p-values for a dict of name: p."""
    items = sorted((p, name) for name, p in p_values.items() if p is not None)
    adjusted, running = {}, 0.0
    for i, (p, name) in enumerate(items):
        running = max(running, min(1.0, (len(items) - i) * p))
        adjusted[name] = running
    return adjusted


def analyse(models, checks=None, seed=20261001):
    rows = session_rows(models) + check_rows(checks)
    rng = np.random.default_rng(seed)
    result = {}
    for trait in PRIMARY + SECONDARY:
        y = matrix(rows, trait)
        configs = int((~np.isnan(y)).any(axis=1).sum())
        tasks = int((~np.isnan(y)).any(axis=0).sum())
        entry = {
            "configurations": configs,
            "tasks": tasks,
            "cells": {
                f"{c}/{f}": (None if np.isnan(y[i, j]) else float(y[i, j]))
                for i, c in enumerate(CONFIGURATIONS)
                for j, f in enumerate(TASKS)
            },
            "sessions": sum(1 for r in rows if r[2] == trait),
            "role": "primary" if trait in PRIMARY else "secondary",
        }
        if configs >= MIN_CONFIGS and tasks >= MIN_TASKS:
            entry["tests"] = test(y, rng)
            mine = [
                {"configuration": c, "task": f, "value": v, "se": None}
                for c, f, t, v in rows
                if t == trait
            ]
            entry["consistency"] = (
                traits.gstudy(mine)["consistency"] if trait != "noticing_threshold" else None
            )
        else:
            entry["tests"] = None
        result[trait] = entry
    adjusted = holm({t: result[t]["tests"]["task"]["p"] for t in PRIMARY if result[t]["tests"]})
    for t in PRIMARY:
        tests = result[t]["tests"]
        if tests:
            tests["task"]["p_holm"] = adjusted.get(t)
            result[t]["passes"] = bool(
                tests["task"]["gain"] is not None
                and tests["task"]["gain"] > 0
                and adjusted.get(t, 1.0) < 0.05
            )
    return {
        "schema_version": "epistemics.battery-v2.v1",
        "tasks": {f: {"core": c, "surface": s} for f, (c, s, _) in TASKS.items()},
        "configurations": list(CONFIGURATIONS),
        "traits": result,
    }


# Recovery of the test through the real designs and per-session fits, at the design's size.
LADDER = {
    0: ("{f}-urn", "plain", 2),
    1: ("{f}-urn", "named", 1),
    2: ("{f}-urn-asked", "named", 1),
    3: ("{f}-urn-probed", "named", 1),
}


def _simulate_cell(args):
    """One configuration × task cell: five sessions through the real designs and fits."""
    from epistemics.disposition_tasks.analysis import CUE_MODELS
    from epistemics.disposition_tasks.render import items_for
    from epistemics.dispositions import fit, observers
    from epistemics.dispositions.response import sample_reports
    from epistemics.ledger.inclusion import TRUE_MAPPING, TWINS, logit

    family, log_tau, gap, seed = args
    rng = np.random.default_rng(seed)
    base = TWINS.get(family, family)
    mapping = TRUE_MAPPING[base]
    precision, gaps = [], []
    for rung, (template, _, count) in LADDER.items():
        module = template.format(f=family)
        items = items_for(module)
        model = CUE_MODELS[module]
        observer = {
            "dependence": observers.corroboration,
            "disclosure": observers.disclosure,
            "mismatch": observers.mismatch,
        }[model]
        for _ in range(count):
            applied = 1 / (1 + np.exp(-(logit(mapping) + 0.3 * rng.normal(size=5))))
            sd = float(np.exp(log_tau + 0.73 * rng.normal()))
            latent = observers.cue_observer(observer, items, applied, 1.0)
            if rung >= 2:
                # Stated rates depart from the applied priors by the session's gap.
                g = max(0.0, gap + 0.06 * rng.normal())
                stated = np.clip(applied + g * rng.choice([-1, 1], 5), 0.01, 0.99)
                said = observers.cue_observer(observer, items, stated, 1.0)
                latent = np.where(items["kind"] == "rate", said, latent)
            reports = sample_reports(latent, min(max(sd, 0.005), 3.0), rng)
            fitted = fit.fit_cues(model, items, reports)
            precision.append(float(np.log(fitted["parameters"]["report_sd"]["mean"])))
            if rung >= 2:
                implied = [s["implied"]["mean"] for s in fitted["slots"]]
                said_rates = [np.mean(s["stated"]) for s in fitted["slots"]]
                gaps.append(float(np.mean([abs(said_rates[k] - implied[k]) for k in (1, 2, 3)])))
    return float(np.mean(precision)), float(np.mean(gaps))


def recovery(seed=20261002, datasets=24, workers=8):
    """Pass rates of the primary test on synthetic studies with and without each trait."""
    from concurrent.futures import ProcessPoolExecutor

    rng = np.random.default_rng(seed)
    scenarios = {
        "no trait": (0.0, 0.0),
        "traits as estimated": (0.82, 0.06),
        "traits frontier-like": (0.49, 0.03),
    }
    jobs, keys = [], []
    for name, (s_precision, s_gap) in scenarios.items():
        for k in range(datasets):
            a_tau = rng.normal(0, s_precision, len(CONFIGURATIONS))
            a_gap = np.abs(rng.normal(0, s_gap, len(CONFIGURATIONS)))
            b_tau = rng.normal(-1.8, 0.33, len(TASKS))
            for i, _ in enumerate(CONFIGURATIONS):
                for j, family in enumerate(TASKS):
                    log_tau = b_tau[j] + a_tau[i] + rng.normal(0, 0.2)
                    gap = 0.02 + a_gap[i] + abs(rng.normal(0, 0.03))
                    jobs.append((family, float(log_tau), float(gap), int(rng.integers(2**31))))
                    keys.append((name, k, i, j))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        cells = list(pool.map(_simulate_cell, jobs, chunksize=4))
    out = {}
    test_rng = np.random.default_rng(seed + 1)
    for name in scenarios:
        passes = {t: 0 for t in RECOVERED}
        for k in range(datasets):
            y = {t: np.full((len(CONFIGURATIONS), len(TASKS)), np.nan) for t in RECOVERED}
            for (n, kk, i, j), (prec, gap) in zip(keys, cells, strict=True):
                if n == name and kk == k:
                    y["precision"][i, j] = prec
                    y["stated_applied_gap"][i, j] = gap
            ps = {t: test(y[t], test_rng, permutations=1000)["task"] for t in RECOVERED}
            adjusted = holm({t: ps[t]["p"] for t in RECOVERED})
            for t in RECOVERED:
                passes[t] += ps[t]["gain"] > 0 and adjusted[t] < 0.05
        out[name] = {t: passes[t] / datasets for t in RECOVERED}
    return {
        "schema_version": "epistemics.battery-v2-recovery.v1",
        "seed": seed,
        "datasets_per_scenario": datasets,
        "pass_rates": out,
        "scope": (
            "Synthetic studies of six configurations × six tasks × five sessions through the real "
            "item designs, observers and per-session fits: log report noise = task + "
            "configuration + interaction (0.2) + session (0.73); stated rates depart from applied "
            "priors by a configuration gap plus noise. Noticing is not simulated here (see the "
            "per-structure recovery and the surrogate power)."
        ),
    }
