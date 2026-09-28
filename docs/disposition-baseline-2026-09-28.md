# What sets the relay baseline — 28 September 2026

In the [description-to-prior retest](disposition-cues-acceptance-2026-09-28.md#retest), both GPT-6 configurations used a relay baseline of about 30% for an ordinary outlet in one fresh context, where the first run had used 50%. The extremes of the mapping did not move. This experiment asks what sets that baseline. It was designed and written down before collection. The results follow below.

**Result.** Early descriptions did not anchor the baseline.
- **Astra** held a fixed 50% default for an uninformative outlet.
- **Sol**, asked cold, assumed most outlets check for themselves (35–40%). After seeing graded descriptions, it put the uninformative outlet at 50%.

What moves across contexts are the ambiguous, mild descriptions. They are judged relative to the other outlets in view, while the extremes stay fixed.

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

## Results

**Collection.** All 8 contexts completed with the minimum 27 calls and no tool errors, in 83–121 seconds. They used 4,200,945 input tokens (3,904,384 cached).

Relay cues, set A. Levels run from strongly reassuring to strongly suggestive, with the irrelevant level in the middle. Implied priors:

| Order | Configuration | First checkpoint and answer | Irrelevant: stated / implied | Levels |
| --- | --- | --- | --- | --- |
| irrelevant-first (repeat 3) | Astra | irrelevant base rate: 0.50 | 0.50 / 0.50 | 0.05, 0.60, 0.50, 0.55, 0.95 |
| irrelevant-first (repeat 4) | Astra | irrelevant base rate: 0.50 | 0.50 / 0.51 | 0.05, 0.51, 0.51, 0.41, 0.95 |
| irrelevant-first (repeat 3) | Sol | irrelevant base rate: 0.40 | 0.40 / 0.42 | 0.05, 0.37, 0.42, 0.51, 0.89 |
| irrelevant-first (repeat 4) | Sol | irrelevant base rate: 0.35 | 0.35 / 0.35 | 0.00, 0.30, 0.35, 0.45, 0.90 |
| reassuring-first | Astra | strongly reassuring probe: 0.10 | 0.50 / 0.50 | 0.06, 0.48, 0.50, 0.60, 0.95 |
| reassuring-first | Sol | strongly reassuring probe: 0.07 | 0.50 / 0.50 | 0.05, 0.50, 0.50, 0.70, 0.95 |
| suggestive-first | Astra | mildly suggestive pair: 0.21 | 0.50 / 0.50 | 0.05, 0.40, 0.50, 0.30, 0.90 |
| suggestive-first | Sol | mildly suggestive pair: 0.25 | 0.50 / 0.52 | 0.05, 0.28, 0.52, 0.51, 0.90 |

**Against the predictions:**
- **Fixed default.**
  - **Astra:** yes. It answered 50% for the uninformative outlet when asked first, in both identical-order repeats, and held 50% at the irrelevant level in all four of its contexts here.
  - **Sol:** partly. Asked first, it gave a lower default, 40% and 35%, and held its first answer through each context. The two identical-order repeats differ by only 0.05.
- **Anchoring by early descriptions:** not supported. The irrelevant level was 50% after eight reassuring cases and 50–52% after eight suggestive ones.
- **Stochastic default:** small within identical orders (0.00–0.07). For Sol, it is smaller than the difference between asking the baseline first (0.35–0.42) and asking it after other descriptions (0.50–0.52).

**The mild descriptions are the unstable part.** Across the twelve relay set-A contexts (first run, retest and these eight):
- **The extremes are fixed:** strongly reassuring 0.00–0.07, strongly suggestive 0.82–0.95.
- **The mild levels move:** "sometimes runs its own surveys of retailers" ranges 0.28–0.60, and "a small newsletter with two analysts" 0.30–0.70.
- **Order matters for the newsletter:** when the newsletter was the first outlet judged (this suggestive-first order, and the retest), Astra put it at about 30%. When other outlets had been judged first, it put the same newsletter at 41–60%.

## Interpretation

1. **Astra has a fixed indifference default.** An outlet described by an irrelevant detail gets 50%, whatever came before it. The single exception, the retest (30%), placed the irrelevant case directly after the first mild judgement, and is not explained by these orders.
2. **Sol's default depends on whether it has anything to compare against.** Asked cold, it assumes most outlets check for themselves (35–40%) and keeps that value. Once it has seen graded descriptions, it places the uninformative outlet at the midpoint of the range it has built (50%).
3. **Ambiguous descriptions are judged relative to the other outlets in view.** *Correction: the [confirmatory test](disposition-range-2026-09-28.md#results) did not support this. Varying the comparison set left the targets unchanged on average; the variation is between contexts.* The strong descriptions are read the same way in every context. A description whose meaning depends on the comparison class, such as a two-analyst newsletter, is judged against the outlets already seen. This is the pattern that relative-judgement accounts predict for human magnitude judgements: range–frequency theory ([Parducci 1965](https://doi.org/10.1037/h0022602)) and decision by sampling ([Stewart, Chater & Brown 2006](https://doi.org/10.1016/j.cogpsych.2005.10.003)).
4. **Implications for the model.** A prior mapped from a description has three parts:
   - a context-free component, for descriptions whose meaning is fixed;
   - a relative component, for descriptions judged against the outlets in view;
   - a default for uninformative sources, fixed for Astra and comparison-dependent for Sol.

   The fixed-mapping model fits the extremes. The middle needs a relative-judgement term, estimable by varying the comparison set within a context.

## Next

- **Relative-judgement module.** Vary the comparison set directly: the same ambiguous descriptions after a strong-reassuring set or after a strong-suggestive set, several of each, both configurations. Fit a range-based model, with a prior that depends on the description's rank within the context's range, against the fixed mapping.
- **Weaker configurations** on the cue modules.
- **Dossier transfer,** with source descriptions from the fixed extremes first, where the mapping is stable.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint | `b63c5c937a5f42f95177c335827024a1ead3f6dcc586ba33ce20ed13e235a3f6` |
| Task validation 0.3.2, seed 20260927 | `8ce4784213cb164d860154fb95a01160af4721df0e5280a2d2c75ad650e0cfed` |
| Task validation 0.3.2, seed 20261027 | `0a9ba09efd0a23b232db7030680707372c6f30d69ab3971ea67abd0cd9e4fbca` |
| plan.json | `88677ad0d7ccc2f8fadb07539531b2f5302b76092fa1202c0c740d923182435c` |
| execution.json | `cbc38d7aaf782d3776f21f9c1f8ac8cf867d31404e6fe6f0151485bf5ae480f3` |
| summary.json | `3cfd353a4325fe156041bd2f3d71eff588c4db357de8ed8e50449d65b00cc4e3` |

Raw collections and transcripts remain private and outside Git. Model revisions are requested aliases, and execution is operator-asserted.
