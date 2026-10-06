"""Live demo of the Clef battery and desk (docs/clef-desk-demo.md, "Live demo").

uv run python -m epistemics.clef.demo [--port 8765] [--replay]

Serves a page on 127.0.0.1 and streams each act as server-sent events while Clef answers:

  act 1  the passport: on urns, how much one draw is worth against several (sample-size neglect)
         and whether it decides before the evidence warrants (jumping to conclusions)
  act 2  transfer: the same measures on natural-language central-bank remarks, against the
         curve the urns predict
  act 3  mitigation: simulated desk episodes traded by three lanes (the model alone, its belief
         gated at the optimal threshold, and the passport lane: classify each remark, add in
         code, wait for the threshold), with the outcome and a running P&L

Live mode calls Workers AI with credentials from the environment or .env (never sent to the
page). Replay mode reads the recorded runs (output/clef-battery-*, clef-far-*, clef-desk-*);
Clef is deterministic, so a live run reproduces them.
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

from epistemics.clef import battery, desk, far, requests
from epistemics.clef.answers import parse
from epistemics.clef.client import Client, load_env_file

ROOTS = {
    "battery": "output/clef-battery-20261006",
    "far": "output/clef-far-20261006",
    "desk": "output/clef-desk-20261006",
}
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


# ---------- Act 3: the desk ----------


def act3(model, answers, emit, pace, episodes=60):
    emit({"type": "act", "act": 3, "model": model, "episodes": episodes})
    eps = desk.episodes()[:episodes]
    uniq = desk.unique_remarks(desk.episodes())
    cum = {lane: 0.0 for lane in ("alone", "gated", "passport", "bayes")}
    for ep in eps:
        emit({"type": "episode", "episode": ep["episode"], "price": ep["price"]})
        decided, hawks = {}, []
        for t in range(desk.MAX_SPEAKERS + 1):
            if t > 0:
                r = ep["remarks"][t - 1]
                cid = f"{model}/classify/{uniq[(r['speaker'], r['text'])]}"
                hawk = answers.get(*_job(cid, model, *desk.classify_text(r["speaker"], r["text"])))[
                    "answer"
                ]
                hawks.append(hawk)
                emit(
                    {
                        "type": "remark",
                        "t": t,
                        "speaker": r["speaker"],
                        "text": r["text"],
                        "hawk": hawk,
                    }
                )
            key = f"{ep['episode']}/{t}"
            choice, belief = answers.many([
                _job(f"{model}/choice/{key}", model, desk.state_text(ep, t), desk.choice_question()),
                _job(f"{model}/belief/{key}", model, desk.state_text(ep, t), desk.belief_question()),
            ])  # fmt: skip
            choice, belief = choice["decision"], belief["answer"]
            lanes = {
                "alone": {"a": "rise", "b": "hold", "draw": "wait"}[max(choice, key=choice.get)],
                "gated": desk.act(t, _z(belief)),
                "passport": desk.act(
                    t, desk.logit(ep["price"]) + desk.LQ * sum(2 * h - 1 for h in hawks)
                ),
                "bayes": desk.act(t, desk.bayes_logodds(ep, t)),
            }
            if t == desk.MAX_SPEAKERS and lanes["alone"] == "wait":
                lanes["alone"] = "rise" if choice["a"] >= choice["b"] else "hold"
            beliefs = {"alone": belief, "gated": belief,
                       "passport": 1 / (1 + np.exp(-(desk.logit(ep["price"]) + desk.LQ * sum(2 * h - 1 for h in hawks)))),
                       "bayes": 1 / (1 + np.exp(-desk.bayes_logodds(ep, t)))}  # fmt: skip
            for lane, action in lanes.items():
                if lane not in decided and action != "wait":
                    decided[lane] = (action, t)
            emit({"type": "step", "t": t, "choice": choice,
                  "beliefs": {k: float(v) for k, v in beliefs.items()},
                  "decided": {k: list(v) for k, v in decided.items()}})  # fmt: skip
            pace(0.6)
            if len(decided) == 4:
                break
        pnl = {}
        for lane, (action, t) in decided.items():
            right = (action == "rise") == ep["rise"]
            pnl[lane] = (desk.WIN if right else -desk.WIN) - desk.COST * t
            cum[lane] += pnl[lane]
        emit({"type": "outcome", "rise": ep["rise"], "pnl": pnl, "cumulative": dict(cum)})
        pace(1.5)
    emit({"type": "summary", "cumulative": dict(cum), "episodes": len(eps)})


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
