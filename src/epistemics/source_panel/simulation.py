"""Calibration-pool recovery and excluded-process checks before a real panel."""

from types import SimpleNamespace

import numpy as np

from epistemics.source_inference.measurement import BLOCK_SD, INDEPENDENT_SD, sigmoid
from epistemics.source_inference.observers import FAMILIES
from epistemics.source_learning.inference import forecast, raw_predictions
from epistemics.source_learning.simulation import memory_manifest, synthetic_answer
from epistemics.source_learning.storage import digest, encoded
from epistemics.source_panel.analysis import adequacy, rmse
from epistemics.source_panel.profiles import fit_profile

GATES = {
    "minimum_family_recovery": 0.9,
    "maximum_gain_mae": 0.15,
    "maximum_new_world_latent_rmse_pp": 5.0,
}


def calibration(seed, context, family, gain, rng):
    manifest = memory_manifest(seed)
    manifest.study_id = context
    answers, observations, locks = [], [], []
    for i in range(12):
        raw = raw_predictions(manifest, i, answers)
        noise = rng.normal(0, BLOCK_SD) + rng.normal(0, INDEPENDENT_SD)
        answer = synthetic_answer(manifest, i, raw, family, gain, noise)
        answers.append(answer)
        observations.append(
            SimpleNamespace(answer=answer, trial=SimpleNamespace(company_id=f"company-{i + 1:02d}"))
        )
        locks.append({"raw": raw})
    return SimpleNamespace(
        manifest=manifest,
        manifest_sha256=digest(encoded(manifest)),
        observations=observations,
        prediction_locks=locks,
    )


def recovery(seed, repetitions=8):
    rng = np.random.default_rng(seed)
    rows = []
    for repetition in range(repetitions):
        gain = (0.83, 1.0, 1.17)[repetition % 3]
        for family in FAMILIES:
            train = [
                calibration(
                    seed + repetition * 3 + w, f"{family}-{repetition}-{w}-{r}", family, gain, rng
                )
                for w in range(2)
                for r in range(2)
            ]
            profile = fit_profile(train)
            target = calibration(
                seed + repetition * 3 + 2, f"target-{family}-{repetition}", family, gain, rng
            )
            raw = [r["raw"] for r in target.prediction_locks]
            latent = [float(sigmoid(gain * r[family]["logit"])) for r in raw]
            predicted = [forecast(r, profile)["mixture_mean"] for r in raw]
            rows.append(
                {
                    "family": family,
                    "selected": profile["decision"],
                    "gain_error": abs(profile["families"][family]["best_gain"] - gain),
                    "new_world_latent_rmse_pp": rmse(latent, predicted),
                }
            )
    metrics = {
        family: {
            "family_recovery": float(
                np.mean([r["selected"] == family for r in rows if r["family"] == family])
            ),
            "gain_mae": float(np.mean([r["gain_error"] for r in rows if r["family"] == family])),
            "new_world_latent_rmse_pp": float(
                np.mean([r["new_world_latent_rmse_pp"] for r in rows if r["family"] == family])
            ),
        }
        for family in FAMILIES
    }
    reverse = [round(1 - p, 2) for p in latent]
    failures = adequacy(raw, reverse, profile, seed=seed)
    checks = {
        "family_recovery": all(
            m["family_recovery"] >= GATES["minimum_family_recovery"] for m in metrics.values()
        ),
        "gain": all(m["gain_mae"] <= GATES["maximum_gain_mae"] for m in metrics.values()),
        "prediction": all(
            m["new_world_latent_rmse_pp"] <= GATES["maximum_new_world_latent_rmse_pp"]
            for m in metrics.values()
        ),
        "excluded_direction_reversal": all(r["outside_boundary"] for r in failures.values()),
    }
    return {
        "response_origin": "synthetic",
        "seed": seed,
        "repetitions_per_family": repetitions,
        "datasets": repetitions * len(FAMILIES),
        "gates": GATES,
        "metrics": metrics,
        "checks": checks,
        "passed": all(checks.values()),
        "scope": "Four calibration contexts across two shared training worlds per dataset, one fresh target world; matched generating families/noise, no simulated presentation or elicitation effect",
    }
