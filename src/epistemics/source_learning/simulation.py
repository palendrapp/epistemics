"""Synthetic acceptance and recovery on coherent, naturally generated company reports."""

from collections import Counter

import numpy as np

from epistemics.source_inference.measurement import BLOCK_SD, INDEPENDENT_SD, sigmoid
from epistemics.source_inference.observers import FAMILIES
from epistemics.source_learning.battery import generate, location, public_trial
from epistemics.source_learning.inference import calibrate, forecast, raw_predictions
from epistemics.source_learning.models import Answer, Manifest
from epistemics.source_learning.service import SourceLearningService, create, export

PARTICIPANT = {
    "kind": "agent",
    "subject_id": "synthetic:source-learning",
    "configuration": {
        "model": "synthetic",
        "model_version": "source-learning/0.1.0",
        "configuration_sha256": "0" * 64,
    },
}
GATES = {
    "minimum_primary_pair_accuracy": 0.9,
    "maximum_joint_gain_mae": 0.15,
    "maximum_joint_heldout_latent_rmse_pp": 5.0,
}


def synthetic_answer(manifest, index, raw, family, gain, noise, query="stop"):
    c, stage = location(index)
    p = float(np.round(sigmoid(gain * raw[family]["logit"] + noise) * 100) / 100)
    return Answer(
        probability=p,
        decision="invest" if p > manifest.companies[c].threshold else "decline",
        query=query if stage == "research" else None,
        measurement_accuracy=round(raw[family]["measurement_accuracy"], 2)
        if manifest.condition == "dense" and stage != "revision"
        else None,
        random_selection_probability=round(raw[family]["random_selection_probability"], 2)
        if manifest.condition == "dense" and stage != "revision"
        else None,
    )


def simulate(directory, seed, condition="sparse", family="joint_process", gain=1.0):
    if family not in FAMILIES:
        raise ValueError("Unknown synthetic family")
    manifest = create(directory, PARTICIPANT, seed=seed, condition=condition, synthetic=True)
    service = SourceLearningService(directory)
    answers = []
    rng = np.random.default_rng(seed + 1701)
    offsets = rng.normal(0, BLOCK_SD, 24)
    for index in range(36):
        trial = service.get_trial()["trial"]
        c, _ = location(index)
        raw = raw_predictions(manifest, index, answers)
        query = ("customer_panel", "selection_audit", "measurement_audit", "stop")[c % 4]
        answer = synthetic_answer(
            manifest, index, raw, family, gain, offsets[c] + rng.normal(0, INDEPENDENT_SD), query
        )
        service.submit(trial["trial_id"], answer)
        answers.append(answer)
    service.finish()
    return export(directory)


def memory_manifest(seed):
    sources, archive, companies = generate(seed)
    return Manifest(
        study_id="synthetic-recovery",
        created_at="2026-09-25T00:00:00Z",
        design_seed=seed,
        implementation_sha256="0" * 64,
        participant=PARTICIPANT,
        response_origin="synthetic",
        condition="sparse",
        condition_assignment="operator_selected",
        sources=sources,
        archive=archive,
        companies=companies,
    )


def recovery(seed, repetitions=32):
    if repetitions < 1:
        raise ValueError("At least one repetition required")
    rng = np.random.default_rng(seed)
    confusion = {f: Counter() for f in FAMILIES}
    decisive = {f: Counter() for f in FAMILIES}
    pair = {f: 0 for f in FAMILIES[:2]}
    gains, errors = {f: [] for f in FAMILIES}, {f: [] for f in FAMILIES}
    for repetition in range(repetitions):
        manifest = memory_manifest(seed + 1000 + repetition)
        gain = (0.83, 1.0, 1.17)[repetition % 3]
        for family in FAMILIES:
            answers, locks, predicted, targets = [], [], [], []
            offsets = rng.normal(0, BLOCK_SD, 24)
            frozen = None
            for index in range(36):
                c, _ = location(index)
                raw = raw_predictions(manifest, index, answers)
                locks.append({"raw": raw})
                if index == 12:
                    frozen = calibrate(locks[:12], answers)
                    confusion[family][frozen["best_family"]] += 1
                    decisive[family][frozen["decision"]] += 1
                    gains[family].append(abs(frozen["families"][family]["best_gain"] - gain))
                    if family in pair:
                        other = FAMILIES[1 - FAMILIES.index(family)]
                        pair[family] += (
                            frozen["families"][family]["log_marginal_likelihood"]
                            > frozen["families"][other]["log_marginal_likelihood"] + 1e-9
                        )
                if frozen is not None:
                    predicted.append(forecast(raw, frozen)["family_means"][family])
                    targets.append(float(sigmoid(gain * raw[family]["logit"])))
                query = ("customer_panel", "selection_audit", "measurement_audit", "stop")[
                    (c + repetition) % 4
                ]
                answer = synthetic_answer(
                    manifest,
                    index,
                    raw,
                    family,
                    gain,
                    offsets[c] + rng.normal(0, INDEPENDENT_SD),
                    query,
                )
                answer.validate_trial(public_trial(manifest, index, answers))
                answers.append(answer)
            errors[family].append(
                float(100 * np.sqrt(np.mean((np.array(predicted) - targets) ** 2)))
            )
    metrics = {
        "primary_pair_accuracy": {f: n / repetitions for f, n in pair.items()},
        "gain_mae_given_family": {f: float(np.mean(v)) for f, v in gains.items()},
        "heldout_latent_rmse_pp_given_family": {f: float(np.mean(v)) for f, v in errors.items()},
    }
    checks = {
        "primary_pair": min(metrics["primary_pair_accuracy"].values())
        >= GATES["minimum_primary_pair_accuracy"],
        "joint_gain": metrics["gain_mae_given_family"]["joint_process"]
        <= GATES["maximum_joint_gain_mae"],
        "joint_prediction": metrics["heldout_latent_rmse_pp_given_family"]["joint_process"]
        <= GATES["maximum_joint_heldout_latent_rmse_pp"],
    }
    return {
        "schema_version": "epistemics.source-learning-recovery.v1",
        "response_origin": "synthetic",
        "seed": seed,
        "repetitions_per_family": repetitions,
        "datasets": repetitions * 3,
        "gates": GATES,
        "checks": checks,
        "passed": all(checks.values()),
        "best_family_confusion": {f: dict(v) for f, v in confusion.items()},
        "decisive_confusion": {f: dict(v) for f, v in decisive.items()},
        **metrics,
        "scope": "Coherent public histories, natural company reports, off-grid reporting gain and company-correlated noise; query branches rotate exogenously, not recovered choice policies",
    }
