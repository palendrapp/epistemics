"""Disposition collections: verified extraction and the tables reported in the docs.

Extraction runs in a subprocess on the root's own implementation snapshot, which re-verifies
each report (exact bytes, reconstruction, recomputed analysis) and reads it with the item
designs and observers of that version. Tables are then computed here.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from epistemics.dispositions import fit

# Runs under the snapshot's code; kept to APIs present in every disposition-tasks version.
EXTRACT = r"""
import json, sys
from pathlib import Path
import numpy as np
from epistemics.disposition_tasks.collection import load_report
from epistemics.disposition_tasks.render import items_for
from epistemics.dispositions import observers
from epistemics.dispositions.response import sigmoid

root = Path(sys.argv[1])
plan = json.loads((root / "plan.json").read_text())
out = []
for entry in plan["runs"]:
    directory = root / "collections" / entry["run_id"]
    record = {"run_id": entry["run_id"], "configuration": entry["configuration"],
              "repeat": entry.get("repeat"), "order_policy": entry.get("order_policy", "random")}
    if not (directory / "report.json").exists():
        record.update(verified=False, error="no report")
        out.append(record)
        continue
    try:
        report = load_report(directory)
    except Exception as error:
        record.update(verified=False, error=f"{type(error).__name__}: {error}")
        out.append(record)
        continue
    m, a = report.manifest, report.analysis
    items = items_for(m.module)
    responses = [None] * len(m.order)
    for row in a["rows"]:
        responses[row["item"]] = row["response"]
    record.update(verified=True, module=m.module, cover=m.cover,
                  variant=getattr(m, "variant", "paired"), order=list(m.order),
                  responses=responses,
                  kinds=[str(k) for k in items["kind"]] if "kind" in items else None,
                  slots=[int(s) for s in items["slot"]] if "slot" in items else None,
                  items={k: np.asarray(v).tolist() for k, v in items.items()})
    if m.module == "checks":
        decision, _ = observers.check_values(items, "linear")
        record["decision_values"] = [float(v) for v in decision]
        record["fits"] = {f: a["fits"][f]["parameters"] for f in a["fits"]}
    elif m.module in ("corroboration", "disclosure"):
        observer = {"corroboration": observers.corroboration, "disclosure": observers.disclosure}[m.module]
        record["indifference"] = [float(v) for v in np.round(sigmoid(observer(items, 0.5, 1.0)) * 100) / 100]
        record["fit"] = a["fit"]["parameters"]
        record["model_comparison"] = a["model_comparison"]["preferred"]
        if "learning" in a:
            record["learning"] = {"parameters": a["learning"]["parameters"],
                                  "learning_probability": a["learning"]["learning_probability"],
                                  "revealed_rate": a.get("revealed_rate")}
    else:
        record["slot_fits"] = [{"slot": s["slot"], "implied": s["implied"], "stated": s["stated"]}
                               for s in a["fit"]["slots"]]
        record["shared"] = a["fit"]["parameters"]
    out.append(record)
print(json.dumps(out))
"""


def extract(root, source=None):
    """Verified, normalised run records for a disposition collection root."""
    root = Path(root).resolve()
    source = Path(source) if source else root / "implementation" / "src"
    output = subprocess.run(
        [sys.executable, "-c", EXTRACT, str(root)],
        env={**os.environ, "PYTHONPATH": str(source)},
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(output.stdout)


def ranks(values):
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
    a, b = ranks(a), ranks(b)
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def summary(record):
    """The headline estimates of one verified run."""
    if not record.get("verified"):
        return {"verified": False, "error": record.get("error")}
    module = record["module"]
    base = {k: record[k] for k in ("module", "variant", "cover", "repeat", "order_policy")}
    if module == "checks":
        responses = np.array(record["responses"], dtype=float)
        decision = np.array(record["decision_values"])
        zero = np.abs(decision) < 1e-9
        linear = record["fits"]["linear"]["certainty_value"]
        entropy = record["fits"]["entropy"]["certainty_value"]
        return {
            **base,
            "certainty_value_linear": linear,
            "certainty_value_entropy": entropy,
            "decision_weight": record["fits"]["linear"]["decision_weight"]["mean"],
            "mean_points_zero_value": float(responses[zero].mean()),
            "mean_points_decision_value": float(responses[~zero].mean()),
            "exact_decision_value": int(np.sum(responses == np.floor(decision + 1e-9))),
        }
    if module in ("corroboration", "disclosure"):
        responses = np.array(record["responses"], dtype=float)
        result = {
            **base,
            "disposition": record["fit"]["disposition"],
            "gamma": record["fit"]["gamma"]["mean"],
            "bias": record["fit"]["bias"]["mean"],
            "report_sd": record["fit"]["report_sd"]["mean"],
            "preferred_model": record["model_comparison"],
            "exact_indifference": int(
                np.sum(np.abs(responses - np.array(record["indifference"])) < 1e-9)
            ),
        }
        if "learning" in record:
            learning = record["learning"]
            result["learning"] = {
                "start": learning["parameters"]["start"],
                "strength": float(2 ** learning["parameters"]["log2_strength"]["mean"]),
                "learning_probability": learning["learning_probability"],
                "revealed_rate": learning["revealed_rate"],
            }
        return result
    implied = [s["implied"]["mean"] for s in record["slot_fits"]]
    # Unprompted modules ask for no stated base rates.
    fits = record["slot_fits"]
    stated = [s["stated"][0] for s in fits] if all(s["stated"] for s in fits) else None
    result = {
        **base,
        "implied": implied,
        "implied_lower_90": [s["implied"]["interval_90"][0] for s in fits],
        "stated": stated,
        "stated_minus_implied_max": float(np.max(np.abs(np.subtract(stated, implied))))
        if stated
        else None,
        "report_sd": record["shared"]["report_sd"]["mean"],
    }
    if module.endswith(("-cues", "-dossier", "-unprompted", "-asked")):
        result["designed_order_spearman"] = spearman(range(len(implied)), implied)
        result["range"] = float(max(implied) - min(implied))
    return result


def descriptor_fits(record):
    """For suggestive and reassuring variants: the disposition fitted per descriptor sentence."""
    from epistemics.disposition_tasks.render import items_for

    items = items_for(record["module"])
    responses = np.array(record["responses"], dtype=float)
    model = {"corroboration": "dependence", "disclosure": "disclosure"}[record["module"]]
    fits = []
    for k in range(3):
        mask = np.arange(len(responses)) % 3 == k
        part = {name: values[mask] for name, values in items.items()}
        fits.append(fit.fit_reports(model, part, responses[mask])["parameters"]["disposition"])
    return fits


def retest(first, second):
    """Mean absolute difference between matching cue or range runs (repeat 1 against repeat 2)."""
    rows = []
    keyed = {(s["module"], s["variant"], r["configuration"]): s for r, s in first}
    for record, s in second:
        key = (s["module"], s["variant"], record["configuration"])
        if key in keyed:
            a, b = np.array(keyed[key]["implied"]), np.array(s["implied"])
            rows.append(
                {
                    "configuration": record["configuration"],
                    "module": s["module"],
                    "variant": s["variant"],
                    "first": keyed[key]["implied"],
                    "second": s["implied"],
                    "mean_absolute_difference": float(np.mean(np.abs(a - b))),
                    "rank_agreement": spearman(a, b),
                }
            )
    return rows


def range_contrast(pairs):
    """Per configuration: mean target prior among reassuring minus among suggestive outlets."""
    by = {}
    for record, s in pairs:
        if s.get("module") != "corroboration-range":
            continue
        by.setdefault(record["configuration"], {}).setdefault(s["variant"], []).append(
            s["implied"][:5]
        )
    result = {}
    for config, variants in by.items():
        if len(variants) == 2:
            reassuring = np.mean(variants["range-reassuring"], axis=0)
            suggestive = np.mean(variants["range-suggestive"], axis=0)
            contrast = reassuring - suggestive
            result[config] = {
                "reassuring": reassuring.tolist(),
                "suggestive": suggestive.tolist(),
                "per_target": contrast.tolist(),
                "mean": float(contrast.mean()),
                "contexts": {v: len(x) for v, x in variants.items()},
            }
    return result
