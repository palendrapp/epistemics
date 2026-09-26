"""Realized outcomes under complete assigned-policy trajectories; no spliced counterfactuals."""

from statistics import mean

from epistemics.source_learning.battery import costs


def metrics(report, policy):
    rows = []
    for j, company in enumerate(report.manifest.companies[12:]):
        before = report.observations[12 + 2 * j].answer
        final = report.observations[13 + 2 * j].answer
        truth = company.record.public.resolved_strong
        cost = costs(company)["customer_panel"] if policy == "always" else 0.0
        gross = float(truth) - company.threshold if final.decision == "invest" else 0.0
        rows.append(
            {
                "company_id": company.company_id,
                "threshold": company.threshold,
                "check_price": costs(company)["customer_panel"],
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
        "check_count": 12 if policy == "always" else 0,
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
        "scope": "Twelve later companies only; outcome errors are realized categories, not access to beliefs or expected decision optimality; fictional points, not money",
    }


def contrast(none, always):
    if [(r["company_id"], r["threshold"], r["check_price"]) for r in none["rows"]] != [
        (r["company_id"], r["threshold"], r["check_price"]) for r in always["rows"]
    ]:
        raise ValueError("Compare matched companies only")
    return {
        "net_payoff_gain": always["mean_net_payoff"] - none["mean_net_payoff"],
        "gross_payoff_gain": always["mean_gross_payoff"] - none["mean_gross_payoff"],
        "brier_change": always["mean_final_brier"] - none["mean_final_brier"],
        "additional_check_cost_per_company": (always["total_check_cost"] - none["total_check_cost"])
        / 12,
    }


def gate(contrasts):
    if len(contrasts) != 2:
        raise ValueError("The feasibility gate requires both frozen worlds")
    gains = [c["net_payoff_gain"] for c in contrasts]
    return {
        "mean_net_payoff_gain": mean(gains),
        "both_worlds_nonnegative": min(gains) >= -1e-12,
        "passed": mean(gains) >= 0.01 - 1e-12 and min(gains) >= -1e-12,
        "scope": "Small development gate, not a validated policy or population confidence claim",
    }
