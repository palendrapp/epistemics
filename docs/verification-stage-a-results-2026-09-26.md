# Verification-value Stage A results — 26 September 2026

The [frozen eight-context comparison](verification-stage-a-plan-2026-09-26.md) is complete. Two requested configurations, two new worlds and two assigned policies produced 288 checkpoints across 192 company evaluations. The primary analysis uses only the 96 later-company evaluations: twelve per context, representing 24 unique later companies across two generated worlds and four configuration/world contrasts. The separate acceptance contexts are excluded.

**Always buying verification improved Brier in all four contrasts but reduced net payoff in all four. Neither configuration passed the frozen feasibility gate.** This is a result about the imposed verification policy and this task's prices, not a finding that the agents voluntarily overspend on research.

## Primary result

Values below are mean net fictional points per later company. The difference is always buying the independent sample minus no additional check. All sample costs are included, including when the final action is to decline.

| Configuration | World | No check | Always check | Net gain | Gross gain | Brier change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Astra | A | 0.14167 | 0.03333 | -0.10833 | -0.02500 | -0.01253 |
| Astra | B | 0.25833 | 0.22500 | -0.03333 | +0.05000 | -0.15909 |
| Sol | A | 0.11667 | 0.03333 | -0.08333 | +0.00000 | -0.01699 |
| Sol | B | 0.25833 | 0.22500 | -0.03333 | +0.05000 | -0.20268 |

Lower Brier is better. Gross and net payoff answer different questions: whether the final actions earned more, and whether they earned enough to cover the checks.

| Configuration | Mean net gain across worlds | Nonnegative in both worlds | Predeclared feasibility gate |
| --- | ---: | --- | --- |
| Astra | -0.07083 | No | Fail |
| Sol | -0.05833 | No | Fail |

The gate was fixed at a mean gain of at least 0.01 and nonnegative gains in both worlds. It is a small development screen, not certification or a population estimate. No cases, failures or policy outcomes were removed to improve it.

## Secondary observations

| Configuration | World | Policy | Final Brier | False acceptances | Missed opportunities | Decisions changed after provisional answer | Checks |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Astra | A | none | 0.08911 | 1 | 1 | 0 | 0 |
| Astra | A | always | 0.07657 | 1 | 2 | 1 | 12 |
| Astra | B | none | 0.19818 | 2 | 2 | 0 | 0 |
| Astra | B | always | 0.03909 | 0 | 2 | 4 | 12 |
| Sol | A | none | 0.09764 | 2 | 1 | 0 | 0 |
| Sol | A | always | 0.08065 | 1 | 2 | 1 | 12 |
| Sol | B | none | 0.24565 | 1 | 3 | 1 | 0 |
| Sol | B | always | 0.04297 | 0 | 2 | 4 | 12 |

False acceptance means investing when demand resolved weak; missed opportunity means declining when it resolved strong. These realized categories do not establish that the ex ante probabilistic choice was irrational. Every always-check context paid 1.00 fictional point for twelve checks; each no-check context paid zero.

## Exploratory price breakdown

This breakdown was not a confirmation endpoint and is used only to interpret the completed outcomes. Each cell contains eight later-company evaluations per policy, pooled across the two worlds for one configuration. Price, company prior and other task features are coupled by the existing generator; differences between price groups cannot isolate a price effect. These are contrasts between complete collected policy trajectories, not a replay of an uncollected selective policy.

| Configuration | Check price | Gross gain/company | Net gain/company |
| --- | ---: | ---: | ---: |
| Astra | 0.01 | +0.07500 | +0.06500 |
| Astra | 0.04 | +0.00000 | -0.04000 |
| Astra | 0.20 | -0.03750 | -0.23750 |
| Sol | 0.01 | +0.03750 | +0.02750 |
| Sol | 0.04 | +0.07500 | +0.03500 |
| Sol | 0.20 | -0.03750 | -0.23750 |

## Execution and provenance

All eight contexts completed. Wall time: 830.659 seconds. Recorded input tokens: 6,822,264, including 6,515,840 cached; output tokens: 33,313; total processed: 6,855,577. Unknown-usage attempts: 0. Account marginal dollar cost is unknown. Acceptance used a separate 2,620,352 processed tokens and 192.250 seconds.

| Context | Seconds | Processed tokens |
| --- | ---: | ---: |
| astra-a-always | 223.524 | 1,137,226 |
| astra-a-none | 205.904 | 1,321,539 |
| astra-b-always | 202.232 | 1,300,804 |
| astra-b-none | 220.809 | 1,162,091 |
| sol-a-always | 82.568 | 245,057 |
| sol-a-none | 76.881 | 243,817 |
| sol-b-always | 307.649 | 1,225,619 |
| sol-b-none | 99.486 | 219,424 |

An independent operator calculation from the final actions, resolved states and check prices reproduced gross/net payoff, expenditure and Brier for every run. The canonical reports and prospective assignment/delivery evidence reconstructed successfully. The run stored 288 accepted answers across 289 submission calls. One Sol-B always-check submission failed; the respondent attributed it to submitting more than two decimal places and then supplied an accepted value. No accepted answer was changed or resubmitted, and no collection was restarted. The rejected numeric value is not retained in the compact execution log; the precision explanation is respondent feedback.

Known limits: two worlds, one context per configuration/world/policy, no repeat estimate for these policy contrasts, requested model aliases with unverified revisions, and operator-asserted execution. The random order placed all always-check contexts first, leaving execution-time/provider drift uncontrolled. Policies were declared upfront and context continued across companies, so arm differences include anticipation and history effects. Six recurring sources and shared worlds create dependence. No independent-company bootstrap or population confidence claim is made.

The source sample was independently drawn and accurately measured but fallible about demand. This is a controlled information purchase, not an evaluation of an actual human reviewer or commercial verification service. There was no buyer outreach, registry write, paid endpoint or payment. Passport-guided allocation was not tested, and no cognitive trait or intervention metric was issued.

## Interpretation and next decision

The extra evidence improved the probability forecasts, especially in world B, but the chosen actions did not earn enough to cover blanket purchasing. The high-price group performed poorly for both configurations; the low-price group had positive descriptive net contrasts. Because price is coupled to prior and because complete contexts can carry policy effects forward, selecting the favorable rows cannot establish that a selective policy would succeed.

Do not advance to passport-guided allocation on this result. First separate offered price from company prior and threshold, and freeze a simple policy using price and distance of the provisional probability from the decision threshold. Collect its whole trajectory on new matched worlds against no check and always check. Balance policy order within matched blocks and include repeated contexts to estimate run variation. Keep the original negative result; any revised loss weights, benefit threshold, allocation and resource bounds must be specified before the next collection. This follow-up is proposed, not launched or validated.

A later protocol revision should give policy-specific final-stage wording, explain available versus charged price more economically, and expose the whole-percent requirement clearly in the machine schema/error. All 32 postcompletion comprehension answers were correct on operator review, but repeated archives, generic policy wording and the one numeric-input error remain usability findings. Human acceptance remains pending.

## Artifact commitments

| Artifact | SHA-256 |
| --- | --- |
| Stage A plan | `cb9ad14bfa31f2a7127dc829a0c4790fa2bd93dcf8d1dffae987a5fef5b9e5ab` |
| Complete summary | `6a17b90e8d0941ef489a4b8cc209fa4499506f10af8dc56289ac8b34858b199f` |
| Execution accounting | `d1a017cc7d53810f2a162c2ea238ee933ac8e4d7e419e1a0be253ef43b83b9fd` |
| Completion/comprehension review | `6e895ffd9a89095360a7a52f579f29611d50d08996bcec58e5ff64b23d0c8b60` |
| Independent operator review | `5d850a3623be26127b73bb3e4a006490e50cd1fb89f838911d1e49151412b717` |

| Context | Canonical report SHA-256 | Verification evidence SHA-256 |
| --- | --- | --- |
| astra-a-always | `843ecd9a235113094ff6bac126b390274aeae4e530e8afa81a01c05198b6b779` | `2ab925ffa0d6884ced78639180d03195a46470a28f63e09c7e3ddcec887f86fb` |
| astra-a-none | `6292d73601f25d23bc08366b64a0d59c0cce0700f5e207a8e502479476ff1401` | `3d719c694e0aa50921e0530627693cf3784a257eb7d5d88a8807525ed4fce389` |
| astra-b-always | `dd41589d35e2de39e0f251b7fbe427380b50754ef546d0804868e763239cbabc` | `059ea911bbe34aea977935d0d192f3168bda08cb6a6e2e6b3828603039a609ca` |
| astra-b-none | `f8ee4e9dad4552c72e0205423c751977dea176d8092dc2541e15949ed568962a` | `94cac971c9c844c45c7f4a3dead93bf6cce7ef7728b0beaa480c5e96f70ddfc2` |
| sol-a-always | `2da05c4daa1b047f972cfaaa6f3a88aeef0e89b7d49c3fb5b5c6f3cad3d66650` | `e253f15263a1522412cdc605f9f4097ef0e8af7b1a3cc6e15bd908ecda3eafa6` |
| sol-a-none | `3d28996ddbfa0a25f79a928bda3e48bcf3c2d1334f755e96c4726a9e2b117051` | `8a55dae700e32a0d5cc6e7e55eb3e1c4e59c2298150f425d998c2d13f84254e2` |
| sol-b-always | `1092adbd13f189665ca13fadbfad1146fb4abd7e73b66d39bf2a59bd6cb87ba8` | `d605478da9bb4925744d05b3ea10b548ab9ce036a7f2f3e9b14244788a735ed8` |
| sol-b-none | `3eda1c9c63c3087893409a39e64cdc7e1fee87e751d48a3fd92082bf472fd9b3` | `24a991a4a93b011bbf2ecb077127a597d3f8a7e796e24b8cfa32edc1755bb32a` |

Original private artifacts remain under `output/verification-stage-a-20260926/`; the public repository contains aggregate findings and hashes only. These commitments are operator-held byte bindings, not independent timestamps or model attestations. See [validation](source-verification-validation-2026-09-26.md) and [the roadmap](mvp.md) for scope and follow-up.
