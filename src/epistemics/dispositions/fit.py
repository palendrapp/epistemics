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


# Capacity battery, Part B (model 0.8): the disposition applied to each case is a baseline plus a
# fixed fraction of the ideal observer's rate for that case's audit record. Uptake 1 is the ideal
# revision and 0 ignores the record; above 1 over-revises.
UPTAKE_BASE = np.round(np.arange(0, 0.301, 0.025), 3)
UPTAKE = np.round(np.arange(0, 1.501, 0.05), 2)
# Posterior probability that uptake is below this is reported as "ignores".
IGNORES_BELOW = 0.1


def fit_uptake(model, items, reports, ideal):
    """Baseline, uptake, sensitivity, bias and report noise, from forecasts only.

    `ideal` gives, per item, the ideal observer's rate for its record (0 where the item has none;
    the observer ignores the disposition on anchors).
    """
    reports = np.asarray(reports, dtype=float)
    keep = np.asarray(items["kind"]) != "rate"
    part = {k: np.asarray(v)[keep] for k, v in items.items()}
    target = np.asarray(ideal, dtype=float)[keep]
    delta = np.clip(
        UPTAKE_BASE[:, None, None, None] + UPTAKE[None, :, None, None] * target, 0.0, 1.0
    )
    latent = REPORT_MODELS[model](part, delta, GAMMA[None, None, :, None])
    forecast = (part["kind"] != "probe").astype(float)
    means = latent[..., None, :] + BIAS[None, None, None, :, None] * forecast
    log_likelihood = np.stack(
        [report_log_likelihood(means, reports[keep], sd) for sd in REPORT_SD], axis=-1
    )
    grids = {
        "baseline": UPTAKE_BASE,
        "uptake": UPTAKE,
        "gamma": GAMMA,
        "bias": BIAS,
        "report_sd": REPORT_SD,
    }
    result = summarize(log_likelihood, grids)
    posterior = np.exp(log_likelihood - logsumexp(log_likelihood))
    marginal = posterior.sum(axis=(0, 2, 3, 4))
    result["ignores_probability"] = float(marginal[UPTAKE < IGNORES_BELOW].sum())
    return result


# Capacity battery, Part A: at each load level, the share of weight on the structure-neglecting
# answer (eta), forecast bias and report noise, on grids under uniform priors.
LOAD_ETA = np.round(np.linspace(0, 1, 11), 2)
REPEAT_EDGE = 0.01


# Model 0.8: the load curve fitted jointly over all levels, for designs with few cases per level.
# Report noise is log-linear in the level, tau_l = tau_0 * exp(load_slope * l), and the neglect
# weight linear, eta_l = eta_0 + eta_slope * l (clipped to [0, 1]).
# The noise and bias grids are finer than the per-level fits': with noise near the floor, a bias
# between coarse grid points is absorbed as extra noise at the low levels, which flattens the
# fitted slope (recovery correlation 0.81-0.85 with the coarse grids, 0.87-0.90 with these).
CURVE_SD0 = np.round(np.exp(np.linspace(np.log(0.01), np.log(1.0), 21)), 4)
CURVE_SLOPE = np.round(np.arange(-0.5, 2.501, 0.1), 2)
CURVE_ETA0 = np.round(np.arange(0, 0.501, 0.1), 2)
CURVE_ETA_SLOPE = np.round(np.arange(0, 0.501, 0.025), 3)
CURVE_BIAS = np.round(np.arange(-0.4, 0.401, 0.025), 3)


def fit_load_curve(model, items, reports):
    """Grid posterior for the load curve: tau_0, load_slope, eta_0, eta_slope and bias."""
    reports = np.asarray(reports, dtype=float)
    exact, neglect = observers.load_answers(model, items)
    level = np.asarray(items["load"], dtype=float)
    eta = np.clip(CURVE_ETA0[:, None, None] + CURVE_ETA_SLOPE[None, :, None] * level, 0.0, 1.0)
    means = (1 - eta) * exact + eta * neglect
    means = means[:, :, None, :] + CURVE_BIAS[None, None, :, None]
    log_likelihood = np.empty(
        (len(CURVE_SD0), len(CURVE_SLOPE), len(CURVE_ETA0), len(CURVE_ETA_SLOPE), len(CURVE_BIAS))
    )
    for a, sd0 in enumerate(CURVE_SD0):
        for b, slope in enumerate(CURVE_SLOPE):
            log_likelihood[a, b] = report_log_likelihood(
                means, reports, sd0 * np.exp(slope * level)
            )
    grids = {
        "tau_0": CURVE_SD0,
        "load_slope": CURVE_SLOPE,
        "eta_0": CURVE_ETA0,
        "eta_slope": CURVE_ETA_SLOPE,
        "bias": CURVE_BIAS,
    }
    return summarize(log_likelihood, grids)


# Structural load (model 0.10): a wrong answer is attributed to a structure when one of that
# structure's misreadings (observers.composite_partials, or ignoring every structure) reproduces
# it, within the 1.5 points used for exactness. A misreading can only explain an error where it
# changes the answer, so each structure's error rate is over those cases.
ATTRIBUTION_EDGE = 0.015


def load_errors(model, items, reports):
    """Wrong answers by the structure whose misreading reproduces them (composite model only)."""
    if model != "composite":
        return None
    reports = np.asarray(reports, dtype=float)
    exact = 1 / (1 + np.exp(-observers.composite(items)))
    readings = {
        **observers.composite_partials(items),
        "every structure ignored": observers.composite(items, ignore_copy=True, ignore_mis=True),
    }
    readings = {name: 1 / (1 + np.exp(-v)) for name, v in readings.items()}
    wrong = np.abs(reports - exact) > ATTRIBUTION_EDGE
    by_structure, matched_any = {}, np.zeros(len(reports), dtype=bool)
    for name, answer in readings.items():
        possible = np.abs(answer - exact) > ATTRIBUTION_EDGE
        matched = wrong & possible & (np.abs(reports - answer) <= ATTRIBUTION_EDGE)
        matched_any |= matched
        by_structure[name] = {"opportunities": int(possible.sum()), "errors": int(matched.sum())}
    loads = np.asarray(items["load"])
    return {
        "wrong": int(wrong.sum()),
        "attributed": int((wrong & matched_any).sum()),
        "by_structure": by_structure,
        "cases": [
            {
                "item": int(i),
                "load": int(loads[i]),
                "response": float(reports[i]),
                "exact": float(exact[i]),
                "matches": [
                    name
                    for name, answer in readings.items()
                    if abs(answer[i] - exact[i]) > ATTRIBUTION_EDGE
                    and abs(reports[i] - answer[i]) <= ATTRIBUTION_EDGE
                ],
            }
            for i in np.flatnonzero(wrong)
        ],
    }


def fit_load(model, items, reports, curve=True):
    """Per load level: eta, bias and report noise; the slopes of log noise and of eta over load;
    the model-free noise between repeated cases; and (model 0.8) the joint load curve."""
    reports = np.asarray(reports, dtype=float)
    exact, neglect = observers.load_answers(model, items)
    loads = np.asarray(items["load"])
    levels = []
    for level in sorted(set(loads.tolist())):
        mask = loads == level
        means = (1 - LOAD_ETA)[:, None, None] * exact[mask] + LOAD_ETA[:, None, None] * neglect[
            mask
        ]
        means = means + BIAS[None, :, None]
        ll = np.stack(
            [report_log_likelihood(means, reports[mask], sd) for sd in REPORT_SD], axis=-1
        )
        fitted = summarize(ll, {"eta": LOAD_ETA, "bias": BIAS, "report_sd": REPORT_SD})
        truth = 1 / (1 + np.exp(-exact[mask]))
        levels.append(
            {
                "load": int(level),
                "readings": int(np.asarray(items["n"])[mask][0]),
                "cases": int(mask.sum()),
                **fitted["parameters"],
                "exact_share": float(np.mean(np.abs(reports[mask] - truth) <= 0.015)),
            }
        )
    x = np.array([lv["load"] for lv in levels], dtype=float)
    log_tau = np.log([lv["report_sd"]["mean"] for lv in levels])
    eta = np.array([lv["eta"]["mean"] for lv in levels])
    repeat_of = np.asarray(items["repeat_of"])
    pairs = [(i, int(j)) for i, j in enumerate(repeat_of) if j >= 0]
    clipped = np.clip(reports, REPEAT_EDGE, 1 - REPEAT_EDGE)
    logits = np.log(clipped) - np.log1p(-clipped)
    return {
        "levels": levels,
        "load_slope": float(np.polyfit(x, log_tau, 1)[0]) if len(x) > 1 else None,
        "eta_slope": float(np.polyfit(x, eta, 1)[0]) if len(x) > 1 else None,
        "repeat_noise": float(np.mean([abs(logits[i] - logits[j]) for i, j in pairs]))
        if pairs
        else None,
        "curve": fit_load_curve(model, items, reports) if curve else None,
        "errors": load_errors(model, items, reports),
    }
