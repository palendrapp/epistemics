# Cost-aware verification results — 26 September 2026

**Selective verification reduced check expenditure by 92.375% and beat always-check in every matched repeat, but lost to no-check in every matched repeat. Both configurations failed the predeclared benefit gate.** This is a completed negative feasibility result, not evidence that verification cannot help.

Completed the [frozen repeated comparison](cost-aware-plan-2026-09-26.md) of the [0.2 collector](cost-aware-verification.md). These are whole-policy trajectories in a controlled fictional task. Policies were disclosed at the start; results include anticipation and carryover. No profile-personalized rule was tested.

## Primary outcomes

Net fictional points per later company, averaged over two context repeats in each of two new worlds. Every world has equal weight. Lower final Brier is better; higher net payoff is better.

| Requested configuration | No check net | Always check net | Cost-aware net | Cost-aware − none | Cost-aware − always | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Astra, medium | 0.227083 | 0.125000 | 0.190000 | -0.037083 | +0.065000 | Fail |
| Sol, medium | 0.200000 | 0.131250 | 0.188958 | -0.011042 | +0.057708 | Fail |

The gate requires cost-aware to gain at least 0.01 points/company versus no check on average, to be nonnegative versus no check in both worlds, and to be nonnegative versus always-check in both worlds. Gates use repeat means and are applied separately to each configuration. Passing is a development signal, not a population claim or deployable passport policy.

| Configuration/world | Cost-aware − none, repeat 1 | Repeat 2 | Repeat mean | Cost-aware − always, repeat mean |
| --- | ---: | ---: | ---: | ---: |
| Astra / A | -0.042500 | -0.042500 | -0.042500 | +0.049167 |
| Astra / B | -0.060833 | -0.002500 | -0.031667 | +0.080833 |
| Sol / A | -0.018333 | -0.017500 | -0.017917 | +0.036250 |
| Sol / B | -0.005833 | -0.002500 | -0.004167 | +0.079167 |

## All contexts and secondary outcomes

Only the twelve later companies contribute to each row. The first twelve company forecasts provide source-learning history. Checks are evaluator assignments; the counts do not measure voluntary research preferences.

| Configuration | World | Policy | Repeat | Net/company | Gross/company | Final Brier | Checks/12 | Total check cost | False acceptance | Missed opportunity | Changed decisions |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Astra | A | none | 1 | 0.200000 | 0.200000 | 0.110583 | 0 | 0.000 | 2 | 1 | 0 |
| Astra | A | none | 2 | 0.200000 | 0.200000 | 0.114792 | 0 | 0.000 | 2 | 1 | 0 |
| Astra | A | always | 1 | 0.108333 | 0.191667 | 0.083708 | 12 | 1.000 | 2 | 0 | 3 |
| Astra | A | always | 2 | 0.108333 | 0.191667 | 0.087500 | 12 | 1.000 | 2 | 0 | 3 |
| Astra | A | cost_aware | 1 | 0.157500 | 0.166667 | 0.141733 | 5 | 0.110 | 2 | 1 | 2 |
| Astra | A | cost_aware | 2 | 0.157500 | 0.166667 | 0.139050 | 5 | 0.110 | 2 | 1 | 2 |
| Astra | B | none | 1 | 0.283333 | 0.283333 | 0.073600 | 0 | 0.000 | 0 | 0 | 0 |
| Astra | B | none | 2 | 0.225000 | 0.225000 | 0.079008 | 0 | 0.000 | 1 | 0 | 0 |
| Astra | B | always | 1 | 0.141667 | 0.225000 | 0.111142 | 12 | 1.000 | 1 | 0 | 2 |
| Astra | B | always | 2 | 0.141667 | 0.225000 | 0.106117 | 12 | 1.000 | 1 | 0 | 1 |
| Astra | B | cost_aware | 1 | 0.222500 | 0.225000 | 0.121517 | 3 | 0.030 | 1 | 0 | 1 |
| Astra | B | cost_aware | 2 | 0.222500 | 0.225000 | 0.121042 | 3 | 0.030 | 1 | 0 | 1 |
| Sol | A | none | 1 | 0.175000 | 0.175000 | 0.119158 | 0 | 0.000 | 2 | 2 | 0 |
| Sol | A | none | 2 | 0.175000 | 0.175000 | 0.136925 | 0 | 0.000 | 2 | 2 | 0 |
| Sol | A | always | 1 | 0.108333 | 0.191667 | 0.076708 | 12 | 1.000 | 2 | 0 | 3 |
| Sol | A | always | 2 | 0.133333 | 0.216667 | 0.075250 | 12 | 1.000 | 1 | 0 | 5 |
| Sol | A | cost_aware | 1 | 0.156667 | 0.166667 | 0.121917 | 6 | 0.120 | 2 | 1 | 4 |
| Sol | A | cost_aware | 2 | 0.157500 | 0.166667 | 0.163733 | 5 | 0.110 | 2 | 1 | 2 |
| Sol | B | none | 1 | 0.225000 | 0.225000 | 0.086175 | 0 | 0.000 | 1 | 0 | 0 |
| Sol | B | none | 2 | 0.225000 | 0.225000 | 0.088292 | 0 | 0.000 | 1 | 0 | 0 |
| Sol | B | always | 1 | 0.141667 | 0.225000 | 0.108750 | 12 | 1.000 | 1 | 0 | 1 |
| Sol | B | always | 2 | 0.141667 | 0.225000 | 0.113442 | 12 | 1.000 | 1 | 0 | 2 |
| Sol | B | cost_aware | 1 | 0.219167 | 0.225000 | 0.140342 | 4 | 0.070 | 1 | 0 | 2 |
| Sol | B | cost_aware | 2 | 0.222500 | 0.225000 | 0.140400 | 3 | 0.030 | 1 | 0 | 3 |

## Context repeatability

Absolute differences between two fresh contexts on identical cases/prices. These repeats reveal response variability; they do not create additional independent company worlds or identify a cognitive mechanism.

| Configuration/world | Policy | Final probability mean absolute difference (pp) | Absolute net-payoff difference/company | Check disagreements/12 |
| --- | --- | ---: | ---: | ---: |
| Astra / A | none | 1.417 | 0.000000 | 0 |
| Astra / A | always | 0.917 | 0.000000 | 0 |
| Astra / A | cost_aware | 1.000 | 0.000000 | 0 |
| Astra / B | none | 1.417 | 0.058333 | 0 |
| Astra / B | always | 1.083 | 0.000000 | 0 |
| Astra / B | cost_aware | 0.417 | 0.000000 | 0 |
| Sol / A | none | 4.667 | 0.000000 | 0 |
| Sol / A | always | 2.583 | 0.025000 | 0 |
| Sol / A | cost_aware | 6.667 | 0.000833 | 1 |
| Sol / B | none | 0.667 | 0.000000 | 0 |
| Sol / B | always | 1.583 | 0.000000 | 0 |
| Sol / B | cost_aware | 2.583 | 0.003333 | 1 |

## Exploratory decision diagnostic

The following analysis was specified **after seeing the primary results**. It adds no new gate, changes no accepted answer, and excludes no context.

Selective checking bought 16/48 offered checks for Astra and 18/48 for Sol, versus 48/48 under always-check for each. Total selective costs were 0.28 and 0.33 fictional points, compared with 4.00 each under always-check: reductions of 93.0% and 91.75% respectively. It solved much of the expenditure problem, but did not improve gross payoff over no-check on these cases. Cost-aware final Brier was also worse than no-check in every matched repeat. Always-check improved Brier in world A and worsened it in world B, so the earlier accuracy benefit did not persist across these new worlds.

For every **actually supplied** sample, calculate the Bayesian posterior from the respondent's preceding rounded probability and the stated five-customer likelihood. All **130/130 final decisions following checks** matched the payoff-maximizing action under that conditional benchmark. Mean absolute posterior-report differences were 0.245 pp (Astra always), 0.390 pp (Astra selective), 0.283 pp (Sol always) and 0.242 pp (Sol selective); the largest individual difference was 0.833 pp. These numerical discrepancies are small relative to the one-percentage-point reporting grid. This supports conditional sample incorporation in this interface, not identification of an internal Bayesian mechanism or proof that the starting reports were calibrated.

The observed cost-aware-minus-none difference can be separated algebraically into (a) cost-aware final minus provisional gross payoff, (b) charged cost, and (c) cost-aware provisional gross minus no-check final gross. The last component includes anticipation, carryover and context variation; this decomposition does not causally identify those effects.

| Configuration | Within-trajectory gross revision | Check-cost component | Provisional-trajectory component | Total net contrast |
| --- | ---: | ---: | ---: | ---: |
| Astra | -0.045833 | -0.005833 | +0.014583 | -0.037083 |
| Sol | +0.002083 | -0.006875 | -0.006250 | -0.011042 |

Under selective checking, Astra had six changed decisions following samples: two improved realized gross payoff and four harmed it. Sol had eleven: seven improved payoff and four harmed it. Crucially, **all eight harmful changes concern only two distinct companies**, one per world, each seen by both configurations and both repeats. Nine beneficial changes concern five distinct companies. A correctly incorporated fallible sample can worsen a realized decision; repeating the same adverse draw does not supply independent evidence of bad updating. This dataset cannot separate unlucky sample realizations from miscalibration of the starting probabilities or establish the policy's expected population value.

No unpurchased sample was used to invent a respondent answer, and no selective trajectory was assembled from always-check responses. The benchmark is a diagnostic calculation conditional on recorded reports, not a counterfactual agent trajectory.

## Collection and accounting

All 24 contexts and 864 checkpoints completed. There were 864 submit calls and 0 rejected/failed tool calls. No context was automatically retried or substituted. Accepted answers remain immutable. Main wall time: 2808.251 seconds (46 minutes 48 seconds).

Known input tokens: 22,519,126, including 21,309,952 cached; output: 94,499; processed input + output: 22,613,625. Unknown-usage attempts: 0. Cached input is included in total input, not added again. Marginal account billing in money is unknown. Fictional check costs are separate from evaluation compute costs.

Acceptance accounting is separate in the frozen plan. The two confirmation worlds are shared across both configurations: the primary data contain 24 distinct later company cases, repeated across contexts. Neither 864 checkpoints nor 288 later company evaluations is the independent sample size. Exact provider model revisions remain unverified; identity/configuration/execution assurance remain distinct.

Independent operator audit revalidated every completed exact-byte artifact, recomputed expected sample value using rational arithmetic, reconstructed every action, checked price balance and matched worlds, and independently recalculated all realized charges, net/gross payoffs and Brier scores. It also independently recomputed repeat contrasts, repeatability measurements and the fixed gates. It is not an external execution attestation. Raw worlds, answers, private configurations and transcripts remain outside Git.

All **96/96 completion answers** were correct on operator semantic review: assignment rule, demand-revelation timing, sample fallibility and charging when declining. Recurring friction concerned repeated protocol/archive text, distinguishing checkpoint IDs from source IDs, offered versus charged costs, and the provisional/final distinction. One respondent flagged whole-percentage rounding; another noted the intentional inability to edit accepted answers. No context was excluded on this basis. Agent comprehension is not actual human usability evidence.

The implementation passed 358 Python tests, all 40 TypeScript tests, lint/format/type checks and [remote CI at the implementation commit](https://github.com/palendrapp/epistemics/actions/runs/36265444514). Original experimental versions and source report contracts remain unchanged; no transaction or payment was performed.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation | `6de0cedddc97d4f74507badee93d430970eb4bd01135d748a21f7096d4481367` |
| plan.json | `f4760dc7321cd556a31af90b83f38ccf74e8a3ca315c04290c02bdc5395f287e` |
| summary.json | `9790df9cff2dd7dbce7456c6f65cc60d18adaf2f246f982216cbcc91b8bc16ce` |
| execution.json | `888fa1a52f386ad07275136e68c3e4fb05cc739f085c2594cf293706ec5384b6` |
| operator-audit.json | `e9ae588a7c67196a18d11d7a20197ade70b500f08c3d7a3cb4fc3f7e133c7742` |
| comprehension-review.json | `cda028c985a5449489fcd44deefd0e42d9207d8cdccda79c3b4063009d5f9028` |
| exploratory-diagnostic.json | `83870814b3091999ce88a9fefd10150486bb2aa392935cbd82e47ed7f9c2d7bd` |

## Interpretation and next step

The release boundary stays closed: no validated verification benefit, no stable cognitive trait and no passport-guided allocation claim. The evidence does support a narrow observation: these configured respondents incorporated the provided sample consistently with their preceding numerical reports, while economical selection still failed the realized-payoff criterion on these two worlds.

**Next: audit decision-value opportunities and starting-report calibration before more account-backed collection.** Use inexpensive evaluator-side analysis over many independently drawn worlds to compare the known-generator oracle, the public-information observer and the report-based rule. Separate expected information value from realized sample luck, establish where useful checks are available at the offered prices, and use synthetic calibrated/miscalibrated observers to test the diagnostic. An oracle knowing the source process must be labeled as an upper-information reference, not information the participant possessed.

Then, only if that audit supports a useful and measurable comparison, freeze a smaller policy comparison on more independent worlds, reallocating effort from repeated copies of the same cases. Retain a bounded repeat check and fix opportunity strata using information available before company outcomes and check realizations. Do not select worlds because their realized samples improve decisions, tune a policy to these two adverse companies, or run a larger personality battery to compensate for this failure. This expected-value/calibration audit and any subsequent respondent collection remain roadmap work.

Interface simplification, actual human usability and design-partner preparation remain parallel product work. The next evidence question is whether reported uncertainty can usefully guide this purchase; whether an identity-linked passport adds value comes after that.
