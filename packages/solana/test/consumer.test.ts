import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { generateKeyPairSigner, getAddressEncoder } from "@solana/kit";
import {
  createProviderBinding,
  evaluate,
  matchesReceipt,
} from "../src/consumer/evaluate.js";
import { allowedUrl, fetchBytes } from "../src/consumer/http.js";
import { measurements } from "../src/consumer/metrics.js";
import { decodeAgent, resolveIdentity } from "../src/consumer/registry.js";
import {
  appendStatus,
  createStatus,
  readStatusHistory,
  verifyStatusHistory,
} from "../src/consumer/status.js";
import { fixture, jsonBytes } from "./consumer-fixture.js";

test("resolve, private fetch, issuer/status verification and task decision work together", async () => {
  const f = await fixture();
  try {
    const result = await evaluate(f.options);
    assert.equal(result.action, "eligible", JSON.stringify(result.reasons));
    assert.equal(result.mode, "simulation");
    assert.equal(result.payment_authorized, false);
    assert.equal(result.measurements.length, 8);
    assert.equal(result.attestation_sha256, f.attestation.attestation_sha256);
    assert.equal(result.status_sequence, "0");
    assert.equal(
      matchesReceipt(
        result,
        f.options.requestBytes,
        f.options.policyBytes,
        f.now,
      ),
      false,
    );
    // Scope matching a trusted local result is deliberately not receipt authentication.
    const local = { ...result, mode: "rpc_observed" as const };
    assert.equal(
      matchesReceipt(
        local,
        f.options.requestBytes,
        f.options.policyBytes,
        f.now,
      ),
      true,
    );
    assert.equal(
      matchesReceipt(
        local,
        jsonBytes({ ...f.request, max_amount: "101" }),
        f.options.policyBytes,
        f.now,
      ),
      false,
    );
    assert.equal(
      matchesReceipt(
        local,
        f.options.requestBytes,
        jsonBytes({ ...f.policy, version: "2" }),
        f.now,
      ),
      false,
    );
    assert.equal(
      matchesReceipt(
        local,
        f.options.requestBytes,
        f.options.policyBytes,
        new Date(result.expires_at),
      ),
      false,
    );
  } finally {
    await f.close();
  }
});

test("synthetic origin cannot qualify an agent even with valid signatures", async () => {
  const f = await fixture("synthetic");
  try {
    const result = await evaluate(f.options);
    assert.equal(result.action, "ineligible");
    assert(result.reasons.some((r) => r.code === "ORIGIN_NOT_AGENT"));
  } finally {
    await f.close();
  }
});

test("subject, configuration, endpoint, payee and budget substitutions are rejected", async () => {
  const f = await fixture();
  try {
    for (const patch of [
      { subject_agent_id: "other-subject" },
      { configuration_sha256: "1".repeat(64) },
      { endpoint: "https://attacker.invalid/task" },
      { payee: f.issuer.address },
      { payment_network: "solana:wrong" },
      { payment_asset: f.issuer.address },
      { max_amount: "1001" },
      { task_id: "unsupported" },
    ]) {
      const result = await evaluate({
        ...f.options,
        requestBytes: jsonBytes({ ...f.request, ...patch }),
      });
      assert.equal(result.action, "ineligible", JSON.stringify(patch));
    }
  } finally {
    await f.close();
  }
});

test("untrusted issuers, byte tampering and invalid bindings fail closed", async () => {
  const f = await fixture();
  try {
    const p = {
      ...f.policy,
      trusted_issuers: [
        { ...f.policy.trusted_issuers[0]!, issuer: f.wallet.address },
      ],
    };
    assert.equal(
      (await evaluate({ ...f.options, policyBytes: jsonBytes(p) })).reasons[0]!
        .code,
      "ISSUER_UNTRUSTED",
    );
    const original = f.artifacts.get("/passport.json")!;
    f.artifacts.set(
      "/passport.json",
      Buffer.concat([original, Buffer.from("\n")]),
    );
    assert.equal(
      (await evaluate(f.options)).reasons[0]!.code,
      "PASSPORT_INVALID_OR_EXPIRED",
    );
    f.artifacts.set("/passport.json", original);
    f.artifacts.set(
      "/binding.json",
      jsonBytes({
        ...f.binding,
        payload: { ...f.binding.payload, payee: f.issuer.address },
      }),
    );
    assert.equal(
      (await evaluate(f.options)).reasons[0]!.code,
      "BINDING_INVALID",
    );
  } finally {
    await f.close();
  }
});

test("current Core owner takes precedence and disables stale operational wallet", async () => {
  const f = await fixture();
  try {
    const newOwner = await generateKeyPairSigner();
    const moved = Buffer.from(f.coreBytes);
    moved.set(getAddressEncoder().encode(newOwner.address), 1);
    f.accounts[5]!.data[0] = moved.toString("base64");
    const identity = await resolveIdentity(
      f.asset,
      f.options.transport,
      f.now,
      f.options.simulationPin,
    );
    assert.equal(identity.controller, newOwner.address);
    assert.equal(identity.operational_wallet, null);
    assert.equal(
      (await evaluate(f.options)).reasons[0]!.code,
      "BINDING_INVALID",
    );
    const renewed = await createProviderBinding(
      {
        ...f.bindingPayload,
        controller: newOwner.address,
        signer: newOwner.address,
      },
      newOwner,
    );
    f.artifacts.set("/binding.json", jsonBytes(renewed));
    assert(
      (await evaluate(f.options)).reasons.some(
        (r) => r.code === "EVALUATED_CONTROLLER_MISMATCH",
      ),
    );
  } finally {
    await f.close();
  }
});

test("registry drift, wrong chain, wrong account owner and malformed account layout cannot qualify", async () => {
  const f = await fixture();
  try {
    await assert.rejects(
      resolveIdentity(
        f.asset,
        { ...f.options.transport, mode: "rpc_observed" },
        f.now,
        f.options.simulationPin,
      ),
      /offline simulation/,
    );
    const changed = structuredClone(f.options.simulationPin!);
    changed.registry.program_data_sha256 = "0".repeat(64);
    assert.equal(
      (await evaluate({ ...f.options, simulationPin: changed })).action,
      "review_required",
    );
    assert.equal(
      (
        await evaluate({
          ...f.options,
          transport: {
            ...f.options.transport,
            async genesis() {
              return "wrong";
            },
          },
        })
      ).action,
      "review_required",
    );
    f.accounts[4]!.owner = f.issuer.address;
    assert.equal((await evaluate(f.options)).action, "review_required");
    assert.throws(() => decodeAgent(Buffer.from([1, 2, 3])), /Truncated/);
    const invalid = Buffer.from(f.agentBytes);
    invalid[138] = 2;
    assert.throws(() => decodeAgent(invalid), /Borsh/);
  } finally {
    await f.close();
  }
});

test("missing status, stale evidence and unsupported assurance return review", async () => {
  const f = await fixture();
  try {
    for (const patch of [
      { max_evaluation_age_seconds: 1 },
      { max_status_age_seconds: 1 },
      { max_binding_age_seconds: 1 },
      { require_verified_execution: true },
      { require_predictive_validation: true },
      { allow_provisional: false },
      { protocol_sha256: "f".repeat(64) },
      { interpretation_version: "unsupported" },
      {
        measurements: [
          {
            metric_id: "not-measured",
            minimum: 0,
            maximum: 1,
            uncertainty: "point",
          },
        ],
      },
    ]) {
      const result = await evaluate({
        ...f.options,
        policyBytes: jsonBytes({ ...f.policy, ...patch }),
      });
      assert.equal(result.action, "review_required", JSON.stringify(patch));
    }
    const missing = {
      ...f.policy,
      trusted_issuers: [
        {
          issuer: f.issuer.address,
          status_base_uri: "https://consumer-test.invalid/missing/",
        },
      ],
    };
    assert.equal(
      (
        await evaluate({ ...f.options, policyBytes: jsonBytes(missing) })
      ).reasons.at(-1)!.code,
      "STATUS_UNAVAILABLE",
    );
    assert.equal(
      (await evaluate({ ...f.options, minimumStatusSequence: "1" })).reasons.at(
        -1,
      )!.code,
      "STATUS_INVALID_OR_ROLLED_BACK",
    );
  } finally {
    await f.close();
  }
});

test("explicit thresholds and missing uncertainty produce different reasons", async () => {
  const f = await fixture();
  try {
    let p = {
      ...f.policy,
      measurements: [
        {
          metric_id: "core.calibration.prior_weight.v1",
          minimum: 5,
          maximum: 6,
          uncertainty: "point",
        },
      ],
    };
    assert.equal(
      (await evaluate({ ...f.options, policyBytes: jsonBytes(p) })).reasons.at(
        -1,
      )!.code,
      "MEASUREMENT_OUTSIDE_POLICY",
    );
    p = {
      ...p,
      measurements: [
        {
          metric_id: "core.discovery.final_brier.v1",
          minimum: 0,
          maximum: 1,
          uncertainty: "entire_95_interval",
        },
      ],
    };
    assert.equal(
      (await evaluate({ ...f.options, policyBytes: jsonBytes(p) })).reasons.at(
        -1,
      )!.code,
      "UNCERTAINTY_MISSING",
    );
    const copy = structuredClone(f.passport);
    copy.dimensions[0].measurements[0].label =
      "A completely different display label";
    assert.deepEqual(measurements(copy), measurements(f.passport));
    copy.dimensions[0].measurements.push(copy.dimensions[0].measurements[0]);
    assert.throws(() => measurements(copy), /Ambiguous/);
  } finally {
    await f.close();
  }
});

test("withdrawals and corrections are signed, append-only and cannot be reversed", async () => {
  const f = await fixture();
  try {
    const withdrawn = await createStatus(
      [f.status],
      f.issuer,
      f.attestation.attestation_sha256,
      {
        status: "withdrawn",
        evaluated_controller: f.controller.address,
        replacement_attestation_sha256: "",
        reason: "Fixture withdrawal",
        issued_at: f.now.toISOString(),
        expires_at: f.expires,
      },
    );
    const writes = await Promise.allSettled([
      appendStatus(f.statusRoot, withdrawn),
      appendStatus(f.statusRoot, withdrawn),
    ]);
    assert.equal(writes.filter((w) => w.status === "fulfilled").length, 1);
    const result = await evaluate(f.options);
    assert.equal(result.action, "ineligible");
    assert(result.reasons.some((r) => r.code === "PASSPORT_WITHDRAWN"));
    const history = await readStatusHistory(
      f.statusRoot,
      f.issuer.address,
      f.attestation.attestation_sha256,
    );
    assert.equal(history.length, 2);
    await assert.rejects(
      createStatus(history, f.issuer, f.attestation.attestation_sha256, {
        ...withdrawn.payload,
        status: "active",
      }),
      /Terminal/,
    );
    await assert.rejects(
      verifyStatusHistory(
        [withdrawn],
        f.issuer.address,
        f.attestation.attestation_sha256,
      ),
      /sequence/,
    );
    const corrected = await createStatus(
      [f.status],
      f.issuer,
      f.attestation.attestation_sha256,
      {
        status: "corrected",
        evaluated_controller: f.controller.address,
        replacement_attestation_sha256: "a".repeat(64),
        reason: "Fixture correction",
        issued_at: f.now.toISOString(),
        expires_at: f.expires,
      },
    );
    await verifyStatusHistory(
      [f.status, corrected],
      f.issuer.address,
      f.attestation.attestation_sha256,
      { now: f.now },
    );
    await assert.rejects(
      verifyStatusHistory(
        [
          f.status,
          {
            ...corrected,
            payload: { ...corrected.payload, reason: "tampered" },
          },
        ],
        f.issuer.address,
        f.attestation.attestation_sha256,
      ),
      /hash/,
    );
  } finally {
    await f.close();
  }
});

test("private hosting and retrieval enforce capability, origin, redirects and byte limits", async () => {
  const f = await fixture();
  try {
    await assert.rejects(
      fetchBytes(`${f.localOrigin}/passport.json`, {
        allowedOrigins: [f.localOrigin],
        allowLoopbackHttp: true,
      }),
      /401/,
    );
    await assert.rejects(
      fetchBytes("https://outside.invalid/passport.json", f.options.retrieval),
      /origins/,
    );
    await assert.rejects(
      fetchBytes("https://consumer-test.invalid/passport.json", {
        ...f.options.retrieval,
        maxBytes: 1,
      }),
      /size/,
    );
    assert.throws(
      () =>
        allowedUrl("http://169.254.169.254/latest", {
          allowedOrigins: ["http://169.254.169.254"],
          allowLoopbackHttp: true,
        }),
      /origins/,
    );
    const server = createServer((_req, res) =>
      res.writeHead(302, { location: "https://outside.invalid/" }).end(),
    );
    await new Promise<void>((resolve) =>
      server.listen(0, "127.0.0.1", resolve),
    );
    try {
      const origin = `http://127.0.0.1:${(server.address() as { port: number }).port}`;
      await assert.rejects(
        fetchBytes(origin, {
          allowedOrigins: [origin],
          allowLoopbackHttp: true,
        }),
        /fetch failed/,
      );
    } finally {
      server.closeAllConnections();
      await new Promise<void>((resolve) => server.close(() => resolve()));
    }
  } finally {
    await f.close();
  }
});

test("unknown fields and ambiguous policies are rejected", async () => {
  const f = await fixture();
  try {
    await assert.rejects(
      evaluate({
        ...f.options,
        requestBytes: jsonBytes({ ...f.request, extra: true }),
      }),
      /Invalid request/,
    );
    await assert.rejects(
      evaluate({
        ...f.options,
        policyBytes: jsonBytes({
          ...f.policy,
          measurements: [f.policy.measurements[0], f.policy.measurements[0]],
        }),
      }),
      /Ambiguous/,
    );
  } finally {
    await f.close();
  }
});

test("remembered status detects a conflicting signed history and an older response", async () => {
  const f = await fixture();
  try {
    const rememberedStatus = {
      [f.attestation.attestation_sha256]: {
        sequence: "0",
        sha256: f.status.payload_sha256,
      },
    };
    assert.equal(
      (await evaluate({ ...f.options, rememberedStatus })).action,
      "eligible",
    );
    assert.equal(
      (
        await evaluate({
          ...f.options,
          rememberedStatus: {
            [f.attestation.attestation_sha256]: {
              sequence: "0",
              sha256: "f".repeat(64),
            },
          },
        })
      ).reasons.at(-1)!.code,
      "STATUS_INVALID_OR_ROLLED_BACK",
    );
    const next = await createStatus(
      [f.status],
      f.issuer,
      f.attestation.attestation_sha256,
      {
        ...f.status.payload,
        issued_at: f.now.toISOString(),
        reason: "Refresh",
      },
    );
    await appendStatus(f.statusRoot, next);
    assert.equal(
      (await evaluate({ ...f.options, rememberedStatus })).action,
      "eligible",
    );
    assert.equal(
      (
        await evaluate({
          ...f.options,
          rememberedStatus: {
            [f.attestation.attestation_sha256]: {
              sequence: "0",
              sha256: "f".repeat(64),
            },
          },
        })
      ).reasons.at(-1)!.code,
      "STATUS_INVALID_OR_ROLLED_BACK",
    );
    await assert.rejects(
      createStatus([f.status], f.issuer, f.attestation.attestation_sha256, {
        ...f.status.payload,
        evaluated_controller: f.wallet.address,
      }),
      /controller cannot change/,
    );
  } finally {
    await f.close();
  }
});

test("operator CLI signs bindings, appends status, exposes catalog and refuses overwrite", async () => {
  const f = await fixture();
  try {
    const signer = await generateKeyPairSigner(true);
    const pkcs = Buffer.from(
      await crypto.subtle.exportKey("pkcs8", signer.keyPair.privateKey),
    );
    const secret = Buffer.concat([
      pkcs.subarray(-32),
      Buffer.from(getAddressEncoder().encode(signer.address)),
    ]);
    const keyFile = join(f.statusRoot, "ephemeral.keypair.json");
    const payloadFile = join(f.statusRoot, "binding-input.json");
    const destination = join(f.statusRoot, "binding.json");
    await writeFile(keyFile, JSON.stringify([...secret]), { mode: 0o600 });
    await writeFile(
      payloadFile,
      jsonBytes({ ...f.bindingPayload, signer: signer.address }),
    );
    const root = fileURLToPath(new URL("../../../", import.meta.url));
    function cli(...args: string[]) {
      return JSON.parse(
        execFileSync(
          process.execPath,
          ["--import", "tsx", "packages/solana/src/consumer-cli.ts", ...args],
          { cwd: root, stdio: ["ignore", "pipe", "pipe"] },
        ).toString(),
      );
    }
    const bindArgs = [
      "bind",
      "--payload",
      payloadFile,
      "--keypair",
      keyFile,
      "--output",
      destination,
    ];
    assert.equal(cli(...bindArgs).status, "signed_provider_binding");
    assert.throws(() => cli(...bindArgs));
    assert.equal(cli("metrics").length, 8);
    const statusArgs = [
      "status",
      "--keypair",
      keyFile,
      "--controller",
      f.controller.address,
      "--status-root",
      f.statusRoot,
      "--attestation",
      f.attestation.attestation_sha256,
      "--status",
      "active",
      "--reason",
      "CLI test",
      "--expires",
      f.expires,
    ];
    assert.equal(cli(...statusArgs).sequence, "0");
    assert.equal(cli(...statusArgs).sequence, "1");
    const history = await readStatusHistory(
      f.statusRoot,
      signer.address,
      f.attestation.attestation_sha256,
    );
    assert.equal(history.length, 2);
    assert.equal(
      JSON.parse(await readFile(destination, "utf8")).payload.signer,
      signer.address,
    );
  } finally {
    await f.close();
  }
});
