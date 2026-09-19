import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import {
  address,
  createKeyPairSignerFromBytes,
  getPublicKeyFromAddress,
  type KeyPairSigner,
  signatureBytes,
  signBytes,
  verifySignature,
} from "@solana/kit";
import { Ajv2020 } from "ajv/dist/2020.js";
import recordSchema from "../../../schemas/record.v1.json" with {
  type: "json",
};
import reportSchema from "../../../schemas/report.v1.json" with {
  type: "json",
};

export interface RecordPayload {
  schema_version: "epistemics.record.v1";
  kind: "evaluation_attestation";
  network: "solana:devnet";
  issuer: string;
  subject_agent_id: string;
  report_sha256: string;
  report_uri: string;
  battery_sha256: string;
  previous_record_sha256: string | null;
  created_at: string;
}

export interface SignedRecord {
  payload: RecordPayload;
  record_sha256: string;
  signature_base64: string;
}

interface ReportMetadata {
  agent: { agent_id: string };
  battery_sha256: string;
}

const ajv = new Ajv2020({ strict: true, allErrors: true });
const validateReport = ajv.compile<ReportMetadata>(reportSchema);
const validateRecord = ajv.compile<SignedRecord>(recordSchema);
const encoder = new TextEncoder();
const SIGNATURE_DOMAIN = "epistemics/record-signature/v1\n";

export function sha256(bytes: Uint8Array | string): string {
  return createHash("sha256").update(bytes).digest("hex");
}

export function readReport(bytes: Uint8Array): ReportMetadata {
  const parsed: unknown = JSON.parse(
    new TextDecoder("utf-8", { fatal: true }).decode(bytes),
  );
  const validate = validateReport;
  if (!validate(parsed)) {
    throw new Error(`Invalid report: ${ajv.errorsText(validate.errors)}`);
  }
  return parsed;
}

function signingBytes(payload: RecordPayload): Uint8Array {
  return encoder.encode(SIGNATURE_DOMAIN + canonicalPayload(payload));
}

/** v1 is a flat string/null map. UTF-16 key order + ECMAScript JSON string escaping. */
export function canonicalPayload(payload: RecordPayload): string {
  return JSON.stringify(
    Object.fromEntries(
      Object.entries(payload).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)),
    ),
  );
}

export function parseRecord(value: unknown): SignedRecord {
  if (!validateRecord(value)) {
    throw new Error(`Invalid record: ${ajv.errorsText(validateRecord.errors)}`);
  }
  address(value.payload.issuer);
  const timestamp = new Date(value.payload.created_at);
  if (
    !Number.isFinite(timestamp.valueOf()) ||
    timestamp.toISOString() !== value.payload.created_at
  ) {
    throw new Error("Invalid record timestamp");
  }
  const uri = new URL(value.payload.report_uri);
  if (
    !["https:", "ipfs:", "ar:"].includes(uri.protocol) ||
    !uri.hostname ||
    uri.username ||
    uri.password
  ) {
    throw new Error("Invalid report URI");
  }
  return value;
}

export async function createRecord(
  reportBytes: Uint8Array,
  issuer: KeyPairSigner,
  reportUri: string,
  previousRecordSha256: string | null = null,
): Promise<SignedRecord> {
  const report = readReport(reportBytes);
  const payload: RecordPayload = {
    schema_version: "epistemics.record.v1",
    kind: "evaluation_attestation",
    network: "solana:devnet",
    issuer: issuer.address,
    subject_agent_id: report.agent.agent_id,
    report_sha256: sha256(reportBytes),
    report_uri: reportUri,
    battery_sha256: report.battery_sha256,
    previous_record_sha256: previousRecordSha256,
    created_at: new Date().toISOString(),
  };
  const signature = await signBytes(
    issuer.keyPair.privateKey,
    signingBytes(payload),
  );
  return parseRecord({
    payload,
    record_sha256: sha256(canonicalPayload(payload)),
    signature_base64: Buffer.from(signature).toString("base64"),
  });
}

export async function verifyRecord(
  value: unknown,
  reportBytes?: Uint8Array,
): Promise<SignedRecord> {
  const record = parseRecord(value);
  if (sha256(canonicalPayload(record.payload)) !== record.record_sha256) {
    throw new Error("Record hash mismatch");
  }
  const sig = Buffer.from(record.signature_base64, "base64");
  if (sig.toString("base64") !== record.signature_base64) {
    throw new Error("Non-canonical signature encoding");
  }
  const key = await getPublicKeyFromAddress(address(record.payload.issuer));
  if (
    !(await verifySignature(
      key,
      signatureBytes(sig),
      signingBytes(record.payload),
    ))
  ) {
    throw new Error("Invalid issuer signature");
  }
  if (reportBytes !== undefined) {
    if (sha256(reportBytes) !== record.payload.report_sha256) {
      throw new Error("Report hash mismatch");
    }
    const report = readReport(reportBytes);
    if (
      report.agent.agent_id !== record.payload.subject_agent_id ||
      report.battery_sha256 !== record.payload.battery_sha256
    ) {
      throw new Error("Report metadata does not match record");
    }
  }
  return record;
}

export async function loadSigner(path: string): Promise<KeyPairSigner> {
  const value: unknown = JSON.parse(await readFile(path, "utf8"));
  if (
    !Array.isArray(value) ||
    value.length !== 64 ||
    !value.every((n) => Number.isInteger(n) && n >= 0 && n <= 255)
  ) {
    throw new Error(
      "Expected a Solana CLI keypair file containing exactly 64 bytes",
    );
  }
  return createKeyPairSignerFromBytes(new Uint8Array(value));
}

export function memoText(record: SignedRecord): string {
  return `epistemics:v1:${record.record_sha256}`;
}
