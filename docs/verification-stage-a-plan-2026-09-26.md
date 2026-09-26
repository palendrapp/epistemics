# Frozen verification-value Stage A — 26 September 2026

This plan was recorded before any Stage A respondent was launched. It implements the [previously proposed comparison](verification-value-v1.md) with the [assigned-check collector](source-verification.md). Two recovery runs and a separate two-context acceptance precede it. Private plans, worlds, configurations and code snapshots remain outside Git.

## Acceptance gate

Both requested Astra-medium contexts completed all 36 checkpoints without rejected submissions or answer retries. No-check took 187.402 seconds; always-check took 192.126 seconds. Each answered all four completion questions correctly on operator semantic review: checks were assigned, outcomes followed the final answer, samples remained fallible, and check costs applied when declining (zero in the no-check arm).

Both respondents noted long repeated histories. The always-check respondent noted the shared final-stage wording about no check; the no-check respondent noted visible unused check prices and cost wording. These did not prevent correct comprehension. The version is retained unchanged for the main comparison. This is acceptance by agents, not human usability evidence.

Acceptance used 2,613,145 input tokens, including 2,502,272 cached tokens, and 7,207 output tokens: 2,620,352 processed tokens. Total wall time was 192.250 seconds. Marginal account billing cost is unknown. Admission to Stage A depends on engineering/comprehension, not a favorable acceptance payoff. Its outcomes are excluded from the confirmation comparison.

## Frozen comparison

Eight fresh contexts: requested `gpt-6-astra` and `gpt-6-sol`, medium reasoning, crossed with two new worlds and two assigned policies. The aliases' provider revisions remain unverified. The whole configuration, prompt, tool permissions, code and world seeds are recorded. Each context has 24 companies and 36 checkpoints and receives only the five public MCP tools. The policies are declared at the start; comparisons include anticipation and history effects.

The randomly drawn order below was frozen before collection, with two contexts per batch:

| Batch | Context 1 | Context 2 |
| --- | --- | --- |
| 1 | Astra, world B, always check | Sol, world A, always check |
| 2 | Sol, world B, always check | Astra, world A, always check |
| 3 | Astra, world B, no check | Astra, world A, no check |
| 4 | Sol, world A, no check | Sol, world B, no check |

This random draw puts always-check contexts before no-check contexts. It is retained transparently; execution-time/provider drift remains a limitation of the small run and is not controlled by matching the generated worlds.

Primary outcome: always-check minus no-check **net realized fictional payoff per later company**, separately for each configuration/world. Early twelve-company forecasts are excluded. Gross payoff, final Brier, errors, decision changes, actual check expenditure, processed/cached/output usage and elapsed time are secondary.

The feasibility gate remains fixed: at least 0.01 additional fictional points per later company averaged across a configuration's two worlds, and nonnegative gains in both worlds. Every completed or failed attempt remains visible. There are four matched context/world contrasts, not independent company-level participants; no company bootstrap or population confidence claim. Any additional breakdown used to interpret results will be labeled exploratory.

Bounds: one attempt per context, 900 seconds each, two concurrent, 3,600 seconds overall. The known-token admission ceiling is 25 million, reserving three million per incoming context. It is not a hard streaming cap. Stop admission after a failed attempt or exhausted boundary, preserve partials, and do not substitute or automatically retry. Acceptance accounting stays separate.

A passed development gate permits considering a bounded follow-up; it does not establish a general intervention, real investment benefit or passport-guided allocation. The latter requires a simple confidence/price comparator, a frozen profile heuristic, new worlds and assessment-cost accounting. No paid reviewer, external buyer, registry write or payment is part of this run.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation | `259cfd9cf81d1b8d389085142110be3c0c2fc7dcb65cfec9a859a5d4c59ba35a` |
| Acceptance plan | `8316bc2c363db454f3076e7426b05a4c465dcbfdc4b286c9ad5710d665b20f1f` |
| Acceptance review | `83cb12b66531afc043e4fb14f993ed0533af415a76b079f633357e8251b4cd92` |
| Stage A plan | `cb9ad14bfa31f2a7127dc829a0c4790fa2bd93dcf8d1dffae987a5fef5b9e5ab` |

The [validation record](source-verification-validation-2026-09-26.md) supplies the two recovery commitments and checks. Roots: `output/verification-acceptance-20260926/` and `output/verification-stage-a-20260926/`. These are operator-held exact-byte commitments, not independent timestamps or model execution attestations.
