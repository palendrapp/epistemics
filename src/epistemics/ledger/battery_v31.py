"""Batteries v3.1 and v3.2: implicit threshold decisions (docs/battery-v3-1-design.md,
docs/battery-v3-2-design.md).

Decision rows are (stated log-odds, act, consequence class, surface), pooled over a
configuration's sessions. Per configuration: the threshold model's theta per class and kappa
(dispositions.decisions.fit_thresholds). The traits are the action bias (theta_balanced), the
consequence sensitivity (v3.1: theta_costly - theta_cheap; v3.2: theta_mild_costly -
theta_mild_cheap) and, in v3.2, the welfare weight ((theta_welfare_hold - theta_welfare_act) / 2).

Primary: generality, as for battery v3. Split the surfaces into random halves; in each split, fit
each configuration's traits on each half and correlate the configurations' values between the
halves; the statistic is the mean split-half correlation over splits, with a permutation p that
shuffles configurations within each surface, Holm-corrected across the traits. It counts only
if at least three configurations depart from the median.

Since v3.2 (after the v3.1 power analysis), each half's trait values are residualised on the
configurations' pooled log kappa before correlating: with bounded flat priors, a less decisive
configuration's thresholds are estimated closer to 0 on both halves, so a general difference in
kappa would otherwise pass as generality of the contrasts.
"""

import numpy as np

from epistemics.dispositions import coherence, decisions, observers
from epistemics.dispositions.response import sample_reports
from epistemics.ledger.battery_v3 import shuffle_configs, surface_key

SPLITS = 200
PERMUTATIONS = 500
TRAITS = {
    "v31": ("action_bias", "sensitivity"),
    "v32": ("action_bias", "sensitivity", "welfare_weight"),
}
PREFIX = {"v31": "decision-", "v32": "decision2-"}
# A configuration departs from the median by more than this (log-odds) on a trait.
DEPARTURE = 0.25


def traits(rows, scheme="v31"):
    fit = decisions.fit_thresholds(rows, scheme=scheme)
    out = {"action_bias": fit["theta_balanced"]["mean"]}
    for name in TRAITS[scheme][1:]:
        out[name] = fit[name]["mean"]
    return out


def _residual(values, covariate):
    x = np.column_stack([np.ones(len(covariate)), covariate])
    coef, *_ = np.linalg.lstsq(x, values, rcond=None)
    return values - x @ coef


def split_half(by_config, rng, splits=SPLITS, scheme="v31", adjust_kappa=True):
    """Mean split-half correlation of each trait across configurations."""
    names = TRAITS[scheme]
    surfaces = sorted({surface_key(r) for rows in by_config.values() for r in rows})
    configs = sorted(by_config)
    log_kappa = {
        c: np.log(decisions.fit_thresholds(by_config[c], scheme=scheme)["kappa"]["mean"])
        for c in configs
    }
    out = {k: [] for k in names}
    for _ in range(splits):
        half = set(map(tuple, rng.permutation(surfaces)[: len(surfaces) // 2]))
        values = {k: ([], []) for k in names}
        kept = []
        for c in configs:
            a = [r for r in by_config[c] if surface_key(r) in half]
            b = [r for r in by_config[c] if surface_key(r) not in half]
            if len(a) < 6 or len(b) < 6:
                continue
            kept.append(c)
            ta, tb = traits(a, scheme), traits(b, scheme)
            for k in names:
                values[k][0].append(ta[k])
                values[k][1].append(tb[k])
        z = np.array([log_kappa[c] for c in kept])
        for k in names:
            x, y = np.array(values[k][0]), np.array(values[k][1])
            if adjust_kappa and len(x) >= 4 and np.std(z) > 1e-9:
                x, y = _residual(x, z), _residual(y, z)
            if len(x) >= 3 and np.std(x) > 1e-9 and np.std(y) > 1e-9:
                out[k].append(float(np.corrcoef(x, y)[0, 1]))
    return {k: float(np.mean(v)) if v else None for k, v in out.items()}


def generality(
    by_config, rng, splits=SPLITS, permutations=PERMUTATIONS, scheme="v31", adjust_kappa=True
):
    observed = split_half(by_config, rng, splits, scheme, adjust_kappa)
    null = {k: [] for k in observed}
    for _ in range(permutations):
        g = split_half(
            shuffle_configs(by_config, rng), rng, max(splits // 10, 20), scheme, adjust_kappa
        )
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
def simulate_config(truth, rng, interaction_sd, designs=decisions.DESIGNS, scheme="v31"):
    offsets = {}
    rows = []
    for letter in designs:
        items = decisions.design(letter, scheme)
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


def draw_truth(rng, trait_sd, stakes_sd=0.0, scheme="v31"):
    bias = float(rng.normal(0, trait_sd["action_bias"]))
    if scheme == "v31":
        sensitivity = float(1.5 + rng.normal(0, trait_sd["sensitivity"]))
        thresholds = [bias - sensitivity / 2, bias, bias + sensitivity / 2]
    else:
        sensitivity = float(1.0 + rng.normal(0, trait_sd["sensitivity"]))
        welfare = float(rng.normal(0, trait_sd["welfare_weight"]))
        offset = float(rng.normal(0, 0.3))  # an action offset specific to the welfare classes
        thresholds = [
            bias - sensitivity / 2,
            bias,
            bias + sensitivity / 2,
            bias + offset - welfare,
            bias + offset + welfare,
        ]
    return {
        "thresholds": thresholds,
        "kappa": float(np.exp(rng.uniform(np.log(1.0), np.log(16.0)))),
        "stakes": float(rng.normal(0, stakes_sd)),
        "stated_sd": 0.05,
        "default_acc": float(rng.choice([0.6, 0.7, 0.8])),
        "default_rate": float(rng.choice([0.2, 0.4])),
    }


RECOVERY_SD = {"action_bias": 0.6, "sensitivity": 0.8, "welfare_weight": 0.6}


def true_traits(truth, scheme):
    t = truth["thresholds"]
    out = {"action_bias": t[1], "sensitivity": t[2] - t[0]}
    if scheme == "v32":
        out["welfare_weight"] = (t[4] - t[3]) / 2
    return out


def recovery(
    configs=100, seed=20261031, interaction_sd=0.1, designs=decisions.DESIGNS, scheme="v31"
):
    """Per-configuration traits and kappa from one session per design against their truths:
    correlation, mean absolute error and 90% interval coverage."""
    rng = np.random.default_rng(seed)
    truths, fits = [], []
    for _ in range(configs):
        truth = draw_truth(rng, RECOVERY_SD, stakes_sd=0.5, scheme=scheme)
        truths.append(truth)
        rows = simulate_config(truth, rng, interaction_sd, designs, scheme)
        # As in the pooled analysis: with the stakes shift.
        fits.append(decisions.fit_thresholds(rows, stakes=True, scheme=scheme))
    keys = {"action_bias": "theta_balanced", **{k: k for k in TRAITS[scheme][1:]}}
    result = {}
    for name, key in {**keys, "kappa": "kappa"}.items():
        if name == "kappa":
            t = np.log([x["kappa"] for x in truths])
            mean = np.log([f["kappa"]["mean"] for f in fits])
            truth = np.exp(t)
        else:
            t = np.array([true_traits(x, scheme)[name] for x in truths])
            mean = np.array([f[key]["mean"] for f in fits])
            truth = t
        lo = np.array([f[key]["interval_90"][0] for f in fits])
        hi = np.array([f[key]["interval_90"][1] for f in fits])
        result[name] = {
            "correlation": float(np.corrcoef(t, mean)[0, 1]),
            "mae": float(np.mean(np.abs(t - mean))),
            "coverage_90": float(np.mean((truth >= lo - 1e-9) & (truth <= hi + 1e-9))),
        }
    passed = all(
        result[k]["correlation"] >= 0.9 and result[k]["coverage_90"] >= 0.8 for k in TRAITS[scheme]
    )
    return {
        "schema_version": f"epistemics.battery-{scheme}-recovery.v1",
        "scheme": scheme,
        "configs": configs,
        "designs": list(designs),
        "interaction_sd": interaction_sd,
        "trait_sd": RECOVERY_SD,
        "parameters": result,
        "passed": passed,
    }


SCENARIOS_POWER = {
    # Configuration traits against configuration x surface interaction on the threshold. In
    # every scenario kappa differs between configurations (1 to 16).
    "general": ({"action_bias": 0.5, "sensitivity": 0.6, "welfare_weight": 0.5}, 0.2),
    "general, strong interaction": (
        {"action_bias": 0.5, "sensitivity": 0.6, "welfare_weight": 0.5},
        0.5,
    ),
    "surface-bound": ({"action_bias": 0.0, "sensitivity": 0.0, "welfare_weight": 0.0}, 0.5),
    "none": ({"action_bias": 0.0, "sensitivity": 0.0, "welfare_weight": 0.0}, 0.0),
}

WORKERS = 8


def _power_dataset(args):
    trait_sd, interaction_sd, configs, seed, splits, permutations, scheme, adjust = args
    rng = np.random.default_rng(seed)
    by_config = {
        str(c): simulate_config(
            draw_truth(rng, trait_sd, scheme=scheme), rng, interaction_sd, scheme=scheme
        )
        for c in range(configs)
    }
    g = generality(by_config, rng, splits, permutations, scheme, adjust)
    passed = any(
        g[k]["p_holm"] is not None and g[k]["p_holm"] < 0.05 and g[k]["split_half_r"] > 0 for k in g
    )
    return passed, {k: g[k]["split_half_r"] for k in TRAITS[scheme]}


def power(
    datasets=100,
    configs=8,
    seed=20261032,
    splits=40,
    permutations=100,
    scheme="v31",
    adjust_kappa=True,
):
    from concurrent.futures import ProcessPoolExecutor

    seeds = np.random.SeedSequence(seed).spawn(len(SCENARIOS_POWER) * datasets)
    result = {}
    with ProcessPoolExecutor(WORKERS) as pool:
        for n, (name, (trait_sd, interaction_sd)) in enumerate(SCENARIOS_POWER.items()):
            jobs = [
                (
                    trait_sd,
                    interaction_sd,
                    configs,
                    seeds[n * datasets + d],
                    splits,
                    permutations,
                    scheme,
                    adjust_kappa,
                )
                for d in range(datasets)
            ]
            outcomes = list(pool.map(_power_dataset, jobs))
            stats = {k: [o[1][k] for o in outcomes] for k in TRAITS[scheme]}
            result[name] = {
                "pass_rate": sum(o[0] for o in outcomes) / datasets,
                "median_split_half": {
                    k: float(np.nanmedian(np.array(v, dtype=float))) for k, v in stats.items()
                },
                "datasets": datasets,
            }
    return {
        "schema_version": f"epistemics.battery-{scheme}-power.v1",
        "scheme": scheme,
        "configs": configs,
        "designs": list(decisions.DESIGNS),
        "splits": splits,
        "permutations": permutations,
        "adjust_kappa": adjust_kappa,
        "result": result,
    }


def analyse(roots, seed=20261033, scheme="v31"):
    """Pooled thresholds per configuration, by situation strength and with the stakes shift;
    normative checks; and generality with its guard."""
    from epistemics.ledger import dispositions

    names = decisions.SCHEMES[scheme]["classes"]
    by_config, sessions = {}, []
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or not record["module"].startswith(PREFIX[scheme]):
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
                    **{k: fit[k]["mean"] for k in TRAITS[scheme][1:]},
                    "kappa": fit["kappa"]["mean"],
                    "act_share": fit["act_share"],
                }
            )
    configs = {}
    for config, rows in by_config.items():
        overall = decisions.fit_thresholds(rows, stakes=True, scheme=scheme)
        anchors = {}
        for r in rows:
            if r["anchor"]:
                key = f"{names[r['cls']]} {1 / (1 + np.exp(-r['stated'])):.2f}"
                anchors.setdefault(key, []).append(r["act"])
        acts = {}
        for r in rows:
            acts.setdefault(names[r["cls"]], []).append(
                [round(float(1 / (1 + np.exp(-r["stated"]))), 2), r["act"]]
            )
        entry = {
            "overall": overall,
            # Normative order among the graded classes.
            "ordered": overall[f"theta_{names[0]}"]["mean"]
            < overall["theta_balanced"]["mean"]
            < overall[f"theta_{names[2]}"]["mean"],
            "anchor_act_share": {k: float(np.mean(v)) for k, v in sorted(anchors.items())},
            # (stated probability, act) per class, sorted: the raw decisions behind the fit.
            "decisions_by_class": {k: sorted(v) for k, v in acts.items()},
        }
        for strength in (0, 1, 2):
            chosen = [r for r in rows if r["strength"] == strength and not r["anchor"]]
            if len(chosen) >= 6:
                fit = decisions.fit_thresholds(chosen, scheme=scheme)
                entry[f"strength_{strength}"] = {
                    k: fit[k] for k in ("kappa", "theta_balanced", *TRAITS[scheme][1:], "decisions")
                }
        configs[config] = entry
    result = {
        "schema_version": f"epistemics.battery-{scheme}.v1",
        "scheme": scheme,
        "sessions": sessions,
        "configurations": configs,
    }
    if len(by_config) >= 3:
        rng = np.random.default_rng(seed)
        result["generality"] = generality(by_config, rng, scheme=scheme)
        spread = {}
        for name in TRAITS[scheme]:
            key = "theta_balanced" if name == "action_bias" else name
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
