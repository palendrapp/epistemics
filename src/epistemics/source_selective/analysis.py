"""Realized whole-trajectory value at bound prices; repeated contexts are not new worlds."""

from statistics import mean

from epistemics.source_selective.policy import expected_value, price_for


def metrics(report, binding):
    rows = []
    for j, company in enumerate(report.manifest.companies[12:]):
        before = report.observations[12 + 2 * j].answer
        final = report.observations[13 + 2 * j].answer
        truth = company.record.public.resolved_strong
        price = price_for(binding, company.company_id)
        cost = price if before.query == "customer_panel" else 0.0
        gross = float(truth) - company.threshold if final.decision == "invest" else 0.0
        rows.append(
            {
                "company_id": company.company_id,
                "threshold": company.threshold,
                "check_price": price,
                "check_supplied": before.query == "customer_panel",
                "provisional_probability": before.probability,
                "final_probability": final.probability,
                "expected_sample_value": expected_value(before.probability, company.threshold),
                "check_cost": cost,
                "gross_payoff": gross,
                "net_payoff": gross - cost,
                "final_brier": (final.probability - truth) ** 2,
                "decision_changed": before.decision != final.decision,
                "false_acceptance": final.decision == "invest" and not truth,
                "missed_opportunity": final.decision == "decline" and truth,
                "final_decision_consistent": final.decision
                == ("invest" if final.probability > company.threshold else "decline")
                or final.probability == company.threshold,
            }
        )
    return {
        "companies": 12,
        "check_count": sum(r["check_supplied"] for r in rows),
        "total_check_cost": sum(r["check_cost"] for r in rows),
        **{
            "mean_" + key: mean(r[key] for r in rows)
            for key in ("net_payoff", "gross_payoff", "final_brier")
        },
        **{
            key: sum(r[key] for r in rows)
            for key in (
                "decision_changed",
                "false_acceptance",
                "missed_opportunity",
                "final_decision_consistent",
            )
        },
        "rows": rows,
        "scope": "Twelve later companies only, at sidecar-bound offered prices. Full policy trajectory, including anticipation and carryover. Fictional points; reported probabilities are not internal beliefs. Legacy canonical-ledger prices and choice scores do not apply.",
    }


def contrast(baseline, candidate):
    if [(r["company_id"], r["threshold"], r["check_price"]) for r in baseline["rows"]] != [
        (r["company_id"], r["threshold"], r["check_price"]) for r in candidate["rows"]
    ]:
        raise ValueError("Compare matched companies and offered prices only")
    return {
        "net_payoff_gain": candidate["mean_net_payoff"] - baseline["mean_net_payoff"],
        "gross_payoff_gain": candidate["mean_gross_payoff"] - baseline["mean_gross_payoff"],
        "brier_change": candidate["mean_final_brier"] - baseline["mean_final_brier"],
        "additional_check_cost_per_company": (
            candidate["total_check_cost"] - baseline["total_check_cost"]
        )
        / 12,
    }


def repeated_contrast(baselines, candidates):
    if len(baselines) != 2 or len(candidates) != 2:
        raise ValueError("Require both frozen context repeats per policy")
    pairs = [contrast(a, b) for a, b in zip(baselines, candidates, strict=True)]
    return {
        "repeat_contrasts": pairs,
        "repeat_mean": {k: mean(p[k] for p in pairs) for k in pairs[0]},
        "both_repeats_nonnegative": min(p["net_payoff_gain"] for p in pairs) >= -1e-12,
    }


def repeatability(analyses):
    a, b = analyses
    contrast(a, b)  # validate matching rows before comparing probabilities
    return {
        "final_probability_mae_pp": 100
        * mean(
            abs(x["final_probability"] - y["final_probability"])
            for x, y in zip(a["rows"], b["rows"], strict=True)
        ),
        "absolute_net_payoff_difference": abs(a["mean_net_payoff"] - b["mean_net_payoff"]),
        "check_assignment_disagreements": sum(
            x["check_supplied"] != y["check_supplied"]
            for x, y in zip(a["rows"], b["rows"], strict=True)
        ),
    }


def gate(comparisons):
    if set(comparisons) != {"a", "b"}:
        raise ValueError("Require both frozen worlds")
    results = {}
    for name, minimum in (("cost_aware_vs_none", 0.01), ("cost_aware_vs_always", 0.0)):
        gains = [comparisons[w][name]["repeat_mean"]["net_payoff_gain"] for w in ("a", "b")]
        results[name] = {
            "mean_net_payoff_gain": mean(gains),
            "both_worlds_nonnegative": min(gains) >= -1e-12,
            "passed": mean(gains) >= minimum - 1e-12 and min(gains) >= -1e-12,
        }
    return {
        "comparators": results,
        "passed": all(r["passed"] for r in results.values()),
        "scope": "Small development gate on repeat means; no population confidence or validated policy claim",
    }
