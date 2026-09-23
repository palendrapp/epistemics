# Investigation 0.3: repeatability and new-case results

The [36-episode pilot](investigation3-pilot.md) completed on 23 September 2026. It provides a repeatable descriptive profile in this authored company task, but does not establish an average-error advantage from fitting the agent's parameters. Uncertain initialization improves predictive log scores relative to the alternatives; important joint-response patterns remain unexplained.

## Completion and provenance

All **36 fresh contexts / 144 checkpoints / 594 probability reports** completed in **34 minutes 40 seconds**, within the declared 45-minute cap. There were no failed submissions, unexpected tool calls, excluded cases or missing usage records. Episode 23 took 220 seconds to return final output/usage after its evaluation had finished; its accepted answers were retained without retry.

The three collections were 12 development cases, 12 fresh-context repetitions and 12 new cases. Each collection contains nine company worlds; across the whole pilot there are **18 distinct worlds**, since repetition and matched prices reuse worlds. Counts below are observations under this design, not independent population samples.

Requested model/configuration: `gpt-6-astra`, medium reasoning, unspecified temperature, CLI 0.155.1, with the same declared prompt and restricted MCP tool set throughout. The alias and execution remain operator-asserted. All 36 thread IDs were distinct. The frozen evaluator and pilot fingerprints matched at completion.

Recorded usage: **5,669,825 input tokens**, including **4,802,944 cached input tokens**, plus **26,866 output tokens**. Noncached input was 866,881 tokens. These are provider-reported processing counts; marginal dollar cost under the existing account is unknown.

The fit was locked before any repeat/new responses. All 24 test-case prediction artifacts bind that lock and were timestamped after the first answer but before the second. Their selected-branch public-trial hashes matched the completed reports. All 36 report byte hashes were verified. Predictions condition on the subsequent scripted public evidence; query choice and hidden company outcomes are not the prediction targets.

| Artifact | SHA-256 |
| --- | --- |
| Precollection plan | `4f8703ea0face6b0f159dd476c4655544a7037263573e8b38415b6cae8312ff1` |
| Locked development fits | `b4465d3a960ccd485677c884f48acfae0827e54cff9a616f95a3b6de329a3a81` |
| Prospective analysis | `2cbbfcb950c4925cf019efe81c8dd5cb05b02c2cfc9e9d3c1fbc7d83c932e6c7` |
| Development passport source | `686a93c3e8d6ff3be6a92533047a2d8cad33db8b2a7392df275fa7e98ff721d2` |
| Repeat passport source | `f89bb38a9ae77f52b1a8f0840c9a0262773577c4902b9e9abfa811f1b712a4b2` |
| New-case passport source | `d0231c43de8ea285f2c936afff553d6493f2aee7e490e17255a1d6f771726a4c` |

Raw artifacts remain private under `output/investigation3-pilot-20260923/`. The three collections have separately derived and verified HTML/Markdown/JSON passports. Development and new-case passports also passed offline demonstration signing with discarded ephemeral keys. No registry transaction, public artifact hosting or payment occurred. Passport model-diagnostic tables are descriptive fits to their own source collections; **the prospective comparison below exclusively uses the locked development estimates**.

## What repeated

The 72 main probability reports before receiving a query result differed by **3.72 probability points RMS** across the same cases in fresh contexts. Research actions matched in **11/12 cases**; all six matched-price research actions matched. The differing choice was between segment and operations checks in a standard review case, where prospective query forecasts were not elicited. Later main reports differed by **5.03 points RMS** over the 66 reports from the 11 cases that selected the same branch. Cases with different revealed evidence are excluded only from this explicitly branch-matched repeatability statistic, not from prediction scoring.

| Observation | Development | Repeat | New cases |
| --- | ---: | ---: | ---: |
| Decision agrees with reported probability/payoff | 48/48 | 48/48 | 48/48 |
| Coherent prospective research forecast sets | 6/6 | 6/6 | 6/6 |
| Research choice maximizes coherent stated value | 6/6 | 6/6 | 6/6 |
| Revision follows the direction of an actual correction | 4/4 | 4/4 | 4/4 |
| Retains explicitly resolved source/backlog event | 2/2 | 4/4 | 4/4 |
| Source report unchanged from background to operating evidence | 12/12 | 12/12 | 12/12 |

The largest prospective total-probability discrepancy was 0.40 points, within the declared rounding tolerance. These are consistency observations, not general forecasting accuracy or optimality under the evaluator's latent world. The research-policy denominator uses coherent forecasts, and all six sets in each collection qualified.

The agent consistently declined the cheap source audit in the development/repeat pair, bought the cheap operations and segment checks, and stopped at all three high prices. Its stated prospective forecasts supported those choices. The descriptive interpretation is sensitivity to expected decision benefit, not indiscriminate information seeking. The large price contrast cannot identify a stable cost-sensitivity coefficient.

## Frozen conditional prediction

The development fit selected source-feedback/report-rate pairs of **0.4/1.0** for working-prior initialization, **0.1/1.0** for hard-report initialization, and **0.5/1.0** for noisy-report initialization. These differing source-feedback coefficients coexist with unchanged elicited source probabilities; they are fitted compromises across multiple report targets, not literal measurements of the amount of source updating.

Each test partition scores all 162 later/prospective probability reports. Lower RMSE is better; higher (less negative) log score is better. Log scores integrate one latent initial state jointly over an episode before normalization by report count.

| Frozen model | Repeat RMSE, points | New RMSE, points | Repeat log score/report | New log score/report |
| --- | ---: | ---: | ---: | ---: |
| Fitted working prior | 8.78 | 11.88 | −3.619 | −6.079 |
| Fitted hard report | 12.77 | 13.83 | −4.780 | −5.175 |
| Fitted noisy report | 8.84 | 12.05 | **−3.285** | **−5.046** |
| Fixed joint observer | 9.04 | **11.84** | −3.674 | −6.320 |
| Fixed cut-source observer | **8.72** | 11.92 | −3.626 | −5.997 |
| Report persistence | 21.01 | 22.42 | −8.899 | −9.887 |

Uncertain initialization improves on hard conditioning and obtains the strongest log scores. Fitting the configuration does **not** show a clear average-error gain over the simple fixed observers. For noisy initialization, the exploratory 95% whole-world bootstrap interval for RMSE minus the fixed joint observer is **[−1.93, +1.24] points** on repeats and **[−1.22, +1.20]** on new cases. Both include zero. There are only nine world clusters per partition and deliberate offset balancing; these intervals do not establish population-level equivalence or superiority.

Predictive uncertainty also needs criticism. The noisy model puts only 1/12 new-case RMSE values above its simulated 97.5th percentile, but **8/12 joint episode log scores fall below its simulated 2.5th percentile**. Broad error ranges alone can hide mismatches in the pattern of reports. Relative likelihood improvement is not adequate evidence that this model family explains the agent's responses. The model-conditional checks are not multiple-testing-adjusted hypothesis tests or trait confidence intervals.

The pilot contains one configuration and therefore cannot compare individual profiles with population pooling. It also did not test an intervention, delegation outcomes, source-label bias, negativity bias or unrestricted hypothesis generation. Passports remain provisional and do not gain a validated-prediction flag.

## Exploratory residual diagnosis

The following decomposition was inspected after the predeclared comparison; it is a development clue, not another held-out model-selection result.

| New-case report target | Noisy-model RMSE, points | Fixed-joint RMSE, points |
| --- | ---: | ---: |
| Company growth | 12.38 | 11.21 |
| Source audit event | 5.82 | 6.10 |
| Backlog event | 14.84 | 15.87 |
| Prospective query forecasts | 12.80 | 12.00 |

The largest noisy-model case error was 23.06 points. In that review case, the agent moved its growth forecast from 50% to 90% and later to 86% after correction, while its backlog forecast stayed at 50%. The model predicted backlog around 11% after the operating evidence. This is a disagreement about how evidence propagates to an auxiliary judgment, not simply slow updating of the focal company forecast.

Across development/repeat/new collections, company forecasts moved by an average absolute **21.00 / 21.92 / 26.08 points** after operating evidence. Backlog reports moved **4.58 / 5.42 / 4.58 points**, and remained unchanged in **7/12, 5/12 and 6/12** cases respectively. Source reports never moved at that transition. Different targets can appropriately have different sensitivities; these observations do not alone establish irrationality or an internal modular architecture.

The next measurement slice should distinguish competing explanations: different inferred causal relationships, selective propagation between company/source/operations judgments, and differences in how uncertain judgments are reported. The current two-parameter family has a source-feedback control and a shared report-rate control, so it cannot independently describe each of those behaviors. Design matched diagnostic contrasts and test recovery before expanding the parameter set or launching another large collection. Keep existing observations as development data for that revision.

## Product and usability implications

The useful passport statement today is: **under these company tasks, decisions and research choices followed the reported probabilities, corrections changed company judgments in the expected direction, and source impressions stayed stable after the operating evidence. Repeated reports were similar but not identical.** This is already more informative than a single quality score. It does not imply that source stability is harmful or that a particular support will improve outcomes.

Respondents mostly reported clear instructions. Remaining feedback included tool discovery overhead, checkpoint/trial terminology, care with the correction sign, and the original estimate remaining in a structured field alongside the corrected document. Preserve the original measurement for provenance, but distinguish it more clearly in a future version. Lack of disclosed likelihoods is intentional in discovery mode, rather than an interface defect to silently remove.

The private human 0.3 flow is running with **zero accepted human answers** at reporting time. Human usability, burden and carryover remain untested. Offline checks passed: the full 253-test Python suite plus the subsequently added complete synthetic-pilot regression (254 tests covered in total), Ruff, TypeScript type/format checks and 35 TypeScript tests. Consumer RPC coverage remains mocked; no new live Solana validation occurred.
