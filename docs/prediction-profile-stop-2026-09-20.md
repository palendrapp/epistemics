# Profile collection stopped — 20 September 2026

The [frozen prediction plan](prediction-budget-2026-09-20.md) started its 144-episode profile partition at 07:59:42 UTC and stopped at 08:38:54 UTC. **55 episodes completed; attempt 56 failed.** No fitted profiles, prediction lock or empirical prediction result were produced. Policy and held-out cases remain unopened.

## Preserved collection

| Requested configuration | Completed profile episodes / 48 | Accepted responses |
| --- | ---: | ---: |
| GPT-5.6 Luna, medium | 19 | 76 |
| GPT-5.6 Terra, medium | 18 | 75 |
| GPT-6 Astra, medium | 18 | 72 |
| Total | **55 / 144** | **223 / 576** |

Terra's nineteenth episode accepted three of its four responses before its Codex process exited unsuccessfully. All seven recorded MCP calls succeeded, with no recorded tool violation. The process did not supply a terminal usage record. Its stderr contains startup warnings but no explanation for the failure. The runner did not retain top-level JSON `error` or `turn.failed` events or the numeric exit code, so the cause cannot be reconstructed from the saved attempt. This is an undiagnosed execution failure, not evidence of a cognitive bias or a demonstrated provider outage.

The 55 completed attempts reported **9,348,522 input tokens**, including **7,611,776 cached input tokens**, plus **43,041 output tokens**: **9,391,563 known processed tokens**. Failed-attempt usage is **unknown**, not zero; the known count is a lower bound on total usage. Cumulative episode time across all 56 attempts was **2,350.10 seconds**, including 35.35 seconds for the failed attempt. Marginal dollar cost remains unknown under the existing Codex account.

All accepted answers, completion receipts, execution records, private stderr, frozen manifests and original implementation were retained in a private snapshot with per-file SHA-256 hashes. No case was retried, replaced or excluded. The original manifest hash remains `24da73620aaedb048300b404f2a3919d90d181ce4ca35216e16843a8362acc76`; the private incident summary hash is `434329e89eedb4cff5884980d0ef51d6cd3674d7b792ff3ea11cd23e68357e93`. These are operator records, not independent execution attestation. Raw responses, source seeds and private artifacts are excluded from Git.

Operational checks verified database integrity, that admission rejects the unresolved/unknown-cost attempt, that profile locking rejects incomplete collection, and that no later episode or prediction lock exists. The original implementation is preserved alongside the snapshot and in commit `23b7f3a`.

## Diagnostics repair and next execution decision

The runner now retains bounded error messages from `error` and `turn.failed` JSON events, the process return code, and local exception text. It keeps the latest 20 error events, at most 2,000 characters per message, with a dropped-event count. It does not retain the raw event stream or reasoning items. The [official non-interactive interface](https://developers.openai.com/codex/noninteractive) documents these error events separately from item and usage events; stderr alone is insufficient for diagnosis.

This repair cannot recover missing historical diagnostics or usage. It adds no retry or change to episode acceptance. Offline subprocess tests exercise errors emitted only on stdout, bounded diagnostic retention, private-reasoning exclusion, missing-usage preservation and admission blocking.

Validation passed: Ruff checks and formatting, all 175 Python tests (including synthetic parameter recovery), TypeScript checking and formatting, and all 20 TypeScript tests. Solana RPC tests use mocks; this work did not perform validator or live-network validation.

Version review: this is an observability repair; task stimuli, respondent prompt, source model, fitted parameters, payoffs, phase gates, admission rules and scoring remain unchanged. The task and benchmark versions remain 0.1.0. The source fingerprint changes, so the stopped run must be read with its archived implementation; its manifests must not be rewritten to match new source. No report contract changes are required.

The next execution increment needs an explicit, versioned interruption/recovery protocol before another long collection. It should bound recovery attempts, preserve accepted answers and original failures, distinguish an interrupted/resumed context from an uninterrupted episode, and keep unknown usage visible in both resource admission and result eligibility. Failures of the task contract must remain distinct from diagnosed transport failures. This incident cannot simply be labeled transient because its cause is unknown.

That protocol is **not implemented or frozen here**, and no replacement benchmark has been launched. Any reuse of this partial collection must be labeled as a protocol amendment or exploratory analysis, rather than completion of the original no-retry plan. Predictive usefulness and assistance benefit remain unestablished.
