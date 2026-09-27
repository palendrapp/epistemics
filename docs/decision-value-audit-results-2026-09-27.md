# Decision-value and calibration audit results — 27 September 2026

**Later on 27 September:** after the [literature review](literature-review-2026-09-27.md), the calibration-focused comparison proposed below became the explicit control arm of a [naturalistic disclosure/shared-origin pilot](decision-value-pilot.md#2b-naturalistic-disclosure-and-shared-origin-pilot). Collection-cost reduction still comes first. The "Strategy update" section records the proposal as it stood when this audit completed.

**The existing task contains useful verification opportunities. Its earlier two-world realized-loss result does not establish that selective checking has negative expected value.** The [frozen offline plan](decision-value-audit-plan-2026-09-27.md) completed **1,024 independent worlds / 12,288 later-company cases** with eight synthetic reporters and three policies. No respondent account usage or new agent collection was needed. The [specification](decision-value-audit.md) gives the mathematical model and information boundaries.

The known-process oracle gained **0.015058 points/company in expectation** from selective checking; the rounded public observer gained **0.015495**, with a 95% Monte Carlo interval of **[0.014969, 0.016021]**. Both exceeded the earlier .01 design target. Nevertheless, **139/512 two-world pairs (27.15%) produced a negative realized contrast for each reference**. These are marginal frequencies, not necessarily the same losing pairs and not probabilities that the original experiment was “just bad luck.” They explain why repeating the same two worlds is a weak test of population benefit.

Always buying the check remained unattractive: expected gains were −0.047184 for the oracle and −0.046214 for rounded public. We should keep the cost-aware question, move toward more independent worlds, and separate forecast calibration, final decision quality and incremental assistance benefit. This audit does not validate benefit for a real agent or open a passport release gate.

## Expected and realized results

Every contrast below compares a synthetic reporter with its own no-check baseline. Sample incorporation is Bayesian by construction. Expectations integrate both company states and all six possible independent-panel counts; realizations use actual generated states and panels. Intervals and sampling frequencies concern this simulator only.

| Reporter | Checks bought | Expected selective gain | Realized selective gain | Expected always-check gain | Two-world selective loss frequency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Known-process oracle | 31.54% | 0.015058 | 0.014665 | -0.047184 | 27.15% |
| Rounded oracle | 31.54% | 0.015058 | 0.014665 | -0.047184 | 27.15% |
| Public observer | 33.11% | 0.015494 | 0.016444 | -0.046232 | 26.76% |
| Rounded public | 33.01% | 0.015495 | 0.016272 | -0.046214 | 27.15% |
| Underconfident control | 42.76% | 0.016479 | 0.017302 | -0.044352 | 25.59% |
| Overconfident control | 21.31% | 0.013686 | 0.014021 | -0.048663 | 30.86% |
| Optimistic control | 29.80% | 0.018399 | 0.019169 | -0.040056 | 20.90% |
| Pessimistic control | 29.63% | 0.018817 | 0.018572 | -0.039587 | 23.24% |

The two-world loss fraction has a binomial Monte Carlo standard error of about 1.97 percentage points for both oracle and rounded public. Outcomes and prices were paired across reporters and policies. Repeated conditions do not multiply the 1,024 independent worlds.

| Batch seed | Oracle expected gain | Oracle realized gain | Rounded-public expected gain | Rounded-public realized gain |
| --- | ---: | ---: | ---: | ---: |
| 20260927 | 0.014953 | 0.014536 | 0.015526 | 0.016219 |
| 20270927 | 0.015163 | 0.014793 | 0.015464 | 0.016325 |

Both independently seeded batches gave positive expected and realized gains for these references. Oracle starting-report rounding happened to leave selective purchases and actions unchanged on these cases. This is not a general guarantee about response grids.

## Improvement is not final decision quality

A worse starting decision creates more room for a check to help. The optimistic and pessimistic controls therefore show larger improvement than the oracle, while still making worse final decisions. Likewise, the public observer’s slightly larger gain does not mean it outperforms the oracle. The absolute expected net payoff and regret make the distinction explicit.

| Reporter | Expected no-check net | Expected selective net | Purchase regret | Action regret | Total regret versus oracle optimum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Known-process oracle | 0.173282 | 0.188340 | 0.000000 | 0.000000 | 0.000000 |
| Rounded oracle | 0.173282 | 0.188340 | 0.000000 | 0.000000 | 0.000000 |
| Public observer | 0.171064 | 0.186558 | 0.000536 | 0.001246 | 0.001782 |
| Rounded public | 0.171024 | 0.186520 | 0.000539 | 0.001282 | 0.001821 |
| Underconfident control | 0.168422 | 0.184901 | 0.000909 | 0.002530 | 0.003439 |
| Overconfident control | 0.171988 | 0.185674 | 0.001764 | 0.000902 | 0.002666 |
| Optimistic control | 0.161824 | 0.180222 | 0.002051 | 0.006067 | 0.008118 |
| Pessimistic control | 0.161386 | 0.180203 | 0.001896 | 0.006241 | 0.008137 |

Purchase regret holds final actions optimal and changes only whether a check was bought. Action regret holds the purchase fixed and changes actions. These diagnostic quantities compare with a privileged reference, not an identified cognitive mechanism. All components were nonnegative within numerical tolerance.

## Starting calibration and source-information uncertainty

The oracle knows the source process; the public observer learns it from visible records under the existing 25-state prior. Differences from the oracle mix information limitations, modeling choices and reporting distortion. They are not all calibration failures.

| Reporter | RMSE from privileged probability (pp) | Expected ten-bin absolute calibration gap (pp) | Empirical ten-bin gap (pp) |
| --- | ---: | ---: | ---: |
| Known-process oracle | 0.000 | 0.000 | 0.946 |
| Rounded oracle | 0.269 | 0.094 | 0.851 |
| Public observer | 6.058 | 0.528 | 0.493 |
| Rounded public | 6.062 | 0.468 | 0.614 |
| Underconfident control | 8.006 | 7.108 | 6.974 |
| Overconfident control | 6.854 | 5.716 | 5.851 |
| Optimistic control | 12.014 | 9.802 | 9.768 |
| Pessimistic control | 12.006 | 9.805 | 9.840 |

The diagnostic distinguishes all four deliberately distorted controls from the calibrated oracle. The public observer differs from the oracle by about six probability points RMS while exhibiting a much smaller binned calibration gap. That is exactly why those quantities must remain separate. Ten bins can hide within-bin errors; empirical absolute gaps have finite-sample upward bias. The small public gap is conditional on this generator, which differs from the observer’s uniform prior. It is not evidence that any real agent is calibrated. No new cognitive parameter or calibration correction was fitted.

## Where the opportunities are

| Pre-outcome group | Cases | Fraction of all cases | Oracle expected selective gain | Rounded-public expected selective gain |
| --- | ---: | ---: | ---: | ---: |
| Price .01 | 4,096 | 33.33% | 0.029462 | 0.030502 |
| Price .04 | 4,096 | 33.33% | 0.015713 | 0.015983 |
| Price .20 | 4,096 | 33.33% | 0.000000 | 0.000000 |
| Public predicted net EVSI ≤ 0 | 8,232 | 66.99% | 0.000407 | 0.000000 |
| Public predicted net EVSI between 0 and .01 | 597 | 4.86% | 0.007687 | 0.004031 |
| Public predicted net EVSI ≥ .01 | 3,459 | 28.15% | 0.051199 | 0.054350 |

Price groups and public-opportunity groups are two separate partitions. The public rule buys no .20 checks. Cases with publicly predicted net EVSI at least .01 comprise **28.15%** of the population and have rounded-public expected gain **0.054350 points/case**. This is a useful pre-outcome recruitment stratum, not a license to select favorable realized draws. If a later design oversamples it, report stratum-specific findings and preserve declared weights for any full-population claim.

The simulated world-level variability implies roughly **225 oracle worlds or 246 rounded-public worlds** for a normal realized-contrast half-width of .005. This is a precision illustration under these fixed synthetic policies, not a power calculation for real respondents. It makes a large realized-payoff confirmation through the current expensive interface unattractive as the immediate next step.

## Exploratory application to the completed agent runs

**This section was specified after the main simulator audit.** It is additional diagnosis, not part of the frozen audit or a new success gate. Original accepted answers and prior results are unchanged.

Apply the exact expectation calculation to each recorded selective starting report, holding its actual purchase rule and provisional action. This benchmark assumes Bayesian payoff-maximizing actions for every possible future panel. Earlier analysis found close agreement on the panels actually delivered, but unobserved branches remain hypothetical. Consequently these are **model-based conditional benchmark values, not measured expected agent-policy values**.

| Configuration | Conditional benchmark expected within-trajectory gain | Actual realized within-trajectory gain | Starting-report RMSE from oracle (pp) | Starting-report RMSE from public observer (pp) |
| --- | ---: | ---: | ---: | ---: |
| Astra | 0.024564 | -0.051667 | 13.117 | 8.974 |
| Sol | 0.025994 | -0.004792 | 13.685 | 10.059 |

These within-trajectory gains differ from the original across-context primary contrasts because they compare against each selective context’s own provisional action. There are only 24 distinct companies, each repeated twice per configuration. Reference disagreement here cannot establish a stable bias, and there is insufficient independent coverage to validate calibration.

On original world B, even the simulated oracle has **positive expected gain (+0.015807)** but **negative realized gain (−0.060833)**. On world A, the rounded public observer has expected gain **+0.038709** and realized gain **−0.018333**. Thus the original worlds contain clear examples of favorable expected purchases followed by unfavorable realized draws. This makes sample luck a plausible contributor; it does not prove that all observed agent losses are explained by luck or remove the need to examine starting reports.

## Strategy update

1. **Keep the task and selective-check hypothesis.** The simulator supports useful, attainable opportunities. Another broad personality battery or a new slow-updating mechanism is not the immediate fix.
2. **Make the next respondent question narrower:** do starting reports track publicly supported uncertainty, and where do they depart consistently? Score calibration, privileged-reference loss and absolute decision quality separately. Keep conditional continuation benchmarks explicitly model-dependent.
3. **Use more independent worlds and fewer repeated copies.** Preserve a small repeatability check. Select or stratify opportunities from public inputs before outcomes; include low-opportunity controls and disclose population weights.
4. **Reduce collection cost before another panel.** Avoid repeated full protocol/archive transmission, while retaining readable public history, outcome timing, human/MCP parity, immutable answers and a version-reviewed acceptance. Then freeze the bounded calibration-focused plan and accounting limits. Do not scale directly to hundreds of expensive contexts to force a realized-payoff result.
5. **Retain realized payoff as an outcome, with appropriate uncertainty.** A successful calibration diagnosis is not demonstrated intervention benefit, and a larger improvement is not necessarily a better agent. Passport-guided allocation, personalization and economic benefit remain unvalidated.

No new respondent panel was launched. Interface simplification, actual human usability and design-partner work remain useful parallel product milestones.

## Validation and commitments

The implementation and frozen plan were [committed and pushed before main execution](https://github.com/palendrapp/epistemics/commit/889bd85). All 1,024 planned worlds completed; none was excluded or replaced. The full repository passes **373 Python tests and 40 TypeScript tests**, Ruff/format, TypeScript and Biome checks. Initial sandbox runs could not bind localhost; complete reruns with loopback access passed. RPC coverage is mocked; no validator, live-network or payment validation occurred.

An independent calculation by the same operator reconstructed source likelihoods, public-history mixtures, every reporter/policy payoff and regret, aggregate means/standard deviations, two-world loss counts and calibration gaps. Maximum probability disagreement was 9.22×10⁻¹⁵; maximum world-metric disagreement 1.12×10⁻¹⁶. This is not an external execution attestation. Evaluator-side cases and ledgers remain outside Git. Existing blanket/selective implementation fingerprints and the main report contract remain unchanged.

| Artifact | SHA-256 |
| --- | --- |
| Audit implementation | `3d319809603942f47a6bfb96d2640d04cbdba92779c667706524d9de443ec39b` |
| plan.json | `bf3240c334dcedf1df460392758e10c09fdb2da07e19484afb1e3d3b2d9dfe97` |
| cases.json | `3ea0c119bc550455d3fbf75699202a0bcf585c52756f49507621dbbe5790c8fb` |
| worlds.json | `7e03b4d672bc0cd07ca794cb3396335248a1ff856a753ac014d713bf78b8809e` |
| summary.json | `0140128b1da9928d331b2d515ac281f8515daf513542fb3a075aa135f2552fa8` |
| operator-audit.json | `7240adeeddf9726033e26d5edfcf827f5cea8b271bda4ac3d84cfcdd775d32b7` |
| archived-diagnostic.json (exploratory) | `b8602bf435d849a61618bcb6b11dbbc2288a7f4a9ee3832c899181fd9553743d` |
