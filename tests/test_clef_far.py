"""Clef far transfer: items, and recovery of the price weight, the inversion check and the
sample-size ratios through plan-run-analysis with a synthetic responder (offline)."""

import json

import numpy as np

from epistemics.clef import far, pilot, requests
from epistemics.ledger import clef_far


def test_items_and_calls():
    assert len(far.remarks_items()) == 65 and len(far.wait_items()) == 21
    calls = far.calls(("clef",))
    assert len(calls) == len({cid for cid, _, _ in calls}) == 258
    for it in far.remarks_items():
        assert sum(s > 0 for _, s, _ in it["remarks"]) == it["r"] and len(it["remarks"]) == it["n"]
    # The same remarks at every price, so the price weight is identified.
    by_comp = {}
    for it in far.remarks_items():
        by_comp.setdefault(it["composition"], set()).add(json.dumps(it["remarks"]))
    assert all(len(v) == 1 for v in by_comp.values())


TRUTH = {"clef": {"alpha": 0.8, "bias": -0.2, "power": 0.6, "theta": 1.5, "empty": 0.2},
         "clef-flash": {"alpha": 0.35, "bias": -0.2, "power": 0.8, "theta": 0.5, "empty": 0.4}}  # fmt: skip
URN = {"clef": {"alpha": 0.8, "beta": 1.2, "bias": -0.2, "beta_by_draws": {"1": 2.0, "3": 1.3, "5": 1.0}},
       "clef-flash": {"alpha": 0.35, "beta": 1.1, "bias": -0.2, "beta_by_draws": {"1": 2.5, "3": 1.4, "5": 1.0}}}  # fmt: skip


def _sig(z):
    return float(1 / (1 + np.exp(-z)))


class _Synthetic:
    def __init__(self, models):
        self.meta = {requests.digest(b): m for _, m, b in far.calls(models)}

    def run(self, model, body):
        meta = self.meta[requests.digest(body)]
        t = TRUTH[meta["model"]]
        if meta["task"] == "remarks":
            it = far.remarks_items()[meta["item"]]
            ev = np.sign(it["net"]) * abs(it["net"]) ** t["power"]
            z = t["alpha"] * it["prior_logodds"] + t["bias"] + ev + (meta["phrasing"] - 1) * 0.05
            answers = {"answer": {"type": "noul", "noul": _sig(z)}}
        else:
            it = far.wait_items()[meta["item"]]
            dec = t["empty"] if not it["sequence"] else _sig(2 * (abs(it["net"]) - t["theta"]))
            side = 1.0 if it["net"] > 0 else 0.0 if it["net"] < 0 else 0.5
            answers = {
                "decision": {
                    "type": "choice",
                    "choice": "draw",
                    "confidence": 0.5,
                    "probabilities": {"a": dec * side, "b": dec * (1 - side), "draw": 1 - dec},
                }
            }
        return {"result": {"model": model, "answers": answers, "usage": {"input_tokens": 300, "output_tokens": 0}},
                "success": True}, 0.01, 1  # fmt: skip


def test_far_parameters_are_recovered(tmp_path):
    root = tmp_path / "far"
    models = tuple(requests.MODELS)
    assert len(pilot.plan(root, models, design="far")["calls"]) == 516
    assert pilot.run(root, _Synthetic(models), log=lambda *_: None, workers=4) == 0
    out = clef_far.summary(root, URN)
    json.dumps(out, allow_nan=False)
    for m, t in TRUTH.items():
        r = out["models"][m]
        assert abs(r["price_weight"]["alpha"] - t["alpha"]) < 0.03, r["price_weight"]
        inv = r["price_weight_after_inversion"]
        other = next(o for o in TRUTH if o != m)
        assert abs(inv["own"] - 1) < 0.03 and abs(inv[other] - 1) > 0.2, inv
        s = r["sample_size"]
        assert (
            abs(s["ratio_3_to_1"] - 3 ** t["power"]) < 0.05
            and abs(s["ratio_5_to_1"] - 5 ** t["power"]) < 0.05
        )
        w = r["waiting"]
        assert abs(w["decide_with_nothing_heard"] - t["empty"]) < 1e-6
        assert w["decide_by_net"]["2"] > w["decide_by_net"]["0"]
