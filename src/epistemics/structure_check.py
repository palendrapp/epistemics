"""Structure checks: how much prompting a configuration needs before it considers a named hidden
structure, tested one structure at a time.

Why one at a time: the hierarchical second layer found that noticing one hidden structure does not
predict noticing another, and showing that it does would take 10-15 structures per configuration
(docs/structure-inclusion-model.md). A consumer instead names the structures that matter; each is
collected on the salience ladder and fitted on its own with the per-structure second layer
(`inclusion_joint`: one family, fidelity mixture), and its inclusion curve becomes a prompting
recommendation (docs/structure-checks.md).

uv run python -m epistemics.structure_check validate --output <file>
uv run python -m epistemics.structure_check check --output <file> [--configuration sol] [--structure copying]
uv run python -m epistemics.structure_check collect <directory> --configuration sol --structure copying --validation <file> --validation <file>
"""

import argparse
import asyncio
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from epistemics.ledger import inclusion
from epistemics.ledger import inclusion_joint as joint

VERSION = "structure-check/0.2.0"
# The structures that can be checked: a hidden structure in one task format, with the module and
# variant that realise each rung of the salience ladder, and the words a consumer would use.
CATALOGUE = {
    "relay": {
        "name": "sources repeating another source",
        "phrase": "that some sources repeat another source's report instead of checking",
        "setting": "company-demand forecasts from document dossiers",
        "format": "dossier",
        "ladder": {
            0: ("corroboration-unprompted", "dossier-a"),
            1: ("corroboration-unprompted", "named-a"),
            2: ("corroboration-asked", "named-a"),
            3: ("corroboration-probed", "named-a"),
        },
    },
    "disclosure": {
        "name": "selective silence",
        "phrase": "that some companies stay silent when their numbers are bad",
        "setting": "company-demand forecasts from document dossiers",
        "format": "dossier",
        # No probed disclosure dossier exists; the full mechanism statement stands at rung 3.
        "ladder": {
            0: ("disclosure-unprompted", "dossier-a"),
            1: ("disclosure-unprompted", "named-a"),
            2: ("disclosure-asked", "named-a"),
            3: ("disclosure-dossier", "dossier-a"),
        },
    },
    "copying": {
        "name": "copied readings",
        "phrase": "that some sensors copy another sensor's reading instead of taking their own",
        "setting": "abstract urn tasks",
        "format": "urn2",
        "ladder": {
            0: ("copying-urn", "urn2-plain"),
            1: ("copying-urn", "urn2-named"),
            2: ("copying-urn-asked", "urn2-named"),
            3: ("copying-urn-probed", "urn2-named"),
        },
    },
    "selection": {
        "name": "selective reporting",
        "phrase": "that some reporters report only the results that favour one side",
        "setting": "abstract urn tasks",
        "format": "urn2",
        "ladder": {
            0: ("selection-urn", "urn2-plain"),
            1: ("selection-urn", "urn2-named"),
            2: ("selection-urn-asked", "urn2-named"),
            3: ("selection-urn-probed", "urn2-named"),
        },
    },
    "mismatch": {
        "name": "misfiled readings",
        "phrase": "that some readings on file come from a different item than the one they are "
        "filed under",
        "setting": "abstract urn tasks",
        # Reworded in tasks 0.12: the urn2 accuracy clause was read as covering misfiling
        # (docs/disposition-abstract2-2026-09-29.md). Plain sessions are unchanged.
        "format": "urn3",
        "ladder": {
            0: ("mismatch-urn", "urn2-plain"),
            1: ("mismatch-urn", "urn3-named"),
            2: ("mismatch-urn-asked", "urn3-named"),
            3: ("mismatch-urn-probed", "urn3-named"),
        },
        # Beyond the ladder: the structure named and its rate stated for each record (tasks 0.13).
        "rated": {"module": "mismatch-urn", "variant": "urn3-rated", "model": "mismatch"},
    },
}
# Battery v2's second surfaces (tasks 0.14), on the same ladder.
CATALOGUE |= {
    "echo": {
        "name": "repeated reports",
        "phrase": "that some observers repeat what another observer told them instead of looking",
        "setting": "abstract urn tasks",
        "format": "urn2b",
        "ladder": {
            0: ("echo-urn", "urn2-plain"),
            1: ("echo-urn", "urn2-named"),
            2: ("echo-urn-asked", "urn2-named"),
            3: ("echo-urn-probed", "urn2-named"),
        },
    },
    "hub": {
        "name": "dropped readings",
        "phrase": "that some hubs forward only the readings that favour one side",
        "setting": "abstract urn tasks",
        "format": "urn2b",
        "ladder": {
            0: ("hub-urn", "urn2-plain"),
            1: ("hub-urn", "urn2-named"),
            2: ("hub-urn-asked", "urn2-named"),
            3: ("hub-urn-probed", "urn2-named"),
        },
    },
    "stale": {
        "name": "stale readings",
        "phrase": "that some readings on file date from before the item last changed",
        "setting": "abstract urn tasks",
        "format": "urn2b",
        "ladder": {
            0: ("stale-urn", "urn2-plain"),
            1: ("stale-urn", "urn2-named"),
            2: ("stale-urn-asked", "urn2-named"),
            3: ("stale-urn-probed", "urn2-named"),
        },
    },
}
# What the consumer does to reach each rung.
ACTIONS = {
    0: ("Nothing needed", "Nothing extra: it considers {name} unprompted."),
    1: ("Mention it", "Say {phrase}."),
    2: ("Mention it and ask how common it is", "Say {phrase}, and ask how common it is."),
    3: (
        "Mention it, ask how common it is and ask about each case",
        "Say {phrase}, ask how common it is, and ask about it for each case.",
    ),
    None: (
        "Not reliable",
        "Even with every prompt tested, it does not reliably take {name} into account.",
    ),
    "rate": ("State how common it is", "Say {phrase}, and state how common it is."),
}
# Inclusion is read for a case in which nothing hints at the structure (the uninformative
# description). A rung is reliable when the 90% interval of inclusion there starts at 0.8 or above.
RELIABLE = 0.8
CHAINS = (40000, 15000)
SEED = 20260930
# Sessions per rung. The validation below picks the cheapest protocol that passes its gates.
PROTOCOLS = {
    "full": {0: 3, 1: 3, 2: 3, 3: 2},
    "reduced": {0: 2, 1: 2, 2: 2, 3: 1},
    "lean": {0: 2, 1: 2, 2: 1, 3: 1},
    "minimal": {0: 1, 1: 1, 2: 1, 3: 1},
}
# Recommending too little prompting (unsafe) is the costly error; one rung too much costs the
# consumer one more sentence of prompt.
GATES = {"unsafe_at_most": 0.10, "within_one_at_least": 0.80, "converged_at_least": 0.90}
TOKENS_PER_SESSION = 0.53e6  # The corrected urn run: 34.7M input tokens over 66 contexts.
# Rated sessions per protocol (the rate-stating rung), and when a session follows the stated
# rates: implied priors within 0.10 of them on average and 0.20 at every level (the task
# validation's tolerance for description modules).
RATED_SESSIONS = {"full": 2, "reduced": 2, "lean": 1, "minimal": 1}
FOLLOWS = {"mean_at_most": 0.10, "largest_at_most": 0.20}
RATED_GATES = {"follows_at_least": 0.90, "false_follows_at_most": 0.10}
# Priors a configuration might apply when it ignores the stated rates: the mappings it judged
# for itself under the named wording (applied, and judged rare), the recovery mapping, and a flat
# default.
IGNORED = {
    "judged, applied": (0.0, 0.5, 0.3, 0.9, 0.96),
    "judged rare": (0.0, 0.05, 0.05, 0.1, 0.2),
    "recovery mapping": (0.03, 0.3, 0.45, 0.6, 0.85),
    "flat default": (0.5, 0.5, 0.5, 0.5, 0.5),
}


# The runner admits a batch only if known usage plus this reserve per run in the batch fits the
# cap, so the cap needs room for the last batch's reserve on top of the expected usage.
RUNNER_RESERVE, RUNNER_CONCURRENCY = 800000, 2


def budget_for(sessions):
    """A token cap that lets the runner admit every batch at the expected usage."""
    return int(sessions * TOKENS_PER_SESSION * 1.1 + RUNNER_CONCURRENCY * RUNNER_RESERVE)


def stated_rates(structure):
    from epistemics.disposition_tasks.urn import RATES

    return RATES[structure]


def follows(implied, rates):
    """Whether a session's implied priors follow the stated rates."""
    gaps = np.abs(np.asarray(implied, dtype=float) - np.asarray(rates, dtype=float))
    return {
        "mean_gap": float(gaps.mean()),
        "largest_gap": float(gaps.max()),
        "follows": bool(
            gaps.mean() <= FOLLOWS["mean_at_most"] and gaps.max() <= FOLLOWS["largest_at_most"]
        ),
    }


def rated_check(models, config, structure):
    """The rate-stating rung: does each rated session's forecasting follow the stated rates?"""
    rated = CATALOGUE[structure].get("rated")
    if not rated:
        return None
    rates = stated_rates(structure)
    rows = [
        {"id": s["id"], **follows(s["slot_means"], rates)}
        for s in models["sessions"]
        if s["configuration"] == config
        and s["module"] == rated["module"]
        and s["variant"] == rated["variant"]
        and s.get("slot_means")
    ]
    if not rows:
        return None
    return {
        "rates": list(rates),
        "sessions": len(rows),
        "followed": sum(r["follows"] for r in rows),
        "reliable": all(r["follows"] for r in rows),
        "rows": rows,
    }


def _rated_one(args):
    """One synthetic rated session: its implied priors under the real design and fit."""
    from epistemics.dispositions import design, observers
    from epistemics.dispositions.response import sample_reports
    from epistemics.ledger.models import cue_marginals

    applied_mean, seed = args
    rng = np.random.default_rng(seed)
    items = design.mismatch_urn()
    omega = rng.uniform(0.1, 0.4)
    target = inclusion.logit(np.clip(applied_mean, 0.005, 0.995))
    applied = 1 / (1 + np.exp(-(target + omega * rng.normal(size=5))))
    latent = observers.cue_observer(observers.mismatch, items, applied, 1.0)
    reports = sample_reports(latent, rng.uniform(0.05, 0.3), rng)
    posterior = cue_marginals("mismatch", items, reports)[0]
    return (posterior @ inclusion.GRID).tolist()


def validate_rated(seed=SEED + 7, datasets=60, workers=8):
    """Sensitivity and specificity of the follows rule through the real design and fit."""
    rates = np.array(stated_rates("mismatch"))
    rng = np.random.default_rng(seed)
    jobs = [("stated rates", rates, int(rng.integers(2**31))) for _ in range(datasets)]
    for name, mapping in IGNORED.items():
        jobs += [(name, np.array(mapping), int(rng.integers(2**31))) for _ in range(datasets // 2)]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        implied = list(pool.map(_rated_one, [(m, s) for _, m, s in jobs]))
    rows = [
        {"source": name, "implied": imp, **follows(imp, rates)}
        for (name, _, _), imp in zip(jobs, implied, strict=True)
    ]
    by_source = {}
    for r in rows:
        cell = by_source.setdefault(r["source"], {"sessions": 0, "follows": 0})
        cell["sessions"] += 1
        cell["follows"] += r["follows"]
    sensitivity = by_source["stated rates"]["follows"] / by_source["stated rates"]["sessions"]
    ignored = [r for r in rows if r["source"] != "stated rates"]
    false_follows = sum(r["follows"] for r in ignored) / len(ignored)
    return {
        "schema_version": "epistemics.structure-check-rated-validation.v1",
        "version": VERSION,
        "seed": seed,
        "rates": rates.tolist(),
        "rule": FOLLOWS,
        "gates": RATED_GATES,
        "by_source": by_source,
        "follows_when_applied": sensitivity,
        "false_follows": false_follows,
        "passed": bool(
            sensitivity >= RATED_GATES["follows_at_least"]
            and false_follows <= RATED_GATES["false_follows_at_most"]
        ),
        "rows": rows,
        "scope": (
            "Synthetic rated sessions through the forecast-only mismatch design and the per-level "
            "description fit, at report noise 0.05-0.3 and per-level spread 0.1-0.4 on the "
            "log-odds scale; respondents apply the stated rates, or one of the priors they might "
            "apply instead."
        ),
    }


def rung_needed(inclusions):
    """Lowest rung whose inclusion is at least RELIABLE, or None."""
    for r, value in enumerate(inclusions):
        if value >= RELIABLE:
            return r
    return None


def true_inclusion(theta, sigma):
    """Inclusion for an uninformative description at each rung, integrated over the session."""
    return [
        float(
            inclusion.phi((r - theta + sigma * inclusion.NODES) / inclusion.LEVEL_NOISE)
            @ inclusion.WEIGHTS
        )
        for r in range(4)
    ]


def recommend(by_rung):
    """Lowest rung whose inclusion interval starts at RELIABLE or above, or None."""
    for r in range(4):
        if by_rung[str(r)]["interval_90"][0] >= RELIABLE:
            return r
    return None


def fit_structure(rows, seed=SEED, chains=4):
    """Per-structure second layer on one structure's sessions, and its recommendation."""
    (family,) = rows
    iterations, burn = CHAINS
    fit = joint.sample(rows, "shared", "mixture", chains, iterations, burn, seed)
    by_rung = fit["inclusion_by_rung"][family]
    valid = fit["rhat_max"] <= joint.RHAT_LIMIT
    return {
        "valid": bool(valid),
        "rhat_max": fit["rhat_max"],
        "recommended_rung": recommend(by_rung) if valid else None,
        "inclusion_by_rung": by_rung,
        "theta": fit["parameters"]["theta"],
        "sigma": fit["parameters"]["sigma"],
        "w": fit["parameters"]["w"],
        "phi": fit["parameters"]["phi"],
        "mapping": fit["mapping"][family],
        "sessions_by_rung": {
            str(r): int(sum(1 for s, _, _ in rows[family] if s == r)) for r in range(4)
        },
    }


def outcome(recommended, needed):
    """exact, conservative (more prompting than needed) or unsafe (less); None counts as rung 4."""
    got, need = 4 if recommended is None else recommended, 4 if needed is None else needed
    return "exact" if got == need else "unsafe" if got < need else "conservative"


def excess(recommended, needed):
    """Rungs of prompting recommended beyond those needed (negative when unsafe)."""
    return (4 if recommended is None else recommended) - (4 if needed is None else needed)


def _validate_one(args):
    family, truth, counts, seed = args
    rng = np.random.default_rng(seed)
    rows = inclusion.simulate(
        rng, truth, stated=True, stated_source="mixture", counts={family: counts}
    )
    result = fit_structure(rows, seed=seed)
    needed = rung_needed(true_inclusion(truth["theta"], truth["sigma"]))
    got = result["recommended_rung"]
    return {
        "family": family,
        "truth": truth,
        "needed": needed,
        "recommended": got,
        "valid": result["valid"],
        "rhat_max": result["rhat_max"],
        "outcome": outcome(got, needed) if result["valid"] else "not converged",
        "excess": excess(got, needed) if result["valid"] else None,
        "unprompted": result["inclusion_by_rung"]["0"],
        "true_unprompted": true_inclusion(truth["theta"], truth["sigma"])[0],
    }


GENERATING = {"theta": (-0.8, 3.2), "w": (0.0, 1.0), "sigma": (0.2, 1.2), "phi": (0.0, 1.0)}


def validate(seed=SEED, datasets=40, workers=8):
    """Recovery of the recommendation under each protocol, through the real item designs."""
    rng = np.random.default_rng(seed)
    families = list(CATALOGUE)
    jobs = []
    for name, counts in PROTOCOLS.items():
        for k in range(datasets):
            truth = {p: float(rng.uniform(*limits)) for p, limits in GENERATING.items()}
            family = families[int(rng.integers(len(families)))]
            jobs.append((name, (family, truth, counts, seed + 1000 * len(jobs) + k)))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_validate_one, [j for _, j in jobs]))
    by_protocol = {}
    for (name, _), row in zip(jobs, results, strict=True):
        by_protocol.setdefault(name, []).append(row)
    summary = {}
    for name, rows in by_protocol.items():
        n = len(rows)
        share = {o: sum(r["outcome"] == o for r in rows) / n for o in ("exact", "conservative")}
        share["unsafe"] = sum(r["outcome"] == "unsafe" for r in rows) / n
        share["converged"] = sum(r["valid"] for r in rows) / n
        share["within_one"] = sum(r["excess"] in (0, 1) for r in rows) / n
        unprompted_error = [
            abs(r["unprompted"]["mean"] - r["true_unprompted"]) for r in rows if r["valid"]
        ]
        passed = (
            share["unsafe"] <= GATES["unsafe_at_most"]
            and share["within_one"] >= GATES["within_one_at_least"]
            and share["converged"] >= GATES["converged_at_least"]
        )
        sessions = sum(PROTOCOLS[name].values())
        summary[name] = {
            "sessions": sessions,
            "tokens_estimate": sessions * TOKENS_PER_SESSION,
            **share,
            "unprompted_mae": float(np.mean(unprompted_error)) if unprompted_error else None,
            "passed": passed,
        }
    passing = [n for n, s in summary.items() if s["passed"]]
    chosen = min(passing, key=lambda n: summary[n]["sessions"]) if passing else None
    return {
        "schema_version": "epistemics.structure-check-validation.v1",
        "version": VERSION,
        "seed": seed,
        "datasets_per_protocol": datasets,
        "generating_ranges": GENERATING,
        "gates": GATES,
        "reliable": RELIABLE,
        "chains": CHAINS,
        "protocols": {n: {str(r): c for r, c in p.items()} for n, p in PROTOCOLS.items()},
        "summary": summary,
        "chosen_protocol": chosen,
        "rows": [{"protocol": name, **row} for (name, _), row in zip(jobs, results, strict=True)],
        "scope": (
            "Synthetic configurations with one structure each (family drawn from the catalogue; "
            "threshold, cue weight, drift and fidelity drawn from the stated ranges), run through "
            "the real item designs and description fits at each protocol's session counts, fitted "
            "by the per-structure second layer. The needed rung is computed from the true "
            "threshold and drift for an uninformative description."
        ),
    }


def check(models, configurations, structures):
    """Structure checks on the ledger's sessions: one fit per configuration and structure."""
    result = {}
    for config in configurations:
        for structure in structures:
            fmt = CATALOGUE[structure]["format"]
            rows = inclusion.ledger_sessions(models, config, fmt=fmt)
            if structure not in rows or not any(s == 3 for s, _, _ in rows[structure]):
                continue
            fit = fit_structure({structure: rows[structure]})
            rated = rated_check(models, config, structure)
            advice = fit["recommended_rung"]
            if fit["valid"] and advice is None and rated and rated["reliable"]:
                advice = "rate"
            short, _ = ACTIONS[advice]
            result.setdefault(config, {})[structure] = {
                **fit,
                "rated": rated,
                "advice": advice if fit["valid"] else None,
                "format": fmt,
                "variants": list(inclusion.FORMAT_VARIANTS.get(fmt, ())),
                "action": short if fit["valid"] else None,
                "sessions": len(rows[structure]),
            }
    return result


def plan(configurations, structures, protocol="full", rungs=(0, 1, 2, 3), rated=False):
    """Runner groups that collect the named structures on the salience ladder (the given rungs;
    leave out a rung whose sessions already exist with the same text), and optionally the
    rate-stating rung."""
    groups = []
    for structure in structures:
        extra = CATALOGUE[structure].get("rated")
        if rated and extra:
            groups.append(
                {
                    "configurations": tuple(configurations),
                    "modules": (extra["module"],),
                    "contexts": tuple(
                        (extra["variant"], "markets", r)
                        for r in range(1, RATED_SESSIONS[protocol] + 1)
                    ),
                }
            )
        for rung, count in PROTOCOLS[protocol].items():
            if rung not in rungs:
                continue
            module, variant = CATALOGUE[structure]["ladder"][rung]
            groups.append(
                {
                    "configurations": tuple(configurations),
                    "modules": (module,),
                    "contexts": tuple((variant, "markets", r) for r in range(1, count + 1)),
                }
            )
    return tuple(groups)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--output", type=Path, required=True)
    v.add_argument("--datasets", type=int, default=40)
    v.add_argument("--workers", type=int, default=8)
    c = sub.add_parser("check")
    c.add_argument("--ledger", type=Path, default=Path("output/ledger.json"))
    c.add_argument("--output", type=Path, required=True)
    c.add_argument("--configuration", action="append", default=None)
    c.add_argument("--structure", action="append", choices=sorted(CATALOGUE), default=None)
    c.add_argument("--validation", type=Path, required=True)
    k = sub.add_parser("collect")
    k.add_argument("directory", type=Path)
    k.add_argument("--configuration", action="append", required=True)
    k.add_argument("--structure", action="append", choices=sorted(CATALOGUE), required=True)
    k.add_argument("--protocol", choices=sorted(PROTOCOLS), required=True)
    k.add_argument("--validation", action="append", type=Path, required=True)
    k.add_argument("--rung", action="append", type=int, choices=range(4), default=None)
    k.add_argument("--rated", action="store_true", help="Also collect the rate-stating rung")
    k.add_argument("--rated-only", action="store_true", help="Collect only the rate-stating rung")
    vr = sub.add_parser("validate-rated")
    vr.add_argument("--output", type=Path, required=True)
    vr.add_argument("--datasets", type=int, default=60)
    k.add_argument("--max-tokens", type=int, default=None)
    a = p.parse_args()
    if a.command == "validate":
        run = validate(datasets=a.datasets, workers=a.workers)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({"summary": run["summary"], "chosen": run["chosen_protocol"]}, indent=2))
    elif a.command == "validate-rated":
        run = validate_rated(datasets=a.datasets)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(
            json.dumps(
                {
                    k: run[k]
                    for k in ("by_source", "follows_when_applied", "false_follows", "passed")
                },
                indent=2,
            )
        )
    elif a.command == "check":
        raw = a.validation.read_bytes()
        validation = json.loads(raw)
        ledger_bytes = a.ledger.read_bytes()
        models = json.loads(ledger_bytes)["models"]
        run = {
            "schema_version": "epistemics.structure-checks.v1",
            "version": VERSION,
            "validation": {
                "file": a.validation.name,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "chosen_protocol": validation["chosen_protocol"],
            },
            "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "reliable": RELIABLE,
            "checks": check(
                models, a.configuration or ["astra", "sol"], a.structure or list(CATALOGUE)
            ),
        }
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        for config, rows in run["checks"].items():
            for structure, r in rows.items():
                print(config, structure, r["valid"], r["advice"], r["action"])
    else:
        from epistemics.disposition_tasks import runner

        rungs = () if a.rated_only else tuple(range(4)) if a.rung is None else tuple(a.rung)
        groups = plan(a.configuration, a.structure, a.protocol, rungs, a.rated or a.rated_only)
        sessions = sum(len(g["contexts"]) * len(g["configurations"]) for g in groups)
        budget = a.max_tokens or budget_for(sessions)
        root = a.directory.resolve()
        planned = runner.prepare(
            root, a.validation, phase="structure-check", groups=groups, max_tokens=budget
        )
        asyncio.run(runner.run(root, planned))


if __name__ == "__main__":
    main()
