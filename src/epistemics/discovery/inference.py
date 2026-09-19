"""Conditional observer models: input is a public trial, never private truth or seed."""

import math
import re
from functools import lru_cache

import numpy as np

from epistemics.company.models import GrowthQuantiles
from epistemics.discovery.models import DiscoveryTrial, ObserverForecast
from epistemics.discovery.world import (
    BIAS,
    GROWTH,
    RENEWAL,
    SD,
    SOURCE_IDS,
    STATES,
    A,
    F,
    G,
    K,
    cdf,
    log_measurement,
    normalize,
)

MODEL_DESCRIPTIONS = {
    "joint_learning": "Joint source bias/precision, disruption, business relationship and origin inference; conditional on the declared observer assumptions.",
    "fixed_sources": "Sources held at zero bias and SD 4, regardless of archive; company, relationship and origin inference retained.",
    "fixed_weak_link": "Source learning retained; disruption reduces renewal-supported growth by 2 points, fixed.",
    "fixed_strong_link": "Source learning retained; disruption reduces renewal-supported growth by 8 points, fixed.",
}


def number(text, label):
    match = re.search(re.escape(label) + r"\s*(-?\d+(?:\.\d+)?)", text)
    if not match:
        raise ValueError(f"Missing public measurement: {label}")
    return float(match.group(1))


def extract(trial: DiscoveryTrial):
    """Interpret the authored visible measurements, not a hidden semantic ledger."""
    docs = {d.document_id: d.text for d in trial.documents}
    values = {}
    labels = {
        "d1": ("demand", "Underlying-demand growth estimate:"),
        "d2": ("renewal", "Renewal-supported growth estimate:"),
        "d3": ("news", "Growth figure in interim trade coverage:"),
        "d4": ("model", "Model projection:"),
        "d5": ("backlog", "Implementation backlog score:"),
        "d8": ("unaffected", "Growth estimate from customers outside the implementation backlog:"),
        "d9": ("new_demand", "Updated underlying-demand growth estimate:"),
    }
    for key, (name, label) in labels.items():
        if key in docs:
            values[name] = number(docs[key], label)
    audit = []
    if "d6" in docs:
        audit = [
            (float(r), float(a))
            for r, a in re.findall(
                r"\| morrow-archive-\d+ \| (-?\d+\.\d+) \| (-?\d+\.\d+) \|", docs["d6"]
            )
        ]
        if len(audit) != 4:
            raise ValueError("Incomplete public source-audit table")
    shared = None
    if "d7" in docs:
        if "editorial synthesis derived from Morrow" in docs["d7"]:
            shared = True
        elif "separately sampled renewal study" in docs["d7"]:
            shared = False
        else:
            raise ValueError("Unrecognized public lineage disclosure")
    return values, audit, shared


@lru_cache(maxsize=256)
def _base_log_weights(serialized: str, model: str):
    if model not in MODEL_DESCRIPTIONS:
        raise ValueError("Unknown observer model")
    trial = DiscoveryTrial.model_validate_json(serialized)
    q = np.zeros(len(STATES))
    if model == "fixed_sources":
        q[np.any((BIAS != 0) | (SD != 4), axis=1)] = -np.inf
    if model.startswith("fixed_") and model.endswith("_link"):
        q[K != int(model == "fixed_strong_link")] = -np.inf
    for source in trial.sources:
        j = SOURCE_IDS.index(source.source_id)
        for row in source.archive:
            q += log_measurement(row.reported_pct - row.audited_pct, BIAS[:, j], SD[:, j])
    for old in trial.analogues:
        mean = old.underlying_growth_pct - np.where(K == 1, 8, 2) * old.rollout_disruption
        q += log_measurement(old.renewal_growth_pct, mean, 3)
    values, audit, shared = extract(trial)
    if "demand" in values:
        q += log_measurement(values["demand"], F + BIAS[:, 0], SD[:, 0])
    if "renewal" in values:
        q += log_measurement(values["renewal"], RENEWAL + BIAS[:, 1], SD[:, 1])
    if "news" in values:
        copy = log_measurement(values["news"], values["renewal"], 0.75)
        independent = log_measurement(values["news"], RENEWAL + BIAS[:, 2], SD[:, 2])
        q += np.where(G == 1, copy, independent)
    if "model" in values:
        expected = round(0.6 * values["demand"] + 0.4 * values["renewal"] + 2, 1)
        if not math.isclose(values["model"], expected, abs_tol=1e-8):
            raise ValueError("Derived document disagrees with its declared inputs")
        # The model is deterministic conditional on already available measurements.
    if "backlog" in values:
        q += log_measurement(values["backlog"], 12 + 20 * A, 6)
    for reported, actual in audit:
        q += log_measurement(reported - actual, BIAS[:, 1], SD[:, 1])
    if shared is not None:
        q[G != int(shared)] = -np.inf
    if "unaffected" in values:
        q += log_measurement(values["unaffected"], F, 1.8)
    if "new_demand" in values:
        q += log_measurement(values["new_demand"], F + BIAS[:, 0], SD[:, 0])
    q.setflags(write=False)
    return q


def posterior(trial: DiscoveryTrial, *, model="joint_learning", source_frame=0.0):
    if not math.isfinite(source_frame):
        raise ValueError("Source framing coefficient must be finite")
    q = _base_log_weights(trial.model_dump_json(), model).copy()
    if model != "fixed_sources":
        for source in trial.sources:
            j = SOURCE_IDS.index(source.source_id)
            frame = (
                1
                if ": skeptical;" in source.profile
                else -1
                if ": optimistic;" in source.profile
                else 0
            )
            # Prior odds of precise vs noisy source. Bias prior remains uniform.
            q += (SD[:, j] == 1.5) * source_frame * frame
    return normalize(q)


def growth_probability(trial, *, model="joint_learning", source_frame=0.0):
    return float(posterior(trial, model=model, source_frame=source_frame) @ cdf((F - 12) / 2))


def forecast(trial: DiscoveryTrial, *, model="joint_learning", source_frame=0.0):
    q = posterior(trial, model=model, source_frame=source_frame)
    masses = np.bincount(STATES[:, 0], weights=q, minlength=len(GROWTH))
    ps = cdf((GROWTH - 12) / 2)

    def quantile(level):
        lo, hi = -30.0, 60.0
        for _ in range(55):
            mid = (lo + hi) / 2
            if masses @ cdf((mid - GROWTH) / 2) < level:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    source = {
        sid: float(q @ (cdf((2 - BIAS[:, j]) / SD[:, j]) - cdf((-2 - BIAS[:, j]) / SD[:, j])))
        for j, sid in enumerate(SOURCE_IDS)
    }
    conditional = q * (A == 0)
    conditional /= conditional.sum()
    return ObserverForecast(
        growth_probability=float(masses @ ps),
        growth_quantiles_pct=GrowthQuantiles(
            p10=quantile(0.1), p50=quantile(0.5), p90=quantile(0.9)
        ),
        source_accuracy=source,
        conditional_growth_probability=float(conditional @ cdf((F - 12) / 2)),
        disruption_probability=float(np.clip(q @ A, 0, 1)),
        strong_disruption_link_probability=float(np.clip(q @ K, 0, 1)),
        shared_origin_probability=float(np.clip(q @ G, 0, 1)),
    )


def report_prediction(trial, *, model="joint_learning", source_frame=0.0, output_frame=0.0):
    """Growth report plus requested source probes; used by multi-run likelihood fitting."""
    q = posterior(trial, model=model, source_frame=source_frame)
    p = float(q @ cdf((F - 12) / 2))
    w = 1 if trial.target_event == "growth_above_12" else -1
    p = 1 / (1 + math.exp(-(math.log(p / (1 - p)) + output_frame * w)))
    result = [p]
    for sid in trial.source_probe_ids:
        j = SOURCE_IDS.index(sid)
        result.append(
            float(q @ (cdf((2 - BIAS[:, j]) / SD[:, j]) - cdf((-2 - BIAS[:, j]) / SD[:, j])))
        )
    return np.array(result)
