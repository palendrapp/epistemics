"""Pipeline validation bound to the implementation fingerprint.

Passing requires every rendered case to display its design's probabilities, distinct names
within each module and cover, no private labels in public checkpoints, and recovery of known
parameters from complete synthetic collections through the real service in every module and
cover. It validates measurement machinery, not any respondent.
"""

import json
import tempfile
from pathlib import Path

import numpy as np

from epistemics.disposition_tasks.collection import CASES, fingerprint, load_report, public_trial
from epistemics.disposition_tasks.render import (
    COVERS,
    MODULES,
    render,
    stated_percentages,
)
from epistemics.disposition_tasks.simulation import simulate

TOLERANCE = {"disposition": 0.15, "certainty_value": 15.0}
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
)


def audit():
    """Rendering audit over every module, cover and item."""
    for module in MODULES:
        for cover in COVERS:
            cases = [render(module, cover, i) for i in range(CASES)]
            texts = [c["case"] for c in cases]
            if len(set(texts)) != CASES:
                raise ValueError(f"Duplicate case text in {module}/{cover}")
            subjects = [t.split(" ")[0:2] for t in texts]
            if module != "checks" and len({tuple(s) for s in subjects}) != CASES:
                raise ValueError(f"Case subjects repeat in {module}/{cover}")
            for i, case in enumerate(cases):
                for p in stated_percentages(module, i):
                    if p not in case["case"]:
                        raise ValueError(f"{module}/{cover}/{i} does not display {p}")
                shown = json.dumps(case).lower()
                if any(word in shown for word in PRIVATE):
                    raise ValueError(f"{module}/{cover}/{i} shows a private label")
    return {
        "modules": len(MODULES),
        "covers": len(COVERS),
        "cases": len(MODULES) * len(COVERS) * CASES,
    }


def estimate(module, analysis, truth):
    if module == "checks":
        row = analysis["fits"][truth["function"]]["parameters"]["certainty_value"]
        return row["mean"], abs(row["mean"] - truth["certainty_value"]) <= TOLERANCE[
            "certainty_value"
        ]
    row = analysis["fit"]["parameters"]["disposition"]
    return row["mean"], abs(row["mean"] - truth["disposition"]) <= TOLERANCE["disposition"]


def validate(seed):
    audited = audit()
    rng = np.random.default_rng(seed)
    contexts = []
    with tempfile.TemporaryDirectory() as tmp:
        for module in MODULES:
            truths = CHECK_TRUTHS if module == "checks" else REPORT_TRUTHS
            for cover in COVERS:
                for t, truth in enumerate(truths):
                    directory = Path(tmp) / f"{module}-{cover}-{t}"
                    order = rng.permutation(CASES).tolist()
                    report = simulate(
                        directory,
                        module=module,
                        cover=cover,
                        order=order,
                        truth=truth,
                        seed=int(rng.integers(2**31)),
                    )
                    reloaded = load_report(directory)
                    shown = [public_trial(reloaded.manifest, i) for i in range(CASES)]
                    value, recovered = estimate(module, report.analysis, truth)
                    contexts.append(
                        {
                            "module": module,
                            "cover": cover,
                            "truth": truth,
                            "estimate": value,
                            "recovered": recovered,
                            "reloaded": reloaded == report
                            and [o.trial for o in report.observations] == shown,
                            "preferred_model": (
                                report.analysis["certainty_function"]["preferred"]
                                if module == "checks"
                                else report.analysis["model_comparison"]["preferred"]
                            ),
                        }
                    )
    return {
        "schema_version": "epistemics.disposition-task-validation.v1",
        "seed": seed,
        "implementation_sha256": fingerprint(),
        "audit": audited,
        "tolerance": TOLERANCE,
        "contexts": contexts,
        "passed": all(c["recovered"] and c["reloaded"] for c in contexts),
        "scope": "Rendering audit and complete synthetic collections through the service at low report noise; no respondent behavior is validated",
    }
