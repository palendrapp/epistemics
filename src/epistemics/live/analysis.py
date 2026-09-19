"""Existing observer analysis plus the original balanced calibration regression."""

import numpy as np

from epistemics.analysis import regression
from epistemics.battery import logit
from epistemics.discovery.analysis import analyze as discovery_analysis
from epistemics.discovery.models import DiscoveryObservation, PrivateCase
from epistemics.discovery.world import OBSERVER_ASSUMPTIONS
from epistemics.live.models import CalibrationResult, DiscoveryResult
from epistemics.models import Metrics, Observation

LIMITATIONS = [
    "Core 0.1 combines one authored discovery case and 24 numeric calibration cases; broad transfer and human/agent norms are not established.",
    "Discovery comes first; changing module order or context policy requires a new protocol review.",
    "Discovery has one resolved company outcome. Ten checkpoints are not ten independent outcomes.",
    "The calibration weights describe responses under disclosed likelihoods and also reflect arithmetic and instruction comprehension.",
    "Bootstrap intervals describe within-run variation; they do not establish repeatability or a shared human/agent internal mechanism.",
    "Discovery observer comparisons are conditional candidate explanations, not diagnoses of a unique cognitive mechanism.",
    "Participant identity, response origin, tools and execution are operator assertions. Shared evaluator filesystem access can reveal private state.",
    "No interventions have been tested in this core session. Passport issuance and identity-linked publication remain separate steps.",
]


def analyze_calibration(observations):
    x, y = [], []
    for o in observations:
        s = o.trial.stimulus
        x.append([1, logit(s["prior_h"]), (2 * s["signal"] - 1) * logit(s["sensor_accuracy"])])
        y.append(logit(o.answer.probability))
    parameters = regression(x, y, ["response_bias", "prior_weight", "evidence_weight"])
    p = np.array([o.answer.probability for o in observations])
    truth = np.array([o.truth["outcome"] for o in observations])
    reference = np.array([o.truth["reference"] for o in observations])
    clipped = np.clip(p, 1e-6, 1 - 1e-6)
    metrics = Metrics(
        n=len(p),
        brier=float(np.mean((p - truth) ** 2)),
        log_loss=float(np.mean(-truth * np.log(clipped) - (1 - truth) * np.log(1 - clipped))),
        reference_rmse=float(np.sqrt(np.mean((p - reference) ** 2))),
        endpoint_reports=int(np.sum((p == 0) | (p == 1))),
    )
    return CalibrationResult(observations=observations, parameters=parameters, metrics=metrics)


def analyze(rows, answers):
    discovery_observations = [
        DiscoveryObservation(
            trial=row["trial"]["payload"], answer=a["answer"], answered_at=a["answered_at"]
        )
        for row, a in zip(rows[:10], answers[:10], strict=True)
    ]
    private = PrivateCase.model_validate(rows[0]["truth"])
    metrics, models = discovery_analysis(discovery_observations, private)
    discovery = DiscoveryResult(
        observations=discovery_observations,
        private_case=private,
        metrics=metrics,
        observer_models=models,
        observer_assumptions=OBSERVER_ASSUMPTIONS,
    )
    calibration = analyze_calibration(
        [
            Observation(
                trial=row["trial"]["payload"],
                answer=a["answer"],
                answered_at=a["answered_at"],
                truth=row["truth"],
            )
            for row, a in zip(rows[10:], answers[10:], strict=True)
        ]
    )
    return discovery, calibration
