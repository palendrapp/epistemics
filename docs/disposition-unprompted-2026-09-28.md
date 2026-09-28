# Unprompted dossiers and weaker configurations on dossiers — 28 September 2026

Preregistration, written and committed before collection.

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
