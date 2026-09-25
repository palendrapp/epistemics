"""Fixed, coverage-constrained design search; all selection precedes synthetic responses."""

import hashlib
from collections import Counter

import numpy as np

from epistemics.source_inference.measurement import expected_model_information, sigmoid
from epistemics.source_inference.observers import (
    FAMILIES,
    best_actions,
    predict_logit,
    research_values,
)
from epistemics.source_inference.world import RULES, Probe, World, distribution, sources


def encoded(value):
    import json

    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def probe_id(probe):
    return digest(probe.model_dump(mode="json"))[:16]


def candidates():
    return tuple(
        Probe(source_id=source.source_id, count=k, prior_strong=prior, disclosed_rule=rule)
        for source in sources()
        for k in range(6)
        for prior in (0.2, 0.5, 0.8)
        for rule in (None, *RULES)
    )


def predictions(history, probes):
    return np.array([[predict_logit(history, p, f) for p in probes] for f in FAMILIES])


def choose_design(history, seed):
    probes = candidates()
    logits = predictions(history, probes)
    information = expected_model_information(logits)
    anchors = [
        i
        for i, p in enumerate(probes)
        if p.count in (2, 3) and p.prior_strong == 0.5 and p.disclosed_rule is None
    ]
    chosen = list(anchors)
    counts = Counter(probes[i].source_id for i in chosen)
    # Two shared anchors + two highest-ranked probes per source. No observed answers used.
    for i in np.argsort(-information, kind="stable"):
        i = int(i)
        if i not in chosen and counts[probes[i].source_id] < 4:
            chosen.append(i)
            counts[probes[i].source_id] += 1
    rng = np.random.default_rng(seed)
    comparator = list(anchors)
    for source in sources():
        available = [
            i for i, p in enumerate(probes) if p.source_id == source.source_id and i not in anchors
        ]
        comparator.extend(map(int, rng.choice(available, 2, replace=False)))
    unused = [i for i in range(len(probes)) if i not in set(chosen + comparator)]
    heldout = list(map(int, rng.choice(unused, 32, replace=False)))
    summaries = []
    for i in chosen:
        summaries.append(
            {
                "probe_id": probe_id(probes[i]),
                "probe": probes[i].model_dump(mode="json"),
                "anchor": i in anchors,
                "marginal_model_information_bits": float(information[i]),
                "predicted_strong_probabilities": dict(
                    zip(FAMILIES, map(float, sigmoid(logits[:, i])), strict=True)
                ),
            }
        )
    return {
        "probes": probes,
        "indices": {"diagnostic": chosen, "matched_random": comparator, "heldout": heldout},
        "summaries": summaries,
        "candidate_information": information.tolist(),
        "method": "Marginal model-information ranking with two fixed anchors and four probes per source; not globally optimal battery design",
    }


def worked_example():
    rows = []
    for rule in (RULES[0], RULES[1], RULES[3]):
        weak, strong = [distribution(World(), h, 1, rule)[4] for h in (False, True)]
        rows.append(
            {
                "rule": rule.model_dump(),
                "report_count": 4,
                "probability_given_weak": weak,
                "probability_given_strong": strong,
                "likelihood_ratio": strong / weak,
                "posterior_strong": strong / (strong + weak),
            }
        )
    return rows


def policy_contrasts(history, probes):
    counts = {
        policy: Counter()
        for policy in ("decision_value", "company_information", "total_information")
    }
    examples, disagreements = [], 0
    regrets = {
        name: [] for name in ("always_customer_panel", "always_selection_audit", "always_stop")
    }
    total = 0
    for probe in probes:
        for threshold in (0.3, 0.7):
            for scale in (0.25, 1, 5):
                costs = {
                    "customer_panel": 0.04 * scale,
                    "selection_audit": 0.02 * scale,
                    "measurement_audit": 0.02 * scale,
                    "unrelated_audit": 0.005 * scale,
                    "stop": 0,
                }
                values = research_values(history, probe, threshold, costs)
                actions = {
                    name: best_actions(values, field)
                    for name, field in (
                        ("decision_value", "net_decision_value"),
                        ("company_information", "company_information_bits"),
                        ("total_information", "total_information_bits"),
                    )
                }
                for name, best in actions.items():
                    counts[name][" | ".join(best)] += 1
                disjoint = not set(actions["decision_value"]) & set(actions["company_information"])
                disagreements += disjoint
                best_value = max(v["net_decision_value"] for v in values.values())
                for policy, action in (
                    ("always_customer_panel", "customer_panel"),
                    ("always_selection_audit", "selection_audit"),
                    ("always_stop", "stop"),
                ):
                    regrets[policy].append(best_value - values[action]["net_decision_value"])
                if disjoint and len(examples) < 6:
                    examples.append(
                        {
                            "probe_id": probe_id(probe),
                            "threshold": threshold,
                            "cost_scale": scale,
                            "actions": actions,
                            "values": values,
                        }
                    )
                total += 1
    return {
        "cases": total,
        "decision_and_company_information_disagree": disagreements,
        "optimal_action_sets": {p: dict(c) for p, c in counts.items()},
        "fixed_policy_mean_foregone_payoff": {p: float(np.mean(v)) for p, v in regrets.items()},
        "examples": examples,
        "scope": "Computed policy contrasts under the joint learner; no collected decisions or identified agent research strategy",
    }
