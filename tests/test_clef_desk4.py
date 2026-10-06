"""The second confirmation desk: design and analysis path on a shrunken world with a synthetic
model whose beliefs are exact and whose classifier under-reads hawkish remarks (offline)."""

import json

import numpy as np

from epistemics.clef import desk2, desk4, pilot, requests
from epistemics.ledger import clef_desk4


def test_design_is_fixed():
    assert desk4.items_digest() == desk4.items_digest()
    assert {k: len(desk4.meetings(k)) for k in desk4.SEEDS} == {
        "record": 40,
        "pool": 100,
        "test": 1000,
    }
    n = (
        len(desk4.record_remarks())
        + 100 * 7
        + 1000 * 14
        + len(desk2.unique_remarks(desk4.meetings("test")))
    )
    assert len(desk4.calls(("clef",))) == n


class _Synthetic:
    def __init__(self):
        self.meta = {}
        for _, meta, body in desk4.calls(("clef",)):
            self.meta.setdefault(requests.digest(body), meta)
        self.by = {"pool-belief": desk4.meetings("pool"), "belief": desk4.meetings("test"),
                   "choice": desk4.meetings("test")}  # fmt: skip
        test_uniq = desk2.unique_remarks(desk4.meetings("test"))
        signs = {
            (r["speaker"], r["text"]): r["sign"]
            for m in desk4.meetings("test")
            for r in m["remarks"]
        }
        self.signs = {"classify": {i: signs[k] for k, i in test_uniq.items()},
                      "record-classify": {i: s for i, (_, s) in enumerate(desk4.record_remarks())}}  # fmt: skip

    def run(self, model, body):
        meta = self.meta[requests.digest(body)]
        if meta["part"] in self.signs:
            sign = self.signs[meta["part"]][int(meta["key"])]
            answers = {"answer": {"type": "noul", "noul": 0.4 if sign > 0 else 0.02}}
        else:
            e, t = (int(x) for x in meta["key"].split("/"))
            z = desk2.oracle_logodds(self.by[meta["part"]][e], t)
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
                "success": True}, 0.0, 1  # fmt: skip


def test_analysis_path(tmp_path, monkeypatch):
    monkeypatch.setattr(desk4, "COUNTS", {"record": 40, "pool": 30, "test": 60})
    root = tmp_path / "desk4"
    pilot.plan(root, ("clef",), design="desk4")
    assert pilot.run(root, _Synthetic(), log=lambda *_: None, workers=4) == 0
    out = clef_desk4.summary(root, k_values=(5, 10, 30), draws=3, permutations=2000)
    json.dumps(out, allow_nan=False)
    m = out["models"]["clef"]
    assert set(m["primary"]) == {"H1", "H2"} and all("pass" in v for v in m["primary"].values())
    acc = m["classification_accuracy"]["strong"]
    assert acc["raw"] < 1.0 and acc["calibrated"] == 1.0
    assert m["lanes"]["passport_calibrated"]["mean"] >= m["lanes"]["passport_raw"]["mean"]
    assert m["lanes"]["gated"]["mean"] == m["lanes"]["oracle"]["mean"]
