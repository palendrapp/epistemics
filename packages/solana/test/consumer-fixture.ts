/** Synthetic account bytes and responses for offline tests, never empirical evidence. */
import { execFileSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  address,
  generateKeyPairSigner,
  getAddressEncoder,
  getProgramDerivedAddress,
} from "@solana/kit";
import {
  type ConsumerPolicy,
  type ConsumerRequest,
  type ProviderBinding,
} from "../src/consumer/contracts.js";
import {
  type ConsumerOptions,
  createProviderBinding,
} from "../src/consumer/evaluate.js";
import { artifactServer } from "../src/consumer/hosting.js";
import {
  type Account,
  CORE_PROGRAM,
  DEPLOYMENT,
  type DeploymentPin,
  NETWORK,
  REGISTRY_PROGRAM,
  type RegistryTransport,
  subjectId,
} from "../src/consumer/registry.js";
import { appendStatus, createStatus } from "../src/consumer/status.js";
import { createPassportAttestation } from "../src/passports.js";
import { sha256 } from "../src/records.js";

export const jsonBytes = (value: unknown) =>
  Buffer.from(`${JSON.stringify(value, null, 2)}\n`);
const root = fileURLToPath(new URL("../../../", import.meta.url));
const rawFixture = JSON.parse(
  execFileSync(
    join(root, ".venv/bin/python"),
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
    service = LiveService(Path(directory) / 'fixture.db')
    agent = {'kind':'agent','subject_id':'synthetic:consumer-test','configuration':{'model':'synthetic','model_version':'test','configuration_sha256':'0'*64}}
    sid = service.start(agent, request_id='synthetic-consumer-fixture', instructions_accepted=True, response_origin='synthetic', seed=17)['session_id']
    while not (current := service.get_trial(sid))['complete']:
        trial = CoreTrial.model_validate(current['trial'])
        answer = discovery(trial.payload) if trial.module == 'discovery' else numeric(trial.payload)
        service.submit(sid, trial.trial_id, answer.model_dump())
    print(json.dumps({'passport':json.loads(service.passport_bytes(sid)), 'report':json.loads(service.report_bytes(sid))}))
`,
    ],
    { cwd: root },
  ).toString(),
);

const key = (value: string) =>
  Buffer.from(getAddressEncoder().encode(address(value)));
function str(value: string) {
  const b = Buffer.from(value);
  const n = Buffer.alloc(4);
  n.writeUInt32LE(b.length);
  return Buffer.concat([n, b]);
}
function account(owner: string, executable: boolean, data: Buffer): Account {
  return { owner, executable, data: [data.toString("base64"), "base64"] };
}

export async function fixture(
  origin: "synthetic" | "agent" = "agent",
  input = rawFixture,
) {
  // Agent-origin variants exercise the acceptance branch with invented test data.
  // They remain simulation mode and are not exported as real evaluations.
  const issuer = await generateKeyPairSigner();
  const controller = await generateKeyPairSigner();
  const wallet = await generateKeyPairSigner();
  const asset = (await generateKeyPairSigner()).address;
  const collection = (await generateKeyPairSigner()).address;
  const subject = subjectId(asset);
  const at = new Date();
  const now = new Date(at.valueOf() + 1000);
  const expires = new Date(at.valueOf() + 3600000).toISOString();
  const report = structuredClone(input.report);
  const passport = structuredClone(input.passport);
  for (const value of [report, passport]) {
    value.context.participant.subject_id = subject;
    value.context.response_origin = origin;
  }
  if (report.cases) {
    // Invented contract fixtures only: keep nested assertions consistent with
    // the simulated identity. This is never exported as an empirical run.
    report.manifest_sha256 = "f".repeat(64);
    for (const item of report.cases) {
      const child = JSON.parse(item.report_json);
      child.manifest.participant.subject_id = subject;
      child.manifest.response_origin = origin;
      child.manifest_sha256 = report.manifest_sha256;
      item.report_json = JSON.stringify(child);
      item.report_sha256 = sha256(item.report_json);
    }
  }
  const reportBytes = jsonBytes(report);
  passport.source.sha256 = sha256(reportBytes);
  const passportBytes = jsonBytes(passport);
  const uri = "https://consumer-test.invalid";
  const attestation = await createPassportAttestation(
    passportBytes,
    reportBytes,
    issuer,
    {
      passportUri: `${uri}/passport.json`,
      issuedAt: at.toISOString(),
      expiresAt: expires,
    },
  );
  const bindingPayload: ProviderBinding = {
    schema_version: "epistemics.provider-binding.v1",
    genesis_hash: DEPLOYMENT.genesis_hash,
    registry_program: REGISTRY_PROGRAM,
    agent_asset: asset,
    subject_agent_id: subject,
    controller: controller.address,
    signer: wallet.address,
    configuration_sha256: "0".repeat(64),
    passport_sha256: sha256(passportBytes),
    passport_uri: `${uri}/passport.json`,
    attestation_uri: `${uri}/attestation.json`,
    endpoint: "https://provider.invalid/research",
    payee: wallet.address,
    payment_network: NETWORK,
    payment_asset: asset,
    issued_at: at.toISOString(),
    expires_at: expires,
  };
  const binding = await createProviderBinding(bindingPayload, wallet);
  const statusRoot = await mkdtemp(join(tmpdir(), "epistemics-consumer-"));
  const status = await createStatus(
    [],
    issuer,
    attestation.attestation_sha256,
    {
      status: "active",
      evaluated_controller: controller.address,
      replacement_attestation_sha256: "",
      reason: "Synthetic fixture issuance",
      issued_at: at.toISOString(),
      expires_at: expires,
    },
  );
  await appendStatus(statusRoot, status);
  const artifacts = new Map([
    ["/passport.json", passportBytes],
    ["/attestation.json", jsonBytes(attestation)],
    ["/binding.json", jsonBytes(binding)],
    [
      "/metadata.json",
      jsonBytes({
        extensions: {
          epistemics: { provider_binding_uri: `${uri}/binding.json` },
        },
      }),
    ],
  ]);
  const token = randomBytes(32).toString("hex");
  const server = artifactServer({
    artifacts,
    token,
    statusRoot,
    issuer: issuer.address,
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const port = (server.address() as { port: number }).port;
  const localOrigin = `http://127.0.0.1:${port}`;
  const [, bump] = await getProgramDerivedAddress({
    programAddress: address(REGISTRY_PROGRAM),
    seeds: [Buffer.from("agent"), key(asset)],
  });
  const agentBytes = Buffer.concat([
    Buffer.from([241, 119, 69, 140, 233, 9, 112, 50]),
    key(collection),
    key(controller.address),
    key(controller.address),
    key(asset),
    Buffer.from([bump, 0, 1]),
    key(wallet.address),
    Buffer.alloc(120),
    Buffer.from([0, 0, 0]),
    str(`${uri}/metadata.json`),
    str("Synthetic test"),
    str(""),
  ]);
  const coreBytes = Buffer.concat([
    Buffer.from([1]),
    key(controller.address),
    Buffer.from([2]),
    key(collection),
    str("Test"),
    str(""),
    Buffer.from([0]),
  ]);
  const pins: DeploymentPin = structuredClone(DEPLOYMENT);
  const accounts: Account[] = [];
  for (const pin of [pins.registry, pins.core]) {
    const data = Buffer.concat([
      Buffer.from([3, 0, 0, 0]),
      Buffer.alloc(8),
      Buffer.from([1]),
      key(pin.upgrade_authority),
      Buffer.from("synthetic bytecode"),
    ]);
    pin.program_data_sha256 = sha256(data);
    accounts.push(
      account(
        "BPFLoaderUpgradeab1e11111111111111111111111",
        true,
        Buffer.concat([Buffer.from([2, 0, 0, 0]), key(pin.program_data)]),
      ),
      account("BPFLoaderUpgradeab1e11111111111111111111111", false, data),
    );
  }
  accounts.push(
    account(REGISTRY_PROGRAM, false, agentBytes),
    account(CORE_PROGRAM, false, coreBytes),
  );
  const transport: RegistryTransport = {
    mode: "simulation",
    async genesis() {
      return DEPLOYMENT.genesis_hash;
    },
    async accounts() {
      return { slot: 100, accounts };
    },
  };
  const policy: ConsumerPolicy = {
    schema_version: "epistemics.consumer-policy.v1",
    policy_id: "test-policy",
    version: "1",
    task_id: "bounded-research",
    trusted_issuers: [
      { issuer: issuer.address, status_base_uri: `${uri}/status/` },
    ],
    protocol_sha256: attestation.payload.protocol_sha256,
    protocol_version: attestation.payload.protocol_version,
    interpretation_version: attestation.payload.interpretation_version,
    max_evaluation_age_seconds: 86400,
    max_status_age_seconds: 600,
    max_binding_age_seconds: 600,
    receipt_ttl_seconds: 60,
    require_verified_execution: false,
    require_predictive_validation: false,
    allow_provisional: true,
    measurements: [
      {
        metric_id: "core.calibration.prior_weight.v1",
        minimum: 0,
        maximum: 2,
        uncertainty: "entire_95_interval",
      },
    ],
    payment_network: NETWORK,
    payment_asset: asset,
    max_amount: "1000",
  };
  const request: ConsumerRequest = {
    schema_version: "epistemics.consumer-request.v1",
    subject_agent_id: subject,
    configuration_sha256: "0".repeat(64),
    task_id: policy.task_id,
    endpoint: bindingPayload.endpoint,
    method: "POST",
    body_sha256: sha256("synthetic service request"),
    payee: wallet.address,
    payment_network: NETWORK,
    payment_asset: asset,
    max_amount: "100",
    nonce: "test-order-1",
  };
  const options: ConsumerOptions = {
    requestBytes: jsonBytes(request),
    policyBytes: jsonBytes(policy),
    agentAsset: asset,
    transport,
    simulationPin: pins,
    now,
    retrieval: {
      allowedOrigins: [uri, localOrigin],
      allowLoopbackHttp: true,
      bearerByOrigin: { [localOrigin]: token },
      loopbackMirrors: { [uri]: localOrigin },
    },
  };
  return {
    issuer,
    controller,
    wallet,
    asset,
    binding,
    bindingPayload,
    attestation,
    statusRoot,
    status,
    artifacts,
    options,
    policy,
    request,
    passport,
    report,
    now,
    expires,
    accounts,
    agentBytes,
    coreBytes,
    localOrigin,
    token,
    async close() {
      server.closeAllConnections();
      await new Promise<void>((resolve, reject) =>
        server.close((e) => (e ? reject(e) : resolve())),
      );
      await rm(statusRoot, { recursive: true, force: true });
    },
  };
}
