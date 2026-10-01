"""Build the ledger: registry metadata joined with facts and estimates from frozen artifacts."""

import json
import subprocess
from pathlib import Path

import numpy as np

from epistemics.ledger import (
    VERSION,
    deliberation,
    dispositions,
    guide,
    models,
    roots,
    transfer,
    variance,
)

CONFIGURATIONS = ("astra", "sol", "astra-low", "sol-low", "luna", "terra")


def is_disposition(root):
    """Collections from the disposition battery, including structure checks run through it."""
    return Path(root).name.startswith(
        (
            "disposition-",
            "structure-check-",
            "traits-stage",
            "capacity-",
            "multi-agent-",
            "confidence-",
            "battery-v3-",
        )
    )


def commit():
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def mean_of(values):
    values = [v for v in values if v is not None]
    return {"mean": float(np.mean(values)), "contexts": len(values)} if values else None


def session_variance(pairs, config):
    """Between-session SD of the ambiguous relay levels over random-order set-A sessions."""
    y, s = [], []
    for record, summary in pairs:
        if (
            record["configuration"] == config
            and summary.get("module") == "corroboration-cues"
            and summary.get("variant") == "cues-a"
            and summary.get("order_policy") == "random"
        ):
            chosen = [record["slot_fits"][level]["implied"] for level in (1, 2, 3)]
            y.append([c["mean"] for c in chosen])
            s.append(variance.standard_errors([c["interval_90"] for c in chosen]))
    if len(y) < 3:
        return None
    result = variance.estimate(y, s)
    return {"sessions": result["sessions"], **result["total_sd"]}


PRESENTATIONS = {
    "cues-a": ("cues", ("cues-a",)),
    "cues-b": ("cues", ("cues-b",)),
    "dossier": ("dossier", None),
    "unprompted": ("unprompted", ("dossier-a",)),
    "named": ("unprompted", ("named-a",)),
    "asked": ("asked", None),
    "probed": ("probed", None),
}


def mappings(select, base):
    """Mean implied prior per description level, by presentation."""
    return {
        name: np.mean([s["implied"] for s in rows], axis=0).tolist()
        for name, (suffix, variants) in PRESENTATIONS.items()
        if (rows := select(f"{base}-{suffix}", variants))
    }


def mapping_sessions(select, base):
    return {
        name: len(rows)
        for name, (suffix, variants) in PRESENTATIONS.items()
        if (rows := select(f"{base}-{suffix}", variants))
    }


WIDE_GAP = 0.15
# Conditions whose stated rates are confounded by the design, kept out of coherence: in the urn
# selection tasks the named mechanism ("hold back every blue ball") makes any record with a blue
# ball logically disqualifying, so stated and applied rates diverge by construction
# (docs/disposition-abstract-2026-09-28.md). The corrected variant (urn2-named) states the mechanism
# per round and is not confounded.
CONFOUNDED = {("selection-urn-asked", "urn-named"), ("selection-urn-probed", "urn-named")}


def confounded(s):
    return (s["module"], s["variant"]) in CONFOUNDED


def coherence_by_condition(mine):
    """Largest stated-minus-implied gap per session, grouped by module and variant."""
    result = {}
    for _, s in mine:
        if confounded(s):
            continue
        if s["module"].endswith(("-cues", "-dossier", "-asked", "-probed")) and (
            s.get("stated_minus_implied_max") is not None
        ):
            key = f"{s['module']}/{s['variant']}"
            result.setdefault(key, []).append(
                (s["stated_minus_implied_max"], s["stated_minus_implied_mean"])
            )
    return result


def passport(pairs, retests, contrasts):
    """Per configuration: the parameters measured so far, pooled over verified contexts."""
    result = {}
    for config in CONFIGURATIONS:
        mine = [(r, s) for r, s in pairs if r["configuration"] == config and s.get("module")]

        def select(module, variants=None, mine=mine):
            return [
                s
                for _, s in mine
                if s["module"] == module and (variants is None or s["variant"] in variants)
            ]

        reports = [s for _, s in mine if s["module"] in ("corroboration", "disclosure")]
        learning = [s["learning"] for s in reports if "learning" in s]
        entry = {
            "relay_default": mean_of(
                [s["disposition"]["mean"] for s in select("corroboration", ("paired", "open"))]
            ),
            "silence_default": mean_of(
                [s["disposition"]["mean"] for s in select("disclosure", ("paired", "open"))]
            ),
            "value_of_certainty": mean_of(
                [s["certainty_value_linear"]["mean"] for s in select("checks")]
            ),
            # Share of checks priced at exactly the floor of their decision value; version 0.1
            # designs had half-point values, which bias the fitted value of certainty slightly
            # negative for respondents who price rationally.
            "checks_priced_at_decision_value": [
                sum(s["exact_decision_value"] for s in select("checks")),
                24 * len(select("checks")),
            ]
            if select("checks")
            else None,
            "evidence_sensitivity": mean_of([s["gamma"] for s in reports]),
            "report_noise_median": float(np.median([s["report_sd"] for s in reports]))
            if reports
            else None,
            "learning": {
                "contexts": len(learning),
                "start": mean_of([x["start"]["mean"] for x in learning]),
                "strength_median": float(np.median([x["strength"] for x in learning]))
                if learning
                else None,
                "detected": sum(x["learning_probability"] > 0.5 for x in learning),
            }
            if learning
            else None,
            # Per presentation: formal sets A and B, the prompted dossier and the unprompted one.
            "relay_description_mapping": mappings(select, "corroboration") or None,
            "disclosure_description_mapping": mappings(select, "disclosure") or None,
            "relay_description_sessions": mapping_sessions(select, "corroboration") or None,
            "disclosure_description_sessions": mapping_sessions(select, "disclosure") or None,
            "description_retest_difference": mean_of(
                [r["mean_absolute_difference"] for r in retests if r["configuration"] == config]
            ),
            "relative_judgement_contrast": contrasts.get(config, {}).get("mean"),
            "relative_judgement_sessions": sum(
                contrasts.get(config, {}).get("contexts", {}).values()
            )
            or None,
            "ambiguous_description_session_sd": session_variance(pairs, config),
            # Sessions whose forecasts use the base rates they state (every level within 0.10),
            # over formal description modules and prompted dossiers.
            "description_coherence": [
                sum(s["stated_minus_implied_max"] <= 0.10 for s in cue_rows),
                len(cue_rows),
            ]
            if (
                cue_rows := [
                    s
                    for _, s in mine
                    if s["module"].endswith(("-cues", "-dossier", "-asked", "-probed"))
                    and not confounded(s)
                    and s.get("stated_minus_implied_max") is not None
                ]
            )
            else None,
            # Per condition: sessions coherent at every level, sessions, and sessions whose
            # forecasts depart widely from their stated rates (mean gap at least 0.15).
            "description_coherence_by_condition": {
                condition: [
                    sum(g <= 0.10 for g, _ in gaps),
                    len(gaps),
                    sum(m >= WIDE_GAP for _, m in gaps),
                ]
                for condition, gaps in coherence_by_condition(mine).items()
            }
            or None,
            "contexts": len(mine),
        }
        if any(v is not None for k, v in entry.items() if k != "contexts"):
            result[config] = entry
    return result


def build(registry_path="docs/experiments.json"):
    registry = json.loads(Path(registry_path).read_text())
    experiments, all_pairs, all_retests, contrasts, usage_by_day = [], [], [], {}, {}
    extracted = {}

    def records_for(root):
        if root not in extracted:
            extracted[root] = dispositions.extract(root) if is_disposition(root) else []
        return extracted[root]

    for entry in registry["experiments"]:
        item = dict(entry)
        root_facts = [
            roots.facts(r) for r in entry.get("roots", []) if Path(r, "plan.json").exists()
        ]
        for f in root_facts:
            day = (f["created_at"] or "")[:10]
            bucket = usage_by_day.setdefault(day, {k: 0 for k in roots.USAGE})
            for k in roots.USAGE:
                bucket[k] += f["usage"][k]
            f.pop("per_run")
        item["facts"] = root_facts
        pairs = []
        for r in entry.get("roots", []):
            if is_disposition(r) and Path(r, "plan.json").exists():
                for record in records_for(r):
                    pairs.append((record, dispositions.summary(record)))
        runs = []
        for record, s in pairs:
            row = {"run_id": record["run_id"], "configuration": record["configuration"], **s}
            if s.get("module") in ("corroboration", "disclosure") and s.get("variant") in (
                "suggestive",
                "reassuring",
            ):
                row["descriptor_fits"] = dispositions.descriptor_fits(record)
            runs.append(row)
        item["runs"] = runs
        if entry.get("compare_with"):
            first = [(r, dispositions.summary(r)) for r in records_for(entry["compare_with"])]
            item["retest"] = dispositions.retest(
                [(r, s) for r, s in first if r.get("verified")],
                [(r, s) for r, s in pairs if r.get("verified")],
            )
            all_retests += item["retest"]
        contrast = dispositions.range_contrast([(r, s) for r, s in pairs if r.get("verified")])
        if contrast:
            item["range_contrast"] = contrast
            contrasts.update(contrast)
        all_pairs += [(r, s) for r, s in pairs if r.get("verified")]
        experiments.append(item)
    experiment_for = {}
    for entry in registry["experiments"]:
        for r in entry.get("roots", []):
            experiment_for.setdefault(r, entry["id"])
    totals = {
        "experiments": len(experiments),
        "contexts_completed": sum(f["runs_completed"] for e in experiments for f in e["facts"]),
        "tool_errors": sum(f["tool_errors"] for e in experiments for f in e["facts"]),
        "usage": {k: sum(d[k] for d in usage_by_day.values()) for k in roots.USAGE},
        "usage_by_day": dict(sorted(usage_by_day.items())),
    }
    records = [r for rs in extracted.values() for r in rs]
    analyses = {"transfer": transfer.analyse(records), "noticing": transfer.noticing(records)}
    frame_roots = [
        r
        for entry in registry["experiments"]
        if entry["id"] in deliberation.FRAME_EXPERIMENTS
        for r in entry.get("roots", [])
        if Path(r, "plan.json").exists()
    ]
    if frame_roots:
        analyses["frame_sensitivity"] = deliberation.passport_frames(frame_roots)
    result = {
        "schema_version": "epistemics.ledger.v1",
        "ledger_version": VERSION,
        "repository_commit": commit(),
        "decisions": registry.get("decisions", []),
        "next": registry.get("next", []),
        "experiments": experiments,
        "passport": passport(all_pairs, all_retests, contrasts),
        "totals": totals,
        "models": models.build(
            {r: records for r, records in extracted.items() if is_disposition(r)}, experiment_for
        ),
        "analyses": analyses,
        "scope": "Recomputed from frozen plans, executions and verified reports; model revisions are requested aliases and execution is operator-asserted.",
    }
    # The passport carries the frame sensitivity too; configurations measured only there get an
    # entry of their own.
    for config, frames in analyses.get("frame_sensitivity", {}).items():
        result["passport"].setdefault(config, {"contexts": frames["sessions"]})[
            "frame_sensitivity"
        ] = frames
    result["guide"] = guide.guide(result, models.descriptors())
    return result
