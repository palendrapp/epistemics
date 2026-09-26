"""Recovery under all three assigned policies; language/verification benefit is not simulated."""

from collections import Counter

import numpy as np

from epistemics.source_inference.measurement import BLOCK_SD, INDEPENDENT_SD, sigmoid
from epistemics.source_inference.observers import FAMILIES
from epistemics.source_learning.battery import location, public_trial
from epistemics.source_learning.inference import calibrate, forecast, raw_predictions
from epistemics.source_learning.simulation import (
    GATES,
    PARTICIPANT,
    memory_manifest,
    synthetic_answer,
)
from epistemics.source_selective.policy import POLICIES, choose, offers, price_for
from epistemics.source_selective.service import VerificationService, create, fingerprint


def simulate(directory, seed, policy, family="joint_process", gain=1.0):
    manifest = create(
        directory, PARTICIPANT, seed=seed, policy=policy, price_seed=seed + 200000, synthetic=True
    )
    service = VerificationService(directory)
    answers = []
    for i in range(36):
        trial = service.get_trial()["trial"]
        answer = synthetic_answer(
            manifest, i, raw_predictions(manifest, i, answers), family, gain, 0, "stop"
        )
        if i >= 12 and i % 2 == 0:
            answer = answer.model_copy(
                update={
                    "query": choose(
                        policy,
                        answer.probability,
                        trial["decision_threshold"],
                        price_for(service.binding, trial["company_id"]),
                    )
                }
            )
        service.submit(trial["trial_id"], answer.model_dump(include={"probability", "decision"}))
        answers.append(answer)
    service.finish()
    return service.evidence()


def recovery(seed, repetitions=32):
    if repetitions < 1:
        raise ValueError("At least one repetition required")
    policies = {}
    for policy in POLICIES:
        rng = np.random.default_rng(seed)
        query_counts = Counter()
        confusion = {f: Counter() for f in FAMILIES}
        gains, errors = {f: [] for f in FAMILIES}, {f: [] for f in FAMILIES}
        pairs = {f: 0 for f in FAMILIES[:2]}
        for repetition in range(repetitions):
            manifest = memory_manifest(seed + 1000 + repetition)
            binding = {"offers": offers(manifest, seed + 200000 + repetition)}
            gain = (0.83, 1.0, 1.17)[repetition % 3]
            for family in FAMILIES:
                answers, locks, predicted, targets = [], [], [], []
                offsets = rng.normal(0, BLOCK_SD, 24)
                frozen = None
                for i in range(36):
                    c, _ = location(i)
                    raw = raw_predictions(manifest, i, answers)
                    locks.append({"raw": raw})
                    if i == 12:
                        frozen = calibrate(locks[:12], answers)
                        confusion[family][frozen["best_family"]] += 1
                        gains[family].append(abs(frozen["families"][family]["best_gain"] - gain))
                        if family in pairs:
                            other = FAMILIES[1 - FAMILIES.index(family)]
                            pairs[family] += (
                                frozen["families"][family]["log_marginal_likelihood"]
                                > frozen["families"][other]["log_marginal_likelihood"] + 1e-9
                            )
                    if frozen is not None:
                        predicted.append(forecast(raw, frozen)["family_means"][family])
                        targets.append(float(sigmoid(gain * raw[family]["logit"])))
                    answer = synthetic_answer(
                        manifest,
                        i,
                        raw,
                        family,
                        gain,
                        offsets[c] + rng.normal(0, INDEPENDENT_SD),
                        "stop",
                    )
                    if i >= 12 and i % 2 == 0:
                        company = manifest.companies[c]
                        answer = answer.model_copy(
                            update={
                                "query": choose(
                                    policy,
                                    answer.probability,
                                    company.threshold,
                                    price_for(binding, company.company_id),
                                )
                            }
                        )
                    if i >= 12 and i % 2 == 0:
                        query_counts[answer.query] += 1
                    answer.validate_trial(public_trial(manifest, i, answers))
                    answers.append(answer)
                errors[family].append(
                    float(100 * np.sqrt(np.mean((np.array(predicted) - targets) ** 2)))
                )
        results = {
            "assigned_check_counts": dict(query_counts),
            "primary_pair_accuracy": {f: n / repetitions for f, n in pairs.items()},
            "gain_mae_given_family": {f: float(np.mean(v)) for f, v in gains.items()},
            "heldout_latent_rmse_pp_given_family": {
                f: float(np.mean(v)) for f, v in errors.items()
            },
            "best_family_confusion": {f: dict(v) for f, v in confusion.items()},
        }
        results["passed"] = bool(
            (policy != "cost_aware" or set(query_counts) == {"stop", "customer_panel"})
            and min(results["primary_pair_accuracy"].values())
            >= GATES["minimum_primary_pair_accuracy"]
            and results["gain_mae_given_family"]["joint_process"] <= GATES["maximum_joint_gain_mae"]
            and results["heldout_latent_rmse_pp_given_family"]["joint_process"]
            <= GATES["maximum_joint_heldout_latent_rmse_pp"]
        )
        policies[policy] = results
    return {
        "schema_version": "epistemics.source-selective-recovery.v1",
        "seed": seed,
        "repetitions_per_family_per_policy": repetitions,
        "datasets": repetitions * 3 * len(POLICIES),
        "implementation_sha256": fingerprint(),
        "gates": GATES,
        "policies": policies,
        "passed": all(v["passed"] for v in policies.values()),
        "response_origin": "synthetic",
        "scope": "Assigned paths, off-grid gains and company-correlated report noise; original recovery gates; no psychological wording effect, real verification benefit or choice policy recovered",
    }
