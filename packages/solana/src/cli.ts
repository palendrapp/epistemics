import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { parseArgs } from "node:util";
import { generateKeyPairSigner } from "@solana/kit";
import { createRecord, loadSigner, memoText, verifyRecord } from "./records.js";
import { anchorRecord, DEFAULT_RPC, verifyAnchor } from "./solana.js";

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    report: { type: "string" },
    record: { type: "string" },
    keypair: { type: "string" },
    uri: { type: "string" },
    output: { type: "string" },
    previous: { type: "string" },
    rpc: { type: "string" },
    signature: { type: "string" },
    submit: { type: "boolean", default: false },
  },
});

function required(name: keyof typeof values): string {
  const value = values[name];
  if (typeof value !== "string" || !value)
    throw new Error(`--${name} is required`);
  return value;
}

async function main() {
  const command = positionals[0];
  if (
    !command ||
    !["demo", "create", "verify", "anchor"].includes(command) ||
    positionals.length !== 1
  ) {
    throw new Error(
      "Usage: pnpm record <demo|create|verify|anchor> --report FILE [--record FILE] [--keypair FILE] [--uri URI] [--output FILE] [--signature SIG] [--submit]",
    );
  }
  const report = await readFile(resolve(required("report")));
  const rpc = values.rpc ?? process.env.SOLANA_RPC_URL ?? DEFAULT_RPC;
  if (command === "demo" || command === "create") {
    const signer =
      command === "demo"
        ? await generateKeyPairSigner()
        : await loadSigner(
            values.keypair ??
              process.env.SOLANA_KEYPAIR_PATH ??
              required("keypair"),
          );
    const record = await createRecord(
      report,
      signer,
      command === "demo"
        ? "https://example.invalid/demo-report.json"
        : required("uri"),
      values.previous ?? null,
    );
    await verifyRecord(record, report);
    const output = resolve(values.output ?? "output/demo-record.json");
    await mkdir(dirname(output), { recursive: true });
    await writeFile(output, `${JSON.stringify(record, null, 2)}\n`, {
      flag: "wx",
    });
    return {
      status: "signed_offline",
      output,
      issuer: signer.address,
      memo: memoText(record),
      ...(command === "demo"
        ? { note: "Ephemeral demo key discarded; example URI is not uploaded" }
        : {}),
    };
  }
  const record = await verifyRecord(
    JSON.parse(await readFile(resolve(required("record")), "utf8")),
    report,
  );
  if (command === "verify") {
    return values.signature
      ? verifyAnchor(record, values.signature, rpc)
      : {
          status: "verified_offline",
          record_sha256: record.record_sha256,
          note: "Signature and exact report bytes verified; on-chain inclusion not checked",
        };
  }
  const signer = await loadSigner(
    values.keypair ?? process.env.SOLANA_KEYPAIR_PATH ?? required("keypair"),
  );
  return anchorRecord(record, report, signer, rpc, values.submit);
}

main()
  .then((result) => console.log(JSON.stringify(result, null, 2)))
  .catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : "Operation failed");
    process.exitCode = 1;
  });
