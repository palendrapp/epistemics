"""Exploratory: how strongly does each configuration react to one analyst's call (exploration log
idea 26)? Across the single-call peer-advice data already collected:

  advice-peer, record stated (multi-agent pilot)   the weight a call deserves is known:
                                                   logit(the phrase's hit rate)
  advice-peer, no record (multi-agent open)
  advice-agent, -relay, -sensor, no record (confidence transfer)
  analysts' calls in order (calls-order): the first call's step

A call's weight is the answer's log-odds minus the stated prior's, signed by the call's direction,
on cases where the agent has no reading of its own (the call is the only evidence). Per
configuration and source: the mean weight; on stated records, the mean ratio to the deserved weight.
"""

from pathlib import Path

import numpy as np

from epistemics.dispositions.screen import logit

ADVICE = ("advice-peer", "advice-agent", "advice-relay", "advice-sensor")
PHRASES = ("I think", "plain", "definitely")


def weights(roots):
    from epistemics.ledger import dispositions

    out = {}
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or record.get("module") not in ADVICE:
                continue
            items = {k: np.asarray(v) for k, v in record["items"].items()}
            source = (
                f"{record['module']} ({'record' if record['variant'] == 'peer-a' else 'no record'})"
            )
            for i, v in enumerate(record["responses"]):
                if v is None or int(items["own"][i]) != 0:
                    continue
                w = (float(logit(v)) - float(logit(items["prior"][i]))) * int(items["call"][i])
                row = {"weight": w, "phrase": int(items["phrase"][i]), "root": Path(root).name,
                       "run": record["run_id"]}  # fmt: skip
                if record["variant"] == "peer-a":
                    q = items[f"hits_{int(items['phrase'][i])}"][i] / 40
                    row["deserved"] = float(logit(q))
                out.setdefault((record["configuration"], source), []).append(row)
    return out


def phrase_of(row):
    """The first call's phrase in an analysts'-calls row (from the item's specification)."""
    from epistemics.dispositions import calls

    for analyst, _, phrase in calls.items_spec()[row["item"]]["calls"]:
        if analyst == row["first"][0]:
            return phrase
    return None


def call_steps(roots):
    from epistemics.ledger import dispositions

    out = {}
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "calls" not in record:
                continue
            for r in record["calls"]["items"]:
                out.setdefault((record["configuration"], "analysts' calls in order"), []).append(
                    {
                        "weight": r["step1"] * r["first"][1],
                        "phrase": phrase_of(r),
                        "run": record["run_id"],
                    }  # fmt: skip
                )
    return out


def summary(advice_roots, calls_roots=()):
    data = {**weights(advice_roots), **(call_steps(calls_roots) if calls_roots else {})}
    table = {}
    for (c, source), rows in sorted(data.items()):
        w = np.array([r["weight"] for r in rows])
        entry = {"mean_weight": float(w.mean()), "n": len(rows),
                 "sessions": len({r.get("run") for r in rows})}  # fmt: skip
        by_phrase = {}
        for r in rows:
            if r["phrase"] is not None:
                by_phrase.setdefault(PHRASES[r["phrase"]], []).append(r["weight"])
        if by_phrase:
            entry["by_phrase"] = {k: float(np.mean(v)) for k, v in by_phrase.items()}
        deserved = [(r["weight"], r["deserved"]) for r in rows if abs(r.get("deserved", 0)) > 0.2]
        if deserved:
            d = np.array(deserved)
            entry["deserved"] = float(d[:, 1].mean())
            entry["ratio_to_deserved"] = float(np.mean(d[:, 0] / d[:, 1]))
        table.setdefault(source, {})[c] = entry
    relative = {}
    for source, configs in table.items():
        for c, e in configs.items():
            others = [v["mean_weight"] for k, v in configs.items() if k != c]
            if others:
                relative.setdefault(c, {})[source] = e["mean_weight"] / float(np.mean(others))
    return {
        "schema_version": "epistemics.call-reaction.v1",
        "sources": table,
        "relative_to_others": relative,
        "scope": "Exploratory: a call's weight on cases without the agent's own reading.",
    }


RECORD_EXPERIMENTS = ("multi-agent-pilot",)


def record_ratios(roots):
    """Per configuration: the weight given to an analyst's call with its record stated, over the
    weight that record implies (1: exact)."""
    sources = summary(roots)["sources"]
    return {
        c: e["ratio_to_deserved"]
        for c, e in sources.get("advice-peer (record)", {}).items()
        if "ratio_to_deserved" in e
    }
