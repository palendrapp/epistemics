import {
  address,
  getPublicKeyFromAddress,
  type KeyPairSigner,
  signatureBytes,
  signBytes,
  verifySignature,
} from "@solana/kit";
import { sha256 } from "../records.js";

export interface Signed<T> {
  payload: T;
  payload_sha256: string;
  signature_base64: string;
}

/** Restricted string-only canonical payload; distinct domains for each contract. */
export function canonical(payload: object): string {
  if (Object.values(payload).some((v) => typeof v !== "string"))
    throw new Error("Signed fields must be strings");
  return JSON.stringify(
    Object.fromEntries(
      Object.entries(payload).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)),
    ),
  );
}

export async function sign<T extends object>(
  payload: T,
  domain: string,
  signer: KeyPairSigner,
): Promise<Signed<T>> {
  const bytes = canonical(payload);
  return {
    payload,
    payload_sha256: sha256(bytes),
    signature_base64: Buffer.from(
      await signBytes(
        signer.keyPair.privateKey,
        new TextEncoder().encode(domain + bytes),
      ),
    ).toString("base64"),
  };
}

export async function verify<T extends object>(
  signed: Signed<T>,
  domain: string,
  expectedSigner: string,
): Promise<void> {
  const bytes = canonical(signed.payload);
  if (sha256(bytes) !== signed.payload_sha256)
    throw new Error("Signed payload hash mismatch");
  const signature = Buffer.from(signed.signature_base64, "base64");
  if (
    signature.length !== 64 ||
    signature.toString("base64") !== signed.signature_base64
  )
    throw new Error("Invalid signature encoding");
  if (
    !(await verifySignature(
      await getPublicKeyFromAddress(address(expectedSigner)),
      signatureBytes(signature),
      new TextEncoder().encode(domain + bytes),
    ))
  )
    throw new Error("Invalid signature");
}

export function timestamp(value: string): number {
  // New contracts require one unambiguous encoding, unlike older attestations.
  const n = Date.parse(value);
  if (!Number.isFinite(n) || new Date(n).toISOString() !== value)
    throw new Error("Expected canonical UTC timestamp");
  return n;
}

export function validity(issued: string, expires: string, now: Date): void {
  if (
    !Number.isFinite(now.valueOf()) ||
    timestamp(issued) > now.valueOf() ||
    timestamp(expires) <= now.valueOf() ||
    timestamp(expires) <= timestamp(issued)
  )
    throw new Error("Outside validity window");
}
