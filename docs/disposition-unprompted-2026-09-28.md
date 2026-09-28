# Unprompted dossiers and weaker configurations on dossiers — 28 September 2026

Preregistration, written and committed before collection; the results follow below.

**Result.** In these cases, when nothing mentioned relaying, Astra and Sol treated every pair of matching reports as independent. That included a second report from "an aggregator site with no reporters", which they had put at 93–95% copied when the mechanism was named. When nothing mentioned selective withholding, they read an update's silence as only slightly bad news, even when the chief executive's bonus depended on the numbers.

The sharp mapping from descriptions to priors found so far depends on being told that the mechanism exists. For relays, this is correlation neglect in the classic sense. Luna's and Terra's relay mappings carried over to dossiers; their disclosure mappings did not, and Terra became less coherent.

This record covers two tests in one collection:
- **Noticing.** The [dossier transfer](disposition-transfer-2026-09-28.md) found that the formal description-to-prior mappings carry over to realistic documents. There the documents still stated the mechanism: some outlets relay one another, and some companies withhold bad indicators. This test removes that statement. It asks whether Astra and Sol raise relaying or selective withholding themselves, when only the source descriptions suggest it.
- **Weaker configurations on dossiers.** Luna and Terra run the same prompted dossiers as Astra and Sol did. The question is whether their formal mappings, and Luna's gap between stated and applied base rates, carry over.

Human studies motivate the first test. People treat correlated reports as independent, and they neglect information that was selected out, unless the structure is made salient ([Enke & Zimmermann 2019](https://doi.org/10.1093/restud/rdx081); [Enke 2020](https://doi.org/10.1093/qje/qjaa012)). Receivers also read too little into what a sender leaves undisclosed ([Jin, Luca & Martin 2021](https://doi.org/10.1257/mic.20180217)). This test is inspired by that work, not a replication of it. Its cases, incentives and respondents differ.

## Design

**Unprompted modules** (disposition-tasks/0.6.0, `corroboration-unprompted` and `disclosure-unprompted`; design 0.5.0). Each case keeps the dossier format and description set A: brief, evidence documents, a masthead or company-profile line carrying the description, and two distractors. What changes:
- **No mechanism statement.** No document says that outlets relay one another, or that some companies share good indicators and withhold bad ones. The rendering audit fails if any unprompted case contains a mechanism word ("relay", "withh", "selective", "repeat", "copies", "copied", "for itself", "for themselves", "at random", "on purpose", "strategic"). It passes on all 48 cases.
- **Forecasts only.** Every question asks for the probability that demand is high. There are no base-rate questions and no structure probes, since both would name the mechanism.
- **No wording cues.** The second outlet's story is always a paywalled headline, so wording carries no copying signal. It is still dated after the first story.
- **Relay briefs** state each outlet's track record ("Orchard Brief's demand calls are correct 90% of the time"). The prompted version said "when it checks for itself".
- **Disclosure briefs** give the sector's routine omission rate ("a given indicator is left out of a quarterly update 50% of the time"). This is the rate the observer model treats as random omission.

Each description level has four forecasts in which the relay (or selective) reading and the independent (or random) reading differ. Four anchors fix sensitivity, bias and noise: single reports and conflicting reports for relays, and updates that share a below-target indicator or withhold nothing for disclosure. Neither relaying nor selective withholding can explain the anchors.

The fit is the description-module fit: one implied prior per level, with shared γ, bias and τ. An implied prior of 0 at every level is full neglect, meaning the respondent never considers that an outlet might be copying or that silence might be selective.

**Design choice made during validation.** The first relay design used second-outlet accuracies of 80–85%. It recovered implied priors with correlation 0.89 on one pilot seed, below the 0.90 gate. Accuracies of 90% and 95%, with priors leaning against the reports, spread the relay and independent readings apart. Correlation rose to 0.93. The disclosure design was unchanged.

**Validation.**
- **Offline recovery** (dispositions, design 0.5.0): passed every gate on both seeds.

  | Module | Correlation | MAE | 90% coverage |
  | --- | --- | --- | --- |
  | Unprompted relay | 0.93 | 0.08 | 0.94–0.96 |
  | Unprompted disclosure | 0.96 | 0.05–0.06 | 0.94–0.96 |

- **Task validation** (0.6): passed on both seeds, with synthetic collections for the two new modules recovered within tolerance.

  The two new contexts are added after the existing ones, so every existing context reuses its 0.5 draws, and its estimates are identical to the 0.5 validation. In a first attempt the new contexts were inserted before the existing ones, which re-drew their random numbers. One existing context then failed: the disclosure learning-low learner on seed 20260927. Learning was detected (P = 0.96), but its start interval collapsed to the single grid point 0.45, next to the true 0.50. Each learning context is checked by 90%-interval coverage, so an occasional miss is expected. The miss is recorded here, not hidden. It says that at low noise the learned-start interval can be one grid step too narrow.

**Collection** (preset `unprompted`, 24 contexts):

| Group | Configurations | Modules | Sessions |
| --- | --- | --- | --- |
| Noticing | GPT-6 Astra and Sol, medium effort | relay and disclosure, unprompted | 3 each, random order |
| Weaker configurations | GPT-5.6 Luna and Terra | relay and disclosure, prompted dossiers | 3 each, random order |

Tokens are about 0.5–0.6 million input tokens per context; the cap is 18 million.

**References.**
- For noticing: Astra's and Sol's prompted dossier sessions from the [transfer](disposition-transfer-2026-09-28.md), three per cell.
- For Luna and Terra: their random-order set-A formal sessions from the [weaker-configuration study](disposition-weaker-cues-2026-09-28.md), three per cell.

  | Configuration | Module | Formal mapping | Coherent sessions | Median τ |
  | --- | --- | --- | --- | --- |
  | Luna | relay | 0.04, 0.33, 0.40, 0.51, 0.91 | 1 of 3 | 0.48 |
  | Luna | disclosure | 0.49, 0.42, 0.62, 0.70, 0.71 | 0 of 3 | 0.82 |
  | Terra | relay | 0.16, 0.31, 0.38, 0.58, 0.89 | 3 of 3 | 0.44 |
  | Terra | disclosure | 0.30, 0.22, 0.46, 0.70, 0.75 | 2 of 3 | 0.19 |

**Analysis.** The noticing tables come from:

```bash
uv run python -m epistemics.ledger noticing <roots>
```

It reports, per configuration and module:
- both mappings, with the strongly suggestive minus strongly reassuring range and the irrelevant level;
- per-session unprompted mappings with lower 90% bounds;
- the mean absolute error of the unprompted forecasts under three priors: the prompted mapping, full neglect (0 at every level) and indifference (50% at every level).

The Luna and Terra tables come from `uv run python -m epistemics.ledger transfer <roots>` and `cues-summary`, as in the transfer study.

## Predictions

**Noticing (Astra and Sol, unprompted dossiers).** Values are pooled over each cell's three sessions.
- **U1. Noticing.** The strongly suggestive level's implied prior exceeds the strongly reassuring level's by at least 0.30, in all four configuration × module cells.
- **U2. No default without the mechanism.** The irrelevant level's implied prior is at most 0.20 in all four cells, against 0.50 in the prompted dossiers. The 50% default seen so far would then be a response to being told that a mechanism exists without its rate.
- **U3. Attenuation.** The unprompted range (strongly suggestive minus strongly reassuring) is smaller than the prompted range in all four cells.
- **U4. Exploratory.** Which of the prompted mapping, full neglect and indifference best predicts the unprompted forecasts. No directional prediction.

If all five levels sit at or below 0.10 in a cell, that cell is full neglect: U1 fails there, and the result is reported as neglect.

**Weaker configurations (Luna and Terra, prompted dossiers).**
- **W1. Predictive gain over neutral.** Own formal priors predict dossier answers with lower error than 50% priors, in all four configuration × module cells. This replicates X2 of the transfer study.
- **W2. Coherence carries over.** Terra's stated and implied priors agree within 0.10 in at least 4 of its 6 dossier sessions; Luna's in at most 2 of 6.
- **W3. Exploratory.** Report noise and mapping differences compared with the formal sessions. No directional prediction.

## Commitments (preregistration)

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint (0.6.0) | `7402be221e634f43ca9b68ae4276e20fbefd5eb106b0a21ca0e68e619a6eddf6` |
| Model and design fingerprint (dispositions, design 0.5.0) | `72e50660e24512d1bab9cdbdad1994b14ac3235b3a86c26f2b70b0ebcb3d6368` |
| Task validation 0.6, seed 20260927 | `cd00973d5a41db26d1a15f38b2367aec1c6bbab1808cf5480f7ee516ae49ca6d` |
| Task validation 0.6, seed 20261027 | `3b3fd0b575899b202b96a483ed8bd2bf1fdf31ea69e290e2aaaa6b5c0d445e29` |
| Recovery validation 0.5, seed 20260927 | `834ffee4a37f1bf02be69c3a0809072ab36b95effb99782c4b10533f0de387b4` |
| Recovery validation 0.5, seed 20261027 | `62a679d5d108b6ea47b3b18250f52ed8084c1bf20fb0bd88e7b8f52e2b526e21` |

## Results

**Collection.**
- **Completion:** all 24 contexts completed with the minimum 27 calls and no tool errors, in 86–163 seconds each.
- **Tokens:** 12,879,782 input tokens in total (11,908,480 cached), or 0.49–0.56 million per context.

The tables regenerate with:

```bash
uv run python -m epistemics.ledger noticing output/disposition-transfer-20260928 output/disposition-unprompted-20260928
```

```bash
uv run python -m epistemics.ledger transfer output/disposition-unprompted-20260928 output/disposition-transfer-20260928 output/disposition-cues-20260928 output/disposition-cues-retest-20260928 output/disposition-variance-20260928 output/disposition-weaker-cues-20260928
```

```bash
uv run python -m epistemics.ledger cues-summary output/disposition-unprompted-20260928
```

### Noticing (Astra and Sol)

Implied priors per description level, from strongly reassuring to strongly suggestive, pooled over three sessions. The error columns give the mean absolute error of the unprompted forecasts under each set of priors.

| Configuration | Module | Prompted dossier | Unprompted dossier | Unprompted range | Unprompted irrelevant level | Error, prompted | Error, full neglect | Error, 50% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Astra | relay | 0.07, 0.47, 0.50, 0.52, 0.93 | 0.00, 0.00, 0.00, 0.00, 0.00 | 0.00 | 0.00 | 0.223 | 0.002 | 0.242 |
| Sol | relay | 0.05, 0.48, 0.52, 0.50, 0.95 | 0.00, 0.00, 0.00, 0.00, 0.03 | 0.03 | 0.00 | 0.217 | 0.006 | 0.237 |
| Astra | disclosure | 0.27, 0.19, 0.50, 0.67, 0.75 | 0.00, 0.00, 0.00, 0.12, 0.22 | 0.22 | 0.00 | 0.191 | 0.039 | 0.210 |
| Sol | disclosure | 0.28, 0.18, 0.50, 0.62, 0.75 | 0.02, 0.19, 0.02, 0.07, 0.24 | 0.23 | 0.02 | 0.198 | 0.045 | 0.211 |

**Sessions.**
- **Relay:** all six sessions put every description, the aggregator included, at 0.00, except one Sol session that gave the aggregator 0.09.
- **Disclosure:** the small suspicion comes from single sessions. One Astra session put the financing and bonus descriptions at 0.20 and 0.40, and another at 0.16 and 0.26; the third put every level at 0. One Sol session gave 0.55 to "a reputation for plain, complete reporting" and 0.62 to the bonus description; its other two gave at most 0.10.
- **Noise:** report noise stayed low (median τ 0.05 for relays, 0.11 and 0.17 for disclosure), so these near-zero priors are precise.

**Against the predictions:**
- **U1. Noticing:** not supported in any cell.
  - **Relay:** both cells meet the preregistered definition of full neglect, with every level at or below 0.10.
  - **Disclosure:** the ranges of 0.22 and 0.23 fall short of 0.30, so these cells show partial suspicion, neither noticing nor full neglect.
- **U2. No default without the mechanism:** supported in all four cells. The irrelevant level was 0.00–0.02, against 0.50–0.52 when the mechanism was named.
- **U3. Attenuation:** supported in all four cells. The unprompted ranges were 0.00–0.23, against 0.47–0.90 prompted.
- **U4. Best predictor (exploratory):** full neglect predicts the unprompted forecasts best in every cell, with errors of 0.2–4.5 points. The prompted mapping gives 19–22 points and 50% priors 21–24 points.

**Completion answers.** These are descriptive only; they are self-reports after the fact, not measurements.
- **Relay:** in five of six sessions the agent named independence of the two reports as an assumption or an ambiguity. Three of them mentioned the aggregator or the source descriptions, for example "whether reports from different sources were independent, especially when a later headline came from an aggregator". All three Astra sessions said they "assumed … conditionally independent reports".
- **Disclosure:** all six sessions described reporting incentives, and five of them omissions, as unquantified. One Astra session said it "treated omissions as uninformative".

On this descriptive evidence, the agents raised the possibility, but their forecasts did not act on it. This pattern resembles Luna's "detect but don't discount" behaviour in the [research-world positive control](research3-positive-control-2026-09-27.md).

### Weaker configurations (Luna and Terra, prompted dossiers)

| Configuration | Module | Formal mapping | Dossier mapping | Mapping difference | Error, own formal | Error, pooled | Error, 50% | Coherent sessions | Median τ, formal → dossier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Luna | relay | 0.04, 0.33, 0.40, 0.51, 0.91 | 0.09, 0.42, 0.51, 0.52, 0.90 | 0.052 | 0.054 | 0.056 | 0.122 | 0 of 3 | 0.48 → 0.48 |
| Luna | disclosure | 0.49, 0.42, 0.62, 0.70, 0.71 | 0.32, 0.38, 0.41, 0.50, 0.49 | 0.168 | 0.149 | 0.141 | 0.137 | 0 of 3 | 0.82 → 0.47 |
| Terra | relay | 0.16, 0.31, 0.38, 0.58, 0.89 | 0.05, 0.37, 0.52, 0.41, 0.80 | 0.114 | 0.075 | 0.061 | 0.117 | 1 of 3 | 0.44 → 0.48 |
| Terra | disclosure | 0.30, 0.22, 0.46, 0.70, 0.75 | 0.35, 0.30, 0.57, 0.64, 0.68 | 0.073 | 0.090 | 0.088 | 0.083 | 1 of 3 | 0.19 → 0.33 |

**Against the predictions:**
- **W1. Predictive gain over neutral:** supported for relays and not for disclosure (two of four cells).
  - **Relay:** own formal priors beat 50% for both (Luna 5.4 against 12.2 points; Terra 7.5 against 11.7).
  - **Disclosure:** 50% priors were slightly better for both (Luna 13.7 against 14.9; Terra 8.3 against 9.0). Luna's disclosure mapping, already flat in the formal module (range 0.22), shifted down and flattened further (range 0.17).
- **W2. Coherence:** supported for Luna, not for Terra.
  - **Luna:** 0 of 6 dossier sessions coherent, as predicted.
  - **Terra:** 2 of 6 coherent, against at least 4 predicted; it was 5 of 6 in the formal module. In one Terra disclosure session every stated and implied prior was exactly 50%, so the descriptions were ignored altogether. In another, stated priors of 0.10–0.70 sat beside implied priors of 0.34–0.92.
- **W3. Noise and mapping differences (exploratory):** Terra's report noise rose on disclosure dossiers (τ 0.19 to 0.33), and its relay mapping moved 0.11 from the formal one. Luna's relay mapping transferred within about 0.05.

## Interpretation

1. **Description-to-prior mappings are conditional on the mechanism being named.** The formal and prompted-dossier results showed Astra and Sol turning descriptions into sharp priors. The comparison here shows that this happens only when a case says the mechanism exists. Unprompted, the same descriptions left the relay prior at zero and moved the disclosure prior only a little.

   For a reader of these agents' forecasts, the product reading is direct. If reports may be copies, or silence may be selective, the agent needs to be told. A description that makes a source look like a copier is not enough.
2. **The 50% default is a response to an unquantified mechanism, not a general prior.** Without the mechanism, the irrelevant description got 0%, not 50%.
3. **The relay neglect is precise, not noisy.** Near-zero noise and near-zero priors in every relay session make it a consistent behaviour of these configurations in this format.
4. **The weaker configurations transfer less.**
   - **Relays:** both Luna's and Terra's relay mappings carried over, and their formal priors beat neutral ones.
   - **Disclosure:** neither model's disclosure mapping carried over.
   - **Coherence:** Terra's coherence between stated and applied priors did not survive the move to documents. Luna stayed incoherent, as in the formal module.
5. **Limits.**
   - **Relay briefs** give the second outlet an explicit track record (90% or 95%). That may invite reading it as an independent source.
   - **Disclosure briefs** give a routine sector omission rate. That may frame silence as benign.

   Both choices were needed to fit the model on its usual scale. The results hold for this design, and a design without them would need a different measurement model. There are three sessions per cell.

## Next

- **Salience:** add one sentence to the unprompted brief that names the mechanism without a rate, to test how little prompting restores the mapping. This is the step from here toward the salience manipulations in the human literature.
- **Reading guide:** add the noticing readings, now drafted from these results.

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `3dccd27455111a97b82510cbc1227e865afe2ae313aae8368bc5efdc09e70dc6` |
| execution.json | `7babce5f6ccb0281a0dd6e21f7ca23c84f0612aa1106a291c6fb1d2416888009` |
| summary.json | `2286b00a889e589f34801e15bfc87386d41c1d5f00cfe583f1eca2cae94d68f3` |
