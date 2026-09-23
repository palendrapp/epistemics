/** Explicitly synthetic workflow, including a NEW collection under the enrolled identity. */
import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  enrollProvider,
  issueEnrolledPassport,
  jsonBytes,
} from "../src/consumer/enrollment.js";
import { evaluate } from "../src/consumer/evaluate.js";
import { appendStatus } from "../src/consumer/status.js";
import { fixture } from "./consumer-fixture.js";

const root = fileURLToPath(new URL("../../../", import.meta.url));
export async function providerPreview() {
  const f = await fixture("synthetic");
  try {
    const bundle = await enrollProvider({
      asset: f.asset,
      authority: f.wallet,
      issuer: f.issuer.address,
      configuration: f.passport.context.participant.configuration,
      protocolVersion: f.passport.context.protocol_version,
      protocolSha256: f.passport.context.protocol_sha256,
      expiresAt: f.expires,
      transport: f.options.transport,
      simulationPin: f.options.simulationPin!,
    });
    const artifacts = JSON.parse(
      execFileSync(
        join(root, ".venv/bin/python"),
        [
          "-c",
          `
import json, sys
from pathlib import Path
from tempfile import TemporaryDirectory
from epistemics.live.service import LiveService
from epistemics.live.models import CoreTrial
from epistemics.baselines import answer_trial as numeric
from epistemics.discovery.simulation import answer_trial as discovery
with TemporaryDirectory() as directory:
    service = LiveService(Path(directory) / 'preview.db')
    sid = service.start(json.loads(sys.stdin.read()), request_id='synthetic-provider-preview', instructions_accepted=True, response_origin='synthetic', seed=17)['session_id']
    while not (current := service.get_trial(sid))['complete']:
        trial = CoreTrial.model_validate(current['trial'])
        answer = discovery(trial.payload) if trial.module == 'discovery' else numeric(trial.payload)
        service.submit(sid, trial.trial_id, answer.model_dump())
    print(json.dumps({'passport':service.passport_bytes(sid).decode(), 'report':service.report_bytes(sid).decode()}))
`,
        ],
        { cwd: root, input: bundle.participantBytes },
      ).toString(),
    ) as { passport: string; report: string };
    const passportBytes = Buffer.from(artifacts.passport),
      reportBytes = Buffer.from(artifacts.report);
    const options = {
      ...bundle,
      authority: f.wallet,
      issuer: f.issuer,
      passportBytes,
      reportBytes,
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
    const issued = await issueEnrolledPassport(options);
    f.artifacts.set("/passport.json", passportBytes);
    f.artifacts.set("/attestation.json", jsonBytes(issued.attestation));
    f.artifacts.set("/binding.json", jsonBytes(issued.binding));
    await appendStatus(f.statusRoot, issued.status);
    const decision = await evaluate({ ...f.options, now: new Date() });
    return { f, bundle, options, issued, decision, passportBytes, reportBytes };
  } catch (error) {
    await f.close();
    throw error;
  }
}

async function main() {
  const directory = resolve(process.argv[2] ?? "output/provider-preview");
  // All artifacts remain local; no fixture key is saved, and no RPC or payment is sent.
  await mkdir(directory, { mode: 0o700 });
  const run = await providerPreview();
  try {
    const files = {
      "participant.json": run.bundle.participantBytes,
      "enrollment.json": jsonBytes(run.bundle.enrollment),
      "registry-before.json": run.bundle.registryBytes,
      "passport.json": run.passportBytes,
      "report.json": run.reportBytes,
      "attestation.json": jsonBytes(run.issued.attestation),
      "binding.json": jsonBytes(run.issued.binding),
      "status.json": jsonBytes(run.issued.status),
      "registry-after.json": jsonBytes(run.issued.registry),
      "receipt.json": jsonBytes(run.issued.receipt),
      "decision.json": jsonBytes(run.decision),
    };
    for (const [name, bytes] of Object.entries(files))
      await writeFile(join(directory, name), bytes, {
        flag: "wx",
        mode: 0o600,
      });
    console.log(
      JSON.stringify(
        {
          output: directory,
          mode: run.decision.mode,
          action: run.decision.action,
          reasons: run.decision.reasons,
          payment_authorized: false,
          scope:
            "Synthetic evaluation and mocked registry; real signatures and private loopback retrieval. Not a registered-provider empirical demonstration.",
        },
        null,
        2,
      ),
    );
  } finally {
    await run.f.close();
  }
}
if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
