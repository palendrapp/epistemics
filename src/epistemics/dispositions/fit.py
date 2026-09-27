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
REPORT_SD = np.array([0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.65, 0.8, 1.0])
CERTAINTY_VALUE = np.arange(-40.0, 160.1, 4.0)
DECISION_WEIGHT = np.round(np.arange(0.5, 1.501, 0.1), 2)
WTP_SD = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 14.0])

REPORT_MODELS = {
    "dependence": observers.corroboration,
    "fixed_discount": observers.fixed_discount,
    "disclosure": observers.disclosure,
    "linear_skepticism": observers.linear_skepticism,
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
