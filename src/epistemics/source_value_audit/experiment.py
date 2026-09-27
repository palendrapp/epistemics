"""Frozen, reproducible offline cohorts and world-clustered Monte Carlo summaries."""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from epistemics.source_inference.world import Probe
from epistemics.source_learning.simulation import memory_manifest
from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_selective.policy import POLICIES, RULE, expected_value, offers
from epistemics.source_selective.service import fingerprint as selective_fingerprint
from epistemics.source_value_audit import VERSION
from epistemics.source_value_audit.core import (
    REPORTERS,
    PublicCase,
    expected_outcome,
    oracle_probability,
    public_probability,
    realized_outcome,
)


def fingerprint():
    root = Path(__file__).parent
    return digest(
        encoded(
            {
                "selective": selective_fingerprint(),
                "audit": {p.name: digest(p.read_bytes()) for p in sorted(root.glob("*.py"))},
            }
        )
    )


def seed_for(batch_seed, index, channel):
    return int(digest(encoded([VERSION, batch_seed, index, channel]))[:16], 16)


def make_plan(batch_seeds=(20260927, 20270927), worlds_per_batch=512):
    if (
        type(worlds_per_batch) is not int
        or not 2 <= worlds_per_batch <= 4096
        or worlds_per_batch % 2
    ):
        raise ValueError("Use an even number of worlds per batch between 2 and 4096")
    if (
        not batch_seeds
        or len(batch_seeds) > 8
        or any(type(s) is not int or s < 0 for s in batch_seeds)
        or len(set(batch_seeds)) != len(batch_seeds)
    ):
        raise ValueError("Use one to eight distinct nonnegative integer batch seeds")
    return {
        "schema_version": "epistemics.source-value-audit-plan.v1",
        "version": VERSION,
        "implementation_sha256": fingerprint(),
        "selective_implementation_sha256": selective_fingerprint(),
        "batch_seeds": list(batch_seeds),
        "worlds_per_batch": worlds_per_batch,
        "companies_per_world": 12,
        "reporters": [asdict(r) for r in REPORTERS],
        "policies": list(POLICIES),
        "purchase_rule": RULE,
        "expected_effect_floor": 0.01,
        "precision_half_width": 0.005,
        "strata": "Public rounded EVSI minus price: <=0, (0,.01), >=.01; fixed before outcomes",
        "uncertainty": "Normal 95% Monte Carlo intervals of independent world means; not agent uncertainty",
        "pairing": "Nonoverlapping consecutive world pairs within each batch; strict negative net contrast",
        "scope": "Offline synthetic audit only; no parameter fitting, real-agent counterfactuals, account calls or certification",
    }


def public_case(manifest, company_index, price):
    """Build public input before resolving this company or revealing any check.

    All previous outcomes are disclosed regardless of purchase. Given those states,
    independent panels give no additional source-process information; the specified
    public observer therefore has the same source-learning trajectory in every policy.
    """
    company = manifest.companies[company_index]
    record = company.record.public
    return PublicCase(
        history=tuple(r.public for r in manifest.archive)
        + tuple(c.record.public for c in manifest.companies[:company_index]),
        probe=Probe(
            source_id=record.source_id,
            world=record.world,
            count=record.count,
            prior_strong=company.prior_strong,
        ),
        threshold=company.threshold,
        price=price,
    )


def simulate_world(batch_seed, index):
    manifest = memory_manifest(seed_for(batch_seed, index, "world"))
    prices = offers(manifest, seed_for(batch_seed, index, "price"))
    cells = {r.name: {policy: [] for policy in POLICIES} for r in REPORTERS}
    cases = []
    for i, offer in enumerate(prices, 12):
        company = manifest.companies[i]
        assert offer["company_id"] == company.company_id
        case = public_case(manifest, i, offer["available_check_cost"])
        q = oracle_probability(case.probe, company.record.source)
        public = public_probability(case)
        public_net_evsi = expected_value(round(public, 2), case.threshold) - case.price
        row = {
            "batch_seed": batch_seed,
            "world_index": index,
            "company_id": company.company_id,
            "threshold": case.threshold,
            "price": case.price,
            "oracle_probability": q,
            "public_probability": public,
            "public_net_evsi": public_net_evsi,
            "public_stratum": "nonpositive"
            if public_net_evsi <= 1e-12
            else "small_positive"
            if public_net_evsi < 0.01
            else "at_least_0.01",
            "strong": company.record.public.resolved_strong,
            "panel_count": company.independent_panel.count,
        }
        for reporter in REPORTERS:
            p = reporter.report(q, public)
            for policy in POLICIES:
                expected = expected_outcome(q, p, case.threshold, case.price, policy)
                realized = realized_outcome(
                    p,
                    case.threshold,
                    case.price,
                    policy,
                    strong=row["strong"],
                    count=row["panel_count"],
                )
                # These are mathematical invariants, not empirical success gates.
                if min(expected[k] for k in ("purchase_regret", "action_regret")) < -1e-12:
                    raise ValueError("Negative regret: expectation calculation is inconsistent")
                if reporter.name == "oracle" and policy == "cost_aware":
                    if expected["total_regret"] > 1e-10:
                        raise ValueError("Known-process policy must attain its own optimum")
                cells[reporter.name][policy].append(expected | realized)
                if reporter.name in ("oracle", "public_rounded") and policy == "cost_aware":
                    for key in ("buy", "expected_gain_over_none", "realized_gain_over_none"):
                        row[f"{reporter.name}_{key}"] = expected.get(key, realized.get(key))
        cases.append(row)
    world = {
        "batch_seed": batch_seed,
        "world_index": index,
        "cells": {
            reporter: {
                policy: {key: float(np.mean([r[key] for r in rows])) for key in rows[0]}
                for policy, rows in policies.items()
            }
            for reporter, policies in cells.items()
        },
    }
    return cases, world


def estimate(values):
    x = np.asarray(values, dtype=float)
    if len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("At least two finite independent units required")
    mean = float(x.mean())
    sd = float(x.std(ddof=1))
    se = sd / len(x) ** 0.5
    return {
        "mean": mean,
        "world_sd": sd,
        "monte_carlo_se": se,
        "monte_carlo_95_interval": [mean - 1.96 * se, mean + 1.96 * se],
        "independent_units": len(x),
    }


def summarize_worlds(worlds):
    result = {}
    for reporter in REPORTERS:
        policies = {}
        for policy in POLICIES:
            rows = [w["cells"][reporter.name][policy] for w in worlds]
            stats = {key: estimate([r[key] for r in rows]) for key in rows[0]}
            stats["realized_minus_expected_gain"] = estimate(
                [r["realized_gain_over_none"] - r["expected_gain_over_none"] for r in rows]
            )
            pair_gains = [
                (rows[i]["realized_gain_over_none"] + rows[i + 1]["realized_gain_over_none"]) / 2
                for i in range(0, len(rows), 2)
            ]
            negative = sum(x < -1e-12 for x in pair_gains)
            fraction = negative / len(pair_gains)
            stats["two_world_realized_losses"] = {
                "count": negative,
                "pairs": len(pair_gains),
                "fraction": fraction,
                "binomial_monte_carlo_se": (fraction * (1 - fraction) / len(pair_gains)) ** 0.5,
            }
            stats["worlds_for_0.005_normal_half_width"] = int(
                np.ceil((1.96 * stats["realized_gain_over_none"]["world_sd"] / 0.005) ** 2)
            )
            policies[policy] = stats
        result[reporter.name] = policies
    return result


def summarize_cases(cases):
    groups = {"all": cases}
    groups.update({f"price_{p}": [r for r in cases if r["price"] == p] for p in (0.01, 0.04, 0.2)})
    groups.update(
        {
            f"public_{s}": [r for r in cases if r["public_stratum"] == s]
            for s in ("nonpositive", "small_positive", "at_least_0.01")
        }
    )
    return {
        name: {
            "cases": len(rows),
            "fraction": len(rows) / len(cases),
            "oracle_purchase_fraction": float(np.mean([r["oracle_buy"] for r in rows]))
            if rows
            else None,
            "public_purchase_fraction": float(np.mean([r["public_rounded_buy"] for r in rows]))
            if rows
            else None,
            "oracle_expected_gain": float(
                np.mean([r["oracle_expected_gain_over_none"] for r in rows])
            )
            if rows
            else None,
            "public_expected_gain": float(
                np.mean([r["public_rounded_expected_gain_over_none"] for r in rows])
            )
            if rows
            else None,
        }
        for name, rows in groups.items()
    }


def calibration(cases):
    """Fixed-bin reliability, distinct from squared error against privileged q.

    q supplies the conditional expected frequency, H its noisy realization. The
    cluster ratio SE uses whole worlds (including worlds absent from a bin).
    Ten fixed bins can mask within-bin error; no individual calibration is fitted.
    """
    world_ids = sorted({(r["batch_seed"], r["world_index"]) for r in cases})
    result = {}
    for reporter in REPORTERS:
        bins = [[] for _ in range(10)]
        for row in cases:
            p = reporter.report(row["oracle_probability"], row["public_probability"])
            bins[min(int(p * 10), 9)].append((row, p))
        rows = []
        for index, entries in enumerate(bins):
            if not entries:
                rows.append({"bin": index, "count": 0})
                continue
            expected_gap = float(np.mean([r["oracle_probability"] - p for r, p in entries]))
            realized_gap = float(np.mean([r["strong"] - p for r, p in entries]))
            clusters = {world: [0, 0.0, 0.0] for world in world_ids}
            for row, p in entries:
                cluster = clusters[row["batch_seed"], row["world_index"]]
                cluster[0] += 1
                cluster[1] += row["oracle_probability"] - p
                cluster[2] += row["strong"] - p
            average_count = len(entries) / len(world_ids)
            expected_se = estimate(
                [(s[1] - expected_gap * s[0]) / average_count for s in clusters.values()]
            )["monte_carlo_se"]
            realized_se = estimate(
                [(s[2] - realized_gap * s[0]) / average_count for s in clusters.values()]
            )["monte_carlo_se"]
            rows.append(
                {
                    "bin": index,
                    "count": len(entries),
                    "mean_report": float(np.mean([p for _, p in entries])),
                    "expected_frequency": float(
                        np.mean([r["oracle_probability"] for r, _ in entries])
                    ),
                    "realized_frequency": float(np.mean([r["strong"] for r, _ in entries])),
                    "expected_frequency_minus_report": expected_gap,
                    "expected_gap_mc_se": expected_se,
                    "realized_frequency_minus_report": realized_gap,
                    "realized_gap_mc_se": realized_se,
                }
            )
        result[reporter.name] = {
            "bins": rows,
            "expected_binned_absolute_gap": sum(
                r["count"] * abs(r["expected_frequency_minus_report"]) for r in rows if r["count"]
            )
            / len(cases),
            "realized_binned_absolute_gap": sum(
                r["count"] * abs(r["realized_frequency_minus_report"]) for r in rows if r["count"]
            )
            / len(cases),
            "scope": "Fixed ten-bin reliability in this simulator population; binning can hide error and empirical absolute gaps have sampling bias",
        }
    return result


def run(directory, *, progress=None):
    directory = Path(directory)
    raw_plan = (directory / "plan.json").read_bytes()
    plan = json.loads(raw_plan)
    if plan != make_plan(plan["batch_seeds"], plan["worlds_per_batch"]):
        raise ValueError("Frozen plan or implementation differs")
    cases, worlds = [], []
    for batch_seed in plan["batch_seeds"]:
        for index in range(plan["worlds_per_batch"]):
            new_cases, world = simulate_world(batch_seed, index)
            cases.extend(new_cases)
            worlds.append(world)
            if progress and len(worlds) % 64 == 0:
                progress(len(worlds))
    raw_cases, raw_worlds = encoded(cases), encoded(worlds)
    pooled = summarize_worlds(worlds)
    oracle = pooled["oracle"]["cost_aware"]["expected_gain_over_none"]
    public = pooled["public_rounded"]["cost_aware"]["expected_gain_over_none"]
    summary = {
        "schema_version": "epistemics.source-value-audit-summary.v1",
        "version": VERSION,
        "implementation_sha256": fingerprint(),
        "plan_sha256": digest(raw_plan),
        "cases_sha256": digest(raw_cases),
        "worlds_sha256": digest(raw_worlds),
        "world_count": len(worlds),
        "case_count": len(cases),
        "response_origin": "synthetic",
        "pooled": pooled,
        "by_batch": {
            str(seed): summarize_worlds([w for w in worlds if w["batch_seed"] == seed])
            for seed in plan["batch_seeds"]
        },
        "opportunities": summarize_cases(cases),
        "starting_calibration": calibration(cases),
        "design_diagnostic": {
            "effect_floor": plan["expected_effect_floor"],
            "oracle_mean_meets_floor": oracle["mean"] >= plan["expected_effect_floor"],
            "public_mean_meets_floor": public["mean"] >= plan["expected_effect_floor"],
            "public_expected_gain_positive_mc_lower_bound": public["monte_carlo_95_interval"][0]
            > 0,
            "licenses_agent_collection": False,
            "scope": "Design feasibility screen against the earlier .01 effect target, not a real-agent benefit gate",
        },
    }
    save(directory / "cases.json", raw_cases)
    save(directory / "worlds.json", raw_worlds)
    save(directory / "summary.json", encoded(summary))
    return summary
