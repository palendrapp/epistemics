import { isDeepStrictEqual } from "node:util";
import {
  address,
  getPublicKeyFromAddress,
  type KeyPairSigner,
  signatureBytes,
  signBytes,
  verifySignature,
} from "@solana/kit";
import { Ajv2020 } from "ajv/dist/2020.js";
import passportSchema from "../../../schemas/passport.v2.json" with {
  type: "json",
};
import attestationSchema from "../../../schemas/passport-attestation.v1.json" with {
  type: "json",
};
import reportSchema from "../../../schemas/report.v4.json" with {
  type: "json",
};
import { sha256 } from "./records.js";

interface Context {
  participant: {
    kind: string;
    subject_id: string;
    configuration?: { configuration_sha256: string };
  };
  response_origin: "agent" | "synthetic" | "unspecified";
  metadata_verification: "operator_asserted";
  protocol_version: string;
  protocol_sha256: string;
  evaluator_version: string;
  completion: string;
  accepted_answers: number;
  planned_answers: number;
  started_at: string;
  completed_at: string;
}

interface CorePassport {
  context: Context;
  source: { sha256: string };
  interpretation_version: string;
  dimensions: { dimension_id: string }[];
}

export interface PassportPayload {
  schema_version: "epistemics.passport-attestation.v1";
  kind: "passport_attestation";
  issuer: string;
  subject_agent_id: string;
  configuration_sha256: string;
  passport_sha256: string;
  passport_uri: string;
  report_sha256: string;
  protocol_sha256: string;
  protocol_version: string;
  evaluator_version: string;
  interpretation_version: string;
  execution_verification: "operator_asserted";
  response_origin: "agent" | "synthetic" | "unspecified";
  issued_at: string;
  expires_at: string;
}

export interface PassportAttestation {
  payload: PassportPayload;
  attestation_sha256: string;
  signature_base64: string;
}

// Date-time semantics for fields used here are checked explicitly below.
const ajv = new Ajv2020({
  strict: true,
  allErrors: true,
  formats: { "date-time": true },
});
// Pydantic's OpenAPI discriminator mapping is an annotation; oneOf still validates
// every union branch, and readPassport requires the explicit agent tag.
ajv.addKeyword({ keyword: "discriminator", schemaType: "object", valid: true });
const validatePassport = ajv.compile<CorePassport>(passportSchema);
const validateReport = ajv.compile<{ context: Context }>(reportSchema);
const validateAttestation = ajv.compile<PassportAttestation>(attestationSchema);
const DOMAIN = "epistemics/passport-attestation-signature/v1\n";
const DIMENSIONS = [
  "evidence_weighting",
  "source_judgment",
  "belief_revision",
  "dependence_and_causal_reasoning",
  "uncertainty_and_calibration",
  "decision_consistency",
];

function parseJson(bytes: Uint8Array): unknown {
  return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
}

function timestamp(value: string): number {
  const result = Date.parse(value);
  if (
    !Number.isFinite(result) ||
    !/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(\.\d+)?(Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(
      value,
    )
  ) {
    throw new Error("Invalid timestamp");
  }
  const [year, month, day] = value.slice(0, 10).split("-").map(Number);
  if (
    !year ||
    !month ||
    !day ||
    month > 12 ||
    day > new Date(Date.UTC(year, month, 0)).getUTCDate()
  ) {
    throw new Error("Invalid timestamp");
  }
  return result;
}

function readPassport(bytes: Uint8Array): CorePassport {
  const value = parseJson(bytes);
  if (!validatePassport(value))
    throw new Error(
      `Invalid core passport: ${ajv.errorsText(validatePassport.errors)}`,
    );
  const c = value.context;
  if (c.participant.kind !== "agent" || !c.participant.configuration)
    throw new Error(
      "Agent core passport required; human publication is not supported",
    );
  if (
    c.completion !== "complete" ||
    c.accepted_answers !== 34 ||
    c.planned_answers !== 34 ||
    c.response_origin === undefined ||
    c.metadata_verification !== "operator_asserted"
  )
    throw new Error("Incomplete or unsupported passport context");
  if (timestamp(c.started_at) > timestamp(c.completed_at))
    throw new Error("Invalid session timestamps");
  if (
    !isDeepStrictEqual(
      value.dimensions.map((d) => d.dimension_id),
      DIMENSIONS,
    )
  )
    throw new Error("Invalid passport dimensions");
  return value;
}

/** Flat string-only payload, UTF-16 key order and ECMAScript JSON escaping. */
export function canonicalPassportPayload(payload: PassportPayload): string {
  return JSON.stringify(
    Object.fromEntries(
      Object.entries(payload).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)),
    ),
  );
}

function signingBytes(payload: PassportPayload): Uint8Array {
  return new TextEncoder().encode(DOMAIN + canonicalPassportPayload(payload));
}

function metadata(passport: CorePassport) {
  const c = passport.context;
  return {
    subject_agent_id: c.participant.subject_id,
    configuration_sha256: c.participant.configuration?.configuration_sha256,
    report_sha256: passport.source.sha256,
    protocol_sha256: c.protocol_sha256,
    protocol_version: c.protocol_version,
    evaluator_version: c.evaluator_version,
    interpretation_version: passport.interpretation_version,
    execution_verification: c.metadata_verification,
    response_origin: c.response_origin,
  };
}

function checkReport(passport: CorePassport, reportBytes: Uint8Array) {
  if (sha256(reportBytes) !== passport.source.sha256)
    throw new Error("Report hash mismatch");
  const report = parseJson(reportBytes);
  if (!validateReport(report))
    throw new Error(
      `Invalid core report: ${ajv.errorsText(validateReport.errors)}`,
    );
  if (!isDeepStrictEqual(report.context, passport.context))
    throw new Error("Report context does not match passport");
}

function parseAttestation(value: unknown): PassportAttestation {
  if (!validateAttestation(value))
    throw new Error(
      `Invalid passport attestation: ${ajv.errorsText(validateAttestation.errors)}`,
    );
  const p = value.payload;
  address(p.issuer);
  const uri = new URL(p.passport_uri);
  if (
    !["https:", "ipfs:", "ar:"].includes(uri.protocol) ||
    !uri.hostname ||
    uri.username ||
    uri.password
  )
    throw new Error("Invalid passport URI");
  if (timestamp(p.issued_at) >= timestamp(p.expires_at))
    throw new Error("Expiry must follow issuance");
  return value;
}

export async function createPassportAttestation(
  passportBytes: Uint8Array,
  reportBytes: Uint8Array,
  issuer: KeyPairSigner,
  options: { passportUri: string; expiresAt: string; issuedAt?: string },
): Promise<PassportAttestation> {
  const passport = readPassport(passportBytes);
  checkReport(passport, reportBytes);
  const payload: PassportPayload = {
    schema_version: "epistemics.passport-attestation.v1",
    kind: "passport_attestation",
    ...metadata(passport),
    configuration_sha256:
      passport.context.participant.configuration!.configuration_sha256,
    issuer: issuer.address,
    passport_sha256: sha256(passportBytes),
    passport_uri: options.passportUri,
    issued_at: options.issuedAt ?? new Date().toISOString(),
    expires_at: options.expiresAt,
  };
  if (timestamp(payload.issued_at) < timestamp(passport.context.completed_at))
    throw new Error("Issuance precedes evaluation completion");
  const sig = await signBytes(issuer.keyPair.privateKey, signingBytes(payload));
  return parseAttestation({
    payload,
    attestation_sha256: sha256(canonicalPassportPayload(payload)),
    signature_base64: Buffer.from(sig).toString("base64"),
  });
}

export async function verifyPassportAttestation(
  value: unknown,
  passportBytes: Uint8Array,
  options: { expectedIssuer: string; now?: Date; reportBytes?: Uint8Array },
): Promise<PassportAttestation> {
  const attestation = parseAttestation(value);
  const p = attestation.payload;
  if (p.issuer !== address(options.expectedIssuer))
    throw new Error(
      "Unexpected issuer; trust must be configured by the consumer",
    );
  if (sha256(canonicalPassportPayload(p)) !== attestation.attestation_sha256)
    throw new Error("Attestation hash mismatch");
  const sig = Buffer.from(attestation.signature_base64, "base64");
  if (sig.toString("base64") !== attestation.signature_base64)
    throw new Error("Non-canonical signature encoding");
  const key = await getPublicKeyFromAddress(address(p.issuer));
  if (!(await verifySignature(key, signatureBytes(sig), signingBytes(p))))
    throw new Error("Invalid issuer signature");
  if (sha256(passportBytes) !== p.passport_sha256)
    throw new Error("Passport hash mismatch");
  const passport = readPassport(passportBytes);
  for (const [field, expected] of Object.entries(metadata(passport))) {
    if (p[field as keyof PassportPayload] !== expected)
      throw new Error(`Passport metadata mismatch: ${field}`);
  }
  const now = (options.now ?? new Date()).valueOf();
  if (
    !Number.isFinite(now) ||
    timestamp(p.issued_at) > now ||
    timestamp(p.issued_at) < timestamp(passport.context.completed_at) ||
    timestamp(p.expires_at) <= now
  )
    throw new Error("Attestation outside its validity window");
  if (options.reportBytes !== undefined)
    checkReport(passport, options.reportBytes);
  return attestation;
}
