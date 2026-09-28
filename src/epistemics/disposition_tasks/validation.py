"""Pipeline validation bound to the implementation fingerprint.

Passing requires every rendered case in every variant to display its design's probabilities,
the two-way sentence exactly in the paired variant, no private labels in public checkpoints,
and recovery of known parameters from complete synthetic collections through the real service:
every module and cover in the paired variant, every other variant in the markets cover, and a
learning respondent in both learning variants. It validates measurement machinery, not any
respondent.
"""

import json
import tempfile
from pathlib import Path

import numpy as np

from epistemics.disposition_tasks.collection import CASES, fingerprint, load_report, public_trial
from epistemics.disposition_tasks.render import (
    COVERS,
    CUE_MODULES,
    CUE_VARIANTS,
    DOSSIER_MODULES,
    DOSSIER_VARIANTS,
    LEARNING_RATES,
    MODULES,
    RANGE_MODULES,
    RANGE_VARIANTS,
    UNPROMPTED_MODULES,
    VARIANTS,
    items_for,
    render,
    stated_percentages,
)
from epistemics.disposition_tasks.simulation import simulate

TOLERANCE = {"disposition": 0.15, "certainty_value": 15.0, "start": 0.15, "cue": 0.15}
REPORT_TRUTHS = [
    {"disposition": 0.15, "gamma": 0.9, "bias": 0.1, "report_sd": 0.15},
    {"disposition": 0.5, "gamma": 1.1, "bias": -0.1, "report_sd": 0.15},
    {"disposition": 0.85, "gamma": 1.0, "bias": 0.0, "report_sd": 0.15},
]
CHECK_TRUTHS = [
    {"function": "linear", "certainty_value": 0.0, "decision_weight": 1.0, "wtp_sd": 3.0},
    {"function": "linear", "certainty_value": 50.0, "decision_weight": 0.9, "wtp_sd": 3.0},
    {"function": "entropy", "certainty_value": 100.0, "decision_weight": 1.1, "wtp_sd": 3.0},
]
# A learner starting at indifference. Strength 8 keeps the start identifiable (the recovery
# study scores the start only from strength 8) while learning remains detectable.
LEARNER = {"start": 0.5, "strength": 8.0, "gamma": 1.0, "bias": 0.0, "report_sd": 0.1}
CUE_RESPONDENT = {"slots": [0.1, 0.3, 0.5, 0.7, 0.9], "gamma": 1.0, "bias": 0.0, "report_sd": 0.15}
# A relative judge: targets sit higher among well-staffed outlets than among aggregators.
RANGE_RESPONDENTS = {
    "range-reassuring": {
        "slots": [0.45, 0.5, 0.55, 0.7, 0.75, 0.05, 0.05, 0.1],
        "gamma": 1.0,
        "bias": 0.0,
        "report_sd": 0.15,
    },
    "range-suggestive": {
        "slots": [0.2, 0.25, 0.4, 0.45, 0.5, 0.9, 0.95, 0.9],
        "gamma": 1.0,
        "bias": 0.0,
        "report_sd": 0.15,
    },
}
PRIVATE = (
    "disposition",
    "probe",
    "delta",
    "sigma",
    "gamma",
    "discount",
    "skepticism",
    "entropy",
    "certainty",
    "selective",
    "prior that",
    "item",
    "variant",
    "suggestive",
    "reassuring",
)
TWO_WAY = (" may have ", "could be either kind")
# Unprompted dossiers must not name or describe relaying or selective withholding.
MECHANISM = (
    "relay",
    "withh",
    "selective",
    "repeat",
    "copies",
    "copied",
    "for itself",
    "for themselves",
    "at random",
    "on purpose",
    "strategic",
)


def variants_of(module):
    if module in CUE_MODULES:
        return CUE_VARIANTS
    if module in RANGE_MODULES:
        return RANGE_VARIANTS
    if module in DOSSIER_MODULES + UNPROMPTED_MODULES:
        return DOSSIER_VARIANTS
    return ("paired",) if module == "checks" else VARIANTS


def covers_of(module):
    return (
        ("markets",)
        if module in CUE_MODULES + RANGE_MODULES + DOSSIER_MODULES + UNPROMPTED_MODULES
        else COVERS
    )


def audit():
    """Rendering audit over every module, cover, variant and item."""
    count = 0
    for module in MODULES:
        kinds = items_for(module).get("kind")
        for cover in covers_of(module):
            for variant in variants_of(module):
                cases = [render(module, cover, i, variant) for i in range(CASES)]
                if len({c["case"] for c in cases}) != CASES:
                    raise ValueError(f"Duplicate case text in {module}/{cover}/{variant}")
                for i, case in enumerate(cases):
                    where = f"{module}/{cover}/{variant}/{i}"
                    for p in stated_percentages(module, i):
                        if p not in case["case"]:
                            raise ValueError(f"{where} does not display {p}")
                    if any(word in json.dumps(case).lower() for word in PRIVATE):
                        raise ValueError(f"{where} shows a private label")
                    if module in UNPROMPTED_MODULES and any(
                        word in json.dumps(case).lower() for word in MECHANISM
                    ):
                        raise ValueError(f"{where} states the mechanism")
                    if module != "checks" and kinds[i] != "single":
                        two_way = any(phrase in case["case"] for phrase in TWO_WAY)
                        if two_way != (variant == "paired"):
                            raise ValueError(f"{where} has the wrong framing")
                count += CASES
    return {"modules": len(MODULES), "covers": len(COVERS), "cases": count}


def contexts_to_validate():
    for module in CUE_MODULES:
        for variant in CUE_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in RANGE_MODULES:
        for variant in RANGE_VARIANTS:
            yield module, "markets", variant, RANGE_RESPONDENTS[variant]
    for module in DOSSIER_MODULES:
        for variant in DOSSIER_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in ("corroboration", "disclosure", "checks"):
        truths = CHECK_TRUTHS if module == "checks" else REPORT_TRUTHS
        for cover in COVERS:
            for truth in truths:
                yield module, cover, "paired", truth
        if module == "checks":
            continue
        for variant in ("open", "suggestive", "reassuring"):
            yield module, "markets", variant, REPORT_TRUTHS[0]
        for variant in LEARNING_RATES:
            yield module, "markets", variant, LEARNER
    # Appended last, so earlier contexts keep the random draws of earlier battery versions.
    for module in UNPROMPTED_MODULES:
        for variant in DOSSIER_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT


def estimate(module, analysis, truth):
    if module == "checks":
        row = analysis["fits"][truth["function"]]["parameters"]["certainty_value"]
        error = abs(row["mean"] - truth["certainty_value"])
        return row["mean"], error <= TOLERANCE["certainty_value"]
    if "slots" in truth:
        if "range" in analysis:
            summary = analysis["range"]
            implied = summary["targets_implied"] + summary["comparisons_implied"]
        else:
            implied = analysis["cues"]["implied"]
        error = max(abs(a - b) for a, b in zip(implied, truth["slots"], strict=True))
        return error, error <= TOLERANCE["cue"]
    if "strength" in truth:
        learning = analysis["learning"]
        row = learning["parameters"]["start"]
        # As in the recovery study, learning must be detected only where it is visible: when the
        # revealed rate differs from the starting value by at least 0.25.
        visible = abs(analysis["revealed_rate"] - truth["start"]) >= 0.25
        detected = learning["learning_probability"] > 0.5 or not visible
        # How well one context pins the start depends on its order (how many informative cases
        # precede the reveals), so the check is coverage by the 90% interval, widened by half a
        # grid step, rather than a fixed tolerance on the posterior mean.
        low, high = row["interval_90"]
        covered = low - 0.025 <= truth["start"] <= high + 0.025
        return row["mean"], detected and covered
    row = analysis["fit"]["parameters"]["disposition"]
    return row["mean"], abs(row["mean"] - truth["disposition"]) <= TOLERANCE["disposition"]


def validate(seed):
    audited = audit()
    rng = np.random.default_rng(seed)
    contexts = []
    with tempfile.TemporaryDirectory() as tmp:
        for n, (module, cover, variant, truth) in enumerate(contexts_to_validate()):
            directory = Path(tmp) / f"{n:02d}-{module}-{cover}-{variant}"
            order = rng.permutation(CASES).tolist()
            report = simulate(
                directory,
                module=module,
                cover=cover,
                order=order,
                truth=truth,
                seed=int(rng.integers(2**31)),
                variant=variant,
                reveal_seed=int(rng.integers(2**31)) if variant in LEARNING_RATES else None,
            )
            reloaded = load_report(directory)
            shown = [public_trial(reloaded.manifest, i) for i in range(CASES)]
            value, recovered = estimate(module, report.analysis, truth)
            contexts.append(
                {
                    "module": module,
                    "cover": cover,
                    "variant": variant,
                    "truth": truth,
                    "estimate": value,
                    "recovered": recovered,
                    "reloaded": reloaded == report
                    and [o.trial for o in report.observations] == shown,
                    "reveals_shown": sum("previous_case" in t for t in shown),
                }
            )
    reveals = all(
        c["reveals_shown"] == (CASES - 1 if c["variant"] in LEARNING_RATES else 0) for c in contexts
    )
    return {
        "schema_version": "epistemics.disposition-task-validation.v5",
        "seed": seed,
        "implementation_sha256": fingerprint(),
        "audit": audited,
        "tolerance": TOLERANCE,
        "contexts": contexts,
        "passed": reveals and all(c["recovered"] and c["reloaded"] for c in contexts),
        "scope": "Rendering audit and complete synthetic collections through the service at low report noise; no respondent behavior is validated",
    }
