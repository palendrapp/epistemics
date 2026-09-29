"""Capacity battery pilot: range-finding summaries (docs/capacity-battery-design.md).

Part A (load modules): per configuration, module and load level, the fitted report noise, the
weight on the structure-neglecting answer and the share of answers within 1.5 points of exact,
with the load slope and the model-free noise between repeated cases. Part B (matched-strength
audit records): the implied rate of the never-named structure at each likelihood-ratio level, beside
the rate an ideal observer would infer from the same audit record.
"""

import json
from math import lgamma
from pathlib import Path

import numpy as np

from epistemics.disposition_tasks import render, urn
from epistemics.disposition_tasks.urn import VIG_SCALES
from epistemics.ledger import dispositions

RATES = np.linspace(0, 1, 1001)
FAMILIES = {"copying-urn": "copying", "selection-urn": "selection", "mismatch-urn": "mismatch"}


def _signature(family, items, i, r):
    """Signature frequency in the audit when the structure acts in a share r of rounds."""
    if family == "copying":
        a, b = float(items["accuracy_a"][i]), float(items["accuracy_b"][i])
        return (1 - r) * (a * b + (1 - a) * (1 - b)) + r
    if family == "selection":
        w = float(items["omission"][i])
        return (1 - r) * 0.5 * (1 - w) / ((1 - r) * (1 - w) + 0.5 * r)
    a = float(items["accuracy_a"][i])
    return (1 - r) * a + r / 2


def ideal(module, variant):
    """Per likelihood-ratio level, the mean over cases of the posterior mean rate given the audit
    record, under a prior with half its weight on no structure and half uniform over the rate.

    The records match the likelihood ratio for a reference rate of 0.2 against none, so stronger
    records also carry higher rate estimates (the maximum-likelihood rate rises with the count).
    """
    family = FAMILIES[module]
    items = render.items_for(module)
    levels, total = VIG_SCALES[variant]
    result = {}
    for slot, lr in enumerate(levels):
        means = []
        for i in np.flatnonzero((items["slot"] == slot) & (items["kind"] != "rate")):
            k = urn.vig_count(family, items, i, slot, variant)
            f = np.clip(_signature(family, items, i, RATES), 1e-12, 1 - 1e-12)
            like = np.exp(
                lgamma(total + 1)
                - lgamma(k + 1)
                - lgamma(total - k + 1)
                + k * np.log(f)
                + (total - k) * np.log(1 - f)
            )
            means.append((like * RATES).mean() / (like[0] + like.mean()))
        result[lr] = float(np.mean(means))
    return result


def usage(root):
    """Input tokens per run: from the collection log, or from each run's own execution record
    when the collection was interrupted before writing its log."""
    root = Path(root)
    if (root / "execution.json").exists():
        execution = json.loads((root / "execution.json").read_text())
        return {
            e["run_id"]: e["usage"]["input_tokens"]
            for e in execution.get("executions", [])
            if e.get("usage")
        }
    result = {}
    for path in (root / "collections").glob("*/execution.json"):
        run = json.loads(path.read_text())
        if run.get("usage"):
            result[path.parent.name] = run["usage"]["input_tokens"]
    return result


def pilot(roots):
    load_rows, vig_rows = [], []
    for root in roots:
        tokens = usage(root)
        for record in dispositions.extract(root):
            if not record.get("verified"):
                continue
            base = {
                "configuration": record["configuration"],
                "module": record["module"],
                "variant": record["variant"],
                "input_tokens": tokens.get(record["run_id"]),
            }
            if record["module"].endswith("-load"):
                load = record["load"]
                load_rows.append(
                    {
                        **base,
                        "levels": [
                            {
                                "load": lv["load"],
                                "readings": lv["readings"],
                                "report_sd": lv["report_sd"]["mean"],
                                "eta": lv["eta"]["mean"],
                                "exact_share": lv["exact_share"],
                            }
                            for lv in load["levels"]
                        ],
                        "load_slope": load["load_slope"],
                        "eta_slope": load["eta_slope"],
                        "repeat_noise": load["repeat_noise"],
                    }
                )
            elif record["variant"] in VIG_SCALES:
                implied = [s["implied"]["mean"] for s in record["slot_fits"]]
                levels = VIG_SCALES[record["variant"]][0]
                vig_rows.append(
                    {
                        **base,
                        "implied_by_lr": dict(zip(levels, implied, strict=True)),
                        "ideal_by_lr": ideal(record["module"], record["variant"]),
                    }
                )
    return {
        "schema_version": "epistemics.capacity-pilot.v1",
        "load": load_rows,
        "vigilance": vig_rows,
    }


def tables(result):
    lines = [
        "| Configuration | Module | Readings | Noise τ | Neglect weight η | Exact within 1.5 points | Tokens |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in result["load"]:
        for lv in r["levels"]:
            lines.append(
                f"| {r['configuration']} | {r['module']} | {lv['readings']} | {lv['report_sd']:.3f} | "
                f"{lv['eta']:.2f} | {lv['exact_share']:.0%} | "
                f"{(r['input_tokens'] or 0) / 1e6:.2f}M |"
            )
        lines.append(
            f"| {r['configuration']} | {r['module']} | slope | {r['load_slope']:.2f} | "
            f"{r['eta_slope']:.2f} | repeat noise {r['repeat_noise']:.3f} | |"
        )
    lines += [
        "",
        "| Configuration | Module | Variant | Implied rate (ideal) by likelihood ratio | Tokens |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in result["vigilance"]:
        values = ", ".join(
            f"{k}: {v:.2f} ({r['ideal_by_lr'][k]:.2f})" for k, v in r["implied_by_lr"].items()
        )
        lines.append(
            f"| {r['configuration']} | {r['module']} | {r['variant']} | {values} | "
            f"{(r['input_tokens'] or 0) / 1e6:.2f}M |"
        )
    return "\n".join(lines)
