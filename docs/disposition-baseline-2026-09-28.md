# What sets the relay baseline — 28 September 2026

In the [description-to-prior retest](disposition-cues-acceptance-2026-09-28.md#retest), both GPT-6 configurations used a relay baseline of about 30% for an ordinary outlet in one fresh context, where the first run had used 50%. The extremes of the mapping did not move. This experiment asks what sets that baseline. It was designed and written down before collection. The results follow below.

## Design

disposition-tasks/0.3.2 adds case-order policies to the runner, with no change to rendering, the model or the analysis:
- **irrelevant-first:** the first checkpoint is the base-rate question for the irrelevant description ("Among outlets like Pinecrest Wire", an outlet "based in a city on the coast", "what proportion relay…?"). It measures the baseline before any other description has been seen.
- **reassuring-first / suggestive-first:** all eight strongly and mildly reassuring (or suggestive) cases come first, and the rest follow in random order.
- **shared order:** every run in a group gets the same order.

**Plan.** Relay cues, description set A (where the shift occurred), markets, 8 fresh contexts:

| Group | Order | Configurations | Contexts |
| --- | --- | --- | --- |
| 1 | irrelevant-first, one order shared by all four runs | Astra, Sol | two repeats each |
| 2 | reassuring-first, one shared order | Astra, Sol | one each |
| 3 | suggestive-first, one shared order | Astra, Sol | one each |

**Measures:**
- **Baseline:** the stated and implied priors at the irrelevant level.
- **Middle of the mapping:** the mean implied prior over the mild and irrelevant levels.
- **Unanchored default:** the very first answer in group 1.

**Predictions:**
- **Fixed default.** If the baseline is a default the configuration applies before seeing anything, the first answer in group 1 is the same in every run, and later irrelevant answers match it.
- **Anchoring.** If early descriptions anchor the baseline, the irrelevant and mild levels sit lower in group 2 than in group 3, by more than the variation between group 1's identical-order repeats.
- **Stochastic default.** If the baseline is drawn afresh in each context, it varies between group 1's identical-order repeats as much as between groups.

The contexts are single observations, so the result is descriptive. A difference of at least 0.10 in the irrelevant-level prior, replicated in both configurations, counts as an effect.

Implementation fingerprint `b63c5c93…a3f6`. Task validations 0.3.2 passed on two seeds.
