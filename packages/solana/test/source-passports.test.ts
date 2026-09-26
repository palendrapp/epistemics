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
from epistemics.source_delivery.simulation import simulate
from epistemics.passport.source_learning import bundle
from epistemics.passport.build import build_passport
from epistemics.source_learning.storage import encoded
with TemporaryDirectory() as tmp:
    d=Path(tmp)/'run'
    simulate(d,31)
    raw=encoded(bundle([d]))
    p=build_passport(raw)
    print(json.dumps({'report':json.loads(raw),'passport':p.model_dump(mode='json')}))
`,
    ],
    { cwd: root, maxBuffer: 8 * 1024 * 1024 },
  ).toString(),
);

test("source passport preserves hashes, absent repeat evidence and unvalidated interpretation", async () => {
  const report = jsonBytes(sample.report),
    p = structuredClone(sample.passport);
  p.source.sha256 = sha256(report);
  const bytes = jsonBytes(p),
    signer = await generateKeyPairSigner();
  const options = {
    passportUri: "https://example.invalid/source.json",
    expiresAt: new Date(Date.now() + 3600000).toISOString(),
  };
  const signed = await createPassportAttestation(
    bytes,
    report,
    signer,
    options,
  );
  await verifyPassportAttestation(signed, bytes, {
    expectedIssuer: signer.address,
    reportBytes: report,
  });
  const metrics = measurements(p);
  assert(
    metrics.some(
      (m) => m.metric_id === "source.coverage.sessions.v1" && m.value === 1,
    ),
  );
  assert(
    metrics.some(
      (m) => m.metric_id === "source.decision_agreement.v1" && m.value === 100,
    ),
  );
  assert(!metrics.some((m) => m.metric_id === "source.repeat_rmse.v1"));
  assert(!metrics.some((m) => /gain|family|adequacy/.test(m.metric_id)));
  for (const field of [
    "parameters_are_validated_traits",
    "personalized_prediction_validated",
    "intervention_benefit_tested",
  ]) {
    const bad = structuredClone(p);
    bad.model_diagnostics[field] = true;
    await assert.rejects(
      createPassportAttestation(jsonBytes(bad), report, signer, options),
    );
  }
  for (const field of ["report_json", "transport_json"]) {
    const bad = structuredClone(sample.report);
    bad.sessions[0][field] += " ";
    const b = jsonBytes(bad),
      passport = structuredClone(p);
    passport.source.sha256 = sha256(b);
    await assert.rejects(
      createPassportAttestation(jsonBytes(passport), b, signer, options),
      /hash/,
    );
  }
  const bad = structuredClone(sample.report);
  const child = JSON.parse(bad.sessions[0].report_json);
  child.manifest.participant.subject_id = "another-agent";
  bad.sessions[0].report_json = JSON.stringify(child);
  bad.sessions[0].report_sha256 = sha256(bad.sessions[0].report_json);
  const b = jsonBytes(bad),
    passport = structuredClone(p);
  passport.source.sha256 = sha256(b);
  await assert.rejects(
    createPassportAttestation(jsonBytes(passport), b, signer, options),
    /binding/,
  );
});

test("cohort identity and unqualified source conditions cannot silently become machine eligibility", async () => {
  const signer = await generateKeyPairSigner();
  const p = structuredClone(sample.passport);
  p.subject_binding = "configuration_cohort";
  p.source_subject_ids = ["first", "second"];
  await assert.rejects(
    createPassportAttestation(jsonBytes(p), jsonBytes(sample.report), signer, {
      passportUri: "https://example.invalid/p",
      expiresAt: new Date(Date.now() + 3600000).toISOString(),
    }),
    /cohort/,
  );
  for (const change of [
    { presentation: "packet" },
    { presentation: "unverified" },
    { condition: "dense" },
    { subject_binding: "configuration_cohort" },
  ])
    assert.throws(
      () => measurements({ ...sample.passport, ...change }),
      /single-subject sparse structured/,
    );
});

test("source facts pass through mocked identity and policy, with missing repeatability requiring review", async () => {
  const f = await fixture("agent", sample);
  try {
    f.policy.measurements = [
      {
        metric_id: "source.decision_agreement.v1",
        minimum: 99,
        maximum: 100,
        uncertainty: "point",
      },
      {
        metric_id: "source.coverage.checkpoints.v1",
        minimum: 36,
        maximum: 36,
        uncertainty: "point",
      },
    ];
    const options = { ...f.options, policyBytes: jsonBytes(f.policy) };
    const result = await evaluate(options);
    assert.equal(result.action, "eligible", JSON.stringify(result.reasons));
    assert.equal(result.mode, "simulation");
    assert.equal(result.payment_authorized, false);
    const repeat = {
      ...f.policy,
      measurements: [
        {
          metric_id: "source.repeat_rmse.v1",
          minimum: 0,
          maximum: 5,
          uncertainty: "point",
        },
      ],
    };
    assert.equal(
      (await evaluate({ ...options, policyBytes: jsonBytes(repeat) })).action,
      "review_required",
    );
    assert.equal(
      (
        await evaluate({
          ...options,
          policyBytes: jsonBytes({
            ...f.policy,
            require_predictive_validation: true,
          }),
        })
      ).action,
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
