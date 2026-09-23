"""Evidence-linked development summary; no automatic passport trait issuance."""

from epistemics.investigation.inference import answer_vector
from epistemics.investigation3.inference import INITIALIZATIONS, fit


def collection_analysis(reports, hashes):
    pairs = []
    for query in ("source_audit", "operations_check", "segment_check"):
        pair = {
            r.assignment.price_condition: r for r in reports if r.assignment.focused_query == query
        }
        low, high = (pair[k] for k in ("low", "high"))
        pairs.append(
            {
                "query": query,
                "pair_id": low.assignment.pair_id,
                "low_price_choice": low.observations[1].answer.query,
                "high_price_choice": high.observations[1].answer.query,
                "pre_purchase_report_difference_pp": [
                    100 * (a - b)
                    for a, b in zip(
                        answer_vector(low.observations[1].answer),
                        answer_vector(high.observations[1].answer),
                        strict=True,
                    )
                ],
                "interpretation": "Matched evidence and pre-sampled outcomes, different prices, separate contexts. A single pair does not establish stable price sensitivity.",
            }
        )
    return {
        "schema_version": "epistemics.investigation-summary.v3",
        "response_origin": reports[0].manifest.response_origin,
        "manifest_sha256": reports[0].manifest_sha256,
        "source_report_hashes": hashes,
        "episodes": len(reports),
        "checkpoints": 4 * len(reports),
        "coverage": {
            "review_offsets": [
                r.assignment.offset for r in reports if r.assignment.family == "review"
            ],
            "prospective_research_cases": sum(r.assignment.family == "research" for r in reports),
        },
        "conditional_fit": fit([r.observations for r in reports]),
        "initialization_fits": {
            m: fit([r.observations for r in reports], initialization=m) for m in INITIALIZATIONS
        },
        "matched_prices": pairs,
        "release_status": "development_only_not_a_passport",
        "unmeasured": [
            "real-participant repeatability",
            "new-case empirical prediction",
            "unrestricted hypothesis generation",
            "intervention benefit",
        ],
    }


def render(reports, aggregate):
    fit = aggregate["conditional_fit"]
    lines = [
        "# Investigation 0.3: development evidence",
        "",
        f"Response origin: **{aggregate['response_origin']}**. {len(reports)} cases, {4 * len(reports)} checkpoints.",
        "",
        "These are task-conditional reports and exploratory fits. They do not identify internal beliefs, stable traits or intervention benefit.",
        "",
        f"Conditional model fit: **{fit['status']}**, RMSE **{fit['report_rmse_pp']:.2f} probability points**. Source-feedback coupling {fit['coupling_grid_estimate']:.2f}; report response rate {fit['response_rate_grid_estimate']:.2f}. These are parameters of this observer family, using the declared noisy initial-response model; no passport label is issued.",
        "",
        "The collection includes two reviews in each offset direction, three matched research-price pairs, and prospective query forecasts in six cases. Detailed report hashes and conditional grid intervals are in analysis.json.",
        "",
    ]
    for i, r in enumerate(reports, 1):
        lines += [
            f"## Case {i}",
            "",
            f"{r.assignment.family.capitalize()} case. Mode: {r.assignment.mode}. Chosen research: **{r.observations[1].answer.query}**.",
            "",
            "| Stage | Growth >12% | Source understate | Backlog >22 | Decision |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
        for o in r.observations:
            a = o.answer
            lines.append(
                f"| {o.trial.stage} | {a.growth_probability:.0%} | {a.audit_understatement_probability:.0%} | {a.backlog_high_probability:.0%} | {a.decision} |"
            )
        lines += [
            "",
            f"Verified transcription offset: {r.assignment.offset:+.0f} points. Growth report revision: {r.analysis['correction_revision_pp'][0]:+.1f} probability points.",
            "",
            f"Decisions consistent with reported probability/payoff: {r.analysis['decision_probability_agreements']}/4.",
            "",
        ]
        own = r.analysis["research"]["reported_expectations"]
        if own:
            lines += [
                f"Prospective forecast coherence within rounding tolerance: **{own['coherence_within_rounding_tolerance']}**. Largest total-probability discrepancy: {own['max_mixture_gap_pp']:.2f} points.",
                "",
                "| Check | Expected benefit from reported forecasts | Cost | Net |",
                "| --- | ---: | ---: | ---: |",
            ]
            for name, v in own["values"].items():
                lines.append(
                    f"| {name} | {v['gross_value']:.4f} | {v['cost']:.4f} | {v['net_value']:.4f} |"
                )
            lines += [
                "",
                "When prospective answers are incoherent, these values are descriptive arithmetic, not an identified research preference.",
                "",
            ]
        lines += ["| Conditional candidate | RMSE, probability points |", "| --- | ---: |"]
        for name, c in r.analysis["candidate_comparisons"].items():
            lines.append(f"| {name} | {c['report_rmse_pp']:.2f} |")
        lines.append("")
    return "\n".join(lines)
