# Source learning: repeated configurations and presentation transfer

The frozen panel completed **16 fresh sessions, 576 forecast/decision checkpoints, 192 source judgments and 192 research choices** in 33 minutes 13 seconds. All planned sessions were retained, with no rejected submissions, answer retries or replacements. See the [protocol](source-panel.md) and [implementation validation](source-panel-validation-2026-09-26.md).

The strongest finding is a task-conditional difference in reproducibility: Astra's sparse repeats differed by about 2.8–2.9 probability points, and Sol's by about 10.8. Astra's reports also remained close to joint-process predictions across structured and prose presentations in the new environment. Configuration-specific fitting added no transfer benefit: Astra tied the shared profile and was slightly worse than the fixed joint observer; Sol's fitted profile was substantially worse than the shared profile. All candidate accounts failed Sol's declared adequacy screen.

This supports reporting scoped behavioral facts and variability, keeping sparse elicitation as the default, and testing a concrete verification benefit. It does not support distinct cognitive mechanism labels or a full epistemic phenotype.

## What was fixed before collection

The panel uses requested `gpt-6-astra` and `gpt-6-sol` aliases at medium reasoning effort. Each collection starts in a fresh process and retains its public history across 24 fictional companies and 36 forecast/decision checkpoints. Immutable model revisions are unverified; execution assurance is operator-asserted. The respondent has five public MCP tools and no file, shell, browser, memory, plugin or subagent access.

Eight sparse baseline collections cross the two configurations, two private source worlds and two fresh repeats. Four separate dense collections add source accuracy/selection questions in the same worlds. Four transfer collections cross both configurations with structured versus prose presentations in one third world. This is three distinct environments and sixteen starting contexts, not 576 independent agents. Each collection also contains twelve research choices; dense collections add 48 source judgments each.

The prose adapter preserves the public factual ledger, including priors, payoffs, ordered resolved source records, business rates, audit results and research costs. It changes how those facts are presented. The task still supplies numeric business rates and a bounded source-process structure; this is not unrestricted research or cross-domain transfer. Three factual comprehension questions appear after completion, identically in all conditions.

The configuration profiles use only the first twelve unaudited forecasts from their four sparse baseline collections (48 reports each). The shared profile uses the same subset from all eight (96 reports). These fits freeze before transfer. Every transfer prediction is then committed before its corresponding answer; no transfer probability enters either fit. Public histories and purchased audits may update the source observer as specified.

Primary comparisons use the first twelve forecasts, whose evidence is matched before research choices can change the path. Results over all 36 checkpoints are secondary, conditional on the research actually selected. The original collector's within-session fits remain diagnostics and are not the panel's transfer predictors.

## Repeated forecasts

The first twelve reports have the same evidence across matched contexts. Values below are RMS differences in probability points; the between-configuration comparison uses each configuration's mean over its two repeats.

| Source world | Astra repeat difference | Sol repeat difference | Difference between configuration means |
| --- | ---: | ---: | ---: |
| A | 2.87 | 10.82 | 8.01 |
| B | 2.83 | 10.78 | 6.87 |

Astra's reports were more reproducible in these two environments. Sol's variation across fresh repeats was larger than the difference between the configuration means in both environments. That makes a simple ranking or distinct trait label premature, even when a fitted model assigns the configurations to different families. These four repeat contrasts are descriptive; they are not a population reliability coefficient or a measure of general intelligence or decision quality.

## Additional source questions

Each dense context adds two source judgments on each of 24 companies. Compare its first twelve company probabilities with the mean of the two matched sparse contexts:

| Configuration / world | RMS difference, points | Mean signed change, points | Sparse repeat difference, points |
| --- | ---: | ---: | ---: |
| Astra / A | 1.22 | −0.13 | 2.87 |
| Astra / B | 2.20 | −0.25 | 2.83 |
| Sol / A | 7.70 | +0.88 | 10.82 |
| Sol / B | 8.68 | −2.13 | 10.78 |

The dense differences are smaller than the corresponding sparse repeat differences, and mean signed changes show no common shift across configurations/worlds. That does not establish equivalence or absence of an elicitation effect: each cell has only one dense context, and its comparison with a two-repeat mean is a different statistic from a pairwise repeat difference. The practical default remains sparse collection, with dense source judgments available for a specific diagnostic question. More questioning has not demonstrated a measurement or decision benefit here.

## Frozen calibration profiles

| Profile | Baseline reports | Preferred candidate | Best reporting gain within candidate |
| --- | ---: | --- | ---: |
| Astra | 48 | Joint source process | 0.70 |
| Sol | 48 | Flat accuracy | 0.85 |
| Shared | 96 | Joint source process | 0.70 |

The fit froze at **13:09:10 UTC**, before the dense and transfer collections. The joint-process observer distinguishes measurement error from selective reporting; flat accuracy treats reporting as one effective accuracy process. These labels describe comparisons among candidate predictors. They do not establish what algorithm either respondent used. In particular, calibration preference must be assessed against the separate, prospective transfer results before it is used in a passport.

The tested gain grid is 0.70–1.30. Astra and the shared fit reach its lower boundary; their preferred gain is therefore constrained by the model's support. Do not turn 0.70 into a precise estimate of conservatism or evidence weighting. Expanding the grid after seeing transfer results would be exploratory and would need fresh validation.

## Prospective transfer prediction

The primary result is RMSE against twelve new unaudited probability reports per context, in probability points. Lower means better prediction of the reports, not better decisions about actual company outcomes. Every comparator was locked before the response.

| Predictor | Astra structured | Astra packet | Sol structured | Sol packet |
| --- | ---: | ---: | ---: | ---: |
| Configuration fit | 5.37 | 4.71 | 15.31 | 18.34 |
| Shared fit | 5.37 | 4.71 | 11.03 | 10.01 |
| Fixed joint process | 5.19 | 4.58 | 13.71 | 12.71 |
| Fixed flat accuracy | 22.31 | 22.99 | 16.43 | 19.53 |
| Fixed discount | 20.73 | 21.08 | 12.36 | 17.95 |
| Configuration mean | 30.97 | 31.00 | 26.45 | 27.98 |
| Shared mean | 30.87 | 30.90 | 26.53 | 28.05 |
| Stated prior | 25.32 | 24.86 | 16.94 | 24.48 |

Astra's fitted and shared predictions coincide at displayed precision and have no advantage over the fixed joint observer in either format. Sol's configuration fit is worse than the shared prediction by 4.28 points in structured evidence and 8.34 in prose. Its calibration preference for flat accuracy therefore fails this new-environment prediction test. Neither result licenses assigning an internal inference algorithm.

The joint account's conditional adequacy screen is satisfied for Astra's twelve initial reports in both formats; flat accuracy and fixed discount fail. Every candidate fails for Sol in both formats. Each entry below shows **observed RMSE / declared 99% simulation boundary**, using each family's configuration-frozen gain distribution. These are conditional screens under the stated report-noise assumptions, not probabilities that a mechanism is true.

| Configuration / presentation | Joint process | Flat accuracy | Fixed discount |
| --- | ---: | ---: | ---: |
| Astra / structured | 5.37 / 5.90 (inside) | 22.06 / 6.47 (outside) | 21.30 / 6.39 (outside) |
| Astra / packet | 4.71 / 5.90 (inside) | 22.73 / 6.47 (outside) | 21.67 / 6.39 (outside) |
| Sol / structured | 11.03 / 5.90 (outside) | 15.31 / 6.83 (outside) | 12.38 / 6.38 (outside) |
| Sol / packet | 10.01 / 5.90 (outside) | 18.34 / 6.83 (outside) | 17.97 / 6.38 (outside) |

The matched structured-versus-packet difference is **1.55 points for Astra and 10.57 for Sol**. Astra's contrast is smaller than its baseline repeat differences; Sol's is comparable to its approximately 10.8-point baseline repeat differences. With one context per transfer presentation, this does not isolate a causal format effect or establish equivalence. The narrower defensible observation is that Astra's joint-process prediction accuracy held up in both tested presentations of this one new environment.

For completeness, secondary RMSE over all 36 checkpoints is:

| Predictor | Astra structured | Astra packet | Sol structured | Sol packet |
| --- | ---: | ---: | ---: | ---: |
| Configuration fit | 6.59 | 5.86 | 19.91 | 19.05 |
| Shared fit | 6.59 | 5.86 | 9.29 | 9.21 |
| Fixed joint process | 4.79 | 4.23 | 9.46 | 9.10 |
| Fixed flat accuracy | 24.64 | 24.38 | 20.09 | 19.22 |
| Fixed discount | 23.42 | 23.31 | 18.14 | 19.96 |
| Configuration mean | 34.06 | 33.76 | 32.26 | 33.10 |
| Shared mean | 34.12 | 33.82 | 32.23 | 33.05 |
| Stated prior | 26.53 | 26.04 | 22.30 | 26.33 |

Later predictions are conditional on the research actually chosen. Structured and packet sessions can choose different checks and subsequently see different evidence, so these errors cannot isolate wording effects. The fixed joint observer remains competitive; individualized fitting still supplies no useful improvement over the relevant shared/simple alternatives in this panel.

The original collector also fits each session's first twelve reports and predicts its later 24. **All three candidates fall outside that separate within-session adequacy screen in 15 of 16 sessions**; Astra / world B / dense is the exception. These local fits are diagnostics, not the transfer predictor above. Their widespread failures further restrict the successful Astra transfer observation to its stated prediction task and discourage stable gain or mechanism claims.

## Decisions, outcomes and research

All **576/576 decisions** were consistent with the submitted probability and the stated investment threshold. This establishes report/action consistency within the task, not correct underlying probabilities. Resolved-outcome Brier scores and realized fictional payoff are shown separately below; each row covers 24 companies and twelve research decisions. Lower Brier is better, while higher payoff is better under this task's particular incentives. Payoff includes purchased research costs.

| Collection | Final Brier | Fictional payoff | Customer panels | Selection audits | Measurement audits | Stop |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| astra-a-dense-1 | 0.1258 | 4.210 | 6 | 1 | 1 | 4 |
| astra-a-sparse-1 | 0.1142 | 4.910 | 6 | 2 | 0 | 4 |
| astra-a-sparse-2 | 0.1101 | 5.205 | 7 | 1 | 0 | 4 |
| astra-b-dense-1 | 0.1394 | 2.295 | 4 | 1 | 0 | 7 |
| astra-b-sparse-1 | 0.1352 | 2.995 | 4 | 1 | 0 | 7 |
| astra-b-sparse-2 | 0.1393 | 2.290 | 5 | 0 | 0 | 7 |
| astra-transfer-packet | 0.1015 | 4.960 | 4 | 1 | 1 | 6 |
| astra-transfer-structured | 0.0974 | 4.980 | 3 | 1 | 2 | 6 |
| sol-a-dense-1 | 0.1459 | 3.500 | 10 | 0 | 0 | 2 |
| sol-a-sparse-1 | 0.1366 | 4.505 | 7 | 1 | 0 | 4 |
| sol-a-sparse-2 | 0.1545 | 3.300 | 11 | 0 | 0 | 1 |
| sol-b-dense-1 | 0.1353 | 2.290 | 5 | 0 | 0 | 7 |
| sol-b-sparse-1 | 0.1536 | 1.990 | 5 | 0 | 0 | 7 |
| sol-b-sparse-2 | 0.1490 | 2.290 | 5 | 0 | 0 | 7 |
| sol-transfer-packet | 0.1061 | 6.395 | 4 | 1 | 0 | 7 |
| sol-transfer-structured | 0.0968 | 5.995 | 2 | 5 | 0 | 5 |

Sol earned higher realized payoff in both transfer presentations despite being harder for the candidate models to describe. Model inadequacy is not a performance ranking. These are a few shared generated worlds, research paths differ, and no buyer policy or intervention was compared. The one-company research-value diagnostic excludes future value from learning about a recurring source and is not a general optimality score. The research-menu ambiguity below is an additional limit on interpreting choices.

## Comprehension and usability

All sixteen completion messages answered the same three questions correctly: company demand is revealed after the final answer, source audits carry forward, and accurate measurement does not imply random selection. This was an operator review of 48 factual answers, not an independent assessment of general understanding.

Recurring feedback identifies concrete improvements:

- State before purchase what each research option reveals and its reliability/independence, while leaving the selected source's unknown process undisclosed.
- Define measurement accuracy as the per-customer quantity being estimated. Describe the audit's scope without revealing the source's answer in advance.
- Make the newly resolved company outcome easier to notice after a final submission; it currently requires history or later archives.
- Explain the retained revision checkpoint after choosing stop, and distinguish the provisional from the final decision.
- Reduce repetitive packet reading without removing access to the full public history. Both packet respondents flagged length.

The packet and structured conditions were left unchanged during collection. Any future wording, evidence-access or checkpoint change needs its own version review and recovery/acceptance checks. Actual human usability remains pending; these are agent reports of friction.

## Resulting delivery decisions

1. **Keep sparse collection as the default.** Offer dense judgments for a defined diagnostic purpose; do not claim that adding questions has improved measurement.
2. **Expose observed repeatability and coverage in a scoped passport evidence adapter.** Preserve configuration, presentation, denominators, source evidence and the distinction between descriptive behavior and model adequacy. Do not issue Sol's flat-accuracy label, Astra's fitted gain or a general reliability ranking as traits.
3. **Clarify research semantics before testing verification value.** The next empirical comparison should evaluate one fixed verification/support choice against no verification, always verify and a simple current-confidence policy, on new matched cases. Report errors, cost and latency separately until a buyer supplies loss weights. A profile-augmented policy must earn incremental value over these alternatives.
4. **Keep model development bounded.** Use these results to formulate a specific explanation of residuals or changing behavior, then test it on fresh evidence if it matters to the buyer decision. Retain fixed/shared prediction as the baseline. Neither widening the gain grid after the fact nor adding arbitrary parameters turns this panel into confirmation.

A design-partner assessment can proceed alongside this work. No customer demand, paid purchase, support benefit or general passport phenotype has been established. See the [updated roadmap](mvp.md) and [decision-value plan](decision-value-pilot.md).

## Execution, validation and commitments

The panel finished at **13:28:02 UTC** on 26 September 2026. Total wall time was **1,993.18 seconds** with two sessions at a time; individual collections ranged from 138.84 to 384.11 seconds. Known processed usage was **20,106,839 tokens**: 20,023,318 input (including 19,096,576 cached) plus 83,521 output. All sixteen attempts have usage records. Monetary cost under the existing account is unknown. The declared 40-million-token admission boundary, 900-second per-run limit and 5,400-second panel limit were not reached.

All 1,251 recorded calls used the allowed public MCP interface. There were no tool errors, rejected submissions, answer retries, substitutions, case exclusions or missing attempts. All sixteen CLI launches emitted the same development-feature warning about disabling host skill discovery; these warnings are retained in the private execution records. They were not response or transport failures.

The exported evidence verifies all 576 public presentation locks and all 144 external transfer predictions, their timing before answers, the frozen profile bindings and the exact training-report hashes. The original task fingerprint and the panel implementation remain unchanged. Before collection, both declared recovery seeds passed; repository checks passed **321 Python tests, 37 TypeScript tests, Ruff lint/format and TypeScript type/format checks**. Solana RPC tests remain mocked; this panel made no validator or live-network transaction.

| Private artifact commitment | SHA-256 |
| --- | --- |
| Precollection plan | `992b180342f72583186b6144a60b737b4c29560019495259bee6cf33f042985f` |
| Frozen configuration/shared profiles | `4da77364b88ab7d2d28f2847ec2e1515a06a28750d9e91ee078458b6f12e3626` |
| Verified comparison summary | `cdb3ec5768b18a43a0309ecc10b50bd31be4bba24897192b3dd38581bd07bef5` |
| Execution and usage accounting | `83fcd70b502bfcd9cdc0c92b7c3752d96e333dcabc4ef4b9082f07362a25a46c` |

Panel implementation: `8ecfeca196c023826fe0c461ca4a4e54c1d68094269d8d9548921f46ad41676d`. These are operator-created commitments, not independent preregistration, execution attestation or identity verification. Private seeds, prompts, source truth, individual reports and logs remain outside Git.

## Interpretation boundaries

Report-prediction error, resolved-outcome accuracy, action consistency and buyer value are different measurements. A lower error against elicited probabilities does not establish better company decisions or access to internal beliefs. Conditional model weights compare only the three implemented accounts; reporting gain is not a stable cognitive trait. The adequacy screen uses the declared noise process and a simulated 99th-percentile boundary, not a calibrated composite-model test.

Two baseline worlds and one transfer world do not support population confidence intervals, stable model rankings or broad cognitive labels. The transfer world has no same-format repeats. Dense questions change both prompting and reporting burden. Later research choices can change the evidence respondents receive. Phase order was fixed, so provider drift cannot be estimated separately.

No support intervention, buyer verification policy, human usability session, passport issuance, registry write or payment is part of this panel. The [decision-value roadmap](decision-value-pilot.md) governs the next step.
