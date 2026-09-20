# Costed prediction plan — 20 September 2026

Current execution status: the original no-retry run below remains stopped. A documented [bounded-recovery amendment has completed the profile stage](prediction-profile-2026-09-20.md), preserving the predecessor and locking fits and predictions before any later-case exposure. The original budget record below is retained for comparison.

The [full prediction benchmark](prediction-benchmark.md) is implemented and a private run manifest is frozen. **Profile collection started, then stopped after 55 completed episodes and one failed attempt.** The [execution record](prediction-profile-stop-2026-09-20.md) preserves 223 accepted responses and the unresolved usage. This note records measured development cost and the resource plan, not an empirical predictive-validity result.

## Measured development run

GPT-5.6 Luna, GPT-5.6 Terra and GPT-6 Astra, all at medium reasoning effort, each completed two predeclared six-checkpoint episodes through the real MCP server under Codex CLI 0.154.0. Six episodes finished and all 36 answers were accepted. The run used existing Codex account access; no API-key purchase, transaction or payment was made.

| Requested configuration | Mean processed tokens / episode | Mean seconds / episode | Projected tokens for 144 episodes | Projected serial hours |
| --- | ---: | ---: | ---: | ---: |
| Luna, medium | 279,693 | 45.13 | 40,275,792 | 1.81 |
| Terra, medium | 305,185 | 43.57 | 43,946,640 | 1.74 |
| Astra, medium | 194,994 | 43.41 | 28,079,064 | 1.74 |
| Full three-configuration plan | — | — | **112,301,496** | **5.28** |

The six successful episodes used 1,554,180 input tokens, of which 1,323,392 were cached, plus 5,563 output tokens: **1,559,743 processed tokens** and 264.24 cumulative episode seconds. Approximately 85% of input was cached. Cached input is included in the input total, not counted a second time. Token counts measure processed context under this agent runtime; they are not a dollar quote, customer price or direct quota-percentage estimate. Marginal dollar cost is unknown under the existing account.

Two earlier setup attempts failed before any checkpoint answer was accepted. The runner had disabled general approval requests without explicitly permitting its four evaluation tools. The fix authorizes only those four tools and leaves unrelated requests unavailable. Both failed attempts remain archived with their original manifests and source snapshots: **61,195 additional processed tokens and 28.13 seconds**. They are reported separately rather than hidden in the successful-case projection. Total observed development usage across all eight attempts was **1,620,938 processed tokens**.

The six successful provider processes exited normally and supplied usage; the collector independently confirms all episode completion receipts. Codex did not acknowledge orderly MCP-server shutdown, so the six underlying transport attempts remain `open` in their frozen collection snapshots. The runner records completed episodes separately from transport closure. These observations are operator records, not independent execution attestation.

## Frozen full plan

The [public specification](../examples/benchmark-prediction-2026-09-20.json) fixes three configurations, two complete design repetitions, **432 episodes / 2,160 checkpoints**, and the [prediction criteria](prediction-benchmark.md#endpoints-and-decision-rule). Each episode gets a fresh context; each configuration uses the same public evidence and payoffs. Source seeds, full design and raw response records remain private.

The plan fixes **432 attempts**, a **234-million processed-token admission ceiling**, **43,000 cumulative episode seconds** (11.94 hours), and a **180-second timeout per episode**. The token/time allowances sum twice each configuration's observed maximum episode use across its 144 planned episodes, then round up. A collection batch also has an explicit episode count. Admission checks occur between episodes, so one episode may overshoot a token/time ceiling; these are not provider-enforced billing limits.

The estimate extrapolates only two longest-graph episodes per configuration. Shorter sequences, model latency, caching, account limits and retries can change actual use. No automatic failed-case retries or case exclusions are allowed in this version. A failure stops collection for inspection; the plan must not silently expand to keep looking for a positive result.

The fresh manifest's exact-byte SHA-256 is `24da73620aaedb048300b404f2a3919d90d181ce4ca35216e16843a8362acc76`. The cost-estimate artifact it cites has SHA-256 `6fa194f8ea5846365ed46ebb3f80894af2021d0958bf6422929be628c633f53d`. These identify local frozen artifacts, not signed/public execution attestations. The implementation is commit `f08977e`. All 18 synthetic validation checks pass for the fresh two-repetition design.

The first execution stage is the profile partition: 144 episodes across the three configurations. Only after all profile responses are collected can the tool lock fitted models and all static held-out predictions. Collection is now stopped under the frozen failure rule; no lock or later-stage responses exist. A versioned interruption/recovery policy is the next prerequisite for further execution. The existing demonstration cases are not reused as this run's final assignments. The evidence-ledger assistance comparison remains a separate, unexecuted increment.
