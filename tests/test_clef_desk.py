"""The simulated desk: episodes, optimal stopping, and the lane scoring with a synthetic model
that jumps to conclusions and compresses evidence (offline)."""

import json

import numpy as np

from epistemics.clef import desk, pilot, requests
from epistemics.ledger import clef_desk


def test_episodes_and_optimal_stopping():
    eps = desk.episodes()
    assert len(eps) == 60 and eps == desk.episodes()
    agree = np.mean([r["sign"] == (1 if ep["rise"] else -1) for ep in eps for r in ep["remarks"]])
    assert 0.6 < agree < 0.8
    assert desk.act(0, 0.0) == "wait" and desk.act(1, desk.LQ) == "wait"
    assert desk.act(2, 2 * desk.LQ) == "rise" and desk.act(2, -2 * desk.LQ) == "hold"
    assert desk.act(desk.MAX_SPEAKERS, 0.1) == "rise"
    assert len(desk.calls(("clef",))) == 2 * 60 * 7 + len(desk.unique_remarks(eps))


def _sig(z):
    return float(1 / (1 + np.exp(-z)))


class _Synthetic:
    """Acts on a lead of one (or at once when the price is 65%), states beliefs with the
    evidence compressed to n**0.5, and classifies every remark correctly."""

    def __init__(self):
        self.meta = {requests.digest(b): m for _, m, b in desk.calls(("clef",))}
        self.eps = desk.episodes()
        self.sign = {(r["speaker"], r["text"]): r["sign"] for ep in self.eps for r in ep["remarks"]}

    def run(self, model, body):
        meta = self.meta[requests.digest(body)]
        if meta["part"] == "classify":
            i = int(meta["key"])
            key = next(k for k, v in desk.unique_remarks(self.eps).items() if v == i)
            answers = {"answer": {"type": "noul", "noul": 0.97 if self.sign[key] > 0 else 0.03}}
        else:
            e, t = (int(x) for x in meta["key"].split("/"))
            ep = self.eps[e]
            net = sum(r["sign"] for r in ep["remarks"][:t])
            if meta["part"] == "belief":
                z = desk.logit(ep["price"]) + desk.LQ * np.sign(net) * abs(net) ** 0.5
                answers = {"answer": {"type": "noul", "noul": _sig(z)}}
            else:
                # Identical states (nothing heard, same price) are identical requests, so the
                # hasty choice depends on the price only.
                hasty = t == 0 and ep["price"] == 0.65
                act = hasty or abs(net) >= 1
                lean = net > 0 or (net == 0 and ep["price"] >= 0.5)
                probs = (
                    (
                        {"a": 0.9, "b": 0.05, "draw": 0.05}
                        if lean
                        else {"a": 0.05, "b": 0.9, "draw": 0.05}
                    )
                    if act
                    else {"a": 0.05, "b": 0.05, "draw": 0.9}
                )
                answers = {
                    "decision": {
                        "type": "choice",
                        "choice": max(probs, key=probs.get),
                        "confidence": 0.9,
                        "probabilities": probs,
                    }
                }
        return {"result": {"model": model, "answers": answers, "usage": {"input_tokens": 300, "output_tokens": 0}},
                "success": True}, 0.01, 1  # fmt: skip


def test_lanes_are_scored(tmp_path):
    root = tmp_path / "desk"
    pilot.plan(root, ("clef",), design="desk")
    assert pilot.run(root, _Synthetic(), log=lambda *_: None, workers=4) == 0
    out = clef_desk.summary(root)
    json.dumps(out, allow_nan=False)
    m = out["models"]["clef"]
    lanes = m["lanes"]
    assert m["classification"]["accuracy"] == 1.0
    # Perfect classification makes the passport lane the exact posterior.
    assert (
        lanes["passport"] == {**lanes["bayes"]}
        or abs(lanes["passport"]["pnl"] - lanes["bayes"]["pnl"]) < 1e-9
    )
    assert lanes["alone"]["nothing_heard"] > 0.2 and lanes["passport"]["nothing_heard"] == 0
    assert lanes["gated"]["nothing_heard"] == 0
    assert m["belief_shift_by_net"]["4"] < 4 * desk.LQ
