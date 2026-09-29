"""Capacity battery pilot: range-finding summaries (docs/capacity-battery-design.md).

Part A (load modules): per configuration, module and load level, the fitted report noise, the
weight on the structure-neglecting answer and the share of answers within 1.5 points of exact,
with the load slope and the model-free noise between repeated cases. Part B (matched-strength
audit records): the implied prior at each likelihood-ratio level (1, 2, 4, 8, 16).
"""

import json
from pathlib import Path

from epistemics.disposition_tasks.urn import VIG_SCALES
from epistemics.ledger import dispositions


def usage(root):
    """Input tokens per run from the collection log."""
    execution = json.loads((Path(root) / "execution.json").read_text())
    return {
        e["run_id"]: e["usage"]["input_tokens"]
        for e in execution.get("executions", [])
        if e.get("usage")
    }


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
                vig_rows.append({**base, "implied_by_lr": dict(zip(levels, implied, strict=True))})
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
        "| Configuration | Module | Variant | Implied prior by likelihood ratio | Tokens |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in result["vigilance"]:
        values = ", ".join(f"{k}: {v:.2f}" for k, v in r["implied_by_lr"].items())
        lines.append(
            f"| {r['configuration']} | {r['module']} | {r['variant']} | {values} | "
            f"{(r['input_tokens'] or 0) / 1e6:.2f}M |"
        )
    return "\n".join(lines)
