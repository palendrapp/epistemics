# Completed profile stage — 20 September 2026

All **144 profile episodes / 576 responses** are complete under the [bounded-recovery amendment](benchmark-recovery.md). GPT-5.6 Luna, GPT-5.6 Terra and GPT-6 Astra, each at medium reasoning effort, contributed 48 episodes / 192 responses. Profile fits, comparator fits and static predictions for 288 held-out checkpoints per configuration were locked at **10:26:28 UTC**. Policy and held-out responses remain uncollected; predictive usefulness and assistance benefit are not yet established.

The clearest fitted difference is Luna's lower effective prior weight. Terra and Astra assign little additional weight to explicitly copied reports. Luna's positive copy-weight estimate is uncertain. These are effective reporting parameters in this task, not direct measurements of internal beliefs or general cognitive traits.

## Fitted profiles

The primary equation is `logit(p_report) = b + w_prior × logit(p0) + w_evidence × U + w_copy × C`. Here `U` aggregates original-source signals and `C` aggregates copied exposures. The primary source model uses Beta(1,1)-smoothed accuracy from the displayed track records. Its reference coefficients are `(0, 1, 1, 0)`.

Each cell gives the estimate and its 95% matched-group bootstrap interval:

| Parameter | Reference | Luna, medium | Terra, medium | Astra, medium |
| --- | ---: | --- | --- | --- |
| Intercept `b` | 0 | −0.043 [−0.130, 0.045] | −0.008 [−0.036, 0.016] | 0.000 [−0.024, 0.026] |
| Prior weight | 1 | **0.829 [0.739, 0.924]** | 0.970 [0.941, 0.998] | 0.994 [0.977, 1.016] |
| Original-evidence weight | 1 | 1.026 [0.926, 1.123] | 1.150 [1.110, 1.181] | 1.115 [1.080, 1.149] |
| Additional copy weight | 0 | 0.113 [−0.007, 0.200] | 0.004 [−0.024, 0.037] | −0.008 [−0.033, 0.013] |

Luna's fitted prior weight is below the reference across this interval: its reported probabilities show less sensitivity to the supplied base rate, conditional on the other terms. Terra's smaller departure is close to the reference, while Astra's interval spans it. These separate intervals are not a formal pairwise model-comparison test.

All three copy-weight intervals include zero. Luna's wider interval leaves more uncertainty about an additional copy effect; this is not a demonstrated generalized susceptibility to repetition. None of the intercept intervals establishes a stable positive or negative offset. The model does not separately identify negativity bias, confirmation bias or a latent source-trust mechanism.

## Why source inference matters

The predeclared sensitivity model uses raw source success rates rather than Beta(1,1) smoothing. It produces the following original-evidence weights:

| Configuration | Raw-source evidence weight and 95% interval |
| --- | --- |
| Luna, medium | 0.883 [0.797, 0.969] |
| Terra, medium | 0.991 [0.956, 1.018] |
| Astra, medium | 0.961 [0.930, 0.990] |

Thus Terra and Astra's coefficients above one in the primary model should not simply be labeled overreaction. Under a different, predeclared source-inference assumption, their gains are close to one, with modest attenuation for Astra. Luna's evidence gain is also lower under this parameterization. Source inference and the mapping from an assessment to a reported probability remain partly confounded.

All primary and sensitivity fits had 1,000 successful bootstrap draws over 24 matched groups, retaining both twins and all their checkpoints. No endpoint probabilities needed clipping. The primary design matrix had condition number 2.328. These intervals describe case reweighting for the fitted task and fixed requested configurations; they do not establish population coverage, domain transfer or immutable provider-model identity. One Terra episode includes a resumed context.

## Execution and accounting

The [original run](prediction-profile-stop-2026-09-20.md) stopped after 55 completed episodes and a failed Terra attempt with three accepted answers. The amendment preserved the original run, its 223 accepted responses and all 56 attempt records. Terra's recovery finished the existing episode in a fresh context using its accepted public history. All 88 subsequent profile episodes completed without another failure.

The final profile accounting is **145 attempts: 144 completed and one retained failure**, with one retry and no unresolved execution. All original answers and receipts were verified unchanged. No case was excluded, replaced or imputed. The original failed attempt's usage remains unknown.

As in development, Codex did not acknowledge orderly MCP shutdown: all 145 underlying transport records remain `open`. Episode completion receipts and completed provider processes are recorded separately from transport closure; the zero unresolved-execution count does not assert that those transports closed cleanly.

Known usage is **24,054,797 input tokens**, including **20,152,448 cached input tokens**, plus **112,094 output tokens**: **24,166,891 known processed tokens**. Cumulative episode time, including the failed attempt, was **6,242.30 seconds / 104.04 minutes**. These totals include the predecessor profile collection but exclude the separate development-costing runs.

The unknown attempt carries a separately labeled **1,000,000-token planning reserve**, producing an admission charge of **25,166,891 tokens**. The reserve is not added to measured usage and is not an upper bound on unknown actual cost. Marginal dollars remain unknown. The frozen ceilings are 441 attempts, a 234-million-token admission charge and 43,000 cumulative episode seconds, with a 180-second timeout per attempt.

The lock records `protocol_status: amended`, `execution_scope: includes_retried_episodes`, and `accounting_complete_at_lock: false`. Completion of this stage does not relabel the predecessor's no-retry plan as completed.

## Frozen artifacts and validation

- Original manifest SHA-256: `24da73620aaedb048300b404f2a3919d90d181ce4ca35216e16843a8362acc76`.
- Amended manifest SHA-256: `6a3a4e88dab06afa49bf81e1e17c35d003c68727c4785a1f1765840553f23fb9`.
- Predecessor snapshot-index SHA-256: `aaa0c4e804b3834d36ef1d1f9f8e49f64f0fc258ba7234d91881ed8dc530593e`.
- Prediction-lock SHA-256: `f03f6e76ae3e5129668a9247e3e0abd2e78bdd6671b1d5aaf5be4c66c9f9d07f`.

These hashes identify exact private artifacts, not independently witnessed execution or signed public attestations. Raw responses, private diagnostics, source seeds and future checkpoint predictions remain outside Git. The frozen implementation is commit `bd9cadb` (benchmark 0.2.0, task/analysis 0.1.0, Codex CLI 0.154.0). The requested model aliases are not independently verified immutable revisions.

Validation passed: 197 Python tests, 20 TypeScript tests, Ruff, formatting and type checks, and [GitHub CI](https://github.com/palendrapp/epistemics/actions/runs/35502042709). All 18 synthetic checks passed on the unchanged design, including parameter recovery and misspecification detection. Recovery-specific tests verify known-parameter recovery after resumed collection, preservation of accepted history, limits, disclosure consistency and refusal to freeze exports before execution is resolved. Solana RPC coverage is mocked; no validator or live-network validation was performed.

Final operational checks verified the complete 48-episode profile partition for each configuration, the unchanged predecessor snapshot and accepted-answer prefixes, database integrity, no later-case exposure, and byte-identical database/file prediction locks including an idempotent lock retry.

The next stage is the frozen policy partition, followed by held-out collection and scoring against the declared baselines. The profiles and static predictions are already fixed. Whether these differences improve prediction enough to justify personalized assistance remains an open empirical question.
