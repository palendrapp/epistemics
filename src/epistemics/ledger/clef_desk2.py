"""The robustness desk (docs/clef-desk-demo.md, "Robustness test"): lanes scored on held-out
meetings when speakers differ in reliability, two of them echo, remarks vary in strength and
every parameter is learned from a scorecard of past meetings.

Lanes: alone, gated, recalibrated (the model's belief recalibrated on the past meetings'
outcomes by logistic regression on its belief and the price: a generic fix), passport (classify,
weight each speaker by the estimated record, add, threshold), passport_flat (one pooled weight),
oracle (exact posterior under the true reliabilities and echoes). Thresholds use the optimal
policy for the committee's mean estimated record. P&L per meeting with 90% bootstrap intervals;
paired differences.

Elicited outputs of a trained head, not direct access to beliefs.
"""

import numpy as np

from epistemics.clef import desk, desk2, pilot
from epistemics.clef.answers import parse
from epistemics.clef.client import ClefError

CLIP = 0.0005
BOOT = 2000
SEED = 20261009
LANES = ("alone", "gated", "recalibrated", "passport", "passport_flat", "oracle")
PAIRS = (("passport", "alone"), ("passport", "recalibrated"), ("recalibrated", "alone"),
         ("passport", "gated"), ("passport", "passport_flat"), ("oracle", "passport"))  # fmt: skip


def _z(p):
    p = float(np.clip(p, CLIP, 1 - CLIP))
    return float(np.log(p / (1 - p)))


def load(root):
    document, _ = pilot.load(root)
    if document.get("design") != "desk2":
        raise ClefError(f"{root} is not a robustness-desk root")
    if document["items"]["desk2"] != desk2.items_digest():
        raise ClefError("The robustness-desk meetings have changed since the plan was frozen")
    records = pilot.answered(root)
    values = {c["id"]: parse(records[c["id"]]["response"], c["questions"])
              for c in document["calls"] if c["id"] in records}  # fmt: skip
    return document, values


def logistic(X, y, iters=50, ridge=1e-3):
    """Logistic regression by Newton's method (a small ridge for stability)."""
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X @ w)))
        g = X.T @ (p - y) + ridge * w
        H = X.T @ (X * (p * (1 - p))[:, None]) + ridge * np.eye(len(w))
        w -= np.linalg.solve(H, g)
    return w


def simulate(m, logodds_at, choice_at, tables):
    """{lane: (position, speakers heard, log-odds at the decision)}."""
    out = {}
    last = desk2.PER_MEETING
    for lane in LANES:
        for t in range(last + 1):
            logodds = logodds_at(lane, t)
            if lane == "alone":
                c = choice_at(t)
                action = {"a": "rise", "b": "hold", "draw": "wait"}[max(c, key=c.get)]
                if action == "wait" and t == last:
                    action = "rise" if c["a"] >= c["b"] else "hold"
            else:
                action = desk.act(t, logodds, tables)
            if action != "wait":
                out[lane] = (action, t, logodds)
                break
    return out


def summary(root):
    document, values = load(root)
    history, test = desk2.meetings("history"), desk2.meetings("test")
    card = desk2.scorecard(history)
    est = desk2.estimated_reliability(card)
    qbar = float(np.mean(list(est.values())))
    tables = desk._value_tables(q=qbar, max_speakers=desk2.PER_MEETING)
    uniq = desk2.unique_remarks(test)
    rng = np.random.default_rng(SEED)
    out = {}
    for model in document["models"]:
        X, y = [], []
        for m in history:
            for t in range(desk2.PER_MEETING + 1):
                b = values[f"{model}/history-belief/{m['meeting']}/{t}"]["answer"]
                X.append([1.0, _z(b), desk2.logit(m["price"])])
                y.append(float(m["rise"]))
        w = logistic(np.array(X), np.array(y))
        rows = {lane: [] for lane in LANES}
        for m in test:

            def hawk(k, m=m, model=model):
                r = m["remarks"][k]
                return values[f"{model}/classify/{uniq[(r['speaker'], r['text'])]}"]["answer"]

            def logodds_at(lane, t, m=m, model=model, hawk=hawk, w=w):
                key = f"{m['meeting']}/{t}"
                if lane in ("alone", "gated"):
                    return _z(values[f"{model}/belief/{key}"]["answer"])
                if lane == "recalibrated":
                    z = _z(values[f"{model}/belief/{key}"]["answer"])
                    return float(w @ [1.0, z, desk2.logit(m["price"])])
                if lane == "passport":
                    return desk2.logit(m["price"]) + sum(
                        (2 * hawk(k) - 1) * desk2.logit(est[m["remarks"][k]["index"]])
                        for k in range(t)
                    )
                if lane == "passport_flat":
                    return desk2.logit(m["price"]) + sum(
                        (2 * hawk(k) - 1) * desk2.logit(qbar) for k in range(t)
                    )
                return desk2.oracle_logodds(m, t)

            def choice_at(t, m=m, model=model):
                return values[f"{model}/choice/{m['meeting']}/{t}"]["decision"]

            sim = simulate(m, logodds_at, choice_at, tables)
            echoed = any(r["echoed"] for r in m["remarks"])
            for lane, (position, t, logodds) in sim.items():
                right = (position == "rise") == m["rise"]
                p = 1 / (1 + np.exp(-logodds))
                rows[lane].append({"pnl": (desk2.WIN if right else -desk2.WIN) - desk2.COST * t,
                                   "heard": t, "right": right, "echoed": echoed,
                                   "log_loss": float(-np.log(np.clip(p if m["rise"] else 1 - p, CLIP, 1)))})  # fmt: skip
        lanes = {}
        for lane, rs in rows.items():
            pnl = np.array([r["pnl"] for r in rs], dtype=float)
            boots = [pnl[rng.integers(0, len(pnl), len(pnl))].mean() for _ in range(BOOT)]
            lanes[lane] = {
                "pnl": float(pnl.mean()), "pnl_90": [float(v) for v in np.percentile(boots, [5, 95])],
                "nothing_heard": float(np.mean([r["heard"] == 0 for r in rs])),
                "speakers_heard": float(np.mean([r["heard"] for r in rs])),
                "right": float(np.mean([r["right"] for r in rs])),
                "log_loss": float(np.mean([r["log_loss"] for r in rs])),
                "pnl_meetings_with_echo": float(np.mean([r["pnl"] for r in rs if r["echoed"]])),
                "pnl_meetings_without_echo": float(np.mean([r["pnl"] for r in rs if not r["echoed"]])),
            }  # fmt: skip
        diffs = {}
        for a, b in PAIRS:
            d = np.array(
                [x["pnl"] - y_["pnl"] for x, y_ in zip(rows[a], rows[b], strict=True)], dtype=float
            )
            boots = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(BOOT)]
            diffs[f"{a}_minus_{b}"] = {"mean": float(d.mean()),
                                       "pnl_90": [float(v) for v in np.percentile(boots, [5, 95])]}  # fmt: skip
        classification = {}
        for strength, _ in desk2.STRENGTH:
            items = [(values[f"{model}/classify/{uniq[(r['speaker'], r['text'])]}"]["answer"], r["sign"])
                     for m in test for r in m["remarks"] if r["strength"] == strength]  # fmt: skip
            classification[strength] = {
                "remarks": len(items),
                "accuracy": float(np.mean([(p > 0.5) == (s > 0) for p, s in items])),
                "mean_hawk_when_hawkish": float(np.mean([p for p, s in items if s > 0])),
                "mean_hawk_when_dovish": float(np.mean([p for p, s in items if s < 0])),
            }
        out[model] = {"lanes": lanes, "differences": diffs, "classification": classification,
                      "recalibration_weights": {"intercept": float(w[0]), "belief": float(w[1]),
                                                "price": float(w[2])}}  # fmt: skip
    return {
        "schema_version": "epistemics.clef-desk2.v1",
        "version": document["version"],
        "plan_digest": document["plan_digest"],
        "meetings": {"history": len(history), "test": len(test),
                     "test_rises": int(sum(m["rise"] for m in test))},
        "scorecard": {desk2.SPEAKERS[j]: {"record": list(card[j]), "estimated": est[j],
                                          "true": desk2.RELIABILITY[j], "echoes": j in desk2.ECHOERS}
                      for j in card},
        "mean_estimated_record": qbar,
        "models": out,
        "scope": (
            "Held-out meetings; every parameter from a scorecard of past meetings; two speakers "
            "echo the previous speaker (not told, not modelled by the passport lane). P&L per "
            f"meeting: +{desk2.WIN} or -{desk2.WIN}, minus {desk2.COST} per speaker waited; 90% "
            "bootstrap intervals; differences paired. Elicited outputs of a trained head, not "
            "direct access to beliefs."
        ),
    }  # fmt: skip
