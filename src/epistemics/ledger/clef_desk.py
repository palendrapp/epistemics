"""The simulated central-bank desk (docs/clef-desk-demo.md): lanes scored against known outcomes.

Per model and lane (alone, gated, passport, bayes): mean P&L per episode with a 90% bootstrap
interval over episodes, the share of positions taken with nothing heard, speakers waited, the
share of correct positions, the log loss of the belief at the decision against the outcome, and
the mean distance of that belief from the exact posterior. Also the classification accuracy of
single remarks and how the model's own beliefs scale with the exact evidence.

Elicited outputs of a trained head, not direct access to beliefs.
"""

import numpy as np

from epistemics.clef import desk, pilot
from epistemics.clef.answers import parse
from epistemics.clef.client import ClefError

CLIP = 0.0005
BOOT = 2000
SEED = 20261007
LANES = ("alone", "gated", "passport", "bayes")


def _z(p):
    p = float(np.clip(p, CLIP, 1 - CLIP))
    return float(np.log(p / (1 - p)))


def load(root):
    document, _ = pilot.load(root)
    if document.get("design") != "desk":
        raise ClefError(f"{root} is not a desk root")
    if document["items"]["desk"] != desk.items_digest():
        raise ClefError("The desk episodes have changed since the plan was frozen")
    records = pilot.answered(root)
    values = {c["id"]: parse(records[c["id"]]["response"], c["questions"])
              for c in document["calls"] if c["id"] in records}  # fmt: skip
    return document, values


def _alone_action(choice):
    best = max(choice, key=choice.get)
    return {"a": "rise", "b": "hold", "draw": "wait"}[best]


def simulate(ep, choice_at, belief_at, hawk_of):
    """{lane: (position, speakers heard, belief log-odds at the decision)} for one episode;
    `choice_at(t)`, `belief_at(t)` and `hawk_of(k)` give the model's answers."""
    out = {}
    last = desk.MAX_SPEAKERS
    for lane in LANES:
        for t in range(last + 1):
            if lane == "alone":
                action = _alone_action(choice_at(t))
                logodds = _z(belief_at(t))
                if action == "wait" and t == last:
                    c = choice_at(t)
                    action = "rise" if c["a"] >= c["b"] else "hold"
            else:
                if lane == "gated":
                    logodds = _z(belief_at(t))
                elif lane == "passport":
                    logodds = desk.logit(ep["price"]) + desk.LQ * sum(
                        2 * hawk_of(k) - 1 for k in range(t)
                    )
                else:
                    logodds = desk.bayes_logodds(ep, t)
                action = desk.act(t, logodds)
            if action != "wait":
                out[lane] = (action, t, logodds)
                break
    return out


def _payoff(ep, position, t):
    right = (position == "rise") == ep["rise"]
    return (desk.WIN if right else -desk.WIN) - desk.COST * t


def summary(root):
    document, values = load(root)
    eps = desk.episodes()
    uniq = desk.unique_remarks(eps)
    models = list(document["models"])
    rng = np.random.default_rng(SEED)
    out = {}
    for m in models:

        def choice_at(t, ep, m=m):
            return values[f"{m}/choice/{ep['episode']}/{t}"]["decision"]

        def belief_at(t, ep, m=m):
            return values[f"{m}/belief/{ep['episode']}/{t}"]["answer"]

        def hawk_of(k, ep, m=m):
            r = ep["remarks"][k]
            return values[f"{m}/classify/{uniq[(r['speaker'], r['text'])]}"]["answer"]

        rows = {lane: [] for lane in LANES}
        for ep in eps:
            sim = simulate(ep, lambda t, ep=ep: choice_at(t, ep), lambda t, ep=ep: belief_at(t, ep),
                           lambda k, ep=ep: hawk_of(k, ep))  # fmt: skip
            bayes_final = {lane: desk.bayes_logodds(ep, sim[lane][1]) for lane in LANES}
            for lane, (position, t, logodds) in sim.items():
                p = 1 / (1 + np.exp(-logodds))
                rows[lane].append({
                    "pnl": _payoff(ep, position, t), "heard": t, "right": (position == "rise") == ep["rise"],
                    "log_loss": float(-np.log(np.clip(p if ep["rise"] else 1 - p, CLIP, 1))),
                    "from_bayes": abs(logodds - bayes_final[lane]),
                })  # fmt: skip
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
                "from_bayes": float(np.mean([r["from_bayes"] for r in rs])),
            }  # fmt: skip
        diffs = {}
        for a, b in (("passport", "alone"), ("gated", "alone"), ("passport", "gated")):
            d = np.array(
                [x["pnl"] - y["pnl"] for x, y in zip(rows[a], rows[b], strict=True)], dtype=float
            )
            boots = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(BOOT)]
            diffs[f"{a}_minus_{b}"] = {"mean": float(d.mean()),
                                       "pnl_90": [float(v) for v in np.percentile(boots, [5, 95])]}  # fmt: skip
        hawks = [(values[f"{m}/classify/{i}"]["answer"], key) for key, i in uniq.items()]
        signs = {(r["speaker"], r["text"]): r["sign"] for ep in eps for r in ep["remarks"]}
        accuracy = float(np.mean([(p > 0.5) == (signs[key] > 0) for p, key in hawks]))
        zb, lb = [], []
        for ep in eps:
            for t in range(desk.MAX_SPEAKERS + 1):
                zb.append(_z(belief_at(t, ep)) - desk.logit(ep["price"]))
                lb.append(desk.bayes_logodds(ep, t) - desk.logit(ep["price"]))
        zb, lb = np.array(zb), np.array(lb)
        by_net = {}
        for k in range(1, 5):
            sel = np.isclose(np.abs(lb), k * desk.LQ)
            if sel.any():
                by_net[str(k)] = float(np.mean(np.sign(lb[sel]) * zb[sel]))
        out[m] = {"lanes": lanes, "differences": diffs,
                  "classification": {"remarks": len(hawks), "accuracy": accuracy,
                                     "mean_hawk_hawkish": float(np.mean([p for p, k in hawks if signs[k] > 0])),
                                     "mean_hawk_dovish": float(np.mean([p for p, k in hawks if signs[k] < 0]))},
                  "belief_shift_by_net": by_net,
                  "bayes_shift_by_net": {str(k): k * desk.LQ for k in range(1, 5)}}  # fmt: skip
    planned = {m: sum(c["model"] == m for c in document["calls"]) for m in models}
    answered = {
        m: sum(c["model"] == m and c["id"] in values for c in document["calls"]) for m in models
    }
    return {
        "schema_version": "epistemics.clef-desk.v1",
        "version": document["version"],
        "plan_digest": document["plan_digest"],
        "calls": {m: {"planned": planned[m], "answered": answered[m]} for m in models},
        "episodes": len(eps),
        "outcomes_rise": int(sum(ep["rise"] for ep in eps)),
        "models": out,
        "scope": (
            "Simulated episodes with known outcomes: a rise drawn from the market price, each "
            f"remark pointing to the outcome with probability {desk.Q} (stated as a record). P&L "
            f"per episode: +{desk.WIN} or -{desk.WIN}, minus {desk.COST} per speaker waited; 90% "
            "bootstrap intervals over episodes; differences are paired. Elicited outputs of a "
            "trained head, not direct access to beliefs."
        ),
    }
