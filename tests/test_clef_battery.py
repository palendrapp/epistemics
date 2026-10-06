"""Clef cognitive battery: items, optimal stopping, and parameter recovery through the full
plan-run-analysis path with a synthetic responder (offline; no live calls)."""

import json

import numpy as np

from epistemics.clef import battery, pilot, requests
from epistemics.ledger import clef_battery


def test_items_and_calls():
    assert len(battery.bookbag_items()) == 120
    assert len(battery.beads_items()) == 2 * len(battery.bead_sequences()) == 58
    assert len(battery.tone_items()) == 36
    calls = battery.calls(("clef",))
    assert len(calls) == len({cid for cid, _, _ in calls}) == 1400
    assert [requests.digest(b) for *_, b in calls] == [
        requests.digest(b) for *_, b in battery.calls(("clef",))
    ]
    item = battery.bookbag_items()[0]
    assert np.isclose(
        item["llr"], (2 * item["r"] - item["n"]) * np.log(item["accuracy"] / (1 - item["accuracy"]))
    )


def test_optimal_stopping_decides_on_a_lead_of_two():
    for q in battery.RATIOS:
        policy = battery.optimal_policy(q)
        assert not policy[(0, 0)][0] and not policy[(1, 1)][0] and policy[(2, 2)][0]
        assert np.isclose(battery.optimal_threshold(q), 2 * battery.logit(q))


TRUTH = {
    "clef": {"alpha": 0.6, "beta": 1.3, "delta": 0.25, "bias": -0.3, "theta": 1.5, "kappa": 2.0,
             "tone": {"hedged": 0.4, "plain": 0.9, "confident": 2.2}},
    "clef-flash": {"alpha": 1.0, "beta": 0.8, "delta": 0.0, "bias": 0.2, "theta": 0.6, "kappa": 4.0,
                   "tone": {"hedged": 0.8, "plain": 0.9, "confident": 1.0}},
}  # fmt: skip


def _sig(z):
    return float(1 / (1 + np.exp(-z)))


class _Synthetic:
    """Answers each call from known parameters, the same in both domains, with a small
    phrasing offset."""

    def __init__(self, models):
        self.meta = {requests.digest(b): m for _, m, b in battery.calls(models)}

    def run(self, model, body):
        meta = self.meta[requests.digest(body)]
        t = TRUTH[meta["model"]]
        jitter = (meta["phrasing"] - 1) * 0.05
        task, i = meta["task"], meta["item"]
        if meta["part"] == "belief":
            it = battery.beads_items()[i]
            answers = {"answer": {"type": "noul", "noul": _sig(0.9 * it["posterior_logodds"])}}
        elif task == "bookbag":
            it = battery.bookbag_items()[i]
            agree = np.sign(it["prior_logodds"]) * np.sign(it["llr"])
            z = (
                t["alpha"] * it["prior_logodds"]
                + (t["beta"] + t["delta"] * agree) * it["llr"]
                + t["bias"]
            )
            answers = {"answer": {"type": "noul", "noul": _sig(z + jitter)}}
        elif task == "beads":
            it = battery.beads_items()[i]
            post = it["posterior_logodds"]
            dec = _sig(t["kappa"] * (abs(post) - t["theta"]))
            side = 1.0 if post > 0 else 0.0 if post < 0 else 0.5
            answers = {
                "decision": {
                    "type": "choice",
                    "choice": "draw",
                    "confidence": 0.5,
                    "probabilities": {"a": dec * side, "b": dec * (1 - side), "draw": 1 - dec},
                }
            }
        else:
            it = battery.tone_items()[i]
            shift = (
                t["tone"][it["wording"]]
                if it["record"] is None
                else it["direction"] * it["record_llr"]
            )
            answers = {
                "answer": {
                    "type": "noul",
                    "noul": _sig(it["prior_logodds"] + it["direction"] * shift + jitter),
                }
            }
        return {"result": {"model": model, "answers": answers, "usage": {"input_tokens": 200, "output_tokens": 0}},
                "success": True}, 0.01, 1  # fmt: skip


def test_parameters_are_recovered_and_transfer_is_detected(tmp_path):
    root = tmp_path / "battery"
    models = tuple(requests.MODELS)
    document = pilot.plan(root, models, design="battery")
    assert document["design"] == "battery" and len(document["calls"]) == 2800
    assert pilot.run(root, _Synthetic(models), log=lambda *_: None, workers=4) == 0
    out = clef_battery.summary(root)
    json.dumps(out, allow_nan=False)
    for m, t in TRUTH.items():
        for d in battery.DOMAINS:
            b = out["models"][m]["bookbag"][d]
            full = b["with_asymmetry"]
            assert (
                abs(full["alpha"] - t["alpha"]) < 0.05 and abs(full["beta"] - t["beta"]) < 0.05
            ), (
                m,
                d,
                b,
            )
            assert abs(b["confirmation_delta"] - t["delta"]) < 0.05, (m, d, b)
            if t["delta"] == 0:  # without an asymmetry the simple fit is the full one
                assert abs(b["alpha"] - t["alpha"]) < 0.05 and abs(b["beta"] - t["beta"]) < 0.05
            for q, r in out["models"][m]["beads"][d]["ratios"].items():
                assert abs(r["theta"] - t["theta"]) < 0.15, (m, d, q, r)
            tone = out["models"][m]["tone"][d]
            want = t["tone"]["confident"] - t["tone"]["hedged"]
            assert abs(tone["tone_index"] - want) < 0.1, (m, d, tone)
            assert abs(tone["tone_index_with_record"]) < 0.05
        tr = out["transfer"][m]
        other = next(o for o in TRUTH if o != m)
        rmse = tr["bookbag"]["desk_rmse"]
        assert rmse["from_urn"] < rmse["bayes"] and rmse["from_urn"] < rmse[f"from_{other}_urn"]
        inv = tr["inversion"]["desk_error_vs_bayes"]
        assert (
            inv["inverted_own_urn"] < inv["raw"]
            and inv["inverted_own_urn"] < inv[f"inverted_{other}_urn"]
        )
        tone_rmse = tr["tone"]["desk_rmse"]
        assert tone_rmse["from_urn"] < tone_rmse[f"from_{other}_urn"]
        for q, r in tr["beads"].items():
            assert r["desk_error"]["from_urn"] < r["desk_error"][f"from_{other}_urn"], (m, q, r)
