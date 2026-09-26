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
import investigationCollectionSchema from "../../../schemas/investigation-collection.v1.json" with {
  type: "json",
};
import investigationReport2Schema from "../../../schemas/investigation-report.v2.json" with {
  type: "json",
};
import investigationReport3Schema from "../../../schemas/investigation-report.v3.json" with {
  type: "json",
};
import passportSchema from "../../../schemas/passport.v2.json" with {
  type: "json",
};
import investigationPassportSchema from "../../../schemas/passport.v3.json" with {
  type: "json",
};
import sourcePassportSchema from "../../../schemas/passport.v4.json" with {
  type: "json",
};
import attestationSchema from "../../../schemas/passport-attestation.v1.json" with {
  type: "json",
};
import reportSchema from "../../../schemas/report.v4.json" with {
  type: "json",
};
import sourceEvidenceSchema from "../../../schemas/source-evidence.v1.json" with {
  type: "json",
};
import sourceReportSchema from "../../../schemas/source-learning-report.v1.json" with {
  type: "json",
};
import { sha256 } from "./records.js";

interface Context {
  session_id: string;
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
  schema_version: string;
  evaluation_mode?: string;
  subject_binding?: string;
  source_subject_ids?: string[];
  presentation?: string;
  condition?: string;
  coverage?: Record<string, number>;
  repeatability?: unknown;
  model_diagnostics?: { fits: unknown };
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
const validateInvestigationPassport = ajv.compile<CorePassport>(
  investigationPassportSchema,
);
const validateInvestigationReport = ajv.compile<{
  context: Context;
  cases: { report_sha256: string; report_json: string }[];
  manifest_sha256: string;
  evaluation_mode: string;
}>(investigationCollectionSchema);
interface InvestigationReportView {
  schema_version: string;
  manifest: {
    study_id: string;
    created_at: string;
    participant: Context["participant"];
    response_origin: Context["response_origin"];
    battery_version: string;
    evaluator_version: string;
    implementation_sha256: string;
    assignments: { mode: string }[];
  };
  manifest_sha256: string;
  assignment: { mode: string };
  observations: { trial: { index: number }; answered_at: string }[];
  completed_at: string;
}
const validateInvestigationCase2 = ajv.compile<InvestigationReportView>(
  investigationReport2Schema,
);
const validateInvestigationCase3 = ajv.compile<InvestigationReportView>(
  investigationReport3Schema,
);
interface SourceEvidenceView {
  context: Context;
  subject_binding: string;
  source_subject_ids: string[];
  presentation: string;
  condition: string;
  coverage: Record<string, number>;
  repeatability: unknown;
  diagnostics: unknown;
  sessions: {
    report_json: string;
    report_sha256: string;
    transport_json: string | null;
    transport_sha256: string | null;
  }[];
}
interface SourceReportView {
  manifest: {
    study_id: string;
    created_at: string;
    participant: Context["participant"];
    response_origin: string;
    condition: string;
    implementation_sha256: string;
    evaluator_version: string;
  };
  manifest_sha256: string;
  completed_at: string;
  observations: { answered_at: string; trial: { trial_id: string } }[];
}
const validateSourcePassport = ajv.compile<CorePassport>(sourcePassportSchema);
const validateSourceEvidence =
  ajv.compile<SourceEvidenceView>(sourceEvidenceSchema);
const validateSourceReport = ajv.compile<SourceReportView>(sourceReportSchema);
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
  const isInvestigation =
    (value as { schema_version?: string })?.schema_version ===
    "epistemics.passport.v3";
  const isSource =
    (value as { schema_version?: string })?.schema_version ===
    "epistemics.passport.v4";
  const validator = isSource
    ? validateSourcePassport
    : isInvestigation
      ? validateInvestigationPassport
      : validatePassport;
  if (!validator(value))
    throw new Error(
      `Invalid supported passport: ${ajv.errorsText(validator.errors)}`,
    );
  const c = value.context;
  if (isSource && value.subject_binding !== "single_subject")
    throw new Error(
      "Configuration-cohort evidence cannot be issued as a single agent identity",
    );
  const expectedAnswers = isSource
    ? 36 * (value.coverage?.sessions ?? 0)
    : isInvestigation
      ? 48
      : 34;
  if (c.participant.kind !== "agent" || !c.participant.configuration)
    throw new Error(
      "Agent passport required; human publication is not supported",
    );
  if (
    c.completion !== "complete" ||
    c.accepted_answers !== expectedAnswers ||
    c.planned_answers !== expectedAnswers ||
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
  if (passport.schema_version === "epistemics.passport.v4") {
    if (!validateSourceEvidence(report))
      throw new Error("Invalid source-learning evidence");
    const c = report.context;
    if (
      !isDeepStrictEqual(c, passport.context) ||
      report.subject_binding !== passport.subject_binding ||
      !isDeepStrictEqual(
        report.source_subject_ids,
        passport.source_subject_ids,
      ) ||
      report.presentation !== passport.presentation ||
      report.condition !== passport.condition ||
      !isDeepStrictEqual(report.coverage, passport.coverage) ||
      !isDeepStrictEqual(report.repeatability, passport.repeatability) ||
      !isDeepStrictEqual(
        report.diagnostics,
        passport.model_diagnostics?.fits,
      ) ||
      report.sessions.length !== report.coverage.sessions ||
      report.subject_binding !== "single_subject" ||
      !isDeepStrictEqual(report.source_subject_ids, [c.participant.subject_id])
    )
      throw new Error("Source evidence context mismatch");
    let first = Infinity,
      last = -Infinity;
    const seen = new Set<string>();
    for (const item of report.sessions) {
      if (sha256(item.report_json) !== item.report_sha256)
        throw new Error("Embedded report hash mismatch");
      const child: unknown = JSON.parse(item.report_json);
      if (!validateSourceReport(child))
        throw new Error("Invalid embedded source report");
      const m = child.manifest;
      if (
        seen.has(m.study_id) ||
        !isDeepStrictEqual(m.participant, c.participant) ||
        m.response_origin !== c.response_origin ||
        m.condition !== report.condition ||
        m.evaluator_version !== c.evaluator_version
      )
        throw new Error("Source session binding mismatch");
      seen.add(m.study_id);
      first = Math.min(first, timestamp(m.created_at));
      last = Math.max(last, timestamp(child.completed_at));
      let previous = timestamp(m.created_at);
      for (const o of child.observations) {
        const time = timestamp(o.answered_at);
        if (time < previous || time > timestamp(child.completed_at))
          throw new Error("Invalid source chronology");
        previous = time;
      }
      if (item.transport_json === null) {
        if (
          item.transport_sha256 !== null ||
          report.presentation !== "unverified" ||
          c.protocol_version !== "source-delivery-unverified/0.1.0" ||
          c.protocol_sha256 !== m.implementation_sha256
        )
          throw new Error("Missing source presentation evidence");
      } else {
        if (sha256(item.transport_json) !== item.transport_sha256)
          throw new Error("Embedded transport hash mismatch");
        const e = JSON.parse(item.transport_json) as {
          schema_version: string;
          completed_at: string;
          binding: {
            schema_version: string;
            version: string;
            presentation: string;
            presentation_version?: string;
            base_manifest_sha256: string;
            implementation_sha256: string;
            created_at: string;
          };
          locks: { locked_at: string; public_trial: { trial_id: string } }[];
        };
        const b = e.binding;
        const panel =
          e.schema_version === "epistemics.source-panel-evidence.v1";
        const delivery =
          e.schema_version === "epistemics.source-delivery-evidence.v1";
        if (
          (!panel && !delivery) ||
          (panel &&
            (b.schema_version !== "epistemics.source-panel-binding.v1" ||
              b.version !== "source-panel/0.1.0")) ||
          (delivery &&
            (b.schema_version !== "epistemics.source-delivery-binding.v1" ||
              b.version !== "source-learning/0.2.0")) ||
          b.presentation !== report.presentation ||
          b.base_manifest_sha256 !== child.manifest_sha256 ||
          b.implementation_sha256 !== c.protocol_sha256 ||
          (panel ? b.presentation_version : b.version) !== c.protocol_version ||
          e.locks.length !== 36 ||
          timestamp(e.completed_at) !== timestamp(child.completed_at) ||
          timestamp(b.created_at) < timestamp(m.created_at)
        )
          throw new Error("Source presentation binding mismatch");
        for (const [i, lock] of e.locks.entries()) {
          if (
            lock.public_trial.trial_id !==
              child.observations[i]!.trial.trial_id ||
            timestamp(lock.locked_at) < timestamp(b.created_at) ||
            timestamp(lock.locked_at) >
              timestamp(child.observations[i]!.answered_at)
          )
            throw new Error("Source presentation chronology mismatch");
        }
      }
    }
    if (first !== timestamp(c.started_at) || last !== timestamp(c.completed_at))
      throw new Error("Source collection chronology mismatch");
    return;
  }
  if (passport.schema_version === "epistemics.passport.v3") {
    if (!validateInvestigationReport(report))
      throw new Error(
        `Invalid investigation source: ${ajv.errorsText(validateInvestigationReport.errors)}`,
      );
    if (
      !isDeepStrictEqual(report.context, passport.context) ||
      report.evaluation_mode !== passport.evaluation_mode
    )
      throw new Error("Report context does not match passport");
    let manifest: InvestigationReportView["manifest"] | undefined;
    let latest = -Infinity;
    for (const [index, item] of report.cases.entries()) {
      if (sha256(item.report_json) !== item.report_sha256)
        throw new Error("Embedded report hash mismatch");
      const child: unknown = JSON.parse(item.report_json);
      const validator =
        (child as { schema_version?: string })?.schema_version ===
        "epistemics.investigation-report.v2"
          ? validateInvestigationCase2
          : validateInvestigationCase3;
      if (!validator(child))
        throw new Error("Invalid embedded investigation case");
      manifest ??= child.manifest;
      const c = report.context;
      if (
        !isDeepStrictEqual(child.manifest, manifest) ||
        !isDeepStrictEqual(child.assignment, manifest.assignments[index]) ||
        child.assignment.mode !== report.evaluation_mode ||
        !isDeepStrictEqual(manifest.participant, c.participant) ||
        manifest.study_id !== c.session_id ||
        timestamp(manifest.created_at) !== timestamp(c.started_at) ||
        manifest.response_origin !== c.response_origin ||
        manifest.battery_version !== c.protocol_version ||
        manifest.evaluator_version !== c.evaluator_version ||
        manifest.implementation_sha256 !== c.protocol_sha256 ||
        child.manifest_sha256 !== report.manifest_sha256
      )
        throw new Error("Investigation case binding mismatch");
      let previous = timestamp(c.started_at);
      for (const [stage, o] of child.observations.entries()) {
        const at = timestamp(o.answered_at);
        if (
          o.trial.index !== stage ||
          at < previous ||
          at > timestamp(child.completed_at)
        )
          throw new Error("Invalid investigation chronology");
        previous = at;
      }
      latest = Math.max(latest, timestamp(child.completed_at));
    }
    if (latest !== timestamp(report.context.completed_at))
      throw new Error("Investigation completion mismatch");
    return;
  }
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
