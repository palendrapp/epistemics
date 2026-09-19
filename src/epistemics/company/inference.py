"""Finite-state inference from public dossier information, with explicit provenance."""

import itertools
import math

import numpy as np

from epistemics.battery import logit, sigmoid
from epistemics.company.models import CompanyTrial, Evidence, Forecast, GrowthQuantiles, WorldModel

STATES = tuple(itertools.product((0, 1), repeat=4))  # growth, margin, temporary, source validity


def prior(world: WorldModel, auxiliary_shift: float = 0) -> np.ndarray:
    pa = sigmoid(logit(world.prior_temporary) + auxiliary_shift)
    weights = []
    for h, m, a, v in STATES:
        pm = world.margin_probabilities[2 * h + a]
        weights.append(
            (world.prior_growth if h else 1 - world.prior_growth)
            * (pa if a else 1 - pa)
            * (world.prior_source_validity if v else 1 - world.prior_source_validity)
            * (pm if m else 1 - pm)
        )
    return np.asarray(weights)


def positive_rate(kind: str, state: tuple, world: WorldModel) -> float:
    h, m, a, v = state
    if kind == "management":
        return (world.management_accuracy if h else 1 - world.management_accuracy) if v else 0.5
    if kind == "independent_growth":
        return world.independent_accuracy if h else 1 - world.independent_accuracy
    if kind == "operations":
        return world.operations_positive_rates[2 * h + a]
    if kind == "margin":
        return world.margin_accuracy if m else 1 - world.margin_accuracy
    if kind == "source_audit":
        return world.audit_accuracy if v else 1 - world.audit_accuracy
    if kind == "temporary_check":
        return world.audit_accuracy if a else 1 - world.audit_accuracy
    raise ValueError(f"Not a stochastic measurement: {kind}")


def likelihood(item: Evidence, history: list[Evidence], world: WorldModel, *, isolated=False):
    """Copies/calculations add no new observation when their parents are already available."""
    by_id = {e.document_id: e for e in history}
    kind, value = item.signal.kind, item.signal.value
    if kind in {"copy", "derived_model"}:
        parents = [by_id[p] for p in item.signal.parents]
        if kind == "copy":
            expected = parents[0].signal.value
        else:
            expected = 8 + 7 * parents[0].signal.value + 4 * parents[1].signal.value
        if value != expected:
            raise ValueError("Document does not match its declared inputs")
        if not isolated:
            return np.ones(len(STATES))
        if kind == "copy":
            return likelihood(parents[0], history, world, isolated=True)
        # The standalone model is a function of two conditionally independent primitive inputs.
        result = []
        for state in STATES:
            p1 = positive_rate(parents[0].signal.kind, state, world)
            p2 = positive_rate(parents[1].signal.kind, state, world)
            result.append(
                sum(
                    (p1 if x else 1 - p1) * (p2 if y else 1 - p2)
                    for x, y in itertools.product((0, 1), repeat=2)
                    if 8 + 7 * x + 4 * y == value
                )
            )
        return np.asarray(result)
    if value not in (0, 1):
        raise ValueError("Primitive measurements must be binary")
    rates = np.asarray([positive_rate(kind, s, world) for s in STATES])
    return rates if value else 1 - rates


def posterior(trial: CompanyTrial, auxiliary_shift: float = 0) -> np.ndarray:
    q = prior(trial.dossier.world, auxiliary_shift)
    history = []
    for item in trial.evidence:
        values = likelihood(item, history, trial.dossier.world)
        if not np.all(values == 1):
            q *= values
            q /= q.sum()
        history.append(item)
    return q


def quantiles(p: float) -> GrowthQuantiles:
    # Y|H=0 ~ Uniform(0,12); Y|H=1 ~ Uniform(12,24), in percentage points.
    def quantile(u):
        return 12 * u / (1 - p) if u <= 1 - p else 12 + 12 * (u - (1 - p)) / p

    return GrowthQuantiles(p10=quantile(0.1), p50=quantile(0.5), p90=quantile(0.9))


def forecast(trial: CompanyTrial, auxiliary_shift: float = 0) -> Forecast:
    q = posterior(trial, auxiliary_shift)
    marginals = [
        float(sum(p for p, state in zip(q, STATES, strict=True) if state[i])) for i in range(4)
    ]
    return Forecast(
        growth_probability=marginals[0],
        margin_probability=marginals[1],
        temporary_probability=marginals[2],
        source_probability=marginals[3],
        growth_quantiles_pct=quantiles(marginals[0]),
    )


def evidence_features(trial: CompanyTrial) -> tuple[float, float, bool]:
    if not trial.evidence:
        return 0.0, 0.0, False
    previous = trial.model_copy(update={"evidence": trial.evidence[:-1]})
    q = posterior(previous)
    base = prior(trial.dossier.world)
    item = trial.evidence[-1]

    def log_ratio(weights, values):
        rates = []
        for h in (0, 1):
            mask = np.asarray([s[0] == h for s in STATES])
            rates.append(float(np.dot(weights[mask], values[mask]) / weights[mask].sum()))
        return math.log(rates[1] / rates[0])

    incremental = log_ratio(q, likelihood(item, trial.evidence[:-1], trial.dossier.world))
    standalone = log_ratio(
        base, likelihood(item, trial.evidence[:-1], trial.dossier.world, isolated=True)
    )
    # Target-relative valence; a source audit can be adverse only in the context of earlier claims.
    direction = incremental if abs(incremental) > 1e-12 else standalone
    return incremental, standalone, direction < -1e-12
