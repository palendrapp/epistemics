# Between-session variance of description priors — 28 September 2026

This is a preregistration, written and committed before collection; the results follow below. Earlier contexts suggested that ambiguous source descriptions are read differently in different fresh sessions, but not because of the comparison set: the [relative-judgement test](disposition-range-2026-09-28.md) found a fixed mapping. This study estimates that between-session variance directly.

## Design

**Collection.** Relay descriptions, set A, markets, random case order. Six new fresh sessions each for GPT-6 Astra and Sol (repeats 11–16), 12 contexts, on the tasks implementation used for the relative-judgement run (fingerprint `7cbee776…f140`).

**Model** (`epistemics.ledger.variance`). The data are the implied priors of the three ambiguous levels: mildly reassuring, irrelevant and mildly suggestive. In session k, each level's prior is its mean, plus a shift shared by all levels in that session, plus a level-specific deviation, plus the session fit's own error, taken from its 90% interval. The two variance components are estimated by restricted maximum likelihood on a grid, with 95% profile-likelihood intervals. The total between-session SD combines them.

**Estimator validation.** Synthetic sessions through the real per-session fit, six sessions and 30 repetitions per cell, report noise 0.1 (`output/variance-validation-20260928.json`, SHA-256 `de9012b3…c1e8c6`). Total SDs from 0.02 to 0.14 were recovered with mean estimates within 0.012 of the truth. 95% interval coverage was 0.87–1.00 for the total and 0.90–1.00 for each component.

**Exploratory estimates** from existing set-A sessions (the first run, retest and baseline experiment, pooled over order policies) were computed before this plan:

| Configuration | Session shift SD | Level-specific SD | Total SD |
| --- | --- | --- | --- |
| Astra (6 sessions) | 0.085 [0.03, 0.20] | 0.065 [0.045, 0.115] | 0.107 [0.074, 0.207] |
| Sol (6 sessions) | 0.085 [0.05, 0.19] | 0.030 [0.015, 0.06] | 0.090 [0.056, 0.192] |

These do not support the impression from the relative-judgement contexts that Sol is less stable than Astra. On this design the two look similar.

## Predictions

- **P1.** Both configurations have a non-negligible total between-session SD for the ambiguous levels: point estimate at least 0.05 in the six new sessions.
- **P2.** The shared session shift is the larger component in both configurations.
- **No directional prediction between configurations.** The exploratory intervals overlap.

**Reading-guide labels,** fixed in advance, for the total SD of ambiguous-description priors:
- **Stable:** below 0.05.
- **Moderate:** 0.05–0.10.
- **Unstable:** 0.10 or more. Two sessions may then differ by more than about 20 points.

The primary estimates use the six new random-order sessions only. Two secondary analyses follow:
- **Random-order pooled:** adding the two earlier random-order set-A sessions per configuration, 8 in total.
- **All orders pooled:** adding the four baseline sessions with controlled orders, 12 in total.
