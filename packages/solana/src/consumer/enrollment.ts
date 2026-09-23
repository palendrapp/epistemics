/** Enrollment precedes collection. It cannot re-label a completed evaluation. */
import { randomUUID } from "node:crypto";
import { isDeepStrictEqual } from "node:util";
import { address, type KeyPairSigner } from "@solana/kit";
import { Ajv2020 } from "ajv/dist/2020.js";
import participantSchema from "../../../../schemas/participant.v1.json" with {
  type: "json",
};
import enrollmentSchema from "../../../../schemas/provider-enrollment.v1.json" with {
  type: "json",
};
import { createPassportAttestation } from "../passports.js";
import { sha256 } from "../records.js";
import { createProviderBinding } from "./evaluate.js";
import {
  type DeploymentPin,
  NETWORK,
  type RegistryIdentity,
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
import { createStatus } from "./status.js";

export const ENROLLMENT_DOMAIN =
  "epistemics/provider-enrollment-signature/v1\n";
export interface Enrollment {
  schema_version: "epistemics.provider-enrollment.v1";
  enrollment_id: string;
  mode: RegistryTransport["mode"];
  genesis_hash: string;
  registry_program: string;
  agent_asset: string;
  subject_agent_id: string;
  controller: string;
  signer: string;
  issuer: string;
  protocol_version: string;
  participant_sha256: string;
  registry_snapshot_sha256: string;
  configuration_sha256: string;
  protocol_sha256: string;
  issued_at: string;
  expires_at: string;
}
export interface AgentParticipant {
  schema_version: "epistemics.participant.v1";
  kind: "agent";
  subject_id: string;
  configuration: {
    model: string;
    model_version: string;
    configuration_sha256: string;
    temperature?: number | null;
  };
}
export interface EnrollmentBundle {
  enrollment: Signed<Enrollment>;
  participantBytes: Uint8Array;
  registryBytes: Uint8Array;
}
interface RegistryOptions {
  transport: RegistryTransport;
  simulationPin?: DeploymentPin;
  now?: Date;
}
const ajv = new Ajv2020({ strict: true, allErrors: true });
ajv.addKeyword({ keyword: "discriminator", schemaType: "object", valid: true });
const checkEnrollment = ajv.compile<Signed<Enrollment>>(enrollmentSchema);
const checkParticipant = ajv.compile<AgentParticipant>(participantSchema);
export const jsonBytes = (value: unknown) =>
  Buffer.from(`${JSON.stringify(value, null, 2)}\n`);

function participant(bytes: Uint8Array): AgentParticipant {
  const value = JSON.parse(
    new TextDecoder("utf-8", { fatal: true }).decode(bytes),
  );
  if (!checkParticipant(value) || value.kind !== "agent")
    throw new Error("Valid agent participant required");
  return value;
}
function authorized(identity: RegistryIdentity, signer: string) {
  if (signer !== identity.controller && signer !== identity.operational_wallet)
    throw new Error(
      "Signer is not the current controller or operational wallet",
    );
}

export async function enrollProvider(
  options: RegistryOptions & {
    asset: string;
    authority: KeyPairSigner;
    issuer: string;
    configuration: AgentParticipant["configuration"];
    protocolVersion: string;
    protocolSha256: string;
    expiresAt: string;
  },
): Promise<EnrollmentBundle> {
  const now = options.now ?? new Date();
  validity(now.toISOString(), options.expiresAt, now);
  address(options.issuer);
  const identity = await resolveIdentity(
    options.asset,
    options.transport,
    now,
    options.simulationPin,
  );
  authorized(identity, options.authority.address);
  const participantBytes = jsonBytes({
    schema_version: "epistemics.participant.v1",
    kind: "agent",
    subject_id: identity.subject_agent_id,
    configuration: options.configuration,
  });
  participant(participantBytes);
  const registryBytes = jsonBytes(identity);
  const payload: Enrollment = {
    schema_version: "epistemics.provider-enrollment.v1",
    enrollment_id: randomUUID(),
    mode: identity.mode,
    genesis_hash: identity.genesis_hash,
    registry_program: identity.registry_program,
    agent_asset: identity.agent_asset,
    subject_agent_id: identity.subject_agent_id,
    controller: identity.controller,
    signer: options.authority.address,
    issuer: options.issuer,
    protocol_version: options.protocolVersion,
    protocol_sha256: options.protocolSha256,
    participant_sha256: sha256(participantBytes),
    registry_snapshot_sha256: sha256(registryBytes),
    configuration_sha256: options.configuration.configuration_sha256,
    issued_at: now.toISOString(),
    expires_at: options.expiresAt,
  };
  const enrollment = await sign(payload, ENROLLMENT_DOMAIN, options.authority);
  if (!checkEnrollment(enrollment))
    throw new Error("Invalid enrollment contract");
  return { enrollment, participantBytes, registryBytes };
}

export async function issueEnrolledPassport(
  options: RegistryOptions &
    EnrollmentBundle & {
      authority: KeyPairSigner;
      issuer: KeyPairSigner;
      passportBytes: Uint8Array;
      reportBytes: Uint8Array;
      passportUri: string;
      attestationUri: string;
      endpoint: string;
      payee: string;
      paymentAsset: string;
      expiresAt: string;
    },
) {
  if (!checkEnrollment(options.enrollment))
    throw new Error("Invalid enrollment contract");
  const p = options.enrollment.payload;
  const now = options.now ?? new Date();
  validity(p.issued_at, p.expires_at, now);
  validity(now.toISOString(), options.expiresAt, now);
  if (timestamp(options.expiresAt) > timestamp(p.expires_at))
    throw new Error("Issuance exceeds enrollment expiry");
  await verify(options.enrollment, ENROLLMENT_DOMAIN, p.signer);
  if (p.issuer !== options.issuer.address)
    throw new Error("Issuer differs from enrollment");
  if (p.mode !== options.transport.mode)
    throw new Error("Cannot promote simulation to live identity");
  if (
    sha256(options.participantBytes) !== p.participant_sha256 ||
    sha256(options.registryBytes) !== p.registry_snapshot_sha256
  )
    throw new Error("Enrollment artifact bytes changed");
  const enrolled = participant(options.participantBytes);
  const before = JSON.parse(
    new TextDecoder("utf-8", { fatal: true }).decode(options.registryBytes),
  ) as RegistryIdentity;
  if (
    before.mode !== p.mode ||
    before.controller !== p.controller ||
    before.subject_agent_id !== p.subject_agent_id ||
    before.agent_asset !== p.agent_asset ||
    before.genesis_hash !== p.genesis_hash ||
    before.registry_program !== p.registry_program ||
    before.observed_at !== p.issued_at
  )
    throw new Error("Enrollment registry binding mismatch");
  authorized(before, p.signer);
  const current = await resolveIdentity(
    p.agent_asset,
    options.transport,
    now,
    options.simulationPin,
  );
  if (
    current.controller !== p.controller ||
    current.subject_agent_id !== p.subject_agent_id ||
    current.genesis_hash !== p.genesis_hash ||
    current.registry_program !== p.registry_program ||
    current.slot < before.slot ||
    current.deployment_sha256 !== before.deployment_sha256
  )
    throw new Error(
      "Identity, authority or deployment changed since enrollment",
    );
  authorized(current, p.signer);
  authorized(current, options.authority.address);
  if (
    enrolled.subject_id !== p.subject_agent_id ||
    enrolled.configuration.configuration_sha256 !== p.configuration_sha256
  )
    throw new Error("Enrolled participant mismatch");
  // Existing passport/source schemas and exact-byte checks validate the artifact first.
  const attestation = await createPassportAttestation(
    options.passportBytes,
    options.reportBytes,
    options.issuer,
    {
      passportUri: options.passportUri,
      issuedAt: now.toISOString(),
      expiresAt: options.expiresAt,
    },
  );
  const passport = JSON.parse(
    new TextDecoder("utf-8", { fatal: true }).decode(options.passportBytes),
  );
  if (!isDeepStrictEqual(passport.context.participant, enrolled))
    throw new Error(
      "Evaluation participant differs from enrollment; never relabel an existing run",
    );
  if (Date.parse(passport.context.started_at) < timestamp(p.issued_at))
    throw new Error("Evaluation predates enrollment");
  if (
    attestation.payload.protocol_version !== p.protocol_version ||
    attestation.payload.protocol_sha256 !== p.protocol_sha256
  )
    throw new Error("Evaluation protocol differs from enrollment");
  if (
    p.mode === "rpc_observed" &&
    attestation.payload.response_origin !== "agent"
  )
    throw new Error("Live provider issuance requires agent-origin evaluation");
  if (
    p.mode === "simulation" &&
    attestation.payload.response_origin !== "synthetic"
  )
    throw new Error(
      "Local provider preview requires explicitly synthetic evaluation",
    );
  address(options.payee);
  address(options.paymentAsset);
  for (const value of [
    options.endpoint,
    options.passportUri,
    options.attestationUri,
  ]) {
    const uri = new URL(value);
    if (uri.protocol !== "https:" || uri.username || uri.password || uri.hash)
      throw new Error(
        "Provider and artifact URIs must be HTTPS without credentials or fragment",
      );
  }
  const binding = await createProviderBinding(
    {
      schema_version: "epistemics.provider-binding.v1",
      genesis_hash: current.genesis_hash,
      registry_program: current.registry_program,
      agent_asset: current.agent_asset,
      subject_agent_id: current.subject_agent_id,
      controller: current.controller,
      signer: options.authority.address,
      configuration_sha256: p.configuration_sha256,
      passport_sha256: sha256(options.passportBytes),
      passport_uri: options.passportUri,
      attestation_uri: options.attestationUri,
      endpoint: options.endpoint,
      payee: options.payee,
      payment_network: NETWORK,
      payment_asset: options.paymentAsset,
      issued_at: now.toISOString(),
      expires_at: options.expiresAt,
    },
    options.authority,
  );
  const status = await createStatus(
    [],
    options.issuer,
    attestation.attestation_sha256,
    {
      status: "active",
      evaluated_controller: current.controller,
      replacement_attestation_sha256: "",
      reason: `Issuance for enrollment ${p.enrollment_id}`,
      issued_at: now.toISOString(),
      expires_at: options.expiresAt,
    },
  );
  return {
    attestation,
    binding,
    status,
    registry: current,
    receipt: {
      schema_version: "epistemics.provider-issuance-receipt.v1",
      enrollment_sha256: options.enrollment.payload_sha256,
      passport_sha256: sha256(options.passportBytes),
      report_sha256: sha256(options.reportBytes),
      attestation_sha256: attestation.attestation_sha256,
      binding_sha256: binding.payload_sha256,
      status_sha256: status.payload_sha256,
      registry_snapshot_sha256: sha256(jsonBytes(current)),
      mode: current.mode,
      execution_verification: "operator_asserted",
      payment_authorized: false,
    },
  };
}
