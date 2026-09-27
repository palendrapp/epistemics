"""Synthetic validation of compact delivery.

Model recovery does not read public presentation, so the unchanged 0.2 recovery gates are
rerun as-is. Compact-specific checks drive complete collections through submit-returned
checkpoints and confirm that every locked checkpoint expands to its exact 0.2 public trial.
"""

import tempfile
from pathlib import Path

from epistemics.source_compact.presentation import expand
from epistemics.source_compact.service import CompactService, create, fingerprint, load_evidence
from epistemics.source_learning.inference import raw_predictions
from epistemics.source_learning.simulation import PARTICIPANT, synthetic_answer
from epistemics.source_learning.storage import encoded
from epistemics.source_selective.policy import POLICIES
from epistemics.source_selective.presentation import present as present_v2
from epistemics.source_selective.simulation import recovery as selective_recovery


def simulate(directory, seed, policy, family="joint_process", gain=1.0):
    manifest = create(
        directory, PARTICIPANT, seed=seed, policy=policy, price_seed=seed + 200000, synthetic=True
    )
    service = CompactService(directory)
    answers = []
    trial = service.get_trial()["trial"]
    for i in range(36):
        answer = synthetic_answer(
            manifest, i, raw_predictions(manifest, i, answers), family, gain, 0, "stop"
        )
        receipt = service.submit(
            trial["trial_id"], answer.model_dump(include={"probability", "decision"})
        )
        answers.append(answer)
        trial = receipt["next_trial"]
    if trial is not None:
        raise ValueError("A checkpoint remained after the final answer")
    service.finish()
    return service.evidence()


def transport(seed):
    """Complete collections per policy; counts of calls and bytes; exact 0.2 expansion."""
    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        for policy in POLICIES:
            directory = Path(tmp) / policy
            evidence = simulate(directory, seed, policy)
            report, _ = load_evidence(directory)
            compact_chars = full_chars = 0
            for observation, lock in zip(report.observations, evidence["locks"], strict=True):
                full = present_v2(observation.trial, evidence["binding"])
                if expand(lock["public_trial"], policy) != full:
                    raise ValueError("Locked compact checkpoint does not expand to 0.2")
                compact_chars += len(encoded(lock["public_trial"]))
                full_chars += len(encoded(full))
            results[policy] = {
                "checkpoints": len(evidence["locks"]),
                "check_count": evidence["analysis"]["check_count"],
                "compact_trial_bytes": compact_chars,
                "v0_2_trial_bytes": full_chars,
                "byte_ratio": compact_chars / full_chars,
                "respondent_tool_calls": 1 + 36 + 1,
                "v0_2_minimum_tool_calls": 1 + 2 * 36 + 1,
            }
    return results


def recovery(seed, repetitions=32):
    model = selective_recovery(seed, repetitions)
    delivery = transport(seed)
    passed = model["passed"] and all(
        r["checkpoints"] == 36 and r["byte_ratio"] < 0.25 for r in delivery.values()
    )
    return {
        "schema_version": "epistemics.source-compact-recovery.v1",
        "seed": seed,
        "repetitions_per_family_per_policy": model["repetitions_per_family_per_policy"],
        "datasets": model["datasets"],
        "implementation_sha256": fingerprint(),
        "model_recovery": model,
        "delivery": delivery,
        "policies": model["policies"],
        "gates": model["gates"],
        "passed": passed,
        "response_origin": "synthetic",
        "scope": "Unchanged 0.2 model-recovery gates (presentation does not enter inference) plus complete compact collections under every policy with exact 0.2 expansion of every locked checkpoint; no wording effect, real verification benefit or respondent token use is simulated",
    }
