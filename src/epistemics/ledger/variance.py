"""Between-session variance of description-to-prior mappings.

For one configuration and design, each fresh session k yields implied priors y_kl for the
description levels l, with standard errors s_kl from its own fit. The model is

    y_kl = mu_l + u_k + e_kl + m_kl,   u_k ~ N(0, su^2), e_kl ~ N(0, se^2), m_kl ~ N(0, s_kl^2),

so u is a shift shared by every level in a session (the whole middle moving together) and e is
level-specific. The two components are estimated by restricted maximum likelihood on a grid, with
95% profile-likelihood intervals, on the probability scale.
"""

import numpy as np

GRID = np.round(np.arange(0.0, 0.3001, 0.005), 3)
PROFILE_DROP = 1.92  # Half the 95% chi-square(1) quantile.
MIN_SE = 0.05 / np.sqrt(12)  # A 0.05-wide grid cell.


def standard_errors(intervals):
    """Approximate standard errors from 90% grid intervals, floored at one grid cell."""
    widths = np.array([hi - lo for lo, hi in intervals])
    return np.maximum(widths / 3.29, MIN_SE)


def log_likelihood(y, s, su, se):
    """REML log-likelihood of sessions y (K x L) with standard errors s (K x L)."""
    k, levels = y.shape
    information = np.zeros((levels, levels))
    weighted = np.zeros(levels)
    parts = []
    for row, errors in zip(y, s, strict=True):
        cov = su**2 * np.ones((levels, levels)) + np.diag(se**2 + errors**2)
        inverse = np.linalg.inv(cov)
        information += inverse
        weighted += inverse @ row
        parts.append((row, cov, inverse))
    mu = np.linalg.solve(information, weighted)
    total = -0.5 * np.linalg.slogdet(information)[1]
    for row, cov, inverse in parts:
        residual = row - mu
        total -= 0.5 * (np.linalg.slogdet(cov)[1] + residual @ inverse @ residual)
    return total, mu


def profile(values, surface):
    best = surface.max()
    keep = values[surface >= best - PROFILE_DROP]
    return [float(keep.min()), float(keep.max())]


def estimate(y, s):
    """Session shift, level-specific and total between-session SDs with 95% profile intervals."""
    y, s = np.asarray(y, dtype=float), np.asarray(s, dtype=float)
    if y.shape[0] < 3:
        raise ValueError("At least three sessions are needed")
    surface = np.array([[log_likelihood(y, s, su, se)[0] for se in GRID] for su in GRID])
    i, j = np.unravel_index(int(np.argmax(surface)), surface.shape)
    _, mu = log_likelihood(y, s, GRID[i], GRID[j])
    total = np.sqrt(GRID[:, None] ** 2 + GRID[None, :] ** 2)
    totals = np.round(total, 3).ravel()
    best_by_total = {}
    for value, ll in zip(totals, surface.ravel(), strict=True):
        best_by_total[value] = max(best_by_total.get(value, -np.inf), ll)
    total_values = np.array(sorted(best_by_total))
    total_profile = np.array([best_by_total[v] for v in total_values])
    return {
        "sessions": int(y.shape[0]),
        "levels": int(y.shape[1]),
        "level_means": mu.tolist(),
        "session_shift_sd": {
            "estimate": float(GRID[i]),
            "interval_95": profile(GRID, surface.max(axis=1)),
        },
        "level_specific_sd": {
            "estimate": float(GRID[j]),
            "interval_95": profile(GRID, surface.max(axis=0)),
        },
        "total_sd": {
            "estimate": float(np.hypot(GRID[i], GRID[j])),
            "interval_95": profile(total_values, total_profile),
        },
        "descriptive_sd_by_level": np.std(y, axis=0, ddof=1).tolist(),
    }


def simulate_sessions(rng, sessions, su, se, means, report_sd=0.1, levels=(1, 2, 3)):
    """Synthetic fresh sessions through the real per-session fit of the relay cue module."""
    from epistemics.dispositions import design, fit, observers
    from epistemics.dispositions.response import sample_reports

    items = design.corroboration_cues()
    forecast = ~np.isin(items["kind"], ("probe", "rate"))
    y, s = [], []
    for _ in range(sessions):
        shift = rng.normal(0, su)
        truth = np.clip(np.array(means) + shift + rng.normal(0, se, len(means)), 0.01, 0.99)
        truth[[0, -1]] = np.array(means)[[0, -1]]  # Extremes stay fixed.
        latent = observers.cue_observer(observers.corroboration, items, truth, 1.0)
        reports = sample_reports(latent + 0.0 * forecast, report_sd, rng)
        result = fit.fit_cues("dependence", items, reports)
        chosen = [result["slots"][level]["implied"] for level in levels]
        y.append([c["mean"] for c in chosen])
        s.append(standard_errors([c["interval_90"] for c in chosen]))
    return np.array(y), np.array(s)


def validate(seed=20260928, sessions=6, repetitions=30):
    """Recovery of the variance components from synthetic sessions at known values."""
    rng = np.random.default_rng(seed)
    means = [0.05, 0.45, 0.5, 0.55, 0.9]
    cells = []
    for su in (0.0, 0.05, 0.1):
        for se in (0.02, 0.06, 0.1):
            rows = {"total_sd": [], "session_shift_sd": [], "level_specific_sd": []}
            truth = {
                "total_sd": float(np.hypot(su, se)),
                "session_shift_sd": su,
                "level_specific_sd": se,
            }
            for _ in range(repetitions):
                y, s = simulate_sessions(rng, sessions, su, se, means)
                result = estimate(y, s)
                for name in rows:
                    low, high = result[name]["interval_95"]
                    rows[name].append((result[name]["estimate"], low <= truth[name] <= high))
            cells.append(
                {
                    **{f"true_{name}": value for name, value in truth.items()},
                    **{
                        f"mean_{name}": float(np.mean([e for e, _ in values]))
                        for name, values in rows.items()
                    },
                    **{
                        f"coverage_{name}": float(np.mean([c for _, c in values]))
                        for name, values in rows.items()
                    },
                }
            )
    return {
        "schema_version": "epistemics.variance-validation.v1",
        "seed": seed,
        "sessions": sessions,
        "repetitions": repetitions,
        "cells": cells,
        "scope": "Synthetic sessions through the real per-session fit; clipping at 0.01 and 0.99; report noise 0.1 on the log-odds scale",
    }
