"""Second layer, joint fit: mapping, inclusion and a stated-rate channel sampled together.

The two-stage fit in `inclusion` plugs in the mapping μ estimated from fully scaffolded sessions,
so the uncertainty in μ is ignored and the cue weight's intervals are too narrow. Here μ (five
levels and a spread ω per family), the inclusion parameters (θ, w, σ) and a stated-rate noise τ are
sampled together by adaptive random-walk Metropolis, with uniform priors on bounded scales:

- logit μ_l in [logit 0.01, logit 0.99]; log ω in [log 0.05, log 2];
- θ in [−1, 4] (one, or one per family); w in [0, 1.5]; log σ in [log 0.05, log 2];
- log τ in [log 0.02, log 2], for stated rates on the log-odds scale.

Stated base rates enter under one of three hypotheses:
- "considered": a stated rate reflects the mapping μ_l whether or not the structure is applied in
  the session's forecasts (so a session can state a rate it does not use);
- "applied": a stated rate reflects the prior the forecasts apply (0 when not included);
- "mixture": each session's stated rates are its applied priors with probability φ (stated–applied
  fidelity) and reflect the mapping otherwise; φ is uniform on [0, 1].

Stated rates enter only at the three ambiguous levels (mildly reassuring, irrelevant, mildly
suggestive) by default. At the extreme levels the applied priors sit near 0 and 1, where the
log-odds scale magnifies differences of a point or two between a whole-percentage stated rate and
the fitted prior; with all five levels, those differences dominated the stated channel (recorded
in docs/structure-inclusion-model.md). Sharing variants and stated-rate hypotheses are compared
by WAIC over sessions.
"""

import numpy as np

from epistemics.dispositions.response import logsumexp
from epistemics.ledger.inclusion import (
    GRID,
    IRRELEVANT,
    LEVEL_NOISE,
    NODES,
    WEIGHTS,
    cell_masses,
    fit_mapping,
    logit,
    phi,
)

FAMILIES = ("relay", "disclosure")
BOUNDS = {
    "logit_mu": (float(logit(0.01)), float(logit(0.99))),
    "log_omega": (np.log(0.05), np.log(2.0)),
    "theta": (-1.0, 4.0),
    "w": (0.0, 1.5),
    "log_sigma": (np.log(0.05), np.log(2.0)),
    "log_tau": (np.log(0.02), np.log(2.0)),
}
LOG_WEIGHTS = np.log(WEIGHTS)
STATED_FLOOR = 0.005  # Whole-percentage stated rates are clipped to [0.5%, 99.5%] for log-odds.
STATED_LEVELS = (1, 2, 3)  # The ambiguous levels; see the module docstring.
GRID_LOGIT = logit(np.clip(GRID, STATED_FLOOR, 1 - STATED_FLOOR))


class Layout:
    """Positions of the parameters in the sampled vector."""

    def __init__(self, families, variant, stated_model="considered"):
        self.families = list(families)
        self.variant = variant
        self.stated_model = stated_model
        names, bounds = [], []
        for fam in self.families:
            names += [f"logit_mu_{fam}_{level}" for level in range(5)] + [f"log_omega_{fam}"]
            bounds += [BOUNDS["logit_mu"]] * 5 + [BOUNDS["log_omega"]]
        thetas = (
            [f"theta_{fam}" for fam in self.families] if variant == "theta_by_family" else ["theta"]
        )
        names += thetas + ["w", "log_sigma", "log_tau"]
        bounds += [BOUNDS["theta"]] * len(thetas) + [
            BOUNDS["w"],
            BOUNDS["log_sigma"],
            BOUNDS["log_tau"],
        ]
        if stated_model == "mixture":
            names.append("phi")
            bounds.append((0.0, 1.0))
        self.names = names
        self.index = {n: i for i, n in enumerate(names)}
        self.low = np.array([b[0] for b in bounds])
        self.high = np.array([b[1] for b in bounds])

    def unpack(self, x):
        out = {}
        for fam in self.families:
            i = self.index[f"logit_mu_{fam}_0"]
            out[fam] = {
                "logit_mu": x[i : i + 5],
                "omega": float(np.exp(x[self.index[f"log_omega_{fam}"]])),
                "theta": float(x[self.index.get(f"theta_{fam}", self.index.get("theta"))]),
            }
        out["w"] = float(x[self.index["w"]])
        out["sigma"] = float(np.exp(x[self.index["log_sigma"]]))
        out["tau"] = float(np.exp(x[self.index["log_tau"]]))
        if "phi" in self.index:
            out["phi"] = float(x[self.index["phi"]])
        return out


def prepare(sessions_by_family, stated_levels=STATED_LEVELS):
    """Arrays per family: rung, grid likelihoods (n×5×21) and stated rates (n×5, NaN if absent
    or outside stated_levels)."""
    data = {}
    for fam, rows in sessions_by_family.items():
        salience = np.array([s for s, _, _ in rows], dtype=float)
        likelihoods = np.array([lik for _, lik, _ in rows], dtype=float)
        stated = np.full((len(rows), 5), np.nan)
        for i, (_, _, st) in enumerate(rows):
            if st is not None:
                stated[i] = np.clip(np.asarray(st, dtype=float), STATED_FLOOR, 1 - STATED_FLOOR)
        outside = [level for level in range(5) if level not in stated_levels]
        stated[:, outside] = np.nan
        data[fam] = {"salience": salience, "likelihoods": likelihoods, "stated": stated}
    return data


def normal_logpdf(x, mean, sd):
    return -0.5 * ((x - mean) / sd) ** 2 - np.log(sd) - 0.5 * np.log(2 * np.pi)


def session_loglik(params, data, stated_model="considered"):
    """Per-session log-likelihood, keyed by family."""
    if stated_model == "mixture":
        applied = session_loglik(params, data, "applied")
        considered = session_loglik(params, data, "considered")
        share = min(max(params["phi"], 1e-12), 1 - 1e-12)
        return {
            fam: np.logaddexp(np.log(share) + applied[fam], np.log1p(-share) + considered[fam])
            for fam in applied
        }
    result = {}
    for fam, d in data.items():
        p = params[fam]
        mu = 1 / (1 + np.exp(-p["logit_mu"]))
        masses = cell_masses(mu, np.full(5, p["omega"]))  # level × grid
        L, stated, salience = d["likelihoods"], d["stated"], d["salience"]
        has = ~np.isnan(stated)
        z = np.where(has, logit(np.where(has, stated, 0.5)), 0.0)
        if stated_model == "applied":
            # Stated rate reflects the applied prior: its density at each grid value.
            dens = np.exp(normal_logpdf(z[:, :, None], GRID_LOGIT[None, None, :], params["tau"]))
            dens = np.where(has[:, :, None], dens, 1.0)
            A = np.einsum("nlg,lg,nlg->nl", L, masses, dens)
            B = L[:, :, 0] * dens[:, :, 0]
            extra = np.zeros(len(salience))
        else:
            A = np.einsum("nlg,lg->nl", L, masses)
            B = L[:, :, 0]
            extra = np.where(has, normal_logpdf(z, p["logit_mu"][None, :], params["tau"]), 0.0).sum(
                axis=1
            )
        cue = p["logit_mu"] - p["logit_mu"][IRRELEVANT]
        arg = (
            salience[:, None, None]
            + params["w"] * cue[None, None, :]
            + params["sigma"] * NODES[None, :, None]
            - p["theta"]
        )
        pi = phi(arg / LEVEL_NOISE)  # n × Q × 5
        levels = pi * A[:, None, :] + (1 - pi) * B[:, None, :]
        per_node = np.log(levels + 1e-300).sum(axis=-1) + LOG_WEIGHTS[None, :]
        result[fam] = logsumexp(per_node, axis=1) + extra
    return result


def log_target(x, layout, data, stated_model):
    if np.any(x < layout.low) or np.any(x > layout.high):
        return -np.inf, None
    per = session_loglik(layout.unpack(x), data, stated_model)
    total = sum(v.sum() for v in per.values())
    return float(total), per


def start_point(layout, data, rng):
    x = np.empty(len(layout.names))
    for fam in layout.families:
        full = data[fam]["likelihoods"][data[fam]["salience"] == 3]
        mu, omega = fit_mapping(full)
        i = layout.index[f"logit_mu_{fam}_0"]
        x[i : i + 5] = logit(mu)
        x[layout.index[f"log_omega_{fam}"]] = np.log(omega)
    for name in layout.names:
        if name.startswith("theta"):
            x[layout.index[name]] = 1.0
    if "phi" in layout.index:
        x[layout.index["phi"]] = 0.5
    x[layout.index["w"]] = 0.3
    x[layout.index["log_sigma"]] = np.log(0.5)
    x[layout.index["log_tau"]] = np.log(0.3)
    x = x + rng.normal(0, 0.05, len(x))
    return np.clip(x, layout.low + 1e-6, layout.high - 1e-6)


def sample(
    sessions_by_family,
    variant="shared",
    stated_model="considered",
    chains=4,
    iterations=6000,
    burn=2000,
    seed=20260928,
    stated_levels=STATED_LEVELS,
):
    """Adaptive random-walk Metropolis; returns draws, per-session log-likelihoods and summaries."""
    data = prepare(sessions_by_family, stated_levels)
    layout = Layout(data, variant, stated_model)
    rng = np.random.default_rng(seed)
    dim = len(layout.names)
    all_draws, all_pointwise, rhat_input = [], [], []
    for _ in range(chains):
        x = start_point(layout, data, rng)
        current, per = log_target(x, layout, data, stated_model)
        cov = np.eye(dim) * 0.01
        history = []
        draws, pointwise = [], []
        for t in range(iterations):
            if t >= 500 and t % 250 == 0:
                recent = np.array(history[-2000:])
                cov = np.cov(recent.T) * (2.38**2 / dim) + np.eye(dim) * 1e-6
            proposal = rng.multivariate_normal(x, cov)
            value, new_per = log_target(proposal, layout, data, stated_model)
            if np.log(rng.random()) < value - current:
                x, current, per = proposal, value, new_per
            history.append(x.copy())
            if t >= burn and t % 5 == 0:
                draws.append(x.copy())
                pointwise.append(np.concatenate([per[f] for f in layout.families]))
        all_draws.append(np.array(draws))
        all_pointwise.append(np.array(pointwise))
        rhat_input.append(np.array(draws))
    draws = np.concatenate(all_draws)
    pointwise = np.concatenate(all_pointwise)
    return summarise(layout, draws, np.array(rhat_input), pointwise, variant, stated_model, data)


def rhat(chains):
    """Split-free Gelman–Rubin statistic per parameter; chains: chains × draws × dim."""
    m, n = chains.shape[:2]
    means = chains.mean(axis=1)
    within = chains.var(axis=1, ddof=1).mean(axis=0)
    between = n * means.var(axis=0, ddof=1)
    var = (n - 1) / n * within + between / n
    return np.sqrt(var / within)


def waic(pointwise):
    """WAIC on the deviance scale from draws × sessions log-likelihoods, with pointwise elpd."""
    lppd = logsumexp(pointwise, axis=0) - np.log(pointwise.shape[0])
    p_waic = pointwise.var(axis=0, ddof=1)
    elpd = lppd - p_waic
    return {
        "waic": float(-2 * elpd.sum()),
        "p_waic": float(p_waic.sum()),
        "se": float(2 * np.sqrt(len(elpd) * np.var(elpd))),
        "elpd_pointwise": elpd.tolist(),
    }


def compare(a, b):
    """Paired WAIC difference (a minus b, deviance scale) and its standard error."""
    diff = -2 * (np.array(a["waic"]["elpd_pointwise"]) - np.array(b["waic"]["elpd_pointwise"]))
    return {"difference": float(diff.sum()), "se": float(np.sqrt(len(diff) * np.var(diff)))}


def interval(values):
    lo, hi = np.quantile(values, [0.05, 0.95])
    return {"mean": float(np.mean(values)), "interval_90": [float(lo), float(hi)]}


def session_fidelity(layout, draws, data, every=20):
    """Per family: each session's posterior probability that its stated rates are its applied
    priors (None for sessions that stated no rates)."""
    totals = {fam: np.zeros(len(d["salience"])) for fam, d in data.items()}
    used = draws[::every]
    for x in used:
        params = layout.unpack(x)
        applied = session_loglik(params, data, "applied")
        considered = session_loglik(params, data, "considered")
        share = min(max(params["phi"], 1e-12), 1 - 1e-12)
        for fam in data:
            a = np.log(share) + applied[fam]
            c = np.log1p(-share) + considered[fam]
            totals[fam] += np.exp(a - np.logaddexp(a, c))
    return {
        fam: [
            None if np.isnan(data[fam]["stated"][i]).all() else float(totals[fam][i] / len(used))
            for i in range(len(totals[fam]))
        ]
        for fam in data
    }


def summarise(layout, draws, chains, pointwise, variant, stated_model, data=None):
    idx = layout.index
    parameters = {}
    for name in layout.names:
        values = draws[:, idx[name]]
        if name.startswith("log_"):
            values = np.exp(values)
            name = name[4:]
        elif name.startswith("logit_mu"):
            continue
        parameters[name] = interval(values)
    mapping = {}
    for fam in layout.families:
        i = idx[f"logit_mu_{fam}_0"]
        logit_mu = draws[:, i : i + 5]
        mu = 1 / (1 + np.exp(-logit_mu))
        mapping[fam] = {
            "mu": [interval(mu[:, level]) for level in range(5)],
            "default": interval(mu[:, IRRELEVANT]),
            "sensitivity": interval(logit_mu[:, 4] - logit_mu[:, 0]),
        }
    rungs = {}
    for fam in layout.families:
        theta = draws[:, idx.get(f"theta_{fam}", idx.get("theta"))]
        sigma = np.exp(draws[:, idx["log_sigma"]])
        rungs[fam] = {
            str(s): interval(
                phi((s - theta[:, None] + sigma[:, None] * NODES[None, :]) / LEVEL_NOISE) @ WEIGHTS
            )
            for s in range(4)
        }
    r = rhat(chains)
    fidelity = session_fidelity(layout, draws, data) if layout.stated_model == "mixture" else None
    return {
        "variant": variant,
        "stated_model": stated_model,
        "parameters": parameters,
        "mapping": mapping,
        "inclusion_by_rung": rungs,
        "waic": waic(pointwise),
        "session_fidelity": fidelity,
        "rhat_max": float(np.max(r)),
        "draws": int(draws.shape[0]),
    }


# Chain lengths per format: the urn format fits three structures (23 parameters), and its extreme
# mapping levels mix slowly, so it needs longer chains to converge.
CHAINS = {"dossier": {"fit": (20000, 8000), "recovery": (10000, 4000)}}
CHAINS["urn"] = {"fit": (40000, 15000), "recovery": (30000, 12000)}


def validate(
    seed=20260928, datasets=30, chains=4, iterations=None, burn=None, models=12, fmt="dossier"
):
    """Parameter recovery (θ, w, σ, mapping) and stated-model recovery, through the real designs.

    Parameter recovery simulates the "considered" hypothesis and fits it. Model recovery simulates
    each stated-rate hypothesis in turn and asks whether the paired WAIC prefers it.
    """
    from epistemics.ledger.inclusion import PRIOR, TRUE_MAPPING, simulate

    default_iterations, default_burn = CHAINS[fmt]["recovery"]
    iterations = iterations or default_iterations
    burn = burn or default_burn
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(datasets):
        truth = {name: float(rng.uniform(*limits)) for name, limits in PRIOR.items()}
        rows_by_family = simulate(rng, truth, stated=True, fmt=fmt)
        result = sample(
            rows_by_family, chains=chains, iterations=iterations, burn=burn, seed=seed + k
        )
        rows.append({"truth": truth, "result": result})
    model_rows = []
    for k in range(models):
        for source in ("considered", "applied"):
            truth = {name: float(rng.uniform(*limits)) for name, limits in PRIOR.items()}
            data = simulate(rng, truth, stated=True, stated_source=source, fmt=fmt)
            fits = {
                m: sample(data, "shared", m, chains, iterations, burn, seed + 1000 + k)
                for m in ("considered", "applied")
            }
            diff = compare(fits["considered"], fits["applied"])
            model_rows.append(
                {
                    "source": source,
                    "difference": diff["difference"],
                    "se": diff["se"],
                    "preferred": "considered" if diff["difference"] < 0 else "applied",
                    "rhat_max": max(f["rhat_max"] for f in fits.values()),
                }
            )
    converged = [r for r in rows if r["result"]["rhat_max"] <= RHAT_LIMIT]
    families = ("relay", "disclosure") if fmt == "dossier" else ("copying", "selection", "mismatch")
    mapping = {f: TRUE_MAPPING[f] for f in families}
    return {
        **recovery_metrics(rows, model_rows, PRIOR, mapping),
        "converged_only": recovery_metrics(converged, [], PRIOR, mapping)["metrics"]
        if len(converged) > 2
        else None,
        "converged_datasets": len(converged),
        "rhat_by_dataset": [r["result"]["rhat_max"] for r in rows],
        "seed": seed,
        "datasets": datasets,
        "chains": chains,
        "iterations": iterations,
        "burn": burn,
        "truths": [r["truth"] for r in rows],
        "estimates": [r["result"]["parameters"] for r in rows],
        "scope": (
            "Synthetic configurations (shared threshold; stated rates reflect the mapping for "
            "parameter recovery; each hypothesis in turn for model recovery) run through the "
            "real item designs and per-session description fit with the collected session "
            "counts; joint fit by adaptive Metropolis."
        ),
        "schema_version": "epistemics.inclusion-joint-recovery.v2",
        "format": fmt,
    }


RHAT_LIMIT = 1.05


def recovery_metrics(rows, model_rows, prior, true_mapping):
    metrics = {}
    for name in prior:
        t = np.array([r["truth"][name] for r in rows])
        m = np.array([r["result"]["parameters"][name]["mean"] for r in rows])
        lo = np.array([r["result"]["parameters"][name]["interval_90"][0] for r in rows])
        hi = np.array([r["result"]["parameters"][name]["interval_90"][1] for r in rows])
        metrics[name] = {
            "correlation": float(np.corrcoef(t, m)[0, 1]),
            "mae": float(np.mean(np.abs(t - m))),
            "coverage_90": float(np.mean((lo <= t) & (t <= hi))),
        }
    mapping_errors, mapping_cover = [], []
    for r in rows:
        for fam, truth_mu in true_mapping.items():
            for level, value in enumerate(truth_mu):
                est = r["result"]["mapping"][fam]["mu"][level]
                mapping_errors.append(abs(est["mean"] - value))
                mapping_cover.append(est["interval_90"][0] <= value <= est["interval_90"][1])
    metrics["mapping"] = {
        "mae": float(np.mean(mapping_errors)),
        "coverage_90": float(np.mean(mapping_cover)),
    }
    model_recovery = {
        source: sum(r["preferred"] == source for r in model_rows if r["source"] == source)
        / max(1, sum(r["source"] == source for r in model_rows))
        for source in ("considered", "applied")
    }
    return {
        "metrics": metrics,
        "stated_model_recovery": model_recovery,
        "stated_model_rows": model_rows,
    }


def validate_fidelity(seed=20261028, datasets=20, chains=4, iterations=10000, burn=4000):
    """Recovery of φ: each synthetic session's stated rates are its applied priors with prob φ."""
    from epistemics.ledger.inclusion import PRIOR, simulate

    rng = np.random.default_rng(seed)
    rows = []
    for k in range(datasets):
        truth = {name: float(rng.uniform(*limits)) for name, limits in PRIOR.items()}
        truth["phi"] = float(rng.uniform(0, 1))
        data = simulate(rng, truth, stated=True, stated_source="mixture")
        result = sample(data, "shared", "mixture", chains, iterations, burn, seed + k)
        rows.append(
            {
                "truth": truth,
                "phi": result["parameters"]["phi"],
                "rhat_max": result["rhat_max"],
            }
        )
    t = np.array([r["truth"]["phi"] for r in rows])
    m = np.array([r["phi"]["mean"] for r in rows])
    lo = np.array([r["phi"]["interval_90"][0] for r in rows])
    hi = np.array([r["phi"]["interval_90"][1] for r in rows])
    return {
        "schema_version": "epistemics.inclusion-fidelity-recovery.v1",
        "seed": seed,
        "datasets": datasets,
        "phi": {
            "correlation": float(np.corrcoef(t, m)[0, 1]),
            "mae": float(np.mean(np.abs(t - m))),
            "coverage_90": float(np.mean((lo <= t) & (t <= hi))),
        },
        "rhat_by_dataset": [r["rhat_max"] for r in rows],
        "rows": rows,
        "scope": (
            "Synthetic configurations whose sessions state their applied priors with "
            "probability φ (and the mapping otherwise), through the real designs and fits."
        ),
    }
