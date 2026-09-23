"""Recovery gates are declared before running; no real-participant validation."""

import numpy as np

from epistemics.diagnostic.battery import schedule
from epistemics.diagnostic.inference import FAMILIES, GRID, PARAMETERS, SD, fit, predictions
from epistemics.investigation.inference import report_log_likelihood, simulate_reports

GENERATORS = {
    "association_only": (0.5, 1, 1),
    "selective_propagation": (1, 0.25, 1),
    "report_smoothing": (1, 1, 0.5),
    "combined": (1.25, 0.5, 0.75),
}
GATES = {"parameter_mae_max": 0.20, "heldout_family_accuracy_min": 0.75}


def recovery(seed=20260923, repetitions=32):
    from epistemics.diagnostic.service import fingerprint

    if repetitions < 1:
        raise ValueError("At least one repetition is required")
    rng = np.random.default_rng(seed)
    train, test = schedule(seed), schedule(seed + 1)
    errors, families, by_generator = [], [], {}
    for family, parameters in GENERATORS.items():
        family_errors = []
        for _ in range(repetitions):
            values = simulate_reports(predictions(train, parameters)[0], rng, sd=SD)
            fits = fit(values, train)
            estimate = [fits["full"]["parameters"][p] for p in PARAMETERS]
            errors.append(np.abs(np.array(parameters) - estimate))
            family_errors.append(errors[-1])
            # Competing restricted families fit development reports only. Score new reports
            # and independent noise under their fixed fitted parameters, without refitting.
            if family != "combined":
                future = simulate_reports(predictions(test, parameters)[0], rng, sd=SD)
                scores = {}
                for name in FAMILIES:
                    if name == "full":
                        continue
                    p = [fits[name]["parameters"][k] for k in PARAMETERS]
                    scores[name] = float(
                        report_log_likelihood(future, predictions(test, p)[0], sd=SD).sum()
                    )
                winner = max(scores, key=scores.get)
                # A nested-family tie is not recovery of a unique family.
                unique = sum(abs(v - scores[winner]) < 1e-8 for v in scores.values()) == 1
                families.append({"generator": family, "winner": winner, "unique": unique})
        by_generator[family] = dict(
            zip(PARAMETERS, np.mean(family_errors, axis=0).tolist(), strict=True)
        )
    mae = np.mean(errors, axis=0)
    # Association-only is nested in both other candidates and cannot be identified
    # by held-out likelihood alone. Report those ties, gate only distinct non-nested cases.
    distinct = [r for r in families if r["generator"] != "association_only"]
    accuracy = sum(r["winner"] == r["generator"] and r["unique"] for r in distinct) / len(distinct)
    degenerate = fit(predictions(train, (0, 1, 1))[0], train)["full"]
    return {
        "schema_version": "epistemics.auxiliary-recovery.v1",
        "implementation_sha256": fingerprint(),
        "seed": seed,
        "repetitions_per_generator": repetitions,
        "gates": GATES,
        "noise_logit_sd": SD,
        "parameter_mae": dict(zip(PARAMETERS, mae.tolist(), strict=True)),
        "parameter_mae_by_generator": by_generator,
        "distinct_family_accuracy": accuracy,
        "family_comparisons": families,
        "zero_association_propagation_unidentified": not degenerate[
            "propagation_identifiable_in_selected_model"
        ],
        "passed": bool(
            max(mae) <= GATES["parameter_mae_max"]
            and accuracy >= GATES["heldout_family_accuracy_min"]
        ),
        "scope": "Synthetic recovery under the declared models, fixed noise and archive templates; no empirical or cross-domain validation.",
        "grid_size": len(GRID),
    }
