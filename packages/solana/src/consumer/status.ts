import { randomBytes } from "node:crypto";
import { link, mkdir, open, readdir, readFile, unlink } from "node:fs/promises";
import { join } from "node:path";
import { address, type KeyPairSigner } from "@solana/kit";
import { type PassportStatus, STATUS_DOMAIN, validate } from "./contracts.js";
import {
  type Signed,
  sign,
  timestamp,
  validity,
  verify,
} from "./signatures.js";

export async function verifyStatusHistory(
  input: unknown,
  issuer: string,
  attestation: string,
  options: { now?: Date; minimumSequence?: string } = {},
): Promise<Signed<PassportStatus>> {
  if (!Array.isArray(input) || !input.length || input.length > 10000)
    throw new Error("Missing or oversized issuer status history");
  let previous: Signed<PassportStatus> | undefined;
  for (const [index, value] of input.entries()) {
    const event = validate("status", value);
    const p = event.payload;
    address(p.evaluated_controller);
    if (
      previous &&
      p.evaluated_controller !== previous.payload.evaluated_controller
    )
      throw new Error(
        "Evaluated controller cannot change within one attestation history",
      );
    if (
      p.issuer !== issuer ||
      p.attestation_sha256 !== attestation ||
      p.sequence !== String(index) ||
      p.previous_sha256 !== (previous?.payload_sha256 ?? "")
    )
      throw new Error("Broken status history binding or sequence");
    if (
      (p.status === "corrected") !==
        (p.replacement_attestation_sha256 !== "") ||
      p.replacement_attestation_sha256 === attestation
    )
      throw new Error("Invalid correction target");
    if (
      timestamp(p.expires_at) <= timestamp(p.issued_at) ||
      (previous &&
        timestamp(p.issued_at) < timestamp(previous.payload.issued_at))
    )
      throw new Error("Invalid status chronology");
    if (
      previous &&
      previous.payload.status !== "active" &&
      (p.status !== previous.payload.status ||
        p.replacement_attestation_sha256 !==
          previous.payload.replacement_attestation_sha256)
    )
      throw new Error("Terminal status cannot be reversed");
    await verify(event, STATUS_DOMAIN, issuer);
    previous = event;
  }
  const result = previous!;
  if (
    options.minimumSequence !== undefined &&
    BigInt(result.payload.sequence) < BigInt(options.minimumSequence)
  )
    throw new Error("Status rollback below remembered sequence");
  if (options.now)
    validity(result.payload.issued_at, result.payload.expires_at, options.now);
  return result;
}

export async function createStatus(
  history: Signed<PassportStatus>[],
  issuer: KeyPairSigner,
  attestation: string,
  fields: Pick<
    PassportStatus,
    | "evaluated_controller"
    | "status"
    | "replacement_attestation_sha256"
    | "reason"
    | "issued_at"
    | "expires_at"
  >,
): Promise<Signed<PassportStatus>> {
  const event = await sign<PassportStatus>(
    {
      ...fields,
      schema_version: "epistemics.passport-status.v1",
      issuer: issuer.address,
      attestation_sha256: attestation,
      sequence: String(history.length),
      previous_sha256: history.at(-1)?.payload_sha256 ?? "",
    },
    STATUS_DOMAIN,
    issuer,
  );
  await verifyStatusHistory([...history, event], issuer.address, attestation);
  return event;
}

function directory(root: string, issuer: string, attestation: string): string {
  address(issuer);
  if (!/^[0-9a-f]{64}$/.test(attestation))
    throw new Error("Invalid attestation digest");
  return join(root, issuer, attestation);
}

export async function readStatusHistory(
  root: string,
  issuer: string,
  attestation: string,
): Promise<Signed<PassportStatus>[]> {
  const dir = directory(root, issuer, attestation);
  let names: string[];
  try {
    names = await readdir(dir);
  } catch (e) {
    if ((e as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw e;
  }
  const files = names.filter((name) => /^\d{8}\.json$/.test(name)).sort();
  if (
    files.some(
      (name, index) => name !== `${String(index).padStart(8, "0")}.json`,
    )
  )
    throw new Error("Status files are not a contiguous history");
  const history = await Promise.all(
    files.map(async (name) =>
      validate("status", JSON.parse(await readFile(join(dir, name), "utf8"))),
    ),
  );
  if (history.length) await verifyStatusHistory(history, issuer, attestation);
  return history;
}

/** Exclusive local writer, append-only events; a crash-held lock needs operator review. */
export async function appendStatus(
  root: string,
  event: Signed<PassportStatus>,
): Promise<void> {
  validate("status", event);
  const { issuer, attestation_sha256: attestation } = event.payload;
  const dir = directory(root, issuer, attestation);
  await mkdir(dir, { recursive: true, mode: 0o700 });
  const lock = join(dir, ".writer-lock");
  const handle = await open(lock, "wx", 0o600);
  try {
    const history = await readStatusHistory(root, issuer, attestation);
    await verifyStatusHistory([...history, event], issuer, attestation);
    const temporary = join(dir, `.${randomBytes(16).toString("hex")}.tmp`);
    const file = await open(temporary, "wx", 0o600);
    try {
      await file.writeFile(`${JSON.stringify(event, null, 2)}\n`);
      await file.sync();
    } finally {
      await file.close();
    }
    try {
      // Atomic publication without replacement; incomplete temporary files stay invisible.
      await link(
        temporary,
        join(dir, `${event.payload.sequence.padStart(8, "0")}.json`),
      );
      const directoryHandle = await open(dir, "r");
      try {
        await directoryHandle.sync();
      } finally {
        await directoryHandle.close();
      }
    } finally {
      await unlink(temporary);
    }
  } finally {
    await handle.close();
    await unlink(lock);
  }
}
