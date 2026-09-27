"""Synthetic respondents, the paired neglect-weight estimator and a precision study.

A respondent with neglect weight chi reports the log-odds normative + chi * (naive - normative),
then probability noise and whole-percent rounding. chi = 0 is Bayesian; chi = 1 counts every
relay as new evidence or ignores what a stated disclosure rule implies. The estimator pairs each
manipulated presentation with its matched control on the same world, so world-level
idiosyncrasies cancel. These are measurement checks, not models of any real respondent.
"""

import numpy as np

from epistemics.research_world.world import (
    PAIRS,
    generate,
    logit,
    naive_logit,
    normative_logit,
    sigmoid,
)


def report(world, chi, noise_sd, rng):
    x = normative_logit(world) + chi * (naive_logit(world) - normative_logit(world))
    p = sigmoid(x) + float(rng.normal(0, noise_sd))
    return float(min(0.99, max(0.01, round(p, 2))))


def paired_estimate(pairs):
    """pairs: (control_world, control_report, manipulated_world, manipulated_report)."""
    observed, predicted = [], []
    for _control, p_control, manipulated, p_manipulated in pairs:
        gap = naive_logit(manipulated) - normative_logit(manipulated)
        if abs(gap) < 1e-9:
            continue
        observed.append(logit(p_manipulated) - logit(p_control))
        predicted.append(gap)
    x, y = np.array(predicted), np.array(observed)
    if len(x) < 2:
        raise ValueError("At least two informative pairs are required")
    chi = float(x @ y / (x @ x))
    residual = y - chi * x
    se = float(np.sqrt(residual @ residual / (len(x) - 1) / (x @ x)))
    return {"chi": chi, "se": se, "pairs": len(x)}


def collect_pairs(family, seeds, chi, noise_sd, rng):
    rows = []
    for seed in seeds:
        worlds = generate(int(seed), family)
        control, manipulated = (worlds[p] for p in PAIRS[family])
        rows.append(
            (
                control,
                report(control, chi, noise_sd, rng),
                manipulated,
                report(manipulated, chi, noise_sd, rng),
            )
        )
    return rows


def precision(
    seed=0, worlds=(8, 16, 24, 32, 48), noise=(0.02, 0.08), chis=(0.0, 0.5, 1.0), reps=400
):
    """Sampling distribution of chi-hat per family, number of worlds, noise and true chi."""
    rng = np.random.default_rng(seed)
    results = []
    for family in PAIRS:
        for sd in noise:
            for n in worlds:
                estimates = {}
                for chi in chis:
                    values = []
                    for _ in range(reps):
                        seeds = rng.integers(0, 2**31, n)
                        values.append(
                            paired_estimate(collect_pairs(family, seeds, chi, sd, rng))["chi"]
                        )
                    estimates[chi] = np.array(values)
                cut = 0.25
                results.append(
                    {
                        "family": family,
                        "noise_sd": sd,
                        "worlds": n,
                        "mean_chi_hat": {str(c): float(v.mean()) for c, v in estimates.items()},
                        "sd_chi_hat": {str(c): float(v.std()) for c, v in estimates.items()},
                        # Classification at the midpoint separating a Bayesian from half neglect.
                        "separates_0_from_0_5": float(
                            (np.mean(estimates[0.0] < cut) + np.mean(estimates[0.5] >= cut)) / 2
                        ),
                    }
                )
    return {
        "schema_version": "epistemics.research-world-precision.v1",
        "seed": seed,
        "repetitions": reps,
        "results": results,
        "scope": "Paired presentations on independent generated worlds; one report per presentation; probability noise and whole-percent rounding; no mixture of respondent types, order effects or learning across companies",
    }
