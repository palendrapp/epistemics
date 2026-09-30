"""Serial position within a session: does error grow as a session's context grows?

Every collection so far ran its 24 cases in one conversation, in random order. A session's
cumulative input is about half a million tokens because each of its roughly 27 model turns resends
the context; the context at the last case is of the order of 30 thousand tokens. For each session whose cases have a normative answer (the
load modules, and the scripted-peer tasks where everything is stated), this compares the error of
each answer with its position. Order is randomised independently of the case, so position is not
confounded with difficulty.
"""

import json
from pathlib import Path

import numpy as np

from epistemics.disposition_tasks.analysis import LOAD_MODELS
from epistemics.dispositions import observers, social
from epistemics.ledger import dispositions

EDGE = 0.01
EXACT = 0.015
PERMUTATIONS = 2000
TERTILES = ((1, 8), (9, 16), (17, 24))


def registry_roots(path="docs/experiments.json"):
    """Collections in the registry from the capacity and multi-agent batteries."""
    data = json.loads(Path(path).read_text())
    entries = data.get("experiments") or data.get("entries")
    prefixes = ("capacity", "multi-agent", "confidence")
    roots = []
    for e in entries:
        if e["id"].startswith(prefixes):
            roots += [r for r in e.get("roots", []) if Path(r).exists() and r not in roots]
    return roots


def ideal(record):
    """Exact log-odds per item, or None where the module has no normative answer."""
    items = {k: np.asarray(v) for k, v in record["items"].items()}
    module, variant = record["module"], record["variant"]
    if module in LOAD_MODELS:
        return observers.load_answers(LOAD_MODELS[module], items)[0]
    if module == "advice-peer" and variant == "peer-a":
        return social.advice_answer(items)
    if module == "conformity-peer" and variant == "peer-a":
        return social.conformity_answers(items)[0]
    if module == "relay-peer" and variant == "chain-stated":
        return social.relay_answer(items)
    return None


def family(configuration):
    return "GPT-5.6" if configuration in ("luna", "terra") else "GPT-6"


def rows(roots):
    out = []
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified"):
                continue
            exact = ideal(record)
            if exact is None:
                continue
            responses = np.asarray(record["responses"], dtype=float)
            clipped = np.clip(responses, EDGE, 1 - EDGE)
            error = np.abs(np.log(clipped / (1 - clipped)) - np.clip(exact, -4.6, 4.6))
            truth = 1 / (1 + np.exp(-exact))
            for position, item in enumerate(record["order"], start=1):
                out.append(
                    {
                        "session": f"{root}/{record['run_id']}",
                        "configuration": record["configuration"],
                        "family": family(record["configuration"]),
                        "module": record["module"],
                        "position": position,
                        "error": float(error[item]),
                        "exact": bool(abs(responses[item] - truth[item]) <= EXACT),
                    }
                )
    return out


def slope(data):
    """Error on position with session fixed effects (both demeaned within session)."""
    x = data["position"] - data["position_mean"]
    y = data["error"] - data["error_mean"]
    return float(np.sum(x * y) / np.sum(x * x))


def demeaned(position, error, session):
    """Position and error with their session means, for the within-session slope."""
    count = np.bincount(session)
    position_mean = np.bincount(session, position) / count
    error_mean = np.bincount(session, error) / count
    return {
        "position": position,
        "position_mean": position_mean[session],
        "error": error,
        "error_mean": error_mean[session],
    }


def summary(rows_, rng):
    result = {}
    for name in ("GPT-6", "GPT-5.6", "all"):
        chosen = [r for r in rows_ if name == "all" or r["family"] == name]
        if not chosen:
            continue
        sessions = sorted({r["session"] for r in chosen})
        index = {s: i for i, s in enumerate(sessions)}
        sid = np.array([index[r["session"]] for r in chosen])
        pos = np.array([r["position"] for r in chosen], dtype=float)
        err = np.array([r["error"] for r in chosen])
        exact = np.array([r["exact"] for r in chosen])

        observed = slope(demeaned(pos, err, sid))
        null = []
        for _ in range(PERMUTATIONS):
            shuffled = pos.copy()
            for s in range(len(sessions)):
                where = np.flatnonzero(sid == s)
                shuffled[where] = rng.permutation(pos[where])
            null.append(slope(demeaned(shuffled, err, sid)))
        null = np.array(null)
        result[name] = {
            "sessions": len(sessions),
            "answers": len(chosen),
            "slope_per_case": observed,
            "slope_per_24_cases": observed * 23,
            "p_two_sided": float((1 + np.sum(np.abs(null) >= abs(observed))) / (1 + len(null))),
            "by_tertile": {
                f"{lo}-{hi}": {
                    "exact_share": float(exact[(pos >= lo) & (pos <= hi)].mean()),
                    "mean_error": float(err[(pos >= lo) & (pos <= hi)].mean()),
                }
                for lo, hi in TERTILES
            },
        }
    return result


def analyse(roots=None, seed=20261017):
    roots = roots or registry_roots()
    data = rows(roots)
    rng = np.random.default_rng(seed)
    by_module = {}
    for module in sorted({r["module"] for r in data}):
        by_module[module] = summary([r for r in data if r["module"] == module], rng)
    return {
        "schema_version": "epistemics.position.v1",
        "roots": roots,
        "overall": summary(data, rng),
        "by_module": by_module,
    }
