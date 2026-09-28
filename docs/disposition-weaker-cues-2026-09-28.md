# Weaker configurations on the description modules — 28 September 2026

Preregistration, written and committed before collection; the results follow below. [Round 2](disposition-round2-2026-09-28.md) found that GPT-5.6 Luna and Terra share the frontier configurations' 50% defaults and zero value of certainty, and differ mainly in precision. This study measures their description-to-prior mappings.

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
