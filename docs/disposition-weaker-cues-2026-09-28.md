# Weaker configurations on the description modules — 28 September 2026

Preregistration, written and committed before collection; the results follow below.

**Result.**
- **Terra:** follows the frontier mapping, more noisily. Coherent in 5 of 6 sessions; median report noise 0.32.
- **Luna:** states sensible base rates but its forecasts do not use them. Coherent in 1 of 6 sessions, with gaps up to 0.34. Its disclosure mapping is compressed to a 0.22 range, and its median report noise is 0.51. [Round 2](disposition-round2-2026-09-28.md) found that GPT-5.6 Luna and Terra share the frontier configurations' 50% defaults and zero value of certainty, and differ mainly in precision. This study measures their description-to-prior mappings.

## Design

- **Configurations:** GPT-5.6 Luna and Terra, medium effort.
- **Modules:** relay descriptions and disclosure descriptions, set A, markets, random case order.
- **Sessions:** three fresh sessions per configuration and module, 12 contexts.
- **Implementation:** the tasks implementation used for the relative-judgement and variance studies (fingerprint `7cbee776…f140`).

**Reference.** The GPT-6 medium mappings, pooled over their set-A sessions (from `output/ledger.json`):

| | Relay A | Disclosure A |
| --- | --- | --- |
| Astra | 0.05, 0.49, 0.49, 0.47, 0.93 | 0.23, 0.20, 0.50, 0.59, 0.75 |
| Sol | 0.04, 0.41, 0.44, 0.54, 0.92 | 0.15, 0.10, 0.50, 0.70, 0.75 |

## Predictions

- **W1. Shared direction.** In both modules, each configuration's mean mapping over its three sessions ranks the strongly reassuring level below the strongly suggestive one, by at least 0.30.
- **W2. Lower precision.** Median report noise τ across each configuration's six sessions exceeds the GPT-6 medium median (0.05). Round 2 measured Luna at 0.31–0.50 and Terra at 0.05–0.42.
- **W3. Coherence.** Stated and implied priors agree within 0.10 at every level in most sessions (at least 4 of 6 per configuration). This is uncertain: Luna's positive-control results showed a gap between what it noticed and what it used.

These are also reported, without prediction:
- the between-session SD of the ambiguous relay levels (three sessions each, wide intervals);
- whether irrelevant details move the prior;
- the size of the mapping range compared with Astra and Sol.

## Results

**Collection.** All 12 contexts completed with the minimum 27 calls and no tool errors, in 94–146 seconds. They used 5,919,860 input tokens (5,291,776 cached). The tables regenerate with `uv run python -m epistemics.ledger cues-summary output/disposition-weaker-cues-20260928`, and `… variance … --configuration <luna|terra> --module <corroboration-cues|disclosure-cues>`.

| Configuration | Module | Mean mapping (3 sessions) | Suggestive − reassuring | Median τ | Coherent sessions (all levels within 0.10) | Irrelevant level by session |
| --- | --- | --- | --- | --- | --- | --- |
| Luna | relay | 0.04, 0.33, 0.40, 0.51, 0.91 | 0.87 | 0.48 | 1/3 | 0.44, 0.37, 0.39 |
| Luna | disclosure | 0.49, 0.42, 0.62, 0.70, 0.71 | 0.22 | 0.82 | 0/3 | 0.47, 0.79, 0.60 |
| Terra | relay | 0.16, 0.31, 0.38, 0.58, 0.89 | 0.73 | 0.44 | 3/3 | 0.53, 0.20, 0.40 |
| Terra | disclosure | 0.30, 0.22, 0.46, 0.70, 0.75 | 0.45 | 0.19 | 2/3 | 0.47, 0.42, 0.50 |

**Against the predictions:**
- **W1 (shared direction, at least 0.30):** supported in three of four cells. Luna's disclosure mapping spans only 0.22.
- **W2 (lower precision):** supported. Median τ over six sessions is 0.51 for Luna and 0.32 for Terra, against 0.05 for GPT-6 medium.
- **W3 (coherence in at least 4 of 6 sessions):** supported for Terra, 5/6. Its one exception was 0.17, at a strongly reassuring disclosure level. Not supported for Luna, at 1/6: its stated–implied gaps were 0.11–0.13 on relays and 0.13–0.34 on disclosure.

**Luna states sensible priors and does not use them.** In one disclosure session it stated 0.20, 0.20, 0.50, 0.60 and 0.75 across the levels, close to Astra and Sol. Its forecasts in the same session implied 0.54, 0.54, 0.79, 0.85 and 0.88. In another, the implied mapping ran against the stated one. On relays it stated 50% for the middle levels while its forecasts implied about 37–39%.

**Between-session SDs** of the ambiguous levels, from three sessions each, with wide intervals:

| | Luna | Terra |
| --- | --- | --- |
| Relay | 0.01 [0.00, 0.16] | 0.14 [0.06, 0.32] |
| Disclosure | 0.17 [0.06, 0.42] | 0.05 [0.03, 0.18] |

Terra's relay baseline moved from 0.20 to 0.53 across its sessions. It stated those baselines, so it was coherent throughout.

## Interpretation

1. **Terra has a noisier version of the frontier mapping.** Same direction, mostly coherent, report noise six times the GPT-6 medium level, and a relay baseline that varies between sessions.
2. **Luna has a gap between what it knows and what it uses.** Asked for base rates, Luna gives priors much like the frontier configurations'. Its forecasts do not apply them: in disclosure the implied mapping is compressed or reversed, with very high report noise. This is the pattern of the [positive control](research3-positive-control-2026-09-27.md), where Luna described fabricated figures as unreliable and used them anyway. It is a fidelity failure, not a different disposition.
3. **For the passport,** stated base rates cannot stand in for implied ones in weaker configurations. The reading guide should report both, and flag a configuration whose forecasts do not use the priors it states.
4. **Reading-guide candidates:**
   - **GPT-5.6 Luna:** states reasonable base rates for qualitative source descriptions, but its probability updates do not reflect them, especially for disclosure. Do not rely on its updates from qualitative source information.
   - **GPT-5.6 Terra:** follows the frontier direction with noisier reports and an unstable relay baseline.

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `f6fe0ecacb6212ae683c1b4ac2357c62ffd3df33fe84484024fa993cf6aae6e2` |
| execution.json | `6cd046152e73430ce941ec7a05671187d3b296a9e23b9f94874866762e2efcb6` |
| summary.json | `2598bbd09d47348dc1c9f37d752a48ae723c42e3addc839c4d87d8e1ccd60606` |
