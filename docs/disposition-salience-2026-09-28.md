# Salience: one sentence naming the mechanism — 28 September 2026

Preregistration, written and committed before collection; the results follow below.

**Result.** One sentence restores the discount for sources that look like copiers or have a motive to hide bad news. The aggregator went from 0–3% copied (unprompted) to 86–92%, and the bonus description from 22–24% selective to 60–73%. It does not restore the 50% default for ambiguous and irrelevant sources. Those stayed low: 0.17–0.33 pooled, and per session usually near 0 or at 0.50. S1 is supported; S2 and S3 are not.

The [unprompted dossiers](disposition-unprompted-2026-09-28.md) showed that Astra's and Sol's description-to-prior mappings depend on the mechanism being named. Without it:
- **Relays:** they treated a matching report from "an aggregator site with no reporters" as independent evidence (implied relay prior 0–3%).
- **Disclosure:** they read silence as only slightly bad news.

This test asks how little is needed to restore the mapping. It adds one sentence saying the mechanism exists, with no rate. In human work on correlation neglect and selection neglect, making the structure salient reduces neglect ([Enke & Zimmermann 2019](https://doi.org/10.1093/restud/rdx081); [Enke 2020](https://doi.org/10.1093/qje/qjaa012)). This test is inspired by that manipulation, not a replication of it.

## Design

**Variant** `named-a` of the unprompted modules (disposition-tasks/0.7.0). Every case is the unprompted dossier with one sentence added at the end of the brief:
- **Relays:** "Background: Some outlets relay another outlet's call instead of checking for themselves; a relayed call simply repeats the original call." This is the sentence the prompted dossiers used.
- **Disclosure:** "Background: Some companies share every on-target indicator and withhold every off-target one."

Nothing else changes: same items (design 0.5.0), same forecast-only questions, same track records, same routine omission rate, same paywalled headlines. The rendering audit checks that each named case contains the sentence exactly once and no other mechanism wording. A test checks that removing it recovers the unprompted case exactly.

Four differences from the prompted dossiers of the [transfer study](disposition-transfer-2026-09-28.md) remain:
- no probes or base-rate questions;
- track records instead of "when it checks for itself";
- every second story a paywalled headline;
- the disclosure brief lacks the prompted version's random-omission clause.

So a full restoration would mean one sentence is enough despite those differences.

**Validation.** Task validation 0.7 passed on both seeds. Every existing context reproduces 0.6 exactly, and the two named contexts recovered within tolerance. The model and design fingerprint is unchanged, so the unprompted designs' [recovery validation](disposition-unprompted-2026-09-28.md#design) applies.

**Collection** (preset `salience`):

| Setting | Value |
| --- | --- |
| Configurations | GPT-6 Astra and Sol, medium effort |
| Modules | relay and disclosure, named variant |
| Sessions | three fresh sessions each, random order |
| Contexts | 12 |
| Tokens | about 0.55 million input tokens each; cap 10 million |

**Analysis.** `uv run python -m epistemics.ledger noticing <roots>` reports the named sessions beside the unprompted and prompted ones for each configuration and module:
- the named mapping, its range and its irrelevant level;
- its mean distance from the prompted and unprompted mappings;
- the mean absolute error of the named forecasts under four priors: the prompted mapping, the unprompted mapping, full neglect and 50%.

## Predictions

All values are pooled over each cell's three sessions, for Astra and Sol in both modules.
- **S1. Restoration.** The strongly suggestive level's implied prior exceeds the strongly reassuring level's by at least 0.30, in all four cells.
- **S2. The default returns.** The irrelevant level lies between 0.35 and 0.65 in all four cells. It was 0.50–0.52 prompted and 0.00–0.02 unprompted.
- **S3. Full restoration.** The named mapping lies within 0.10 of the prompted-dossier mapping on average across levels, in all four cells.
- **S4. Exploratory.** Which prior best predicts the named forecasts. No directional prediction.

## Commitments (preregistration)

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint (0.7.0) | `c9681e5d3048860467821251e71bdc866f10ab78b8853d281b72ae7c5c60f24c` |
| Model and design fingerprint (unchanged, design 0.5.0) | `72e50660e24512d1bab9cdbdad1994b14ac3235b3a86c26f2b70b0ebcb3d6368` |
| Task validation 0.7, seed 20260927 | `d6ef8f607a49f013840e311f1b0d2465ce9ff00f340f2ebeebcabdc1815eeb09` |
| Task validation 0.7, seed 20261027 | `fa0f8f391d0c307e83b18b1b49217b00bff326456100f8f4264df5a42f7c90eb` |

## Results

**Collection.**
- **Completion:** all 12 contexts completed with the minimum 27 calls and no tool errors, in 82–218 seconds each.
- **Tokens:** 6,740,220 input tokens in total (6,307,072 cached), or 0.55–0.58 million per context.

The table regenerates with:

```bash
uv run python -m epistemics.ledger noticing output/disposition-transfer-20260928 output/disposition-unprompted-20260928 output/disposition-salience-20260928
```

Implied priors per description level, from strongly reassuring to strongly suggestive, pooled over three sessions per cell:

| Configuration | Module | Prompted dossier | Unprompted | Named, no rate | Named range | Named irrelevant level | Distance to prompted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Astra | relay | 0.07, 0.47, 0.50, 0.52, 0.93 | 0.00, 0.00, 0.00, 0.00, 0.00 | 0.01, 0.29, 0.33, 0.29, 0.86 | 0.85 | 0.33 | 0.138 |
| Sol | relay | 0.05, 0.48, 0.52, 0.50, 0.95 | 0.00, 0.00, 0.00, 0.00, 0.03 | 0.00, 0.19, 0.17, 0.14, 0.92 | 0.92 | 0.17 | 0.215 |
| Astra | disclosure | 0.27, 0.19, 0.50, 0.67, 0.75 | 0.00, 0.00, 0.00, 0.12, 0.22 | 0.08, 0.03, 0.25, 0.44, 0.60 | 0.52 | 0.25 | 0.195 |
| Sol | disclosure | 0.28, 0.18, 0.50, 0.62, 0.75 | 0.02, 0.19, 0.02, 0.07, 0.24 | 0.14, 0.09, 0.18, 0.62, 0.73 | 0.59 | 0.18 | 0.117 |

Mean absolute error of the named forecasts under each set of priors:

| Configuration | Module | Prompted mapping | Unprompted mapping | Full neglect | 50% |
| --- | --- | --- | --- | --- | --- |
| Astra | relay | 0.066 | 0.157 | 0.157 | 0.118 |
| Sol | relay | 0.107 | 0.117 | 0.121 | 0.165 |
| Astra | disclosure | 0.081 | 0.107 | 0.151 | 0.119 |
| Sol | disclosure | 0.076 | 0.124 | 0.159 | 0.126 |

**Sessions.**
- **Relay:** the irrelevant level split by session.
  - Astra: 0.10, 0.39 and 0.50.
  - Sol: 0.00, 0.00 and 0.50.
  - Within a session, the ambiguous levels followed the irrelevant one. Sol's first session gave 0.00–0.05 to every outlet except the aggregator (0.97), and its third gave 0.35–0.50 to the ambiguous outlets.
- **Disclosure:** the irrelevant level was 0.10–0.33 in every session.
- **Noise:** report noise stayed low (median τ 0.07 and 0.10 for relays, 0.10 and 0.19 for disclosure).

**Against the predictions:**
- **S1. Restoration:** supported in all four cells. The ranges were 0.85 and 0.92 for relays and 0.52 and 0.59 for disclosure. Unprompted they were 0.00–0.23; prompted, 0.47–0.90.
- **S2. The default returns:** not supported in any cell. The irrelevant level was 0.17–0.33 pooled, against the predicted 0.35–0.65. Astra's relay cell (0.33) came closest.
- **S3. Full restoration:** not supported in any cell. The named mapping differed from the prompted one by 0.12–0.22 on average. The extremes were nearly restored; the middle levels were not.
- **S4. Best predictor (exploratory):** the prompted mapping predicts the named forecasts best in all four cells, with errors of 6.6–10.7 points. The margin over the unprompted mapping is small for Sol's relays (10.7 against 11.7).

**Completion answers.** These are descriptive only.
- **Relay:** all six sessions named relaying or independence as the main ambiguity, and several said the relay chance was unstated.
- **Disclosure:** all six sessions named how much weight omissions or selectivity should get.

## Interpretation

1. **Naming the mechanism is enough to discount obvious cases.** With one sentence and no rate, both configurations again treated a report from the aggregator as mostly copied, and silence as bad news when the chief executive's bonus depended on the numbers. The practical rule is to say that sources can copy each other or that silence can be selective. A description alone does not do it, but one sentence naming the possibility does, for the clear-cut sources.
2. **Ambiguous sources get "probably independent", not 50/50.** Named without a rate, the mechanism was mostly applied only where a description made it likely. The 50% default seen in the formal modules and prompted dossiers did not come back reliably. It appeared in only two of six relay sessions.

   Those designs also asked directly for each description's base rate and probed the structure. The 50% default may be a response to being asked for an unstated rate. That is a hypothesis these data raise, not one they test.
3. **Taken together with the unprompted results,** mechanism awareness is now measured in three steps:
   - **Unprompted:** neglect.
   - **Named:** discount where a description suggests it.
   - **Named and asked:** a 50% default everywhere else.

## Next

- **Default induction:** add the base-rate question for each description (or the probes) to the named design, to test whether asking for the rate brings back the 50% default.
- **Reading guide:** the noticing readings now report the named result beside the unprompted one.

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `fd5a3fd6af55dc4cc2ad309fd249cb27caaf08062500f72a7e3e627a6391e99a` |
| execution.json | `abd03f8c235ad3165cf2d4c6e0bd9d6d13a83c277706d33fbde75442af75e96e` |
| summary.json | `ac39c1dc2943d93219599fb1c84a134d52b01e8e12f1a7d030bcc8e89864563b` |
