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


def cases(roots):
    from epistemics.ledger import dispositions

    out = {}
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "wording" not in record:
                continue
            w = record["wording"]
            for r in w["cases"]:
                out.setdefault((record["configuration"], w["family"]), {}).setdefault(
                    r["wording"], []
                ).append(r["weight"])
    return {k: {w: np.array(v) for w, v in by.items()} for k, by in out.items()}


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
