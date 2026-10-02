"""Confident wording across families (exploration log idea 28; dispositions.wording).

Per configuration, family and wording: the mean weight a claim gets (log-odds toward it), with a
bootstrap interval over cases. Per family: each configuration's weight on the two confident
wordings against the median of the other configurations (face value at 1.5 times or more, as in
the reading guide), the increment "confirmed" adds to "definitely", and the spread from
"I think..." to "definitely... confirmed".
"""

import numpy as np

from epistemics.dispositions.wording import FAMILIES, WORDINGS

BOOTSTRAP = 4000
FACE_VALUE = 1.5
CEILING = 0.99
WORDING_EXPERIMENTS = ("wording-families",)


def records(roots):
    from epistemics.ledger import dispositions

    for root in roots:
        for record in dispositions.extract(root):
            if record.get("verified") and "wording" in record:
                yield record


def cases(roots):
    out = {}
    for record in records(roots):
        w = record["wording"]
        for r in w["cases"]:
            out.setdefault((record["configuration"], w["family"]), {}).setdefault(
                r["wording"], []
            ).append(r["weight"])
    return {k: {w: np.array(v) for w, v in by.items()} for k, by in out.items()}


def ceilings(roots):
    """Per configuration and family: the sessions, and whether each "definitely... confirmed"
    answer is at 99% or more toward the claim (where the weight understates the move)."""
    out = {}
    for record in records(roots):
        w = record["wording"]
        e = out.setdefault((record["configuration"], w["family"]), {"top": [], "sessions": 0})
        e["sessions"] += 1
        for c in w["cases"]:
            if c["wording"] == "confirmed":
                toward = c["answer"] if c["direction"] == 1 else 1 - c["answer"]
                e["top"].append(round(toward, 2) >= CEILING)
    return out


def _interval(x):
    return [float(np.percentile(x, 5)), float(np.percentile(x, 95))]


def summary(roots, seed=20261002):
    data = cases(roots)
    rng = np.random.default_rng(seed)
    configs = sorted({c for c, _ in data})
    families = [f for f in FAMILIES if any((c, f) in data for c in configs)]
    boots = {}
    for key, by in data.items():
        for w, x in by.items():
            idx = rng.integers(0, len(x), size=(BOOTSTRAP, len(x)))
            boots[(*key, w)] = x[idx].mean(axis=1)
    out = {}
    for family in families:
        present = [c for c in configs if (c, family) in data]
        table = {}
        for c in present:
            by = data[(c, family)]
            entry = {
                "weights": {
                    w: {
                        "mean": float(by[w].mean()),
                        "interval_90": _interval(boots[(c, family, w)]),
                        "cases": len(by[w]),
                    }  # fmt: skip
                    for w in WORDINGS
                    if w in by
                }
            }
            for w in ("definitely", "confirmed"):
                others = [o for o in present if o != c and w in data[(o, family)]]
                if w not in by or not others:
                    continue
                med = np.median([boots[(o, family, w)] for o in others], axis=0)
                ratio = boots[(c, family, w)] / med
                point = by[w].mean() / np.median([data[(o, family)][w].mean() for o in others])
                entry[f"{w}_to_others"] = {"ratio": float(point), "interval_90": _interval(ratio)}
            if "definitely" in by and "confirmed" in by:
                d = boots[(c, family, "confirmed")] - boots[(c, family, "definitely")]
                entry["confirmed_adds"] = {
                    "mean": float(by["confirmed"].mean() - by["definitely"].mean()),
                    "interval_90": _interval(d),
                }
            if "I think" in by and "confirmed" in by:
                d = boots[(c, family, "confirmed")] - boots[(c, family, "I think")]
                entry["spread"] = {
                    "mean": float(by["confirmed"].mean() - by["I think"].mean()),
                    "interval_90": _interval(d),
                }
            r = entry.get("confirmed_to_others")
            entry["face_value"] = bool(r and r["ratio"] >= FACE_VALUE and r["interval_90"][0] > 1)
            table[c] = entry
        out[family] = table
    return {
        "schema_version": "epistemics.wording.v1",
        "families": out,
        "scope": (
            "Exploratory: one claim without a record against a stated prior; weight in log-odds "
            "toward the claim. Face value: a 'definitely... confirmed' claim moves the answer at "
            "least 1.5 times as far as the other configurations' median, with the interval above 1."
        ),
    }


def passport_wording(roots, record_ratios=None):
    """The passport's reaction to confident wording, per configuration: in each family, the weight
    of a "definitely... confirmed" claim without a record against the median of the other
    configurations, the spread from "I think...", and the share of those answers at 99% or more;
    across families, the geometric mean of the ratios and whether its spread is the smallest in
    every family. record_ratios: the weight given to an analyst's call with its record stated,
    over the weight the record implies (call_reaction.record_ratios)."""
    table = summary(roots)["families"]
    ceiling = ceilings(roots)
    out = {}
    for c in sorted({c for t in table.values() for c in t}):
        families = {}
        for family, t in table.items():
            e = t.get(c)
            if not e or "confirmed_to_others" not in e or "spread" not in e:
                continue
            top = ceiling.get((c, family), {})
            families[family] = {
                "confident": e["weights"]["confirmed"]["mean"],
                "tentative": e["weights"]["I think"]["mean"],
                "ratio": e["confirmed_to_others"]["ratio"],
                "interval_90": e["confirmed_to_others"]["interval_90"],
                "spread": e["spread"]["mean"],
                "ceiling": float(np.mean(top["top"])) if top.get("top") else None,
                "sessions": top.get("sessions", 0),
            }
        if not families:
            continue
        least = all(
            v["spread"] <= min(o["spread"]["mean"] for o in table[f].values() if "spread" in o)
            for f, v in families.items()
        )
        out[c] = {
            "families": families,
            "pooled_ratio": float(np.exp(np.mean(np.log([v["ratio"] for v in families.values()])))),
            "least_spread": bool(least and len(table[next(iter(families))]) > 1),
            "sessions": sum(v["sessions"] for v in families.values()),
            "record_ratio": (record_ratios or {}).get(c),
        }
    return out


def phrase_sets(roots, three="urn3", four="urn", seed=20261003):
    """Phrase-set dependence (idea 30): per configuration, the "definitely... confirmed" weight with
    three wordings offered against four, and its ratio to the other configurations' median in each
    set; the shift is the three-wording ratio over the four-wording one (bootstrap over cases)."""
    data = cases(roots)
    configs = sorted({c for c, f in data if f == three} & {c for c, f in data if f == four})
    rng = np.random.default_rng(seed)

    def boot(x):
        return x[rng.integers(0, len(x), size=(BOOTSTRAP, len(x)))].mean(axis=1)

    top = {(c, f): boot(data[(c, f)]["confirmed"]) for c in configs for f in (three, four)}
    out = {}
    for c in configs:
        others = [o for o in configs if o != c]
        entry = {}
        for name, f in (("three", three), ("four", four)):
            x = data[(c, f)]
            point = x["confirmed"].mean() / np.median(
                [data[(o, f)]["confirmed"].mean() for o in others]
            )
            ratio = top[(c, f)] / np.median([top[(o, f)] for o in others], axis=0)
            entry[name] = {
                "weights": {w: float(v.mean()) for w, v in x.items()},
                "confirmed_to_others": {"ratio": float(point), "interval_90": _interval(ratio)},
            }
            entry[f"_{name}"] = ratio
        r3, r4 = entry.pop("_three"), entry.pop("_four")
        d = top[(c, three)] - top[(c, four)]
        entry["confirmed_shift"] = {
            "mean": float(
                data[(c, three)]["confirmed"].mean() - data[(c, four)]["confirmed"].mean()
            ),
            "interval_90": _interval(d),
        }
        entry["ratio_shift"] = {
            "ratio": entry["three"]["confirmed_to_others"]["ratio"]
            / entry["four"]["confirmed_to_others"]["ratio"],
            "interval_90": _interval(r3 / r4),
        }
        out[c] = entry
    return {
        "schema_version": "epistemics.wording-phrase-sets.v1",
        "configurations": out,
        "scope": (
            "Exploratory: the urn family's 'definitely... confirmed' call with three wordings "
            "offered against four; ratio_shift above 1 means the configuration stands further from "
            "the others when the top phrase is the top of three."
        ),
    }
