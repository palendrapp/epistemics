"""Deterministic, task-conditional readings of existing reports; no new trait fitting."""

import hashlib
import json
from datetime import UTC, datetime

from epistemics.company.models import CompanyReport
from epistemics.discovery.analysis import growth_report
from epistemics.discovery.models import DiscoveryReport
from epistemics.models import Report
from epistemics.participants import (
    AgentConfiguration,
    AgentParticipant,
    EvaluationConditions,
    SessionContext,
)
from epistemics.passport import INTERPRETATION_VERSION, PASSPORT_VERSION
from epistemics.passport.models import (
    DIMENSIONS,
    CandidateSupport,
    Dimension,
    EvidenceReference,
    Measurement,
    ObservationExample,
    Passport,
    SourceArtifact,
)

CONTRACTS = {
    "epistemics.report.v1": Report,
    "epistemics.report.v2": CompanyReport,
    "epistemics.report.v3": DiscoveryReport,
}
LIMITATIONS = [
    "Draft derived from one completed report; this is not a completed standard passport battery.",
    "Descriptions are provisional and task-conditional; no human or agent population norms are used.",
    "Reported probabilities do not provide direct access to internal beliefs or unique mechanisms.",
    "The source schema is validated; imported metrics and execution are not independently verified.",
    "Response origin is an operator assertion. Unspecified origin must not be treated as a real agent.",
    "Source reports remain private local artifacts; no publishing, signing or on-chain issuance occurs.",
]


def refs(*pointers):
    return [EvidenceReference(json_pointer=p) for p in pointers]


def pointer_value(data, pointer):
    value = data
    for part in pointer.split("/")[1:]:
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def metric(data, pointer, label, unit, *, scale=1, reference=None):
    return Measurement(
        label=label,
        value=pointer_value(data, pointer) * scale,
        unit=unit,
        reference=reference,
        method="Descriptive statistic imported from source report",
        evidence=refs(pointer),
    )


def parameter(report, name, label, reference=1):
    p = report.parameters[name]
    return Measurement(
        label=label,
        value=p.estimate,
        unit="weight",
        reference=reference,
        interval_95=p.interval_95,
        method=p.method,
        limitations=p.warnings,
        evidence=refs(f"/parameters/{name}"),
    )


def example(text, *pointers):
    return ObservationExample(description=text, evidence=refs(*pointers))


def dimension(key, summary, *, measurements=(), examples=(), limits=(), identified=True):
    return Dimension(
        dimension_id=key,
        title=DIMENSIONS[key],
        evidence_status="provisional" if identified else "insufficient_evidence",
        summary=summary,
        measurements=list(measurements),
        examples=list(examples),
        limitations=list(limits) or ["One run; repeatability across contexts is not established."],
    )


def empty_dimensions():
    return {
        key: dimension(
            key,
            "This report does not contain enough evidence to characterize this dimension.",
            identified=False,
        )
        for key in DIMENSIONS
    }


def weight_description(p, label):
    value = p.estimate
    if p.interval_95 is not None and p.interval_95[0] <= 1 <= p.interval_95[1]:
        return (
            f"{label} was estimated at {value:.3f}; its within-run interval includes reference 1."
        )
    if abs(value - 1) < 0.0005:
        return f"{label} matched reference 1 to the displayed precision ({value:.3f})."
    relation = "less" if value < 1 else "more"
    return (
        f"{label} received {relation} weight than the disclosed reference ({value:.3f} versus 1)."
    )


def belief_dimensions(report, data):
    dims = empty_dimensions()
    index = max(
        (i for i, o in enumerate(report.observations) if o.trial.task == "evidence_integration"),
        key=lambda i: abs(
            report.observations[i].answer.probability - report.observations[i].truth["reference"]
        ),
    )
    o = report.observations[index]
    dims["evidence_weighting"] = dimension(
        "evidence_weighting",
        weight_description(report.parameters["evidence_weight"], "New evidence")
        + " "
        + weight_description(report.parameters["prior_weight"], "Prior information"),
        measurements=[
            parameter(report, "evidence_weight", "New evidence weight"),
            parameter(report, "prior_weight", "Prior information weight"),
        ],
        examples=[
            example(
                f"At prior {o.trial.stimulus['prior_h']:.0%}, reported probability was "
                f"{o.answer.probability:.1%}; the disclosed model gives {o.truth['reference']:.1%}. "
                "This is the trial with the largest absolute reference discrepancy.",
                f"/observations/{index}",
            )
        ],
        limits=[
            "Explicit numeric likelihoods: instruction interpretation and arithmetic can affect these weights.",
            "Weight comparisons are descriptive, not population bias diagnoses; intervals are within-run only.",
        ],
    )
    dims["source_judgment"] = dimension(
        "source_judgment",
        weight_description(report.parameters["source_update_weight"], "Source-reliability updates"),
        measurements=[
            parameter(report, "source_update_weight", "Source update weight"),
            parameter(report, "source_prior_weight", "Source prior weight"),
            metric(
                data,
                "/metrics/source_validity/reference_rmse",
                "Source reference RMSE",
                "pp",
                scale=100,
                reference=0,
            ),
        ],
        limits=[
            "The source model and starting reliability are supplied; spontaneous reputation effects are unmeasured."
        ],
    )
    fits = report.model_fits
    dims["belief_revision"] = dimension(
        "belief_revision",
        "A fixed learning-rate rule and a changing-regime model describe this sequence. "
        "Their errors on held-out reports indicate fit, not which internal mechanism was used.",
        measurements=[
            Measurement(
                label=name.replace("_", " "),
                value=fit.parameter,
                unit="model parameter",
                method="Fitted on the first 32 reports",
                evidence=refs(f"/model_fits/{name}"),
                limitations=[
                    f"Near-optimal range {fit.near_optimal_range}; a sensitivity range, not a confidence interval."
                ],
            )
            for name, fit in fits.items()
        ]
        + [
            metric(
                data, f"/model_fits/{name}/heldout_rmse", f"{name}: held-out RMSE", "pp", scale=100
            )
            for name in fits
        ],
        limits=["One outcome sequence does not establish a general updating-speed tendency."],
    )
    dims["uncertainty_and_calibration"] = dimension(
        "uncertainty_and_calibration",
        "Forecast scores are available for the 24 evidence-integration trials. "
        "This run does not establish general calibration or overconfidence.",
        measurements=[
            metric(
                data,
                "/metrics/evidence_integration/brier",
                "Evidence-task Brier score",
                "Brier",
                reference=0,
            ),
            metric(
                data,
                "/metrics/evidence_integration/log_loss",
                "Evidence-task log loss",
                "nats",
                reference=0,
            ),
        ],
        limits=[
            "Outcome scores depend on the task distribution; lower proper scores indicate better forecasts."
        ],
    )
    return dims


def company_change(report, index, field="growth_probability"):
    before, after = report.observations[index - 1], report.observations[index]
    p, q = getattr(before.answer, field), getattr(after.answer, field)
    return example(
        f"In {after.trial.episode_id}, {field.replace('_', ' ')} moved "
        f"from {p:.1%} to {q:.1%} at step {after.trial.step} ({(q - p) * 100:+.1f} pp).",
        f"/observations/{index - 1}/answer/{field}",
        f"/observations/{index}",
    )


def company_dimensions(report, data):
    dims = empty_dimensions()
    fit = report.model_fits["weighted_evidence"]
    positive = report.parameters["positive_weight"].estimate
    negative = report.parameters["negative_weight"].estimate
    dims["evidence_weighting"] = dimension(
        "evidence_weighting",
        (
            f"Under the weighted-evidence model, favorable evidence weight was {positive:.3f} "
            f"and unfavorable evidence weight was {negative:.3f}; the reference is 1 for each."
            if fit.identified
            else "This run does not separate the weighted-evidence parameters; no directional interpretation is assigned."
        ),
        measurements=[
            parameter(report, "positive_weight", "Favorable evidence weight"),
            parameter(report, "negative_weight", "Unfavorable evidence weight"),
            metric(
                data,
                "/model_fits/weighted_evidence/heldout_rmse",
                "Weighted model held-out RMSE",
                "pp",
                scale=100,
            ),
        ],
        examples=[company_change(report, 1)],
        identified=fit.identified,
        limits=fit.warnings
        + [
            "Positive/negative refers to evidence about the target, not emotional wording.",
            "Output gain and retention are fixed; these weights do not uniquely identify input mechanisms.",
        ],
    )
    dims["source_judgment"] = dimension(
        "source_judgment",
        "Source-reliability reports can be compared with the disclosed joint model; an audit example shows the observed revision.",
        measurements=[
            metric(
                data,
                "/metrics/source_probability/reference_rmse",
                "Source reference RMSE",
                "pp",
                scale=100,
            )
        ],
        examples=[company_change(report, 6, "source_probability")],
        limits=[
            "This measures use of supplied source information, not a source-prestige parameter."
        ],
    )
    dims["belief_revision"] = dimension(
        "belief_revision",
        "The checkpoints show how the company judgment changes after a source audit and an auxiliary-explanation check.",
        examples=[company_change(report, 6), company_change(report, 7)],
        limits=[
            "These are observations in a disclosed model, not a fitted general persistence trait."
        ],
    )
    redundant = [i for i, o in enumerate(report.observations) if o.truth.redundant]
    index = max(
        redundant,
        key=lambda i: abs(
            report.observations[i].answer.growth_probability
            - report.observations[i - 1].answer.growth_probability
        ),
    )
    update = report.diagnostics["mean_absolute_update_on_redundant_items"] * 100
    dims["dependence_and_causal_reasoning"] = dimension(
        "dependence_and_causal_reasoning",
        f"Company probabilities changed by {update:.2f} pp on average when a document added no independent observation under the disclosed model.",
        measurements=[
            metric(
                data,
                "/diagnostics/mean_absolute_update_on_redundant_items",
                "Mean absolute redundant-item update",
                "pp",
                scale=100,
                reference=0,
            ),
        ]
        + (
            [parameter(report, "duplicate_weight", "Duplicate-counting coefficient", reference=0)]
            if fit.identified
            else []
        ),
        examples=[company_change(report, index)],
        limits=[
            "The example is the largest absolute change on a redundant item, not a representative random trial.",
            "The coefficient is conditional on the weighted model; causal reasoning is only partially covered.",
        ]
        + fit.warnings,
    )
    dims["uncertainty_and_calibration"] = dimension(
        "uncertainty_and_calibration",
        "Forecast and interval performance is based on six company outcomes, with repeated checkpoints within each company.",
        measurements=[
            metric(
                data,
                "/metrics/growth_probability/final_brier",
                "Final growth Brier score",
                "Brier",
                reference=0,
            ),
            metric(
                data,
                "/diagnostics/final_80pct_interval_coverage",
                "Final 80% interval coverage",
                "%",
                scale=100,
                reference=80,
            ),
        ],
        limits=[
            "Six outcomes are insufficient to establish a stable calibration trait; 54 checkpoints are not 54 independent outcomes."
        ],
    )
    dims["decision_consistency"] = decision_dimension(
        data,
        "/diagnostics/decision_report_agreement",
        len(report.observations),
        "The choices use a supplied binary payoff and linear utility; agreement does not identify risk preferences.",
    )
    return dims


def decision_dimension(data, pointer, count, limit):
    agreement = pointer_value(data, pointer)
    return dimension(
        "decision_consistency",
        f"Choices agreed with the expected-payoff action implied by reported probabilities at {agreement:.1%} of {count} checkpoints.",
        measurements=[
            metric(data, pointer, "Decision/report agreement", "%", scale=100, reference=100)
        ],
        limits=[limit],
    )


def discovery_change(report, index, label):
    before, after = report.observations[index - 1 : index + 1]
    p = growth_report(before.trial, before.answer)
    q = growth_report(after.trial, after.answer)
    return example(
        f"{label}: P(growth > 12%) moved from {p:.1%} to {q:.1%} ({100 * (q - p):+.1f} pp).",
        f"/observations/{index - 1}",
        f"/observations/{index}",
    )


def discovery_dimensions(report, data):
    dims = empty_dimensions()
    dims[
        "evidence_weighting"
    ].summary = (
        "This single discovery case does not estimate evidence weights or a negativity parameter."
    )
    audit = 6
    last_sources = {}
    for index, observation in enumerate(report.observations[:audit]):
        for name, probability in observation.answer.source_accuracy.items():
            last_sources[name] = (probability, index)
    source_examples = []
    for name, q in report.observations[audit].answer.source_accuracy.items():
        if name in last_sources:
            p, index = last_sources[name]
            source_examples.append(
                example(
                    f"Reported accuracy for {name} was {p:.1%} at checkpoint {index} "
                    f"and {q:.1%} at audit checkpoint {audit}; other evidence arrived between probes.",
                    f"/observations/{index}/answer/source_accuracy",
                    f"/observations/{audit}/answer/source_accuracy",
                )
            )
    dims["source_judgment"] = dimension(
        "source_judgment",
        "Source accuracy was elicited initially and again at the audit. Changes include intervening evidence; a stable source-impression bias is not fitted.",
        examples=source_examples,
        identified=bool(source_examples),
        limits=[
            "Source accuracy means the probability that the next comparable raw estimate is within 2 percentage points of a later audit.",
            "Source histories and probes belong to one authored case; transfer is unmeasured.",
        ],
    )
    dims["belief_revision"] = dimension(
        "belief_revision",
        "The trajectory shows revision after a source audit and a provenance reveal. Observer errors describe candidate explanations of these reports.",
        examples=[
            discovery_change(report, 6, "Source audit"),
            discovery_change(report, 7, "Provenance reveal"),
        ],
        measurements=[
            metric(
                data,
                f"/observer_models/{name}/growth_report_rmse",
                f"{name}: report RMSE",
                "pp",
                scale=100,
            )
            for name in report.observer_models
        ],
        limits=[
            "Candidate observers are modeling assumptions; a closer fit does not diagnose a unique cognitive mechanism."
        ],
    )
    update = report.metrics["derived_model_absolute_probability_update"] * 100
    dims["dependence_and_causal_reasoning"] = dimension(
        "dependence_and_causal_reasoning",
        f"The derived-model document changed the company probability by {update:.2f} pp. The provenance reveal provides a separate dependency observation.",
        measurements=[
            metric(
                data,
                "/metrics/derived_model_absolute_probability_update",
                "Absolute derived-model update",
                "pp",
                scale=100,
            ),
            metric(
                data,
                "/metrics/lineage_reveal_absolute_probability_update",
                "Absolute provenance-reveal update",
                "pp",
                scale=100,
            ),
        ],
        examples=[
            discovery_change(report, 4, "Derived model"),
            discovery_change(report, 7, "Provenance reveal"),
        ],
        limits=[
            "These are single-case changes; zero change alone does not establish dependency awareness."
        ],
    )
    final = report.observations[-1].answer.growth_quantiles_pct
    dims["uncertainty_and_calibration"] = dimension(
        "uncertainty_and_calibration",
        "One resolved company outcome supports descriptive forecast scores, but cannot establish calibration.",
        measurements=[
            metric(data, "/metrics/final_brier", "Final Brier score", "Brier", reference=0)
        ],
        examples=[
            example(
                f"Final 80% growth interval: [{final.p10:.2f}%, {final.p90:.2f}%]; "
                f"realized growth: {report.private_case.realized_growth_pct:.2f}%.",
                "/observations/9/answer/growth_quantiles_pct",
                "/private_case/realized_growth_pct",
            )
        ],
        limits=[
            "Ten checkpoints share a single outcome; no general confidence or calibration label is assigned."
        ],
    )
    dims["decision_consistency"] = decision_dimension(
        data,
        "/metrics/decision_report_agreement",
        len(report.observations),
        "Agreement concerns one binary payoff task and does not identify risk preferences. Failure-worded probabilities are complemented before interpretation.",
    )
    return dims


def build_passport(raw: bytes, *, response_origin="unspecified", created_at=None) -> Passport:
    data = json.loads(raw)
    if isinstance(data, dict) and data.get("schema_version") == "epistemics.report.v4":
        from epistemics.live.passport import build_core_passport

        return build_core_passport(raw, response_origin=response_origin, created_at=created_at)
    if (
        isinstance(data, dict)
        and data.get("schema_version") == "epistemics.investigation-collection.v1"
    ):
        from epistemics.passport.investigation import build_investigation_passport

        return build_investigation_passport(
            raw, response_origin=response_origin, created_at=created_at
        )
    contract = CONTRACTS.get(data.get("schema_version")) if isinstance(data, dict) else None
    if contract is None:
        raise ValueError(
            "Passport import supports completed report.v1–v4 or investigation collection artifacts only"
        )
    if response_origin not in {"agent", "synthetic", "unspecified"}:
        raise ValueError("Legacy agent reports cannot be relabeled as human responses")
    report = contract.model_validate(data)
    digest = hashlib.sha256(raw).hexdigest()
    participant = AgentParticipant(
        subject_id=report.agent.agent_id,
        configuration=AgentConfiguration(
            **report.agent.model_dump(exclude={"agent_id", "context_policy"})
        ),
    )
    context = SessionContext(
        session_id=report.session_id,
        participant=participant,
        response_origin=response_origin,
        protocol_version=report.battery_version,
        protocol_sha256=report.battery_sha256,
        evaluator_version=report.evaluator_version,
        conditions=EvaluationConditions(context_policy=report.agent.context_policy),
        started_at=report.started_at,
        completed_at=report.completed_at,
        completion="complete",
        accepted_answers=len(report.observations),
        planned_answers=len(report.observations),
    )
    try:
        if isinstance(report, Report):
            dimensions = belief_dimensions(report, data)
        elif isinstance(report, CompanyReport):
            dimensions = company_dimensions(report, data)
        else:
            dimensions = discovery_dimensions(report, data)
    except (KeyError, ValueError) as error:
        raise ValueError(
            f"Source report lacks required measurements or observations: {error}"
        ) from error
    supports = []
    if isinstance(report, Report):
        p = report.parameters["evidence_weight"]
        if p.estimate < 0.9995 and p.interval_95 is not None and p.interval_95[1] < 1:
            supports.append(
                CandidateSupport(
                    dimension_id="evidence_weighting",
                    hypothesis="Structured review may help integrate new independent evidence; the fitted weight does not identify the cause.",
                    support="Show an evidence ledger separating prior assumptions, new observations, source reliability and dependencies.",
                    evaluation_needed="Compare baseline, generic review and this support on fresh weak, strong and duplicated-evidence cases; measure forecast quality and cost.",
                    evidence=refs("/parameters/evidence_weight"),
                )
            )
    identity = json.dumps(
        [PASSPORT_VERSION, INTERPRETATION_VERSION, digest, response_origin], separators=(",", ":")
    ).encode()
    passport = Passport(
        passport_id=hashlib.sha256(identity).hexdigest(),
        created_at=created_at or datetime.now(UTC),
        context=context,
        source=SourceArtifact(schema_version=report.schema_version, sha256=digest),
        dimensions=list(dimensions.values()),
        support_candidates=supports,
        limitations=LIMITATIONS + report.limitations,
    )
    # Every displayed observation/statistic has a resolvable location in the exact source artifact.
    for item in passport.dimensions:
        for entry in [*item.measurements, *item.examples]:
            for ref in entry.evidence:
                pointer_value(data, ref.json_pointer)
    return passport


def verify_derivation(passport: Passport, raw: bytes) -> None:
    if hashlib.sha256(raw).hexdigest() != passport.source.sha256:
        raise ValueError("Source report bytes do not match the passport digest")
    expected = build_passport(
        raw, response_origin=passport.context.response_origin, created_at=passport.created_at
    )
    if passport != expected:
        raise ValueError("Passport differs from its deterministic source-report interpretation")
