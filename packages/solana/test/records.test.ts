import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mock, test } from "node:test";
import { fileURLToPath } from "node:url";
import {
  blockhash,
  generateKeyPairSigner,
  getCompiledTransactionMessageDecoder,
  getSignatureFromTransaction,
  getTransactionDecoder,
  signatureBytes,
  verifySignature,
} from "@solana/kit";
import { MEMO_PROGRAM_ADDRESS } from "@solana-program/memo";
import {
  canonicalPayload,
  createRecord,
  memoText,
  readReport,
  sha256,
  verifyRecord,
} from "../src/records.js";
import {
  anchorRecord,
  assertAnchorIncluded,
  assertDevnet,
  buildAnchorTransaction,
  DEVNET_GENESIS,
  type ParsedTransaction,
  verifyAnchor,
} from "../src/solana.js";

const root = fileURLToPath(new URL("../../../", import.meta.url));
const python = fileURLToPath(
  new URL("../../../.venv/bin/python", import.meta.url),
);
// Real Python -> JSON Schema -> TypeScript interoperability, without committing a random fixture.
const report = execFileSync(
  python,
  ["-c", "from epistemics.cli import demo; print(demo().model_dump_json())"],
  { cwd: root },
);
const uri = "ipfs://bafy-example-report";
const signer = await generateKeyPairSigner();
const record = await createRecord(report, signer, uri);

test("accepts the actual Python report and signs/verifies exact bytes", async () => {
  assert.equal(readReport(report).agent.agent_id, "demo:reference");
  assert.deepEqual(await verifyRecord(record, report), record);
  assert.equal(record.payload.report_sha256, sha256(report));
});

test("rejects incomplete or non-report JSON", () => {
  assert.throws(() => readReport(Buffer.from("{}")), /Invalid report/);
  const incomplete = JSON.parse(report.toString());
  incomplete.observations.pop();
  assert.throws(
    () => readReport(Buffer.from(JSON.stringify(incomplete))),
    /Invalid report/,
  );
});

test("a report whitespace change is detected as a byte-level mismatch", async () => {
  await assert.rejects(
    verifyRecord(record, Buffer.concat([report, Buffer.from("\n")])),
    /Report hash mismatch/,
  );
});

test("signature binds the issuer, URI, predecessor and agent", async () => {
  for (const patch of [
    { issuer: (await generateKeyPairSigner()).address },
    { report_uri: "https://example.com/different" },
    { previous_record_sha256: "1".repeat(64) },
    { subject_agent_id: "another-agent" },
  ]) {
    const tampered = { ...record, payload: { ...record.payload, ...patch } };
    tampered.record_sha256 = sha256(canonicalPayload(tampered.payload));
    await assert.rejects(verifyRecord(tampered), /Invalid issuer signature/);
  }
});

test("rejects hash mutation, unknown fields, network and schema versions", async () => {
  await assert.rejects(
    verifyRecord({ ...record, record_sha256: "0".repeat(64) }),
    /hash mismatch/,
  );
  await assert.rejects(
    verifyRecord({ ...record, unexpected: true }),
    /Invalid record/,
  );
  for (const patch of [
    { network: "solana:mainnet" },
    { schema_version: "epistemics.record.v2" },
  ]) {
    await assert.rejects(
      verifyRecord({ ...record, payload: { ...record.payload, ...patch } }),
      /Invalid record/,
    );
  }
});

test("canonical payload encoding ignores insertion order and handles string escaping", () => {
  const reversed = Object.fromEntries(
    Object.entries(record.payload).reverse(),
  ) as typeof record.payload;
  assert.equal(canonicalPayload(reversed), canonicalPayload(record.payload));
  const encoded = canonicalPayload({
    ...record.payload,
    subject_agent_id: 'agent:\n"λ',
  });
  assert.ok(encoded.startsWith('{"battery_sha256":'));
  assert.ok(encoded.includes('"subject_agent_id":"agent:\\n\\"λ"'));
});

test("builds a valid signed transaction with an actual Memo instruction", async () => {
  const tx = await buildAnchorTransaction(record, signer, {
    blockhash: blockhash("11111111111111111111111111111111"),
    lastValidBlockHeight: 123n,
  });
  const sig = tx.signatures[signer.address];
  assert.ok(sig);
  assert.ok(
    await verifySignature(
      signer.keyPair.publicKey,
      signatureBytes(sig),
      tx.messageBytes,
    ),
  );
  const message = getCompiledTransactionMessageDecoder().decode(
    tx.messageBytes,
  );
  assert.ok(message.version === 0);
  const instruction = message.instructions[0];
  assert.ok(instruction);
  assert.equal(
    message.staticAccounts[instruction.programAddressIndex],
    MEMO_PROGRAM_ADDRESS,
  );
  assert.equal(new TextDecoder().decode(instruction.data), memoText(record));
  assert.ok(instruction.accountIndices?.includes(0));
});

test("refuses an anchor signed by someone other than the issuer", async () => {
  await assert.rejects(
    buildAnchorTransaction(record, await generateKeyPairSigner(), {
      blockhash: blockhash("11111111111111111111111111111111"),
      lastValidBlockHeight: 123n,
    }),
    /must be the record issuer/,
  );
});

const included: ParsedTransaction = {
  meta: { err: null },
  transaction: {
    message: {
      accountKeys: [{ pubkey: signer.address, signer: true }],
      instructions: [
        { programId: MEMO_PROGRAM_ADDRESS, parsed: memoText(record) },
      ],
    },
  },
};

test("inclusion requires success, issuer signature, correct program and matching commitment", () => {
  assert.doesNotThrow(() => assertAnchorIncluded(record, included));
  assert.throws(() => assertAnchorIncluded(record, null), /missing/);
  assert.throws(
    () =>
      assertAnchorIncluded(record, { ...included, meta: { err: "failed" } }),
    /unsuccessful/,
  );
  for (const key of ["signer", "memo", "program"]) {
    const altered = structuredClone(included);
    const message = altered.transaction.message;
    if (key === "signer")
      message.accountKeys = [{ pubkey: signer.address, signer: false }];
    else
      message.instructions = [
        {
          programId: key === "program" ? signer.address : MEMO_PROGRAM_ADDRESS,
          parsed: key === "memo" ? "wrong memo" : memoText(record),
        },
      ];
    assert.throws(() => assertAnchorIncluded(record, altered));
  }
});

test("wrong network is rejected", () => {
  assert.doesNotThrow(() => assertDevnet(DEVNET_GENESIS));
  assert.throws(() => assertDevnet("mainnet"), /devnet only/);
});

test("RPC flow simulates by default, sends only explicitly, then requires finalized inclusion", async () => {
  const calls: string[] = [];
  let genesis = DEVNET_GENESIS;
  let failSimulation = false;
  let failSend = false;
  let finalized = true;
  const fetchMock = mock.method(
    globalThis,
    "fetch",
    async (_input: string | URL | Request, init?: RequestInit) => {
      const request = JSON.parse(String(init?.body));
      calls.push(request.method);
      let result: unknown;
      switch (request.method) {
        case "getGenesisHash":
          result = genesis;
          break;
        case "getLatestBlockhash":
          result = {
            context: { slot: 1 },
            value: {
              blockhash: "11111111111111111111111111111111",
              lastValidBlockHeight: 100,
            },
          };
          break;
        case "simulateTransaction":
          result = {
            context: { slot: 1 },
            value: { err: failSimulation ? "failure" : null, logs: [] },
          };
          break;
        case "sendTransaction":
          if (failSend) throw new Error("Connection closed after request");
          result = getSignatureFromTransaction(
            getTransactionDecoder().decode(
              Buffer.from(request.params[0], "base64"),
            ),
          );
          break;
        case "getTransaction":
          // Kit omits the chain's default finalized commitment on the wire.
          assert.equal(
            request.params[1].commitment ?? "finalized",
            "finalized",
          );
          result = finalized ? included : null;
          break;
        default:
          throw new Error(`Unexpected method: ${request.method}`);
      }
      return new Response(
        JSON.stringify({ jsonrpc: "2.0", id: request.id, result }),
        {
          headers: { "Content-Type": "application/json" },
        },
      );
    },
  );
  try {
    const url = "https://devnet-rpc.example.invalid";
    assert.equal(
      (await anchorRecord(record, report, signer, url)).status,
      "simulated",
    );
    assert.ok(!calls.includes("sendTransaction"));
    const sent = await anchorRecord(record, report, signer, url, true);
    assert.equal(sent.status, "submitted");
    assert.equal(
      (await verifyAnchor(record, sent.signature, url)).status,
      "finalized",
    );
    finalized = false;
    await assert.rejects(
      verifyAnchor(record, sent.signature, url),
      /missing or unsuccessful/,
    );
    failSend = true;
    await assert.rejects(
      anchorRecord(record, report, signer, url, true),
      (error: unknown) => {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes(sent.signature));
        assert.ok(error.message.includes("outcome unknown"));
        return true;
      },
    );
    failSimulation = true;
    await assert.rejects(
      anchorRecord(record, report, signer, url, true),
      /Simulation failed/,
    );
    assert.equal(calls.filter((c) => c === "sendTransaction").length, 2);
    genesis = "wrong-network";
    await assert.rejects(
      anchorRecord(record, report, signer, url, true),
      /devnet only/,
    );
  } finally {
    fetchMock.mock.restore();
  }
});
