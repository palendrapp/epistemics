"""Far transfer for the Clef battery (docs/clef-battery-design.md, "Far transfer").

Natural-language central-bank remarks with the market price stated but no hit rates, so there is
no exact Bayesian answer; each test uses a property a Bayesian answer must have instead.

  price weight   z = alpha * price log-odds + a fixed effect per set of remarks. A Bayesian moves
                 one for one with the price (alpha = 1). Primary on the sets with a net of at most
                 one remark (answers well away from saturation); also without the no-remarks set,
                 the no-remarks set alone, and all sets.
  inversion      the answers inverted through the model's urn-fitted map (and the other model's);
                 the price weight after inversion should be 1
  sample size    the evidence of 3 and 5 agreeing remarks against 1 (price removed with alpha):
                 Bayes 3 and 5 for independent speakers; the urn regression predicts
                 3*beta_3/beta_1 and 5*beta_5/beta_1, and the urn's unanimous samples their own
                 ratios (the two urn estimators differ; neither is privileged)
  waiting        P(take a position now) with no remarks heard, and by net count, against the near
                 desk of the battery

Elicited outputs of a trained head, not direct access to beliefs.
"""

import numpy as np

from epistemics.clef import far, pilot
from epistemics.clef.answers import parse
from epistemics.clef.client import ClefError

CLIP = 0.0005
BOOT = 1000
SEED = 20261006
MODERATE = 1  # largest |net| of the primary sets


def _z(p):
    p = np.clip(np.asarray(p, dtype=float), CLIP, 1 - CLIP)
    return np.log(p / (1 - p))


def load(root):
    document, _ = pilot.load(root)
    if document.get("design") != "far":
        raise ClefError(f"{root} is not a far-transfer root")
    if document["items"]["far"] != far.items_digest():
        raise ClefError("The far-transfer items have changed since the plan was frozen")
    records = pilot.answered(root)
    values = {c["id"]: parse(records[c["id"]]["response"], c["questions"])
              for c in document["calls"] if c["id"] in records}  # fmt: skip
    return document, values


def _mean(values, model, task, n, field, transform):
    out = []
    for i in range(n):
        got = [values.get(f"{model}/{task}/far/{i}/{ph}") for ph in far.PHRASINGS]
        if any(g is None for g in got):
            return None
        out.append(np.mean([transform(g[field]) for g in got]))
    return np.array(out)


def _fe_slope(lp, comp, y):
    """Slope on lp with a fixed effect per composition."""
    levels = sorted(set(comp.tolist()))
    X = np.c_[lp, *[(comp == c).astype(float) for c in levels]]
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(coef[0])


def price_weight(z, items, mask, rng):
    lp = np.array([it["prior_logodds"] for it in items])[mask]
    comp = np.array([it["composition"] for it in items])[mask]
    y = z[mask]
    alpha = _fe_slope(lp, comp, y)
    n = len(y)
    boots = [
        _fe_slope(lp[idx], comp[idx], y[idx])
        for idx in (rng.integers(0, n, n) for _ in range(BOOT))
    ]
    return alpha, [float(v) for v in np.percentile(boots, [5, 95])]


def _decide(choice):
    return choice["a"] + choice["b"]


def summary(root, urn, near_wait=None):
    """`urn`: {model: urn bookbag fit (alpha, beta, bias, beta_by_draws)}; `near_wait`: {model:
    {"empty": p, "by_net": {k: p}}} from the battery's near desk, optional."""
    document, values = load(root)
    models = list(document["models"])
    items = far.remarks_items()
    nets = np.array([it["net"] for it in items])
    lp = np.array([it["prior_logodds"] for it in items])
    primary = np.abs(nets) <= MODERATE
    out = {}
    for m in models:
        z = _mean(values, m, "remarks", len(items), "answer", _z)
        r = {}
        if z is not None:
            rng = np.random.default_rng(SEED)
            alpha, a90 = price_weight(z, items, primary, rng)
            alpha_all, _ = price_weight(z, items, np.ones(len(items), bool), rng)
            heard = primary & (np.array([it["n"] for it in items]) > 0)
            alpha_heard, heard90 = price_weight(z, items, heard, rng)
            no_remarks = np.array([it["n"] == 0 for it in items])
            alpha_none = float(np.polyfit(lp[no_remarks], z[no_remarks], 1)[0])
            r["price_weight"] = {"alpha": alpha, "alpha_90": a90, "alpha_all_sets": alpha_all,
                                 "alpha_with_remarks": alpha_heard, "alpha_with_remarks_90": heard90,
                                 "alpha_no_remarks": alpha_none,
                                 "urn_alpha": urn[m]["alpha"],
                                 **{f"{o}_urn_alpha": urn[o]["alpha"] for o in models if o != m}}  # fmt: skip
            inverted = {}
            for o in models:
                p = urn[o]
                zc = lp + (z - p["alpha"] * lp - p["bias"]) / p["beta"]
                inverted["own" if o == m else o] = price_weight(zc, items, primary, rng)[0]
            r["price_weight_after_inversion"] = inverted
            comps = np.array([it["composition"] for it in items])
            evidence = {}
            for c in sorted(set(comps.tolist())):
                k = comps == c
                evidence[far.COMPOSITIONS[c]] = float(np.mean(z[k] - alpha * lp[k]))
            e = {n: (evidence[(n, n)] - evidence[(n, 0)]) / 2 for n in (1, 3, 5)}
            b = urn[m]["beta_by_draws"]
            r["sample_size"] = {
                "evidence": {str(n): v for n, v in e.items()},
                "ratio_3_to_1": e[3] / e[1], "ratio_5_to_1": e[5] / e[1],
                "bayes": [3.0, 5.0],
                "urn_predicted": [3 * b["3"] / b["1"], 5 * b["5"] / b["1"]],
                **({"urn_predicted_unanimous": [urn[m]["unanimous"]["ratio_3_to_1"],
                                                urn[m]["unanimous"]["ratio_5_to_1"]]}
                   if "unanimous" in urn[m] else {}),
                "mean_abs_answer_5_agreeing": float(np.mean(np.abs(z[np.abs(nets) == 5]))),
            }  # fmt: skip
        witems = far.wait_items()
        p_dec = _mean(values, m, "wait", len(witems), "decision", _decide)
        if p_dec is not None:
            wnets = np.array([abs(it["net"]) for it in witems])
            empty = [i for i, it in enumerate(witems) if it["sequence"] == ""]
            heard = np.array([it["sequence"] != "" for it in witems])
            r["waiting"] = {
                "decide_with_nothing_heard": float(p_dec[empty[0]]),
                "decide_by_net": {str(k): float(p_dec[heard & (wnets == k)].mean())
                                  for k in sorted(set(wnets[heard].tolist()))},
                "near_desk": (near_wait or {}).get(m),
            }  # fmt: skip
        out[m] = r
    planned = {m: sum(c["model"] == m for c in document["calls"]) for m in models}
    answered = {
        m: sum(c["model"] == m and c["id"] in values for c in document["calls"]) for m in models
    }
    return {
        "schema_version": "epistemics.clef-far.v1",
        "version": document["version"],
        "plan_digest": document["plan_digest"],
        "calls": {m: {"planned": planned[m], "answered": answered[m]} for m in models},
        "models": out,
        "scope": (
            "Answers averaged over three phrasings, clipped at 0.05% and 99.95%. Price weight: "
            "slope on the price's log-odds with a fixed effect per set of remarks, on sets with a "
            "net of at most one remark (90% bootstrap over items); a Bayesian answer has 1. "
            "Urn values from the battery's urn bookbag fit. Elicited outputs of a trained head, "
            "not direct access to beliefs."
        ),
    }


def near_waiting(battery_root):
    """The battery's near desk: P(decide) with nothing heard and by |net count| (both ratios)."""
    from epistemics.clef import battery
    from epistemics.ledger import clef_battery

    document, values = clef_battery.load(battery_root)
    items = battery.beads_items()
    out = {}
    for m in document["models"]:
        p = clef_battery._phrased(values, m, "beads", "desk", len(items), "decision", _decide)[0]
        if p is None:
            continue
        nets = np.array(
            [abs(it["sequence"].count("+") - it["sequence"].count("-")) for it in items]
        )
        heard = np.array([it["sequence"] != "" for it in items])
        empty = ~heard
        out[m] = {"decide_with_nothing_heard": float(p[empty].mean()),
                  "decide_by_net": {str(k): float(p[heard & (nets == k)].mean())
                                    for k in sorted(set(nets[heard].tolist())) if k <= 4}}  # fmt: skip
    return out
