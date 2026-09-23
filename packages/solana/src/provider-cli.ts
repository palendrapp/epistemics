import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { parseArgs } from "node:util";
import {
  type Enrollment,
  enrollProvider,
  issueEnrolledPassport,
  jsonBytes,
} from "./consumer/enrollment.js";
import { rpcTransport } from "./consumer/http.js";
import type { Signed } from "./consumer/signatures.js";
import { appendStatus } from "./consumer/status.js";
import { loadSigner } from "./records.js";

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    directory: { type: "string" },
    asset: { type: "string" },
    configuration: { type: "string" },
    "authority-keypair": { type: "string" },
    issuer: { type: "string" },
    "issuer-keypair": { type: "string" },
    "protocol-version": { type: "string" },
    "protocol-sha256": { type: "string" },
    expires: { type: "string" },
    rpc: { type: "string", default: "https://api.devnet.solana.com" },
    passport: { type: "string" },
    report: { type: "string" },
    "passport-uri": { type: "string" },
    "attestation-uri": { type: "string" },
    endpoint: { type: "string" },
    payee: { type: "string" },
    "payment-asset": { type: "string" },
  },
});
function required(name: keyof typeof values) {
  const value = values[name];
  if (!value) throw new Error(`--${name} is required`);
  return value;
}
async function save(directory: string, name: string, bytes: Uint8Array) {
  await writeFile(join(directory, name), bytes, { flag: "wx", mode: 0o600 });
}
async function main() {
  if (
    positionals.length !== 1 ||
    !["enroll", "issue"].includes(positionals[0]!)
  )
    throw new Error("Choose enroll or issue");
  const directory = resolve(required("directory"));
  const authority = await loadSigner(required("authority-keypair"));
  const transport = rpcTransport(required("rpc"));
  if (positionals[0] === "enroll") {
    const bundle = await enrollProvider({
      asset: required("asset"),
      authority,
      issuer: required("issuer"),
      transport,
      configuration: JSON.parse(
        await readFile(required("configuration"), "utf8"),
      ),
      protocolVersion: required("protocol-version"),
      protocolSha256: required("protocol-sha256"),
      expiresAt: required("expires"),
    });
    // An existing enrollment directory is never replaced, including after partial writes.
    await mkdir(directory, { mode: 0o700 });
    await save(directory, "participant.json", bundle.participantBytes);
    await save(directory, "registry-before.json", bundle.registryBytes);
    await save(directory, "enrollment.json", jsonBytes(bundle.enrollment));
    return {
      status: "enrolled",
      mode: bundle.enrollment.payload.mode,
      subject: bundle.enrollment.payload.subject_agent_id,
      participant: join(directory, "participant.json"),
    };
  }
  const enrollment = JSON.parse(
    await readFile(join(directory, "enrollment.json"), "utf8"),
  ) as Signed<Enrollment>;
  const passportBytes = await readFile(required("passport"));
  const result = await issueEnrolledPassport({
    enrollment,
    participantBytes: await readFile(join(directory, "participant.json")),
    registryBytes: await readFile(join(directory, "registry-before.json")),
    transport,
    authority,
    issuer: await loadSigner(required("issuer-keypair")),
    passportBytes,
    reportBytes: await readFile(required("report")),
    passportUri: required("passport-uri"),
    attestationUri: required("attestation-uri"),
    endpoint: required("endpoint"),
    payee: required("payee"),
    paymentAsset: required("payment-asset"),
    expiresAt: required("expires"),
  });
  const out = join(directory, "issued");
  await mkdir(out, { mode: 0o700 });
  await save(out, "passport.json", passportBytes);
  await save(out, "attestation.json", jsonBytes(result.attestation));
  await save(out, "binding.json", jsonBytes(result.binding));
  await save(out, "registry-after.json", jsonBytes(result.registry));
  await appendStatus(join(out, "status"), result.status);
  await save(
    out,
    "artifacts.json",
    jsonBytes({
      "/passport.json": "passport.json",
      "/attestation.json": "attestation.json",
      "/binding.json": "binding.json",
    }),
  );
  await save(out, "receipt.json", jsonBytes(result.receipt));
  return {
    status: "issued_locally",
    mode: result.registry.mode,
    output: out,
    payment_authorized: false,
  };
}
main()
  .then((result) => console.log(JSON.stringify(result, null, 2)))
  .catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
