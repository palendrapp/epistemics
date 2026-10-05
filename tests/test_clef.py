"""Clef pilot: request building, answer parsing, the client, the frozen plan and the analysis.

All offline. The client is exercised with a mocked opener and the pilot with a synthetic responder
(an exact Bayesian observer standing in for Clef), so these tests cover the code path, not the
live service; live coverage is the smoke test (docs/clef-pilot-design.md).
"""

import io
import json
import urllib.error
from collections import Counter

import numpy as np
import pytest

from epistemics.clef import pilot, requests
from epistemics.clef.answers import choice, noul, parse, rate
from epistemics.clef.client import ClefError, Client
from epistemics.disposition_tasks.render import items_for, render
from epistemics.dispositions import evident, observers


def test_plan_has_the_designed_calls():
    calls = requests.calls()
    assert len({cid for cid, _, _ in calls}) == len(calls) == 768
    counts = Counter(f"{m['model']}/{m['part']}" for _, m, _ in calls)
    for model in requests.MODELS:
        assert {p: counts[f"{model}/{p}"] for p in ("q1", "q2", "q3", "joint", "repeat",
                "paraphrase")} == {"q1": 48, "q2": 96, "q3": 48, "joint": 120, "repeat": 48,
                                   "paraphrase": 24}  # fmt: skip
    again = requests.calls()
    assert [requests.digest(b) for _, _, b in calls] == [requests.digest(b) for _, _, b in again]


def test_questions_are_converted_verbatim():
    q = "What is the probability that Fenwick Dairy's demand is high?"
    assert requests.noul(q)["instructions"] == "Is it true that Fenwick Dairy's demand is high?"
    assert requests.paraphrase(q)["instructions"] == "Is Fenwick Dairy's demand high?"
    rate_q = requests.rate_choice("Among outlets like X, what proportion relay?")
    assert list(rate_q["criteria"]) == list(requests.RATE_KEYS)
    assert rate_q["criteria"]["p100"] == "100%" and len(rate_q["criteria"]) == 21
    with pytest.raises(ValueError):
        requests.noul("How likely is it?")


def test_joint_wording_matches_the_cue_modules_own_items():
    for module in requests.CUES:
        items = items_for(module)
        for i, kind in enumerate(items["kind"]):
            question = render(module, "markets", i, requests.CUES_VARIANT)["question"]
            if kind == "probe":
                assert question == requests.probe_question(module, i)
            elif kind == "rate":
                assert question == requests.rate_question(module, i)


def test_joint_calls_order_questions():
    module = "relay-hinted"
    i = requests.described_forecasts(module)[0]
    _, forward = requests.joint(module, "alone", i, "forward")
    _, reverse = requests.joint(module, "alone", i, "reverse")
    assert tuple(forward) == ("rate", "probe", "forecast")
    assert tuple(reverse) == ("forecast", "probe", "rate")
    assert len(requests.described_forecasts(module)) == 20


def test_answer_shapes():
    assert noul(0.7) == 0.7
    assert noul({"probability": 0.7}) == 0.7
    assert noul({"probabilities": {"true": 0.7, "false": 0.3}}) == 0.7
    assert noul({"probabilities": [{"option": "TRUE", "probability": 0.7}]}) == 0.7
    with pytest.raises(ValueError):
        noul({"answer": "yes"})
    flat = {k: 1 / 21 for k in requests.RATE_KEYS}
    assert np.isclose(choice({"probabilities": flat}).sum(), 1)
    peaked = {k: (1.0 if k == "p30" else 0.0) for k in requests.RATE_KEYS}
    assert rate({"probabilities": peaked}) == (0.3, 0.3)
    with pytest.raises(ValueError):
        choice({"probabilities": {"p00": 1.0}})
    wrapped = {"result": {"answers": {"a": {"probability": 0.2}}}, "success": True}
    assert parse(wrapped, {"a": "noul"}) == {"a": 0.2}


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_client_retries_transient_errors_and_never_reports_credentials():
    attempts = []

    def opener(request, timeout):
        attempts.append(request.full_url)
        if len(attempts) == 1:
            raise urllib.error.HTTPError(request.full_url, 429, "busy", {}, io.BytesIO(b"slow"))
        return _Response(json.dumps({"result": {"answers": {}}}).encode())

    client = Client("acct-123", "secret-token", backoff=0, opener=opener)
    payload, _, tries = client.run("@cf/cloudflare/clef", {"model": "clef"})
    assert tries == 2 and payload == {"result": {"answers": {}}}
    assert attempts[0].endswith("/accounts/acct-123/ai/run/@cf/cloudflare/clef")

    def refuses(request, timeout):
        body = b"bad token secret-token for account acct-123"
        raise urllib.error.HTTPError(request.full_url, 400, "bad", {}, io.BytesIO(body))

    with pytest.raises(ClefError) as error:
        Client("acct-123", "secret-token", backoff=0, opener=refuses).run("m", {})
    assert "secret-token" not in str(error.value) and "acct-123" not in str(error.value)


def test_client_needs_both_environment_variables(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acct")
    with pytest.raises(ClefError):
        Client.from_env()


# A synthetic Clef: an exact Bayesian observer whose structure prior for a described source is
# RATE[slot] (anchors 0.5), stating that prior as its base rate.
RATE = {0: 0.2, 1: 0.35, 2: 0.5, 3: 0.65, 4: 0.8}


def _sigmoid(z):
    return float(1 / (1 + np.exp(-z)))


def _truth(meta, qid):
    module, i = meta["module"], meta["item"]
    items = items_for(module)
    if module in requests.EVIDENT:
        return _sigmoid(evident.correct(module, items)[i])
    sub = {k: np.asarray(v)[[i]] for k, v in items.items()}
    slot = int(items["slot"][i])
    r = RATE.get(slot, 0.5)
    structure = requests.STRUCTURE[module]
    kind = str(items["kind"][i])
    if qid == "rate" or kind == "rate":
        return r
    if qid == "probe" or kind == "probe":
        p = observers.structure_posterior(structure, sub, r)[0]
        return 0.5 if np.isnan(p) else float(p)
    observe = observers.corroboration if structure == "corroboration" else observers.disclosure
    return _sigmoid(observe(sub, np.array([r]), 1.0)[0])


class _Synthetic:
    def __init__(self, models=tuple(requests.MODELS)):
        self.meta = {requests.digest(b): m for _, m, b in requests.calls(models)}
        self.sent = 0

    def run(self, model, body):
        meta = self.meta[requests.digest(body)]
        answers = {}
        for qid, q in body["questions"].items():
            value = _truth(meta, qid)
            if q["type"] == "choice":
                key = f"p{round(value * 20) * 5:02d}"
                answers[qid] = {"choice": key, "confidence": 1.0,
                                "probabilities": {k: float(k == key) for k in requests.RATE_KEYS}}  # fmt: skip
            else:
                answers[qid] = {"probabilities": {"true": value, "false": 1 - value}}
        self.sent += 1
        return {"result": {"model": model, "answers": answers, "usage": {"prompt_tokens": 300}},
                "success": True}, 0.01, 1  # fmt: skip


def test_plan_is_frozen_and_runs_resume(tmp_path):
    root = tmp_path / "pilot"
    document = pilot.plan(root, ("clef-flash",))
    assert len(document["calls"]) == 384
    with pytest.raises(ClefError):
        pilot.plan(root, ("clef-flash",))
    client = _Synthetic(("clef-flash",))
    remaining = pilot.run(root, client, limit=10, log=lambda *_: None)
    assert remaining == 374 and len(pilot.answered(root)) == 10
    pilot.run(root, client, limit=5, log=lambda *_: None)
    assert len(pilot.answered(root)) == 15 and client.sent == 15
    lines = (root / "requests.jsonl").read_text().splitlines()
    first = json.loads(lines[0])
    first["body"]["state"] += " "
    (root / "requests.jsonl").write_text("\n".join([json.dumps(first), *lines[1:]]) + "\n")
    with pytest.raises(ClefError):
        pilot.load(root)


def test_analysis_recovers_a_synthetic_bayesian(tmp_path):
    from epistemics.ledger import clef

    root = tmp_path / "pilot"
    pilot.plan(root, ("clef",))
    assert pilot.run(root, _Synthetic(("clef",)), log=lambda *_: None) == 0
    out = clef.summary(root)
    m = out["models"]["clef"]
    assert m["calls"] == {"planned": 384, "answered": 384}
    for module in requests.EVIDENT:
        assert m["q1"][module]["structure_use"] == 1.0
        assert m["q1"][module]["false_structure"] == 0.0
        assert m["q1"][module]["error"] < 0.05
    assert m["q4"]["repeat"]["deterministic"] and m["q4"]["paraphrase"] == 0
    for module, w in m["q3"]["within"].items():
        assert w["forecast_gap"] < 0.05 and w["probe_gap"] < 0.05, module
        assert w["forecast_gap_rotated"] > w["forecast_gap"] + 0.05, module
    for module, a in m["q3"]["across"].items():
        assert a["gap"] < 0.1, module
    for module in requests.HINTED:
        assert m["q2"][module]["deviation"] == 0  # the synthetic answers ignore the variant
        assert np.allclose(m["q2"][module]["implied"]["alone"], list(RATE.values()), atol=0.05)
    json.dumps(out, allow_nan=False)
