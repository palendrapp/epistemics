import assert from "node:assert/strict";
import { test } from "node:test";
import { generateKeyPairSigner, getAddressEncoder } from "@solana/kit";
import {
  ENROLLMENT_DOMAIN,
  enrollProvider,
  issueEnrolledPassport,
  jsonBytes,
} from "../src/consumer/enrollment.js";
import { sign } from "../src/consumer/signatures.js";
import { sha256 } from "../src/records.js";
import { fixture } from "./consumer-fixture.js";
import { providerPreview } from "./provider-preview.js";

test("new evaluation enrolled before collection, signed issuance and private consumer traversal", async () => {
  const run = await providerPreview();
  try {
    assert.equal(run.issued.registry.mode, "simulation");
    assert.equal(
      run.issued.receipt.enrollment_sha256,
      run.bundle.enrollment.payload_sha256,
    );
    assert.equal(run.decision.passport_sha256, sha256(run.passportBytes));
    assert.equal(
      run.decision.attestation_sha256,
      run.issued.attestation.attestation_sha256,
    );
    assert.equal(run.decision.action, "ineligible");
    assert.ok(
      run.decision.reasons.some((r) => r.code === "ORIGIN_NOT_AGENT"),
      JSON.stringify(run.decision.reasons),
    );
    assert.equal(run.decision.payment_authorized, false);
    const changedProtocol = await sign(
      { ...run.bundle.enrollment.payload, protocol_sha256: "a".repeat(64) },
      ENROLLMENT_DOMAIN,
      run.f.wallet,
    );
    await assert.rejects(
      issueEnrolledPassport({ ...run.options, enrollment: changedProtocol }),
      /protocol differs/,
    );
    const alteredPassport = JSON.parse(run.passportBytes.toString());
    const alteredReport = JSON.parse(run.reportBytes.toString());
    alteredPassport.context.participant.configuration.model = "another-model";
    alteredReport.context.participant.configuration.model = "another-model";
    const alteredReportBytes = jsonBytes(alteredReport);
    alteredPassport.source.sha256 = sha256(alteredReportBytes);
    await assert.rejects(
      issueEnrolledPassport({
        ...run.options,
        passportBytes: jsonBytes(alteredPassport),
        reportBytes: alteredReportBytes,
      }),
      /participant differs/,
    );
    const report = JSON.parse(run.reportBytes.toString());
    const participant = JSON.parse(
      Buffer.from(run.bundle.participantBytes).toString(),
    );
    assert.deepEqual(report.context.participant, participant);
    assert.ok(
      Date.parse(report.context.started_at) >=
        Date.parse(run.bundle.enrollment.payload.issued_at),
    );
    for (const field of ["participantBytes", "registryBytes"] as const) {
      await assert.rejects(
        issueEnrolledPassport({
          ...run.options,
          [field]: Buffer.concat([
            Buffer.from(run.options[field]),
            Buffer.from(" "),
          ]),
        }),
        /bytes changed/,
      );
    }
    await assert.rejects(
      issueEnrolledPassport({
        ...run.options,
        issuer: await generateKeyPairSigner(),
      }),
      /Issuer differs/,
    );
    await assert.rejects(
      issueEnrolledPassport({
        ...run.options,
        authority: await generateKeyPairSigner(),
      }),
      /current controller/,
    );
    await assert.rejects(
      issueEnrolledPassport({
        ...run.options,
        transport: { ...run.options.transport, mode: "rpc_observed" },
      }),
      /promote simulation/,
    );
    const p = structuredClone(run.bundle.enrollment);
    p.payload.controller = run.f.issuer.address;
    await assert.rejects(
      issueEnrolledPassport({ ...run.options, enrollment: p }),
      /hash mismatch/,
    );
    // Both account ownership and signer authorization are freshly resolved before issuance.
    const newController = await generateKeyPairSigner();
    const data = Buffer.from(run.f.accounts[5]!.data[0], "base64");
    Buffer.from(getAddressEncoder().encode(newController.address)).copy(
      data,
      1,
    );
    run.f.accounts[5]!.data[0] = data.toString("base64");
    await assert.rejects(
      issueEnrolledPassport(run.options),
      /changed since enrollment/,
    );
  } finally {
    await run.f.close();
  }
});

test("pre-enrollment runs, protocol substitution and unauthorized enrollment are rejected", async () => {
  const f = await fixture("synthetic");
  try {
    const base = {
      asset: f.asset,
      authority: f.wallet,
      issuer: f.issuer.address,
      configuration: f.passport.context.participant.configuration,
      protocolVersion: f.passport.context.protocol_version,
      protocolSha256: f.passport.context.protocol_sha256,
      transport: f.options.transport,
      simulationPin: f.options.simulationPin!,
      expiresAt: f.expires,
    };
    await assert.rejects(
      enrollProvider({ ...base, authority: await generateKeyPairSigner() }),
      /current controller/,
    );
    const bundle = await enrollProvider(base);
    const options = {
      ...bundle,
      authority: f.wallet,
      issuer: f.issuer,
      passportBytes: f.artifacts.get("/passport.json")!,
      reportBytes: jsonBytes(f.report),
      passportUri: f.bindingPayload.passport_uri,
      attestationUri: f.bindingPayload.attestation_uri,
      endpoint: f.bindingPayload.endpoint,
      payee: f.wallet.address,
      paymentAsset: f.asset,
      expiresAt: f.expires,
      transport: f.options.transport,
      simulationPin: f.options.simulationPin!,
      now: new Date(),
    };
    await assert.rejects(issueEnrolledPassport(options), /predates enrollment/);
  } finally {
    await f.close();
  }
});
