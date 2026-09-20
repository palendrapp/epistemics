import { Ajv2020 } from "ajv/dist/2020.js";
import decisionSchema from "../../../../schemas/consumer-decision.v1.json" with {
  type: "json",
};
import policySchema from "../../../../schemas/consumer-policy.v1.json" with {
  type: "json",
};
import requestSchema from "../../../../schemas/consumer-request.v1.json" with {
  type: "json",
};
import statusSchema from "../../../../schemas/passport-status.v1.json" with {
  type: "json",
};
import bindingSchema from "../../../../schemas/provider-binding.v1.json" with {
  type: "json",
};
import type { Signed } from "./signatures.js";

export const BINDING_DOMAIN = "epistemics/provider-binding-signature/v1\n";
export const STATUS_DOMAIN = "epistemics/passport-status-signature/v1\n";

export interface ProviderBinding {
  schema_version: "epistemics.provider-binding.v1";
  genesis_hash: string;
  registry_program: string;
  agent_asset: string;
  subject_agent_id: string;
  controller: string;
  signer: string;
  configuration_sha256: string;
  passport_sha256: string;
  passport_uri: string;
  attestation_uri: string;
  endpoint: string;
  payee: string;
  payment_network: string;
  payment_asset: string;
  issued_at: string;
  expires_at: string;
}

export interface PassportStatus {
  schema_version: "epistemics.passport-status.v1";
  issuer: string;
  evaluated_controller: string;
  attestation_sha256: string;
  sequence: string;
  previous_sha256: string;
  status: "active" | "withdrawn" | "corrected";
  replacement_attestation_sha256: string;
  reason: string;
  issued_at: string;
  expires_at: string;
}

export interface ConsumerRequest {
  schema_version: "epistemics.consumer-request.v1";
  subject_agent_id: string;
  configuration_sha256: string;
  task_id: string;
  endpoint: string;
  method: "POST";
  body_sha256: string;
  payee: string;
  payment_network: string;
  payment_asset: string;
  max_amount: string;
  nonce: string;
}

export interface ConsumerPolicy {
  schema_version: "epistemics.consumer-policy.v1";
  policy_id: string;
  version: string;
  task_id: string;
  trusted_issuers: { issuer: string; status_base_uri: string }[];
  protocol_sha256: string;
  protocol_version: string;
  interpretation_version: string;
  max_evaluation_age_seconds: number;
  max_status_age_seconds: number;
  max_binding_age_seconds: number;
  receipt_ttl_seconds: number;
  require_verified_execution: boolean;
  require_predictive_validation: boolean;
  allow_provisional: boolean;
  measurements: {
    metric_id: string;
    minimum: number | null;
    maximum: number | null;
    uncertainty: "point" | "entire_95_interval";
  }[];
  payment_network: string;
  payment_asset: string;
  max_amount: string;
}

export interface ConsumerDecision {
  schema_version: "epistemics.consumer-decision.v1";
  action: "eligible" | "review_required" | "ineligible";
  mode: "rpc_observed" | "simulation";
  payment_authorized: false;
  task_id: string;
  request_sha256: string;
  policy_sha256: string;
  passport_sha256: string | null;
  attestation_sha256: string | null;
  binding_sha256: string | null;
  status_sha256: string | null;
  status_sequence: string | null;
  registry_snapshot_sha256: string | null;
  issued_at: string;
  expires_at: string;
  reasons: {
    code: string;
    disposition: "review_required" | "ineligible";
    detail: string;
    metric_id: string | null;
  }[];
  measurements: {
    metric_id: string;
    value: number;
    unit: string;
    interval_95: [number, number] | null;
    evidence_pointer: string;
    evidence_status: string;
  }[];
}

const ajv = new Ajv2020({ strict: true, allErrors: true });
const validators = {
  binding: ajv.compile<Signed<ProviderBinding>>(bindingSchema),
  status: ajv.compile<Signed<PassportStatus>>(statusSchema),
  policy: ajv.compile<ConsumerPolicy>(policySchema),
  request: ajv.compile<ConsumerRequest>(requestSchema),
  decision: ajv.compile<ConsumerDecision>(decisionSchema),
};
type Contracts = {
  binding: Signed<ProviderBinding>;
  status: Signed<PassportStatus>;
  policy: ConsumerPolicy;
  request: ConsumerRequest;
  decision: ConsumerDecision;
};
export function validate<K extends keyof Contracts>(
  kind: K,
  value: unknown,
): Contracts[K] {
  const validator = validators[kind];
  if (!validator(value))
    throw new Error(`Invalid ${kind}: ${ajv.errorsText(validator.errors)}`);
  return value as Contracts[K];
}
