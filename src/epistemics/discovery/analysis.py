"""Outcome scoring and conditional observer comparisons; no trait fit from one case."""

import math

import numpy as np

from epistemics.discovery.inference import MODEL_DESCRIPTIONS, extract, forecast
from epistemics.discovery.models import ObserverComparison

LIMITATIONS = [
    "One company case and one outcome; repeated checkpoints are not independent replications. No stable behavioral parameters or population intervals are fitted from this report.",
    "Observer predictions integrate unknown source states using public archives. Their functional forms, grids and priors remain modeling assumptions, not disclosed facts or uniquely correct answers.",
    "Fixed-gain observer comparisons cannot identify private beliefs or separate every inference/reporting mechanism.",
    "The finite observer family can miss an agent's alternative business explanation. Inspect absolute fit and extraction errors before interpreting relative model fit.",
    "Authored document extraction is deterministic for these templates; open-ended semantic interpretation and new scenario families remain unvalidated.",
    "Historical archives are consecutive resolved cases; source profiles, archive length, provenance and response wording are assigned independently of latent fundamentals and potential observations.",
    "Source histories recur inside this case. Cross-company learning, active research and minimal-probe arms remain future conditions.",
    "Source and conditional probes may influence reasoning. Context and filesystem isolation are the host's responsibility; identities and execution are operator assertions.",
]


def growth_report(trial, answer):
    return (
        answer.target_probability
        if trial.target_event == "growth_above_12"
        else 1 - answer.target_probability
    )


def analyze(observations, private_case):
    y = private_case.realized_growth_pct
    target = y > 12
    p = np.array([growth_report(o.trial, o.answer) for o in observations])
    clip = np.clip(p, 1e-6, 1 - 1e-6)
    agreement = []
    intervals = []
    extraction = []
    for o, prob in zip(observations, p, strict=True):
        a = o.answer
        agreement.append(
            (a.decision == "invest") == (prob * o.trial.gain - (1 - prob) * o.trial.loss > 1e-12)
        )
        lo, hi = a.growth_quantiles_pct.p10, a.growth_quantiles_pct.p90
        intervals.append(hi - lo + 10 * max(lo - y, 0) + 10 * max(y - hi, 0))
        public, _, _ = extract(o.trial)
        for key, value in a.extracted_values.items():
            expected = public["renewal" if key == "renewal_estimate_pct" else "model"]
            extraction.append(abs(value - expected))
    metrics = {
        "checkpoints": float(len(p)),
        "independent_company_outcomes": 1.0,
        "mean_brier": float(np.mean((p - target) ** 2)),
        "final_brier": float((p[-1] - target) ** 2),
        "mean_log_loss": float(np.mean(-target * np.log(clip) - (1 - target) * np.log(1 - clip))),
        "decision_report_agreement": float(np.mean(agreement)),
        "mean_80pct_interval_score": float(np.mean(intervals)),
        "final_80pct_interval_covered": float(
            observations[-1].answer.growth_quantiles_pct.p10
            <= y
            <= observations[-1].answer.growth_quantiles_pct.p90
        ),
        "mean_extraction_absolute_error_pct_points": float(np.mean(extraction)),
        "derived_model_absolute_probability_update": abs(float(p[4] - p[3])),
        "source_audit_absolute_probability_update": abs(float(p[6] - p[5])),
        "lineage_reveal_absolute_probability_update": abs(float(p[7] - p[6])),
    }
    models = {}
    for name, description in MODEL_DESCRIPTIONS.items():
        predictions = [forecast(o.trial, model=name) for o in observations]
        models[name] = ObserverComparison(
            forecasts=predictions,
            growth_report_rmse=math.sqrt(
                sum((x.growth_probability - v) ** 2 for x, v in zip(predictions, p, strict=True))
                / len(p)
            ),
            description=description,
        )
    return metrics, models
