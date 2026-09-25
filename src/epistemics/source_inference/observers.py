"""Competing behavioral observers learn only from public source records."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import numpy as np

from epistemics.source_inference.world import RANDOM, RULES, Probe, PublicRecord, Rule, distribution

Family = Literal["joint_process", "flat_accuracy", "fixed_discount"]
FAMILIES: tuple[Family, ...] = ("joint_process", "flat_accuracy", "fixed_discount")
ACCURACIES = (0.5, 0.65, 0.8, 0.95, 1.0)


@dataclass(frozen=True)
class State:
    accuracy: float
    rule: Rule


def states(family: Family) -> tuple[State, ...]:
    if family not in FAMILIES:
        raise ValueError("Unknown observer family")
    if family == "fixed_discount":
        return (State(1.0, RANDOM),)
    return tuple(
        State(r, rule)
        for r in ACCURACIES
        for rule in (RULES if family == "joint_process" else (RANDOM,))
    )


@lru_cache(maxsize=2048)
def learned_weights(history: tuple[PublicRecord, ...], source_id: str, family: Family):
    support = states(family)
    log_weights = np.zeros(len(support))  # Uniform finite prior, explicit in the design plan.
    if family != "fixed_discount":
        for row in history:
            if row.source_id == source_id:
                likelihood = [
                    distribution(row.world, row.resolved_strong, s.accuracy, s.rule)[row.count]
                    for s in support
                ]
                with np.errstate(divide="ignore"):
                    log_weights += np.log(likelihood)
    if not np.isfinite(log_weights).any():
        raise ValueError("Public archive has zero probability under every source state")
    weights = np.exp(log_weights - np.max(log_weights))
    return tuple(map(float, weights / weights.sum()))


def posterior(history: tuple[PublicRecord, ...], probe: Probe, family: Family):
    """P(company state, source process | public archive, report, optional process audit)."""
    support = states(family)
    weights = np.array(learned_weights(history, probe.source_id, family))
    if family == "joint_process" and probe.disclosed_rule:
        weights *= np.array([s.rule == probe.disclosed_rule for s in support])
    likelihood = np.array(
        [
            [distribution(probe.world, h, s.accuracy, s.rule)[probe.count] for s in support]
            for h in (False, True)
        ]
    )
    joint = likelihood * weights * np.array([1 - probe.prior_strong, probe.prior_strong])[:, None]
    if joint.sum() <= 0:
        raise ValueError("Report or disclosed process is outside the observer's support")
    joint /= joint.sum()
    if family == "fixed_discount":
        # Deliberately simple, history-independent heuristic: 35% of literal report log evidence.
        log_prior = np.log(probe.prior_strong / (1 - probe.prior_strong))
        log_evidence = np.log(likelihood[1, 0] / likelihood[0, 0])
        p = 1 / (1 + np.exp(-(log_prior + 0.35 * log_evidence)))
        joint = np.array([[1 - p], [p]])
    return joint, support


def predict(history: tuple[PublicRecord, ...], probe: Probe, family: Family) -> float:
    joint, _ = posterior(history, probe, family)
    return float(joint[1].sum())


def predict_logit(history, probe, family):
    joint, _ = posterior(history, probe, family)
    # Use both masses rather than 1-p: extreme but nonzero tails stay representable.
    return float(np.log(joint[1].sum()) - np.log(joint[0].sum()))


def source_summary(history: tuple[PublicRecord, ...], source_id: str, family: Family):
    weights = np.array(learned_weights(history, source_id, family))
    support = states(family)
    return {
        "expected_measurement_accuracy": float(weights @ [s.accuracy for s in support]),
        "rule_probabilities": {
            f"{rule.direction}:{rule.panels}": float(
                sum(w for w, s in zip(weights, support, strict=True) if s.rule == rule)
            )
            for rule in RULES
        },
    }


def entropy(probabilities):
    p = np.asarray(probabilities)
    return float(-np.sum(p[p > 0] * np.log2(p[p > 0])))


def research_values(history, probe, threshold=0.5, costs=None):
    """One-query-then-act values under the joint observer, not a fitted research trait.

    Invest yields 1-threshold if H and -threshold otherwise; decline yields zero.
    Source audits resolve their named process parameter; the customer panel is independent.
    """
    if not 0 < threshold < 1:
        raise ValueError("Decision threshold must be strictly between zero and one")
    default = {
        "customer_panel": 0.04,
        "selection_audit": 0.02,
        "measurement_audit": 0.02,
        "unrelated_audit": 0.005,
        "stop": 0.0,
    }
    costs = default if costs is None else costs
    if set(costs) != set(default) or any(not np.isfinite(c) or c < 0 for c in costs.values()):
        raise ValueError("Supply nonnegative finite costs for all five actions")
    if costs["stop"] != 0:
        raise ValueError("Stopping has zero cost")
    joint, support = posterior(history, probe, "joint_process")
    before_p = float(joint[1].sum())
    before_value = max(0, before_p - threshold)
    groups = {}
    for query, key in (
        ("selection_audit", lambda s: s.rule),
        ("measurement_audit", lambda s: s.accuracy),
    ):
        outcomes = []
        for value in dict.fromkeys(key(s) for s in support):
            branch = joint * np.array([key(s) == value for s in support])[None, :]
            probability = float(branch.sum())
            if probability > 0:
                outcomes.append((probability, branch / probability))
        groups[query] = outcomes
    panel = np.array([distribution(probe.world, h, 1.0, RANDOM) for h in (False, True)])
    groups["customer_panel"] = []
    for count in range(probe.world.panel_size + 1):
        branch = joint * panel[:, count, None]
        probability = float(branch.sum())
        if probability > 0:
            groups["customer_panel"].append((probability, branch / probability))
    groups["unrelated_audit"] = [(0.5, joint), (0.5, joint)]
    groups["stop"] = [(1.0, joint)]
    result = {}
    for query, outcomes in groups.items():
        expected_value = sum(prob * max(0, float(b[1].sum()) - threshold) for prob, b in outcomes)
        company_info = entropy([1 - before_p, before_p]) - sum(
            prob * entropy(b.sum(axis=1)) for prob, b in outcomes
        )
        joint_info = entropy(joint) - sum(prob * entropy(b) for prob, b in outcomes)
        result[query] = {
            "cost": float(costs[query]),
            "gross_decision_value": max(0.0, float(expected_value - before_value)),
            "net_decision_value": float(expected_value - before_value - costs[query]),
            "company_information_bits": max(0.0, float(company_info)),
            # This policy values company, source AND an irrelevant fair coin, an explicit foil.
            "total_information_bits": 1.0 if query == "unrelated_audit" else max(0.0, joint_info),
        }
    return result


def best_actions(values, field):
    maximum = max(row[field] for row in values.values())
    return sorted(q for q, row in values.items() if abs(row[field] - maximum) < 1e-10)
