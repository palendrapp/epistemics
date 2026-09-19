import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { parseArgs } from "node:util";
import { generateKeyPairSigner } from "@solana/kit";
import {
  createPassportAttestation,
  verifyPassportAttestation,
} from "./passports.js";
import { loadSigner } from "./records.js";

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    passport: { type: "string" },
    report: { type: "string" },
    attestation: { type: "string" },
    keypair: { type: "string" },
    issuer: { type: "string" },
    uri: { type: "string" },
    expires: { type: "string" },
    output: { type: "string" },
  },
});

function required(name: keyof typeof values): string {
  const value = values[name];
  if (!value) throw new Error(`--${name} is required`);
  return value;
}

async function main() {
  const command = positionals[0];
  if (
    !command ||
    !["demo", "create", "verify"].includes(command) ||
    positionals.length !== 1
  )
    throw new Error(
      "Usage: pnpm passport-record <demo|create|verify> --passport FILE [--report FILE] [--attestation FILE] [--issuer TRUSTED_KEY] [--keypair FILE --uri URI --expires ISO_TIMESTAMP --output FILE]",
    );
  const passport = await readFile(resolve(required("passport")));
  const report = values.report
    ? await readFile(resolve(values.report))
    : undefined;
  if (command === "verify") {
    const verified = await verifyPassportAttestation(
      JSON.parse(await readFile(resolve(required("attestation")), "utf8")),
      passport,
      {
        expectedIssuer: required("issuer"),
        ...(report ? { reportBytes: report } : {}),
      },
    );
    return {
      status: "verified_offline",
      attestation_sha256: verified.attestation_sha256,
      issuer: verified.payload.issuer,
      response_origin: verified.payload.response_origin,
      report_bytes_checked: report !== undefined,
      derivation_recomputed: false,
      registry_binding_verified: false,
      execution_verified: false,
      revocation_checked: false,
      payment_authorized: false,
    };
  }
  if (!report) throw new Error("--report is required for issuance");
  const signer =
    command === "demo"
      ? await generateKeyPairSigner()
      : await loadSigner(required("keypair"));
  const attestation = await createPassportAttestation(
    passport,
    report,
    signer,
    {
      passportUri:
        command === "demo"
          ? "https://example.invalid/passport.json"
          : required("uri"),
      expiresAt:
        command === "demo"
          ? new Date(Date.now() + 86400000).toISOString()
          : required("expires"),
    },
  );
  await verifyPassportAttestation(attestation, passport, {
    expectedIssuer: signer.address,
    reportBytes: report,
  });
  const output = resolve(required("output"));
  await mkdir(dirname(output), { recursive: true });
  await writeFile(output, `${JSON.stringify(attestation, null, 2)}\n`, {
    flag: "wx",
  });
  return {
    status: "signed_offline",
    output,
    issuer: signer.address,
    response_origin: attestation.payload.response_origin,
    note:
      command === "demo"
        ? "Ephemeral demonstration key discarded; no publication or transaction"
        : "Detached issuer assertion; no publication, registry verification or transaction",
  };
}

main()
  .then((result) => console.log(JSON.stringify(result, null, 2)))
  .catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : "Operation failed");
    process.exitCode = 1;
  });
