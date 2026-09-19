# Epistemic passport roadmap

## Product outcome

A human or an agent can complete the same underlying evaluation and receive a readable, machine-readable epistemic passport. A consumer can understand its measured tendencies, inspect supporting evidence and determine what assistance has been tested. Agent passports can be signed and associated with stable identity on Solana; human use can remain private.

The [passport brief](epistemic-passport.md) defines the intended dimensions and experience. The central acceptance question is: **does this profile help someone understand what to expect when delegating to this agent?** Measurement quality, auditability and identity binding make that profile dependable.

The [cognitive-security extension](cognitive-security.md) adds a second question: **can this profile help us choose support that improves the decision maker's performance?** The shared core now provides human and agent interfaces. Real participant completion, useful interpretation and support validation remain product checks.

The first usable milestone is concrete: **a human and a fresh agent complete the same battery through their respective interfaces and receive passports using the same dimensions and scoring definitions, with evaluation conditions visible.** This is an initial product demonstration, not evidence that the populations share norms or internal mechanisms.

## What exists today

| Component | Implemented capability | Remaining product work |
| --- | --- | --- |
| Passport foundation | Shared metadata, deterministic v1–v4 report import, HTML/Markdown/JSON profiles and exact-source verification | Real participant feedback, stronger interpretation and issuance. |
| Evaluation | Shared 34-checkpoint core through browser and MCP; original 88-trial, 54-checkpoint company and 10-checkpoint discovery protocols remain available | Measure core burden with real participants and add coverage beyond one discovery scenario. |
| Modeling | Prior/evidence fits, source inference, sequential comparisons and company decision/uncertainty probes | Map supported measurements to readable dimensions and explicit interpretation rules. |
| Validation tooling | Synthetic recovery and a matched discovery pipeline with frozen assignments, fresh-process collection, held-out predictions and uncertainty reports | Use this tooling internally to check released measures; establish real-agent repeatability for the core. |
| Session integrity | Shared transactional state, immutable answers, concurrent idempotent retries, resume and byte-stable completed artifacts | Hosted execution isolation and independently verified collection. |
| Signed records | Exact-byte report hashes, versioned envelopes and domain-separated Ed25519 signatures for v1–v3 evaluation reports | Add a passport artifact contract and signer/verifier support; study profiles are not currently accepted. |
| Solana | Memo construction, devnet simulation/submission and finalized inclusion verification | Stable identity association, artifact publication/retrieval, indexing and lifecycle handling. |

Legacy reports still require an `AgentDescriptor`, including model and configuration fields. The shared core adopts the participant/session boundary without changing those reports or their signed bytes. See [core 0.1 and passport 0.2](live-core.md), alongside the [legacy import contract](passport-v1.md).

Existing integration coverage includes real local MCP transport, Python-to-TypeScript schema validation, tamper checks and mocked RPC flows. It does not include live-chain or validator validation. Current demonstrations of the matched profile pipeline use synthetic policies; they are not issued profiles of real agents.

## Delivery sequence

| Milestone | Main deliverable | Completion criterion |
| --- | --- | --- |
| 1. Shared foundation and passport — implemented | Participant/session metadata contracts, profile schema and readable renderer | Existing agent artifacts produce an honestly scoped draft passport; the new contract represents humans without fabricated model metadata. |
| 2. One evaluation, two interfaces — implementation ready | Core 0.1: discovery 10 + calibration 24, browser/MCP adapters and automatic passports | Actual human and fresh-agent completion/review remain pending; synthetic service, HTTP, browser and MCP flows are checked. |
| 3. Dependable interpretation | Release checks, real-run feedback and explicit interpretation rules | Every published dimension has support for its stated scope, or is clearly provisional/insufficient. |
| 4. Identity and issuance | Signed passport, off-chain retrieval and Solana identity association | A consumer resolves an agent's passport and verifies issuer, configuration, artifact integrity and history. |
| 5. Tested support | One intervention comparison and a passport support section | The passport distinguishes a candidate support from its measured benefit, uncertainty, cost and regressions. |

Milestones 1–3 produce the local alpha. Record integration can proceed once the passport contract is stable; intervention experiments need the baseline workflow and scoring. Public efficacy claims and issuance depend on the relevant measurement checks. Timing and run budgets will be set from the first complete human and agent runs rather than assumed now.

## Milestone 1 — shared foundation and a readable passport

Implemented as [local draft passport 0.1](passport-v1.md). The human contract is available; live human collection is milestone 2. Only single completed v1–v3 reports are imported, with no cross-session aggregation or passport issuance.

Define a versioned participant contract with `human` and `agent` kinds, a common pseudonymous subject identifier, and kind-appropriate metadata. Agents record model/prompt/tool/runtime configuration; human sessions record relevant instructions, interface, tools and assistance without inventing model fields. Record protocol, conditions and evidence provenance for both. Preserve existing report versions and exact signed bytes through explicit adapters or migrations into new artifacts.

Define a versioned passport contract for subject/configuration, protocol, coverage, dimension measurements, interpretations, evidence references and provenance. Build a renderer whose plain-language summaries are traceable to explicit rules and observations. Give each dimension a coverage and evidence status; missing support must be visible.

Start from existing report artifacts to make the output concrete, labeling synthetic fixtures clearly. Keep performance, directional tendencies and variability separate. Do not introduce an overall score or unsupported population ranking.

Include an optional support section in the proposed contract. Separate model-suggested interventions from tested effects; neither may be represented as implemented or effective without supporting evidence.

Acceptance: the contract supports both participant kinds, and a reader can identify evaluation conditions, understand each supported tendency, inspect an example and find the limits of the claim without reading coefficient tables. A fixture-generated rendering is labeled as a draft or demonstration, not an issued real-participant result.

## Milestone 2 — one standard evaluation, two interfaces

The first implementation is [core 0.1](live-core.md). A new protocol freezes discovery-first order, shared plain-language instructions, no early outcomes and continuous context. It produces report.v4 and passport.v2. Synthetic recovery and adapter parity checks pass. This completes the initial software flow; the acceptance run below and broader matched contrasts remain outstanding.

Compose a bounded core from existing tasks and selected additions. Include both controlled and discovery conditions, with targeted repetitions and varied scenarios. Keep discovery central, retain calibration probes with explicit references, and use company assessment as a domain module. Set the final length using completion time and measurement coverage rather than concatenating every existing battery.

For each proposed dimension, specify the task contrast, fitted parameter or performance measure, readable interpretation, evidence requirement and possible support. Add matched contrasts where existing tasks cannot distinguish source impressions, evidence valence, updating and output effects. Do not represent all six dimensions as established simply because the renderer has six sections.

Expose a common session service with a human browser interface and MCP adapter. Both receive the same public task content, evidence order and response semantics for a given assignment. The browser provides instructions, practice, probability/interval/decision controls, progress and pause/resume. It receives no evaluator seeds, future evidence or answer keys. Record actual interface, timing, tools and assistance; preserve immutable answers and idempotent retries.

Freeze composition and interpretation together, review battery/evaluator versions, and run parameter-recovery checks for experimental changes. Version any substantive change to task content introduced for human usability. Common tasks and scoring do not imply identical context-reset or time-budget conditions; make those differences explicit.

Acceptance: a human and a fresh agent each complete the same battery through the shared engine and receive passports plus audit artifacts. Record all attempted modules and distinguish complete from partial runs. Replaying equivalent submitted answers through either adapter gives equivalent measurements, excluding transport metadata.

## Milestone 3 — make the interpretations dependable

Exercise the complete workflow with real humans and fresh agents, including repeat runs and wording variants. Collect whether the profile is understandable and useful, alongside completion, duration, cost and performance. Check model recovery and competing explanations with the existing synthetic tooling; use held-out observations where fitting or support selection requires them.

Publish a claim matrix connecting each dimension to its observed behavior, model assumptions and interpretation rules. Test that labels remain appropriately stable under irrelevant changes and respond to relevant behavioral differences. Record failures, refusals and incomplete runs. Human and agent interpretation thresholds require their own evidence; identical model parameters do not establish identical internal mechanisms or population percentiles.

Acceptance: every released statement is traceable to evidence at its stated scope, and repeatability or sensitivity concerns are visible. A usable alpha may contain provisional dimensions. Broad trait claims require broader support; the larger matched-study tooling remains an internal development option.

## Milestone 4 — issue and verify the passport

Extend the signed-artifact contract and verifier to bind the passport, evaluated configuration, protocol and evidence digests. Preserve exact-byte hashing and versioned signature domains. Publish readable and machine-readable artifacts with an explicit evidence-access policy, then anchor and retrieve them through the Solana integration.

Implement an identity association that keeps stable subject identity, controller authorization, evaluator issuance and execution verification distinct. Select existing primitives or a custom registry against the lifecycle requirements in [identity and records](identity-and-records.md). A configuration change creates a new evaluation scope; corrections and withdrawals preserve historical records.

Acceptance: a consumer can resolve an agent's passport, verify the issuer and artifact bytes, recognize its configuration and age, and inspect the claimed execution-verification level. Validate chain behavior on a local validator or devnet and report that coverage separately from mocked tests.

## Milestone 5 — test targeted cognitive support

Start with one intervention: an evidence ledger and explicit reassessment step for a participant showing weak integration of independent evidence. Treat the proposed mechanism and benefit as hypotheses. Compare baseline, generic review and targeted support on fresh matched cases containing weak, strong and duplicated evidence.

Measure forecasting or decision performance against declared objectives, together with cost and deterioration in other conditions. Keep intervention selection separate from its held-out evaluation. Record agent prompt/tool changes as assisted configurations; account for human learning and carryover instead of assuming memory can be reset.

Acceptance: the passport shows what was tried, the comparison conditions, measured effect and uncertainty, cost, limits and any regressions. A null or harmful result is still a valid completed comparison. Intervention success requires performance evidence; changing a fitted parameter alone is insufficient. See [cognitive security](cognitive-security.md).

## After the first complete product

Add a comparison view for compatible passports, showing changes in measured behavior alongside configuration/protocol differences and uncertainty. Add further domain modules and budgeted information seeking when their measures support useful interpretations. Keep independent evaluator records visible rather than allowing a subject to rewrite its history.

Acceptance: consumers can compare like conditions, identify unmeasured dimensions and inspect evidence behind differences. Reputation aggregation and marketplace ranking remain separate product choices.

## Scope boundaries

- A passport describes demonstrated behavior under declared conditions; it does not certify all future behavior or expose internal beliefs.
- The current local MCP service requires evaluator/subject isolation supplied by the deployment. It is not a hosted multi-tenant service.
- Current model/configuration metadata is operator-asserted. Signing and anchoring do not upgrade execution verification.
- Public identity records need not expose private prompts or transcripts. Evidence access and artifact availability are explicit product concerns.
- A unified passport command, contract, renderer and identity registry are planned work, not current CLI features.

## Immediate build

Milestone 1 is implemented and tested. Next, choose the bounded core composition, wire the shared participant/session boundary into the evaluator service, and expose it through MCP and a minimal human interface. Preserve existing report/CLI behavior. The next combined demo should be the complete human/agent-to-passport flow.
