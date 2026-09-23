import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { generateKeyPairSigner } from "@solana/kit";
import { evaluate } from "../src/consumer/evaluate.js";
import { measurements } from "../src/consumer/metrics.js";
import {
  createPassportAttestation,
  verifyPassportAttestation,
} from "../src/passports.js";
import { sha256 } from "../src/records.js";
import { fixture, jsonBytes } from "./consumer-fixture.js";

const root = fileURLToPath(new URL("../../../", import.meta.url));
const sample = JSON.parse(
  execFileSync(
    join(root, ".venv/bin/python"),
    [
      "-c",
      `
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from epistemics.investigation3.cli import demo
from epistemics.passport.investigation import bundle
from epistemics.investigation2.service import encoded
from epistemics.passport.build import build_passport
with TemporaryDirectory() as tmp:
    directory=Path(tmp)/'collection'
    demo(directory,23)
    from epistemics.investigation3.service import export
    export(directory)
    raw=encoded(bundle(directory))
    passport=build_passport(raw)
    print(json.dumps({'report':json.loads(raw),'passport':passport.model_dump(mode='json')}))
`,
    ],
    { cwd: root, maxBuffer: 8 * 1024 * 1024 },
  ).toString(),
);

test("investigation passport signs, verifies and exposes scoped facts and denominators", async () => {
  const report = jsonBytes(sample.report),
    passport = jsonBytes({
      ...sample.passport,
      source: { ...sample.passport.source, sha256: sha256(report) },
    });
  const signer = await generateKeyPairSigner();
  const signed = await createPassportAttestation(passport, report, signer, {
    passportUri: "https://example.invalid/investigation.json",
    expiresAt: new Date(Date.now() + 3600000).toISOString(),
  });
  await verifyPassportAttestation(signed, passport, {
    expectedIssuer: signer.address,
    reportBytes: report,
  });
  assert.equal(signed.payload.response_origin, "synthetic");
  const metrics = measurements(sample.passport);
  assert(
    metrics.some(
      (m) =>
        m.metric_id === "investigation.decision_agreement.v1" &&
        m.value === 100,
    ),
  );
  assert(
    metrics.some(
      (m) =>
        m.metric_id === "investigation.coverage.decisions.v1" && m.value === 48,
    ),
  );
  assert(!metrics.some((m) => /coupling|response_rate/.test(m.metric_id)));
  assert.throws(
    () => measurements({ ...sample.passport, evaluation_mode: "calibration" }),
    /discovery mode only/,
  );
  await assert.rejects(
    verifyPassportAttestation(
      signed,
      Buffer.concat([passport, Buffer.from(" ")]),
      { expectedIssuer: signer.address },
    ),
    /hash/,
  );
  for (const field of [
    "parameters_are_validated_traits",
    "empirical_predictive_validation",
    "intervention_benefit_tested",
  ]) {
    const invalid = structuredClone(sample.passport);
    invalid.model_diagnostics[field] = true;
    await assert.rejects(
      createPassportAttestation(jsonBytes(invalid), report, signer, {
        passportUri: "https://example.invalid/p",
        expiresAt: new Date(Date.now() + 3600000).toISOString(),
      }),
    );
  }
  const bad = structuredClone(sample.report);
  bad.cases[0].report_json += " ";
  const b = jsonBytes(bad),
    p = structuredClone(sample.passport);
  p.source.sha256 = sha256(b);
  await assert.rejects(
    createPassportAttestation(jsonBytes(p), b, signer, {
      passportUri: "https://example.invalid/p",
      expiresAt: new Date(Date.now() + 3600000).toISOString(),
    }),
    /Embedded report hash/,
  );
});

test("investigation facts flow through identity, status and policy in mocked RPC; no payment", async () => {
  const f = await fixture("agent", sample);
  try {
    f.policy.measurements = [
      {
        metric_id: "investigation.decision_agreement.v1",
        minimum: 99,
        maximum: 100,
        uncertainty: "point",
      },
      {
        metric_id: "investigation.coverage.decisions.v1",
        minimum: 48,
        maximum: 48,
        uncertainty: "point",
      },
    ];
    const options = { ...f.options, policyBytes: jsonBytes(f.policy) };
    const result = await evaluate(options);
    assert.equal(result.action, "eligible", JSON.stringify(result.reasons));
    assert.equal(result.mode, "simulation");
    assert.equal(result.payment_authorized, false);
    const strict = { ...f.policy, require_predictive_validation: true };
    assert.equal(
      (await evaluate({ ...options, policyBytes: jsonBytes(strict) })).action,
      "review_required",
    );
    const missing = {
      ...f.policy,
      measurements: [
        {
          ...f.policy.measurements[0]!,
          metric_id: "investigation.coupling.v1",
        },
      ],
    };
    assert.equal(
      (await evaluate({ ...options, policyBytes: jsonBytes(missing) })).action,
      "review_required",
    );
  } finally {
    await f.close();
  }
  const synthetic = await fixture("synthetic", sample);
  try {
    assert.equal((await evaluate(synthetic.options)).action, "ineligible");
  } finally {
    await synthetic.close();
  }
});
