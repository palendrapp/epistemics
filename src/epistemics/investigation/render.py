"""Readable developmental results alongside the private machine-readable reports."""


def render(reports):
    origin = reports[0].manifest.response_origin
    rows = [
        "# Company investigation: development results",
        "",
        f"Response origin: **{origin}**. {len(reports)} episodes, four checkpoints each.",
        "",
        "These results describe the observed tasks. Model comparisons are conditional on "
        "the specified observer family and reporting assumptions. They do not establish "
        "an internal mechanism, stable trait, validated passport dimension or benefit from assistance.",
        "",
    ]
    for i, report in enumerate(reports, 1):
        a = report.analysis
        rows.extend(
            [
                f"## Episode {i}",
                "",
                f"Mode: {report.assignment.mode}. "
                f"Research choice: **{a['research']['selected']}**. "
                f"Committed decision: **{report.observations[2].answer.decision}**.",
                "",
                "| Checkpoint | Growth >12% | Source understates | Backlog >22 | Decision |",
                "| --- | ---: | ---: | ---: | --- |",
            ]
        )
        for name, observation in zip(
            (
                "Background",
                "Operating report / research choice",
                "Research result / commitment",
                "Transcription review",
            ),
            report.observations,
            strict=True,
        ):
            answer = observation.answer
            rows.append(
                f"| {name} | {answer.growth_probability:.0%} | "
                f"{answer.audit_understatement_probability:.0%} | "
                f"{answer.backlog_high_probability:.0%} | {answer.decision} |"
            )
        rows.extend(
            [
                "",
                f"Growth forecast revision after correction: **{a['correction_revision_pp'][0]:+.1f} probability points**; "
                f"conditional joint reference: {a['conditional_reference_revision_pp'][0]:+.1f}.",
                "",
                "| Research option | Expected gain from information | Cost | Net value |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for name, value in a["research"]["conditional_reference_values"].items():
            rows.append(
                f"| {name} | {value['gross_value']:.4f} | {value['cost']:.4f} | {value['net_value']:.4f} |"
            )
        rows.extend(
            [
                "",
                "Research values are in hypothetical payoff points under the reference model, "
                "for the committed decision before correction. Discovery participants were not given that model.",
                "",
                "| Candidate observer | Report RMSE (probability points) | Report log likelihood |",
                "| --- | ---: | ---: |",
            ]
        )
        for name, fit in a["candidate_comparisons"].items():
            rows.append(
                f"| {name} | {fit['report_rmse_pp']:.2f} | {fit['report_log_likelihood']:.2f} |"
            )
        rows.extend(
            [
                "",
                "A best-fitting candidate can still fit poorly, and a single episode cannot establish a reliable individual profile.",
                "",
            ]
        )
    return "\n".join(rows)
