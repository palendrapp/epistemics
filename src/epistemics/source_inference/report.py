"""Reproducible, explicitly synthetic design artifacts."""

import hashlib
import importlib.metadata
from pathlib import Path

from epistemics.source_inference import ANALYSIS_VERSION, DESIGN_VERSION, WORLD_VERSION
from epistemics.source_inference.design import (
    choose_design,
    encoded,
    policy_contrasts,
    predictions,
    probe_id,
    worked_example,
)
from epistemics.source_inference.measurement import BLOCK_SD, GAINS, INDEPENDENT_SD
from epistemics.source_inference.observers import ACCURACIES, FAMILIES, source_summary
from epistemics.source_inference.validation import (
    GATES,
    GENERATING_GAINS,
    check_gates,
    controls,
    experiment,
)
from epistemics.source_inference.world import RANDOM, RULES, archive, render, sources


def fingerprint():
    payload = {
        "files": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))
        },
        "dependencies": {name: importlib.metadata.version(name) for name in ("numpy", "pydantic")},
    }
    return hashlib.sha256(encoded(payload)).hexdigest()


def run(directory: Path, seed=20260925, repetitions=32):
    if repetitions < 1 or not 0 <= seed < 2**32 - 10:
        raise ValueError("Use a nonnegative seed below 2**32-10 and at least one repetition")
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("Use an empty output directory; existing design artifacts are immutable")
    directory.mkdir(parents=True, exist_ok=True)
    commitments = {}

    def save(name, value):
        raw = encoded(value)
        with (directory / name).open("xb") as stream:
            stream.write(raw)
        commitments[name] = hashlib.sha256(raw).hexdigest()

    plan = {
        "schema_version": "epistemics.source-design-plan.v1",
        "world_version": WORLD_VERSION,
        "design_version": DESIGN_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "implementation_sha256": fingerprint(),
        "seeds": {
            "design_history": seed,
            "calibration_history": seed + 1,
            "heldout_history": seed + 2,
            "design_selection": seed + 3,
            "responses": seed + 4,
            "controls": seed + 5,
            "stress": seed + 6,
        },
        "repetitions_per_family": repetitions,
        "public_archive_rows_per_source": 12,
        "source_ids": [s.source_id for s in sources()],
        "source_accuracy_support": ACCURACIES,
        "source_rule_support": [r.model_dump() for r in RULES],
        "source_prior": "Uniform over each family's finite source-state support",
        "families": FAMILIES,
        "fitted_response_gain_grid": GAINS.tolist(),
        "generating_response_gains": GENERATING_GAINS,
        "report_model": {
            "independent_logit_sd": INDEPENDENT_SD,
            "source_block_logit_sd": BLOCK_SD,
            "rounding": 0.01,
            "block_integration": "15-point Gauss-Hermite quadrature",
            "stress_independent_logit_sd": 0.4,
        },
        "gates": GATES,
        "design": "Two fixed anchors and two information-ranked probes per source; matched-random comparator shares anchors; 32 disjoint heldout templates",
        "scope": "Offline synthetic design only; no active participant battery, agent run or passport trait",
    }
    # Record the specification before generating worlds, choosing probes or drawing responses.
    save("plan.json", plan)
    private = {
        name: archive(plan["seeds"][name])
        for name in ("design_history", "calibration_history", "heldout_history")
    }
    public = {name: tuple(row.public for row in rows) for name, rows in private.items()}
    design = choose_design(public["design_history"], plan["seeds"]["design_selection"])
    probes = design["probes"]
    heldout_probes = tuple(probes[i] for i in design["indices"]["heldout"])
    save(
        "private-worlds.json",
        {name: [r.model_dump(mode="json") for r in rows] for name, rows in private.items()},
    )
    save(
        "public-inputs.json",
        {
            "histories": {
                name: [r.model_dump(mode="json") for r in rows] for name, rows in public.items()
            },
            "probes": [
                {"probe_id": probe_id(p), "probe": p.model_dump(mode="json"), "document": render(p)}
                for p in probes
            ],
            "chosen_indices": design["indices"],
            "candidate_marginal_information_bits": design["candidate_information"],
        },
    )
    calibration = predictions(public["calibration_history"], probes)
    heldout = predictions(public["heldout_history"], heldout_probes)
    blocks = [p.source_id for p in probes]
    heldout_blocks = [p.source_id for p in heldout_probes]
    selection = {name: design["indices"][name] for name in ("diagnostic", "matched_random")}
    save(
        "prediction-lock.json",
        {
            "families": FAMILIES,
            "calibration_logits": calibration.tolist(),
            "heldout_logits": heldout.tolist(),
            "calibration_blocks": blocks,
            "heldout_blocks": heldout_blocks,
            "selected_indices": selection,
            "meaning": "Public-history predictions for every fitted gain are locked before synthetic reports are sampled",
        },
    )
    baseline = experiment(
        calibration,
        heldout,
        blocks,
        heldout_blocks,
        selection,
        repetitions,
        plan["seeds"]["responses"],
    )
    stress = experiment(
        calibration,
        heldout,
        blocks,
        heldout_blocks,
        selection,
        repetitions,
        plan["seeds"]["stress"],
        independent_sd=0.4,
    )
    checks = controls(
        calibration,
        heldout,
        blocks,
        heldout_blocks,
        selection["diagnostic"],
        plan["seeds"]["controls"],
        [
            i
            for i, p in enumerate(probes)
            if p.disclosed_rule == RANDOM and p.prior_strong == 0.5 and p.count in (2, 4)
        ],
    )
    result = {
        "schema_version": "epistemics.source-design-report.v1",
        "world_version": WORLD_VERSION,
        "design_version": DESIGN_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "implementation_sha256": plan["implementation_sha256"],
        "response_origin": "synthetic",
        "participant_collection_ready": False,
        "empirical_predictive_validation": False,
        "model_parameters_are_passport_traits": False,
        "plan": plan,
        "artifact_sha256": dict(commitments),
        "candidate_probes": len(probes),
        "selected_probes": design["summaries"],
        "design_method": design["method"],
        "worked_example": worked_example(),
        "source_learning": [
            {
                "evaluator_only_process": s.model_dump(mode="json"),
                "learned_from_public_design_archive": {
                    f: source_summary(public["design_history"], s.source_id, f)
                    for f in FAMILIES[:2]
                },
            }
            for s in sources()
        ],
        "baseline": baseline,
        "higher_noise": stress,
        "controls": checks,
        "gates": check_gates(baseline, checks),
        "research_policy_contrasts": policy_contrasts(
            public["design_history"], [probes[i] for i in selection["diagnostic"]]
        ),
        "limitations": [
            "Source processes are learned; business expansion rates are disclosed controls, not learned business semantics.",
            "Finite observer supports include the generating source processes; model recovery is under specified synthetic response families.",
            "Response gain is a reporting nuisance parameter, not an evidence-weight trait.",
            "Source-selection audits are known diagnostic conditions; unlikely audit/history combinations are intentionally included.",
            "Model probabilities condition on candidate families, priors, noise and gain support. Their maximum need not be adequate.",
            "Diagnostic counts and source outcomes are deliberately balanced; this is not a calibration or investment-return sample.",
            "The fixed-discount foil intentionally ignores history and selection audits; it is not a complete alternative theory.",
            "The high-noise condition matches the inference noise specification; unmodeled noise robustness is untested.",
            "Online adaptation, source labels, drift, free hypothesis discovery, human usability, live MCP collection and support benefit are pending.",
        ],
    }
    save("report.json", result)
    markdown = render_report(result, commitments["report.json"])
    with (directory / "report.md").open("x") as stream:
        stream.write(markdown)
    return result


def render_report(result, report_digest):
    baseline = result["baseline"]["designs"]["diagnostic"]
    lines = [
        "# Source-inference design validation",
        "",
        "**Synthetic design results. No agents or humans were evaluated.**",
        "",
        f"Seed: {result['plan']['seeds']['design_history']}. Development screens passed: **{result['gates']['passed']}**.",
        f"{result['candidate_probes']} candidate probes; {len(result['selected_probes'])} selected; 32 heldout templates with fresh public histories.",
        "",
        "## Exact selection example",
        "",
        "Known perfect measurement, 70%/30% customer expansion, equal prior, exactly four of five customers expanding.",
        "",
        "| Sampling rule | Likelihood ratio | P(strong demand) |",
        "| --- | ---: | ---: |",
    ]
    for row in result["worked_example"]:
        lines.append(
            f"| {row['rule']['direction']} of {row['rule']['panels']} | {row['likelihood_ratio']:.3f} | {100 * row['posterior_strong']:.2f}% |"
        )
    lines += [
        "",
        "## Model discrimination",
        "",
        "Each row uses fresh simulated reports. Columns count the best family; this table alone does not establish adequacy.",
        "",
        "| Generating family | Joint process | Flat accuracy | Fixed discount | Ambiguous at 0.8 threshold |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for family in FAMILIES:
        counts = baseline["best_family_confusion"][family]
        ambiguous = baseline["decisive_confusion"][family].get("ambiguous", 0)
        lines.append(
            f"| {family} | {counts.get(FAMILIES[0], 0)} | {counts.get(FAMILIES[1], 0)} | {counts.get(FAMILIES[2], 0)} | {ambiguous} |"
        )
    lines += [
        "",
        "| Design / noise | Joint vs flat: joint correct | Joint vs flat: flat correct |",
        "| --- | ---: | ---: |",
    ]
    for regime in ("baseline", "higher_noise"):
        for name, row in result[regime]["designs"].items():
            a = row["primary_pair_accuracy"]
            lines.append(
                f"| {name} / {regime} | {a['joint_process']:.1%} | {a['flat_accuracy']:.1%} |"
            )
    lines += [
        "",
        "## Reporting-parameter recovery and new-input prediction",
        "",
        "Fits use calibration reports; predictions use new public histories and disjoint templates. Targets are noiseless synthetic response means.",
        "",
        "| Generating family | Gain MAE, given family | New-input RMSE, given family (points) | New-input RMSE, selected family (points) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for family in FAMILIES:
        row = baseline["conditional_on_generating_family"][family]
        selected = baseline["selected_family_new_input_latent_rmse_pp"][family]
        lines.append(
            f"| {family} | {row['gain_mae']:.3f} | {row['new_input_latent_rmse_pp']:.3f} | {selected:.3f} |"
        )
    lines += [
        "",
        "## Failure controls",
        "",
        f"Neutral evidence: **{result['controls']['neutral_control']['decision']}**, with all response gains tied.",
        "Once a random-sampling audit is supplied, the joint and flat observers give identical forecasts and equal model evidence, even for informative company observations.",
        f"Excluded reversal process: all candidates outside their conditional heldout simulation envelope: **{result['controls']['direction_reversal']['all_candidates_inadequate']}**.",
        "",
        "## Research policy contrasts",
        "",
    ]
    policy = result["research_policy_contrasts"]
    lines.append(
        f"Across {policy['cases']} price/threshold contrasts, decision value and company-information policies have disjoint optimal choices in {policy['decision_and_company_information_disagree']} cases."
    )
    lines += [
        "",
        "These are computed policy predictions, not collected agent decisions.",
        "",
        "## Limits",
        "",
    ] + [f"- {limitation}" for limitation in result["limitations"]]
    lines += [
        "",
        "## Commitments",
        "",
        f"Exact report SHA-256: `{report_digest}`",
        "",
        f"Implementation: `{result['implementation_sha256']}`",
        "",
    ]
    for name, value in result["artifact_sha256"].items():
        lines.append(f"- {name}: `{value}`")
    return "\n".join(lines) + "\n"
