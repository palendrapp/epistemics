"""Exploratory sweep across every disposition collection (docs/exploration-log.md).

Not a test: configuration signatures computed from behaviour already collected, to find regularities
worth an experiment. Answers come from the verified extraction (each root read with its own frozen
implementation and designs); case timing from reports whose bytes match their recorded sha256;
usage and tool calls from each root's execution log. No agent text is read.

Signatures per configuration and collection (probability answers only):
  grain       share of answers that are whole multiples of 5 percentage points
  extremity   mean |log-odds| of the answers (clipped at 1% and 99%)
  boldness    mean of |log-odds| minus the other configurations' median |log-odds| on the same case
  departure   mean |log-odds - the other configurations' median log-odds| on the same case
  modal       share of answers equal to the other configurations' most common answer
  latency     median seconds from a case's checkpoint to its answer
  output      output tokens per case
  retest      mean |log-odds difference| between repeated runs of the same cases
Case classes, for the within-session comparison of grain:
  open        screen, coherence-set and statement cases whose answer depends on an unstated model
  determinate their anchors, fixed (fallback) and computable cases, and statements' prior cases
  stated      cases of the batteries that state the probabilities
"""

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path

import numpy as np

SIGNATURES = (
    "grain",
    "extremity",
    "boldness",
    "departure",
    "modal",
    "latency",
    "output",
    "retest",
)
CLIP = 0.01
MIN_CONFIGURATIONS = 4  # a collection enters the stability table when this many share it


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), CLIP, 1 - CLIP)
    return np.log(p / (1 - p))


def roots(base="output"):
    out = []
    for plan in sorted(Path(base).glob("*/plan.json")):
        try:
            schema = json.loads(plan.read_text()).get("schema_version")
        except (OSError, ValueError):
            continue
        if schema == "epistemics.disposition-plan.v1":
            out.append(plan.parent)
    return out


def case_class(module, items, i):
    kind = str(items["kind"][i]) if "kind" in items else ""
    if module.startswith(("screen-", "cohere-", "statement-")):
        if kind in ("anchor", "fixed", "prior"):
            return "determinate"
        if "computable" in items and int(items["computable"][i]) == 1:
            return "determinate"
        return "open"
    return "stated"


def _timings(directory):
    """Seconds per case position, if the report's bytes match its recorded hash."""
    report, recorded = directory / "report.json", directory / "report.sha256"
    if not report.exists() or not recorded.exists():
        return None
    raw = report.read_bytes()
    if hashlib.sha256(raw).hexdigest() != recorded.read_text().split()[0]:
        return None
    out = []
    for o in json.loads(raw)["observations"]:
        start = datetime.fromisoformat(o["locked_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(o["answered_at"].replace("Z", "+00:00"))
        out.append((end - start).total_seconds())
    return out


def _executions(root):
    path = root / "execution.json"
    if not path.exists():
        return {}
    return {e["run_id"]: e for e in json.loads(path.read_text()).get("executions", [])}


def rows_for(root):
    """One row per probability answer of every verified run in a root."""
    from epistemics.ledger import dispositions

    executions = _executions(root)
    rows, runs = [], []
    for record in dispositions.extract(root):
        if not record.get("verified") or record.get("responses") is None:
            continue
        items = {k: np.asarray(v) for k, v in record["items"].items()}
        module = record["module"]
        if module == "checks":
            continue
        timings = _timings(root / "collections" / record["run_id"])
        position = {int(i): k for k, i in enumerate(record["order"])}
        e = executions.get(record["run_id"], {})
        usage = e.get("usage") or {}
        tools = [t.get("tool") for t in (e.get("tools") or [])]
        runs.append(
            {
                "root": root.name,
                "run_id": record["run_id"],
                "configuration": record["configuration"],
                "module": module,
                "cases": len(record["order"]),
                "output_tokens": usage.get("output_tokens"),
                "history_calls": tools.count("get_history"),
            }
        )
        for i, value in enumerate(record["responses"]):
            if value is None:
                continue
            if "response" in items and str(items["response"][i]) != "probability":
                continue
            rows.append(
                {
                    "root": root.name,
                    "configuration": record["configuration"],
                    "case": (module, record["cover"], record["variant"], i),
                    "repeat": record.get("repeat"),
                    "value": float(value),
                    "class": case_class(module, items, i),
                    "latency": timings[position[i]] if timings else None,
                }
            )
    return rows, runs


def _collection(name):
    """A root's collection name: its date and any suffix removed."""
    parts = name.split("-")
    for k, part in enumerate(parts):
        if len(part) == 8 and part.isdigit():
            return "-".join(parts[:k])
    return name


def signatures(rows, runs):
    """Per collection and configuration: every signature, and grain by case class."""
    by = defaultdict(list)
    for r in rows:
        by[(_collection(r["root"]), r["configuration"])].append(r)
    # Consensus: per case (within a root), the other configurations' answers.
    cases = defaultdict(lambda: defaultdict(list))
    for r in rows:
        cases[(r["root"], r["case"])][r["configuration"]].append(r["value"])
    out = defaultdict(dict)
    for (collection, config), mine in by.items():
        values = np.array([r["value"] for r in mine])
        z = _logit(values)
        bold, depart, modal = [], [], []
        for r in mine:
            others = [
                v for c, vs in cases[(r["root"], r["case"])].items() if c != config for v in vs
            ]
            if len(others) < 2:
                continue
            own = float(_logit(r["value"]))
            zo = _logit(others)
            bold.append(abs(own) - float(np.median(np.abs(zo))))
            depart.append(abs(own - float(np.median(zo))))
            counts = defaultdict(int)
            for v in others:
                counts[round(v, 2)] += 1
            modal.append(round(r["value"], 2) == max(counts, key=counts.get))
        latencies = [r["latency"] for r in mine if r["latency"] is not None]
        mine_runs = [
            u for u in runs if _collection(u["root"]) == collection and u["configuration"] == config
        ]
        tokens = [u["output_tokens"] / u["cases"] for u in mine_runs if u["output_tokens"]]
        # Retest: the same configuration's repeated answers to the same case.
        repeated = defaultdict(list)
        for r in mine:
            repeated[(r["root"], r["case"])].append(r["value"])
        retest = [
            abs(float(_logit(a)) - float(_logit(b)))
            for vs in repeated.values()
            if len(vs) > 1
            for a, b in combinations(vs, 2)
        ]
        grain_by = {}
        for cls in ("open", "determinate", "stated"):
            v = np.array([r["value"] for r in mine if r["class"] == cls])
            if len(v):
                grain_by[cls] = {
                    "grain": float(np.mean(np.round(v * 100) % 5 == 0)),
                    "n": int(len(v)),
                }
        out[collection][config] = {
            "answers": int(len(values)),
            "grain": float(np.mean(np.round(values * 100) % 5 == 0)),
            "extremity": float(np.mean(np.abs(z))),
            "boldness": float(np.mean(bold)) if bold else None,
            "departure": float(np.mean(depart)) if depart else None,
            "modal": float(np.mean(modal)) if modal else None,
            "latency": float(np.median(latencies)) if latencies else None,
            "output": float(np.mean(tokens)) if tokens else None,
            "retest": float(np.mean(retest)) if retest else None,
            "retest_pairs": len(retest),
            "history_calls": int(sum(u["history_calls"] for u in mine_runs)),
            "grain_by_class": grain_by,
        }
    return {k: dict(v) for k, v in out.items()}


def _ranks(values):
    order = np.argsort(np.argsort(values))
    return order.astype(float)


def stability(table):
    """For each signature: Spearman correlations of configurations' values between every pair of
    collections that share at least MIN_CONFIGURATIONS configurations, and each configuration's
    mean rank (0 lowest) across collections."""
    out = {}
    for sig in SIGNATURES:
        per = {
            c: {k: v[sig] for k, v in configs.items() if v.get(sig) is not None}
            for c, configs in table.items()
        }
        per = {c: v for c, v in per.items() if len(v) >= MIN_CONFIGURATIONS}
        rhos = []
        for a, b in combinations(sorted(per), 2):
            shared = sorted(set(per[a]) & set(per[b]))
            if len(shared) < MIN_CONFIGURATIONS:
                continue
            x = _ranks([per[a][s] for s in shared])
            y = _ranks([per[b][s] for s in shared])
            if np.std(x) > 0 and np.std(y) > 0:
                rhos.append(float(np.corrcoef(x, y)[0, 1]))
        mean_rank = defaultdict(list)
        for v in per.values():
            names = sorted(v)
            ranks = _ranks([v[n] for n in names]) / max(len(names) - 1, 1)
            for n, r in zip(names, ranks, strict=True):
                mean_rank[n].append(float(r))
        out[sig] = {
            "collections": len(per),
            "pairs": len(rhos),
            "mean_rho": float(np.mean(rhos)) if rhos else None,
            "share_positive": float(np.mean(np.array(rhos) > 0)) if rhos else None,
            "mean_rank": {
                n: {"rank": float(np.mean(r)), "collections": len(r)}
                for n, r in sorted(mean_rank.items())
            },
        }
    return out


def grain_by_class(table):
    """Within a configuration and collection, grain on open against determinate cases."""
    out = []
    for collection, configs in sorted(table.items()):
        for config, v in sorted(configs.items()):
            g = v["grain_by_class"]
            if "open" in g and "determinate" in g:
                out.append(
                    {
                        "collection": collection,
                        "configuration": config,
                        "open": g["open"]["grain"],
                        "determinate": g["determinate"]["grain"],
                        "n_open": g["open"]["n"],
                        "n_determinate": g["determinate"]["n"],
                    }
                )
    return out


PAIRS = (("astra", "sol"), ("astra-low", "sol-low"), ("astra-high", "sol-high"))


def open_grain(table):
    """Grain on open cases per collection, and the effort-matched GPT-6 comparisons (Astra
    against Sol at the same effort). Statements are kept but flagged: their determinate cases
    repeat the stated prior, so only their open cases are comparable."""
    per, pairs = {}, []
    for collection, configs in sorted(table.items()):
        row = {
            c: v["grain_by_class"]["open"]["grain"]
            for c, v in configs.items()
            if "open" in v["grain_by_class"]
        }
        if not row:
            continue
        per[collection] = row
        for a, b in PAIRS:
            if a in row and b in row:
                pairs.append(
                    {"collection": collection, "astra": a, "sol": b, "difference": row[a] - row[b]}
                )
    return {
        "per_collection": per,
        "pairs": pairs,
        "astra_rounder": sum(p["difference"] > 0 for p in pairs),
        "of": len(pairs),
    }


def sweep(base="output", workers=6):
    from concurrent.futures import ProcessPoolExecutor

    found = roots(base)
    rows, runs = [], []
    with ProcessPoolExecutor(workers) as pool:
        for r, u in pool.map(rows_for, found):
            rows += r
            runs += u
    table = signatures(rows, runs)
    return {
        "schema_version": "epistemics.sweep.v1",
        "roots": [r.name for r in found],
        "answers": len(rows),
        "runs": len(runs),
        "signatures": table,
        "stability": stability(table),
        "grain_by_class": grain_by_class(table),
        "open_grain": open_grain(table),
        "scope": "Exploratory: behaviour already collected, summarised to suggest experiments; "
        "no test, no claim.",
    }
