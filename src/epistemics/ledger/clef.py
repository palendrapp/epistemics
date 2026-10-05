"""Clef pilot analysis (docs/clef-pilot-design.md, "Analysis").

Every measure reuses the function that computed it for the agent configurations, applied to
Clef's answers (the probability of true for noul questions; the probability-weighted mean for base
rates). Per model:

  Q1  evident dossiers: error against the exact posterior by case type, structure use, false
      structure (dispositions.evident.session); a reliability table and extremity (mean |answer
      log-odds| minus |correct log-odds|: negative means answers sit closer to 0.5 than the
      posterior)
  Q2  hinted dossiers: implied structure priors per description (fit.fit_cues, on answers rounded
      to whole percentages, the resolution its report likelihood assumes), alone and with the
      mechanism stated; the mean absolute log-odds distance of alone from reference answers on
      described cases (the deviation of adapter_eval.hinted_summary; Clef has no session noise)
  Q3  cues-a: the passport's stated-applied gap (finance_transfer._gap). Within state, on joint
      calls: the forecast against the observer's forecast, and the probe against the observer's
      structure posterior, both given the base rate Clef gave in the same call; beside the same
      gaps with the base rates rotated across the module's cases (a case-blind baseline)
  Q4  repeats, alone against joint, question order, paraphrase

Answers are elicited outputs of a trained head, not direct access to the model's beliefs.
"""

import numpy as np

from epistemics.clef import pilot, requests
from epistemics.clef.answers import parse, rate, unwrap
from epistemics.clef.client import ClefError

CLIP = 0.01
BINS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


def _z(p):
    p = np.clip(np.asarray(p, dtype=float), CLIP, 1 - CLIP)
    return np.log(p / (1 - p))


def _mean(values):
    values = [v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def _items(module):
    from epistemics.disposition_tasks.render import items_for

    return items_for(module)


def _subset(items, index):
    return {k: np.asarray(v)[index] for k, v in items.items()}


def load(root):
    document, _ = pilot.load(root)
    for module, value in document["items"].items():
        if requests.items_digest(module) != value:
            raise ClefError(f"The {module} design has changed since the plan was frozen")
    records = pilot.answered(root)
    values, modes, latency, usage = {}, {}, [], {}
    for c in document["calls"]:
        record = records.get(c["id"])
        if record is None:
            continue
        values[c["id"]] = parse(record["response"], c["questions"])
        answers = unwrap(record["response"])["answers"]
        for qid, kind in c["questions"].items():
            if kind == "choice":
                modes[(c["id"], qid)] = rate(answers[qid])[1]
        latency.append(record["elapsed_seconds"])
        for k, v in (unwrap(record["response"]).get("usage") or {}).items():
            if isinstance(v, int | float):
                usage[f"{c['model']}/{k}"] = usage.get(f"{c['model']}/{k}", 0) + v
    return document, values, modes, {"latency": latency, "usage": usage}


def _answers(values, model, part, module, variant, n, qid="answer", tag=""):
    """Answers to one question over a module's cases, in item order (None where missing)."""
    suffix = f"/{tag}" if tag else ""
    out = []
    for i in range(n):
        v = values.get(f"{model}/{part}/{module}/{variant}/{i}{suffix}")
        out.append(None if v is None else v.get(qid, v.get("rate")))
    return out


def q1(values, model):
    from epistemics.dispositions import evident

    out, pooled = {}, []
    for module in requests.EVIDENT:
        items = _items(module)
        answers = _answers(values, model, "q1", module, "alone", len(items["kind"]))
        if None in answers:
            out[module] = {"complete": False}
            continue
        s = evident.session(module, items, answers)
        out[module] = {"complete": True, "error": s["error"], "error_by_type": s["error_by_type"],
                       "structure_use": s["structure_use"],
                       "false_structure": s["false_structure"]}  # fmt: skip
        pooled += [(c["correct"], c["answer"]) for c in s["cases"]]
    if not pooled:
        return out
    correct, answer = (np.array(x) for x in zip(*pooled, strict=True))
    table = []
    for lo, hi in zip(BINS[:-1], BINS[1:], strict=True):
        mask = (correct >= lo) & ((correct < hi) if hi < 1 else (correct <= hi))
        if mask.any():
            table.append({"correct_from": lo, "correct_to": hi, "cases": int(mask.sum()),
                          "mean_correct": float(correct[mask].mean()),
                          "mean_answer": float(answer[mask].mean())})  # fmt: skip
    out["reliability"] = table
    out["extremity"] = float(np.mean(np.abs(_z(answer)) - np.abs(_z(correct))))
    out["cases"] = len(pooled)
    return out


def _fit(module, answers):
    """The agents' cue fit. Its report likelihood is censored at whole percentages (the agents'
    resolution), so Clef's answers enter it rounded to whole percentages; every other measure uses
    them unrounded."""
    from epistemics.disposition_tasks.analysis import CUE_MODELS
    from epistemics.dispositions import fit

    reports = np.round(np.asarray(answers, dtype=float) * 100) / 100
    result = fit.fit_cues(CUE_MODELS[module], _items(module), reports)
    return [{"slot": s["slot"], "implied": s["implied"], "stated": s["stated"]}
            for s in result["slots"]]  # fmt: skip


def q2(values, model):
    out = {}
    for module in requests.HINTED:
        items = _items(module)
        n = len(items["kind"])
        arms = {v: _answers(values, model, "q2", module, v, n) for v in requests.HINTED_VARIANTS}
        if any(None in a for a in arms.values()):
            out[module] = {"complete": False}
            continue
        implied = {v: [s["implied"]["mean"] for s in _fit(module, a)] for v, a in arms.items()}
        described = items["slot"] >= 0
        distance = np.abs(_z(arms["alone"]) - _z(arms["reference"]))[described]
        out[module] = {
            "complete": True,
            "implied": implied,
            "deviation": float(distance.mean()),
            "mapping_distance": float(
                np.mean(np.abs(np.subtract(implied["alone"], implied["reference"])))
            ),
            "mean_answer": {v: float(np.mean(a)) for v, a in arms.items()},
        }
    return out


def _within(module, cases, rates, probes, forecasts):
    from epistemics.dispositions import observers

    structure = requests.STRUCTURE[module]
    items = _subset(_items(module), cases)
    observe = observers.corroboration if structure == "corroboration" else observers.disclosure
    r = np.asarray(rates, dtype=float)
    forecast_gap = np.abs(_z(forecasts) - _z(1 / (1 + np.exp(-observe(items, r, 1.0)))))
    probe_gap = np.abs(_z(probes) - _z(observers.structure_posterior(structure, items, r)))
    return forecast_gap, probe_gap


def q3(values, model):
    from epistemics.ledger.finance_transfer import LEVELS, _gap

    across, within = {}, {}
    for module in requests.CUES:
        n = len(_items(module)["kind"])
        answers = _answers(values, model, "q3", module, requests.CUES_VARIANT, n)
        if None in answers:
            across[module] = {"complete": False}
            continue
        slots = _fit(module, answers)
        across[module] = {
            "complete": True,
            "gap": _gap({"slot_fits": slots}),
            "levels": {s["slot"]: {"stated": float(np.mean(s["stated"])),
                                   "implied": s["implied"]["mean"]}
                       for s in slots if s["slot"] in LEVELS and s["stated"]},
        }  # fmt: skip
    for module in requests.HINTED + requests.CUES:
        variant = "alone" if module in requests.HINTED else requests.CUES_VARIANT
        cases = requests.described_forecasts(module)
        rows = [values.get(f"{model}/joint/{module}/{variant}/{i}/forward") for i in cases]
        if None in rows:
            within[module] = {"complete": False}
            continue
        rates = [r["rate"] for r in rows]
        probes = [r["probe"] for r in rows]
        forecasts = [r["forecast"] for r in rows]
        own = _within(module, cases, rates, probes, forecasts)
        rotated = [_within(module, cases, np.roll(rates, s), probes, forecasts)
                   for s in range(1, len(cases))]  # fmt: skip
        within[module] = {
            "complete": True,
            "cases": len(cases),
            "mechanism_named_by_questions": module in requests.HINTED,
            "forecast_gap": float(own[0].mean()),
            "forecast_gap_rotated": float(np.mean([g[0].mean() for g in rotated])),
            "probe_gap": float(own[1].mean()),
            "probe_gap_rotated": float(np.mean([g[1].mean() for g in rotated])),
            "rate_mean": float(np.mean(rates)),
            "rate_sd": float(np.std(rates)),
        }
    return {"across": across, "within": within}


def _logit_difference(a, b):
    pairs = [(x, y) for x, y in zip(a, b, strict=True) if x is not None and y is not None]
    if not pairs:
        return None
    x, y = (np.array(v) for v in zip(*pairs, strict=True))
    return float(np.mean(np.abs(_z(x) - _z(y))))


def q4(values, model):
    out = {}
    spreads = []
    for module in requests.EVIDENT:
        for i in requests.CHECK_ITEMS:
            calls = [values.get(f"{model}/q1/{module}/alone/{i}")] + [
                values.get(f"{model}/repeat/{module}/alone/{i}/{r}")
                for r in range(1, requests.REPEATS + 1)
            ]
            got = [c["answer"] for c in calls if c is not None]
            if len(got) == len(calls):
                spreads.append(max(got) - min(got))
    out["repeat"] = {"cases": len(spreads), "max_spread": max(spreads) if spreads else None,
                     "mean_spread": _mean(spreads),
                     "deterministic": bool(spreads) and max(spreads) < 1e-3}  # fmt: skip
    joint_vs_single, order = {}, {}
    for module in requests.HINTED + requests.CUES:
        variant = "alone" if module in requests.HINTED else requests.CUES_VARIANT
        part = "q2" if module in requests.HINTED else "q3"
        cases = requests.described_forecasts(module)
        single = [values.get(f"{model}/{part}/{module}/{variant}/{i}") for i in cases]
        forward = [values.get(f"{model}/joint/{module}/{variant}/{i}/forward") for i in cases]
        reverse = [values.get(f"{model}/joint/{module}/{variant}/{i}/reverse") for i in cases]
        joint_vs_single[module] = _logit_difference(
            [s and s["answer"] for s in single], [f and f["forecast"] for f in forward]
        )
        order[module] = {
            q: _logit_difference([f and f[q] for f in forward], [r and r[q] for r in reverse])
            for q in ("probe", "forecast")
        }
        rate_pairs = [
            (f["rate"], r["rate"]) for f, r in zip(forward, reverse, strict=True) if f and r
        ]
        order[module]["rate_abs"] = (
            float(np.mean([abs(a - b) for a, b in rate_pairs])) if rate_pairs else None
        )
    out["alone_vs_joint"] = joint_vs_single
    out["order"] = order
    q1_answers, paraphrased = [], []
    for module in requests.EVIDENT:
        for i in requests.CHECK_ITEMS:
            a = values.get(f"{model}/q1/{module}/alone/{i}")
            p = values.get(f"{model}/paraphrase/{module}/alone/{i}")
            q1_answers.append(a and a["answer"])
            paraphrased.append(p and p["answer"])
    out["paraphrase"] = _logit_difference(q1_answers, paraphrased)
    return out


def agents(evident_roots=(), hinted_roots=(), cues_roots=()):
    """The agent configurations' values on the same cases, from their collected roots."""
    from epistemics.ledger import adapter_eval

    out = {}
    if evident_roots:
        for c, e in adapter_eval.summary(evident_roots)["configurations"].items():
            alone = e["arms"].get("alone")
            if alone:
                out.setdefault(c, {})["q1"] = {k: alone[k] for k in (
                    "error", "error_present", "error_absent", "error_control", "structure_use",
                    "false_structure", "sessions")}  # fmt: skip
    if hinted_roots:
        for c, e in adapter_eval.hinted_summary(hinted_roots)["configurations"].items():
            arms = e["arms"]
            if "alone" in arms:
                out.setdefault(c, {})["q2"] = {
                    "deviation": arms["alone"]["deviation"],
                    "mapping_distance": arms["alone"]["mapping_distance"],
                    "reference_noise_floor": arms.get("reference", {}).get("deviation"),
                    "reference_mapping": e["reference_mapping"],
                    "sessions": arms["alone"]["sessions"],
                }
    if cues_roots:
        from epistemics.ledger import dispositions
        from epistemics.ledger.finance_transfer import _gap

        gaps = {}
        for root in cues_roots:
            for r in dispositions.extract(root):
                if (r.get("verified") and r.get("module") in requests.CUES
                        and r.get("variant") == requests.CUES_VARIANT):  # fmt: skip
                    g = _gap(r)
                    if g is not None:
                        gaps.setdefault(r["configuration"], []).append(g)
        for c, v in gaps.items():
            out.setdefault(c, {})["q3"] = {"gap": float(np.mean(v)), "sessions": len(v)}
    return out


def summary(root, evident_roots=(), hinted_roots=(), cues_roots=()):
    document, values, _, meta = load(root)
    models = {}
    for model in document["models"]:
        planned = [c for c in document["calls"] if c["model"] == model]
        models[model] = {
            "calls": {"planned": len(planned),
                      "answered": sum(c["id"] in values for c in planned)},
            "q1": q1(values, model),
            "q2": q2(values, model),
            "q3": q3(values, model),
            "q4": q4(values, model),
        }  # fmt: skip
    latency = meta["latency"]
    return {
        "schema_version": "epistemics.clef-pilot.v1",
        "version": document["version"],
        "plan_digest": document["plan_digest"],
        "models": models,
        "agents": agents(evident_roots, hinted_roots, cues_roots),
        "latency_median_seconds": float(np.median(latency)) if latency else None,
        "usage": meta["usage"],
        "scope": (
            "Clef's answers to the cases the agent configurations answered: the probability of "
            "true for noul questions, the probability-weighted mean for base rates. Elicited "
            "outputs of a trained head, not direct access to beliefs. Within-state gaps are "
            "absolute log-odds distances from the Bayesian observer given the base rate Clef gave "
            "in the same call; 'rotated' uses another case's base rate (mean over rotations). On "
            "hinted cases the joint questions themselves name the mechanism."
        ),
    }
