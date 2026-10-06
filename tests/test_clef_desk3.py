"""The confirmation desk: the preregistered statistics and the analysis path on a shrunken
world with a synthetic model whose beliefs are the exact posterior (offline)."""

import json

import numpy as np
import pytest

from epistemics.clef import desk2, desk3, pilot, requests
from epistemics.ledger import clef_desk3


def test_sign_flip_and_holm():
    rng = np.random.default_rng(0)
    assert clef_desk3.sign_flip_p(rng.normal(1.0, 1.0, 200), permutations=2000) < 0.01
    assert clef_desk3.sign_flip_p(rng.normal(0.0, 1.0, 200), permutations=2000) > 0.01
    adjusted = clef_desk3.holm({"a": 0.01, "b": 0.02, "c": 0.04})
    assert adjusted == pytest.approx({"a": 0.03, "b": 0.04, "c": 0.04})


def test_design_is_fixed():
    assert desk3.items_digest() == desk3.items_digest()
    assert {k: len(desk3.meetings(k)) for k in desk3.SEEDS} == {
        "record": 40,
        "pool": 100,
        "test": 400,
    }
    assert len(desk3.calls(("clef",))) == 100 * 7 + 400 * 14 + len(
        desk2.unique_remarks(desk3.meetings("test"))
    )


class _Exact:
    def __init__(self):
        self.meta = {}
        for _, meta, body in desk3.calls(("clef",)) + desk3.record_calls(("clef",)):
            self.meta.setdefault(requests.digest(body), meta)
        self.record = [sign for _, sign in sorted(desk3.record_remarks().items())]
        self.by = {"pool-belief": desk3.meetings("pool"), "belief": desk3.meetings("test"),
                   "choice": desk3.meetings("test")}  # fmt: skip
        uniq = desk2.unique_remarks(desk3.meetings("test"))
        signs = {
            (r["speaker"], r["text"]): r["sign"]
            for m in desk3.meetings("test")
            for r in m["remarks"]
        }
        self.sign = {i: signs[k] for k, i in uniq.items()}

    def run(self, model, body):
        meta = self.meta[requests.digest(body)]
        if meta["part"] in ("classify", "record-classify"):
            signs = self.sign if meta["part"] == "classify" else dict(enumerate(self.record))
            # Under-reads hawkish remarks, as Clef does with mild ones: calibration should fix it.
            answers = {
                "answer": {"type": "noul", "noul": 0.4 if signs[int(meta["key"])] > 0 else 0.02}
            }
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
    monkeypatch.setattr(desk3, "COUNTS", {"record": 40, "pool": 30, "test": 60})
    monkeypatch.setattr(clef_desk3, "PERMUTATIONS", 2000)
    root = tmp_path / "desk3"
    pilot.plan(root, ("clef",), design="desk3")
    assert pilot.run(root, _Exact(), log=lambda *_: None, workers=4) == 0
    out = clef_desk3.summary(root, k_values=(5, 10, 30), draws=3)
    json.dumps(out, allow_nan=False)
    m = out["models"]["clef"]
    assert set(m["primary"]) == {"H1", "H2"}
    assert all("p_holm" in v and "pass" in v for v in m["primary"].values())
    # Exact beliefs at the same threshold are the oracle; acting at once is never waiting.
    assert m["lanes"]["gated"]["mean"] == m["lanes"]["oracle"]["mean"]
    assert m["nothing_heard"]["alone"] == 1.0
    record_root = tmp_path / "record"
    pilot.plan(record_root, ("clef",), design="desk3-record")
    assert pilot.run(record_root, _Exact(), log=lambda *_: None, workers=4) == 0
    e = clef_desk3.exploratory(root, record_root)["models"]["clef"]
    assert e["classification_accuracy"]["strong"]["raw"] < 1.0
    assert e["classification_accuracy"]["strong"]["calibrated"] == 1.0
    assert e["passport_variants"]["calibrated"]["mean"] >= e["passport_variants"]["as_run"]["mean"]
