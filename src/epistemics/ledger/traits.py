"""Which candidate traits are general? A generalizability study over the sessions collected so far.

Exploratory reanalysis (docs/traits-2026-09-29.md). For each candidate trait, every session gives
one value, measured in one task (a hidden structure in one format). The value is decomposed as

    y = μ + config_c + task_t + (config × task)_ct + session noise,

with the effects random. Task effects are expected (some tasks are harder, some cues plainer) and
do not count against a trait. A general trait needs configurations to keep their relative
position across tasks: a configuration effect large relative to the interaction. Consistency is
ρ = σ²_config / (σ²_config + σ²_config×task), the share of a configuration's task-specific
deviation that it carries to every task.

Transfer is also scored directly: each configuration's deviation from the other configurations
in one held-out task is predicted from its average deviation in the other tasks
(leave-one-task-out), and compared with predicting no deviation (the task's population mean).
"""

import json

import numpy as np

from epistemics.ledger import inclusion_joint as joint

EDGE = 0.02  # Priors are clipped to [2%, 98%] before taking log-odds.


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), EDGE, 1 - EDGE)
    return np.log(p) - np.log1p(-p)


# Tasks: a hidden structure in one format. Each (module, variant) maps to a task and a rung:
# "open" sessions (the structure not named or not asked about) measure only report precision
# and evidence weight; "named" sessions (the structure named and its rate asked or implied by the
# full mechanism statement) also measure the default, cue sensitivity and stated-applied gap.
def task_of(module, variant):
    family = module.split("-")[0]
    names = {
        "corroboration": "relay",
        "disclosure": "disclosure",
        "copying": "copying",
        "selection": "selection",
        "mismatch": "mismatch",
    }
    if family not in names or "range" in module or module == "checks":
        return None, None
    structure = names[family]
    if module in ("corroboration", "disclosure"):
        return f"{structure} · paired", "named" if variant == "paired" else "open"
    if module.endswith("-cues"):
        return f"{structure} · formal", "named"
    if module.endswith("-dossier"):
        return f"{structure} · dossier", "named"
    if module.endswith(("-asked", "-probed")) and not module.startswith(
        ("copying", "selection", "mismatch")
    ):
        return f"{structure} · dossier", "named"
    if module.endswith("-unprompted"):
        return f"{structure} · dossier", "open"
    # Urn tasks: only the corrected texts measure priors (copying and selection urn2, mismatch
    # urn3); every version measures precision.
    current = {"copying": "urn2-named", "selection": "urn2-named", "mismatch": "urn3-named"}
    if variant == "urn3-rated":
        return None, None
    asked = module.endswith(("-asked", "-probed"))
    rung = "named" if asked and variant == current[structure] else "open"
    return f"{structure} · urn", rung


def session_values(s):
    """Candidate trait values from one ledger session."""
    task, rung = task_of(s["module"], s["variant"])
    if task is None or (s.get("order_policy") not in (None, "random")):
        return task, {}
    means = s.get("means") or {}
    out = {}
    if means.get("report_sd"):
        out["precision"] = float(np.log(means["report_sd"]))
    if means.get("gamma") is not None:
        out["evidence_weight"] = float(means["gamma"])
    if rung == "named":
        if "disposition" in means:
            out["missing_rate_default"] = float(logit(means["disposition"]))
        slots = s.get("slot_means")
        if slots:
            out["missing_rate_default"] = float(logit(slots[2]))
            out["cue_sensitivity"] = float(logit(slots[4]) - logit(slots[0]))
            stated = s.get("stated")
            if stated and all(stated[level] for level in (1, 2, 3)):
                out["stated_applied_gap"] = float(
                    np.mean([abs(np.mean(stated[level]) - slots[level]) for level in (1, 2, 3)])
                )
    return task, out


TRAITS = {
    "precision": "log report noise (lower is more precise)",
    "evidence_weight": "evidence weight γ (1 is Bayesian)",
    "missing_rate_default": "prior for a named structure whose rate is not given, uninformative "
    "description (log-odds)",
    "cue_sensitivity": "log-odds range of the prior from the most reassuring to the most "
    "suggestive description",
    "stated_applied_gap": "mean gap between stated and applied base rates at the ambiguous levels",
    "noticing_threshold": "prompting needed before it considers the structure (rungs; per-structure "
    "second-layer fits)",
}


def collect(models, checks=None):
    """Rows (trait, configuration, task, value, se) from ledger sessions and structure checks."""
    rows = []
    for s in models["sessions"]:
        task, values = session_values(s)
        for trait, value in values.items():
            rows.append(
                {
                    "trait": trait,
                    "configuration": s["configuration"],
                    "task": task,
                    "value": value,
                    "se": None,
                    "session": s["id"],
                }
            )
    for config, by_structure in ((checks or {}).get("checks") or {}).items():
        for structure, check in by_structure.items():
            if not check.get("valid"):
                continue
            lo, hi = check["theta"]["interval_90"]
            rows.append(
                {
                    "trait": "noticing_threshold",
                    "configuration": config,
                    "task": f"{structure} · {check.get('format', '')}",
                    "value": check["theta"]["mean"],
                    "se": (hi - lo) / 3.29,
                    "session": None,
                }
            )
    return rows


def log_sd_target(log_s, n, ss):
    """Log posterior of a log standard deviation: n zero-mean normal terms with sum of squares ss,
    a half-normal prior with scale 1 (standardized units) and the log-scale Jacobian."""
    s = np.exp(log_s)
    return -n * np.log(s) - 0.5 * ss / s**2 - 0.5 * s**2 + log_s


def gstudy(rows, iterations=20000, burn=5000, chains=4, seed=20260929):
    """Crossed random effects by Gibbs sampling, with half-normal (scale 1 SD of y) priors on the
    standard deviations. Rows with a known se use it as their error; others share σ_session."""
    y = np.array([r["value"] for r in rows], dtype=float)
    scale = float(y.std()) or 1.0
    z = (y - y.mean()) / scale
    configs = sorted({r["configuration"] for r in rows})
    tasks = sorted({r["task"] for r in rows})
    cells = sorted({(r["configuration"], r["task"]) for r in rows})
    ci = np.array([configs.index(r["configuration"]) for r in rows])
    ti = np.array([tasks.index(r["task"]) for r in rows])
    ki = np.array([cells.index((r["configuration"], r["task"])) for r in rows])
    known = np.array([r["se"] is not None for r in rows])
    se = np.array([(r["se"] or 0.0) / scale for r in rows])
    rng = np.random.default_rng(seed)
    names = ("config", "task", "interaction", "session")
    all_draws = []
    for _ in range(chains):
        mu, a, b, ab = 0.0, np.zeros(len(configs)), np.zeros(len(tasks)), np.zeros(len(cells))
        log_sd = np.log(np.full(4, 0.5))
        steps = np.full(4, 0.3)
        draws = []
        for t in range(iterations):
            sd = np.exp(log_sd)
            var_e = np.where(known, np.maximum(se, 1e-3) ** 2, sd[3] ** 2)
            w = 1 / var_e
            r = z - a[ci] - b[ti] - ab[ki]
            mu = rng.normal((w * r).sum() / w.sum(), np.sqrt(1 / w.sum()))
            for eff, idx, s_ in ((a, ci, sd[0]), (b, ti, sd[1]), (ab, ki, sd[2])):
                resid = z - mu - a[ci] - b[ti] - ab[ki] + eff[idx]
                prec = np.bincount(idx, w, len(eff)) + 1 / s_**2
                mean = np.bincount(idx, w * resid, len(eff)) / prec
                eff[:] = rng.normal(mean, np.sqrt(1 / prec))
            residual = (z - mu - a[ci] - b[ti] - ab[ki])[~known]
            sums = [(len(e), float((e**2).sum())) for e in (a, b, ab)]
            sums.append((len(residual), float((residual**2).sum())))
            for j, (n, ss) in enumerate(sums):
                if j == 3 and known.all():
                    continue
                proposal = log_sd[j] + rng.normal(0, steps[j])
                if np.log(rng.random()) < log_sd_target(proposal, n, ss) - log_sd_target(
                    log_sd[j], n, ss
                ):
                    log_sd[j] = proposal
            if t >= burn and t % 5 == 0:
                draws.append(np.concatenate([[mu], np.exp(log_sd), a]))
        all_draws.append(np.array(draws))
    chains_arr = np.array(all_draws)
    flat = chains_arr.reshape(-1, chains_arr.shape[-1])
    sds = flat[:, 1:5] * scale
    rho = sds[:, 0] ** 2 / (sds[:, 0] ** 2 + sds[:, 2] ** 2)
    watched = [1, 3, *range(5, flat.shape[1])]  # config and interaction SDs, config effects
    return {
        "configurations": configs,
        "tasks": tasks,
        "sessions": int((~known).sum()),
        "cells": len(cells),
        "sd": {n: joint.interval(sds[:, i]) for i, n in enumerate(names)},
        "consistency": joint.interval(rho),
        "config_effects": {
            c: joint.interval(flat[:, 5 + i] * scale) for i, c in enumerate(configs)
        },
        "rhat_max": float(np.max(joint.rhat(chains_arr[:, :, watched]))),
    }


def loto(rows):
    """Leave-one-task-out: a configuration's deviation from the other configurations in a task,
    predicted from its mean deviation in the other tasks, against predicting none."""
    cell = {}
    for r in rows:
        cell.setdefault((r["configuration"], r["task"]), []).append(r["value"])
    means = {k: float(np.mean(v)) for k, v in cell.items()}
    tasks = sorted({t for _, t in means})
    configs = sorted({c for c, _ in means})

    def deviation(c, t):
        others = [means[(o, t)] for o in configs if o != c and (o, t) in means]
        return means[(c, t)] - np.mean(others) if others and (c, t) in means else None

    rows_out = []
    for c in configs:
        for t in tasks:
            held = deviation(c, t)
            if held is None:
                continue
            rest = [deviation(c, u) for u in tasks if u != t]
            rest = [d for d in rest if d is not None]
            if not rest:
                continue
            predicted = float(np.mean(rest))
            rows_out.append(
                {"configuration": c, "task": t, "observed": held, "predicted": predicted}
            )
    if not rows_out:
        return None
    obs = np.array([r["observed"] for r in rows_out])
    pred = np.array([r["predicted"] for r in rows_out])
    mse_trait, mse_none = float(np.mean((obs - pred) ** 2)), float(np.mean(obs**2))
    signed = [r for r in rows_out if abs(r["predicted"]) > 1e-9 and abs(r["observed"]) > 1e-9]
    return {
        "cells": len(rows_out),
        "rmse_trait": float(np.sqrt(mse_trait)),
        "rmse_no_deviation": float(np.sqrt(mse_none)),
        "gain": 1 - mse_trait / mse_none if mse_none > 0 else None,
        "sign_agreement": (
            sum(np.sign(r["observed"]) == np.sign(r["predicted"]) for r in signed) / len(signed)
            if signed
            else None
        ),
        "rows": rows_out,
    }


def analyse(models, checks=None):
    rows = collect(models, checks)
    result = {}
    for trait, description in TRAITS.items():
        mine = [r for r in rows if r["trait"] == trait]
        if len({r["configuration"] for r in mine}) < 2 or len({r["task"] for r in mine}) < 2:
            continue
        result[trait] = {
            "description": description,
            "gstudy": gstudy(mine),
            "transfer": loto(mine),
        }
    return {
        "schema_version": "epistemics.traits.v1",
        "traits": result,
        "scope": (
            "Exploratory reanalysis of verified ledger sessions (random case order only; urn "
            "priors from the corrected texts only) and of the per-structure second-layer fits in "
            "the structure checks. Configuration effects are estimated from few configurations "
            "and should be read as a planning input, not as trait estimates."
        ),
    }


def table(result):
    lines = [
        "| Trait | Configurations | Tasks | Sessions | SD config | SD config × task | SD task | "
        "SD session | Consistency ρ | Transfer gain | Sign agreement |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    f = lambda x: f"{x['mean']:.2f} [{x['interval_90'][0]:.2f}, {x['interval_90'][1]:.2f}]"  # noqa: E731
    for trait, r in result["traits"].items():
        g, t = r["gstudy"], r["transfer"] or {}
        g_session = g["sd"]["session"]["mean"]
        gain = t.get("gain")
        sign = t.get("sign_agreement")
        lines.append(
            f"| {trait} | {len(g['configurations'])} | {len(g['tasks'])} | {g['sessions']} | "
            f"{g['sd']['config']['mean']:.2f} | {g['sd']['interaction']['mean']:.2f} | "
            f"{g['sd']['task']['mean']:.2f} | "
            f"{'—' if not g['sessions'] else f'{g_session:.2f}'} | {f(g['consistency'])} | "
            f"{'—' if gain is None else f'{gain:.2f}'} ({t.get('cells', 0)} cells) | "
            f"{'—' if sign is None else f'{sign:.2f}'} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    ledger = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "output/ledger.json"))
    models = ledger["models"]
    print(table(analyse(models, models.get("structure_checks"))))
