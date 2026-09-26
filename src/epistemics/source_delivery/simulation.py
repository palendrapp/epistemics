"""Engineering acceptance; wording effects require actual respondent evidence."""

from epistemics.source_delivery.service import DeliveryService, create, fingerprint
from epistemics.source_learning.battery import location
from epistemics.source_learning.inference import raw_predictions
from epistemics.source_learning.service import export
from epistemics.source_learning.simulation import PARTICIPANT, synthetic_answer
from epistemics.source_learning.simulation import recovery as base_recovery


def simulate(directory, seed, condition="sparse", presentation="structured", participant=None):
    m = create(
        directory,
        participant or PARTICIPANT,
        seed=seed,
        condition=condition,
        synthetic=True,
        presentation=presentation,
    )
    s = DeliveryService(directory)
    answers = []
    for i in range(36):
        t = s.get_trial()["trial"]
        c, _ = location(i)
        raw = raw_predictions(m, i, answers)
        a = synthetic_answer(
            m,
            i,
            raw,
            "joint_process",
            1.0,
            0,
            ("customer_panel", "selection_audit", "measurement_audit", "stop")[c % 4],
        )
        s.submit(t["trial_id"], a)
        answers.append(a)
    s.finish()
    s.evidence()
    return export(directory)


def recovery(seed, repetitions=32):
    result = base_recovery(seed, repetitions)
    result["schema_version"] = "epistemics.source-delivery-recovery.v1"
    result["implementation_sha256"] = fingerprint()
    result["scope"] += (
        "; generator, inference and answer sequence unchanged; clarified text has no synthetic behavioral effect"
    )
    return result
