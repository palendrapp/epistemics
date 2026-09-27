"""Per-case scores against the private ledger, and cross-context neglect estimates.

Decisions are scored ex ante: the expected payoff of the chosen action under the normative
posterior given everything the respondent saw, so sample luck does not enter the primary
score. Realized payoff is reported separately.
"""

import math
from collections import defaultdict
from statistics import mean

from epistemics.research_world import check
from epistemics.research_world.synthetic import paired_estimate
from epistemics.research_world.world import (
    ANCHORS,
    PAIRS,
    generate,
    logit,
    naive_logit,
    normative_logit,
    sigmoid,
)


def check_llr(positive):
    if positive:
        return math.log(check.P_POSITIVE_STRONG / check.P_POSITIVE_WEAK)
    return math.log((1 - check.P_POSITIVE_STRONG) / (1 - check.P_POSITIVE_WEAK))


def clipped_logit(p):
    return logit(min(0.99, max(0.01, p)))


def analyze(manifest, observations):
    from epistemics.research_world.collection import world_for

    rows, by_case = [], defaultdict(list)
    for o in observations:
        by_case[o.trial["case_number"]].append(o)
    for item in manifest.items:
        world = world_for(item)
        first, *rest = by_case[item.case]
        final = rest[0] if rest else first
        normative = sigmoid(normative_logit(world))
        bought = first.answer.check == "buy"
        positive, _ = check.draw(world)
        after = sigmoid(normative_logit(world) + check_llr(positive)) if bought else normative
        price = item.check_price if bought else 0.0
        invest = final.answer.decision == "invest"
        value = (
            check.expected_value(normative, world.threshold) - item.check_price
            if item.check_price is not None
            else None
        )
        rows.append(
            {
                "case": item.case,
                "pair_seed": item.pair_seed,
                "family": item.family,
                "presentation": item.presentation,
                "structure_manipulated": item.presentation == PAIRS[item.family][1],
                "anchor": item.presentation == ANCHORS[item.family],
                "threshold": world.threshold,
                "reported": first.answer.probability,
                "normative": normative,
                "naive": sigmoid(naive_logit(world)),
                "logit_error": clipped_logit(first.answer.probability) - normative_logit(world),
                "check_price": item.check_price,
                "check_bought": bought,
                "check_net_value_normative": value,
                "check_net_value_at_report": (
                    check.expected_value(first.answer.probability, world.threshold)
                    - item.check_price
                    if item.check_price is not None
                    else None
                ),
                "final_reported": final.answer.probability,
                "final_decision": final.answer.decision,
                "decision_consistent": final.answer.decision
                == ("invest" if final.answer.probability > world.threshold else "decline")
                or final.answer.probability == world.threshold,
                "expected_payoff": (after - world.threshold if invest else 0.0) - price,
                "optimal_expected_payoff": max(0.0, after - world.threshold) - price,
                "realized_payoff": (
                    (1.0 if world.strong else 0.0) - world.threshold if invest else 0.0
                )
                - price,
            }
        )
    groups = defaultdict(list)
    for r in rows:
        groups[f"{r['family']}/{r['presentation']}"].append(r)
    return {
        "cases": len(rows),
        "rows": rows,
        "by_presentation": {
            key: {
                "cases": len(g),
                "mean_logit_error": mean(r["logit_error"] for r in g),
                "mean_abs_error_pp": 100 * mean(abs(r["reported"] - r["normative"]) for r in g),
                "decision_consistent": sum(r["decision_consistent"] for r in g),
                "checks_bought": sum(r["check_bought"] for r in g),
            }
            for key, g in sorted(groups.items())
        },
        "mean_expected_payoff": mean(r["expected_payoff"] for r in rows),
        "mean_action_regret": mean(
            r["optimal_expected_payoff"] - r["expected_payoff"] for r in rows
        ),
        "mean_realized_payoff": mean(r["realized_payoff"] for r in rows),
        "scope": "One context. Normative and naive references come from the private ledger; neglect weights need matched presentations from separate contexts.",
    }


def panel(reports):
    """Neglect weights per arm and family from matched presentations in separate contexts."""
    seen = defaultdict(dict)
    for report in reports:
        for r in report.analysis["rows"]:
            key = (report.manifest.arm, r["family"], r["pair_seed"])
            if r["presentation"] in seen[key]:
                raise ValueError("A presentation of one world may appear in only one context")
            seen[key][r["presentation"]] = (report.manifest.study_id, r["reported"])
    estimates = {}
    for arm in {k[0] for k in seen}:
        for family, (control, manipulated) in PAIRS.items():
            pairs = []
            for (a, f, seed), entries in sorted(seen.items()):
                if (a, f) != (arm, family) or not {control, manipulated} <= set(entries):
                    continue
                if entries[control][0] == entries[manipulated][0]:
                    raise ValueError("Matched presentations must come from separate contexts")
                worlds = generate(seed, family)
                pairs.append(
                    (
                        worlds[control],
                        entries[control][1],
                        worlds[manipulated],
                        entries[manipulated][1],
                    )
                )
            if len(pairs) >= 2:
                estimates[f"{arm}/{family}"] = paired_estimate(pairs)
    return estimates
