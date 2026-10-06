"""Plan, run and smoke-test the Clef pilot (docs/clef-pilot-design.md, "Implementation").

plan   writes <root>/plan.json (every call's metadata and request digest, the items digest of
       each module) and <root>/requests.jsonl (the frozen bodies). A root's plan is never
       rewritten.
run    sends every planned call not yet answered, after checking each frozen body against its
       digest, and appends one record per call to <root>/calls.jsonl (failures to errors.jsonl).
       Rerunning resumes; nothing is overwritten.
smoke  one call per question type per model, raw responses to <out>/smoke.jsonl, to confirm the
       response shape before a plan is frozen.
"""

import datetime
import json
import os
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from epistemics.clef import requests
from epistemics.clef.answers import parse, unwrap
from epistemics.clef.client import ClefError

PLAN_SCHEMA = "epistemics.clef-pilot-plan.v1"
STOP_AFTER_FAILURES = 5


def _now():
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _append(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _lines(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _design(name):
    """(call builder, version, items digests) of a design: the pilot or the cognitive battery."""
    if name == "battery":
        from epistemics.clef import battery

        return battery.calls, battery.VERSION, {"battery": battery.items_digest()}
    if name == "far":
        from epistemics.clef import far

        return far.calls, far.VERSION, {"far": far.items_digest()}
    if name == "desk":
        from epistemics.clef import desk

        return desk.calls, desk.VERSION, {"desk": desk.items_digest()}
    if name == "desk2":
        from epistemics.clef import desk2

        return desk2.calls, desk2.VERSION, {"desk2": desk2.items_digest()}
    if name == "desk3":
        from epistemics.clef import desk3

        return desk3.calls, desk3.VERSION, {"desk3": desk3.items_digest()}
    if name == "desk4":
        from epistemics.clef import desk4

        return desk4.calls, desk4.VERSION, {"desk4": desk4.items_digest()}
    if name == "desk3-record":
        from epistemics.clef import desk3

        return desk3.record_calls, desk3.VERSION, {"desk3-record": desk3.record_digest()}
    modules = requests.EVIDENT + requests.HINTED + requests.CUES
    return requests.calls, requests.VERSION, {m: requests.items_digest(m) for m in modules}


def plan(root, models=tuple(requests.MODELS), design="pilot"):
    root = Path(root)
    if (root / "plan.json").exists():
        raise ClefError(f"{root} already has a plan; a frozen plan is never rewritten")
    root.mkdir(parents=True, exist_ok=True)
    build, version, items = _design(design)
    planned = build(models)
    calls = [{"id": cid, **meta, "digest": requests.digest(b)} for cid, meta, b in planned]
    if len({c["id"] for c in calls}) != len(calls):
        raise ClefError("Duplicate call ids")
    document = {
        "schema_version": PLAN_SCHEMA,
        "design": design,
        "version": version,
        "created": _now(),
        "models": {m: requests.MODELS[m] for m in models},
        "cover": requests.COVER,
        "items": items,
        "counts": dict(Counter(f"{c['model']}/{c['part']}" for c in calls)),
        "calls": calls,
    }
    document["plan_digest"] = requests.digest(calls)
    with open(root / "requests.jsonl", "w") as f:
        for cid, _, b in planned:
            f.write(json.dumps({"id": cid, "body": b}, ensure_ascii=False) + "\n")
    (root / "plan.json").write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n")
    return document


def load(root):
    root = Path(root)
    document = json.loads((root / "plan.json").read_text())
    if requests.digest(document["calls"]) != document["plan_digest"]:
        raise ClefError("plan.json does not match its digest")
    bodies = {r["id"]: r["body"] for r in _lines(root / "requests.jsonl")}
    for c in document["calls"]:
        if requests.digest(bodies.get(c["id"])) != c["digest"]:
            raise ClefError(f"Frozen body for {c['id']} does not match its digest")
    return document, bodies


def answered(root):
    """{call id: record} for every successful call."""
    return {r["id"]: r for r in _lines(Path(root) / "calls.jsonl") if r["status"] == "ok"}


def run(root, client, limit=None, log=print, workers=1):
    """Send unanswered calls (`workers` at a time); stop after STOP_AFTER_FAILURES consecutive
    failures."""
    root = Path(root)
    document, bodies = load(root)
    done = answered(root)
    pending = [c for c in document["calls"] if c["id"] not in done]
    if limit is not None:
        pending = pending[:limit]
    lock = threading.Lock()
    state = {"failures": 0, "sent": 0, "stop": False}

    def send(c):
        if state["stop"]:
            return
        try:
            payload, elapsed, attempts = client.run(document["models"][c["model"]], bodies[c["id"]])
            output = unwrap(payload)
            if not isinstance(output, dict) or "answers" not in output:
                raise ClefError(f"No answers in response: {json.dumps(payload)[:300]}")
        except ClefError as error:
            with lock:
                state["failures"] += 1
                _append(root / "errors.jsonl", {"id": c["id"], "time": _now(), "error": str(error)})
                log(f"error {c['id']}: {error}")
                if state["failures"] >= STOP_AFTER_FAILURES:
                    state["stop"] = True
            return
        try:
            parse(payload, c["questions"])
            parsed = True
        except (ValueError, KeyError, TypeError):
            parsed = False
        record = {"id": c["id"], "digest": c["digest"], "status": "ok", "parsed": parsed,
                  "response": payload, "response_digest": requests.digest(payload),
                  "elapsed_seconds": round(elapsed, 4), "attempts": attempts, "time": _now()}  # fmt: skip
        with lock:
            state["failures"] = 0
            _append(root / "calls.jsonl", record)
            state["sent"] += 1
            if state["sent"] % 100 == 0:
                log(f"{state['sent']}/{len(pending)} calls")

    if workers <= 1:
        for c in pending:
            send(c)
            if state["stop"]:
                break
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(send, pending))
    if state["stop"]:
        raise ClefError(f"Stopped after {state['failures']} consecutive failures")
    remaining = len(document["calls"]) - len(answered(root))
    log(f"sent {state['sent']}; {remaining} of {len(document['calls'])} planned calls remain")
    return remaining


SMOKE_STATE = (
    "A jar holds 10 marbles: 7 red and 3 blue. One marble is drawn at random. Before drawing, "
    "the person drawing says the jar has been shaken well."
)
SMOKE_QUESTIONS = {
    "noul": {"red": {"type": "noul", "instructions": "Is it true that the drawn marble is red?"}},
    # Direction check: the state makes this false, so the probability of true should be low.
    "noul-false": {
        "twenty": {"type": "noul", "instructions": "Is it true that the jar holds 20 marbles?"}
    },
    "choice": {
        "share": requests.rate_choice(
            "Among jars like this one, what proportion of marbles are red?"
        )
    },
    "score": {
        "shaken": {
            "type": "score",
            "instructions": "How well mixed are the marbles?",
            "criteria": ["Not mixed", "Somewhat mixed", "Well mixed"],
        }
    },
}


def _shape(value, depth=0):
    if isinstance(value, dict):
        if depth > 3:
            return "{...}"
        return {k: _shape(v, depth + 1) for k, v in list(value.items())[:25]}
    if isinstance(value, list):
        return [_shape(value[0], depth + 1), f"... {len(value)} items"] if value else []
    return type(value).__name__


def smoke(out, client, models=tuple(requests.MODELS), log=print):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for model in models:
        for kind, questions in SMOKE_QUESTIONS.items():
            body = requests.body(model, SMOKE_STATE, questions)
            payload, elapsed, attempts = client.run(requests.MODELS[model], body)
            _append(out / "smoke.jsonl", {"model": model, "kind": kind, "body": body,
                                          "response": payload, "elapsed_seconds": round(elapsed, 4),
                                          "attempts": attempts, "time": _now()})  # fmt: skip
            log(f"{model} {kind} ({elapsed:.2f} s): {json.dumps(_shape(payload))}")
            try:
                kinds = {k: q["type"] for k, q in questions.items() if q["type"] != "score"}
                log(f"  parsed: {parse(payload, kinds)}")
            except (ValueError, KeyError, TypeError) as error:
                log(f"  not parsed: {error}")
