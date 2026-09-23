# Investigation evidence in a passport

Implemented 23 September 2026. Completed investigation 0.2 and 0.3 collections now produce a deterministic, evidence-linked `passport.v3` in JSON, Markdown and HTML. The TypeScript attestation and machine consumer support this contract alongside the existing core passport. This completes the local path from investigation responses to an inspectable machine policy decision. Public hosting, registered-provider execution and payments remain separate roadmap items.

## Source and interpretation

`epistemics.investigation-collection.v1` embeds all 12 original report files as exact UTF-8 strings with SHA-256 digests. The adapter checks the common manifest, ordered assignments, public trials reconstructed from the frozen world, accepted response shape, rounding and chronology. It recomputes behavioral facts rather than trusting an imported `analysis` field. Original reports and their byte hashes are unchanged.

`passport/0.3.0` and `passport-interpretation/0.3.0` bind the collection's exact bytes. The profile records 12 cases, 48 checkpoints, 198 probability reports, nine unique worlds, the evaluated subject/configuration, discovery or calibration mode, and the manifest's declared context policy. Actual interface provenance is `unspecified`: the old manifest does not independently attest whether responses arrived over browser or MCP. Subject kind cannot establish transport or verified execution.

The readable and machine views distinguish three things:

- Observed behavior: decision/report agreement, prospective forecast coherence, research choice agreement with coherent stated values, response to actual corrections, resolved-event retention and source-report persistence.
- Coverage: counts of relevant cases/checks beside the percentages, including the number of coherent research cases used in policy agreement. Missing denominators produce missing metrics, not perfect scores.
- Model diagnostics: initialization, source-feedback coupling, response rate, conditional uncertainty and error. These are inspectable alternative explanations, not consumer traits.

The six familiar dimension headings remain, but evidence weighting and general dependence/causal reasoning are explicitly insufficiently covered. No global cognitive score, stable personality label or automatic intervention recommendation is generated. Research coherence is not outcome calibration, source persistence is not automatically a defect, and correction-direction agreement is not a measure of the optimal update magnitude.

The diagnostic contract fixes `parameters_are_validated_traits`, `empirical_predictive_validation` and `intervention_benefit_tested` to false. A passport made from 0.2 reports retains the 0.2 hard-start analysis. [0.3 reanalysis](company-investigation-v3.md#exploratory-reanalysis-of-the-existing-agent-run) is a separate, explicitly post-hoc artifact; it never retroactively changes the evaluated protocol.

## Machine consumption and signatures

The catalog adds 14 `investigation.*.v1` identifiers to the eight existing core identifiers: eight observations and six coverage counts. Mappings bind interpretation version, dimension, exact evidence pointer and units. Source-feedback and response-rate coefficients have no consumer metric IDs. Policies should require relevant coverage as well as a percentage.

The current investigation catalog qualifies **discovery** observations only. Calibration passports remain renderable/signable but require review in the consumer until a policy contract explicitly distinguishes that scope. Synthetic responses remain ineligible. Requests for verified execution or validated predictive usefulness require review. Provisional acceptance is an explicit policy choice; it does not make a threshold empirically validated.

The existing `passport-attestation.v1` canonical payload and `epistemics/passport-attestation-signature/v1` domain remain unchanged. They already bind the passport's exact bytes, source hash, subject, configuration and protocol/interpretation versions. Old passport contracts and legacy report signatures are unchanged. A verifier must support passport.v3 to accept the new evidence contract.

Python `passport verify` recomputes derivation. The TypeScript signer checks schemas, exact artifact hashes, embedded report hashes, common subject/configuration/protocol/mode bindings and chronology; it does **not** rerun scientific inference or recompute all metrics. Issuers should run Python verification before signing. A consumer trusts its independently configured issuer for the interpretation, checks signature/status/identity and applies its own policy. None of those steps proves which model executed the evaluation.

Source collections contain evaluator-side worlds and response records. Keep them private; the public passport is a summary with evidence references, and authorized auditors can retrieve the bound source separately. No raw collection is committed to this repository. Human passports remain private and the agent attestation tool continues to reject human issuance.

## Run locally

```sh
uv run epistemics passport bundle-investigation \
  --directory output/investigation3/collection --output output/investigation3/source.json
uv run epistemics passport create \
  --report output/investigation3/source.json --output output/investigation3/passport
uv run epistemics passport verify output/investigation3/passport/passport.json \
  --report output/investigation3/source.json
pnpm passport-record demo \
  --passport output/investigation3/passport/passport.json \
  --report output/investigation3/source.json --output output/investigation3/attestation.json
pnpm consumer metrics
```

The demo signs with a discarded ephemeral key and does not publish or submit a transaction. For production issuance, use the [attestation workflow](passport-attestation.md) and establish the [provider/controller association](machine-consumer.md). Outputs refuse overwrite.

## Completed checks and existing-agent result

The complete Python suite passed 248 tests, including actual stdio MCP transport, local browser HTTP collection and deterministic passport derivation. The TypeScript suite passed 35 tests, including signatures, tampering, status, policy decisions and the investigation adapter. The consumer integration uses real local HTTP and **mocked Solana RPC**. No validator or funded network transaction was tested in this increment. A complete synthetic 0.3 collection was exported, bundled, rendered, verified and signed offline. Visual browser inspection was unavailable because the host was locked; automated browser-flow checks passed.

The unchanged 21 September agent run now has a passport. Its source collection hash is `98a0d7c541c1cca4d8a1adc72b010e01e8bf4a7ac57c8dba4999ef43e9c112c4`. Observations include 48/48 decision/report agreements, 6/6 coherent prospective research sets, 6/6 coherent research choices maximizing reported value, 4/4 corrections in the expected direction, and 4/4 resolved-event checks retained. Source reports remained unchanged from background to evidence in 12/12 cases. These are descriptions of this one run, not a new validation result.

## Next evidence milestone

Prepare a small, costed acceptance and repeatability run before attempting another large benchmark:

1. Freeze the 0.3 protocol fingerprint, participant configuration, delivery prompt, case schedule, baselines and loss functions before collecting new responses. Calibrate an adequacy diagnostic using predictive distributions; the legacy eight-point RMSE screen alone is insufficient for the noisy-start model.
2. Use one configuration for 12 development cases, then lock its fits. Repeat those 12 cases in new contexts and evaluate 12 newly generated cases. This proposed 36-episode pilot separates same-case repeatability from new-case prediction; it cannot establish improvement over population pooling with only one configuration.
3. Precompute each possible branch's predictions from the public sequence and initial answers before scoring later reports. Compare all three initializations, fixed joint/cut observers and report persistence. Report RMSE and predictive log score separately. Keep matched price pairs together and show per-case errors; do not treat 198 reports as 198 independent tasks.
4. Use an initial 45-minute agent collection budget, based on the previous roughly nine-minute 12-case acceptance. Record model usage, retries and failures. If interrupted, preserve accepted answers and label the run incomplete; do not omit difficult cases. This is a proposed cap, not a measured provider cost or a launched job.
5. Have an actual human complete the same 12-case browser form and review instructions, burden and interpretation. Automated or synthetic completions cannot satisfy this acceptance item.

This pilot informs the next release gate; it is not the finalized statistical benchmark or permission to claim individualized predictive superiority. Only after its design is frozen and its results reviewed should collection expand across configurations or test targeted support. In parallel, connect an explicitly identified provider to the existing consumer with authorized artifacts and simulated purchase reasons. Hosted jobs and x402 settlement follow as the commercial increment.
