"""Battery v3: coherence between stated and revealed belief (docs/battery-v3-design.md).

Pairs are (stated log-odds, revealed log-odds) per scenario, pooled over a configuration's
sessions. Coherence per configuration: r = alpha + beta s + e, with residual sd tau_c.

Primary: generality. Split the 30 surfaces into random halves; in each split, fit each
configuration's beta and tau_c on each half and correlate the configurations' values between the
halves; the statistic is the mean split-half correlation over splits, with a permutation p that
shuffles configurations within each surface.
"""

import numpy as np

from epistemics.dispositions import coherence, observers
from epistemics.dispositions.response import sample_reports

SPLITS = 200
PERMUTATIONS = 500


def line(pairs):
    s = np.array([p["stated"] for p in pairs])
    r = np.array([p["revealed"] for p in pairs])
    x = np.column_stack([np.ones_like(s), s])
    coef, *_ = np.linalg.lstsq(x, r, rcond=None)
    residual = r - x @ coef
    tau = float(np.sqrt(np.sum(residual**2) / max(len(r) - 2, 1)))
    return {"alpha": float(coef[0]), "beta": float(coef[1]), "tau_c": tau, "pairs": len(r)}


def surface_key(pair):
    return tuple(pair["surface"])


def split_half(by_config, rng, splits=SPLITS):
    """Mean split-half correlation of beta and of log tau_c across configurations."""
    surfaces = sorted({surface_key(p) for pairs in by_config.values() for p in pairs})
    configs = sorted(by_config)
    out = {"beta": [], "tau_c": []}
    for _ in range(splits):
        half = set(map(tuple, rng.permutation(surfaces)[: len(surfaces) // 2]))
        values = {"beta": ([], []), "tau_c": ([], [])}
        for c in configs:
            a = [p for p in by_config[c] if surface_key(p) in half]
            b = [p for p in by_config[c] if surface_key(p) not in half]
            if len(a) < 3 or len(b) < 3:
                continue
            fa, fb = line(a), line(b)
            values["beta"][0].append(fa["beta"])
            values["beta"][1].append(fb["beta"])
            values["tau_c"][0].append(np.log(max(fa["tau_c"], 1e-3)))
            values["tau_c"][1].append(np.log(max(fb["tau_c"], 1e-3)))
        for k in out:
            x, y = values[k]
            if len(x) >= 3 and np.std(x) > 0 and np.std(y) > 0:
                out[k].append(float(np.corrcoef(x, y)[0, 1]))
    return {k: float(np.mean(v)) if v else None for k, v in out.items()}


def shuffle_configs(by_config, rng):
    """Within each surface, permute which configuration each pair belongs to."""
    pooled = {}
    for c, pairs in by_config.items():
        for p in pairs:
            pooled.setdefault(surface_key(p), []).append((c, p))
    out = {c: [] for c in by_config}
    for rows in pooled.values():
        labels = [c for c, _ in rows]
        for label, (_, p) in zip(rng.permutation(labels), rows, strict=True):
            out[str(label)].append(p)
    return out


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
    order = sorted(ps, key=ps.get)
    running = 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, (len(order) - i) * ps[k]))
        result[k]["p_holm"] = running
    return result


# Simulation, for recovery and power: a configuration's sessions on designs a-f (one each), with
# its traits and a configuration x surface interaction on the revealed belief.
def simulate_config(truth, rng, interaction_sd, designs=coherence.DESIGNS):
    offsets = {}
    pairs = []
    for letter in designs:
        items = coherence.design(letter)
        kinds = np.asarray(items["kind"])
        reports = np.zeros(len(kinds))
        stated = {}
        for i in np.flatnonzero(kinds == "stated"):
            row = {k: items[k][i] for k in items}
            fill = {
                (0, kind, k): truth["default_acc"] if kind == "acc" else truth["default_rate"]
                for kind, k in coherence.unstated(row)
            }
            latent = observers.composite(coherence._observer_items([row], fill))[0]
            stated[int(items["scenario"][i])] = latent
            reports[i] = sample_reports(latent, truth["stated_sd"], rng)
        for i in np.flatnonzero(kinds == "revealed"):
            surface = (int(items["domain"][i]), int(items["source"][i]))
            offset = offsets.setdefault(surface, rng.normal(0, interaction_sd))
            s = stated[int(items["scenario"][i])]
            r = truth["alpha"] + truth["beta"] * s + offset + rng.normal(0, truth["tau_c"])
            p = 1 / (1 + np.exp(-r))
            reports[i] = np.clip(np.round(coherence.certainty_equivalent(p, truth["rho"])), 0, 100)
        for i in np.flatnonzero(kinds == "lottery"):
            ce = coherence.certainty_equivalent(items["lottery_p"][i], truth["rho"])
            reports[i] = np.clip(np.round(ce + rng.normal(0, 1.0)), 0, 100)
        pairs += coherence.fit_coherence(items, reports)["pairs"]
    return pairs


def draw_truth(rng, trait_sd):
    return {
        "alpha": float(rng.normal(0, 0.2)),
        "beta": float(np.clip(1 + rng.normal(0, trait_sd["beta"]), 0.2, 1.8)),
        "tau_c": float(np.exp(np.log(0.2) + rng.normal(0, trait_sd["log_tau"]))),
        "rho": float(np.exp(rng.normal(np.log(0.9), 0.2))),
        "stated_sd": 0.05,
        "default_acc": float(rng.choice([0.6, 0.7, 0.8])),
        "default_rate": float(rng.choice([0.2, 0.4])),
    }


def recovery(configs=60, seed=20261019, interaction_sd=0.1):
    """Per-configuration beta and tau_c from six sessions against their truths."""
    rng = np.random.default_rng(seed)
    truths, fits = [], []
    for _ in range(configs):
        truth = draw_truth(rng, {"beta": 0.25, "log_tau": 0.6})
        truths.append(truth)
        fits.append(line(simulate_config(truth, rng, interaction_sd)))
    result = {}
    for name, transform in (("beta", lambda v: v), ("tau_c", np.log)):
        t = transform(np.array([x[name] for x in truths]))
        f = transform(np.array([max(x[name], 1e-3) for x in fits]))
        result[name] = {
            "correlation": float(np.corrcoef(t, f)[0, 1]),
            "mae": float(np.mean(np.abs(t - f))),
        }
    return {"configs": configs, "interaction_sd": interaction_sd, "parameters": result}


SCENARIOS_POWER = {
    # Configuration traits against configuration x surface interaction on the revealed belief.
    "general": ({"beta": 0.15, "log_tau": 0.4}, 0.1),
    "general, strong interaction": ({"beta": 0.15, "log_tau": 0.4}, 0.3),
    "surface-bound": ({"beta": 0.0, "log_tau": 0.0}, 0.3),
    "none": ({"beta": 0.0, "log_tau": 0.0}, 0.0),
}


def power(datasets=100, configs=8, seed=20261020, splits=60, permutations=100):
    rng = np.random.default_rng(seed)
    result = {}
    for name, (trait_sd, interaction_sd) in SCENARIOS_POWER.items():
        passes, stats = 0, {"beta": [], "tau_c": []}
        for _ in range(datasets):
            by_config = {}
            for c in range(configs):
                truth = draw_truth(rng, trait_sd)
                by_config[str(c)] = simulate_config(truth, rng, interaction_sd)
            g = generality(by_config, rng, splits, permutations)
            for k in stats:
                stats[k].append(g[k]["split_half_r"])
            passes += any(
                g[k]["p_holm"] is not None and g[k]["p_holm"] < 0.05 and g[k]["split_half_r"] > 0
                for k in g
            )
        result[name] = {
            "pass_rate": passes / datasets,
            "median_split_half": {
                k: float(np.nanmedian(np.array(v, dtype=float))) for k, v in stats.items()
            },
            "datasets": datasets,
        }
    return {
        "schema_version": "epistemics.battery-v3-power.v1",
        "configs": configs,
        "result": result,
    }


def analyse(roots, seed=20261021):
    """Pooled coherence per configuration, by strength, stakes and load; and generality."""
    from epistemics.ledger import dispositions

    by_config, loaded, sessions = {}, {}, []
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or not record["module"].startswith("coherence-"):
                continue
            c = record["coherence"]
            target = loaded if record["variant"] == "v3-loaded" else by_config
            target.setdefault(record["configuration"], []).extend(c["pairs"])
            sessions.append(
                {
                    "configuration": record["configuration"],
                    "module": record["module"],
                    "variant": record["variant"],
                    **{k: c[k] for k in ("alpha", "beta", "tau_c", "mean_gap")},
                    "rho": c["calibration"]["rho"]["mean"],
                    "strong_stated_error": c.get("strong_stated_error"),
                }
            )
    configs = {}
    for config, pairs in by_config.items():
        entry = {"overall": line(pairs)}
        for strength in (0, 1, 2):
            chosen = [p for p in pairs if p["strength"] == strength]
            if len(chosen) >= 3:
                entry[f"strength_{strength}"] = line(chosen)
        weak = [p for p in pairs if p["strength"] == 2]
        for label, chosen in (
            ("stakes", [p for p in weak if p["stakes"]]),
            ("no_stakes", [p for p in weak if not p["stakes"]]),
        ):
            # Shift towards the goal-congruent hypothesis: signed by the stakes direction.
            if chosen:
                entry[f"{label}_revealed_minus_stated"] = float(
                    np.mean(
                        [(p["revealed"] - p["stated"]) * (p["stakes_dir"] or 1) for p in chosen]
                    )
                )
        if config in loaded:
            entry["loaded"] = line(loaded[config])
        configs[config] = entry
    rng = np.random.default_rng(seed)
    result = {
        "schema_version": "epistemics.battery-v3.v1",
        "sessions": sessions,
        "configurations": configs,
    }
    if len(by_config) >= 3:
        result["generality"] = generality(by_config, rng)
    return result
