"""Calibration-only pooled/configuration fits, used without later response inputs."""

import numpy as np

from epistemics.source_inference.measurement import GAINS, fit, log_likelihood, logsumexp
from epistemics.source_inference.observers import FAMILIES
from epistemics.source_learning.inference import forecast


def fit_profile(reports):
    if not reports:
        raise ValueError("A profile needs completed training collections")
    logits, answers, blocks, inputs = [], [], [], []
    seen = set()
    for report in reports:
        sid = report.manifest.study_id
        if sid in seen:
            raise ValueError("A training collection cannot be counted twice")
        seen.add(sid)
        for observation, lock in zip(
            report.observations[:12], report.prediction_locks[:12], strict=True
        ):
            logits.append([lock["raw"][f]["logit"] for f in FAMILIES])
            answers.append(observation.answer.probability)
            blocks.append(f"{sid}:{observation.trial.company_id}")
        inputs.append(report.manifest_sha256)
    matrix = np.asarray(logits).T
    result = fit(matrix, answers, blocks)
    likelihood = log_likelihood(matrix[:, None, :] * GAINS[None, :, None], answers, blocks)
    result["gain_probabilities"] = {
        f: np.exp(row - logsumexp(row)).tolist()
        for f, row in zip(FAMILIES, likelihood, strict=True)
    }
    result["baseline_mean"] = float(np.mean(answers))
    result["training_collections"] = len(reports)
    result["training_reports"] = len(answers)
    result["training_manifests"] = inputs
    result["scope"] = "Only first twelve unaudited reports per named training collection"
    return result


def predictions(raw, profiles, prior):
    return {
        "configuration_profile": forecast(raw, profiles["configuration"])["mixture_mean"],
        "shared_profile": forecast(raw, profiles["shared"])["mixture_mean"],
        "fixed_joint": raw["joint_process"]["probability"],
        "fixed_flat": raw["flat_accuracy"]["probability"],
        "fixed_discount": raw["fixed_discount"]["probability"],
        "configuration_mean": profiles["configuration"]["baseline_mean"],
        "shared_mean": profiles["shared"]["baseline_mean"],
        "stated_prior": prior,
    }
