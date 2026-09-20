# Epistemic passport roadmap

## Product outcome

Build infrastructure for measuring and coordinating epistemic reliability: how humans and agents acquire information, judge evidence, revise conclusions, express uncertainty and act. The passport is the first portable product of that measurement layer. Its value is whether the measured profile helps predict behavior and improve a concrete decision about delegation, verification or assistance.

An agent or orchestrator can discover another agent, inspect that profile, verify its provenance and evaluated configuration, and decide whether and how to delegate or purchase a service. The same profile is readable by a person; the same underlying evaluation supports private human participation.

The primary distribution path is the **agent economy**. [Agent Registry identity, machine consumption and x402 commerce](agent-economy.md) are core product work. Our initial revenue hypothesis is paid evaluation/re-evaluation, followed by fleet monitoring and managed policy services. A later contribution network could pay humans and agents for verified testing, expert judgment and reproducible failures. We do not automatically receive a fee from transactions involving a passport.

The [product brief](epistemic-passport.md) defines the intended dimensions. The near-term acceptance questions are: **does the profile predict behavior on unseen cases, and does using it improve a delegation or assistance decision at an acceptable cost?** The [cognitive-security extension](cognitive-security.md) supplies the intervention comparison. Predictive validation is internal product release work; the customer receives a bounded evaluation and an interpretable result. The broader ambition includes continuous observation, team composition and economic allocation, with separate evidence requirements for each.

## Current position

| Component | Working now | Still needed |
| --- | --- | --- |
| Evaluation | Shared 34-checkpoint core: discovery 10 + calibration 24, human browser and agent MCP; one fresh-agent acceptance with cost/timing and usability feedback | Actual human completion/review, agent repeatability and version-reviewed usability fixes |
| Profile | Deterministic HTML/Markdown/JSON; six dimensions; source references, provisional/insufficient coverage and a versioned eight-metric consumer catalog | Broader scenarios/contrasts and validated task-policy thresholds |
| Collection | Transactional state, immutable answers, idempotent retry/resume, private evaluator state, byte-stable completion | Hosted tenant boundaries and evaluator/subject execution isolation |
| Validation | Synthetic recovery; matched discovery assignments, fresh-process collection and held-out prediction tooling | Real-agent evidence for intended product claims and task selection utility |
| Predictive usefulness | Provenance pilot plus multi-configuration benchmark: resource accounting, frozen fits/predictions, stage gates, baseline comparisons, uncertainty and source-inference sensitivity | Complete empirical prediction beyond simple baselines and a demonstrated support-selection benefit |
| Passport signature and consumer | Offline attestations plus pinned devnet identity reads, provider/controller bindings, signed withdrawal/correction history, private retrieval and task decisions | Controlled registered-provider demonstration, public availability, tenant isolation and outcome-validated policies |
| Legacy Solana records | v1–v3 report signatures, devnet Memo construction/simulation/submission and finalized inclusion verifier | Validator/live-network validation; current RPC integration coverage is mocked |
| Commerce | Source-reviewed integration and commercial design | x402 gateway, durable payment/job ledger, pricing evidence and paying pilot |

The implementation remains a local alpha. Synthetic service, HTTP, browser, MCP and consumer demonstrations are completed. A [fresh Astra agent completed all 34 combined-core checkpoints](core-acceptance-2026-09-20.md); an actual human completion is still needed. The [consumer adapter](machine-consumer.md) also resolved a public devnet identity using live reads. No paid endpoint or public artifact hosting is live, and no registry write or payment has been made.

## Delivery order

| Stage | Deliverable | Completion criterion |
| --- | --- | --- |
| 1. Predictive usefulness — next measurement milestone | Real core acceptance runs, matched cases, held-out behavior predictions and one profile-guided support decision | Predict duplicated-evidence behavior beyond simple baselines; evaluate whether using the profile improves fresh decisions after accounting for cost |
| 2. Machine-consumable passport — parallel integration milestone | Detached signature, versioned measurements, identity resolution, status and task policy | A buyer resolves an existing agent and gets a reproducible decision with reasons before any payment; empirical recommendations cite their validation scope |
| 3. Paid evaluation service and first customer | x402 purchase of one bounded, resumable evaluation job | One job/entitlement across retries, reconciled settlement, verifiable delivery, measured cost and evidence of customer value |
| 4. Broader epistemic policies and observation | Active information acquisition, retraction/noise contrasts, repeated and prospective observation; historical replay pilot | Predict specified search/update/stopping behavior and characterize drift on new cases, with contamination and selection limits visible |
| 5. Coordination and recurring value | Fleet refresh, managed policy API, reviewer/team selection and scoped permission recommendations | Profile-guided allocation improves outcomes versus simple alternatives; joint failure rates and costs are measured |
| 6. Paid contribution network | Verified experiments, expert judgments, provenance work and red-team bounties | Contributions are independently checkable, compensation is reliable, and their value exceeds collection, verification and dispute costs |

Stages 1 and 2 proceed together. The shared core's human usability check remains an immediate acceptance task; the first fresh-agent run is complete. Stage 3 can sell accurately scoped evaluations with provisional findings; claims that a profile predicts failures or improves selection require the relevant stage 1 evidence. Later stages extend measured task coverage and coordination only after their own checks. A signed profile alone does not establish predictive usefulness or justify increased authority.

## Next demonstration: predict a failure and use the prediction

The [predictive-usefulness pilot](predictive-usefulness-pilot.md) is the next bounded measurement deliverable. The case generator, synthetic checks, [sequential MCP collection](provenance-collection.md) and [frozen prediction benchmark](prediction-benchmark.md) are implemented. A [six-episode development run](prediction-budget-2026-09-20.md) measured costs and froze a 432-episode comparison across three configurations, with two repetitions, declared baselines and empirical targets. The [profile stage is now complete](prediction-profile-2026-09-20.md): 144 episodes / 576 responses, with fitted profiles and held-out predictions locked before any later-case exposure. A [bounded-recovery amendment](benchmark-recovery.md) preserved the original stopped run and recovered one Terra episode without changing accepted answers; its earlier usage remains unknown. Luna's lower fitted prior weight is a descriptive task-conditional result, not yet evidence of predictive usefulness. Next collect the frozen policy and held-out partitions, then score the locked predictions against every declared baseline, including null results. After that, use frozen profiles to select an evidence ledger or independent review, and test whether that choice improves decisions relative to cost.

Keep profile estimation, policy development and final evaluation cases separate. Compare individualized predictions with pooled behavior, persistence and simple calibration/performance summaries. Compare profile-guided assistance with no assistance, generic review and an untailored assistance policy under declared budgets. Test favorable and unfavorable evidence, including cases where little updating is appropriate. Report predictive performance separately from forecasting/decision quality.

The pilot is complete when the planned comparisons, uncertainty, cost, failures and limits are reported. Product success requires the predeclared predictive and practical benefit criteria to be met; a null or harmful result must narrow the claim or trigger revision. No current passport should be relabeled as a validated general phenotype. The empirical comparisons remain pending; the implemented pilot and collector do not change core 0.1.

## Parallel build: resolve, verify, decide

The [local machine-consumer increment](machine-consumer.md) is implemented without changing task behavior, report schemas or legacy signed bytes. It pins the reviewed SDK/IDL and observed devnet deployment, resolves current authority, checks signed provider/configuration/payee bindings and issuer status, retrieves private artifacts and evaluates a versioned task policy over stable metric IDs. A live registry read passed; the complete consumer flow uses synthetic identities and mocked RPC with real private HTTP.

Next complete a controlled registered-provider demonstration: collect under its canonical chain/program/asset subject ID, establish the issuer's evaluated-controller binding, publish only authorized artifacts, resolve them through the registry and prepare a simulated bounded service purchase. Then add hosted availability/tenant boundaries and the payment adapter. Current recommendations remain unsigned local results; rechecking immediately before purchase and authorizing/settling payment are separate operations.

Acceptance is one complete machine-consumer flow with explicit provenance and policy reasons. Offline tests, mocked RPC, actual registry reads and funded devnet transactions must be reported separately. A signature does not prove which model ran, and a registry identity does not certify cognitive quality.

## Then: charge for a bounded evaluation job

Build a payment gateway around the evaluator, not a fee on each trial or poll. A quote states scope, budget, inference responsibility and failure policy. A settled payment creates one resumable job; entitlement controls subsequent access. Distinguish payer, evaluated subject, issuer and provider.

Use x402 v2 and an SVM-capable facilitator. Keep a durable job/payment state machine, request fingerprints and recovery across crashes. Verify and settle are different steps. Test duplicate settlement, cross-order replay, concurrent retries, body changes, timeout after possible settlement and access to private results. Choose actual prices after measuring costs and customer demand. The [commerce design](agent-economy.md#paid-evaluation-api--proposed-next-slice) defines the integration boundaries.

## Broader measurement and observation

Run the combined core with a real human and fresh agents, then repeat selected configurations. Record completion, duration, inference cost and whether the profile helps explain the observed behavior. The current single discovery company cannot establish broad source-framing or negativity traits.

Add matched contrasts separating source label from track record, negative wording from diagnosticity, copied from independent evidence, and source distrust from causal-model revision. For every released claim, connect observed behavior, assumptions, uncertainty and interpretation rules. Review battery/evaluator versions and run recovery validation when experimental behavior changes. Common human/agent tasks do not imply common population norms or internal mechanisms.

After the bounded pilot, add **active information acquisition**: participants choose documents, sources, hypothesis-discriminating queries and whether to stop under explicit costs. Measure what they acquire, forego and act on. Hypothesis-generation breadth needs a scored observable task; verbal explanations alone do not establish an internal search process. Version these additions separately from passive evidence presentation.

Add **continuous observation** through authorized decision histories: record information available at decision time, forecasts, confidence, stated invalidation conditions, action and later resolution. Start with prospective collection and distinguish genuine drift from changes in task mix, selection and configuration. Production observation and repeated controlled tests supply different evidence.

Pilot **historical point-in-time replay** only with availability timestamps, document versions, provenance and explicit leakage checks. Restricting supplied documents does not remove outcomes already known through model training or human memory. Flag familiar events, use concealed or prospective outcomes where possible, and report the remaining contamination uncertainty. Historical returns alone do not identify reasoning quality.

These additions require dedicated task/data design; none is currently implemented as a released passport capability. Predictive success supports the stated behavioral scope without uniquely identifying an internal cognitive mechanism.

## Coordination, permissions and paid contributions

Extend individual support selection into reviewer and team allocation once their joint performance is measured. Different profile labels do not establish independent errors. Evaluate shared-source dependence, correlated failures, reviewer information access and marginal benefit against a simple routing policy under comparable budgets. A review purchase should be justified by expected decision benefit after cost, not information gain alone.

Start permission policies as inspectable recommendations for a named task, value at risk and available oversight. Test them in shadow mode before enforcing scoped permissions. Record which evidence justified autonomy, required review or abstention; allow uncertainty to result in escalation. No broad permission grant follows automatically from a favorable passport.

The later [contribution network](agent-economy.md#paid-contributions--later-expansion) adds a second side to the service: paid participants, expert adjudicators, provenance researchers and red-teamers. Begin with a curated workflow and explicit compensation/acceptance rules. Verify contributions, deduplicate findings, handle disputes and measure the cost of producing useful evidence before opening a marketplace. Paying contributors is an expense funded by customer demand or a defined budget, not a demonstrated growth loop.

## Release boundaries

- Reported probabilities are observations, not access to internal beliefs. Every passport stays conditional on its task, configuration and conditions.
- Current execution metadata is operator-asserted. Issuer, controller, configuration and execution verification remain distinct.
- Browser/MCP evaluation, draft rendering, offline signatures and the local machine consumer are implemented. Identity has live devnet read coverage; consumer decisions use mocked identity fixtures. Public hosting, registered-provider end-to-end validation and payments remain pending.
- Human use remains private by default and does not require a wallet. Identity-linked publication is a separate choice.
- Legacy report.v1–v3 record signing and Memo semantics remain unchanged. New passport signatures have a separate schema and signature domain.
- The separate provenance pilot implements new task generation and synthetic fitting under its own version. Shared-core collection is unchanged. Sequential MCP collection is implemented. Complete empirical pilot comparisons, support selection, production observation, team routing and contributor payments remain pending.
