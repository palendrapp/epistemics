"""The robustness desk: the world, the scorecard and the lane plumbing with a synthetic model
whose beliefs are the exact posterior (offline)."""

import json

import numpy as np

from epistemics.clef import desk2, pilot, requests
from epistemics.ledger import clef_desk2


def test_world():
    test = desk2.meetings("test")
    assert test == desk2.meetings("test") and len(test) == desk2.TEST
    assert all(len(m["remarks"]) == desk2.PER_MEETING for m in test)
    assert any(r["echoed"] for m in test for r in m["remarks"])
    card = desk2.scorecard()
    assert sum(n for _, n in card.values()) == desk2.HISTORY * desk2.PER_MEETING
    # The oracle is the exact posterior: one independent remark moves it by its speaker's logit.
    m = test[0]
    r = m["remarks"][0]
    shift = desk2.oracle_logodds(m, 1) - desk2.logit(m["price"])
    assert np.isclose(abs(shift), desk2.logit(desk2.RELIABILITY[r["index"]]))


class _Exact:
    """Beliefs equal to the exact posterior; acts at once; classifies by the remark's sign."""

    def __init__(self):
        self.meta = {}
        for _, meta, body in desk2.calls(("clef",)):
            self.meta.setdefault(requests.digest(body), []).append(meta)
        self.meetings = {"history-belief": desk2.meetings("history"), "belief": desk2.meetings("test"),
                         "choice": desk2.meetings("test")}  # fmt: skip
        uniq = desk2.unique_remarks(desk2.meetings("test"))
        signs = {
            (r["speaker"], r["text"]): r["sign"]
            for m in desk2.meetings("test")
            for r in m["remarks"]
        }
        self.sign = {i: signs[k] for k, i in uniq.items()}

    def run(self, model, body):
        meta = self.meta[requests.digest(body)][0]
        if meta["part"] == "classify":
            answers = {
                "answer": {
                    "type": "noul",
                    "noul": 0.95 if self.sign[int(meta["key"])] > 0 else 0.05,
                }
            }
        else:
            e, t = (int(x) for x in meta["key"].split("/"))
            z = desk2.oracle_logodds(self.meetings[meta["part"]][e], t)
            if meta["part"] == "choice":
                probs = (
                    {"a": 0.8, "b": 0.1, "draw": 0.1}
                    if z > 0
                    else {"a": 0.1, "b": 0.8, "draw": 0.1}
                )
                answers = {
                    "decision": {
                        "type": "choice",
                        "choice": "a",
                        "confidence": 0.8,
                        "probabilities": probs,
                    }
                }
            else:
                answers = {"answer": {"type": "noul", "noul": float(1 / (1 + np.exp(-z)))}}
        return {"result": {"model": model, "answers": answers, "usage": {"input_tokens": 400, "output_tokens": 0}},
                "success": True}, 0.01, 1  # fmt: skip


def test_lanes_with_exact_beliefs(tmp_path):
    root = tmp_path / "desk2"
    pilot.plan(root, ("clef",), design="desk2")
    assert pilot.run(root, _Exact(), log=lambda *_: None, workers=4) == 0
    out = clef_desk2.summary(root)
    json.dumps(out, allow_nan=False)
    lanes = out["models"]["clef"]["lanes"]
    # Exact beliefs acted on at the same threshold are the oracle lane.
    assert lanes["gated"]["pnl"] == lanes["oracle"]["pnl"]
    assert lanes["alone"]["nothing_heard"] == 1.0
    assert out["models"]["clef"]["recalibration_weights"]["belief"] > 0.5
    assert out["models"]["clef"]["classification"]["mixed"]["accuracy"] == 1.0
