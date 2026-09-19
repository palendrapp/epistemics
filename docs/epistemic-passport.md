# Epistemic passport

## Product purpose

An epistemic passport is a portable, interpretable behavioral profile attached to an agent identity and a specific configuration. It helps a person or another agent answer: **what should I expect when this agent encounters evidence, uncertainty, disagreement and decisions?**

The product is a standard evaluation, a readable profile, and a verifiable record. Computational models and measurement checks support the interpretation behind that profile. Running a research study is not the customer's workflow.

A second purpose is cognitive security: use the explicit model to identify where a decision maker may benefit from support, choose a targeted intervention and test whether it helps. The intended profile includes both observed tendencies and response to assistance. This direction includes humans as well as agents; the current implementation is agent-focused.

“Phenotype” means observed tendencies across the declared evaluation conditions. The ambition is broad coverage of epistemic behavior. Every issued passport must make its actual coverage clear: a finite evaluation cannot fully characterize an agent in every setting, and elicited probabilities are observations rather than direct access to internal beliefs.

This document defines the product direction. The repository implements a [shared core battery and human/MCP interfaces](live-core.md), draft passports, and legacy signed-report components. Broader phenotype coverage and the identity-linked issuance flow remain proposed.

## The experience

1. Identify the agent and configuration to evaluate: model revision, prompt, tools, decoding settings and memory/context policy, with disclosure rules for private contents.
2. Run a versioned passport evaluation through MCP. The evaluator manages task selection, order, fresh contexts, checkpoints and retries within a declared budget.
3. Receive a concise profile with dimension summaries, representative observations, practical implications and links to supporting measurements.
4. Issue an evaluator-signed passport binding that profile to the evaluated configuration, protocol and evidence artifacts. Publish an identity association and commitment on Solana, with off-chain artifact storage.
5. Let consumers verify provenance, inspect scope and compare compatible passports. Re-evaluate changed configurations and retain evaluation history.
6. Where authorized, use the profile to select support, compare assisted and baseline performance on fresh cases, and record the conditions under which that support helps.

The intended public surface is one evaluation command or API operation and one resulting passport. `epistemics serve` and the dedicated core MCP adapter now run a combined 34-checkpoint evaluation and produce a draft. `epistemics passport create` also derives drafts from existing reports. Signing and publication remain separate work.

## Same evaluation for humans and agents

Human participation is a requirement of the shared evaluator design. Core 0.1 now serves the same public scenarios, evidence sequence, response semantics and scoring through a human browser interface and agent MCP adapter. The participant/session boundary supports both kinds without requiring humans to supply model/version fields. The original agent report contracts remain unchanged; the shared workflow uses report.v4 and passport.v2.

The human interface adds task instructions, practice, response controls, progress and pause/resume. It must not silently supply extra hints, evidence or feedback. Record interface, tools, assistance, time and context policies so comparisons have a clear scope. The same behavioral model can describe responses from both kinds of participant while its interpretation and population references require separate support.

The first usable delivery target is a human and a fresh agent completing the same core battery and receiving readable passports. Human results can remain private; identity-linked issuance is a separate choice. The [roadmap](mvp.md) makes this flow an early milestone.

## Profile dimensions

These are proposed product dimensions, not a claim that all are already measured adequately.

| Dimension | Question the reader wants answered | Starting point and remaining work |
| --- | --- | --- |
| Evidence weighting | How much does new evidence move its judgment relative to prior expectations, and does evidence strength matter? | Existing prior/evidence tasks and company sequences; broaden contexts and establish readable behavioral anchors. |
| Source judgment | How does it form an impression of a source, and how readily does track record change that impression? | Existing claim/source task and discovery source/archive manipulations; convert their outputs into supported profile statements. |
| Revision and persistence | When evidence conflicts with its view, does it revise the conclusion, distrust the source, or change its explanation? | Existing joint inference, source audits and reversal tasks; add compact matched contrasts to distinguish these responses. |
| Dependence and causal reasoning | Does it count repeated coverage as fresh evidence, and can it distinguish evidence about a company from evidence about its explanation? | Company provenance and auxiliary-hypothesis probes; expand beyond one authored discovery mechanism. |
| Uncertainty and calibration | Do stated probabilities and intervals match demonstrated predictive performance? | Existing proper scores and interval reports; ensure enough independent outcomes for each strength of claim. |
| Judgment-to-decision consistency | Do choices follow the judgments it reports under stated payoffs, and how does uncertainty affect action? | Existing company decision probes; keep payoff comprehension, preference and inconsistency distinct. |

Stability across repetitions, wording and contexts accompanies every dimension. It is a property of the evidence supporting the profile, not a separate claim that an agent has one immutable trait.

Information seeking under a cost or time budget is a useful later dimension. The current battery does not measure it. Domain modules, starting with portfolio-manager company assessment, add context-specific detail to the core passport.

## Model behind the profile

Explicit inference modeling remains central. Organize the behavioral model around source impressions, interpretation of evidence and dependencies, updating of hypotheses and explanations, and expression through probabilities, intervals and decisions. These components connect the user's proposed input and output terms: an apparent reluctance to update could arise from source distrust, a different causal explanation, or how a judgment is reported.

The evaluation needs contrasts that distinguish those explanations where feasible. When competing models fit similarly, describe the observed behavior and retain that ambiguity instead of assigning a confident cognitive label. The profile is a readable view of the evidence and model, not a personality narrative generated independently of them.

Intervention hypotheses extend this model. A fitted explanation suggests what to try; a separate comparison establishes whether the support improves outcomes. The proposed [cognitive-security layer](cognitive-security.md) specifies candidate supports, an intervention check, human adaptation and disclosure rules. Baseline traits, predicted benefits and measured intervention effects must remain distinct.

## How a dimension reads

Each dimension should contain:

- A plain-language tendency, anchored to observed behavior rather than an unexplained score.
- A measurement with units or an explicit reference point, and its uncertainty or repeatability where estimable.
- Representative task observations, including material exceptions.
- A practical implication stated at the scope supported by those observations.
- Coverage, conditions and evidence status: supported, provisional, or insufficient evidence, using versioned criteria.

For example, an **illustrative, unmeasured** source-judgment entry could read: “Initially favors established sources; changes that preference when given a sustained contrary track record.” The evidence would separately show the initial source-label effect and the change after the archive. The implication might be: “Provide source history alongside unfamiliar claims.” A generic label such as “gullible” would obscure both the conditions and the useful intervention.

Keep three kinds of result distinct: performance on a task, a directional tendency such as greater response to negative evidence, and variability across runs or contexts. A larger tendency coefficient is not automatically better or worse. Negative-evidence weighting also needs to be separated from negative wording and from genuinely more diagnostic bad news.

The default view should emphasize behavior and implications. Detailed coefficients, model assumptions and fit diagnostics remain inspectable. Avoid a single epistemic-quality score, arbitrary 0–100 trait scales, or population percentiles without an appropriate comparison set.

## Evaluation design

The core should be a fixed, versioned, budgeted collection of short scenarios. It should combine controlled calibration probes with discovery tasks where the agent must infer source reliability and the structure connecting evidence to outcomes. Both modes are useful; the discovery tasks are central to characterizing behavior in less specified situations.

Design the composition around the proposed dimensions rather than concatenating every existing battery. Reuse existing generators and analysis where they fit. Sample multiple scenarios, evidence strengths and directions; include targeted contrasts and repetitions where interpretation depends on them. Keep company assessment as a domain module so one business mechanism does not define an agent's general profile.

Freeze a release's task composition, scoring and interpretation rules together. Measure completion rate, cost and duration with real agents before setting a service budget. Preserve accepted answers, idempotent retries, evaluator-side hidden state and records of incomplete attempts. A partial run must show missing coverage and must not receive a complete-passport status.

Measurement quality is release engineering: check known synthetic behaviors, confusing alternatives, repeatability and sensitivity to irrelevant wording. Apply these checks to the claims each dimension makes. Unsupported dimensions can display insufficient evidence; useful, supported observations need not wait for an exhaustive theory of agent cognition.

## Passport artifact and identity

The proposed versioned passport artifact binds:

- Stable subject identifier and exact evaluated configuration fingerprint.
- Evaluator identity, execution-verification method and evaluation time.
- Battery, scoring/model and interpretation versions.
- Run coverage, conditions, resource budget and completion status.
- Dimension measurements, readable interpretations and supporting observation references.
- Optional intervention candidates and tested effects, with baseline/assisted configuration references and their evidence status.
- Exact-byte digests and locations of evidence artifacts, with their access policy.
- References to earlier passports and explicit correction or withdrawal events where applicable.

The readable rendering and machine-readable artifact must describe the same measurements. Public sharing should not require publishing private system prompts or full transcripts: configuration digests and controlled-access evidence can support that separation. Consumers need access to the evidence to independently reproduce an interpretation; a digest alone does not provide it.

A stable agent identity can accumulate passports for multiple configurations. A new model, prompt, toolset or memory policy does not automatically inherit an old configuration's profile. Comparisons must account for protocol versions and context, as well as the subject name. Report evaluation age and configuration changes explicitly; do not imply perpetual validity.

Solana supplies the record's identity association, authenticated provenance and discoverable history in the intended product. Detailed measurements and transcripts live off-chain. Issuer identity, subject/controller identity, configuration identity and execution verification remain distinct. A valid signature or on-chain commitment authenticates an attestation; it does not establish which model actually ran or that every interpretation is correct.

The current client signs individual v1–v3 evaluation reports and supports devnet Memo commitments. It has no stable-identity registry, artifact hosting/indexing, passport aggregation or passport signing contract. The matched-study profiles are not yet accepted by that signer. See [identity and records](identity-and-records.md) for existing guarantees and proposed lifecycle rules.

## Next implementation boundary

The draft profile contract, renderer and shared 34-checkpoint core workflow are implemented. Coverage gaps and synthetic demonstrations are explicit. Next, run actual humans and fresh agents through their respective interfaces to check whether the questions and profiles are understandable, useful and reasonably repeatable. Use that feedback to revise the bounded composition and add discriminating contrasts.

The draft contract includes untested support candidates, with an initial evidence-ledger suggestion rule. After the baseline workflow, implement one bounded comparison of a targeted support against no assistance and generic assistance, using the same report and configuration discipline.

Extend signing and verification to the passport artifact, then implement the identity association and publication/retrieval path. Keep the larger matched-study machinery available for developing and checking difficult measures; it is an internal tool rather than the default passport experience. Detailed milestones are in [MVP scope](mvp.md).
