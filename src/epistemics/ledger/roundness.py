"""Exploratory: is a round answer a report of uncertainty (docs/exploration-log.md, idea 4)?

On the open-inference screen's sessions (F2, F4 and F5, forms a, b and c), three checks per
configuration, all post hoc:

  A  Openness. The share of round answers (whole multiples of 5 points) by how open the case is:
     anchors and fixed (fallback) cases, then open cases in thirds of the screen's openness audit
     (P90 - P10 of the observer's predicted log-odds over plausible parameters), within family and
     form. If roundness reports uncertainty, it rises with openness.
  B  Fallback-likeness. On open cases of forms a and b, with the revised observer fitted to the
     configuration's own answers (the fallback round's profiles): |z - z_observer| - |z -
     z_fallback|, positive when the answer is nearer the fitted fallback than the observer's
     answer. If round answers are where the agent stops computing, they are more fallback-like.
  C  Trust. Across configurations and families, the share of round answers on open cases against
     the fitted fallback weight (trust) m.

Near-certain answers (0.01-0.04, 0.96-0.99) are mostly not multiples of 5, so roundness is
confounded with extremity; A and B are also reported on mid-range answers (0.06-0.94) only.
Behaviour only; the designs collected are checked against the current ones before openness or the
observer is used.
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from epistemics.dispositions import screen

ROOTS = (
    "output/screen-stage-a-20261001",
    "output/screen-stage-b-20261001",
    "output/screen-fallback-20261001",
)
PROFILES = "output/screen-fallback-analysis-20261001.json"
FAMILIES = ("num", "lists", "trend")


MID = (0.06, 0.94)  # near-certain answers (0.01-0.04, 0.96-0.99) are mostly not multiples of 5


def _round(v):
    return bool(round(float(v) * 100) % 5 == 0)


def _keep(v, mid):
    return not mid or MID[0] <= float(v) <= MID[1]


def answers(roots=ROOTS):
    from epistemics.ledger import dispositions

    out = []
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "screen" not in record:
                continue
            family, form = record["screen"]["family"], record["screen"]["form"]
            if family not in FAMILIES:
                continue
            current = screen._design(family, form)
            same = all(
                np.array_equal(
                    np.asarray(record["items"][k]).astype(str), np.asarray(current[k]).astype(str)
                )
                for k in ("kind", "data")
            )
            out.append(
                {
                    "root": Path(root).name,
                    "configuration": record["configuration"],
                    "family": family,
                    "form": form,
                    "responses": np.asarray(record["responses"], dtype=float),
                    "current_design": same,
                }
            )
    return out


def _tertiles(family, form):
    items = screen._design(family, form)
    openness = screen.openness(family, form)
    open_ = np.asarray(items["kind"]) == "open"
    cuts = np.percentile(openness[open_], [100 / 3, 200 / 3]) if open_.any() else (0, 0)
    out = []
    for i, kind in enumerate(items["kind"]):
        if kind != "open":
            out.append(str(kind))
        else:
            out.append(("low", "middle", "high")[int(np.searchsorted(cuts, openness[i]))])
    return out


def check_openness(rows, mid=False):
    table = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if not r["current_design"]:
            continue
        for i, cls in enumerate(_tertiles(r["family"], r["form"])):
            if _keep(r["responses"][i], mid):
                table[r["configuration"]][cls].append(_round(r["responses"][i]))
    return {
        c: {cls: {"round": float(np.mean(v)), "n": len(v)} for cls, v in sorted(t.items())}
        for c, t in sorted(table.items())
    }


def check_fallback(rows, profiles, mid=False):
    out = defaultdict(lambda: {"round": [], "other": []})
    by_family = defaultdict(lambda: {"round": [], "other": []})
    for r in rows:
        if not r["current_design"] or r["form"] not in ("a", "b"):
            continue
        entry = profiles.get(r["family"], {}).get(r["configuration"])
        if not entry:
            continue
        params = entry["revised"]["parameters"]
        items = screen._design(r["family"], r["form"])
        from epistemics.ledger import screen_fit

        p = screen_fit.predict(r["family"], items, params)
        z_fallback = float(screen.logit(params["fallback"]))
        for i, kind in enumerate(items["kind"]):
            if kind != "open" or not _keep(r["responses"][i], mid):
                continue
            z = float(screen.logit(r["responses"][i]))
            f = abs(z - float(screen.logit(p[i]))) - abs(z - z_fallback)
            key = "round" if _round(r["responses"][i]) else "other"
            out[r["configuration"]][key].append(f)
            by_family[(r["configuration"], r["family"])][key].append(f)

    def summary(v):
        return {
            k: {"fallback_likeness": float(np.mean(x)) if x else None, "n": len(x)}
            for k, x in v.items()
        }

    return {
        "by_configuration": {c: summary(v) for c, v in sorted(out.items())},
        "by_family": {f"{c}|{f}": summary(v) for (c, f), v in sorted(by_family.items())},
    }


def check_trust(rows, profiles):
    points = []
    shares = defaultdict(list)
    for r in rows:
        if r["form"] not in ("a", "b") or not r["current_design"]:
            continue
        items = screen._design(r["family"], r["form"])
        for i, kind in enumerate(items["kind"]):
            if kind == "open":
                shares[(r["configuration"], r["family"])].append(_round(r["responses"][i]))
    for (c, family), v in sorted(shares.items()):
        entry = profiles.get(family, {}).get(c)
        if entry:
            points.append(
                {
                    "configuration": c,
                    "family": family,
                    "round_open": float(np.mean(v)),
                    "trust": entry["revised"]["parameters"]["trust"],
                    "fallback": entry["revised"]["parameters"]["fallback"],
                }
            )

    def corr(xs, ys):
        if len(xs) < 3 or np.std(xs) == 0 or np.std(ys) == 0:
            return None
        rx, ry = np.argsort(np.argsort(xs)), np.argsort(np.argsort(ys))
        return float(np.corrcoef(rx, ry)[0, 1])

    within = {
        f: corr(
            [p["round_open"] for p in points if p["family"] == f],
            [p["trust"] for p in points if p["family"] == f],
        )
        for f in FAMILIES
    }
    return {
        "points": points,
        "spearman_all": corr([p["round_open"] for p in points], [p["trust"] for p in points]),
        "spearman_within_family": within,
    }


def analyse(roots=ROOTS, profiles_path=PROFILES):
    rows = answers(roots)
    profiles = json.loads(Path(profiles_path).read_text())["profiles"]
    return {
        "schema_version": "epistemics.roundness.v1",
        "scope": "Exploratory, post hoc: screen F2, F4 and F5; profiles from the fallback round's "
        "revised-observer fits to forms a and b.",
        "sessions": len(rows),
        "sessions_with_current_design": sum(r["current_design"] for r in rows),
        "openness": check_openness(rows),
        "fallback": check_fallback(rows, profiles),
        # The same two checks on mid-range answers only: extremity confounds roundness.
        "openness_mid": check_openness(rows, mid=True),
        "fallback_mid": check_fallback(rows, profiles, mid=True),
        "trust": check_trust(rows, profiles),
    }
