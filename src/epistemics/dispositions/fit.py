"""Grid posteriors for each module under uniform priors on finite parameter grids.

Evidence (log marginal likelihood) compares models with matched grid sizes. Estimates are
posterior means; intervals are central 90% intervals of the marginal grid posterior.
"""

import numpy as np

from epistemics.dispositions import observers
from epistemics.dispositions.response import (
    logsumexp,
    report_log_likelihood,
    wtp_log_likelihood,
)

DISPOSITION = np.round(np.linspace(0, 1, 21), 3)
GAMMA = np.round(np.arange(0.5, 1.501, 0.1), 2)
BIAS = np.round(np.arange(-0.6, 0.601, 0.15), 2)
# Report noise on the log-odds scale. Model 0.6 adds 0.01-0.03: precise configurations sat at the
# old floor of 0.05 (docs/traits-2026-09-29.md). Reports are whole percentages, so the lowest
# values are only partly identified.
REPORT_SD = np.array([0.01, 0.02, 0.03, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.65, 0.8, 1.0])
CERTAINTY_VALUE = np.arange(-40.0, 160.1, 4.0)
DECISION_WEIGHT = np.round(np.arange(0.5, 1.501, 0.1), 2)
WTP_SD = np.array([0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 14.0])

# Prior strength (pseudo-observations) for learned base rates; 1024 is effectively no learning.
STRENGTH = np.array([0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 1024.0])
LEARNING_LIMIT = 32.0

REPORT_MODELS = {
    "dependence": observers.corroboration,
    "fixed_discount": observers.fixed_discount,
    "disclosure": observers.disclosure,
    "linear_skepticism": observers.linear_skepticism,
    "mismatch": observers.mismatch,
}


def summarize(log_likelihood, grids):
    total = logsumexp(log_likelihood)
    posterior = np.exp(log_likelihood - total)
    rows = {}
    for axis, (name, grid) in enumerate(grids.items()):
        other = tuple(i for i in range(len(grids)) if i != axis)
        marginal = posterior.sum(axis=other)
        cdf = np.cumsum(marginal)
        lo, hi = np.searchsorted(cdf, [0.05, 0.95])
        rows[name] = {
            "mean": float(marginal @ grid),
            "interval_90": [
                float(grid[min(lo, len(grid) - 1)]),
                float(grid[min(hi, len(grid) - 1)]),
            ],
        }
    best = np.unravel_index(int(np.argmax(log_likelihood)), log_likelihood.shape)
    return {
        "log_evidence": float(total - np.log(log_likelihood.size)),
        "parameters": rows,
        "maximum": {
            name: float(grid[i]) for (name, grid), i in zip(grids.items(), best, strict=True)
        },
    }


def fit_reports(model, items, reports):
    """Disposition, sensitivity, forecast bias and report noise for a T2 or T3 respondent.

    Bias shifts forecasts toward high demand; it does not apply to structure probes.
    """
    latent = REPORT_MODELS[model](items, DISPOSITION[:, None, None], GAMMA[None, :, None])
    forecast = (items["kind"] != "probe").astype(float)
    means = latent[:, :, None, :] + BIAS[None, None, :, None] * forecast
    log_likelihood = np.stack(
        [report_log_likelihood(means, reports, sd) for sd in REPORT_SD], axis=-1
    )
    grids = {"disposition": DISPOSITION, "gamma": GAMMA, "bias": BIAS, "report_sd": REPORT_SD}
    return summarize(log_likelihood, grids)


def fit_checks(function, items, wtp):
    """Value of certainty, weight on decision value and WTP noise for a T5 respondent."""
    decision, gain = observers.check_values(items, function)
    means = CERTAINTY_VALUE[:, None, None] * gain + DECISION_WEIGHT[None, :, None] * decision
    log_likelihood = np.stack([wtp_log_likelihood(means, wtp, sd) for sd in WTP_SD], axis=-1)
    grids = {
        "certainty_value": CERTAINTY_VALUE,
        "decision_weight": DECISION_WEIGHT,
        "wtp_sd": WTP_SD,
    }
    return summarize(log_likelihood, grids)


def fit_learning(model, items, reports, successes, trials):
    """A T2 or T3 respondent who learns the base rate from structures revealed after each case.

    The disposition at each case is the posterior mean of a Beta prior with mean `start` and
    strength `strength` after the revealed cases shown before it.
    """
    delta = observers.learned(
        DISPOSITION[:, None, None, None],
        STRENGTH[None, :, None, None],
        successes,
        trials,
    )
    latent = REPORT_MODELS[model](items, delta, GAMMA[None, None, :, None])
    forecast = (items["kind"] != "probe").astype(float)
    means = latent[:, :, :, None, :] + BIAS[None, None, None, :, None] * forecast
    log_likelihood = np.stack(
        [report_log_likelihood(means, reports, sd) for sd in REPORT_SD], axis=-1
    )
    grids = {
        "start": DISPOSITION,
        "log2_strength": np.log2(STRENGTH),
        "gamma": GAMMA,
        "bias": BIAS,
        "report_sd": REPORT_SD,
    }
    result = summarize(log_likelihood, grids)
    posterior = np.exp(log_likelihood - logsumexp(log_likelihood))
    marginal = posterior.sum(axis=(0, 2, 3, 4))
    # Equal prior weight on learning and on no learning, whatever the grid's composition.
    learning = STRENGTH <= LEARNING_LIMIT
    odds = marginal[learning].mean() / marginal[~learning].mean()
    result["learning_probability"] = float(odds / (1 + odds))
    return result


def _report_grid(model, items, reports, delta):
    """Log-likelihood over (delta, gamma, bias, report_sd) for the given items."""
    latent = REPORT_MODELS[model](items, delta, GAMMA[None, :, None])
    latent = np.broadcast_to(
        latent, (np.shape(delta)[0] if np.ndim(delta) else 1, *latent.shape[-2:])
    )
    forecast = (items["kind"] != "probe").astype(float)
    means = latent[:, :, None, :] + BIAS[None, None, :, None] * forecast
    return np.stack([report_log_likelihood(means, reports, sd) for sd in REPORT_SD], axis=-1)


def _marginal(weights, grid):
    cdf = np.cumsum(weights)
    lo, hi = np.searchsorted(cdf, [0.05, 0.95])
    return {
        "mean": float(weights @ grid),
        "interval_90": [float(grid[min(lo, len(grid) - 1)]), float(grid[min(hi, len(grid) - 1)])],
    }


def fit_cues(model, items, reports):
    """A disposition for each description slot, with shared sensitivity, bias and noise.

    Stated base-rate answers are not used for the fit; they are returned beside the implied
    dispositions so the two can be compared.
    """
    slots, kinds = items["slot"], items["kind"]
    evidence = kinds != "rate"

    def part(mask):
        return {k: v[mask] for k, v in items.items()}, reports[mask]

    anchor_items, anchor_reports = part(evidence & (slots < 0))
    shared = _report_grid(model, anchor_items, anchor_reports, 0.5)[0]
    levels = sorted(set(slots[slots >= 0].tolist()))
    per_slot = np.stack(
        [
            _report_grid(model, *part(evidence & (slots == s)), DISPOSITION[:, None, None])
            for s in levels
        ]
    )
    slot_evidence = logsumexp(per_slot, axis=1)
    shared = shared + (slot_evidence - np.log(len(DISPOSITION))).sum(axis=0)
    total = logsumexp(shared)
    posterior = np.exp(shared - total)
    conditional = np.exp(per_slot - slot_evidence[:, None])
    marginals = (conditional * posterior[None, None]).sum(axis=(2, 3, 4))
    stated = {s: [float(r) for r in reports[(kinds == "rate") & (slots == s)]] for s in levels}
    return {
        "log_evidence": float(total - np.log(posterior.size)),
        "slots": [
            {"slot": s, "implied": _marginal(marginals[i], DISPOSITION), "stated": stated[s]}
            for i, s in enumerate(levels)
        ],
        "parameters": {
            name: _marginal(posterior.sum(axis=tuple(j for j in range(3) if j != axis)), grid)
            for axis, (name, grid) in enumerate(
                (("gamma", GAMMA), ("bias", BIAS), ("report_sd", REPORT_SD))
            )
        },
    }
