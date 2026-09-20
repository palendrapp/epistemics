# Completed prediction benchmark — 20 September 2026

**Result: `criteria_not_met`.** All 432 planned episodes and 2,160 responses are complete. Configuration-specific profiles predicted held-out responses better than the all-reports and persistence baselines, but **did not improve on a pooled profile**. The gain over reference calibration fell short of the declared minimum, and two configurations exceeded the absolute error ceiling. This completes the frozen prediction comparison; it does not validate personalized assistance or a general cognitive phenotype.

The [frozen protocol](prediction-benchmark.md), [costed plan](prediction-budget-2026-09-20.md), [recovery amendment](benchmark-recovery.md) and [profile-stage results](prediction-profile-2026-09-20.md) document the design and its history. No endpoint, comparator, threshold or case inclusion rule was changed after predictions were locked.

## What was evaluated

The requested configurations were GPT-5.6 Luna, GPT-5.6 Terra and GPT-6 Astra, each at medium reasoning effort. These are provider aliases, not independently verified immutable revisions. Each episode started a fresh ephemeral respondent process with the public MCP interface; two failed attempts were recovered with their accepted public answers restored unchanged.

The task distinguishes original evidence from explicitly copied reports, across evidence direction, source track record and matched cases. It remains one fictional binary-source task family. It does not measure general negativity, confirmation bias or resistance to adversarial content.

| Partition | Completed episodes | Accepted responses | Role |
| --- | ---: | ---: | --- |
| Profile | 144 | 576 | Fit all static predictors |
| Policy | 144 | 720 | Reserved development observations; excluded from prediction fitting/scoring |
| Held-out | 144 | 864 | Score locked predictions |
| Total | **432** | **2,160** | All planned cases retained |

Fits and static predictions were locked at **10:26:28 UTC**, before policy or held-out collection. The primary endpoint uses the **720 post-evidence held-out responses**, 240 per configuration. Prior-only responses do not enter that endpoint. The persistence comparator uses only the preceding accepted response within the episode; the other predictions were fixed at the lock.

## Held-out prediction results

The table reports probability RMSE in **percentage points**; lower is better. The macro average gives each configuration equal weight. These are errors in predicting reported probabilities, not errors against realized company outcomes.

| Predictor | Luna | Terra | Astra | Macro average |
| --- | ---: | ---: | ---: | ---: |
| Individual four-parameter profile | 8.881 | 8.098 | 1.380 | **6.120** |
| Pooled four-parameter profile | 8.748 | 8.106 | 1.346 | **6.067** |
| Reference calibration | 9.461 | 8.644 | 2.937 | 7.014 |
| One gain for all reports | 12.895 | 12.681 | 9.234 | 11.603 |
| Persistence | 19.779 | 17.794 | 17.559 | 18.377 |
| Raw-source sensitivity, separate analysis | 8.954 | 8.118 | 1.286 | 6.119 |

The frozen rule required at least **1 percentage point** of macro RMSE improvement over **every** primary comparator, a positive lower 95% bootstrap bound for every improvement, and individual RMSE of at most **5 points for every configuration**.

| Comparator | Individual-profile improvement, points | Paired 95% interval | Minimum gain met? | Positive lower bound? |
| --- | ---: | --- | --- | --- |
| Pooled | −0.053 | [−0.183, 0.193] | No | No |
| Reference calibration | 0.895 | [0.518, 1.720] | No | Yes |
| One gain for all reports | 5.483 | [3.994, 7.882] | Yes | Yes |
| Persistence | 12.258 | [9.475, 15.887] | Yes | Yes |

Only Astra meets the individual absolute error ceiling. All planned cases are complete and execution records are resolved under the amended recovery protocol. Accounting remains incomplete because usage is unknown for two failed attempts.

Intervals use the predeclared 2,000 paired bootstrap draws over 24 matched groups, preserving both twins and the same group draws across configurations. They describe case reweighting conditional on these fitted profiles and requested configurations. They exclude fitting uncertainty and do not establish population coverage. The thresholds were pragmatic pilot targets, not power-validated effect sizes.

## Interpretation and secondary observations

The main product finding is that **these fitted individual differences did not add demonstrated predictive value over sharing one profile**. This is not proof that all configurations behave identically, or that profiling cannot help on other tasks. It does mean this run cannot support a claim that our current individualized profile improves prediction beyond its declared simple alternatives.

The model that separates original evidence from copies outperformed the comparator that gives both one common gain. That supports this model structure for prediction within the tested task. It does not show that any configuration has a general repetition vulnerability. All three profile-stage copy-weight intervals included zero. The earlier fitted differences remain descriptive and conditional on the source-inference model.

The predeclared raw-source-frequency sensitivity has macro RMSE of 6.119 points, essentially the same as the primary 6.120. It remains a sensitivity analysis, not a replacement primary result. In particular, the primary evidence weights above one should not be relabeled as general overreaction: changing the source-inference assumption substantially changes their interpretation.

Secondary individual-profile MAE is 5.280 points for Luna, 1.716 for Terra and 1.166 for Astra. Predicted decision agreement is 97.9%, 97.9% and 100%, respectively, using the declared 0.5 threshold. This is agreement with participants' decisions, not evidence that those decisions were correct or improved by support. Terminal Brier/regret quantities in the private report are expectations under the evaluator model, not realized investment outcomes.

**Exploratory residual diagnostic, computed after primary scoring:** the five largest errors contribute 43.4% of Luna's squared error, 98.8% of Terra's and 8.2% of Astra's. Errors above 10 probability points occur at 31, 5 and 0 of the respective 240 checkpoints. The large Terra RMSE therefore coexists with a much smaller MAE. This motivates inspecting occasional large deviations as well as average response weights; it does not identify their cause. No observations were dropped, predictions refitted or criteria recomputed around these cases.

## Execution, recovery and resources

There were **434 attempts: 432 completed and two retained failures**, with two retries and zero unresolved attempts. No case was excluded, replaced or imputed.

- The original Terra profile attempt failed after three accepted answers. The pre-lock recovery amendment preserved the stopped predecessor and restored those same answers in a fresh context. Its usage remains unknown.
- A Luna held-out attempt timed out after three accepted answers. The already-frozen recovery policy permitted one fresh-context retry, which restored those answers and completed. Its failed-attempt usage also remains unknown. This did not require or receive a new protocol amendment.

The Luna failure has a timing discrepancy: UTC timestamps span **14:22:17.973970–14:41:49.521133**, or **1,171.547 seconds**, while the runner records **180.017 monotonic seconds**. The cause is unknown. Budget accounting used the recorded duration, so it must not be described as a universal wall-clock bound. The retry recorded 35.292 seconds. No other attempt had a UTC/recorded-duration discrepancy greater than five seconds in the completion check.

MCP transport records contain **433 `open` and one `closed`** status. Provider-process outcomes and episode completion receipts are separate from orderly transport shutdown; zero unresolved execution does not mean all transports acknowledged closure.

| Partition | Attempts | Known processed tokens | Recorded cumulative seconds |
| --- | ---: | ---: | ---: |
| Profile | 145 | 24,166,891 | 6,242.30 |
| Policy | 144 | 30,524,779 | 7,285.90 |
| Held-out | 145 | 35,216,714 | 8,401.84 |
| Total | **434** | **89,908,384** | **21,930.04** |

Known totals comprise **89,523,105 input tokens**, including **76,993,792 cached input tokens**, plus **385,279 output tokens**. Cached input is not added twice. Recorded cumulative duration is about 6.09 hours and excludes gaps between attempts; the timing discrepancy above remains visible.

Usage is a **known lower bound**. Two unknown attempts carry a separate 2,000,000-token planning reserve, yielding a 91,908,384-token admission charge. That reserve is neither measured usage nor an upper bound on unknown actual usage. The run stayed within the frozen admission ceilings and below the three-unknown-attempt stop threshold. The existing signed-in account was used; marginal dollars are unknown. These totals include the predecessor profile attempts, but exclude development costing and the separate 34-checkpoint core acceptance run.

## Artifact integrity and verification

The result records `protocol_status: amended`, `execution_scope: includes_retried_episodes` and `accounting_complete: false`. It does not relabel the original no-retry predecessor as completed.

| Artifact | SHA-256 |
| --- | --- |
| Amended benchmark manifest | `6a3a4e88dab06afa49bf81e1e17c35d003c68727c4785a1f1765840553f23fb9` |
| Prediction lock | `f03f6e76ae3e5129668a9247e3e0abd2e78bdd6671b1d5aaf5be4c66c9f9d07f` |
| Final benchmark report | `e459c5e83a4c603434a150b11f4f2c267e48c1c1b421f93855c089ab40a140db` |
| Completed private archive index | `f2e06abc7ea3759650fb113bef8eb445a5a757314bd5449cba4c7e4eb6d08de6` |
| Completion verification | `3d845f71220e2deb24bcb07ca3ae2a71ce1a627e650b2f847d52a16e877817e5` |
| Luna collection export | `c4b429ae655e64ed22157c522fae78d3ef412440a37bacfbd37ec383c2fda831` |
| Terra collection export | `b8bbbb4ed2821a83dd3acb327e6cb7683fe2939a27794c2d5e580c6568c6a4b1` |
| Astra collection export | `f9e67c0d9a42224e0dd0956d8d717a599b35b15b008d31877d94136768961aa3` |

The frozen benchmark implementation remains commit `bd9cadb4c8a145af68afb261d559ed0c5b5a059a`, with implementation fingerprint `34660fde859d0d706d75f8e270c39399204fd61e0c1ab2676c0c80aced2d8184`, benchmark 0.2.0, task/analysis 0.1.0 and Codex CLI 0.154.0. The machine-consumer implementation added during collection did not alter those sources.

Verification passed: report-schema validation, all partition/response counts, unchanged profile responses and completion receipts, all 315 files in the profile archive, database integrity checks, matching database/file lock and report bytes, idempotent analysis, and direct recomputation of individual RMSE from the frozen predictions. A new 605-file private archive contains the completed run, frozen implementation, lock, result and verification, with a verified hash index. Raw cases, evaluator seeds, responses and private diagnostics remain outside Git. These hashes provide exact-byte integrity, not independently witnessed execution.

The implementation's [CI checks passed](https://github.com/palendrapp/epistemics/actions/runs/35508531070): 197 Python tests, 33 TypeScript tests, formatting/lint and type checks. Synthetic recovery validates the software/model pipeline; it does not convert this empirical result into a passing predictive claim.

## Consequence for the roadmap

Keep shipping inspectable, machine-readable **descriptive** passports, including measured behavior, uncertainty, configuration and provenance. A consumer policy that requires validated individual prediction or intervention benefit should continue returning review when that evidence is absent.

Before another predictive claim, audit residual patterns and repeatability, check task/response comprehension, and compare a pooled model with models that can describe occasional large deviations. Treat these now-observed cases as development data; freeze any revision and collect genuinely new held-out cases. Budget the next run from this measured cost rather than automatically repeating the full 432 episodes.

In parallel, complete human usability acceptance and a controlled registered-provider consumer demonstration. A separately frozen assistance experiment can test whether a ledger or review helps at all, and whether profile selection adds value over giving the same support without personalization. None of those benefits has yet been established. The [roadmap](mvp.md) keeps paid bounded evaluation, hosted delivery and later outcome-validated policies distinct.
