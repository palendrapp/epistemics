# Bounded recovery for prediction collection

Benchmark **0.2.0** adds an optional frozen recovery policy. The [public policy](../examples/benchmark-recovery.json) permits one additional attempt per episode and nine across the entire benchmark. Reaching three attempts with unknown or incomplete usage stops further admission and prevents a final empirical report. A failed retry cannot trigger another retry.

The task remains provenance pilot 0.1.0. Evidence, source histories, payoffs, reported-probability model, acceptance thresholds, partition assignments and respondent prompt are unchanged. Recovery changes the execution context, so the benchmark version is increased and interrupted contexts are disclosed. Offline validation checks both synthetic parameter recovery through resumed collection and real MCP resumption using a synthetic respondent; neither is an empirical model result.

## What can recover

Eligible failures are unsuccessful process exits, timeouts, or missing terminal usage after an otherwise finished episode. Eligibility does not establish that a failure was transient or caused by the provider. Recorded task violations, failed MCP calls, unclassified exceptions, normal exits without completing the task, and running/abandoned attempts stop collection for inspection. Decisions about retries do not use the respondent's probability values or apparent task performance.

A retry uses the same assignment, subject and requested configuration in a fresh process. The existing MCP collector supplies the current checkpoint and previously accepted public history. Earlier answers and their original receipts cannot be changed; exact repeated submissions remain idempotent. If all answers and completion already exist, a recovery can finish without submitting them again.

Every new attempt records its parent attempt, accepted-answer count at startup, a hash of that history, context mode, failure category, process exit code, diagnostics and available usage. Old failures remain failed records after successful recovery. The accounting view distinguishes historical failures from episodes whose execution remains unresolved. A pending episode must be resolved before another case is opened.

## Resource accounting

All attempts, including failures, count against the attempt and cumulative episode-time limits. The original 180-second episode timeout still applies. Admission remains between episodes, so one episode can overshoot a token/time admission ceiling.

The token admission charge is **known processed tokens + 1,000,000 tokens per attempt with unknown/incomplete usage**. The reserve is a planning charge, not a measured cost, estimate of actual usage or guaranteed upper bound. Known token totals never include this reserve. Failed attempts with a partial usage record retain that known portion and an additional reserve for the unknown remainder. Actual usage remains a lower bound when any attempt is incomplete; marginal dollars remain unknown under the existing account.

For the initial 432-episode plan, the amendment raises the attempt allowance from 432 to **441**. It preserves the **234-million-token admission ceiling**, **43,000 cumulative episode seconds**, and the original case count. The amended token ceiling applies to the admission charge, not a claim that unknown actual usage is bounded. Reaching the unknown-usage threshold stops the run even if other allowances remain.

## Amend an existing stopped run

An amendment creates a **new directory and manifest**. It preserves an exact, hashed predecessor snapshot and copies the response databases and attempt records. The original directory and original manifest are not rewritten. Only the new benchmark database binding is updated to the new manifest. The amendment records its reason and predecessor hashes.

Amendment is allowed once, before a prediction lock, analysis report or any later-partition exposure. It checks the unchanged task/design and respondent-configuration bindings. It does not bypass those checks to reuse responses under a different task or prompt. Source fingerprints continue to bind each implementation separately.

For a historical process failure whose terminal diagnostics were not captured, the operator must explicitly identify the failed attempt in the amendment review. The recorded reason must preserve the uncertainty about its cause and usage. This review cannot override a recorded task violation, failed MCP call or already classified failure. Running/abandoned attempts cannot be silently relabeled as failed.

```sh
uv run epistemics benchmark amend-recovery \
  --benchmark PRIVATE_STOPPED_RUN \
  --policy examples/benchmark-recovery.json \
  --output PRIVATE_AMENDED_RUN \
  --review-process-exit REVIEWED_FAILED_ATTEMPT_ID \
  --reason 'Observed unsuccessful process exit; cause and usage remain unknown. Preserve accepted history under the amended recovery protocol.'
uv run epistemics benchmark run --benchmark PRIVATE_AMENDED_RUN --split profile --max-episodes 1
```

The first bounded batch verifies live recovery. Subsequent batches skip completed episodes and retain the same frozen limits. No further policy changes may be made by editing the manifest or raising limits after seeing a failure. A fresh benchmark can also declare `recovery` in its specification before collection; without it, failure remains a stop condition.

## Interpretation and machine-readable disclosure

The primary fit and prediction score retain every planned case, including resumed cases, without imputation or exclusions. Consequently, a profile from a run with recovery describes the configuration **under the disclosed recovery protocol**. It does not establish that fresh and resumed contexts produce equivalent responses.

Prediction locks and reports identify protocol amendments and retried episodes. Version 0.2 reports expose:

- `protocol_status`: `original` or `amended`.
- `execution_scope`: `uninterrupted` or `includes_retried_episodes`.
- `accounting_complete`: false whenever any historical usage remains unknown.
- `accounting.totals.usage_scope`: `complete` or `known_lower_bound`.
- Separate known token totals, planning reserves, admission charges, failure counts and retry chains.

Report validation rejects contradictory disclosure fields. `complete: true` describes complete case collection and resolved execution, not complete cost accounting or uninterrupted execution. Consumers requiring fully known costs or uninterrupted contexts must check the corresponding fields. A numerical prediction criterion can pass under the amended protocol while accounting remains incomplete; this is never relabeled as completion of the original no-retry plan.

The execution check occurs before collection exports are frozen, so an unresolved final process does not make its episode impossible to resume. Existing profile/policy/held-out stage gates and exact-byte prediction locks still apply. These are operator-controlled checks, not independent execution attestation, verified provider identity or a validated epistemic passport.
