"""Central-bank statements as sequential evidence: stage A, stage B, the datability probe and the
validation before collection (docs/statement-updating-design.md).

A configuration's three sessions of a form (the Latin square) are pooled: the model is fitted to
all its answers, and the three laws (order, path, content) are computed model-free. A law test is
calibrated by simulation: a Bayesian combiner with the configuration's own fitted readings, prior
use and report noise (eta 0, beta 1, alpha 1) answers the same three sessions many times; a
configuration departs from a law when its statistic exceeds the simulated distribution
(permutation-style p) and a practical threshold.

  Stage A (form a): H1 readings differ (for at least one slot, at least three configurations
  depart from the configurations' median by DELTA with their 90% interval excluding it); H2 at
  least one configuration departs from the order or the path law (Holm across configurations,
  per law); H3 whether any departs from the content law.
  Stage B: consistency ICC across forms a and b for each parameter and law statistic, permutation
  p, Holm across them.
"""

from concurrent.futures import ProcessPoolExecutor

import numpy as np

from epistemics.dispositions import statements as st
from epistemics.ledger import screen as screen_ledger

DELTA = 0.25  # 1/8 of the readings' plausible range (0 to 2 log-odds per change)
PRACTICAL = {"order": 0.2, "path": 0.2, "content": 0.1}  # mean absolute log-odds
LAWS = ("order", "path", "content")
GPT56 = ("luna", "terra")


def sessions(roots):
    from epistemics.ledger import dispositions

    out = []
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified"):
                continue
            if "statement" in record:
                s = record["statement"]
                out.append(
                    {
                        "configuration": record["configuration"],
                        "module": record["module"],
                        "form": s["form"],
                        "rotation": s["rotation"],
                        "sequences": s["sequences"],
                        "anchors_ok": s["anchors_ok"],
                        "stylistic_steps": s["stylistic_steps"],
                    }
                )
            elif "statement_probe" in record:
                p = record["statement_probe"]
                out.append(
                    {
                        "configuration": record["configuration"],
                        "module": record["module"],
                        "form": p["form"],
                        "probe": p,
                    }
                )
    return out


def by_configuration(rows, form):
    out = {}
    for r in rows:
        if r["form"] != form or "sequences" not in r:
            continue
        c = out.setdefault(r["configuration"], {"records": [], "rotations": [], "anchors_ok": True})
        c["records"] += r["sequences"]
        c["rotations"].append(r["rotation"])
        c["anchors_ok"] = c["anchors_ok"] and r["anchors_ok"]
    return out


def simulate(form, truth, rng, rotations=st.ROTATIONS):
    records = []
    for r in rotations:
        items = st.design(form, r)
        records += st.sequences(items, st.respond(items, truth, rng))
    return records


def law_test(records, fitted, form, rotations, sims, rng):
    """Each law's statistic against Bayesian combiners with the configuration's fitted readings,
    prior use and noise, answering the same sessions."""
    observed = st.laws(records)
    null = st.truth_from_fit(fitted, bayesian=True)
    draws = {law: [] for law in (*LAWS, "recency")}
    for _ in range(sims):
        stats = st.laws(simulate(form, null, rng, rotations))
        for law in draws:
            if stats[law] is not None:
                draws[law].append(abs(stats[law]) if law == "recency" else stats[law])
    out = {}
    if observed["recency"] is not None and draws["recency"]:
        sample = np.array(draws["recency"])
        value = abs(observed["recency"])
        out["recency"] = {
            "value": observed["recency"],
            "p": float((1 + np.sum(sample >= value - 1e-12)) / (1 + len(sample))),
        }
    for law in LAWS:
        value = observed[law]
        if value is None or not draws[law]:
            out[law] = {"value": value, "p": None, "departs": False}
            continue
        sample = np.array(draws[law])
        p = float((1 + np.sum(sample >= value - 1e-12)) / (1 + len(sample)))
        out[law] = {
            "value": value,
            "null_95": float(np.percentile(sample, 95)),
            "p": p,
            "departs": bool(p < 0.05 and value >= PRACTICAL[law]),
        }
    return observed, out


def analyse(args):
    configuration, records, form, rotations, sims, seed = args
    fitted = st.fit(records)
    observed, tests = law_test(records, fitted, form, rotations, sims, np.random.default_rng(seed))
    return configuration, {"fit": fitted, "laws": observed, "tests": tests}


def _analyse_all(configs, form, sims, seed):
    seeds = np.random.SeedSequence(seed).spawn(len(configs))
    jobs = [
        (c, v["records"], form, tuple(sorted(v["rotations"])), sims, s)
        for (c, v), s in zip(sorted(configs.items()), seeds, strict=True)
    ]
    with ProcessPoolExecutor(4) as pool:
        return dict(pool.map(analyse, jobs))


def readings_differ(results):
    """H1 per slot: configurations departing from the configurations' median by DELTA, with the
    90% interval excluding the median."""
    out = {}
    for slot in st.SLOTS:
        key = f"w_{slot}"
        means = {c: r["fit"][key]["mean"] for c, r in results.items()}
        median = float(np.median(list(means.values())))
        departing = [
            c
            for c, r in results.items()
            if abs(means[c] - median) >= DELTA
            and not (r["fit"][key]["interval_90"][0] <= median <= r["fit"][key]["interval_90"][1])
        ]
        out[slot] = {"median": median, "departing": departing, "passes": len(departing) >= 3}
    return out


def stage_a(roots, form="a", sims=1000, seed=20261115):
    configs = by_configuration(sessions(roots), form)
    incomplete = sorted(c for c, v in configs.items() if sorted(v["rotations"]) != [1, 2, 3])
    results = _analyse_all(configs, form, sims, seed)
    for c in results:
        results[c]["anchors_ok"] = configs[c]["anchors_ok"]
        results[c]["rotations"] = sorted(configs[c]["rotations"])
    h1 = readings_differ(results)
    tests = {}
    for law in LAWS:
        ps = {
            c: r["tests"][law]["p"] for c, r in results.items() if r["tests"][law]["p"] is not None
        }
        holm = screen_ledger.holm(ps) if ps else {}
        departing = [
            c
            for c in holm
            if holm[c] < 0.05 and results[c]["tests"][law]["value"] >= PRACTICAL[law]
        ]
        tests[law] = {"p_holm": holm, "departing": sorted(departing)}
    return {
        "schema_version": "epistemics.statements-stage-a.v1",
        "form": form,
        "configurations": results,
        "incomplete": incomplete,
        "H1_readings_differ": {
            "slots": h1,
            "holds": any(v["passes"] for v in h1.values()),
        },
        "H2_order_or_path": {
            "order": tests["order"],
            "path": tests["path"],
            "holds": bool(tests["order"]["departing"] or tests["path"]["departing"]),
        },
        "H3_content": tests["content"],
    }


STAGE_B_PARAMETERS = (*(f"w_{s}" for s in st.SLOTS), "gamma", "eta", "beta", "alpha")


def stage_b(roots, sims=500, seed=20261116):
    rows = sessions(roots)
    per_form = {}
    for form in st.FORMS:
        configs = by_configuration(rows, form)
        per_form[form] = _analyse_all(configs, form, sims, seed + st.FORMS.index(form))
    paired = sorted(set(per_form["a"]) & set(per_form["b"]))
    rng = np.random.default_rng(seed)
    out, ps = {}, {}
    if len(paired) >= 3:
        for name in STAGE_B_PARAMETERS + LAWS:

            def value(c, form, name=name):
                r = per_form[form][c]
                return r["laws"][name] if name in LAWS else r["fit"][name]["mean"]

            matrix = [[value(c, "a"), value(c, "b")] for c in paired]
            if any(v is None for row in matrix for v in row):
                continue
            icc, p = screen_ledger.icc_test(matrix, rng)
            out[name] = {"values": dict(zip(paired, matrix, strict=True)), "icc": icc, "p": p}
            ps[name] = p
    for name, p_holm in screen_ledger.holm(ps).items():
        out[name]["p_holm"] = p_holm
        out[name]["passed"] = out[name]["icc"] >= 0.5 and p_holm < 0.05
    return {
        "schema_version": "epistemics.statements-stage-b.v1",
        "configurations": paired,
        "measures": out,
        "passed": [k for k, v in out.items() if v.get("passed")],
    }


def probe(roots):
    """The datability probe: statements any configuration places in one period above the limit."""
    rows = [r for r in sessions(roots) if "probe" in r]
    flagged = {}
    for r in rows:
        for s in r["probe"]["statements"]:
            if s["flagged"]:
                flagged.setdefault(f"{r['form']}:{s['sid']}", []).append(r["configuration"])
    return {
        "schema_version": "epistemics.statements-probe.v1",
        "sessions": [
            {"configuration": r["configuration"], "form": r["form"], **r["probe"]} for r in rows
        ],
        "flagged": flagged,
        "limit": st.PROBE_LIMIT,
    }


# Validation before collection.
def draw_truth(rng):
    return {
        "w": {s: float(rng.uniform(0.2, 1.5)) for s in st.SLOTS},
        "tilt": float(rng.uniform(-0.3, 0.3)),
        "c": float(rng.uniform(-0.3, 0.3)),
        "gamma": float(rng.uniform(0.3, 1.2)),
        "eta": float(rng.uniform(0.0, 1.0)),
        "beta": float(rng.uniform(0.5, 1.5)),
        "alpha": float(rng.uniform(0.5, 1.0)),
        "tau": float(rng.uniform(0.1, 0.5)),
        "dilution": float(rng.uniform(0.0, 0.3)),
    }


SCENARIOS = {
    "bayesian": {"eta": 0.0, "beta": 1.0, "alpha": 1.0, "dilution": 0.0},
    "fading": {"eta": 0.0, "beta": 1.0, "alpha": 0.6, "dilution": 0.0},
    "averaging": {"eta": 0.6, "beta": 1.0, "alpha": 1.0, "dilution": 0.0},
    "over_reacting": {"eta": 0.0, "beta": 1.6, "alpha": 1.0, "dilution": 0.0},
    "diluting": {"eta": 0.0, "beta": 1.0, "alpha": 1.0, "dilution": 0.3},
}


def _recovery_chunk(args):
    n, seed = args
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        truth = draw_truth(rng)
        fitted = st.fit(simulate("a", truth, rng))
        rows.append((truth, fitted))
    return rows


def _calibration_chunk(args):
    scenario, n, sims, seed = args
    rng = np.random.default_rng(seed)
    hits = {law: 0 for law in LAWS}
    for _ in range(n):
        truth = {**draw_truth(rng), **SCENARIOS[scenario]}
        truth["tau"] = float(rng.uniform(0.05, 0.5))
        records = simulate("a", truth, rng)
        fitted = st.fit(records)
        _, tests = law_test(records, fitted, "a", st.ROTATIONS, sims, rng)
        for law in LAWS:
            hits[law] += tests[law]["departs"]
    return scenario, hits, n


def _truth_value(truth, name):
    return truth["w"][name[2:]] if name.startswith("w_") else truth[name]


def validation(agents=300, calibration=200, sims=200, seed=20261117, workers=4):
    """Recovery of the readings, prior use, averaging, step gain and retention from one
    configuration's three sessions (form a), and the law tests' false departures for Bayesian
    combiners (at most 10%) and their power against fading, averaging, over-reaction and
    dilution."""
    seeds = np.random.SeedSequence(seed).spawn(workers + len(SCENARIOS) * workers)
    chunk = agents // workers
    with ProcessPoolExecutor(workers) as pool:
        rows = [
            r
            for part in pool.map(_recovery_chunk, [(chunk, s) for s in seeds[:workers]])
            for r in part
        ]
        jobs = [
            (scenario, calibration // workers, sims, s)
            for k, scenario in enumerate(SCENARIOS)
            for s in seeds[workers + k * workers : workers + (k + 1) * workers]
        ]
        totals = {}
        for scenario, hits, n in pool.map(_calibration_chunk, jobs):
            t = totals.setdefault(scenario, {"n": 0, **{law: 0 for law in LAWS}})
            t["n"] += n
            for law in LAWS:
                t[law] += hits[law]
    recovery = {}
    names = (
        *(f"w_{s}" for s in st.SLOTS),
        *("gamma", "eta", "beta", "alpha", "dilution", "tau", "c", "tilt"),
    )
    for name in names:
        true = np.array([_truth_value(t, name) for t, _ in rows])
        est = np.array([f[name]["mean"] for _, f in rows])
        inside = np.mean(
            [
                f[name]["interval_90"][0] - 1e-9
                <= _truth_value(t, name)
                <= f[name]["interval_90"][1] + 1e-9
                for t, f in rows
            ]
        )
        recovery[name] = {"r": float(np.corrcoef(true, est)[0, 1]), "coverage_90": float(inside)}
    # Confusion among the combining parameters and the readings' scale.
    scale_true = np.array([np.mean(list(t["w"].values())) for t, _ in rows])
    combining = ("eta", "beta", "alpha", "dilution")
    confusion = {}
    for a in combining:
        est = np.array([f[a]["mean"] for _, f in rows])
        others = {b: np.array([t[b] for t, _ in rows]) for b in combining if b != a}
        others["w_scale"] = scale_true
        others["gamma"] = np.array([t["gamma"] for t, _ in rows])
        confusion[a] = {b: float(np.corrcoef(est, v)[0, 1]) for b, v in others.items()}

    def recovers(names):
        return all(recovery[n]["r"] >= 0.8 and recovery[n]["coverage_90"] >= 0.8 for n in names)

    rates = {
        scenario: {law: t[law] / t["n"] for law in LAWS} | {"n": t["n"]}
        for scenario, t in totals.items()
    }
    passed = {
        # The readings and prior use carry stage A's hypotheses; the combining parameters are
        # reported separately (exploratory in stage A, tested for reliability in stage B).
        "readings_and_prior": recovers((*(f"w_{s}" for s in st.SLOTS), "gamma")),
        "combining": recovers(("eta", "beta", "alpha")),
        "confusion": all(abs(v) <= 0.3 for row in confusion.values() for v in row.values()),
        "false_departures": all(rates["bayesian"][law] <= 0.10 for law in LAWS),
    }
    return {
        "schema_version": "epistemics.statements-validation.v1",
        "agents": len(rows),
        "calibration_agents": calibration,
        "null_simulations": sims,
        "recovery": recovery,
        "confusion": confusion,
        "law_rates": rates,
        "passed": passed,
    }
