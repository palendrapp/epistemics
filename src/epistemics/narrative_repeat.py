"""Compare exact-wording narrative repeats without changing the frozen evaluator."""

import argparse
from pathlib import Path

import numpy as np

from epistemics.narrative.inference import ARTIFACT, DEMAND, total_variation_pp
from epistemics.narrative.models import Report
from epistemics.narrative.service import digest, encoded, save


def compare(first_bytes, repeat_bytes):
    first, repeat = (Report.model_validate_json(raw) for raw in (first_bytes, repeat_bytes))
    for field in (
        "battery_version",
        "evaluator_version",
        "implementation_sha256",
        "assignments",
        "context_policy",
        "response_origin",
    ):
        if getattr(first.manifest, field) != getattr(repeat.manifest, field):
            raise ValueError(f"Repeat must preserve {field}")
    if first.manifest.participant.kind != repeat.manifest.participant.kind:
        raise ValueError("Repeat must preserve participant kind")
    if first.manifest.participant.kind == "agent":
        for field in ("model", "model_version", "temperature"):
            if getattr(first.manifest.participant.configuration, field) != getattr(
                repeat.manifest.participant.configuration, field
            ):
                raise ValueError(f"Repeat must preserve requested {field}")
    rows = []
    for a in first.manifest.assignments:
        before, after = first.cases[a.assignment_id], repeat.cases[a.assignment_id]
        if any(before[i].trial != after[i].trial for i in (0, 1)):
            raise ValueError("Early public stimuli must be identical")
        same_query = before[1].answer.query == after[1].answer.query
        if same_query and before[2].trial != after[2].trial:
            raise ValueError("Identical choices must yield identical research evidence")
        rows.append(
            {
                "assignment_id": a.assignment_id,
                "domain": a.domain,
                "direction": a.direction,
                "presentation": a.presentation,
                "initial_joint_tv_pp": total_variation_pp(
                    before[0].answer.joint.vector(), np.array(after[0].answer.joint.vector())
                ),
                "signal_forecast_mean_absolute_difference_pp": float(
                    100
                    * np.mean(
                        np.abs(
                            np.array(before[0].answer.signal_if_state.vector())
                            - after[0].answer.signal_if_state.vector()
                        )
                    )
                ),
                "post_signal_joint_tv_pp": total_variation_pp(
                    before[1].answer.joint.vector(), np.array(after[1].answer.joint.vector())
                ),
                "same_research_choice": same_query,
                "post_audit_joint_tv_pp": total_variation_pp(
                    before[2].answer.joint.vector(), np.array(after[2].answer.joint.vector())
                )
                if same_query
                else None,
            }
        )
    aggregates = {}
    for key in (
        "initial_joint_tv_pp",
        "signal_forecast_mean_absolute_difference_pp",
        "post_signal_joint_tv_pp",
        "post_audit_joint_tv_pp",
    ):
        values = [r[key] for r in rows if r[key] is not None]
        aggregates[key] = {
            "count": len(values),
            "incomparable": len(rows) - len(values),
            "mean": float(np.mean(values)) if values else None,
            "maximum": max(values) if values else None,
        }
    pairs = []
    for pair in sorted({a.pair_id for a in first.manifest.assignments}):
        group = [a for a in first.manifest.assignments if a.pair_id == pair]
        narrative = next(a for a in group if a.presentation == "narrative")
        facts = next(a for a in group if a.presentation == "facts")
        n = np.array(
            [r.cases[narrative.assignment_id][0].answer.joint.vector() for r in (first, repeat)]
        )
        f = np.array(
            [r.cases[facts.assignment_id][0].answer.joint.vector() for r in (first, repeat)]
        )
        pairs.append(
            {
                "pair_id": pair,
                "domain": narrative.domain,
                "direction": narrative.direction,
                "first_run_initial_format_tv_pp": total_variation_pp(n[0], f[0]),
                "repeat_run_initial_format_tv_pp": total_variation_pp(n[1], f[1]),
                "format_mean_initial_tv_pp": total_variation_pp(n.mean(axis=0), f.mean(axis=0)),
                "narrative_minus_facts_demand_pp_by_run": (100 * (n - f) @ DEMAND).tolist(),
                "narrative_minus_facts_artifact_pp_by_run": (100 * (n - f) @ ARTIFACT).tolist(),
            }
        )
    return {
        "schema_version": "epistemics.narrative-repeat-comparison.v1",
        "first_report_sha256": digest(first_bytes),
        "repeat_report_sha256": digest(repeat_bytes),
        "cases": rows,
        "repeat_distances": aggregates,
        "research_choice_agreement": {
            "matched": sum(r["same_research_choice"] for r in rows),
            "total": len(rows),
        },
        "presentation_comparisons": pairs,
        "mean_first_run_format_tv_pp": float(
            np.mean([p["first_run_initial_format_tv_pp"] for p in pairs])
        ),
        "mean_repeat_run_format_tv_pp": float(
            np.mean([p["repeat_run_initial_format_tv_pp"] for p in pairs])
        ),
        "mean_format_means_tv_pp": float(np.mean([p["format_mean_initial_tv_pp"] for p in pairs])),
        "limitations": [
            "Two observations per wording estimate limited within-format variability; they do not isolate a stable causal presentation effect.",
            "Requested model alias/revision labels and protocol match; provider revision and execution remain unverified. Compare operator configuration commitments separately.",
            "Post-audit comparisons require the same chosen audit; all early cases remain included.",
            "No significance threshold, general trait, empirical held-out predictive claim or intervention benefit.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Exact-wording narrative repeat comparison")
    parser.add_argument("--first-report", type=Path, required=True)
    parser.add_argument("--repeat-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = compare(args.first_report.read_bytes(), args.repeat_report.read_bytes())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        save(args.output, encoded(result))
        print(encoded(result).decode(), end="")
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
