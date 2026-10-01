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
                    "bare": d.get("bare"),
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
        "grain_anchor": dl.grain([v for r in anchors for v in r["probability"]]),
        "frame_shift": _frame_shift(pair_rows, ladder_rows),
    }
    out["sessions"] = sorted(out["sessions"])
    return out


def _frame_shift(pair_rows, ladder_rows):
    """Exploratory (found in the pilot): the anchor sessions' estimates against the agent's own
    ladder answers at the same thresholds, whatever the anchor: the mean change in |log-odds|
    (negative: less extreme in the comparison frame), and the mean estimates after low and high
    anchors."""
    own = {
        (r["series"], t): v
        for r in ladder_rows
        for t, v in zip(r["thresholds"], r["answers"], strict=True)
    }
    rows = [p for p in pair_rows if (p["series"], p["threshold"]) in own]
    if not rows:
        return None
    o = np.array([own[(p["series"], p["threshold"])] for p in rows])
    e = np.array([p["estimate"] for p in rows])
    side = np.array([p["side"] for p in rows])
    return {
        "extremity_change": float(np.mean(np.abs(screen.logit(e)) - np.abs(screen.logit(o)))),
        "ladder_mean": float(o.mean()),
        "estimate_low": float(e[side == "low"].mean()),
        "estimate_high": float(e[side == "high"].mean()),
    }


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


def followup(roots):
    """The follow-up: the anchored thresholds asked directly (no comparison, three per series,
    random order), against the same thresholds on the ladder and after a comparison. Per
    configuration: mean |log-odds| and the share of mid-range answers at multiples of 5 in each
    frame (original four series), and grain over the whole bare session."""
    rows = sessions(roots)
    out = {}
    for c in sorted({r["configuration"] for r in rows}):
        mine = [r for r in rows if r["configuration"] == c]
        ladder = {
            (x["series"], t): v
            for r in mine
            if r["module"] == "ladder"
            for x in r["ladders"]
            for t, v in zip(x["thresholds"], x["answers"], strict=True)
        }
        bare = {
            (b["series"], b["threshold"]): b["answer"]
            for r in mine
            if r["module"] == "bare"
            for b in r["bare"]
        }
        anchored = {}
        for r in mine:
            if r["module"] == "anchor":
                for p in r["pairs"]:
                    anchored.setdefault((p["series"], p["threshold"]), []).append(p["estimate"])
        keys = sorted(set(ladder) & set(bare) & set(anchored))
        if not keys:
            continue

        def frame(values):
            v = np.array(values)
            mid = v[(v >= dl.MID[0]) & (v <= dl.MID[1])]
            return {
                "mean": float(v.mean()),
                "extremity": float(np.mean(np.abs(screen.logit(v)))),
                "share_5": float(np.mean(np.round(mid * 100) % 5 == 0)) if len(mid) else None,
                "n": len(v),
            }

        out[c] = {
            "thresholds": len(keys),
            "ladder": frame([ladder[k] for k in keys]),
            "bare": frame([bare[k] for k in keys]),
            "after_comparison": frame([v for k in keys for v in anchored[k]]),
            "bare_session_grain": dl.grain(
                [v for r in mine if r["module"] == "bare" for v in r["probability"]]
            ),
        }
    return {
        "schema_version": "epistemics.deliberation-followup.v1",
        "configurations": out,
        "scope": "Exploratory follow-up to the pilot: which frame moves grain and extremity.",
    }


def frames(roots, baseline_roots=()):
    """The second follow-up: the share of mid-range estimates at multiples of 5, and their mean
    |log-odds|, after each kind of first question; per configuration and pooled over each GPT-6
    variant's three efforts. baseline_roots add the same thresholds asked directly (bare) and on
    the ladder, for reference."""
    rows = sessions(list(roots) + list(baseline_roots))
    families = {
        "astra": ("astra", "astra-low", "astra-high"),
        "sol": ("sol", "sol-low", "sol-high"),
    }
    anchored = {(s, dl.thresholds(s)[r]) for s in range(len(dl.SERIES)) for r in dl.ANCHORED}

    def summary(values):
        v = np.array(values, dtype=float)
        if not len(v):
            return None
        mid = v[(v >= dl.MID[0]) & (v <= dl.MID[1])]
        return {
            "share_5": float(np.mean(np.round(mid * 100) % 5 == 0)) if len(mid) else None,
            "extremity": float(np.mean(np.abs(screen.logit(v)))),
            "n": len(v),
            "n_mid": len(mid),
        }

    collected = {}
    for r in rows:
        bucket = collected.setdefault(r["configuration"], {})
        if r["module"] == "frames":
            for p in r["pairs"]:
                bucket.setdefault(p["frame"], []).append(p["estimate"])
        elif r["module"] == "bare":
            for b in r["bare"]:
                if (b["series"], b["threshold"]) in anchored:
                    bucket.setdefault("direct", []).append(b["answer"])
        elif r["module"] == "ladder":
            for x in r["ladders"]:
                for t, v in zip(x["thresholds"], x["answers"], strict=True):
                    if (x["series"], t) in anchored:
                        bucket.setdefault("ladder", []).append(v)
    names = ("ladder", "direct", *dl.FRAMES)
    per = {c: {f: summary(b.get(f, [])) for f in names} for c, b in sorted(collected.items())}
    pooled = {
        name: {
            f: summary([v for c in cs if c in collected for v in collected[c].get(f, [])])
            for f in names
        }
        for name, cs in families.items()
    }
    return {
        "schema_version": "epistemics.deliberation-frames.v1",
        "configurations": per,
        "families": pooled,
        "scope": "Exploratory second follow-up: which first question switches Astra's readout.",
    }


def quality(roots):
    """Exploratory: are follow-up answers (estimates after a first question: the pilot's anchor
    sessions and the frame sessions) worse than fresh ones (the ladder; the same thresholds asked
    directly), judged against the configuration's own answers? Per configuration, on the twelve
    anchored thresholds:
      distance     mean |log-odds - the own ladder answer|, for direct and for follow-up answers,
                   against the distance rounding the ladder answer to 5 points alone would give;
      discrimination  within a session, the fall in log-odds from a series' lowest to its highest
                   anchored threshold (ranks 1 and 5), by answer set;
      violations   within a session, a higher threshold answered with a higher probability (two
                   chances per series);
      retest       mean |log-odds difference| between two follow-up answers to one threshold."""
    rows = sessions(roots)
    anchored = {(s, dl.thresholds(s)[r]) for s in range(len(dl.SERIES)) for r in dl.ANCHORED}
    z = screen.logit
    out = {}
    for c in sorted({r["configuration"] for r in rows}):
        mine = [r for r in rows if r["configuration"] == c]
        ladder, sessions_ = {}, []
        for r in mine:
            if r["module"] == "ladder":
                for x in r["ladders"]:
                    for t, v in zip(x["thresholds"], x["answers"], strict=True):
                        if (x["series"], t) in anchored:
                            ladder[(x["series"], t)] = v
                sessions_.append(("ladder", {(x["series"], rk): v for x in r["ladders"]
                                             for rk, v in enumerate(x["answers"])}))  # fmt: skip
            elif r["module"] == "bare":
                sessions_.append(
                    ("direct", {(b["series"], b["rank"]): b["answer"] for b in r["bare"]})
                )
            elif r["module"] in ("anchor", "frames"):
                sessions_.append(
                    ("follow-up", {(p["series"], p["rank"]): p["estimate"] for p in r["pairs"]})
                )
        if not ladder:
            continue
        direct, follow = [], []
        by_threshold = {}
        for r in mine:
            if r["module"] == "bare":
                direct += [
                    (b["series"], b["threshold"], b["answer"])
                    for b in r["bare"]
                    if (b["series"], b["threshold"]) in anchored
                ]
            elif r["module"] in ("anchor", "frames"):
                for p in r["pairs"]:
                    follow.append((p["series"], p["threshold"], p["estimate"]))
                    by_threshold.setdefault((p["series"], p["threshold"]), []).append(p["estimate"])

        def distance(answers, ladder=ladder):
            d = [abs(float(z(v)) - float(z(ladder[(s, t)]))) for s, t, v in answers]
            return float(np.mean(d)) if d else None

        floor = [abs(float(z(round(v * 20) / 20)) - float(z(v))) for v in ladder.values()]
        discrimination, violations = {}, {}
        for kind, answers in sessions_:
            for s in range(len(dl.SERIES)):
                ranks = [answers.get((s, r)) for r in dl.ANCHORED]
                if any(v is None for v in ranks):
                    continue
                discrimination.setdefault(kind, []).append(float(z(ranks[0])) - float(z(ranks[-1])))
                violations.setdefault(kind, []).extend([ranks[1] > ranks[0], ranks[2] > ranks[1]])
        retest = [
            abs(float(z(a)) - float(z(b)))
            for vs in by_threshold.values()
            for i, a in enumerate(vs)
            for b in vs[i + 1 :]
        ]
        out[c] = {
            "distance_direct": distance(direct),
            "distance_follow_up": distance(follow),
            "distance_rounding_only": float(np.mean(floor)),
            "discrimination": {k: float(np.mean(v)) for k, v in discrimination.items()},
            "violations": {k: float(np.mean(v)) for k, v in violations.items()},
            "retest_follow_up": float(np.mean(retest)) if retest else None,
            "answers": {"direct": len(direct), "follow_up": len(follow)},
        }
    return {
        "schema_version": "epistemics.deliberation-quality.v1",
        "configurations": out,
        "scope": "Exploratory: follow-up against fresh answers, judged against each "
        "configuration's own ladder; no ground truth.",
    }


def followups(roots):
    """Follow-up rounding on the peer-advice cases: per configuration and variant, the share of
    mid-range answers at multiples of 5 for fresh and follow-up cases (pooled over both forms,
    mixed within sessions); for each case answered fresh in one form and as a follow-up in the
    other, the mean |log-odds| between the two answers; for the stated variant, the mean error
    against the exact answer, fresh against follow-up."""
    from epistemics.ledger import dispositions

    collected = {}
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "followup" not in record:
                continue
            f = record["followup"]
            entry = collected.setdefault((record["configuration"], f["variant"]), [])
            entry += f["answers"]
    out = {}
    for (c, variant), answers in sorted(collected.items()):

        def share(kind, answers=answers):
            v = [a["answer"] for a in answers if a["kind"] == kind]
            mid = [x for x in v if dl.MID[0] <= x <= dl.MID[1]]
            return {
                "share_5": sum(round(x * 100) % 5 == 0 for x in mid) / len(mid) if mid else None,
                "n": len(mid),
            }

        fresh = {a["base"]: a["answer"] for a in answers if a["kind"] == "fresh"}
        follow = {a["base"]: a["answer"] for a in answers if a["kind"] == "followup"}
        both = sorted(set(fresh) & set(follow))
        entry = {
            "fresh": share("fresh"),
            "followup": share("followup"),
            "matched_gap": float(
                np.mean(
                    [abs(float(screen.logit(fresh[b]) - screen.logit(follow[b]))) for b in both]
                )
            )
            if both
            else None,
            "matched": len(both),
        }
        if variant == "stated":
            for kind in ("fresh", "followup"):
                e = [a["error"] for a in answers if a["kind"] == kind and "error" in a]
                entry[f"error_{kind}"] = float(np.mean(e)) if e else None
        out.setdefault(c, {})[variant] = entry
    return {
        "schema_version": "epistemics.followups.v1",
        "configurations": out,
        "scope": "Exploratory: follow-up rounding on the peer-advice cases.",
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
