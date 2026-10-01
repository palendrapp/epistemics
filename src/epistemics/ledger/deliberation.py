"""Deliberation style pilot: readout grain and adjustment from anchors, per configuration
(docs/deliberation-style-design.md). Exploratory, with the design note's predictions written down
before collection:

  P1  grain: Astra's rho above Sol's at each effort.
  P2  plateaus: Astra's share of identical adjacent ladder answers above Sol's.
  P3  anchoring: a differs between Astra and Sol at matched effort (the reading: Astra higher).
  P4  effort: within each variant, a falls from low to high effort.
  P5  seconds per case: Sol's above Astra's on ladder cases.

Each prediction is summarised descriptively (how many of the three effort-matched comparisons go
the predicted way, and whether the 90% intervals separate); there is no formal test.
"""

from pathlib import Path

import numpy as np

from epistemics.dispositions import deliberation as dl
from epistemics.dispositions import screen

PAIRS = (("astra", "sol"), ("astra-low", "sol-low"), ("astra-high", "sol-high"))
EFFORT = {"astra": ("astra-low", "astra", "astra-high"), "sol": ("sol-low", "sol", "sol-high")}


def sessions(roots):
    from epistemics.ledger import dispositions, sweep

    out = []
    for root in roots:
        root = Path(root)
        executions = sweep._executions(root)
        for record in dispositions.extract(root):
            if not record.get("verified") or "deliberation" not in record:
                continue
            d = record["deliberation"]
            timings = sweep._timings(root / "collections" / record["run_id"])
            usage = (executions.get(record["run_id"]) or {}).get("usage") or {}
            out.append(
                {
                    "configuration": record["configuration"],
                    "module": d["module"],
                    "form": d["form"],
                    "ladders": d.get("ladders"),
                    "pairs": d.get("pairs"),
                    "probability": [
                        v
                        for v, r in zip(d["responses"], record["items"]["response"], strict=True)
                        if r == "probability"
                    ],
                    "seconds": float(np.median(timings)) if timings else None,
                    "output_per_case": (
                        usage["output_tokens"] / 24 if usage.get("output_tokens") else None
                    ),
                }
            )
    return out


def configuration(rows):
    ladders = [r for r in rows if r["module"] == "ladder"]
    anchors = [r for r in rows if r["module"] == "anchor"]
    ladder_rows = [x for r in ladders for x in r["ladders"]]
    pair_rows = [x for r in anchors for x in r["pairs"]]
    steps = sum(len(x["answers"]) - 1 for x in ladder_rows)
    out = {
        "sessions": {
            r["module"] + ("" if r["module"] == "ladder" else f"-{r['form']}") for r in rows
        },
        "grain": dl.grain([v for r in rows for v in r["probability"]]),
        "grain_ladder": dl.grain([v for r in ladders for v in r["probability"]]),
        "plateau_share": (sum(x["plateaus"] for x in ladder_rows) / steps if steps else None),
        "violations": sum(x["violations"] for x in ladder_rows),
        "anchoring": dl.anchoring(pair_rows),
        "anchoring_on_own": dl.anchoring_on_own(pair_rows, ladder_rows) if ladder_rows else None,
        "consistency": float(np.mean([p["consistent"] for p in pair_rows])) if pair_rows else None,
        "seconds_ladder": ladders[0]["seconds"] if ladders else None,
        "seconds_anchor": float(np.mean([r["seconds"] for r in anchors if r["seconds"]]))
        if any(r["seconds"] for r in anchors)
        else None,
        "output_ladder": ladders[0]["output_per_case"] if ladders else None,
    }
    out["sessions"] = sorted(out["sessions"])
    return out


def _compare(results, getter, interval_getter=None):
    rows = []
    for a, s in PAIRS:
        if a in results and s in results:
            va, vs = getter(results[a]), getter(results[s])
            if va is None or vs is None:
                continue
            row = {
                "astra": a,
                "sol": s,
                "astra_value": va,
                "sol_value": vs,
                "astra_higher": va > vs,
            }
            if interval_getter:
                ia, is_ = interval_getter(results[a]), interval_getter(results[s])
                row["separate"] = bool(ia[0] > is_[1] or is_[0] > ia[1])
            rows.append(row)
    return {
        "comparisons": rows,
        "astra_higher": sum(r["astra_higher"] for r in rows),
        "of": len(rows),
    }


def pilot(roots):
    rows = sessions(roots)
    results = {}
    for c in sorted({r["configuration"] for r in rows}):
        results[c] = configuration([r for r in rows if r["configuration"] == c])

    def a_mean(r):
        return r["anchoring"]["a"]["mean"] if r["anchoring"] else None

    def a_interval(r):
        return r["anchoring"]["a"]["interval_90"]

    effort = {v: {c: a_mean(results[c]) for c in cs if c in results} for v, cs in EFFORT.items()}
    return {
        "schema_version": "epistemics.deliberation-pilot.v1",
        "configurations": results,
        "P1_grain": _compare(
            results, lambda r: r["grain"]["rho"]["mean"], lambda r: r["grain"]["rho"]["interval_90"]
        ),
        "P2_plateaus": _compare(results, lambda r: r["plateau_share"]),
        "P3_anchoring": _compare(results, a_mean, a_interval),
        "P4_effort": effort,
        "P5_seconds": _compare(results, lambda r: r["seconds_ladder"]),
        "scope": "Exploratory pilot; predictions written down before collection, summarised "
        "descriptively.",
    }


# Validation before collection.
def _draw(rng):
    return {
        "params": screen.observer_draw("trend", rng, 1)[0],
        "rho": float(rng.uniform(0, 1)),
        "a": float(rng.uniform(0, 0.6)),
        "tau": float(rng.uniform(0.1, 0.5)),
    }


def _simulate(truth, rng):
    rows = []
    for module in dl.MODULES:
        items = dl.design(module)
        answers = dl.respond(items, truth, rng)
        s = dl.session(items, answers)
        rows.append(
            {
                "module": s["module"],
                "form": s["form"],
                "ladders": s.get("ladders"),
                "pairs": s.get("pairs"),
                "probability": [
                    float(v)
                    for v, r in zip(answers, items["response"], strict=True)
                    if r == "probability"
                ],
                "seconds": None,
                "output_per_case": None,
            }
        )
    return configuration(rows)


def _chunk(args):
    n, seed = args
    rng = np.random.default_rng(seed)
    return [(t, _simulate(t, rng)) for t in (_draw(rng) for _ in range(n))]


def validation(agents=300, seed=20261120, workers=4):
    """Recovery of the readout grain rho and the anchoring weight a from one configuration's
    three sessions: r >= 0.8, 90% coverage >= 0.8, confusion with report noise and with each
    other <= 0.3. The secondary estimate of a against the agent's own ladder answers is reported
    with its bias."""
    from concurrent.futures import ProcessPoolExecutor

    seeds = np.random.SeedSequence(seed).spawn(workers)
    with ProcessPoolExecutor(workers) as pool:
        rows = [
            r for part in pool.map(_chunk, [(agents // workers, s) for s in seeds]) for r in part
        ]

    def metric(true, est, intervals):
        true, est = np.array(true), np.array(est)
        inside = np.mean(
            [lo - 1e-9 <= t <= hi + 1e-9 for t, (lo, hi) in zip(true, intervals, strict=True)]
        )
        return {"r": float(np.corrcoef(true, est)[0, 1]), "coverage_90": float(inside)}

    rho = metric(
        [t["rho"] for t, _ in rows],
        [f["grain"]["rho"]["mean"] for _, f in rows],
        [f["grain"]["rho"]["interval_90"] for _, f in rows],
    )
    a = metric(
        [t["a"] for t, _ in rows],
        [f["anchoring"]["a"]["mean"] for _, f in rows],
        [f["anchoring"]["a"]["interval_90"] for _, f in rows],
    )
    tau = np.array([t["tau"] for t, _ in rows])
    rho_est = np.array([f["grain"]["rho"]["mean"] for _, f in rows])
    a_est = np.array([f["anchoring"]["a"]["mean"] for _, f in rows])
    confusion = {
        "rho_with_tau": float(np.corrcoef(rho_est, tau)[0, 1]),
        "a_with_tau": float(np.corrcoef(a_est, tau)[0, 1]),
        "a_with_rho": float(np.corrcoef(a_est, [t["rho"] for t, _ in rows])[0, 1]),
        "rho_with_a": float(np.corrcoef(rho_est, [t["a"] for t, _ in rows])[0, 1]),
    }
    own = np.array([f["anchoring_on_own"] for _, f in rows], dtype=float)
    true_a = np.array([t["a"] for t, _ in rows])
    passed = all(m["r"] >= 0.8 and m["coverage_90"] >= 0.8 for m in (rho, a)) and all(
        abs(v) <= 0.3 for v in confusion.values()
    )
    return {
        "schema_version": "epistemics.deliberation-validation.v1",
        "agents": len(rows),
        "rho": rho,
        "a": a,
        "confusion": confusion,
        "a_on_own": {
            "r": float(np.corrcoef(true_a, own)[0, 1]),
            "mean_bias": float(np.mean(own - true_a)),
        },
        "passed": passed,
    }
