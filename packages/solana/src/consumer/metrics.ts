import type { ConsumerDecision } from "./contracts.js";

// Catalog binds existing signed observations by exact source pointer and unit,
// never by display labels. Version separately from unchanged passport.v2 bytes.
export const METRIC_CATALOG = [
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

export interface PassportView {
  interpretation_version: string;
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
  if (passport.interpretation_version !== "passport-interpretation/0.2.0")
    throw new Error("Unsupported metric interpretation version");
  return METRIC_CATALOG.flatMap((metric) => {
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
