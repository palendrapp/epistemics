import { address, type KeyPairSigner } from "@solana/kit";
import { verifyPassportAttestation } from "../passports.js";
import { sha256 } from "../records.js";
import {
  BINDING_DOMAIN,
  type ConsumerDecision,
  type ConsumerRequest,
  type ProviderBinding,
  validate,
} from "./contracts.js";
import { type FetchPolicy, fetchBytes, parseJson } from "./http.js";
import { measurements, type PassportView } from "./metrics.js";
import {
  type DeploymentPin,
  NETWORK,
  type RegistryTransport,
  resolveIdentity,
} from "./registry.js";
import {
  type Signed,
  sign,
  timestamp,
  validity,
  verify,
} from "./signatures.js";
import { verifyStatusHistory } from "./status.js";

export async function createProviderBinding(
  payload: ProviderBinding,
  signer: KeyPairSigner,
): Promise<Signed<ProviderBinding>> {
  if (payload.signer !== signer.address)
    throw new Error("Binding signer mismatch");
  if (timestamp(payload.expires_at) <= timestamp(payload.issued_at))
    throw new Error("Binding expiry must follow issuance");
  const result = await sign(payload, BINDING_DOMAIN, signer);
  validate("binding", result);
  return result;
}

export interface ConsumerOptions {
  requestBytes: Uint8Array;
  policyBytes: Uint8Array;
  agentAsset: string;
  transport: RegistryTransport;
  retrieval: FetchPolicy;
  bindingUri?: string;
  minimumStatusSequence?: string;
  rememberedStatus?: Record<string, { sequence: string; sha256: string }>;
  now?: Date;
  simulationPin?: DeploymentPin;
}

/** An inspectable policy recommendation. It never sends a service request or payment. */
export async function evaluate(
  options: ConsumerOptions,
): Promise<ConsumerDecision> {
  const request = validate("request", parseJson(options.requestBytes));
  const policy = validate("policy", parseJson(options.policyBytes));
  const now = options.now ?? new Date();
  const endTimes = [now.valueOf() + policy.receipt_ttl_seconds * 1000];
  const result: ConsumerDecision = {
    schema_version: "epistemics.consumer-decision.v1",
    action: "eligible",
    mode: options.transport.mode,
    payment_authorized: false,
    task_id: request.task_id,
    request_sha256: sha256(options.requestBytes),
    policy_sha256: sha256(options.policyBytes),
    passport_sha256: null,
    attestation_sha256: null,
    binding_sha256: null,
    status_sha256: null,
    status_sequence: null,
    registry_snapshot_sha256: null,
    issued_at: now.toISOString(),
    expires_at: new Date(endTimes[0]!).toISOString(),
    reasons: [],
    measurements: [],
  };
  function reason(
    code: string,
    disposition: "review_required" | "ineligible",
    detail: string,
    metric: string | null = null,
  ) {
    result.reasons.push({ code, disposition, detail, metric_id: metric });
  }
  function finish() {
    result.action = result.reasons.some((r) => r.disposition === "ineligible")
      ? "ineligible"
      : result.reasons.length
        ? "review_required"
        : "eligible";
    // A failure still has a bounded receipt lifetime; it confers no permission.
    result.expires_at = new Date(
      Math.max(now.valueOf(), Math.min(...endTimes)),
    ).toISOString();
    return validate("decision", result);
  }
  function fresh(issued: string, maxAge: number, code: string) {
    const t = timestamp(issued);
    endTimes.push(t + maxAge * 1000);
    if (t > now.valueOf() || now.valueOf() >= t + maxAge * 1000)
      reason(
        code,
        "review_required",
        "Evidence is outside the policy freshness window.",
      );
  }
  if (
    new Set(policy.trusted_issuers.map((i) => i.issuer)).size !==
      policy.trusted_issuers.length ||
    new Set(policy.measurements.map((m) => m.metric_id)).size !==
      policy.measurements.length ||
    policy.measurements.some(
      (m) =>
        (m.minimum === null && m.maximum === null) ||
        (m.minimum !== null && m.maximum !== null && m.minimum > m.maximum),
    )
  )
    throw new Error("Ambiguous or empty policy requirement");
  for (const issuer of policy.trusted_issuers) address(issuer.issuer);
  address(request.payee);
  address(request.payment_asset);
  const endpoint = new URL(request.endpoint);
  if (
    endpoint.protocol !== "https:" ||
    endpoint.username ||
    endpoint.password ||
    endpoint.hash
  )
    reason(
      "ENDPOINT_UNSUPPORTED",
      "ineligible",
      "Service endpoint must use HTTPS without credentials or a fragment.",
    );
  if (request.task_id !== policy.task_id)
    reason(
      "TASK_MISMATCH",
      "ineligible",
      "Request is outside this policy's task scope.",
    );
  if (
    request.payment_network !== NETWORK ||
    request.payment_network !== policy.payment_network ||
    request.payment_asset !== policy.payment_asset ||
    BigInt(request.max_amount) > BigInt(policy.max_amount)
  )
    reason(
      "PAYMENT_SCOPE_MISMATCH",
      "ineligible",
      "Network, asset or maximum amount exceeds the policy.",
    );
  if (result.reasons.length) return finish();

  let identity;
  try {
    identity = await resolveIdentity(
      options.agentAsset,
      options.transport,
      now,
      options.simulationPin,
    );
  } catch {
    reason(
      "IDENTITY_UNAVAILABLE_OR_CHANGED",
      "review_required",
      "Current identity and pinned deployment could not be verified.",
    );
    return finish();
  }
  result.registry_snapshot_sha256 = sha256(JSON.stringify(identity));
  if (identity.subject_agent_id !== request.subject_agent_id) {
    reason(
      "SUBJECT_MISMATCH",
      "ineligible",
      "Resolved chain/program/asset differs from the requested subject.",
    );
    return finish();
  }
  let bindingInput;
  try {
    let uri = options.bindingUri;
    if (!uri) {
      const metadata = parseJson(
        await fetchBytes(identity.metadata_uri, options.retrieval),
      ) as {
        extensions?: { epistemics?: { provider_binding_uri?: string } };
      };
      uri = metadata.extensions?.epistemics?.provider_binding_uri;
    }
    if (!uri) throw new Error("No binding reference");
    bindingInput = parseJson(await fetchBytes(uri, options.retrieval));
  } catch {
    reason(
      "BINDING_UNAVAILABLE",
      "review_required",
      "No retrievable provider binding within configured origins.",
    );
    return finish();
  }

  let binding;
  try {
    binding = validate("binding", bindingInput);
    const p = binding.payload;
    if (
      p.subject_agent_id !== identity.subject_agent_id ||
      p.genesis_hash !== identity.genesis_hash ||
      p.registry_program !== identity.registry_program ||
      p.agent_asset !== identity.agent_asset ||
      p.controller !== identity.controller ||
      ![identity.controller, identity.operational_wallet].includes(p.signer)
    )
      throw new Error("Current authority mismatch");
    await verify(binding, BINDING_DOMAIN, p.signer);
    validity(p.issued_at, p.expires_at, now);
    result.binding_sha256 = binding.payload_sha256;
    fresh(p.issued_at, policy.max_binding_age_seconds, "BINDING_STALE");
    endTimes.push(timestamp(p.expires_at));
  } catch {
    reason(
      "BINDING_INVALID",
      "ineligible",
      "Provider binding signature, current authority or validity failed.",
    );
    return finish();
  }
  const b = binding.payload;
  for (const field of [
    "configuration_sha256",
    "endpoint",
    "payee",
    "payment_network",
    "payment_asset",
  ] as const) {
    if (b[field] !== request[field])
      reason(
        `PROVIDER_${field.toUpperCase()}_MISMATCH`,
        "ineligible",
        `Current provider binding differs at ${field}.`,
      );
  }
  if (result.reasons.some((r) => r.disposition === "ineligible"))
    return finish();

  let passportBytes, attestationInput;
  try {
    [passportBytes, attestationInput] = await Promise.all([
      fetchBytes(b.passport_uri, options.retrieval),
      fetchBytes(b.attestation_uri, options.retrieval).then(parseJson),
    ]);
  } catch {
    reason(
      "PASSPORT_UNAVAILABLE",
      "review_required",
      "Passport or attestation could not be retrieved within configured origins.",
    );
    return finish();
  }
  const claimedIssuer = (
    attestationInput as { payload?: { issuer?: string } } | null
  )?.payload?.issuer;
  const trust = policy.trusted_issuers.find((i) => i.issuer === claimedIssuer);
  if (!trust) {
    reason(
      "ISSUER_UNTRUSTED",
      "ineligible",
      "Issuer is not in the buyer's trust policy.",
    );
    return finish();
  }
  let attestation;
  try {
    attestation = await verifyPassportAttestation(
      attestationInput,
      passportBytes,
      { expectedIssuer: trust.issuer, now },
    );
    const p = attestation.payload;
    if (
      p.passport_sha256 !== b.passport_sha256 ||
      p.passport_uri !== b.passport_uri ||
      p.subject_agent_id !== request.subject_agent_id ||
      p.configuration_sha256 !== request.configuration_sha256
    )
      throw new Error("Attestation binding mismatch");
    result.passport_sha256 = p.passport_sha256;
    result.attestation_sha256 = attestation.attestation_sha256;
    endTimes.push(Date.parse(p.expires_at));
  } catch {
    reason(
      "PASSPORT_INVALID_OR_EXPIRED",
      "ineligible",
      "Passport bytes, signed metadata or attestation validity failed.",
    );
    return finish();
  }
  const p = attestation.payload;
  if (p.response_origin !== "agent")
    reason(
      "ORIGIN_NOT_AGENT",
      "ineligible",
      "Synthetic or unspecified responses cannot qualify an agent.",
    );
  if (
    p.protocol_sha256 !== policy.protocol_sha256 ||
    p.protocol_version !== policy.protocol_version ||
    p.interpretation_version !== policy.interpretation_version
  )
    reason(
      "PROTOCOL_UNSUPPORTED",
      "review_required",
      "Passport protocol or interpretation is outside the declared policy.",
    );
  if (policy.require_verified_execution)
    reason(
      "EXECUTION_UNVERIFIED",
      "review_required",
      "This attestation supports operator-asserted execution only.",
    );
  if (policy.require_predictive_validation)
    reason(
      "PREDICTIVE_SCOPE_UNSUPPORTED",
      "review_required",
      "Core passport.v2 does not establish predictive validity for this task.",
    );
  if (!policy.allow_provisional)
    reason(
      "PROVISIONAL_EVIDENCE",
      "review_required",
      "The policy does not accept the current provisional profile.",
    );
  const passport = parseJson(passportBytes) as PassportView;
  const completed = Date.parse(passport.context.completed_at);
  if (!Number.isFinite(completed))
    throw new Error("Invalid evaluation completion time");
  fresh(
    new Date(completed).toISOString(),
    policy.max_evaluation_age_seconds,
    "EVALUATION_STALE",
  );

  let history;
  try {
    const base = new URL(trust.status_base_uri);
    if (!base.pathname.endsWith("/") || base.search || base.hash)
      throw new Error("Invalid status base URI");
    history = parseJson(
      await fetchBytes(
        new URL(`${attestation.attestation_sha256}.json`, base).href,
        options.retrieval,
      ),
    );
  } catch {
    reason(
      "STATUS_UNAVAILABLE",
      "review_required",
      "Required issuer status is unavailable.",
    );
    return finish();
  }
  try {
    const remembered =
      options.rememberedStatus?.[attestation.attestation_sha256];
    const status = await verifyStatusHistory(
      history,
      trust.issuer,
      attestation.attestation_sha256,
      {
        now,
        ...((remembered?.sequence ?? options.minimumStatusSequence) ===
        undefined
          ? {}
          : {
              minimumSequence:
                remembered?.sequence ?? options.minimumStatusSequence!,
            }),
      },
    );
    if (
      remembered &&
      (history as { payload_sha256: string }[])[Number(remembered.sequence)]
        ?.payload_sha256 !== remembered.sha256
    )
      throw new Error("Issuer equivocation at remembered sequence");
    if (timestamp(status.payload.issued_at) < Date.parse(p.issued_at))
      throw new Error("Status predates issuance");
    result.status_sha256 = status.payload_sha256;
    result.status_sequence = status.payload.sequence;
    if (status.payload.evaluated_controller !== identity.controller)
      reason(
        "EVALUATED_CONTROLLER_MISMATCH",
        "ineligible",
        "Current controller differs from the issuer's evaluated-controller binding; require fresh issuer evidence.",
      );
    fresh(
      status.payload.issued_at,
      policy.max_status_age_seconds,
      "STATUS_STALE",
    );
    endTimes.push(timestamp(status.payload.expires_at));
    if (status.payload.status !== "active")
      reason(
        `PASSPORT_${status.payload.status.toUpperCase()}`,
        "ineligible",
        "Issuer has withdrawn or corrected this attestation; a replacement needs a new decision.",
      );
  } catch {
    reason(
      "STATUS_INVALID_OR_ROLLED_BACK",
      "review_required",
      "Status signature, history, validity or remembered sequence failed.",
    );
    return finish();
  }

  try {
    result.measurements = measurements(passport);
  } catch {
    reason(
      "METRICS_UNSUPPORTED",
      "review_required",
      "Measurement mapping is ambiguous or unsupported.",
    );
    return finish();
  }
  for (const requirement of policy.measurements) {
    const m = result.measurements.find(
      (entry) => entry.metric_id === requirement.metric_id,
    );
    if (!m || m.evidence_status !== "provisional") {
      reason(
        "MEASUREMENT_MISSING",
        "review_required",
        "Required measurement has insufficient coverage.",
        requirement.metric_id,
      );
      continue;
    }
    const interval =
      requirement.uncertainty === "point" ? [m.value, m.value] : m.interval_95;
    if (!interval) {
      reason(
        "UNCERTAINTY_MISSING",
        "review_required",
        "Policy requires a 95% interval that is unavailable.",
        requirement.metric_id,
      );
      continue;
    }
    if (
      (requirement.minimum !== null && interval[0]! < requirement.minimum) ||
      (requirement.maximum !== null && interval[1]! > requirement.maximum)
    )
      reason(
        "MEASUREMENT_OUTSIDE_POLICY",
        "ineligible",
        "Measurement does not meet the declared threshold and uncertainty rule.",
        requirement.metric_id,
      );
  }
  return finish();
}

/** Scope check for a trusted in-process result, NOT authentication of a supplied receipt.
 * Decisions are unsigned local recommendations; re-resolve/re-evaluate before payment.
 */
export function matchesReceipt(
  decision: ConsumerDecision,
  requestBytes: Uint8Array,
  policyBytes: Uint8Array,
  now = new Date(),
): boolean {
  validate("decision", decision);
  validate("request", parseJson(requestBytes));
  validate("policy", parseJson(policyBytes));
  return (
    decision.action === "eligible" &&
    decision.mode === "rpc_observed" &&
    sha256(requestBytes) === decision.request_sha256 &&
    sha256(policyBytes) === decision.policy_sha256 &&
    timestamp(decision.issued_at) <= now.valueOf() &&
    timestamp(decision.expires_at) > now.valueOf()
  );
}

export function requestBytes(request: ConsumerRequest): Uint8Array {
  validate("request", request);
  return Buffer.from(`${JSON.stringify(request, null, 2)}\n`);
}
