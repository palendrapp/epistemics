"""Second layer, hierarchical: one inclusion threshold per structure, partially pooled.

The per-structure fits (docs/disposition-abstract2-2026-09-29.md) converged, but their thresholds
differed by structure. Here each structure keeps its own per-structure model (mapping μ and spread
ω, cue weight w, session drift σ, stated-rate noise τ and fidelity φ under the mixture stated
channel, as in `inclusion_joint`). Only its threshold is tied to the others:

    θ_k ~ N(θ̄, τ_θ²), truncated to [−1, 4];  θ̄ uniform on [−1, 4];
    τ_θ half-normal with scale 1 rung, on [0.02, 3].

With five structures per configuration, a flat prior on τ_θ leaves a long upper tail; the
half-normal (Gelman 2006, for few groups) says spreads beyond two rungs are unlikely.

θ̄ is the configuration's typical threshold. τ_θ, in rungs of the salience ladder, is how much the
threshold varies between structures, that is, how far noticing generalises. As τ_θ grows the model
becomes the separate per-structure fits; as it shrinks, one threshold for every structure.

A structure here is a hidden structure in one format: relay and disclosure dossiers (with the
formal cue modules), and the corrected urn tasks' copying, selection and mismatch.

Sampling. Given (θ̄, τ_θ) the structures are independent, so each structure's block gets its own
adaptive random-walk Metropolis step, and (θ̄, τ_θ) get cheap steps on the prior terms alone. Two
moves act on every structure at once: a shift (θ̄ and every θ_k move together) and a scale (every
θ_k − θ̄ and τ_θ scale together), which lets chains cross the funnel near τ_θ = 0.
"""

from concurrent.futures import ProcessPoolExecutor

import numpy as np

from epistemics.ledger import inclusion_joint as joint
from epistemics.ledger.inclusion import COUNTS, PRIOR, URN_COUNTS, phi

FORMAT = {
    "relay": "dossier",
    "disclosure": "dossier",
    "copying": "urn2",
    "selection": "urn2",
    "mismatch": "urn2",
}
THETA_BOUNDS = joint.BOUNDS["theta"]
TAU_BOUNDS = (0.02, 3.0)
TAU_SCALE = 1.0  # Half-normal prior scale for τ_θ, in rungs.
# Decision rule for τ_θ (in rungs): noticing generalises across structures if the 90% interval
# lies below this, and is structure-specific if it lies above.
SPREAD_LIMIT = 0.5
SHIFT_SD = 0.2
SCALE_SD = 0.3
HYPER_STEPS = 5
# Histogram bins for the posterior densities the dashboard draws.
THETA_EDGES = np.round(np.arange(-1.0, 4.001, 0.1), 2)
TAU_EDGES = np.round(np.arange(0.0, 3.001, 0.05), 2)
ITERATIONS, BURN = 30000, 12000


READINGS = ("generalises", "undetermined", "structure-specific")


def spread_reading(lo, hi):
    """The decision rule for τ_θ's 90% interval."""
    return READINGS[0] if hi < SPREAD_LIMIT else READINGS[2] if lo > SPREAD_LIMIT else READINGS[1]


def truncated_logpdf(theta, mean, sd):
    """Normal log density truncated to the θ bounds (θ may be an array)."""
    lo, hi = THETA_BOUNDS
    mass = float(phi((hi - mean) / sd) - phi((lo - mean) / sd))
    return joint.normal_logpdf(np.asarray(theta), mean, sd) - np.log(max(mass, 1e-300))


class Structure:
    """One structure's data and parameter block (the joint model with a single family)."""

    def __init__(self, fam, rows):
        self.fam = fam
        self.data = joint.prepare({fam: rows})
        self.layout = joint.Layout(self.data, "shared", "mixture")
        self.theta = self.layout.index["theta"]

    def loglik(self, x):
        if np.any(x < self.layout.low) or np.any(x > self.layout.high):
            return -np.inf, None
        per = joint.session_loglik(self.layout.unpack(x), self.data, "mixture")[self.fam]
        return float(per.sum()), per


def hyper_logprior(thetas, bar, tau):
    if not (THETA_BOUNDS[0] <= bar <= THETA_BOUNDS[1] and TAU_BOUNDS[0] <= tau <= TAU_BOUNDS[1]):
        return -np.inf
    return float(truncated_logpdf(thetas, bar, tau).sum()) - 0.5 * (tau / TAU_SCALE) ** 2


def run_chain(sessions_by_family, iterations, burn, seed, thin=5):
    """One chain. Returns draws (structure blocks in order, then θ̄ and τ_θ) and per-session
    log-likelihoods for each saved draw."""
    rng = np.random.default_rng(seed)
    structures = [Structure(fam, rows) for fam, rows in sessions_by_family.items()]
    xs = [joint.start_point(s.layout, s.data, rng) for s in structures]
    for s, x in zip(structures, xs, strict=True):
        x[s.theta] = float(np.clip(rng.normal(1.0, 0.5), -0.9, 3.9))
    state = [s.loglik(x) for s, x in zip(structures, xs, strict=True)]
    lls = [v for v, _ in state]
    pers = [p for _, p in state]
    thetas = np.array([x[s.theta] for s, x in zip(structures, xs, strict=True)])
    bar, tau = float(thetas.mean()), float(np.clip(thetas.std(), 0.3, 2.0))
    covs = [np.eye(len(x)) * 0.01 for x in xs]
    history = [[] for _ in structures]
    hyper_cov = np.eye(2) * 0.05
    hyper_history = []
    draws, pointwise = [], []
    k_count = len(structures)

    def everything_at(new_thetas):
        """Log-likelihoods of every structure with its θ replaced."""
        out = []
        for s, x, value in zip(structures, xs, new_thetas, strict=True):
            y = x.copy()
            y[s.theta] = value
            out.append((y, *s.loglik(y)))
        return out

    for t in range(iterations):
        if t >= 500 and t % 250 == 0:
            for k, x in enumerate(xs):
                recent = np.array(history[k][-2000:])
                covs[k] = np.cov(recent.T) * (2.38**2 / len(x)) + np.eye(len(x)) * 1e-6
            recent = np.array(hyper_history[-2000:])
            hyper_cov = np.cov(recent.T) * (2.38**2 / 2) + np.eye(2) * 1e-6
        # Each structure's block, with its θ's prior from the configuration distribution.
        for k, s in enumerate(structures):
            proposal = rng.multivariate_normal(xs[k], covs[k])
            value, per = s.loglik(proposal)
            if np.isfinite(value):
                new = value + float(truncated_logpdf(proposal[s.theta], bar, tau))
                old = lls[k] + float(truncated_logpdf(xs[k][s.theta], bar, tau))
                if np.log(rng.random()) < new - old:
                    xs[k], lls[k], pers[k] = proposal, value, per
            history[k].append(xs[k].copy())
        thetas = np.array([x[s.theta] for s, x in zip(structures, xs, strict=True)])
        # The configuration distribution given the thresholds.
        current = hyper_logprior(thetas, bar, tau)
        for _ in range(HYPER_STEPS):
            b, s_ = rng.multivariate_normal([bar, tau], hyper_cov)
            value = hyper_logprior(thetas, b, s_)
            if np.log(rng.random()) < value - current:
                bar, tau, current = float(b), float(s_), value
        hyper_history.append([bar, tau])
        # Shift: θ̄ and every θ_k together.
        delta = rng.normal(0, SHIFT_SD)
        new_thetas = thetas + delta
        if np.all((new_thetas >= THETA_BOUNDS[0]) & (new_thetas <= THETA_BOUNDS[1])):
            moved = everything_at(new_thetas)
            value = sum(m[1] for m in moved) + hyper_logprior(new_thetas, bar + delta, tau)
            if np.isfinite(value) and np.log(rng.random()) < value - (sum(lls) + current):
                xs = [m[0] for m in moved]
                lls = [m[1] for m in moved]
                pers = [m[2] for m in moved]
                bar, thetas = bar + delta, new_thetas
                current = hyper_logprior(thetas, bar, tau)
        # Scale: every θ_k − θ̄ and τ_θ together; the Jacobian is exp((K + 1) s).
        s_ = rng.normal(0, SCALE_SD)
        new_thetas = bar + (thetas - bar) * np.exp(s_)
        new_tau = tau * np.exp(s_)
        if np.all((new_thetas >= THETA_BOUNDS[0]) & (new_thetas <= THETA_BOUNDS[1])):
            prior = hyper_logprior(new_thetas, bar, new_tau)
            if np.isfinite(prior):
                moved = everything_at(new_thetas)
                value = sum(m[1] for m in moved) + prior + (k_count + 1) * s_
                if np.isfinite(value) and np.log(rng.random()) < value - (sum(lls) + current):
                    xs = [m[0] for m in moved]
                    lls = [m[1] for m in moved]
                    pers = [m[2] for m in moved]
                    thetas, tau, current = new_thetas, float(new_tau), prior
        if t >= burn and t % thin == 0:
            draws.append(np.concatenate([*xs, [bar, tau]]))
            pointwise.append(np.concatenate(pers))
    return np.array(draws), np.array(pointwise)


def density(values, edges):
    counts, _ = np.histogram(values, bins=edges)
    return (counts / max(counts.sum(), 1)).round(5).tolist()


def truncated_normal_draws(rng, mean, sd):
    """One draw per (mean, sd) pair from the normal truncated to the θ bounds."""
    lo, hi = THETA_BOUNDS
    out = mean + sd * rng.normal(size=len(mean))
    for _ in range(200):  # Rejection: every bounded mean keeps at least 45% of its mass inside.
        outside = (out < lo) | (out > hi)
        if not outside.any():
            break
        out[outside] = mean[outside] + sd[outside] * rng.normal(size=int(outside.sum()))
    return np.clip(out, lo, hi)


def sample(
    sessions_by_family, chains=4, iterations=ITERATIONS, burn=BURN, seed=20260929, workers=1
):
    """Fit the hierarchical model; chains run in parallel when workers > 1."""
    args = [(sessions_by_family, iterations, burn, seed + c) for c in range(chains)]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(_chain, args))
    else:
        results = [_chain(a) for a in args]
    return summarise(sessions_by_family, results, seed)


def _chain(args):
    return run_chain(*args)


def summarise(sessions_by_family, results, seed=0):
    structures = [Structure(fam, rows) for fam, rows in sessions_by_family.items()]
    chains = np.array([d for d, _ in results])  # chains × draws × dim
    draws = np.concatenate([d for d, _ in results])
    pointwise = np.concatenate([p for _, p in results])
    per_structure, offset, session_offset = {}, 0, 0
    threshold_index = []
    for s in structures:
        dim = len(s.layout.names)
        n = len(s.data[s.fam]["salience"])
        fit = joint.summarise(
            s.layout,
            draws[:, offset : offset + dim],
            chains[:, :, offset : offset + dim],
            pointwise[:, session_offset : session_offset + n],
            "shared",
            "mixture",
            s.data,
        )
        fit["waic"].pop("elpd_pointwise", None)
        fit["theta_density"] = density(draws[:, offset + s.theta], THETA_EDGES)
        per_structure[s.fam] = {"format": FORMAT.get(s.fam), **fit}
        threshold_index.append(offset + s.theta)
        offset += dim
        session_offset += n
    bar, tau = draws[:, -2], draws[:, -1]
    rng = np.random.default_rng(seed)
    new = truncated_normal_draws(rng, bar, tau)
    spread = joint.interval(tau)
    lo, hi = spread["interval_90"]
    r = joint.rhat(chains)
    return {
        "theta_bar": joint.interval(bar),
        "tau_theta": spread,
        "spread_reading": spread_reading(lo, hi),
        "tau_theta_above_limit": float(np.mean(tau > SPREAD_LIMIT)),
        "theta_new_structure": joint.interval(new),
        "densities": {
            "theta_edges": THETA_EDGES.tolist(),
            "tau_edges": TAU_EDGES.tolist(),
            "theta_bar": density(bar, THETA_EDGES),
            "theta_new_structure": density(new, THETA_EDGES),
            "tau_theta": density(tau, TAU_EDGES),
        },
        "structures": per_structure,
        "rhat_max": float(np.max(r)),
        "rhat_hyper": [float(r[-2]), float(r[-1])],
        # The thresholds and their distribution only; validity uses every parameter.
        "rhat_thresholds": float(np.max(r[[*threshold_index, -2, -1]])),
        "valid": bool(np.max(r) <= joint.RHAT_LIMIT),
        "waic": {k: v for k, v in joint.waic(pointwise).items() if k != "elpd_pointwise"},
        "draws": int(draws.shape[0]),
        "families": list(sessions_by_family),
    }


# Recovery: synthetic configurations with known θ̄, τ_θ and per-structure parameters, run through
# the real item designs and description fits at the collected session counts.
HYPER_PRIOR = {"theta_bar": (0.3, 2.7), "tau_theta": (0.0, 1.5)}


def recovery_counts():
    return {
        fam: (COUNTS if FORMAT[fam] == "dossier" else URN_COUNTS)[fam]
        for fam in ("relay", "disclosure", "copying", "selection", "mismatch")
    }


def synthetic(rng, counts, spread=None):
    """A synthetic configuration; spread fixes τ_θ instead of drawing it."""
    from epistemics.ledger.inclusion import simulate

    truth = {name: float(rng.uniform(*limits)) for name, limits in HYPER_PRIOR.items()}
    if spread is not None:
        truth["tau_theta"] = float(spread)
    for fam in counts:
        truth[f"theta_{fam}"] = float(
            np.clip(rng.normal(truth["theta_bar"], truth["tau_theta"]), -0.9, 3.9)
        )
        truth[f"w_{fam}"] = float(rng.uniform(*PRIOR["w"]))
        truth[f"sigma_{fam}"] = float(rng.uniform(*PRIOR["sigma"]))
        truth[f"phi_{fam}"] = float(rng.uniform(0, 1))
    rows = simulate(rng, truth, stated=True, stated_source="mixture", counts=counts)
    return truth, rows


def _fit_dataset(args):
    rows, chains, iterations, burn, seed = args
    return sample(rows, chains, iterations, burn, seed)


def validate(seed=20260929, datasets=30, chains=4, iterations=ITERATIONS, burn=BURN, workers=8):
    rng = np.random.default_rng(seed)
    counts = recovery_counts()
    made = [synthetic(rng, counts) for _ in range(datasets)]
    jobs = [(rows, chains, iterations, burn, seed + 100 * k) for k, (_, rows) in enumerate(made)]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_fit_dataset, jobs))
    rows = [{"truth": t, "result": r} for (t, _), r in zip(made, results, strict=True)]
    return {
        "schema_version": "epistemics.inclusion-hier-recovery.v1",
        "seed": seed,
        "datasets": datasets,
        "chains": chains,
        "iterations": iterations,
        "burn": burn,
        "session_counts": {f: {str(k): v for k, v in c.items()} for f, c in counts.items()},
        "generating_ranges": {**HYPER_PRIOR, "w": PRIOR["w"], "sigma": PRIOR["sigma"]},
        **recovery_metrics(rows),
        "rows": [
            {
                "truth": r["truth"],
                "theta_bar": r["result"]["theta_bar"],
                "tau_theta": r["result"]["tau_theta"],
                "spread_reading": r["result"]["spread_reading"],
                "thetas": {
                    fam: x["parameters"]["theta"] for fam, x in r["result"]["structures"].items()
                },
                "rhat_max": r["result"]["rhat_max"],
            }
            for r in rows
        ],
        "scope": (
            "Synthetic configurations with per-structure thresholds drawn from N(θ̄, τ_θ²), "
            "per-structure cue weight, drift and stated-rate fidelity, run through the real item "
            "designs and description fits with the collected session counts (dossier relay and "
            "disclosure, corrected urn copying, selection and mismatch)."
        ),
    }


def recovery_metrics(rows):
    def metric(truth, result):
        t, m = np.array(truth), np.array([x["mean"] for x in result])
        lo = np.array([x["interval_90"][0] for x in result])
        hi = np.array([x["interval_90"][1] for x in result])
        return {
            "correlation": float(np.corrcoef(t, m)[0, 1]),
            "mae": float(np.mean(np.abs(t - m))),
            "coverage_90": float(np.mean((lo <= t) & (t <= hi))),
        }

    theta_truth, theta_fit = [], []
    for r in rows:
        for fam, x in r["result"]["structures"].items():
            theta_truth.append(r["truth"][f"theta_{fam}"])
            theta_fit.append(x["parameters"]["theta"])
    readings = {}
    for r in rows:
        tau = r["truth"]["tau_theta"]
        band = "below 0.25" if tau < 0.25 else "above 0.75" if tau > 0.75 else "0.25 to 0.75"
        cell = readings.setdefault(band, {})
        reading = r["result"]["spread_reading"]
        cell[reading] = cell.get(reading, 0) + 1
    wrong = sum(
        (r["truth"]["tau_theta"] < 0.25 and r["result"]["spread_reading"] == "structure-specific")
        or (r["truth"]["tau_theta"] > 0.75 and r["result"]["spread_reading"] == "generalises")
        for r in rows
    )
    converged = [r for r in rows if r["result"]["rhat_max"] <= joint.RHAT_LIMIT]
    return {
        "metrics": {
            "theta_bar": metric(
                [r["truth"]["theta_bar"] for r in rows], [r["result"]["theta_bar"] for r in rows]
            ),
            "tau_theta": metric(
                [r["truth"]["tau_theta"] for r in rows], [r["result"]["tau_theta"] for r in rows]
            ),
            "theta_k": metric(theta_truth, theta_fit),
        },
        "spread_readings_by_true_spread": readings,
        "wrong_direction_readings": int(wrong),
        "converged_datasets": len(converged),
        "rhat_by_dataset": [r["result"]["rhat_max"] for r in rows],
    }


# Power: how many structures per configuration would let the spread reading reach "generalises"?
# A surrogate replaces each structure's full model by a normal estimate of its threshold, with a
# posterior SD in the range the unpooled per-structure fits gave (0.15-0.47 rungs); the pooled part
# becomes a normal-normal model on a grid, with the same priors and decision rule. It ignores the
# truncation of θ_k to [−1, 4]. It is checked against the full model at five structures (the
# recovery study) and, by `spot_check`, at a larger number.
SURROGATE_SE = (0.15, 0.45)
BAR_GRID = np.linspace(-1.0, 4.0, 101)
TAU_GRID = np.linspace(0.02, 3.0, 150)


def surrogate(estimates, ses):
    """Reading and posterior mean of τ_θ given normal threshold estimates and their SDs."""
    estimates, ses = np.asarray(estimates, dtype=float), np.asarray(ses, dtype=float)
    var = TAU_GRID[None, :, None] ** 2 + ses[None, None, :] ** 2
    diff = estimates[None, None, :] - BAR_GRID[:, None, None]
    loglik = (-0.5 * diff**2 / var - 0.5 * np.log(var)).sum(axis=-1)
    loglik = loglik - 0.5 * (TAU_GRID[None, :] / TAU_SCALE) ** 2
    posterior = np.exp(loglik - loglik.max()).sum(axis=0)
    posterior /= posterior.sum()
    cdf = np.cumsum(posterior)
    lo, hi = TAU_GRID[np.minimum(np.searchsorted(cdf, [0.05, 0.95]), len(TAU_GRID) - 1)]
    return spread_reading(lo, hi), float(posterior @ TAU_GRID)


def surrogate_draw(rng, thetas):
    ses = rng.uniform(*SURROGATE_SE, len(thetas))
    return surrogate(np.asarray(thetas) + rng.normal(0, ses), ses)


def power(
    seed=20260930,
    structures=(5, 8, 10, 15, 20, 30),
    spreads=(0.0, 0.1, 0.25, 0.5, 0.75, 1.0),
    repetitions=400,
):
    """Share of each reading by number of structures and true spread, under the surrogate."""
    rng = np.random.default_rng(seed)
    cells = []
    for k in structures:
        for spread in spreads:
            tally = dict.fromkeys(READINGS, 0)
            for _ in range(repetitions):
                bar = rng.uniform(*HYPER_PRIOR["theta_bar"])
                thetas = np.clip(bar + spread * rng.normal(size=k), -0.9, 3.9)
                tally[surrogate_draw(rng, thetas)[0]] += 1
            cells.append(
                {"structures": k, "spread": spread} | {r: n / repetitions for r, n in tally.items()}
            )
    return cells


def surrogate_check(recovery, seed=20260931, draws=50):
    """The surrogate on the full-model recovery study's true thresholds, against the full model's
    readings, by band of the true spread."""
    rng = np.random.default_rng(seed)
    bands, means = {}, []
    for row in recovery["rows"]:
        truth = row["truth"]
        thetas = [v for k, v in truth.items() if k.startswith("theta_") and k != "theta_bar"]
        outcomes = [surrogate_draw(rng, thetas) for _ in range(draws)]
        spread = truth["tau_theta"]
        band = "below 0.25" if spread < 0.25 else "above 0.75" if spread > 0.75 else "0.25 to 0.75"
        cell = bands.setdefault(
            band, {"datasets": 0, "full": dict.fromkeys(READINGS, 0), "surrogate": {}}
        )
        cell["datasets"] += 1
        cell["full"][row["spread_reading"]] += 1
        for r in READINGS:
            share = sum(o[0] == r for o in outcomes) / draws
            cell["surrogate"][r] = cell["surrogate"].get(r, 0.0) + share
        means.append((float(np.mean([o[1] for o in outcomes])), row["tau_theta"]["mean"]))
    s, f = np.array(means).T
    return {
        "bands": bands,
        "tau_mean_correlation": float(np.corrcoef(s, f)[0, 1]),
        "tau_mean_difference": float(np.mean(s - f)),
    }


def spot_check(structures, spread, datasets=8, seed=20261001, workers=8):
    """The full model on synthetic configurations with more structures (base designs reused as
    "relay#2" and so on) and a fixed true spread."""
    from epistemics.ledger.inclusion import COUNTS, URN_COUNTS

    bases = list(FORMAT)
    names = [
        bases[i % len(bases)] + (f"#{i // len(bases) + 1}" if i >= len(bases) else "")
        for i in range(structures)
    ]
    counts = {
        n: (COUNTS if FORMAT[n.split("#")[0]] == "dossier" else URN_COUNTS)[n.split("#")[0]]
        for n in names
    }
    rng = np.random.default_rng(seed)
    made = [synthetic(rng, counts, spread) for _ in range(datasets)]
    jobs = [(rows, 4, ITERATIONS, BURN, seed + 100 * k) for k, (_, rows) in enumerate(made)]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_fit_dataset, jobs))
    readings = [r["spread_reading"] for r in results]
    return {
        "structures": structures,
        "spread": spread,
        "datasets": datasets,
        "readings": {r: readings.count(r) for r in READINGS},
        "tau_theta": [r["tau_theta"] for r in results],
        "rhat_max": [r["rhat_max"] for r in results],
        "seed": seed,
    }
