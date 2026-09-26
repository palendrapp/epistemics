"""Offline, script-free renderings of the same machine-readable passport."""

import html
import re

from epistemics.passport.models import Passport

LABELS = {
    "provisional": "Provisional observations",
    "insufficient_evidence": "Insufficient evidence",
}
ORIGINS = {
    "synthetic": "SYNTHETIC DEMONSTRATION · not a real participant evaluation",
    "unspecified": "RESPONSE ORIGIN UNSPECIFIED · do not assume a real agent run",
    "agent": "AGENT RESPONSES · operator-asserted execution",
    "human": "HUMAN RESPONSES · operator-asserted execution",
}


def number(value):
    return f"{value:.4g}"


def measurement_value(measurement):
    result = f"{number(measurement.value)} {measurement.unit}"
    if measurement.reference is not None:
        result += f"; reference {number(measurement.reference)}"
    if measurement.interval_95 is not None:
        lo, hi = measurement.interval_95
        result += f"; reported 95% interval [{number(lo)}, {number(hi)}]"
    return result


def md(value):
    # Imported identifiers and labels must not become markup, links or raw HTML.
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", html.escape(str(value))).replace("\n", " ")


def scope_description(passport):
    if passport.scope == "investigation_battery_provisional_profile":
        return f"All 12 investigation cases and 48 checkpoints are complete ({passport.evaluation_mode}). Behavioral observations are provisional; cognitive fits and initialization assumptions remain development diagnostics."
    if passport.scope == "core_battery_provisional_profile":
        return "All 34 core checkpoints are complete. Interpretations remain provisional and task-conditional."
    return "A completed source evaluation is not a complete standard passport battery."


def render_markdown(passport: Passport) -> str:
    context = passport.context
    subject = context.participant
    text = [
        "# Epistemic passport",
        "",
        "**Draft · unsigned · provisional core profile**"
        if passport.scope == "core_battery_provisional_profile"
        else "**Draft · unsigned · provisional investigation profile**"
        if passport.scope == "investigation_battery_provisional_profile"
        else "**Draft · unsigned · partial profile**",
        "",
        f"**{ORIGINS[context.response_origin]}**",
        "",
        f"Subject: {md(subject.subject_id)} ({subject.kind}).",
        f"Protocol: {md(context.protocol_version)}. Accepted checkpoints: {context.accepted_answers}.",
        scope_description(passport),
        "",
    ]
    if subject.kind == "agent":
        text += [
            f"Model: {md(subject.configuration.model)} / {md(subject.configuration.model_version)}.",
            "",
        ]
    for dimension in passport.dimensions:
        text += [
            f"## {md(dimension.title)}",
            "",
            f"*{LABELS[dimension.evidence_status]}*",
            "",
            md(dimension.summary),
            "",
        ]
        for observation in dimension.examples:
            text += [
                f"- {md(observation.description)}",
                f"  Evidence: {md(', '.join(r.json_pointer for r in observation.evidence))}",
            ]
        if dimension.examples:
            text.append("")
        for measurement in dimension.measurements:
            text += [
                f"- **{md(measurement.label)}:** {md(measurement_value(measurement))}",
                f"  Method: {md(measurement.method)}. Evidence: {md(', '.join(r.json_pointer for r in measurement.evidence))}",
            ]
            text += [f"  {md(note)}" for note in measurement.limitations]
        text += ["", *[f"- Limit: {md(note)}" for note in dimension.limitations], ""]
    if passport.schema_version == "epistemics.passport.v3":
        text += [
            "## Model explanations · development only",
            "",
            "These fits are alternative explanations of this run. They are not validated traits or evidence of intervention benefit.",
            "",
            "| Initialization | Source feedback | Report response | RMSE (points) | Adequacy |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
        for name, fit in passport.model_diagnostics.fits.items():
            text.append(
                f"| {md(name)} | {fit['coupling_grid_estimate']:.2f} | {fit['response_rate_grid_estimate']:.2f} | {fit['report_rmse_pp']:.2f} | {md(fit['status'])} |"
            )
        text += [
            "",
            "Conditional grid intervals are not calibrated trait uncertainty. The eight-point fit diagnostic is a development convention.",
            "",
        ]
    if passport.schema_version == "epistemics.passport.v4":
        text += [
            "## Source-learning scope",
            "",
            f"Binding: {md(passport.subject_binding)}. Presentation: {md(passport.presentation)}. Elicitation: {md(passport.condition)}.",
            "",
            "Original subject IDs: " + md(", ".join(passport.source_subject_ids)),
            "",
            "## Model explanations · development only",
            "",
            "These are within-session prediction diagnostics, separate from repeatability, external transfer and outcome quality. No fitted parameter is a validated trait.",
            "",
            "| Session | Fitted later-report RMSE | Fixed joint RMSE | All candidates inadequate |",
            "| --- | ---: | ---: | --- |",
        ]
        for name, fit in passport.model_diagnostics.fits.items():
            errors = fit["heldout_behavior_rmse_pp"]
            text.append(
                f"| {md(name)} | {errors['frozen_mixture']:.2f} | {errors['fixed_joint_observer']:.2f} | {fit['all_candidates_inadequate']} |"
            )
        text += ["", "### Matched repeats", ""]
        if not passport.repeatability:
            text += ["No matched repeated sessions; repeatability is unmeasured.", ""]
        for world in passport.repeatability:
            for pair in world["pairs"]:
                text.append(
                    f"- World {world['world_number']}, sessions {[i + 1 for i in pair['sessions']]}: {pair['rmse_pp']:.2f} probability points RMS across twelve unaudited forecasts."
                )
        text.append("")
    text += ["## Support to test", ""]
    if not passport.support_candidates:
        text += [
            "No targeted support is proposed from this report. No intervention has been tested.",
            "",
        ]
    for support in passport.support_candidates:
        text += [
            f"**Untested candidate — {md(support.dimension_id)}**",
            "",
            md(support.hypothesis),
            "",
            md(support.support),
            "",
            md(support.evaluation_needed),
            "",
            f"Evidence: {md(', '.join(r.json_pointer for r in support.evidence))}",
            "",
        ]
    text += [
        "## Conditions and provenance",
        "",
        "```json",
        context.model_dump_json(indent=2),
        "```",
        "",
        f"Source SHA-256: `{passport.source.sha256}`",
        f"Source schema: `{passport.source.schema_version}`",
        f"Passport ID: `{passport.passport_id}`",
        f"Interpretation: `{passport.interpretation_version}`",
        f"Generated: {passport.created_at.isoformat()}",
        "",
        "## Scope and limitations",
        "",
        *[f"- {md(note)}" for note in passport.limitations],
        "",
    ]
    # JSON metadata can contain literal backticks; use a fence longer than any content run.
    metadata = context.model_dump_json(indent=2)
    fence = "`" * max(3, 1 + max((len(x) for x in re.findall(r"`+", metadata)), default=0))
    text = [
        fence + "json" if line == "```json" else fence if line == "```" else line for line in text
    ]
    return "\n".join(text)


CSS = """
:root{color-scheme:light;--ink:#192d2c;--muted:#536b68;--line:#d7dfd7;--paper:#fffefa;--green:#205b48}
*{box-sizing:border-box}body{margin:0;background:#eff2eb;color:var(--ink);font:16px/1.6 system-ui,sans-serif}
main{max-width:1120px;margin:auto;padding:48px 28px}h1{font-size:clamp(34px,5vw,58px);letter-spacing:-.04em;line-height:1.1;margin:12px 0}
h2{font-size:23px;line-height:1.25;margin:12px 0}h3{font-size:17px}p{margin:12px 0}.eyebrow{text-transform:uppercase;letter-spacing:.15em;font-size:12px;font-weight:700}
.lede{max-width:760px;font-size:18px}.muted{color:var(--muted)}.origin{padding:12px 18px;border-left:4px solid var(--green);background:#e0ebdf;margin:22px 0;font-size:13px;font-weight:650}
.meta{display:flex;flex-wrap:wrap;gap:20px;margin:24px 0 32px}.meta div{min-width:170px;flex:1}.meta dt{font-size:12px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}.meta dd{margin:5px 0;overflow-wrap:anywhere;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:25px;overflow-wrap:anywhere}
.status{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--green);font-weight:700}.insufficient_evidence .status{color:#7b6245}
.example{background:#f0f4ed;border-radius:7px;padding:12px 15px;font-size:14px}.evidence{font:11px/1.5 ui-monospace,monospace;color:var(--muted);overflow-wrap:anywhere}
details{margin-top:20px;border-top:1px solid var(--line);padding-top:12px}summary{cursor:pointer;font-weight:600;font-size:14px}.measure{padding:10px 0;border-bottom:1px solid var(--line)}.measure strong{font-size:14px}.value{font:14px/1.6 ui-monospace,monospace}.method,.limits{font-size:13px;color:var(--muted)}ul{padding-left:20px}.wide{margin-top:22px}pre{font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere}code{font-family:ui-monospace,monospace;overflow-wrap:anywhere}a{color:var(--green)}footer{margin:26px 0;font-size:12px;color:var(--muted)}
@media(max-width:740px){main{padding:25px 16px}.grid{grid-template-columns:1fr}.card{padding:20px}}
@media print{body{background:white}main{padding:0;max-width:none}.grid{display:block}.card{margin-bottom:16px;break-inside:avoid}details{display:block}.origin{background:white}}
"""


def render_html(passport: Passport) -> str:
    escape = html.escape
    context = passport.context
    subject = context.participant

    def evidence(items):
        return (
            '<p class="evidence">Source pointers: '
            + escape(", ".join(r.json_pointer for r in items))
            + "</p>"
        )

    def notes(items):
        return (
            '<ul class="limits">' + "".join(f"<li>{escape(note)}</li>" for note in items) + "</ul>"
        )

    cards = []
    for dimension in passport.dimensions:
        observations = "".join(
            '<div class="example">' + escape(o.description) + evidence(o.evidence) + "</div>"
            for o in dimension.examples
        )
        measurements = "".join(
            '<div class="measure"><strong>'
            + escape(m.label)
            + '</strong><div class="value">'
            + escape(measurement_value(m))
            + '</div><p class="method">'
            + escape(m.method)
            + "</p>"
            + notes(m.limitations)
            + evidence(m.evidence)
            + "</div>"
            for m in dimension.measurements
        )
        details = (
            "<details><summary>Measurements and evidence</summary>" + measurements + "</details>"
            if measurements
            else ""
        )
        cards.append(
            f'<section class="card {dimension.evidence_status}"><span class="status">'
            + LABELS[dimension.evidence_status]
            + "</span><h2>"
            + escape(dimension.title)
            + "</h2><p>"
            + escape(dimension.summary)
            + "</p>"
            + observations
            + details
            + notes(dimension.limitations)
            + "</section>"
        )
    supports = (
        "".join(
            '<div class="example"><strong>Untested candidate</strong><p>'
            + escape(s.hypothesis)
            + "</p><p>"
            + escape(s.support)
            + "</p><p>"
            + escape(s.evaluation_needed)
            + "</p>"
            + evidence(s.evidence)
            + "</div>"
            for s in passport.support_candidates
        )
        or "<p>No targeted support is proposed from this report. No intervention has been tested.</p>"
    )
    provenance = (
        f"<p>Source schema: <code>{escape(passport.source.schema_version)}</code></p>"
        f"<p>Exact source SHA-256: <code>{passport.source.sha256}</code></p>"
        f"<p>Passport ID: <code>{passport.passport_id}</code></p>"
        f"<p>Interpretation: <code>{escape(passport.interpretation_version)}</code></p>"
        f"<p>Generated: {escape(passport.created_at.isoformat())}</p>"
        "<details><summary>Recorded session conditions</summary><pre>"
        + escape(context.model_dump_json(indent=2))
        + "</pre></details>"
    )
    diagnostic_html = ""
    if passport.schema_version == "epistemics.passport.v3":
        rows = "".join(
            f"<tr><td>{escape(name)}</td><td>{fit['coupling_grid_estimate']:.2f}</td><td>{fit['response_rate_grid_estimate']:.2f}</td><td>{fit['report_rmse_pp']:.2f}</td><td>{escape(fit['status'])}</td></tr>"
            for name, fit in passport.model_diagnostics.fits.items()
        )
        diagnostic_html = (
            '<section class="card wide"><h2>Model explanations · development only</h2><p>These fits are alternative explanations of this run. They are not validated traits or evidence of intervention benefit.</p><div style="overflow-x:auto"><table><thead><tr><th>Initialization</th><th>Source feedback</th><th>Report response</th><th>RMSE (points)</th><th>Adequacy</th></tr></thead><tbody>'
            + rows
            + '</tbody></table></div><p class="limits">Conditional intervals are not calibrated trait uncertainty. The eight-point fit diagnostic is a development convention.</p></section>'
        )
    if passport.schema_version == "epistemics.passport.v4":
        rows = "".join(
            f"<tr><td>{escape(name)}</td><td>{fit['heldout_behavior_rmse_pp']['frozen_mixture']:.2f}</td><td>{fit['heldout_behavior_rmse_pp']['fixed_joint_observer']:.2f}</td><td>{fit['all_candidates_inadequate']}</td></tr>"
            for name, fit in passport.model_diagnostics.fits.items()
        )
        repeats = "".join(
            f"<li>World {world['world_number']}, sessions {escape(str([i + 1 for i in pair['sessions']]))}: {pair['rmse_pp']:.2f} points RMS over twelve matched forecasts.</li>"
            for world in passport.repeatability
            for pair in world["pairs"]
        )
        diagnostic_html = (
            '<section class="card wide"><h2>Source-learning scope</h2><p>'
            + escape(
                f"Binding: {passport.subject_binding}; presentation: {passport.presentation}; elicitation: {passport.condition}."
            )
            + "</p><p>Original subjects: "
            + escape(", ".join(passport.source_subject_ids))
            + "</p><h3>Matched repeats</h3>"
            + (
                "<ul>" + repeats + "</ul>"
                if repeats
                else "<p>No matched repeated sessions; repeatability is unmeasured.</p>"
            )
            + '<h3>Model explanations · development only</h3><p>Within-session prediction errors in probability points. These are separate from external transfer, outcome quality and stable traits.</p><div style="overflow-x:auto"><table><thead><tr><th>Session</th><th>Fitted error</th><th>Fixed joint error</th><th>All candidates inadequate</th></tr></thead><tbody>'
            + rows
            + "</tbody></table></div></section>"
        )
    model = subject.configuration.model if subject.kind == "agent" else "Human participant"
    heading_subject = (
        "configuration"
        if getattr(passport, "subject_binding", None) == "configuration_cohort"
        else "decision maker"
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
        "<title>Epistemic passport · "
        + escape(subject.subject_id)
        + "</title><style>"
        + CSS
        + f'</style></head><body><main><header><div class="eyebrow">Epistemics / {escape(passport.passport_version)}</div>'
        f'<h1>How this {heading_subject}<br>uses evidence.</h1><p class="lede">'
        "Observed behavior, its supporting measurements, and the limits of this evaluation.</p>"
        '<p class="muted">Draft · unsigned · private local artifact</p>'
        '<div class="origin">' + ORIGINS[context.response_origin] + '</div><dl class="meta">'
        "<div><dt>Subject</dt><dd>" + escape(subject.subject_id) + "</dd></div>"
        "<div><dt>Participant</dt><dd>" + escape(model) + "</dd></div>"
        "<div><dt>Protocol</dt><dd>" + escape(context.protocol_version) + "</dd></div>"
        f"<div><dt>Accepted checkpoints</dt><dd>{context.accepted_answers}</dd></div></dl>"
        '<p class="muted">'
        + escape(scope_description(passport))
        + ' Dimensions below remain provisional or insufficiently measured.</p></header><div class="grid">'
        + "".join(cards)
        + "</div>"
        + diagnostic_html
        + '<section class="card wide"><h2>Support to test</h2>'
        + supports
        + '</section><section class="card wide"><h2>Conditions and provenance</h2>'
        + provenance
        + '</section><section class="card wide"><h2>Scope and limitations</h2>'
        + notes(passport.limitations)
        + "</section><footer>Evidence pointers refer to the exact source "
        "report, which remains separate. This rendering does not publish or authenticate execution."
        "</footer></main></body></html>\n"
    )
