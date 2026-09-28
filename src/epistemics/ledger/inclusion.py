"""Second layer (draft): structure inclusion across a salience ladder.

The description modules give, per session and description level, a grid likelihood for the prior
an agent applies to a hidden-structure hypothesis (a relay, a selective sender). This layer
explains those priors with a few abstract parameters per configuration:

- inclusion threshold θ: how much prompting the hypothesis needs before it enters the agent's
  model, on a fixed salience ladder (0 unprompted; 1 named; 2 named and asked for its rate;
  3 named, asked and probed, or the full mechanism statement);
- cue-driven inclusion w: how far a suggestive description, by itself, brings the hypothesis in;
- session drift σ: how much a session's readiness to include it varies (a state shared by the
  session's description levels);
- the mapping μ: the prior applied to each description when the hypothesis is included, summarised
  as a default d (the irrelevant description) and description sensitivity κ (strongly suggestive
  minus strongly reassuring, on the log-odds scale).

A level's prior is 0 when the hypothesis is not included and logit-normal around μ_l (spread ω)
when it is. Inclusion at level l of session s has probability Φ((S + w c_l + ε_s − θ) / ς), with
ε_s ~ N(0, σ²), c_l = logit μ_l − logit μ_irrelevant and ς fixed. The mapping is estimated from
the fully scaffolded sessions (ladder 3); θ, w and σ get a grid posterior under uniform priors,
integrating ε_s by Gauss–Hermite quadrature.
"""

import numpy as np

from epistemics.dispositions.response import erfc

GRID = np.round(np.linspace(0, 1, 21), 3)  # The description fits' disposition grid.
LADDER = {
    ("unprompted", "dossier-a"): 0,
    ("unprompted", "named-a"): 1,
    ("asked", "named-a"): 2,
    ("probed", "named-a"): 3,
    ("dossier", "dossier-a"): 3,
    ("cues", "cues-a"): 3,
}
THETA = np.round(np.arange(-1.0, 4.001, 0.1), 2)
W = np.round(np.arange(0.0, 1.501, 0.1), 2)
SIGMA = np.array([0.05, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0])
LEVEL_NOISE = 0.3  # ς: level-specific inclusion noise, fixed.
MU = np.round(np.arange(0.01, 0.991, 0.01), 2)
OMEGA = np.array([0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1.0, 1.3, 1.6])
NODES, WEIGHTS = np.polynomial.hermite_e.hermegauss(15)
WEIGHTS = WEIGHTS / WEIGHTS.sum()
IRRELEVANT = 2


def phi(x):
    return 0.5 * erfc(-np.asarray(x, dtype=float) / np.sqrt(2))


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-9, 1 - 1e-9)
    return np.log(p) - np.log1p(-p)


def rung(module, variant):
    """Salience of a session's condition, or None when it is not on the ladder."""
    kind = module.split("-", 1)[1]
    return LADDER.get((kind, variant))


def family(module):
    return "relay" if module.startswith("corroboration") else "disclosure"


def cell_masses(mu, omega):
    """Grid masses of a logit-normal prior with median mu and log-odds spread omega."""
    edges = np.concatenate([[0.0], (GRID[1:] + GRID[:-1]) / 2, [1.0]])
    cdf = phi((logit(edges)[None, :] - logit(mu)[..., None]) / np.asarray(omega)[..., None])
    cdf[..., 0], cdf[..., -1] = 0.0, 1.0
    return np.diff(cdf, axis=-1)


def fit_mapping(likelihoods):
    """Per level: the included mapping μ and one spread ω, by grid maximum likelihood.

    likelihoods: sessions × 5 × 21 grid likelihoods from fully scaffolded sessions.
    """
    L = np.asarray(likelihoods, dtype=float)
    masses = cell_masses(MU[:, None], OMEGA[None, :])  # μ × ω × grid
    loglik = np.stack(
        [
            np.log(np.einsum("sg,mog->smo", L[:, level], masses) + 1e-300).sum(axis=0)
            for level in range(5)
        ]
    )  # level × μ × ω
    best_by_omega = loglik.max(axis=1).sum(axis=0)
    o = int(np.argmax(best_by_omega))
    mu = MU[np.argmax(loglik[:, :, o], axis=1)]
    return mu, float(OMEGA[o])


def level_terms(likelihoods, mu, omega):
    """Per session and level: likelihood if included (A) and if not (B)."""
    L = np.asarray(likelihoods, dtype=float)
    masses = cell_masses(mu, np.full(5, omega))  # level × grid
    A = np.einsum("slg,lg->sl", L, masses)
    B = L[:, :, 0]
    return A, B


def inclusion_probability(salience, cue, theta, w, sigma, eps):
    return phi((salience + w * cue + sigma * eps - theta) / LEVEL_NOISE)


def log_posterior(sessions):
    """Grid log-likelihood over (θ, w, σ) for one configuration's sessions.

    sessions: list of (salience, cue[5], A[5], B[5]), where A and B are the level likelihoods if
    the hypothesis is included and if it is not.
    """
    theta = THETA[:, None, None, None, None]
    w = W[None, :, None, None, None]
    sigma = SIGMA[None, None, :, None, None]
    eps = NODES[None, None, None, :, None]
    total = np.zeros((len(THETA), len(W), len(SIGMA)))
    for salience, cue, A, B in sessions:
        p = inclusion_probability(
            salience, np.asarray(cue)[None, None, None, None, :], theta, w, sigma, eps
        )
        levels = p * np.asarray(A) + (1 - p) * np.asarray(B)
        session = np.exp(np.log(levels + 1e-300).sum(axis=-1)) @ WEIGHTS
        total += np.log(session + 1e-300)
    return total


def summarise(grid, weights):
    cdf = np.cumsum(weights)
    lo, hi = np.searchsorted(cdf, [0.05, 0.95])
    return {
        "mean": float(weights @ grid),
        "interval_90": [float(grid[min(lo, len(grid) - 1)]), float(grid[min(hi, len(grid) - 1)])],
    }


VARIANTS = ("shared", "theta_by_family", "w_by_family")


def prepare(sessions_by_family):
    """Mapping per family from fully scaffolded sessions, and each session's level terms."""
    mapping, terms = {}, {}
    for fam, rows in sessions_by_family.items():
        full = [lik for s, lik, _ in rows if s == 3]
        if not full:
            continue
        mu, omega = fit_mapping(full)
        cue = logit(mu) - logit(mu[IRRELEVANT])
        mapping[fam] = {
            "mu": mu.tolist(),
            "omega": omega,
            "default": float(mu[IRRELEVANT]),
            "sensitivity": float(logit(mu[4]) - logit(mu[0])),
            "sessions": len(full),
        }
        A, B = level_terms([lik for _, lik, _ in rows], mu, omega)
        terms[fam] = [(s, cue, a, b) for (s, _, _), a, b in zip(rows, A, B, strict=True)]
    return mapping, terms


def joint_loglik(terms, variant):
    """Grid log-likelihood and the names of its axes, for one sharing variant."""
    by_family = {fam: log_posterior(rows) for fam, rows in terms.items()}  # θ × w × σ each
    if variant == "shared" or len(by_family) == 1:
        return sum(by_family.values()), ("theta", "w", "sigma")
    relay, disclosure = by_family["relay"], by_family["disclosure"]
    if variant == "theta_by_family":
        total = relay[:, None, :, :] + disclosure[None, :, :, :]
        return total, ("theta_relay", "theta_disclosure", "w", "sigma")
    total = relay[:, :, None, :] + disclosure[:, None, :, :]
    return total, ("theta", "w_relay", "w_disclosure", "sigma")


AXIS_GRIDS = {
    "theta": THETA,
    "theta_relay": THETA,
    "theta_disclosure": THETA,
    "w": W,
    "w_relay": W,
    "w_disclosure": W,
    "sigma": SIGMA,
}


def fit(sessions_by_family, variant="shared"):
    """sessions_by_family: {family: [(salience, likelihoods 5×21, stated or None), ...]}."""
    mapping, terms = prepare(sessions_by_family)
    loglik, axes = joint_loglik(terms, variant)
    peak = loglik.max()
    posterior = np.exp(loglik - peak)
    total = posterior.sum()
    posterior /= total
    parameters = {
        name: summarise(
            AXIS_GRIDS[name],
            posterior.sum(axis=tuple(j for j in range(len(axes)) if j != axis)),
        )
        for axis, name in enumerate(axes)
    }
    means = {name: v["mean"] for name, v in parameters.items()}
    # Probability of including the hypothesis for an uninformative description, per rung and
    # family, at the posterior means.
    rungs = {}
    for fam in terms:
        theta = means.get(f"theta_{fam}", means.get("theta"))
        sigma = means["sigma"]
        rungs[fam] = {
            str(s): float(inclusion_probability(s, 0.0, theta, 0.0, sigma, NODES) @ WEIGHTS)
            for s in range(4)
        }
    return {
        "variant": variant,
        "mapping": mapping,
        "parameters": parameters,
        "log_evidence": float(peak + np.log(total) - np.log(posterior.size)),
        "inclusion_by_rung": rungs,
        "check": check(terms, means),
        "sessions": sum(len(r) for r in terms.values()),
    }


def check(terms, means):
    """Observed against predicted inclusion, by family and rung, at levels whose mapping is 0.3+.

    A level counts as observed-included when the hypothesis explains its data better than
    exclusion (A > B). Predicted is the mean inclusion probability at the posterior means,
    integrated over the session state.
    """
    rows = {}
    for fam, sessions in terms.items():
        theta = means.get(f"theta_{fam}", means.get("theta"))
        w = means.get(f"w_{fam}", means.get("w"))
        for salience, cue, A, B in sessions:
            p = inclusion_probability(salience, cue[:, None], theta, w, means["sigma"], NODES)
            predicted = p @ WEIGHTS
            for level in range(5):
                if cue[level] < logit(0.3) - logit(0.5) or level == 0:
                    continue
                key = f"{fam}/{salience}"
                row = rows.setdefault(key, {"levels": 0, "observed": 0, "predicted": 0.0})
                row["levels"] += 1
                row["observed"] += int(A[level] > B[level])
                row["predicted"] += float(predicted[level])
    return {
        key: {
            "levels": r["levels"],
            "observed_rate": r["observed"] / r["levels"],
            "predicted_rate": r["predicted"] / r["levels"],
        }
        for key, r in sorted(rows.items())
    }


def ledger_sessions(models, configuration, with_ids=False):
    """This configuration's description sessions on the ladder, from the ledger's model block.

    With with_ids, also returns each family's session ids in the same order.
    """
    rows, ids = {}, {}
    for s in models["sessions"]:
        if s["configuration"] != configuration or not s.get("slots"):
            continue
        if s["module"].endswith("-cues") and s.get("order_policy") != "random":
            continue
        salience = rung(s["module"], s["variant"])
        if salience is None:
            continue
        stated = [v[0] for v in s["stated"]] if all(s["stated"]) else None
        rows.setdefault(family(s["module"]), []).append((salience, np.array(s["slots"]), stated))
        ids.setdefault(family(s["module"]), []).append(s["id"])
    return (rows, ids) if with_ids else rows


# Recovery: synthetic configurations with known θ, w, σ, run through the real item designs and
# the real per-session description fit, with the session counts of the collected data.
TRUE_MAPPING = {
    "relay": np.array([0.05, 0.45, 0.5, 0.5, 0.93]),
    "disclosure": np.array([0.25, 0.2, 0.5, 0.65, 0.75]),
}
COUNTS = {"relay": {0: 3, 1: 3, 2: 6, 3: 14}, "disclosure": {0: 3, 1: 3, 2: 3, 3: 5}}
PRIOR = {"theta": (0.3, 2.7), "w": (0.0, 1.0), "sigma": (0.2, 1.2)}
PRIORS = {
    "shared": PRIOR,
    "theta_by_family": {
        "theta_relay": (0.3, 2.7),
        "theta_disclosure": (0.3, 2.7),
        "w": (0.0, 1.0),
        "sigma": (0.2, 1.2),
    },
}


def designs():
    from epistemics.dispositions import design

    return {
        ("relay", 0): design.corroboration_unprompted(),
        ("relay", 1): design.corroboration_unprompted(),
        ("relay", 2): design.corroboration_asked(),
        ("relay", 3): design.corroboration_cues(),
        ("disclosure", 0): design.disclosure_unprompted(),
        ("disclosure", 1): design.disclosure_unprompted(),
        ("disclosure", 2): design.disclosure_asked(),
        ("disclosure", 3): design.disclosure_cues(),
    }


def simulate(
    rng, truth, omega=0.4, report_sd=(0.05, 0.3), stated=False, stated_source="considered"
):
    """Synthetic sessions per family. Stated rates, when asked, report the mapping ("considered")
    or the session's applied prior ("applied")."""
    from epistemics.dispositions import observers
    from epistemics.dispositions.response import sample_reports

    items_for = designs()
    observer = {"relay": observers.corroboration, "disclosure": observers.disclosure}
    model = {"relay": "dependence", "disclosure": "disclosure"}
    rows = {}
    for fam, counts in COUNTS.items():
        mu = TRUE_MAPPING[fam]
        cue = logit(mu) - logit(mu[IRRELEVANT])
        for salience, n in counts.items():
            items = items_for[(fam, salience)]
            for _ in range(n):
                eps = rng.normal()
                theta = truth.get(f"theta_{fam}", truth.get("theta"))
                p = inclusion_probability(salience, cue, theta, truth["w"], truth["sigma"], eps)
                included = rng.random(5) < p
                applied = np.where(
                    included,
                    1 / (1 + np.exp(-(logit(mu) + omega * rng.normal(size=5)))),
                    0.0,
                )
                latent = observers.cue_observer(observer[fam], items, applied, 1.0)
                source_here = stated_source
                if stated_source == "mixture":
                    source_here = "applied" if rng.random() < truth["phi"] else "considered"
                source = (
                    logit(mu)
                    if source_here == "considered"
                    else logit(np.clip(applied, 0.005, 0.995))
                )
                latent = np.where(
                    items["kind"] == "rate", source[np.maximum(items["slot"], 0)], latent
                )
                reports = sample_reports(latent, rng.uniform(*report_sd), rng)
                rates = items["kind"] == "rate"
                answers = (
                    [float(reports[rates & (items["slot"] == level)][0]) for level in range(5)]
                    if stated and rates.any()
                    else None
                )
                rows.setdefault(fam, []).append(
                    (salience, slot_likelihoods(model[fam], items, reports), answers)
                )
    return rows


def slot_likelihoods(model, items, reports):
    """Per level: the grid posterior of the level's prior (uniform prior, so ∝ likelihood)."""
    from epistemics.ledger.models import cue_marginals

    return cue_marginals(model, items, np.asarray(reports, dtype=float))[0]


def validate(seed=20260928, datasets=30, variant="shared"):
    rng = np.random.default_rng(seed)
    prior = PRIORS[variant]
    rows = []
    for _ in range(datasets):
        truth = {k: float(rng.uniform(*v)) for k, v in prior.items()}
        result = fit(simulate(rng, truth), variant)
        rows.append({"truth": truth, "estimate": result["parameters"]})
    metrics = {}
    for name in prior:
        t = np.array([r["truth"][name] for r in rows])
        m = np.array([r["estimate"][name]["mean"] for r in rows])
        lo = np.array([r["estimate"][name]["interval_90"][0] for r in rows])
        hi = np.array([r["estimate"][name]["interval_90"][1] for r in rows])
        grid = AXIS_GRIDS[name]
        step = float(np.min(np.diff(grid)))
        metrics[name] = {
            "correlation": float(np.corrcoef(t, m)[0, 1]),
            "mae": float(np.mean(np.abs(t - m))),
            "coverage_90": float(np.mean((lo - step / 2 <= t) & (t <= hi + step / 2))),
        }
    return {
        "schema_version": "epistemics.inclusion-recovery.v1",
        "seed": seed,
        "datasets": datasets,
        "variant": variant,
        "generating_ranges": prior,
        "session_counts": {f: {str(k): v for k, v in c.items()} for f, c in COUNTS.items()},
        "metrics": metrics,
        "rows": rows,
        "scope": (
            "Synthetic configurations with known inclusion threshold, cue-driven inclusion and "
            "session drift, run through the real item designs and per-session description fit at "
            "report noise 0.05-0.3 and mapping spread 0.4, with the collected session counts."
        ),
    }
