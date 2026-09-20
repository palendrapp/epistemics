# Investigation 0.2: fresh-agent acceptance — 21 September 2026

Twelve fresh GPT-6 Astra processes completed **12 cases, 48 checkpoints and 198 probability reports** through the public MCP interface in **8 minutes 50 seconds**. All 48 submissions were accepted on the first attempt. The battery now produces interpretable observations about research choice, forecast coherence and correction handling. Its fitted cognitive parameters remain development diagnostics: the conditional model fits poorly, and a post-collection check identifies its treatment of initial reports as an important source of error.

## What the agent did

**Decisions were consistent with stated probabilities.** All 48 invest/hold decisions followed the declared linear payoff rule, including holding at a tie. Both purchased checks that resolved a directly elicited event were reported correctly and retained at review: four correct checks across the source and backlog cases. These are observations of response consistency, not direct access to internal beliefs.

**Research choices followed price and reported expected benefit.** In each of the three matched pairs, the respondent bought the focused check at a cost of 0.005 points and stopped when its price was 1 point. Each pair used the same evidence and pre-sampled outcomes in separate fresh contexts.

| Focused check | Low-price choice | High-price choice | Low-price net benefit from reported expectations |
| --- | --- | --- | ---: |
| Historical source audit | Buy source audit | Stop | +0.0050 |
| Backlog check | Buy backlog check | Stop | +0.3450 |
| Unaffected-cohort check | Buy cohort check | Stop | +0.0746 |

All six research choices maximized value calculated from that respondent's own elicited expectations. The prospective answers were also coherent: all repeated event probabilities agreed exactly with their main probes, and the largest total-probability discrepancy was **0.26 percentage points**, below the 1.5-point rounding tolerance. In all three purchased research cases, the eventual growth forecast exactly matched the earlier forecast conditional on the result that occurred.

This is useful evidence of an internally consistent reported research policy. It does not identify a stable price-sensitivity parameter: these are deliberately large price contrasts, and the high price exceeds the perfect-information value available under the declared payoff. The small positive source-audit value is also close to rounding precision. Matched-case growth forecasts differed by 2–6 points before purchase, so price effects and fresh-process response variation are not separated by this single run.

Across all 12 cases, research choices agreed with the conditional reference in 11 cases. The exception was a review case where the respondent stopped and the reference preferred the cohort check. Prospective expectations were not requested in that case, so its subjective research value is unavailable. Overall choices were six cohort checks, four stops, one backlog check and one source audit; none exceeded the perfect-information bound implied by the respondent's reported probability.

**The agent responded to actual corrections in both directions.** All four nonzero corrections moved its growth forecast in the same direction as the corrected operating estimate.

| Case | Change to operating estimate | Growth forecast before → after review | Forecast change |
| --- | ---: | ---: | ---: |
| 5 | +6 points | 12% → 40% | +28 points |
| 8 | +6 points | 85% → 94% | +9 points |
| 9 | −6 points | 24% → 10% | −14 points |
| 12 | −6 points | 23% → 14% | −9 points |

These revisions can be large; this run does not supply a simple picture of globally slow reporting. The two review cases confirming zero error produced growth changes of −4 and 0 points. In all six research cases, where zero error was known from the outset, the later confirmation left every forecast unchanged. Confirmation of a previously uncertain zero offset can itself be informative, so the two types of zero review should not be conflated.

**Source reports were comparatively stable.** The source-understatement probability stayed exactly unchanged from Background to Evidence in all 12 cases, while growth forecasts changed. The direct source audit moved its elicited event probability from 50% to 0%, which was correctly retained. This suggests selective separation of source and company judgments in these responses; it does not establish an inability to learn about sources or a general anchoring bias.

## What the cognitive model explains—and misses

The frozen conditional fit selected **source-feedback coupling `rho = 0`** and **report response rate `alpha = 1`**. Within this model family, that favors separate source inference and immediate report adjustment. However, its RMSE was **11.86 percentage points**, above the eight-point development diagnostic. Its status remains `inadequate_absolute_fit`.

| Conditional observer | RMSE across 162 scored reports |
| --- | ---: |
| Separate source inference | 11.86 points |
| Joint inference | 12.90 points |
| Joint inference ignoring transcription review | 13.20 points |
| Halfway report adjustment | 16.34 points |

The first three reports in each case are conditioned on, not scored, leaving 108 later main reports plus 54 prospective reports. For the best conditional fit, main growth RMSE was **14.43 points**, source-probe RMSE **0.82**, and backlog RMSE **9.92**; prospective-report RMSE was **14.73**. The separation parameter explains the stable source answers much better than it explains growth inference. The largest fitted miss was case 12's Evidence growth forecast: 82% reported versus 48.6% predicted.

**An exploratory initialization check changes the diagnosis.** Applying the same joint observer without conditioning its starting state on the initial probability reports reduced RMSE from **12.90 to 7.62 points on the same 162 reports**. This alternative retains the archive/analogue working prior. For example, in case 10 the initial growth report was 75%, but the later report was 48%. The fitted separate-source model predicted 72.4%, whereas the unconditioned joint reference predicted 48.0%.

This implicates the mapping from an initial answer to the model's persistent latent prior. It does not prove that respondents ignore priors or that the alternative is a validated replacement. An initial answer might reflect a different interpretation, reporting noise or a richer hypothesis structure; three marginals do not identify a full joint prior. Initial projection residuals were below 0.000000001 points, so numerical inability to match those marginals does not explain the discrepancy.

The initialization comparison was added after collection. It is not a frozen empirical prediction test, and the conditional fit and alternative baseline must remain separately labeled. The grid's concentrated parameter intervals are not trustworthy trait certainty under this model mismatch. No new passport trait or intervention recommendation is issued.

## Usability, execution and resources

The requested configuration was `gpt-6-astra`, medium reasoning, through Codex CLI 0.155.1 and the existing signed-in account. The launcher followed the official [non-interactive interface](https://learn.chatgpt.com/docs/non-interactive-mode). Each case used a distinct ephemeral process, a temporary working directory, empty accepted history and continuous context within its four stages. Only the five episode MCP tools were allowed; repository instructions, user configuration, browsing, shell, plugins, memory and subagents were disabled. The code-mode host supplied tool transport. The model alias and execution conditions are operator-asserted, not an independently attested immutable model revision or OS-isolated execution.

The frozen battery/evaluator/analysis versions were all 0.2.0. The runtime used a copied implementation, including browser assets, with a verified matching fingerprint. There were no launch recoveries, case exclusions, answer changes, missing usage records or task changes during collection. Twelve distinct execution IDs and all report-byte hashes were verified. Collection occurred at 00:29–00:38 on 21 September in Europe/London (23:29–23:38 UTC on 20 September).

Provider-reported usage was **1,872,108 input tokens**, including **1,608,576 cached input tokens**, plus **9,284 output tokens**: **1,881,392 processed tokens**. Cached input is a subset, not an extra quantity. Individual cases took 39.3–50.9 seconds. Marginal monetary cost under the signed-in account is unknown; this is not an API-price estimate. The development-feature warning appeared in all processes and did not interrupt collection.

All six review respondents identified a real interface inconsistency: the review document verifies the transcription while the `transcription_checked` field and status text still describe it as unchecked. That field currently means verified **before** the episode and also controls model assumptions. A revision should separate that meaning from current review status, rather than merely flipping the flag. One respondent also found the selected historical-report wording ambiguous, one flagged percentage-versus-API-decimal wording, and three mentioned initial tool discovery. The earlier numbered-stage/commitment confusion was not reported in this run.

The existing model and actual stdio MCP regression checks passed again: **15 tests**. The previous version-development checks include 230 Python tests, browser/HTTP coverage and 33 TypeScript tests; those were not all rerun for this documentation-only result update. No Solana write, payment or public raw-result upload occurred.

A separate, untouched human collection was prepared and opened at its instructions page, using the same frozen implementation and a private localhost link. No agent supplied human answers. Actual human completion, time, assistance and feedback remain pending. Humans retain cross-case memory; agents here had fresh contexts, so a shared task is not identical exposure. The burden of 198 probability reports also remains a human usability question.

There are **nine unique worlds**, because the three research worlds each appear at two prices. Repeated stages and paired outcomes are not independent samples. The optional realized-outcome audit averages each price pair before averaging worlds; its Brier loss is 0.1915. This small, selected development set cannot establish general calibration, investment skill or a comparison with the earlier version.

## Next bounded development step

1. Correct the public review-status and historical-report wording in a versioned revision, preserving this run and its original implementation.
2. Separate uncertainty/noise in the initial elicitation from subsequent evidence use. Compare initialization alternatives on these development observations, and validate any revised model's recovery before new collection. Do not add cognitive bias labels to compensate for a poor observation model.
3. Freeze a small repeat/new-case comparison and explicit model baselines before running it. Include observed research policy and correction behavior alongside model parameters; retain the large-price-contrast and elicitation-burden limits.
4. Complete real human acceptance. Only after a difficulty repeats should one targeted-support comparison test improvement and its cost. Current observations show coherent research choices and substantial revisions, so neither unnecessary-research nor global slow-update assistance is justified by this run alone.

## Artifact commitments

Raw responses, private prompts, evaluator state, runner configuration and the frozen source copy remain ignored under `output/investigation2-agent-20260921/`. These hashes bind exact file bytes; they do not provide independent execution attestation.

| Artifact | SHA-256 |
| --- | --- |
| Implementation | `b1901b04d1bf94b1eddb9318dda199de8e7669c6cd3900745ea601ba170f30be` |
| Collection manifest | `bc312322584e02b7fbf65158eccc43f5ab305a770073195ebfe5e70b8b1fe8b6` |
| Respondent configuration | `9d1c4747fce26980fc6079e24c7fea06af2c4d978a53f6616d248257dc2f7344` |
| Execution record | `feedfa317cdb644b69c245cc94e537e3ef1db15670d488220ef00ff24544f3f6` |
| Per-report hash manifest | `29ae96d31a576616532292163a246eba7abd90aaa05523caaf20e0c8ab8166be` |
| Frozen evaluator aggregate analysis | `d71fc0c20f884d7e4f135c046332e1ff84094f122c587694639a5a0bec70e948` |
| Post-collection descriptive analysis | `0cc7bb91051a9ceb7a174c1085c0e8b63e07cac1c5f532a8f7af48e4b5d96190` |
| Exploratory residual/initialization audit | `2dfcccc75d71d3db0af2ee3cafd74dfdaab2cc1fb7fc43bdedaf2b8ca2ff870b` |
