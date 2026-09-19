# Epistemic passport roadmap

## Product outcome

An agent or orchestrator can discover another agent, inspect a portable cognitive profile, verify its provenance and evaluated configuration, and decide whether and how to delegate or purchase a service. The same profile is readable by a person; the same underlying evaluation supports private human participation.

The primary distribution path is the **agent economy**. [Agent Registry identity, machine consumption and x402 commerce](agent-economy.md) are core product work. Our initial revenue hypothesis is paid evaluation/re-evaluation, followed by fleet monitoring and managed policy services. We do not automatically receive a fee from transactions involving a passport.

The [product brief](epistemic-passport.md) defines the intended dimensions. The acceptance question is: **does the profile improve a concrete delegation decision?** The [cognitive-security extension](cognitive-security.md) adds: **can it identify assistance that improves performance?** Both require task-conditional evidence, rather than an overall reputation score.

## Current position

| Component | Working now | Still needed |
| --- | --- | --- |
| Evaluation | Shared 34-checkpoint core: discovery 10 + calibration 24, human browser and agent MCP | Actual human and fresh-agent completion/review of this combined core, repeatability and cost measurements |
| Profile | Deterministic HTML/Markdown/JSON; six dimensions; source references and explicit provisional/insufficient coverage | Broader scenarios and contrasts; stable metric identifiers for consumer policies |
| Collection | Transactional state, immutable answers, idempotent retry/resume, private evaluator state, byte-stable completion | Hosted tenant boundaries and evaluator/subject execution isolation |
| Validation | Synthetic recovery; matched discovery assignments, fresh-process collection and held-out prediction tooling | Real-agent evidence for intended product claims and task selection utility |
| Passport signature | Offline passport-attestation.v1 for agent core passport.v2; exact-byte hashes, explicit issuer, validity window and machine verification output | Registry association, availability, withdrawal/correction status and policy decisions |
| Legacy Solana records | v1–v3 report signatures, devnet Memo construction/simulation/submission and finalized inclusion verifier | Validator/live-network validation; current RPC integration coverage is mocked |
| Commerce | Source-reviewed integration and commercial design | x402 gateway, durable payment/job ledger, pricing evidence and paying pilot |

The implementation remains a local alpha. Synthetic service, HTTP, browser and MCP demonstrations are completed. Earlier fresh agents ran predecessor batteries; that does not satisfy the combined core's real-participant acceptance check. No paid endpoint, registry adapter or public artifact hosting is live.

## Delivery order

| Stage | Deliverable | Completion criterion |
| --- | --- | --- |
| 1. Shared evaluation and profile — software ready | Human/MCP collection and one interpretable draft artifact | Actual human and fresh agent finish and review the core; record time, failures and usefulness |
| 2. Machine-consumable passport — started | Detached signature, versioned measurements, identity resolution, status and task policy | A buyer resolves an existing agent and gets a reproducible decision with reasons before any payment |
| 3. Paid evaluation service | x402 purchase of one bounded, resumable evaluation job | Repeated/concurrent requests create one job and one entitlement; all settlement ambiguity is reconciled; result can be verified |
| 4. Useful selection and support | Broader evidence, repeatability, comparisons and one targeted intervention | Profiles inform a bounded delegation choice; intervention effect includes uncertainty, cost and regressions |
| 5. Distribution and recurring value | Marketplace/router adapter, fleet refresh and managed policy API | A customer uses the integration repeatedly and pays for a measurable benefit |

Measurement work continues alongside stages 2–3. Signature infrastructure can ship with honest provisional evidence; autonomous policy thresholds and efficacy claims need their own validation. We will not delay all interoperability until every trait is established, or silently promote current observations into general competence guarantees.

## Next build: resolve, verify, decide

The [offline attestation increment](passport-attestation.md) is implemented and tested without changing task behavior, report schemas or legacy signed bytes. Next:

1. Pin and verify a specific 8004-Solana deployment and SDK/IDL. Resolve chain/program/asset, current authority, operational wallet, endpoint and passport reference. Use an adapter; build a new identity program only for a concrete unmet requirement.
2. Add artifact hosting/retrieval and issuer status history with explicit access rules. Keep report evidence private unless publication is authorized. Check digest, issuer trust, current configuration, evaluation age, expiry and corrections/withdrawals separately.
3. Add stable measurement identifiers and a versioned consumer policy/result contract. Missing evidence returns review, not an assumed pass. Bind every decision to the task, passport digest, policy and maximum spend.
4. Demonstrate provider selection before a simulated x402 request. Reject stale configuration, wrong subject/payee, untrusted issuer, synthetic origin, unavailable required status and unsupported task coverage.

Acceptance is one complete machine-consumer flow with explicit provenance and policy reasons. Offline tests, mocked RPC, actual registry reads and funded devnet transactions must be reported separately. A signature does not prove which model ran, and a registry identity does not certify cognitive quality.

## Then: charge for a bounded evaluation job

Build a payment gateway around the evaluator, not a fee on each trial or poll. A quote states scope, budget, inference responsibility and failure policy. A settled payment creates one resumable job; entitlement controls subsequent access. Distinguish payer, evaluated subject, issuer and provider.

Use x402 v2 and an SVM-capable facilitator. Keep a durable job/payment state machine, request fingerprints and recovery across crashes. Verify and settle are different steps. Test duplicate settlement, cross-order replay, concurrent retries, body changes, timeout after possible settlement and access to private results. Choose actual prices after measuring costs and customer demand. The [commerce design](agent-economy.md#paid-evaluation-api--proposed-next-slice) defines the integration boundaries.

## Measurement and support track

Run the combined core with a real human and fresh agents, then repeat selected configurations. Record completion, duration, inference cost and whether the profile helps explain the observed behavior. The current single discovery company cannot establish broad source-framing or negativity traits.

Add matched contrasts separating source label from track record, negative wording from diagnosticity, copied from independent evidence, and source distrust from causal-model revision. For every released claim, connect observed behavior, assumptions, uncertainty and interpretation rules. Review battery/evaluator versions and run recovery validation when experimental behavior changes. Common human/agent tasks do not imply common population norms or internal mechanisms.

For one support comparison, test an evidence ledger and reassessment against baseline and generic review on fresh matched cases. Track performance, cost and regressions; a changed fitted parameter alone is not an improvement. Bind assisted configurations and retain null or harmful results. Detailed vulnerability information can require controlled access.

## Release boundaries

- Reported probabilities are observations, not access to internal beliefs. Every passport stays conditional on its task, configuration and conditions.
- Current execution metadata is operator-asserted. Issuer, controller, configuration and execution verification remain distinct.
- Browser/MCP evaluation, draft rendering and offline signatures are implemented. Public hosting, lifecycle status, registry binding and payments are not.
- Human use remains private by default and does not require a wallet. Identity-linked publication is a separate choice.
- Legacy report.v1–v3 record signing and Memo semantics remain unchanged. New passport signatures have a separate schema and signature domain.
