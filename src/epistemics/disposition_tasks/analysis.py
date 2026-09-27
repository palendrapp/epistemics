"""Per-context fits of the disposition model and its rivals.

T2 and T3 estimate the disposition from all 24 checkpoints (forecasts and structure probes).
Rival models make no probe predictions, so model comparison uses the 18 forecasts only. Learning
variants add a fit in which the disposition is learned from structures revealed before each case.
T5 fits both certainty functions to the stated maximum prices.
"""

import numpy as np

from epistemics.disposition_tasks.render import items_for
from epistemics.dispositions import fit, observers

MODELS = {
    "corroboration": ("dependence", "fixed_discount"),
    "disclosure": ("disclosure", "linear_skepticism"),
    "checks": ("linear", "entropy"),
}


def subset(items, mask):
    return {k: v[mask] for k, v in items.items()}


def comparison(fits):
    evidence = {m: r["log_evidence"] for m, r in fits.items()}
    peak = max(evidence.values())
    weights = {m: float(np.exp(v - peak)) for m, v in evidence.items()}
    total = sum(weights.values())
    return {
        "log_evidence": evidence,
        "model_probability": {m: w / total for m, w in weights.items()},
        "preferred": max(evidence, key=evidence.get),
        "scope": "Equal model priors and uniform grid priors; conditional on these two candidates",
    }


def certainty_comparison(fits):
    """A function is selected only when the value of certainty is credibly positive.

    The functions coincide at zero, and below zero every negative latent price is reported as
    zero, so they then differ only through the few decision-relevant checks.
    """
    result = comparison(fits)
    low, _ = fits[result["preferred"]]["parameters"]["certainty_value"]["interval_90"]
    if low <= 0:
        result["preferred"] = "undetermined"
    return result


def analyze(manifest, observations):
    items = items_for(manifest.module)
    field = "points" if manifest.module == "checks" else "probability"
    responses = np.full(len(manifest.order), np.nan)
    for observation, index in zip(observations, manifest.order, strict=True):
        responses[index] = getattr(observation.answer, field)
    rows = [
        {"case": case + 1, "item": index, "response": float(responses[index])}
        for case, index in enumerate(manifest.order)
    ]
    model, rival = MODELS[manifest.module]
    if manifest.module == "checks":
        fits = {f: fit.fit_checks(f, items, responses) for f in (model, rival)}
        decision, _ = observers.check_values(items, "linear")
        zero = np.abs(decision) < 1e-9
        return {
            "module": manifest.module,
            "variant": manifest.variant,
            "fits": fits,
            "certainty_function": certainty_comparison(fits),
            "mean_points": {
                "zero_decision_value": float(responses[zero].mean()),
                "positive_decision_value": float(responses[~zero].mean()),
            },
            "rows": rows,
        }
    forecast = items["kind"] != "probe"
    only = subset(items, forecast)
    rivals = {m: fit.fit_reports(m, only, responses[forecast]) for m in (model, rival)}
    result = {
        "module": manifest.module,
        "variant": manifest.variant,
        "fit": fit.fit_reports(model, items, responses),
        "forecast_only": rivals,
        "model_comparison": comparison(rivals),
        "rows": rows,
    }
    if manifest.revealed is not None:
        successes, trials = observers.revealed_counts(manifest.order, manifest.revealed)
        result["learning"] = fit.fit_learning(model, items, responses, successes, trials)
        result["revealed_rate"] = float(np.mean([r for r in manifest.revealed if r is not None]))
    return result
