import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { generateKeyPairSigner, signBytes } from "@solana/kit";
import {
  canonicalPassportPayload,
  createPassportAttestation,
  type PassportAttestation,
  verifyPassportAttestation,
} from "../src/passports.js";
import { sha256 } from "../src/records.js";

const root = fileURLToPath(new URL("../../../", import.meta.url));
const python = join(root, ".venv/bin/python");
const fixture = JSON.parse(
  execFileSync(
    python,
    [
      "-c",
      `
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from epistemics.live.service import LiveService
from epistemics.live.models import CoreTrial
from epistemics.baselines import answer_trial as numeric
from epistemics.discovery.simulation import answer_trial as discovery
with TemporaryDirectory() as directory:
    service = LiveService(Path(directory) / 'test.db')
    agent = {'kind':'agent', 'subject_id':'synthetic:passport-test', 'configuration':{'model':'analytic', 'model_version':'test', 'configuration_sha256':'0'*64}}
    sid = service.start(agent, request_id='passport-interop-test', instructions_accepted=True, response_origin='synthetic', seed=17)['session_id']
    while not (current := service.get_trial(sid))['complete']:
        trial = CoreTrial.model_validate(current['trial'])
        answer = discovery(trial.payload) if trial.module == 'discovery' else numeric(trial.payload)
        service.submit(sid, trial.trial_id, answer.model_dump())
    print(json.dumps({'passport':service.passport_bytes(sid).decode(), 'report':service.report_bytes(sid).decode()}))
`,
    ],
    { cwd: root },
  ).toString(),
);
const passport = Buffer.from(fixture.passport);
const report = Buffer.from(fixture.report);
const signer = await generateKeyPairSigner();
const issuedAt = new Date().toISOString();
const expiresAt = new Date(Date.parse(issuedAt) + 3600000).toISOString();
const options = {
  passportUri: "https://example.invalid/passport.json",
  issuedAt,
  expiresAt,
};
const attestation = await createPassportAttestation(
  passport,
  report,
  signer,
  options,
);
const verifyOptions = {
  expectedIssuer: signer.address,
  now: new Date(issuedAt),
  reportBytes: report,
};

async function resign(value: PassportAttestation) {
  const canonical = canonicalPassportPayload(value.payload);
  value.attestation_sha256 = sha256(canonical);
  value.signature_base64 = Buffer.from(
    await signBytes(
      signer.keyPair.privateKey,
      new TextEncoder().encode(
        `epistemics/passport-attestation-signature/v1\n${canonical}`,
      ),
    ),
  ).toString("base64");
  return value;
}

test("core Python artifacts round-trip without changing draft or synthetic status", async () => {
  assert.deepEqual(
    await verifyPassportAttestation(attestation, passport, verifyOptions),
    attestation,
  );
  assert.equal(attestation.payload.response_origin, "synthetic");
  assert.equal(attestation.payload.execution_verification, "operator_asserted");
  assert.equal(
    JSON.parse(passport.toString()).issuance_status,
    "draft_unsigned",
  );
  assert.equal(attestation.payload.passport_sha256, sha256(passport));
  assert.equal(attestation.payload.report_sha256, sha256(report));
  const reversed = Object.fromEntries(
    Object.entries(attestation.payload).reverse(),
  ) as typeof attestation.payload;
  assert.equal(
    canonicalPassportPayload(reversed),
    canonicalPassportPayload(attestation.payload),
  );
});

test("consumer must independently select a trusted issuer and enforce validity", async () => {
  await assert.rejects(
    verifyPassportAttestation(attestation, passport, {
      ...verifyOptions,
      expectedIssuer: (await generateKeyPairSigner()).address,
    }),
    /Unexpected issuer/,
  );
  for (const now of [
    new Date(Date.parse(issuedAt) - 1),
    new Date(expiresAt),
    new Date(Number.NaN),
  ]) {
    await assert.rejects(
      verifyPassportAttestation(attestation, passport, {
        ...verifyOptions,
        now,
      }),
      /validity window/,
    );
  }
  await assert.rejects(
    createPassportAttestation(passport, report, signer, {
      ...options,
      expiresAt: issuedAt,
    }),
    /Expiry/,
  );
});

test("byte mutations and signed metadata substitutions fail", async () => {
  await assert.rejects(
    verifyPassportAttestation(
      attestation,
      Buffer.concat([passport, Buffer.from("\n")]),
      verifyOptions,
    ),
    /Passport hash/,
  );
  await assert.rejects(
    verifyPassportAttestation(attestation, passport, {
      ...verifyOptions,
      reportBytes: Buffer.concat([report, Buffer.from("\n")]),
    }),
    /Report hash/,
  );
  for (const patch of [
    { subject_agent_id: "other-agent" },
    { configuration_sha256: "1".repeat(64) },
    { protocol_sha256: "1".repeat(64) },
    { response_origin: "agent" as const },
    { passport_uri: "https://example.invalid/other" },
  ]) {
    const changed = structuredClone(attestation);
    Object.assign(changed.payload, patch);
    changed.attestation_sha256 = sha256(
      canonicalPassportPayload(changed.payload),
    );
    await assert.rejects(
      verifyPassportAttestation(changed, passport, verifyOptions),
      /signature/,
    );
  }
  const changed = structuredClone(attestation);
  changed.payload.subject_agent_id = "other-agent";
  await assert.rejects(
    verifyPassportAttestation(await resign(changed), passport, verifyOptions),
    /metadata mismatch/,
  );
});

test("rejects unknown schemas, assurance escalation and unknown properties", async () => {
  for (const patch of [
    { schema_version: "epistemics.passport-attestation.v2" },
    { execution_verification: "verified" },
    { extra: true },
  ]) {
    await assert.rejects(
      verifyPassportAttestation(
        { ...attestation, payload: { ...attestation.payload, ...patch } },
        passport,
        verifyOptions,
      ),
      /Invalid passport attestation/,
    );
  }
  await assert.rejects(
    verifyPassportAttestation(
      { ...attestation, unexpected: true },
      passport,
      verifyOptions,
    ),
    /Invalid passport attestation/,
  );
  await assert.rejects(
    createPassportAttestation(passport, report, signer, {
      ...options,
      passportUri: "https://user:password@example.invalid/profile",
    }),
    /Invalid passport URI/,
  );
});

test("signature domain and calendar validity cannot be substituted", async () => {
  const wrongDomain = structuredClone(attestation);
  wrongDomain.signature_base64 = Buffer.from(
    await signBytes(
      signer.keyPair.privateKey,
      new TextEncoder().encode(
        `epistemics/record-signature/v1\n${canonicalPassportPayload(wrongDomain.payload)}`,
      ),
    ),
  ).toString("base64");
  await assert.rejects(
    verifyPassportAttestation(wrongDomain, passport, verifyOptions),
    /signature/,
  );
  for (const expiresAt of [
    "2028-02-30T12:00:00.000Z",
    "2028-01-01T24:00:00.000Z",
  ]) {
    await assert.rejects(
      createPassportAttestation(passport, report, signer, {
        ...options,
        expiresAt,
      }),
      /timestamp/,
    );
  }
  await assert.rejects(
    createPassportAttestation(passport, report, signer, {
      ...options,
      issuedAt: "2000-01-01T00:00:00.000Z",
    }),
    /precedes evaluation/,
  );
});

test("requires matching completed agent artifacts and excludes human publication", async () => {
  for (const mutate of [
    (p: any) => {
      p.context.participant = { kind: "human", subject_id: "private-human" };
    },
    (p: any) => {
      p.context.accepted_answers = 33;
    },
    (p: any) => {
      p.dimensions[1] = p.dimensions[0];
    },
    (p: any) => {
      p.context.participant.subject_id = "different-subject";
    },
  ]) {
    const p = JSON.parse(passport.toString());
    mutate(p);
    await assert.rejects(
      createPassportAttestation(
        Buffer.from(JSON.stringify(p)),
        report,
        signer,
        options,
      ),
    );
  }
});

test("CLI emits machine-readable verification boundaries and never overwrites", async () => {
  const dir = await mkdtemp(join(tmpdir(), "epistemics-passport-"));
  const cli = join(root, "packages/solana/src/passport-cli.ts");
  const run = (...args: string[]) =>
    execFileSync(process.execPath, ["--import", "tsx", cli, ...args], {
      cwd: root,
      stdio: "pipe",
    }).toString();
  try {
    const p = join(dir, "passport.json"),
      r = join(dir, "report.json"),
      a = join(dir, "attestation.json");
    await writeFile(p, passport);
    await writeFile(r, report);
    const created = JSON.parse(
      run("demo", "--passport", p, "--report", r, "--output", a),
    );
    const checked = JSON.parse(
      run(
        "verify",
        "--passport",
        p,
        "--attestation",
        a,
        "--issuer",
        created.issuer,
      ),
    );
    assert.equal(checked.status, "verified_offline");
    for (const field of [
      "report_bytes_checked",
      "registry_binding_verified",
      "execution_verified",
      "revocation_checked",
      "payment_authorized",
      "derivation_recomputed",
    ])
      assert.equal(checked[field], false);
    const original = await readFile(a);
    assert.throws(() =>
      run("demo", "--passport", p, "--report", r, "--output", a),
    );
    assert.deepEqual(await readFile(a), original);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
