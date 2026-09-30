"""Battery v3.1: implicit threshold decisions (docs/battery-v3-1-design.md).

Decision rows are (stated log-odds, act, consequence class, surface), pooled over a
configuration's sessions. Per configuration: the threshold model's theta per class and kappa
(dispositions.decisions.fit_thresholds). The traits are the action bias (theta_balanced) and the
consequence sensitivity (theta_costly - theta_cheap).

Primary: generality, as for battery v3. Split the surfaces into random halves; in each split, fit
each configuration's traits on each half and correlate the configurations' values between the
halves; the statistic is the mean split-half correlation over splits, with a permutation p that
shuffles configurations within each surface, Holm-corrected across the two traits. It counts only
if at least three configurations depart from the median.
"""

import numpy as np

from epistemics.dispositions import coherence, decisions, observers
from epistemics.dispositions.response import sample_reports
from epistemics.ledger.battery_v3 import shuffle_configs, surface_key

SPLITS = 200
PERMUTATIONS = 500
TRAITS = ("action_bias", "sensitivity")
# A configuration departs from the median by more than this (log-odds) on a trait.
DEPARTURE = 0.25


def traits(rows):
    fit = decisions.fit_thresholds(rows)
    return {"action_bias": fit["theta_balanced"]["mean"], "sensitivity": fit["sensitivity"]["mean"]}


def split_half(by_config, rng, splits=SPLITS):
    """Mean split-half correlation of the action bias and of the consequence sensitivity."""
    surfaces = sorted({surface_key(r) for rows in by_config.values() for r in rows})
    configs = sorted(by_config)
    out = {k: [] for k in TRAITS}
    for _ in range(splits):
        half = set(map(tuple, rng.permutation(surfaces)[: len(surfaces) // 2]))
        values = {k: ([], []) for k in TRAITS}
        for c in configs:
            a = [r for r in by_config[c] if surface_key(r) in half]
            b = [r for r in by_config[c] if surface_key(r) not in half]
            if len(a) < 6 or len(b) < 6:
                continue
            ta, tb = traits(a), traits(b)
            for k in TRAITS:
                values[k][0].append(ta[k])
                values[k][1].append(tb[k])
        for k in TRAITS:
            x, y = values[k]
            if len(x) >= 3 and np.std(x) > 0 and np.std(y) > 0:
                out[k].append(float(np.corrcoef(x, y)[0, 1]))
    return {k: float(np.mean(v)) if v else None for k, v in out.items()}


def generality(by_config, rng, splits=SPLITS, permutations=PERMUTATIONS):
    observed = split_half(by_config, rng, splits)
    null = {k: [] for k in observed}
    for _ in range(permutations):
        g = split_half(shuffle_configs(by_config, rng), rng, max(splits // 10, 20))
        for k in null:
            if g[k] is not None:
                null[k].append(g[k])
    result = {}
    for k, v in observed.items():
        values = np.array(null[k])
        p = None if v is None else float((1 + np.sum(values >= v)) / (1 + len(values)))
        result[k] = {"split_half_r": v, "p": p}
    ps = {k: r["p"] for k, r in result.items() if r["p"] is not None}
    running = 0.0
    for i, k in enumerate(sorted(ps, key=ps.get)):
        running = max(running, min(1.0, (len(ps) - i) * ps[k]))
        result[k]["p_holm"] = running
    return result


# Simulation, for recovery and power: a configuration's sessions on the given designs, with its
# thresholds and a configuration x surface interaction on the threshold (a surface-specific
# reading of the described consequences).
def simulate_config(truth, rng, interaction_sd, designs=decisions.DESIGNS):
    offsets = {}
    rows = []
    for letter in designs:
        items = decisions.design(letter)
        kinds = np.asarray(items["kind"])
        reports = np.zeros(len(kinds))
        latent = {}
        for i in np.flatnonzero((kinds == "stated") | (kinds == "anchor")):
            row = {k: items[k][i] for k in items}
            fill = {
                (0, kind, k): truth["default_acc"] if kind == "acc" else truth["default_rate"]
                for kind, k in coherence.unstated(row)
            }
            belief = observers.composite(coherence._observer_items([row], fill))[0]
            latent[int(items["scenario"][i])] = belief
            if kinds[i] == "stated":
                reports[i] = sample_reports(belief, truth["stated_sd"], rng)
        for i in np.flatnonzero((kinds == "decision") | (kinds == "anchor")):
            surface = (int(items["domain"][i]), int(items["source"][i]))
            offset = offsets.setdefault(surface, rng.normal(0, interaction_sd))
            theta = truth["thresholds"][int(items["cls"][i])] + offset
            theta -= (
                truth.get("stakes", 0.0) * int(items["stakes"][i]) * int(items["stakes_dir"][i])
            )
            z = truth["kappa"] * (latent[int(items["scenario"][i])] - theta)
            p = decisions.LAPSE / 2 + (1 - decisions.LAPSE) * decisions._phi(np.array(z))
            reports[i] = float(rng.random() < p)
        rows += decisions.trials(items, reports)
    return rows


def draw_truth(rng, trait_sd, stakes_sd=0.0):
    bias = float(rng.normal(0, trait_sd["action_bias"]))
    sensitivity = float(1.5 + rng.normal(0, trait_sd["sensitivity"]))
    return {
        "thresholds": [bias - sensitivity / 2, bias, bias + sensitivity / 2],
        "kappa": float(np.exp(rng.uniform(np.log(1.0), np.log(16.0)))),
        "stakes": float(rng.normal(0, stakes_sd)),
        "stated_sd": 0.05,
        "default_acc": float(rng.choice([0.6, 0.7, 0.8])),
        "default_rate": float(rng.choice([0.2, 0.4])),
    }


RECOVERY_SD = {"action_bias": 0.6, "sensitivity": 0.8}


def recovery(configs=100, seed=20261031, interaction_sd=0.1, designs=decisions.DESIGNS):
    """Per-configuration action bias, consequence sensitivity and kappa from one session per
    design against their truths: correlation, mean absolute error and 90% interval coverage."""
    rng = np.random.default_rng(seed)
    truths, fits = [], []
    for _ in range(configs):
        truth = draw_truth(rng, RECOVERY_SD, stakes_sd=0.5)
        truths.append(truth)
        fits.append(decisions.fit_thresholds(simulate_config(truth, rng, interaction_sd, designs)))
    t = {
        "action_bias": np.array([x["thresholds"][1] for x in truths]),
        "sensitivity": np.array([x["thresholds"][2] - x["thresholds"][0] for x in truths]),
        "kappa": np.log([x["kappa"] for x in truths]),
    }
    names = {"action_bias": "theta_balanced", "sensitivity": "sensitivity", "kappa": "kappa"}
    result = {}
    for name, key in names.items():
        mean = np.array([f[key]["mean"] for f in fits])
        if name == "kappa":
            mean = np.log(mean)
        lo = np.array([f[key]["interval_90"][0] for f in fits])
        hi = np.array([f[key]["interval_90"][1] for f in fits])
        truth = t[name] if name != "kappa" else np.exp(t[name])
        result[name] = {
            "correlation": float(np.corrcoef(t[name], mean)[0, 1]),
            "mae": float(np.mean(np.abs(t[name] - mean))),
            "coverage_90": float(np.mean((truth >= lo) & (truth <= hi))),
        }
    passed = all(
        result[k]["correlation"] >= 0.9 and result[k]["coverage_90"] >= 0.8 for k in TRAITS
    )
    return {
        "schema_version": "epistemics.battery-v31-recovery.v1",
        "configs": configs,
        "designs": list(designs),
        "interaction_sd": interaction_sd,
        "trait_sd": RECOVERY_SD,
        "parameters": result,
        "passed": passed,
    }


SCENARIOS_POWER = {
    # Configuration traits against configuration x surface interaction on the threshold.
    "general": ({"action_bias": 0.5, "sensitivity": 0.6}, 0.2),
    "general, strong interaction": ({"action_bias": 0.5, "sensitivity": 0.6}, 0.5),
    "surface-bound": ({"action_bias": 0.0, "sensitivity": 0.0}, 0.5),
    "none": ({"action_bias": 0.0, "sensitivity": 0.0}, 0.0),
}


WORKERS = 8


def _power_dataset(args):
    trait_sd, interaction_sd, configs, seed, splits, permutations = args
    rng = np.random.default_rng(seed)
    by_config = {
        str(c): simulate_config(draw_truth(rng, trait_sd), rng, interaction_sd)
        for c in range(configs)
    }
    g = generality(by_config, rng, splits, permutations)
    passed = any(
        g[k]["p_holm"] is not None and g[k]["p_holm"] < 0.05 and g[k]["split_half_r"] > 0 for k in g
    )
    return passed, {k: g[k]["split_half_r"] for k in TRAITS}


def power(datasets=100, configs=8, seed=20261032, splits=40, permutations=100):
    from concurrent.futures import ProcessPoolExecutor

    seeds = np.random.SeedSequence(seed).spawn(len(SCENARIOS_POWER) * datasets)
    result = {}
    with ProcessPoolExecutor(WORKERS) as pool:
        for n, (name, (trait_sd, interaction_sd)) in enumerate(SCENARIOS_POWER.items()):
            jobs = [
                (trait_sd, interaction_sd, configs, seeds[n * datasets + d], splits, permutations)
                for d in range(datasets)
            ]
            outcomes = list(pool.map(_power_dataset, jobs))
            stats = {k: [o[1][k] for o in outcomes] for k in TRAITS}
            result[name] = {
                "pass_rate": sum(o[0] for o in outcomes) / datasets,
                "median_split_half": {
                    k: float(np.nanmedian(np.array(v, dtype=float))) for k, v in stats.items()
                },
                "datasets": datasets,
            }
    return {
        "schema_version": "epistemics.battery-v31-power.v1",
        "configs": configs,
        "designs": list(decisions.DESIGNS),
        "splits": splits,
        "permutations": permutations,
        "result": result,
    }


def analyse(roots, seed=20261033):
    """Pooled thresholds per configuration, by situation strength and with the stakes shift;
    normative checks; and generality with its guard."""
    from epistemics.ledger import dispositions

    by_config, sessions = {}, []
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or not record["module"].startswith("decision-"):
                continue
            d = record["decisions"]
            by_config.setdefault(record["configuration"], []).extend(d["trials"])
            fit = d["fit"]
            sessions.append(
                {
                    "configuration": record["configuration"],
                    "module": record["module"],
                    "variant": record["variant"],
                    "action_bias": fit["theta_balanced"]["mean"],
                    "sensitivity": fit["sensitivity"]["mean"],
                    "kappa": fit["kappa"]["mean"],
                    "act_share": fit["act_share"],
                }
            )
    configs = {}
    for config, rows in by_config.items():
        overall = decisions.fit_thresholds(rows, stakes=True)
        anchors = {}
        for r in rows:
            if r["anchor"]:
                anchors.setdefault(f"{1 / (1 + np.exp(-r['stated'])):.2f}", []).append(r["act"])
        entry = {
            "overall": overall,
            "ordered": overall["theta_cheap"]["mean"]
            < overall["theta_balanced"]["mean"]
            < overall["theta_costly"]["mean"],
            # Anchors: the share acting at each fixed ideal belief (balanced consequences).
            "anchor_act_share": {k: float(np.mean(v)) for k, v in sorted(anchors.items())},
        }
        for strength in (0, 1, 2):
            chosen = [r for r in rows if r["strength"] == strength and not r["anchor"]]
            if len(chosen) >= 6:
                fit = decisions.fit_thresholds(chosen)
                entry[f"strength_{strength}"] = {
                    k: fit[k] for k in ("kappa", "theta_balanced", "sensitivity", "decisions")
                }
        configs[config] = entry
    result = {
        "schema_version": "epistemics.battery-v31.v1",
        "sessions": sessions,
        "configurations": configs,
    }
    if len(by_config) >= 3:
        rng = np.random.default_rng(seed)
        result["generality"] = generality(by_config, rng)
        spread = {}
        for name, key in (("action_bias", "theta_balanced"), ("sensitivity", "sensitivity")):
            values = np.array([e["overall"][key]["mean"] for e in configs.values()])
            spread[name] = {
                "between_configuration_sd": float(np.std(values)),
                "departing_configurations": int(
                    np.sum(np.abs(values - np.median(values)) > DEPARTURE)
                ),
            }
            result["generality"][name]["interpretable"] = (
                spread[name]["departing_configurations"] >= 3
            )
        result["spread"] = spread
    return result
