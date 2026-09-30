"""Multi-agent battery, Stage 1: recovery studies for the scripted-peer fits
(docs/multi-agent-design.md).

Synthetic respondents with known parameters, drawn over the ranges below, answer the real designs;
the fits are refitted with one, two and three sessions pooled per cell. Gates are the house
standards, fixed before the study: correlation 0.9 and 90% interval coverage 0.8 (whole grid
cells) for primary parameters, correlation 0.85 for secondary ones, among respondents with report
noise up to 0.5. T2 (copying-peer) uses the copying design, ideal observer and uptake fit
unchanged, so the capacity battery's uptake recovery for copying applies to it.
"""

from concurrent.futures import ProcessPoolExecutor

import numpy as np

from epistemics.dispositions import social
from epistemics.dispositions.response import sample_reports
from epistemics.dispositions.validation import GATES, cell_edges, draw
from epistemics.ledger.capacity import SESSIONS, WORKERS, pooled

NOISE = {"bias": (-0.3, 0.3), "report_sd": (0.01, 0.8)}
TASKS = {
    "advice": {
        "design": social.advice_design,
        "prior": {"beta_own": (0.3, 1.3), "beta_rec": (0.0, 1.3), "beta_conf": (-0.3, 0.8)},
        "primary": {"beta_rec": social.ADVICE_REC, "beta_conf": social.ADVICE_CONF},
        "secondary": {"beta_own": social.ADVICE_OWN},
    },
    "conformity": {
        "design": social.conformity_design,
        "prior": {"beta_own": (0.3, 1.3), "eta": (0.0, 1.0), "kappa": (-0.3, 1.0)},
        "primary": {"kappa": social.CONFORM_KAPPA},
        "secondary": {"eta": social.CONFORM_ETA, "beta_own": social.CONFORM_OWN},
    },
    "relay-stated": {
        "design": social.relay_design,
        "prior": {"omega": (0.0, 1.8), "gamma": (0.6, 1.4)},
        "primary": {"omega": social.RELAY_OMEGA},
        "secondary": {},
    },
    "relay-open": {
        "design": social.relay_design,
        "prior": {"fidelity": (0.35, 1.0), "gamma": (0.6, 1.4)},
        "primary": {"fidelity": social.RELAY_FIDELITY},
        "secondary": {},
    },
}
GATES_SOCIAL = {"primary_correlation": 0.9, "secondary_correlation": 0.85, "coverage_90": 0.8}


def latent(task, items, truth):
    if task == "advice":
        return social.advice_answer(items, truth["beta_own"], truth["beta_rec"], truth["beta_conf"])
    if task == "conformity":
        exact, counted, own, conform = social.conformity_terms(items)
        return (
            truth["beta_own"] * own
            + (1 - truth["eta"]) * exact
            + truth["eta"] * counted
            + truth["kappa"] * conform
        )
    if task == "relay-stated":
        fidelity = np.asarray(items["fidelity"], dtype=float) ** truth["omega"]
        return social.relay_answer(items, fidelity, truth["gamma"])
    return social.relay_answer(items, truth["fidelity"], truth["gamma"])


def fitted(task, items, reports):
    if task == "advice":
        return social.fit_advice(items, reports)
    if task == "conformity":
        return social.fit_conformity(items, reports)
    return social.fit_relay(items, reports, stated=task == "relay-stated")


def _case(job):
    task, truth, seed, sessions = job
    rng = np.random.default_rng(seed)
    items = TASKS[task]["design"]()
    means = latent(task, items, truth) + truth["bias"]
    reports = np.concatenate(
        [sample_reports(means, truth["report_sd"], rng) for _ in range(sessions)]
    )
    return {"truth": truth, "fit": fitted(task, pooled(items, sessions), reports)["parameters"]}


def _metrics(task, rows):
    limit = GATES["agent_noise_band"]["report_sd"]
    agent = [r for r in rows if r["truth"]["report_sd"] <= limit]
    spec = TASKS[task]
    result = {"respondents": len(agent), "parameters": {}}
    passed = True
    for role in ("primary", "secondary"):
        for name, grid in spec[role].items():
            truth = np.array([r["truth"][name] for r in agent])
            mean = np.array([r["fit"][name]["mean"] for r in agent])
            lower, upper = cell_edges(grid)
            lo = np.array(
                [lower[np.searchsorted(grid, r["fit"][name]["interval_90"][0])] for r in agent]
            )
            hi = np.array(
                [upper[np.searchsorted(grid, r["fit"][name]["interval_90"][1])] for r in agent]
            )
            row = {
                "role": role,
                "correlation": float(np.corrcoef(truth, mean)[0, 1]),
                "mae": float(np.mean(np.abs(truth - mean))),
                "coverage_90": float(np.mean((lo <= truth) & (truth <= hi))),
            }
            gate = GATES_SOCIAL[f"{role}_correlation"]
            row["passed"] = bool(
                row["correlation"] >= gate and row["coverage_90"] >= GATES_SOCIAL["coverage_90"]
            )
            passed &= row["passed"]
            result["parameters"][name] = row
    result["passed"] = bool(passed)
    return result


def recovery(respondents=100, seed=20261014, sessions=SESSIONS):
    rng = np.random.default_rng(seed)
    result = {}
    with ProcessPoolExecutor(WORKERS) as pool:
        for task, spec in TASKS.items():
            truths = [draw(rng, {**spec["prior"], **NOISE}) for _ in range(respondents)]
            seeds = rng.integers(2**31, size=respondents).tolist()
            by_sessions = {}
            for k in sessions:
                jobs = [(task, t, s, k) for t, s in zip(truths, seeds, strict=True)]
                by_sessions[k] = _metrics(task, list(pool.map(_case, jobs)))
            passing = [k for k, m in by_sessions.items() if m["passed"]]
            result[task] = {
                "sessions": by_sessions,
                "sessions_needed": min(passing) if passing else None,
            }
    return {
        "schema_version": "epistemics.social-recovery.v1",
        "gates": GATES_SOCIAL,
        "tasks": result,
    }


def table(result):
    lines = [
        "| Task | Parameter | Role | 1 session: r, coverage | 2 sessions | 3 sessions |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for task, r in result["tasks"].items():
        names = r["sessions"][next(iter(r["sessions"]))]["parameters"]
        for name, first in names.items():
            cells = [
                f"{r['sessions'][k]['parameters'][name]['correlation']:.2f}, "
                f"{r['sessions'][k]['parameters'][name]['coverage_90']:.2f}"
                for k in r["sessions"]
            ]
            lines.append(f"| {task} | {name} | {first['role']} | " + " | ".join(cells) + " |")
        lines.append(f"| {task} | sessions needed: {r['sessions_needed']} | | | | |")
    return "\n".join(lines)
