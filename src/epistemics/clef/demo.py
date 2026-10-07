"""Live demo of the Clef battery and desk (docs/clef-desk-demo.md, "Live demo").

uv run python -m epistemics.clef.demo [--port 8765] [--replay]

Serves a page on 127.0.0.1 and streams each act as server-sent events while Clef answers:

  act 1  the passport: on urns, how much one draw is worth against several (sample-size neglect)
         and whether it decides before the evidence warrants (jumping to conclusions)
  act 2  transfer: the same measures on natural-language central-bank remarks, against the
         curve the urns predict
  act 3  mitigation, on the preregistered confirmation desk (docs/clef-desk4-preregistration.md):
         the model's remark classifier is calibrated on the desk's labelled past remarks, the
         generic recalibration is fitted on ten of the model's own past forecasts, and held-out
         meetings are traded by the model alone, its belief gated at the optimal threshold, the
         recalibrated belief, the passport lane (calibrated classification, evidence added in
         code, optimal threshold) and the oracle, with the outcome and a running P&L

Live mode calls Workers AI with credentials from the environment or .env (never sent to the
page). Replay mode reads the recorded runs (output/clef-battery-*, clef-far-*, clef-desk4-*);
Clef is deterministic, so a live run reproduces them, and replaying all 1,000 meetings of act 3
reproduces the preregistered ledger (tests/test_clef_demo.py).
"""

import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

from epistemics.clef import battery, desk, desk2, desk4, far, requests
from epistemics.clef.answers import parse
from epistemics.clef.client import Client, load_env_file

ROOTS = {
    "battery": "output/clef-battery-20261006",
    "far": "output/clef-far-20261006",
    "desk4": "output/clef-desk4-20261006",
}
PREREGISTERED = "output/clef-desk4-20261006.json"
PAGE = Path(__file__).parent / "assets" / "demo.html"
CLIP = 0.0005


def _z(p):
    p = float(np.clip(p, CLIP, 1 - CLIP))
    return float(np.log(p / (1 - p)))


class Answers:
    """Answers by call id: from Clef (live) or from the recorded roots (replay)."""

    def __init__(self, live):
        self.live = live
        self.client = None
        self.cache = {}
        self.lock = threading.Lock()
        self.recorded = {}
        for root in ROOTS.values():
            path = Path(root) / "calls.jsonl"
            plan = Path(root) / "plan.json"
            if not path.exists():
                continue
            kinds = {c["id"]: c["questions"] for c in json.loads(plan.read_text())["calls"]}
            for line in path.read_text().splitlines():
                r = json.loads(line)
                if r["status"] == "ok":
                    if r["id"] in self.recorded:
                        raise ValueError(f"call id {r['id']} is recorded in more than one root")
                    self.recorded[r["id"]] = parse(r["response"], kinds[r["id"]])
        if live:
            load_env_file()
            self.client = Client.from_env(timeout=60, retries=4, backoff=1.0)

    def get(self, call_id, body, kinds):
        with self.lock:
            if call_id in self.cache:
                return self.cache[call_id]
        if self.live:
            payload, _, _ = self.client.run(requests.MODELS[body["model"]], body)
            value = parse(payload, kinds)
        else:
            value = self.recorded[call_id]
        with self.lock:
            self.cache[call_id] = value
        return value

    def many(self, jobs):
        """[(call id, body, kinds)] answered together (six at a time when live)."""
        if not self.live:
            return [self.get(*j) for j in jobs]
        with ThreadPoolExecutor(max_workers=6) as pool:
            return list(pool.map(lambda j: self.get(*j), jobs))


def _kinds(questions):
    return {k: ("options" if q["type"] == "choice" else q["type"]) for k, q in questions.items()}


def _job(call_id, model, state, questions):
    return (call_id, {"model": model, "state": state, "questions": questions}, _kinds(questions))


# ---------- Act 1: the passport on urns ----------

URN_DRAWS = (1, 3, 5)


def _bookbag_index(prior, q, sample):
    return (battery.PRIORS.index(prior) * len(battery.ACCURACIES) * len(battery.SAMPLES)
            + battery.ACCURACIES.index(q) * len(battery.SAMPLES) + battery.SAMPLES.index(sample))  # fmt: skip


BEAD_STATES = ("", "+", "+-", "++", "++-", "+++")


def act1(model, answers, emit, pace):
    """Unanimous bookbag samples at every prior and hit rate (the ledger's `unanimous` estimator:
    the prior cancels between all-A and all-B samples), then the beads states."""
    emit({"type": "act", "act": 1, "model": model})
    items = battery.bookbag_items()
    weights = {}
    for n in URN_DRAWS:
        per = []
        for q in battery.ACCURACIES:
            for p in battery.PRIORS:
                pair = []
                for r in (n, 0):
                    i = _bookbag_index(p, q, (n, r))
                    jobs = [_job(f"{model}/bookbag/urn/{i}/{ph}", model, *battery.bookbag_text(items[i], "urn", ph))
                            for ph in battery.PHRASINGS]  # fmt: skip
                    got = answers.many(jobs)
                    pair.append(float(np.mean([_z(g["answer"]) for g in got])))
                    lp, llr = items[i]["prior_logodds"], items[i]["llr"]
                    emit({"type": "urn_draw", "n": n, "state": jobs[0][1]["state"],
                          "answer": float(np.mean([g["answer"] for g in got])),
                          "bayes": float(1 / (1 + np.exp(-(lp + llr))))})  # fmt: skip
                    pace(0.25)
                per.append((pair[0] - pair[1]) / 2 / battery.logit(q))
        weights[n] = float(np.mean(per))
        emit({"type": "urn_weight", "n": n, "weight": weights[n], "ratio": weights[n] / weights[1]})
    beads = battery.beads_items()
    decided = {}
    for seq in BEAD_STATES:
        i = next(k for k, it in enumerate(beads) if it["ratio"] == 0.85 and it["sequence"] == seq)
        jobs = [_job(f"{model}/beads/urn/{i}/{ph}", model, *battery.beads_text(beads[i], "urn", ph))
                for ph in battery.PHRASINGS]  # fmt: skip
        got = answers.many(jobs)
        p = float(np.mean([g["decision"]["a"] + g["decision"]["b"] for g in got]))
        lead = abs(seq.count("+") - seq.count("-"))
        decided[seq] = p
        emit({"type": "bead_state", "sequence": seq, "decide": p, "optimal": lead >= 2,
              "state": jobs[0][1]["state"]})  # fmt: skip
        pace()
    emit({"type": "passport", "model": model,
          "compression": weights[5] / weights[1], "single_overweight": weights[1],
          "decide_with_nothing": decided[""], "decide_on_one": decided["+"]})  # fmt: skip


# ---------- Act 2: transfer to central-bank remarks ----------


def act2(model, answers, emit, pace, urn_ratio=None):
    """Unanimous remark sets at every market price (the price cancels between all-rise and
    all-hold sets), then the wait state with nothing heard."""
    emit({"type": "act", "act": 2, "model": model, "urn_ratio": urn_ratio})
    items = far.remarks_items()
    shifts = {}
    for n in (1, 3, 5):
        per = []
        for pi in range(len(far.PRICES)):
            pair = []
            for r in (n, 0):
                i = far.COMPOSITIONS.index((n, r)) * len(far.PRICES) + pi
                jobs = [_job(f"{model}/remarks/far/{i}/{ph}", model, *far.remarks_text(items[i], ph))
                        for ph in far.PHRASINGS]  # fmt: skip
                got = answers.many(jobs)
                pair.append(float(np.mean([_z(g["answer"]) for g in got])))
                emit({"type": "far_set", "n": n, "price": far.PRICES[pi],
                      "remarks": [{"speaker": s, "text": t} for s, _, t in items[i]["remarks"]],
                      "answer": float(np.mean([g["answer"] for g in got]))})  # fmt: skip
                pace(0.4)
            per.append((pair[0] - pair[1]) / 2)
        shifts[n] = float(np.mean(per))
        emit({"type": "far_weight", "n": n, "shift": shifts[n], "ratio": shifts[n] / shifts[1]})
    witems = far.wait_items()
    i = next(k for k, it in enumerate(witems) if it["sequence"] == "")
    jobs = [
        _job(f"{model}/wait/far/{i}/{ph}", model, *far.wait_text(witems[i], ph))
        for ph in far.PHRASINGS
    ]
    got = answers.many(jobs)
    emit(
        {
            "type": "far_wait",
            "decide_with_nothing": float(
                np.mean([g["decision"]["a"] + g["decision"]["b"] for g in got])
            ),
        }
    )


# ---------- Act 3: the preregistered desk ----------

LANES = ("alone", "gated", "recalibrated", "passport", "oracle")
SHOWCASE = {"mild": 3}


def _showcase(labelled, strength, raw):
    """Typical cases for the calibration panel: hawkish remarks with distinct wording, for mild
    ones those the raw reader gets wrong (P(hawkish) below one half), closest to the line first.
    The panel's summary reports the accuracy over all labelled remarks."""
    picked, seen = [], set()
    for name, n in SHOWCASE.items():
        rows = [i for i, (key, sign) in enumerate(labelled) if strength[key] == name and sign > 0
                and (name != "mild" or raw[i] < 0.5)]  # fmt: skip
        rows.sort(key=lambda i: -raw[i])
        for i in rows:
            text = labelled[i][0][1]
            if (
                text not in seen
                and len([j for j in picked if strength[labelled[j][0]] == name]) < n
            ):
                picked.append(i)
                seen.add(text)
    return picked


def act3(model, answers, emit, pace, episodes=60):
    from epistemics.ledger.clef_desk4 import (
        calibrate,
        calibration_map,
        recal_subsets,
        recal_weights,
    )

    preregistered = None
    if Path(PREREGISTERED).exists():
        lanes = json.loads(Path(PREREGISTERED).read_text())["models"][model]["lanes"]
        preregistered = {k: lanes[v]["mean"] for k, v in (("alone", "alone"), ("gated", "gated"),
                         ("recalibrated", "recalibrated_10"), ("passport", "passport_calibrated"),
                         ("oracle", "oracle"))}  # fmt: skip
    emit(
        {
            "type": "act",
            "act": 3,
            "model": model,
            "episodes": episodes,
            "preregistered": preregistered,
        }
    )

    # 1. Calibrate the remark reader on the desk's labelled past remarks.
    emit({"type": "status", "text": "calibrating…"})
    labelled = desk4.record_remarks()
    strength = {
        (r["speaker"], r["text"]): r["strength"]
        for m in desk4.meetings("record")
        for r in m["remarks"]
    }
    jobs = [
        _job(f"{model}/record-classify/{i}", model, *desk.classify_text(*key))
        for i, (key, _) in enumerate(labelled)
    ]
    values = {j[0]: g for j, g in zip(jobs, answers.many(jobs), strict=True)}
    cal = calibration_map(values, model)
    raw_readings = [values[f"{model}/record-classify/{i}"]["answer"] for i in range(len(labelled))]
    for i in _showcase(labelled, strength, raw_readings):
        (speaker, text), sign = labelled[i]
        raw = values[f"{model}/record-classify/{i}"]["answer"]
        emit({"type": "calib_remark", "speaker": speaker, "text": text, "strength": strength[(speaker, text)],
              "hawkish": sign > 0, "raw": raw, "calibrated": calibrate(cal, raw)})  # fmt: skip
        pace(2)
    accuracy = {}
    for name, _ in desk2.STRENGTH:
        rows = [(values[f"{model}/record-classify/{i}"]["answer"], sign)
                for i, (key, sign) in enumerate(labelled) if strength[key] == name]  # fmt: skip
        accuracy[name] = {"raw": float(np.mean([(p > 0.5) == (s > 0) for p, s in rows])),
                          "calibrated": float(np.mean([(calibrate(cal, p) > 0.5) == (s > 0) for p, s in rows]))}  # fmt: skip
    emit({"type": "calibration", "remarks": len(labelled), "accuracy": accuracy})
    pace(3)

    # 2. The generic fix: recalibrate the model's own beliefs on ten of its past forecasts.
    emit({"type": "status", "text": "fitting recalibration…"})
    subsets = recal_subsets()[desk4.PRIMARY_K]
    pool = desk4.meetings("pool")
    card = desk4.scorecard()
    needed = sorted({int(i) for idx in subsets for i in idx})
    jobs = [_job(f"{model}/pool-belief/{pool[i]['meeting']}/{t}", model, desk2.state_text(pool[i], t, card),
                 desk.belief_question()) for i in needed for t in range(desk4.PER_MEETING + 1)]  # fmt: skip
    values.update({j[0]: g for j, g in zip(jobs, answers.many(jobs), strict=True)})
    fits = recal_weights(values, model, subsets)
    emit({"type": "recalibration", "fits": len(fits), "meetings": desk4.PRIMARY_K})

    # 3. Trade the held-out meetings.
    est = desk2.estimated_reliability(card)
    tables = desk._value_tables(
        q=float(np.mean(list(est.values()))), max_speakers=desk4.PER_MEETING
    )
    emit({"type": "scorecard", "records": [{"speaker": desk2.SPEAKERS[j], "matched": m_, "of": n_}
                                           for j, (m_, n_) in sorted(card.items())]})  # fmt: skip
    test = desk4.meetings("test")[:episodes]
    uniq = desk2.unique_remarks(desk4.meetings("test"))
    last = desk4.PER_MEETING
    cum = dict.fromkeys(LANES, 0.0)
    nothing_heard = dict.fromkeys(LANES, 0)
    for n_done, m in enumerate(test, start=1):
        emit({"type": "episode", "episode": m["meeting"], "index": n_done, "price": m["price"]})
        decided, fit_decided, evidence = {}, [None] * len(fits), 0.0
        for t in range(last + 1):
            if t > 0:
                r = m["remarks"][t - 1]
                raw = answers.get(*_job(f"{model}/classify/{uniq[(r['speaker'], r['text'])]}", model,
                                        *desk.classify_text(r["speaker"], r["text"])))["answer"]  # fmt: skip
                p = calibrate(cal, raw)
                evidence += (2 * p - 1) * desk2.logit(est[r["index"]])
                emit({"type": "remark", "t": t, "speaker": r["speaker"], "text": r["text"], "raw": raw,
                      "calibrated": p, "record": est[r["index"]]})  # fmt: skip
            key = f"{m['meeting']}/{t}"
            choice, belief = answers.many([
                _job(f"{model}/choice/{key}", model, desk2.state_text(m, t, card), desk.choice_question()),
                _job(f"{model}/belief/{key}", model, desk2.state_text(m, t, card), desk.belief_question()),
            ])  # fmt: skip
            choice, zb = choice["decision"], _z(belief["answer"])
            alone = {"a": "rise", "b": "hold", "draw": "wait"}[max(choice, key=choice.get)]
            if alone == "wait" and t == last:
                alone = "rise" if choice["a"] >= choice["b"] else "hold"
            passport = desk2.logit(m["price"]) + evidence
            oracle = desk2.oracle_logodds(m, t)
            recal = [float(w @ [1.0, zb, desk2.logit(m["price"])]) for w in fits]
            actions = {"alone": alone, "gated": desk.act(t, zb, tables), "passport": desk.act(t, passport, tables),
                       "oracle": desk.act(t, oracle, tables)}  # fmt: skip
            for lane, action in actions.items():
                if lane not in decided and action != "wait":
                    decided[lane] = (action, t)
            for f, logodds in enumerate(recal):
                if fit_decided[f] is None:
                    action = desk.act(t, logodds, tables)
                    if action != "wait":
                        fit_decided[f] = (action, t)
            done = sum(d is not None for d in fit_decided)
            sig = lambda x: float(1 / (1 + np.exp(-x)))  # noqa: E731
            emit({"type": "step", "t": t,
                  "beliefs": {"alone": sig(zb), "gated": sig(zb), "recalibrated": float(np.mean([sig(x) for x in recal])),
                              "passport": sig(passport), "oracle": sig(oracle)},
                  "decided": {k: list(v) for k, v in decided.items()}, "recal_decided": done, "recal_fits": len(fits)})  # fmt: skip
            pace(0.6)
            if len(decided) == 4 and done == len(fits):
                break

        def payoff(action, heard, m=m):
            right = (action == "rise") == m["rise"]
            return (desk2.WIN if right else -desk2.WIN) - desk2.COST * heard

        pnl = {
            lane: float(payoff(*decided[lane])) for lane in ("alone", "gated", "passport", "oracle")
        }
        pnl["recalibrated"] = float(np.mean([payoff(*d) for d in fit_decided]))
        for lane in ("alone", "gated", "passport", "oracle"):
            nothing_heard[lane] += decided[lane][1] == 0
        for lane in LANES:
            cum[lane] += pnl[lane]
        emit(
            {
                "type": "outcome",
                "rise": m["rise"],
                "pnl": pnl,
                "cumulative": dict(cum),
                "index": n_done,
            }
        )
        pace(1.5)
    emit({"type": "summary", "cumulative": dict(cum), "episodes": len(test),
          "nothing_heard": {k: v / len(test) for k, v in nothing_heard.items() if k != "recalibrated"}})  # fmt: skip


# ---------- Server ----------


class Handler(BaseHTTPRequestHandler):
    answers = {}
    delay = 0.35

    def log_message(self, *args):
        pass

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            body = PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if url.path != "/events":
            self.send_error(404)
            return
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        model = q.get("model", "clef-flash")
        act = q.get("act", "1")
        mode = q.get("mode", "replay")
        if model not in requests.MODELS or act not in ("1", "2", "3") or mode not in self.answers:
            self.send_error(400)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        speed = float(q.get("speed", "1"))

        def emit(event):
            data = json.dumps(event, default=float)
            self.wfile.write(f"data: {data}\n\n".encode())
            self.wfile.flush()

        def pace(k=1):
            time.sleep(self.delay * k / max(speed, 0.1))

        try:
            answers = self.answers[mode]
            if act == "1":
                act1(model, answers, emit, pace)
            elif act == "2":
                act2(
                    model, answers, emit, pace, float(q["urn_ratio"]) if "urn_ratio" in q else None
                )
            else:
                act3(model, answers, emit, pace, int(q.get("episodes", "60")))
            emit({"type": "done"})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as error:  # noqa: BLE001 - report to the page, never the credentials
            try:
                emit({"type": "error", "message": type(error).__name__ + ": " + str(error)[:300]})
            except (BrokenPipeError, ConnectionResetError):
                pass


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m epistemics.clef.demo")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--replay", action="store_true", help="only replay recorded runs")
    args = parser.parse_args(argv)
    Handler.answers = {"replay": Answers(live=False)}
    if not args.replay:
        Handler.answers["live"] = Answers(live=True)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Clef demo on http://127.0.0.1:{args.port} ({', '.join(Handler.answers)})")
    server.serve_forever()


if __name__ == "__main__":
    main()
