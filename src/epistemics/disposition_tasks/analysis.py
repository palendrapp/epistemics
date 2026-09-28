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
CUE_MODELS = {
    "corroboration-cues": "dependence",
    "disclosure-cues": "disclosure",
    "corroboration-range": "dependence",
    "corroboration-dossier": "dependence",
    "disclosure-dossier": "disclosure",
}
RANGE_TARGETS = 5


def range_summary(result):
    """Targets (the same descriptions in every variant) and the comparison outlets."""
    implied = [s["implied"]["mean"] for s in result["slots"]]
    stated = [s["stated"][0] for s in result["slots"]]
    return {
        "targets_implied": implied[:RANGE_TARGETS],
        "targets_stated": stated[:RANGE_TARGETS],
        "comparisons_implied": implied[RANGE_TARGETS:],
        "comparisons_stated": stated[RANGE_TARGETS:],
        "stated_minus_implied_mae": float(np.mean(np.abs(np.subtract(stated, implied)))),
        "targets_mean": float(np.mean(implied[:RANGE_TARGETS])),
    }


def ranks(values):
    """Average ranks, so tied values (to 0.001) share a rank."""
    values = np.round(np.asarray(values, dtype=float), 3)
    order = np.argsort(values, kind="stable")
    result = np.empty(len(values))
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        result[order[i : j + 1]] = (i + j) / 2
        i = j + 1
    return result


def spearman(a, b):
    a, b = ranks(np.asarray(a)), ranks(np.asarray(b))
    if np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def cue_summary(result):
    """Implied against stated priors, the designed ordering and the irrelevant control."""
    implied = [s["implied"]["mean"] for s in result["slots"]]
    stated = [s["stated"][0] for s in result["slots"]]
    irrelevant = result["slots"][2]["implied"]
    low, high = irrelevant["interval_90"]
    shift = irrelevant["mean"] - 0.5
    return {
        "implied": implied,
        "stated": stated,
        "stated_minus_implied_mae": float(np.mean(np.abs(np.subtract(stated, implied)))),
        "stated_implied_spearman": spearman(stated, implied),
        "designed_order_spearman": spearman(range(len(implied)), implied),
        "range": float(max(implied) - min(implied)),
        # Moved: beyond one grid step from indifference, with an interval that excludes it.
        "irrelevant_shift": float(shift),
        "irrelevant_moved": bool(abs(shift) > 0.05 and not low <= 0.5 <= high),
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
    if manifest.module in CUE_MODELS:
        result = fit.fit_cues(CUE_MODELS[manifest.module], items, responses)
        if manifest.module.endswith("-range"):
            summary = {"range": range_summary(result)}
        else:
            summary = {"cues": cue_summary(result)}
        return {
            "module": manifest.module,
            "variant": manifest.variant,
            "fit": result,
            **summary,
            "rows": rows,
        }
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
