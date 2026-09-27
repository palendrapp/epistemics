# Compact delivery acceptance — 27 September 2026

**Engineering and comprehension passed. The token saving was modest for Astra and is not established for Sol.**
- **Engineering:** all six fresh contexts completed all 36 checkpoints of [source-verification 0.3](source-compact.md) with the minimum 39 tool calls and no tool errors.
- **Comprehension:** every completion answer was correct, including the new question on the history encoding.
- **Astra:** each context used about 22% fewer input tokens than the 0.2 Astra contexts.
- **Sol:** the harness varied too much between contexts to show a reduction.

This is engineering acceptance only. It establishes no verification benefit, stable trait or passport claim.

## Design

The frozen plan was committed before collection. It used one new world, and Astra and Sol medium each completed all three assigned policies, making six fresh contexts run two at a time. Validations were the two passed compact synthetic runs. No context was retried or substituted, and accepted answers are immutable.

## Results

| Context | Input tokens | Cached | Output | Seconds | Tool calls | Tool errors | Checks | Decisions consistent |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Astra, always | 980,224 | 941,184 | 2,193 | 189 | 39 | 0 | 12 | 12/12 |
| Astra, cost-aware | 1,010,679 | 938,752 | 2,272 | 153 | 39 | 0 | 4 | 12/12 |
| Astra, none | 973,781 | 935,168 | 2,011 | 149 | 39 | 0 | 0 | 12/12 |
| Sol, always | 176,659 | 155,136 | 2,881 | 258 | 39 | 0 | 12 | 12/12 |
| Sol, cost-aware | 233,244 | 207,104 | 3,929 | 98 | 39 | 0 | 7 | 12/12 |
| Sol, none | 965,569 | 897,152 | 3,906 | 154 | 39 | 0 | 0 | 12/12 |

Total known usage was 4,340,156 input tokens (4,074,496 cached) and 17,192 output tokens, with no unknown-usage attempts. Main wall time was 596 seconds. Each context called `describe_battery` once, `get_trial` once, `submit_answer` 36 times and `finish_evaluation` once, and never called `get_history`.

## Token use compared with 0.2

These are different worlds and dates, so the comparison is descriptive, not a controlled estimate.

| Configuration | 0.2 contexts (26 September) | 0.3 compact contexts |
| --- | --- | --- |
| Astra | 1.14–1.39 million; mean 1.28 million over 15 contexts | 0.97–1.01 million; mean 0.99 million over 3 contexts |
| Sol | 0.21–0.37 million in 9 of 12 contexts; 0.66, 1.90 and 2.14 million in the others | 0.18, 0.23 and 0.97 million |

Astra used about 22% fewer input tokens per context and finished faster: 149–189 seconds, against 198–247 seconds for its 0.2 acceptance contexts. Halving tool calls and cutting checkpoint bytes by about 89% therefore reduced Astra's use by roughly a fifth, not in proportion. Most of Astra's per-context use does not come from evaluation payloads.

Sol's use again spans more than a factor of five across contexts with identical call sequences. Its compact no-check context resembles the earlier high outliers. Some harness or model behavior outside the evaluation interface dominates Sol's cost, and this acceptance cannot show whether compact delivery changed it.

**Implication for cost planning.** Budget per context by configuration, using these measured ranges rather than payload size. Reducing checkpoints per context, or companies per context, is now the more direct lever than further compression.

## Comprehension and friction

All 30 completion answers were correct on operator review:
- the assignment rule;
- demand-revelation timing;
- sample fallibility;
- charging when declining;
- the meaning of `3W`.

Reported friction:
- **Policy-generic definition.** The `check` field definition describes the cost-aware case, where the charge is unknown until the provisional answer, even under always and none policies (Astra, always). A policy-specific definition would remove this.
- **Irrelevant prices.** Offered prices remain visible under the no-check policy (Astra, none).
- **History encoding.** The compact `source_history` notation took a moment to parse (Sol, always; Astra, cost-aware), though every respondent explained it correctly.
- **Empty final checkpoint.** A separate final checkpoint is required when no check was supplied (Astra, none; Sol, none; Astra, cost-aware). This is the protocol's design, not an interface fault.
- **Workflow.** One respondent noted carrying `next_trial` forward from each receipt, which is the intended workflow.

None of these is a comprehension failure. The first two are candidates for a later wording revision under a new version; 0.3 stays unchanged for the collection it was accepted for.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation (fingerprint) | `c736080b8e42d1f01209888a64bf30461e32ccecc9ea4b08d1323358a2fadb43` |
| plan.json | `e4bd708a5204d1a4d03cb0589851a49d924f4dc9e64fd453054bcf150ec99092` |
| summary.json | `4f8c489a18608a678fe955cd4f36b55499e10f696f89ac393904439bd7f089da` |
| execution.json | `ae325ba371788d0529572b8398cde7029225221f5c7815dc6dd3b7daaab67fb7` |

Raw worlds, answers, configurations and transcripts remain private and outside Git. Model revisions are requested aliases, not verified immutable revisions, and execution is operator-asserted. Realized payoffs above describe one world and are not an outcome comparison.
