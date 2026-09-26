import type { ConsumerDecision } from "./contracts.js";

// Catalog binds existing signed observations by exact source pointer and unit,
// never by display labels. Version separately from unchanged passport.v2 bytes.
const CORE_METRICS = [
  {
    id: "core.calibration.evidence_weight.v1",
    dimension: "evidence_weighting",
    pointer: "/calibration/parameters/evidence_weight",
    unit: "weight",
  },
  {
    id: "core.calibration.prior_weight.v1",
    dimension: "evidence_weighting",
    pointer: "/calibration/parameters/prior_weight",
    unit: "weight",
  },
  {
    id: "core.calibration.reference_rmse.v1",
    dimension: "uncertainty_and_calibration",
    pointer: "/calibration/metrics/reference_rmse",
    unit: "pp",
  },
  {
    id: "core.calibration.brier.v1",
    dimension: "uncertainty_and_calibration",
    pointer: "/calibration/metrics/brier",
    unit: "Brier",
  },
  {
    id: "core.discovery.final_brier.v1",
    dimension: "uncertainty_and_calibration",
    pointer: "/discovery/metrics/final_brier",
    unit: "Brier",
  },
  {
    id: "core.discovery.derived_update.v1",
    dimension: "dependence_and_causal_reasoning",
    pointer: "/discovery/metrics/derived_model_absolute_probability_update",
    unit: "pp",
  },
  {
    id: "core.discovery.provenance_update.v1",
    dimension: "dependence_and_causal_reasoning",
    pointer: "/discovery/metrics/lineage_reveal_absolute_probability_update",
    unit: "pp",
  },
  {
    id: "core.discovery.decision_agreement.v1",
    dimension: "decision_consistency",
    pointer: "/discovery/metrics/decision_report_agreement",
    unit: "%",
  },
] as const;

const INVESTIGATION_METRICS = [
  {
    id: "investigation.decision_agreement.v1",
    dimension: "decision_consistency",
    pointer: "/facts/decision_agreement_percent",
    unit: "%",
  },
  {
    id: "investigation.research_policy_agreement.v1",
    dimension: "decision_consistency",
    pointer: "/facts/research_policy_agreement_percent",
    unit: "%",
  },
  {
    id: "investigation.research_coherence.v1",
    dimension: "uncertainty_and_calibration",
    pointer: "/facts/research_coherence_percent",
    unit: "%",
  },
  {
    id: "investigation.prospective_mixture_gap.v1",
    dimension: "uncertainty_and_calibration",
    pointer: "/facts/prospective_max_mixture_gap_pp",
    unit: "pp",
  },
  {
    id: "investigation.correction_direction.v1",
    dimension: "belief_revision",
    pointer: "/facts/correction_direction_agreement_percent",
    unit: "%",
  },
  {
    id: "investigation.resolved_event_retention.v1",
    dimension: "belief_revision",
    pointer: "/facts/resolved_probe_agreement_percent",
    unit: "%",
  },
  {
    id: "investigation.source_persistence.v1",
    dimension: "source_judgment",
    pointer: "/facts/source_persistence_percent",
    unit: "%",
  },
  {
    id: "investigation.source_revision.v1",
    dimension: "source_judgment",
    pointer: "/facts/source_revision_mean_absolute_pp",
    unit: "pp",
  },
  {
    id: "investigation.coverage.correction_cases.v1",
    dimension: "belief_revision",
    pointer: "/coverage/nonzero_review_cases",
    unit: "count",
  },
  {
    id: "investigation.coverage.resolved_checks.v1",
    dimension: "belief_revision",
    pointer: "/coverage/resolved_probe_checks",
    unit: "count",
  },
  {
    id: "investigation.coverage.research_cases.v1",
    dimension: "uncertainty_and_calibration",
    pointer: "/coverage/research_cases",
    unit: "count",
  },
  {
    id: "investigation.coverage.policy_cases.v1",
    dimension: "decision_consistency",
    pointer: "/coverage/research_policy_cases",
    unit: "count",
  },
  {
    id: "investigation.coverage.decisions.v1",
    dimension: "decision_consistency",
    pointer: "/coverage/checkpoints",
    unit: "count",
  },
  {
    id: "investigation.coverage.unique_worlds.v1",
    dimension: "decision_consistency",
    pointer: "/coverage/unique_worlds",
    unit: "count",
  },
] as const;

const SOURCE_METRICS = [
  {
    id: "source.decision_agreement.v1",
    dimension: "decision_consistency",
    pointer: "/facts/decision_agreement_percent",
    unit: "%",
  },
  {
    id: "source.final_brier.v1",
    dimension: "uncertainty_and_calibration",
    pointer: "/facts/final_brier",
    unit: "Brier",
  },
  {
    id: "source.repeat_rmse.v1",
    dimension: "uncertainty_and_calibration",
    pointer: "/facts/repeat_rmse_pp",
    unit: "pp",
  },
  {
    id: "source.mean_payoff.v1",
    dimension: "decision_consistency",
    pointer: "/facts/mean_payoff_per_company",
    unit: "points",
  },
  ...["customer_panel", "selection_audit", "measurement_audit", "stop"].map(
    (q) => ({
      id: `source.research.${q}.v1`,
      dimension: "source_judgment",
      pointer: `/facts/research_${q}_percent`,
      unit: "%",
    }),
  ),
  ...["sessions", "unique_worlds", "companies", "checkpoints"].map((k) => ({
    id: `source.coverage.${k}.v1`,
    dimension: "decision_consistency",
    pointer: `/coverage/${k}`,
    unit: "count",
  })),
  ...["repeat_pairs", "repeat_worlds", "matched_forecasts_per_pair"].map(
    (k) => ({
      id: `source.coverage.${k}.v1`,
      dimension: "uncertainty_and_calibration",
      pointer: `/coverage/${k}`,
      unit: "count",
    }),
  ),
  ...["research_choices", "source_judgments"].map((k) => ({
    id: `source.coverage.${k}.v1`,
    dimension: "source_judgment",
    pointer: `/coverage/${k}`,
    unit: "count",
  })),
] as const;
export const METRIC_CATALOG = [
  ...CORE_METRICS,
  ...INVESTIGATION_METRICS,
  ...SOURCE_METRICS,
];

export interface PassportView {
  interpretation_version: string;
  presentation?: string;
  condition?: string;
  subject_binding?: string;
  evaluation_mode?: "discovery" | "calibration";
  context: { completed_at: string };
  dimensions: {
    dimension_id: string;
    evidence_status: string;
    measurements: {
      value: number;
      unit: string;
      interval_95: [number, number] | null;
      evidence: { artifact_id: string; json_pointer: string }[];
    }[];
  }[];
}

/** Call only after passport schema/signature verification. No derivation claim. */
export function measurements(
  passport: PassportView,
): ConsumerDecision["measurements"] {
  if (
    passport.interpretation_version === "passport-interpretation/0.3.0" &&
    passport.evaluation_mode !== "discovery"
  )
    throw new Error(
      "Investigation metric policies currently support discovery mode only",
    );
  if (
    passport.interpretation_version === "passport-interpretation/0.4.0" &&
    (passport.presentation !== "structured" ||
      passport.condition !== "sparse" ||
      passport.subject_binding !== "single_subject")
  )
    throw new Error(
      "Source metric policies currently qualify single-subject sparse structured evidence only",
    );
  const catalog =
    passport.interpretation_version === "passport-interpretation/0.2.0"
      ? CORE_METRICS
      : passport.interpretation_version === "passport-interpretation/0.3.0"
        ? INVESTIGATION_METRICS
        : passport.interpretation_version === "passport-interpretation/0.4.0"
          ? SOURCE_METRICS
          : null;
  if (!catalog) throw new Error("Unsupported metric interpretation version");
  return catalog.flatMap((metric) => {
    const dimension = passport.dimensions.find(
      (d) => d.dimension_id === metric.dimension,
    );
    const candidates =
      dimension?.measurements.filter(
        (m) =>
          m.unit === metric.unit &&
          m.evidence.length === 1 &&
          m.evidence[0]!.artifact_id === "source-report" &&
          m.evidence[0]!.json_pointer === metric.pointer,
      ) ?? [];
    if (candidates.length > 1) throw new Error("Ambiguous metric mapping");
    const m = candidates[0];
    if (!m) return [];
    if (
      !Number.isFinite(m.value) ||
      (m.interval_95 !== null &&
        (!m.interval_95.every(Number.isFinite) ||
          m.interval_95[0] > m.interval_95[1]))
    )
      throw new Error("Invalid measurement");
    return [
      {
        metric_id: metric.id,
        value: m.value,
        unit: m.unit,
        interval_95: m.interval_95,
        evidence_pointer: metric.pointer,
        evidence_status: dimension!.evidence_status,
      },
    ];
  });
}
