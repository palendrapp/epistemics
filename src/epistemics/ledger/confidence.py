"""Confidence persuasion: the transfer test across four surfaces
(docs/confidence-transfer-design.md).

The trait is w_conf, the log-odds a configuration gives per step of a source's expressed
confidence when nothing says how reliable the source is, fitted by the T1-open model on the same
24 cases on every surface. Units are configurations x surfaces, one session each.

Primary: leave one surface out. A configuration's deviation from the other configurations on a
held-out surface is predicted from its mean deviation on the other three; the gain is 1 - MSE of
that prediction / MSE of predicting no deviation, with a within-surface permutation p.
"""

import numpy as np

from epistemics.ledger.battery_v2 import deviations, shuffled

SURFACES = ("advice-peer", "advice-relay", "advice-sensor", "advice-agent")
SOCIAL = ("advice-peer", "advice-relay")
CONFIGURATIONS = ("astra-low", "astra", "astra-high", "sol-low", "sol", "sol-high", "luna", "terra")
PERMUTATIONS = 2000


def gain(y):
    """Leave-one-surface-out transfer gain and sign agreement (y: configurations x surfaces)."""
    d = deviations(y)
    pred = np.full_like(d, np.nan)
    for t in range(d.shape[1]):
        block = np.delete(d, t, axis=1)
        has = ~np.isnan(block)
        pred[:, t] = np.where(
            has.any(axis=1), np.nansum(block, axis=1) / np.maximum(has.sum(axis=1), 1), np.nan
        )
    ok = ~np.isnan(d) & ~np.isnan(pred)
    denom = float(np.sum(d[ok] ** 2))
    return {
        "gain": float(1 - np.sum((d[ok] - pred[ok]) ** 2) / denom) if denom > 0 else None,
        "cells": int(ok.sum()),
        "sign_agreement": float(np.mean(np.sign(d[ok]) == np.sign(pred[ok]))) if ok.any() else None,
    }


def test(y, rng, permutations=PERMUTATIONS):
    observed = gain(y)
    if observed["gain"] is None:
        return {**observed, "p": None}
    null = [gain(shuffled(y, rng))["gain"] for _ in range(permutations)]
    null = np.array([g for g in null if g is not None])
    return {**observed, "p": float((1 + np.sum(null >= observed["gain"])) / (1 + len(null)))}


# Power (before the preregistration). Configuration values are the task-A estimates so far:
# Astra 0.00-0.10, Sol 0.29-0.50, Luna 0.06, Terra 0.88. Estimates vary within a configuration by
# about 0.08 (Astra and Sol retests) for GPT-6 and more for GPT-5.6, whose fits are noisier.
TRAIT = {
    "astra-low": 0.00,
    "astra": 0.05,
    "astra-high": 0.00,
    "sol-low": 0.29,
    "sol": 0.42,
    "sol-high": 0.50,
    "luna": 0.06,
    "terra": 0.88,
}
NOISE = {c: (0.15 if c in ("luna", "terra") else 0.08) for c in CONFIGURATIONS}


def simulate(rng, scenario):
    """One data set: 'general' (every surface reflects the trait), 'social' (only A and B do;
    C and D carry an unrelated configuration effect of the same spread), 'none' (every surface
    carries an unrelated effect of the same spread)."""
    theta = np.array([TRAIT[c] for c in CONFIGURATIONS])
    noise = np.array([NOISE[c] for c in CONFIGURATIONS])
    y = np.empty((len(CONFIGURATIONS), len(SURFACES)))
    for t, surface in enumerate(SURFACES):
        shares = scenario == "general" or (scenario == "social" and surface in SOCIAL)
        effect = theta if shares else rng.permutation(theta)
        y[:, t] = effect + rng.normal(0, 0.1) + rng.normal(0, noise)
    return y


def power(datasets=400, seed=20261015, permutations=500):
    rng = np.random.default_rng(seed)
    result = {}
    for scenario in ("general", "social", "none"):
        passes, gains = 0, []
        for _ in range(datasets):
            r = test(simulate(rng, scenario), rng, permutations)
            gains.append(r["gain"])
            passes += r["gain"] is not None and r["gain"] > 0 and r["p"] < 0.05
        result[scenario] = {
            "pass_rate": passes / datasets,
            "median_gain": float(np.median(gains)),
            "datasets": datasets,
        }
    return {
        "schema_version": "epistemics.confidence-power.v1",
        "trait": TRAIT,
        "noise": NOISE,
        "result": result,
    }


def analyse(roots, seed=20261016):
    """The preregistered analysis: w_conf per configuration and surface from the collections,
    the leave-one-surface-out test, and the secondary tests."""
    from epistemics.ledger import social

    cells = {}
    for row in social.pilot(roots)["rows"]:
        if row["module"] in SURFACES and row["variant"] == "peer-open":
            cells.setdefault((row["configuration"], row["module"]), []).append(row["parameters"])
    y = np.full((len(CONFIGURATIONS), len(SURFACES)), np.nan)
    intervals = {}
    for (config, surface), fits in cells.items():
        if config in CONFIGURATIONS:
            first = fits[0]["w_conf"]  # one session per cell; the first collected is used
            y[CONFIGURATIONS.index(config), SURFACES.index(surface)] = first["mean"]
            intervals[f"{config}/{surface}"] = first["interval_90"]
    rng = np.random.default_rng(seed)
    primary = test(y, rng)
    direction = [
        (
            effort,
            surface,
            y[CONFIGURATIONS.index(f"sol{effort}"), s],
            y[CONFIGURATIONS.index(f"astra{effort}"), s],
        )
        for effort in ("-low", "", "-high")
        for s, surface in enumerate(SURFACES)
    ]
    wins = [s > a for _, _, s, a in direction if not (np.isnan(s) or np.isnan(a))]
    relay = SURFACES.index("advice-relay")
    return {
        "schema_version": "epistemics.confidence-transfer.v1",
        "matrix": {
            c: dict(zip(SURFACES, map(float, y[i]), strict=True))
            for i, c in enumerate(CONFIGURATIONS)
        },
        "intervals": intervals,
        "primary": primary,
        "sol_above_astra": {"wins": int(sum(wins)), "comparisons": len(wins)},
        "relay_excludes_zero": {
            c: bool(intervals.get(f"{c}/advice-relay", [0, 0])[0] > 0) for c in CONFIGURATIONS
        },
        "relay_values": {c: float(y[i, relay]) for i, c in enumerate(CONFIGURATIONS)},
        "social_minus_nonsocial": {
            c: float(np.nanmean(y[i, :2]) - np.nanmean(y[i, 2:]))
            for i, c in enumerate(CONFIGURATIONS)
        },
    }
