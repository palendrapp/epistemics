# Compact verification delivery, source-verification/0.3.0

This increment reduces collection cost before the [naturalistic disclosure and shared-origin pilot](decision-value-pilot.md#2b-naturalistic-disclosure-and-shared-origin-pilot), whose explicit arm reuses this task. It changes public delivery only. The canonical source-learning ledger, the cost-aware check rule, bound prices, realized-payoff analysis and passport guard are those of [source-verification 0.2](cost-aware-verification.md). The 0.2 implementation and its evidence are unchanged, and 0.2 results should not be pooled with 0.3 collections without a stated reason.

The implementation lives in `epistemics.source_compact`. Browser and MCP share one service.

## Why

The [24-context 0.2 comparison](cost-aware-results-2026-09-26.md) used 22.5 million known input tokens, 95% of them cached.
- **Per context:** Astra contexts each used 1.18–1.39 million. Sol contexts mostly used 0.21–0.37 million, with two cost-aware contexts at 1.90 and 2.14 million, despite similar tool-call counts. The respondent harness, not only payload size, drives cost.
- **Per checkpoint:** each 0.2 checkpoint re-sent the source's complete archive as verbose JSON, 62% of checkpoint bytes across the comparison. It also repeated fixed policy and stage text, and the protocol required two tool calls, `get_trial` then `submit_answer`.

## What changed

| 0.2 | 0.3 compact |
| --- | --- |
| Full archive per checkpoint: one JSON object per record, repeating source ID and world constants | `source_history`: the same records in the same order, as `3W 4S …` (reported count of five, then strong/weak resolution) |
| Company evidence as sentences carrying numbers | `source_report`, `independent_sample`, `prior_strong` and `decision_threshold` fields; the sentence templates are fixed |
| Policy description, research/diagnostic placeholders and stage text repeated per checkpoint | Sent once in `describe_battery`: constants, field definitions, stage instructions and workflow. Checkpoints carry a one-line stage reminder |
| `get_trial` then `submit_answer` for every checkpoint | `submit_answer` locks and returns `next_trial`; `get_trial` only begins or recovers |
| History rows carry full 0.2 trials | History rows carry compact trials |

**Information equivalence is enforced, not assumed.** `present()` builds the 0.2 public trial, compacts it, expands it again and refuses to return the checkpoint unless the expansion reproduces the 0.2 trial exactly. Evidence verification recomputes every locked checkpoint from the canonical report. The compact form contains no information 0.2 lacked, and precomputes no counts or sufficient statistics: records remain individual and ordered.

Retries remain idempotent. An identical retry of an accepted answer returns the original receipt with the checkpoint now awaiting an answer. The next checkpoint's prediction and presentation locks are created before it is returned. A fifth completion question checks understanding of the history encoding.

## Validation

Two independently seeded synthetic validations passed on 27 September against implementation fingerprint `c736080b8e42d1f01209888a64bf30461e32ccecc9ea4b08d1323358a2fadb43`.
- **Unchanged recovery gates:** the 0.2 model-recovery gates were rerun with 32 repetitions per family and policy (288 datasets per seed). All three policies passed at both seeds. Presentation does not enter inference, so this checks that the gates still hold, not a new property.
- **Complete compact collections:** under every policy, each validation drove a complete collection through submit-returned checkpoints, verified the evidence, and expanded every locked checkpoint to its exact 0.2 trial.

| Seed | none | always | cost_aware | Checks assigned (none/always/cost-aware) |
| --- | ---: | ---: | ---: | --- |
| 20260927 | 0.110 | 0.112 | 0.106 | 0 / 12 / 4 |
| 20261027 | 0.110 | 0.112 | 0.105 | 0 / 12 / 3 |

Values are compact checkpoint bytes as a fraction of 0.2 checkpoint bytes over all 36 checkpoints. A complete collection needs 38 respondent tool calls, against at least 74 for 0.2.

| Artifact | SHA-256 |
| --- | --- |
| compact-validation-20260927.json | `d52b3348e4d1cd35f623583c378c6ffaf31e49c445c0ef481a93837d373f913e` |
| compact-validation-20261027.json | `be666d562d5f9ddea660ec6c2cdc84a3de760f6eec5188b6c679f0e8b6adac54` |

The offline tests cover:
- exact expansion at every checkpoint for three policies and two worlds;
- absence of evaluator secrets;
- concurrent identical retries and rejected answer changes;
- locked next checkpoints;
- exact charged costs;
- evidence tampering;
- the passport guard;
- a complete stdio MCP collection using one call per checkpoint;
- a complete authenticated browser collection;
- acceptance-plan preparation.

**Token savings could not be estimated offline.** A simple accumulation model fitted to the 0.2 Astra transcripts implies negative fixed cost per turn. The harness evidently does not resend every earlier tool result on every call; code-mode execution can batch calls within one model turn. Byte and call reductions are therefore not a token forecast. Actual usage must be measured in a fresh-agent acceptance. The runner now also records model turns.

## Acceptance

**Completed 27 September; [results](compact-acceptance-2026-09-27.md).** Engineering and comprehension passed in all six contexts. Astra used about 22% fewer input tokens per context than under 0.2; Sol's harness varied too much to show a change.

`python -m epistemics.source_compact.runner <directory> --validation <seed-a> --validation <seed-b>` prepares and runs a frozen acceptance:
- **Contexts:** one new world, with Astra and Sol medium each completing all three policies (six fresh contexts, two at a time).
- **Limits:** 900 seconds per context, 3,600 seconds total, an 8-million known-token admission ceiling, a 1.5-million reserve per context and no automatic retry.
- **Pass criteria:** every context completes 36 checkpoints; tool errors are reviewed; completion answers are correct, including the history encoding; and reported friction is reviewed.
- **Token comparison:** tokens are compared descriptively with the 0.2 acceptance and comparison contexts. Worlds differ, so this is not a controlled estimate.

Running it uses the existing account and needs explicit operator approval. It establishes engineering and comprehension only.

A comparison design is intentionally absent. The next respondent comparison follows the pilot plan: this task as the explicit arm with more independent worlds, pre-outcome opportunity strata, low-opportunity controls and a small repeatability check. Human browser acceptance is implemented but paused with other fresh human collection.

## Commands

```sh
uv run python -m epistemics.source_compact validate-synthetic --seed 20260927 --output output/compact-validation-20260927.json
uv run python -m epistemics.source_compact simulate --directory output/compact-demo --policy cost_aware --seed 7
uv run python -m epistemics.source_compact create --participant participant.json --directory output/compact-human --policy cost_aware
uv run python -m epistemics.source_compact serve --directory output/compact-human
uv run python -m epistemics.source_compact export --directory output/compact-human
```
