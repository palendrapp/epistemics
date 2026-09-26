# Frozen cost-aware verification comparison — 26 September 2026

This plan was recorded before any main respondent was launched. The [protocol](cost-aware-verification.md) fixes the expected-sample-value rule, offered-price design, analysis and resource limits. [Offline validation](cost-aware-validation-2026-09-26.md) passes on 576 synthetic datasets; a separate three-context acceptance precedes this comparison.

## Acceptance review

All three requested Astra-medium contexts completed 36 checkpoints each. On operator semantic review, all twelve completion answers were correct: each described its assigned rule, outcome timing, sample fallibility and cost when declining. There were no rejected submissions, retries or changed accepted answers. Repeated protocol/archive text was the main interface friction. The no-check respondent noted unused offered prices; explicit zero charges and stage wording resolved the ambiguity. This is agent acceptance, not human usability evidence. Admission depends on comprehension and engineering, not favorable payoff; acceptance outcomes are excluded.

Acceptance wall time was 454.011 seconds. Known input tokens: 3,827,615, including 3,670,272 cached; output: 12,104; processed input + output: 3,839,719. Unknown-usage attempts: 0. Monetary billing is unknown.

## Frozen comparison

**24 fresh contexts:** requested Astra/Sol, medium, crossed with two new worlds, three policies and two context repeats. Every context has 24 companies / 36 checkpoints. The five public MCP tools are the only tools provided; earlier accepted public evidence remains available within each continuing context. Exact provider revisions remain unverified, and execution is operator-asserted.

Policies are no check, always check and cost-aware. The latter buys when the expected payoff improvement from the five-customer sample, calculated from the accepted provisional probability and decision threshold, exceeds the offered price (strict margin greater than 1e-12). No fitted passport parameter enters the rule. Prices are assigned by a separate frozen seed, shared across policies/configurations/repeats. Every prior receives all three prices and each threshold receives two of each. This is a balanced incomplete crossing, not full orthogonality.

The randomized block order below is frozen. Each world/repeat block contains every policy once for each configuration. Orders rotate and reverse; two configurations run concurrently in each batch. No responses are used to select, reorder or replace contexts.

| Batch | Context 1 | Context 2 |
| --- | --- | --- |
| 1 | Astra, world A, always, repeat 1 | Sol, world A, cost_aware, repeat 1 |
| 2 | Astra, world A, none, repeat 1 | Sol, world A, none, repeat 1 |
| 3 | Astra, world A, cost_aware, repeat 1 | Sol, world A, always, repeat 1 |
| 4 | Astra, world B, none, repeat 1 | Sol, world B, always, repeat 1 |
| 5 | Astra, world B, cost_aware, repeat 1 | Sol, world B, cost_aware, repeat 1 |
| 6 | Astra, world B, always, repeat 1 | Sol, world B, none, repeat 1 |
| 7 | Astra, world A, cost_aware, repeat 2 | Sol, world A, none, repeat 2 |
| 8 | Astra, world A, always, repeat 2 | Sol, world A, always, repeat 2 |
| 9 | Astra, world A, none, repeat 2 | Sol, world A, cost_aware, repeat 2 |
| 10 | Astra, world B, cost_aware, repeat 2 | Sol, world B, always, repeat 2 |
| 11 | Astra, world B, none, repeat 2 | Sol, world B, none, repeat 2 |
| 12 | Astra, world B, always, repeat 2 | Sol, world B, cost_aware, repeat 2 |

## Outcomes and decision criterion

Primary: cost-aware minus none and cost-aware minus always, net realized fictional points per later company. Exclude the first twelve companies. For each configuration/world, average the two repeats per policy, then contrast; equally weight the two worlds. The two worlds are shared across configurations. Context repeats measure variation on identical cases, not additional independent worlds.

The development gate, separately per configuration, requires mean net gain of at least 0.01 versus none and nonnegative repeat-mean gains versus none in both worlds; it also requires nonnegative repeat-mean gains versus always in both worlds. Report each repeat, repeat-contrast signs, within-policy numerical-report differences, net differences and check disagreements. Gross payoff, final Brier, errors, decision changes, check expenditure, usage and elapsed time are secondary. Any additional diagnostic breakdown will be exploratory.

No company bootstrap or population confidence claim. Full trajectories include anticipation and carryover. A passed development gate can support a bounded transfer test; it does not establish a stable trait, general verification benefit, real investment return, or benefit from passport-guided allocation.

## Resource and failure bounds

One attempt per context; 900 seconds per attempt, two concurrent, 7,200 seconds overall. Known processed-token admission ceiling: 40 million, with three million reserved per incoming context. This is not a hard streaming cap. Stop new admission after a failed attempt or exhausted boundary; preserve partials and unknown usage, with no automatic retries or substitutions. Correctable rejected submissions within the ongoing context are counted and preserved separately from accepted immutable answers. Fictional check cost and compute expense remain separate.

No reviewer purchase, payment, outreach, identity enrollment or registry write is included.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation | `6de0cedddc97d4f74507badee93d430970eb4bd01135d748a21f7096d4481367` |
| Acceptance plan | `171b499d0bea1a36b2f9a9fd2ad2ed8593007379d0220fe51beec4d473b64708` |
| Acceptance operator audit | `47fdc413d71b3c658549a4b261dad578745f20cdd12396a24e9dba48bb476807` |
| Acceptance review | `37eb5203eec74554ce8abb8eaec8438dfb0ad7064880e12e76a2857688b57141` |
| Main plan | `f4760dc7321cd556a31af90b83f38ccf74e8a3ca315c04290c02bdc5395f287e` |

Private roots: `output/selective-acceptance-20260926/` and `output/selective-comparison-20260926/`. Each holds the frozen code snapshot, private seeds/configurations, exact evidence and bounded execution accounting. These are operator commitments, not independent timestamps or model attestations.
