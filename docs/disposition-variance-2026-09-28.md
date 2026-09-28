# Between-session variance of description priors — 28 September 2026

This is a preregistration, written and committed before collection; the results follow below.

**Result.** P1 was supported: ambiguous descriptions vary between sessions by a total SD of 0.07 for Astra and 0.11 for Sol. P2 was not: the variation is mostly level-specific, not a shared session shift. Astra's uninformative default never moved from 50%; Sol's ranged from 22% to 52%. Earlier contexts suggested that ambiguous source descriptions are read differently in different fresh sessions, but not because of the comparison set: the [relative-judgement test](disposition-range-2026-09-28.md) found a fixed mapping. This study estimates that between-session variance directly.

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

## Results

**Collection.** All 12 sessions completed with the minimum 27 calls and no tool errors, in 96–202 seconds. They used 6,293,415 input tokens (5,886,976 cached). Estimates regenerate with `uv run python -m epistemics.ledger variance output/disposition-variance-20260928 --configuration <astra|sol>`, adding the earlier roots for the pooled analyses.

Between-session SDs of the three ambiguous relay levels (mildly reassuring, irrelevant, mildly suggestive), with 95% profile intervals:

| Analysis | Configuration | Sessions | Session shift | Level-specific | Total |
| --- | --- | --- | --- | --- | --- |
| Primary (new sessions) | Astra | 6 | 0.00 [0.00, 0.06] | 0.07 [0.05, 0.10] | **0.07 [0.05, 0.10]** |
| Primary (new sessions) | Sol | 6 | 0.07 [0.00, 0.19] | 0.08 [0.05, 0.15] | **0.11 [0.07, 0.20]** |
| Random order pooled | Astra | 8 | 0.06 [0.00, 0.13] | 0.07 [0.05, 0.11] | 0.09 [0.07, 0.14] |
| Random order pooled | Sol | 8 | 0.08 [0.02, 0.17] | 0.07 [0.04, 0.11] | 0.10 [0.07, 0.18] |
| All orders pooled | Astra | 12 | 0.05 [0.00, 0.10] | 0.07 [0.06, 0.10] | 0.09 [0.07, 0.12] |
| All orders pooled | Sol | 12 | 0.08 [0.05, 0.14] | 0.05 [0.03, 0.09] | 0.09 [0.07, 0.15] |

Level by level, across the six new sessions:
- **Astra.** The irrelevant outlet sat at 0.50 in every session (SD 0.004). The two mild descriptions varied independently: "sometimes runs its own surveys" 0.40–0.60, and "a small newsletter with two analysts" 0.33–0.60.
- **Sol.** All three levels varied: SDs of 0.08, 0.12 and 0.13. The irrelevant outlet ranged from 0.22 to 0.52.

**Coherence.** Stated and implied priors agreed within 0.05 in 10 of 12 sessions. The two exceptions were both Sol's:
- **One small:** 0.09, at the strongly reassuring level, 0.00 stated against 0.09 implied.
- **One large:** its forecasts for the irrelevant outlet implied 22% while it stated 50%. That is the first clear stated–implied divergence in these modules.

Sol's report noise was also higher in two sessions (τ ≈ 0.5, against 0.05–0.25 otherwise).

**Against the predictions:**
- **P1** (total SD of at least 0.05 in both configurations): **supported**, with 0.07 for Astra and 0.11 for Sol.
- **P2** (shared session shift the larger component in both): **not supported.**
  - **Astra:** the variation is entirely level-specific (shift 0.00), because its uninformative default never moved.
  - **Sol:** the two components are about equal (0.07 and 0.08).

  The shared shift seen in the relay set-A retest was not the typical pattern.
- **Labels,** by point estimate:
  - **Astra: moderate** (0.07).
  - **Sol: unstable** (0.11), though its interval (0.07–0.20) reaches into moderate. The pooled analyses put both at 0.09–0.10.

## Interpretation

1. **Ambiguous source descriptions carry real between-session variability in both configurations.** It is about 0.07–0.11 on the probability scale. Two sessions can read the same mild description 15–30 points apart. This is a reliability property of the configuration: it does not come from comparison sets, and not only from order.
2. **The configurations differ in where the variability sits.**
   - **Astra:** its uninformative default is exactly stable (50% in every session), and only mildly informative descriptions move, each on its own.
   - **Sol:** its default moves too (22–52%), so a source with no informative description is read differently from session to session.
3. **Model consequence.** The description-to-prior mapping needs a per-configuration, per-level between-session variance, not a single session shift. For passport claims, a description-derived prior should carry an interval of about ±0.15–0.20 (two SDs) unless measured over several sessions.
4. **Reading-guide candidates:**
   - **GPT-6 Astra:** "no information" means 50%, reliably. Priors from vague descriptions vary between sessions by about ±0.15.
   - **GPT-6 Sol:** priors from vague or uninformative descriptions vary between sessions by about ±0.2, and once diverged from its stated base rate. Supply explicit base rates.

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `68f7ddda8c2e3c47c9a2132f268734be3a9abcbd627c4c1383d8418ad53d7a1f` |
| execution.json | `27f352dc731ce6c2ab8f8707fc667ca1142f9e17b241f7733bd92bae19e9630d` |
| summary.json | `12da18cc77e15124d29b3094e6971cbc8a5c2fac93e96b940f46ec6d43708d06` |
| Estimator validation | `de9012b3b2b87faa65d571714862d658764be81becd69cdd67a8810f1dc1e8c6` |
