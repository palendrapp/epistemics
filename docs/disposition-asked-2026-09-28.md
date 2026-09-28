# Default induction: asking for the base rate — 28 September 2026

Preregistration, written and committed before collection.

The [salience test](disposition-salience-2026-09-28.md) found that one sentence naming the mechanism restores Astra's and Sol's discount for clear cases. It did not restore the 50% default for ambiguous and irrelevant sources: those stayed at 0.17–0.33, and per session they were usually near 0 or at 0.50.

The earlier designs that produced a 50% default, the formal description modules and the prompted dossiers, also asked directly for each description's base rate: "Among outlets like X, what proportion relay …?" This test adds that question to the named dossiers. It asks whether being asked for an unstated rate is what produces the 50/50 default.

## Design

**Modules** `corroboration-asked` and `disclosure-asked` (disposition-tasks/0.8.0; design 0.6.0; variant `named-a`). Each description level has:
- **One base-rate question.** The wording is the description modules' question. The case is a brief naming the mechanism in the named variant's sentence, an "About us" line or company profile carrying the description, and two distractors. For disclosure the brief also gives the sector's routine omission rate.
- **Three forecasts from the named dossiers.** These are unchanged, with the named sentence in every brief.

The four anchors are unchanged, so each session has 24 cases. The implied prior is fitted from the forecasts only; the stated rates are compared with it, as in the description modules. Cases come in random order, so some forecasts for a description come before its rate question and some after, as in the earlier designs.

**Which three forecasts.** For relays, the three most informative of the four forecasts per level were kept. On three pilot seeds they recovered implied priors with correlation 0.93, against 0.92–0.94 for the first three. For disclosure the first three were kept (0.94–0.95).

**Validation.**
- **Offline recovery** (dispositions, design 0.6.0): passed every gate on both seeds. Asked relay: correlation 0.92, MAE 0.08, 90% coverage 0.96. Asked disclosure: 0.93–0.94, 0.07, 0.94. Stated rates recovered within 0.04 on average. All earlier recovery results are identical to 0.5.
- **Task validation** (0.8): passed on both seeds. Every earlier context reproduces 0.7 exactly, and the two asked contexts recovered within tolerance.
- **Rendering audit:** every asked case names the mechanism exactly once in its text. Only the base-rate questions mention it again.

**Collection** (preset `asked`):

| Setting | Value |
| --- | --- |
| Configurations | GPT-6 Astra and Sol, medium effort |
| Modules | relay and disclosure, asked |
| Sessions | three fresh sessions each, random order |
| Contexts | 12 |
| Tokens | about 0.55 million input tokens each; cap 10 million |

**Analysis.** `uv run python -m epistemics.ledger noticing <roots>` adds an "asked" block for each configuration and module:
- the asked mapping, its range, its irrelevant level and the mean stated rates;
- sessions in which every stated rate is within 0.10 of the implied prior;
- the distance to the prompted-dossier and named mappings;
- the error of the asked forecasts under five priors: the prompted, named and unprompted mappings, full neglect and 50%.

## Predictions

All values are pooled over each cell's three sessions, for Astra and Sol in both modules.
- **A1. The default is induced.** The irrelevant level lies between 0.35 and 0.65 in all four cells. It was 0.17–0.33 named without the question, and 0.50–0.52 in the prompted dossiers.
- **A2. Full restoration.** The asked mapping lies within 0.10 of the prompted-dossier mapping on average across levels, in all four cells. The named mapping was 0.12–0.22 away.
- **A3. Coherence.** Stated rates agree with the implied priors within 0.10 at every level, in at least 5 of 6 sessions per configuration.
- **A4. Exploratory.** Which prior best predicts the asked forecasts. No directional prediction.

If A1 fails, the remaining difference from the prompted dossiers includes the structure probes, which would be the next thing to add.

## Commitments (preregistration)

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint (0.8.0) | `3503041bb08bf1fa7e7773b73f814672827a9be5e824c308fa5717bb3b0b5f22` |
| Model and design fingerprint (dispositions, design 0.6.0) | `963dc5a025acdf32c8764f591648574da89ed67c10d43e3fa7673bfb66010bee` |
| Recovery validation 0.6, seed 20260927 | `97705a3be070e2e8c2b7fa6cac796c5c7f5cbfd7e09c9fa6b8bedb3f49319820` |
| Recovery validation 0.6, seed 20261027 | `da4cc12c2351998f94f245102cedf3644832641870003f94e15596c99607120d` |
| Task validation 0.8, seed 20260927 | `0a424624863e5b0ff07d4307906ac326d896d0ee2a42156af3f2685cfecb183e` |
| Task validation 0.8, seed 20261027 | `4e5b5cde6c28657ae15ec51ada4867473c6463bc1a3be74178246713f796553a` |
