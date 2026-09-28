# Dossier transfer of description priors — 28 September 2026

Preregistration, written and committed before collection; the results follow below.

**Result.** The formal mappings transfer. Own formal priors predicted dossier answers within 1.4–4.0 points on average, against 7.7–9.2 for a neutral 50% observer (X2 supported in all four cells). Mappings differed by only 0.025–0.060. The rank-agreement condition of X1 failed for relays, where the middle levels are nearly tied. This is the first transfer test in the [generative model](epistemic-generative-model.md#6-transfer-layer-naturalistic) plan. It asks whether the description-to-prior mappings measured in the formal modules predict answers when the same cases arrive as realistic documents.

## Design

The dossier modules (disposition-tasks/0.5.0; `epistemics.disposition_tasks.dossier`) use exactly the items, numbers and questions of the relay and disclosure description modules, set A. Only the presentation changes. Each case becomes a small bundle:
- **Case brief:** the prior, the reference rates, and the general mechanism (relaying, or selective against random omission) as a background fact.
- **Evidence:**
  - relays: two markets stories, the second with an "About" masthead line carrying the description;
  - disclosure: a shareholder letter naming which KPIs came in on or below target, and a company profile carrying the description.
- **Distractors:** two, about unrelated companies.
- **Order:** documents in a fixed shuffled order after the brief.

When the wording cue is "cannot be compared", the second story is a paywalled headline. Identical and different wording are shown as actual sentences, and the brief states the relay and independent wording rates. The second story is always dated after the first, as a relay requires, and that could itself suggest relaying.

The mechanism stays stated. A test of whether agents notice relaying unprompted needs a forecast-only design, because probes and base-rate questions name the mechanism. That is left for later.

**Collection** (preset `transfer`):

| Setting | Value |
| --- | --- |
| Configurations | GPT-6 Astra and Sol, medium effort |
| Modules | relay dossier, disclosure dossier |
| Sessions | three fresh sessions each, random order |
| Contexts | 12 |
| Tokens | about 0.6–0.7 million input tokens each (dossiers are 1.7 times longer than formal cases); cap 12 million |

**Formal reference.** Each configuration's mean implied prior per level over its random-order set-A formal sessions: 8 each for relays (first run, retest, variance study) and 2 each for disclosure (first run, retest). Pooled priors average all configurations with formal set-A sessions: Astra, Sol, Luna and Terra.

**Analysis** (`uv run python -m epistemics.ledger transfer <roots>`):
- **Mapping transfer:** the mean dossier mapping against the formal mapping, as mean absolute difference per level and rank agreement.
- **Prediction:** mean absolute error, in probability, between each dossier probe and forecast and the probability an exact observer predicts from three candidate priors: the configuration's own formal mapping, the pooled mapping, and 50% at every level.

## Predictions

- **X1. Mapping transfer.** For Astra and Sol in both modules, the dossier mapping lies within 0.10 of the formal mapping on average across levels, with rank agreement of at least 0.8.
- **X2. Predictive gain over neutral.** Own formal priors predict dossier answers with lower error than 50% priors, in all four configuration × module cells.
- **X3. Own against pooled.** Exploratory, no directional prediction: the set-A mappings of Astra and Sol are similar.

The implementation fingerprint is `277c5125…aef3`. Task validations 0.5 passed on two seeds; see Commitments.

## Commitments (preregistration)

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint | `277c5125eaf5873783fd4e1439d82d184236fea157e8977ba0812d95e91aaef3` |
| Task validation 0.5, seed 20260927 | `b5a23f5d327bc02beea5d6bfa46916d046f02edacc292e2199bda900942af892` |
| Task validation 0.5, seed 20261027 | `0ff7a3cef68ef457087061f5074722bbaf735d8d0557ee4f4608c9af184dccd1` |

## Results

**Collection.** All 12 sessions completed with the minimum 27 calls and no tool errors, in 97–154 seconds. They used 6,704,969 input tokens (6,290,816 cached), or 0.54–0.58 million per session. The tables regenerate with:

```bash
uv run python -m epistemics.ledger transfer output/disposition-transfer-20260928 output/disposition-cues-20260928 output/disposition-cues-retest-20260928 output/disposition-variance-20260928 output/disposition-weaker-cues-20260928
```

```bash
uv run python -m epistemics.ledger cues-summary output/disposition-transfer-20260928
```

| Configuration | Module | Formal mapping | Dossier mapping | Mapping difference | Rank agreement | Error, own formal | Error, pooled | Error, 50% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Astra | relay | 0.05, 0.49, 0.48, 0.47, 0.92 | 0.07, 0.47, 0.50, 0.52, 0.93 | 0.025 | 0.60 | 0.014 | 0.020 | 0.077 |
| Sol | relay | 0.04, 0.44, 0.43, 0.54, 0.92 | 0.05, 0.48, 0.52, 0.50, 0.95 | 0.041 | 0.70 | 0.027 | 0.033 | 0.092 |
| Astra | disclosure | 0.23, 0.20, 0.50, 0.59, 0.75 | 0.27, 0.19, 0.50, 0.67, 0.75 | 0.026 | 1.00 | 0.021 | 0.025 | 0.086 |
| Sol | disclosure | 0.15, 0.10, 0.50, 0.70, 0.75 | 0.28, 0.18, 0.50, 0.62, 0.75 | 0.060 | 1.00 | 0.040 | 0.030 | 0.083 |

Errors are the mean absolute difference, in probability, between each dossier probe or forecast and the exact observer's prediction from each set of priors.

**Across all 12 dossier sessions:**
- **Coherence:** stated and implied priors agreed within 0.10.
- **Irrelevant level:** 0.50–0.52 in every session. That includes Sol, whose irrelevant relay outlet ranged from 0.22 to 0.52 across the formal variance sessions.
- **Report noise:** at the 0.05 floor, except Sol's relay dossiers (median 0.37).
- **The reassuring reversal carried over:** on average, and in 5 of 6 disclosure sessions, both configurations treated "a reputation for plain, complete reporting" as more reassuring than "checked by an independent auditor", as they had in the formal module.

**Against the predictions:**
- **X1 (within 0.10 and rank agreement at least 0.8):**
  - **Distance:** met in all four cells, with mapping differences of 0.025–0.060.
  - **Rank agreement:** met for disclosure (1.00 for both). Not met for relays (0.60 and 0.70). The three middle relay levels lie within 0.05 of one another in both presentations, so their order flips with small changes.

  As preregistered, X1 holds for disclosure and fails for relays. The failure is a property of near-tied levels, where rank agreement was the wrong criterion, not a large difference.
- **X2 (own formal priors beat 50%):** supported in all four cells. Errors were 0.014–0.040 against 0.077–0.092.
- **X3 (own against pooled), exploratory:** own priors were better in three cells by 0.003–0.006. Pooled priors were better for Sol's disclosure (0.030 against 0.040). Sol's formal disclosure mapping rests on two sessions and was more extreme than its dossier mapping.

## Interpretation

1. **The formal description-to-prior mappings transfer to realistic documents.** A 24-case formal session's mapping predicts dossier answers to within 1.4–4.0 probability points on average. A neutral 50% observer is off by 7.7–9.2. The mapping is a property of the configuration, not of the task format, at least when the mechanism is stated.
2. **Where the mappings are least stable, transfer is noisiest,** which is what the variance study predicts: the relay middle levels, and Sol's disclosure extremes measured from only two formal sessions. Configuration-specific priors add little over pooled ones here, because Astra and Sol map descriptions similarly.
3. **Dossiers did not add variability.** If anything, both configurations were steadier in the realistic format: the irrelevant level stayed at 50% throughout. Realistic distractors and document structure did not disturb the mapping.
4. **Limits.**
   - **Stated mechanism:** the mechanism was stated in the brief. Whether agents consider relaying or selective disclosure unprompted is not yet tested.
   - **Size:** three dossier sessions per cell, and two formal disclosure sessions per configuration.

## Next

- **Unprompted variant:** a forecast-only dossier design with no mechanism statement, to test noticing as well as using.
- **Weaker configurations on dossiers:** Luna and Terra, where the formal mapping and the stated–implied gap may transfer differently.
- **Reading-guide draft** from the passport.

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `4978ed01addf5384849e7801a8a8a063ba37d19d5e0ddba0ba32da577848368e` |
| execution.json | `b2d5abdd2cf8a414f7050a4304e9a4c749821e1633909ed902b1b2d9b5c37057` |
| summary.json | `755e47070b8406ef42ce1fa7f88353987414ec3422c06e8045a3f1b49e7a1f47` |
