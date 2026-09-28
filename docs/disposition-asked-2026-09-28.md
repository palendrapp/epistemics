# Default induction: asking for the base rate — 28 September 2026

Preregistration, written and committed before collection; the results follow below.

**Result.** Asking for each description's base rate split the two configurations:
- **Astra:** being asked brought back the 50% default and the prompted mapping. Its irrelevant level rose to 0.38 for relays and 0.48 for disclosure, its mappings came within 0.04–0.08 of the prompted ones, and its stated rates matched its forecasts in 5 of 6 sessions.
- **Sol:** for relays, its stated rates for ambiguous outlets returned to about 40%, but its forecasts kept acting on 9–17%. None of its three relay sessions was coherent; before this, Sol had been coherent in 22 of 24 description and dossier sessions. For disclosure, Sol was coherent, but its default only partly returned (0.29).

A1–A3 hold for Astra and fail for Sol.

**Update after the retest.** Three fresh Sol sessions did not reproduce the gap's size: +0.04 at the ambiguous levels, against +0.25 here ([retest with probes](disposition-probed-2026-09-28.md)). Across six sessions, the gap is wide in two and small in four. The claims below about Sol's gap describe these three sessions; the gap is intermittent, not a stable trait.

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

## Results

**Collection.**
- **Completion:** all 12 contexts completed with the minimum 27 calls and no tool errors, in 82–124 seconds each.
- **Tokens:** 6,714,512 input tokens in total (6,279,424 cached), or 0.55–0.58 million per context.

The table regenerates with:

```bash
uv run python -m epistemics.ledger noticing output/disposition-transfer-20260928 output/disposition-unprompted-20260928 output/disposition-salience-20260928 output/disposition-asked-20260928
```

The prompted and named mappings are repeated from the [transfer](disposition-transfer-2026-09-28.md) and [salience](disposition-salience-2026-09-28.md) studies. Levels run from strongly reassuring to strongly suggestive, pooled over three sessions per cell.

| Configuration | Module | Prompted dossier | Named, no rate | Asked: implied | Asked: stated | Irrelevant level | Distance to prompted | Coherent sessions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Astra | relay | 0.07, 0.47, 0.50, 0.52, 0.93 | 0.01, 0.29, 0.33, 0.29, 0.86 | 0.02, 0.32, 0.38, 0.43, 0.94 | 0.02, 0.32, 0.38, 0.43, 0.93 | 0.38 | 0.080 | 3 of 3 |
| Sol | relay | 0.05, 0.48, 0.52, 0.50, 0.95 | 0.00, 0.19, 0.17, 0.14, 0.92 | 0.01, 0.17, 0.09, 0.14, 0.78 | 0.01, 0.38, 0.37, 0.40, 0.93 | 0.09 | 0.261 | 0 of 3 |
| Astra | disclosure | 0.27, 0.19, 0.50, 0.67, 0.75 | 0.08, 0.03, 0.25, 0.44, 0.60 | 0.34, 0.17, 0.48, 0.59, 0.75 | 0.33, 0.17, 0.50, 0.63, 0.75 | 0.48 | 0.039 | 2 of 3 |
| Sol | disclosure | 0.28, 0.18, 0.50, 0.62, 0.75 | 0.14, 0.09, 0.18, 0.62, 0.73 | 0.09, 0.08, 0.29, 0.52, 0.65 | 0.09, 0.10, 0.30, 0.53, 0.67 | 0.29 | 0.139 | 3 of 3 |

Mean absolute error of the asked forecasts under each set of priors:

| Configuration | Module | Prompted | Named | Unprompted | Full neglect | 50% |
| --- | --- | --- | --- | --- | --- | --- |
| Astra | relay | 0.035 | 0.038 | 0.190 | 0.190 | 0.095 |
| Sol | relay | 0.116 | 0.049 | 0.103 | 0.108 | 0.167 |
| Astra | disclosure | 0.014 | 0.064 | 0.149 | 0.188 | 0.053 |
| Sol | disclosure | 0.048 | 0.025 | 0.105 | 0.141 | 0.086 |

**Sessions.**
- **Astra relay:** the irrelevant level was 0.50, 0.15 and 0.50, and stated rates matched the forecasts within 0.01 in every session.
- **Sol relay:** every session stated 0.25–0.60 for the three ambiguous outlets (mean 0.37–0.40 per level), yet its forecasts implied 0.00–0.42 (mean 0.09–0.17 per level). In one session it stated 0.40, 0.50 and 0.60 while its forecasts implied 0.05, 0.00 and 0.00.
- **The one incoherent Astra session (disclosure):** it stated 0.60 for the mildly suggestive company while its forecasts implied 0.46.
- **Noise:** report noise was at the 0.05 floor for Astra and for Sol's disclosure, and 0.18 for Sol's relays.

**Against the predictions:**
- **A1. The default is induced:** supported for Astra, not for Sol (two of four cells).
  - **Astra:** 0.38 and 0.48.
  - **Sol:** 0.09 and 0.29.
- **A2. Full restoration:** supported for Astra, not for Sol (two of four cells).
  - **Astra:** within 0.080 and 0.039 of the prompted mapping.
  - **Sol:** 0.261 and 0.139 away. Sol's forecasts stayed close to its named mapping (0.049 and 0.068).
- **A3. Coherence:** supported for Astra (5 of 6 sessions), not for Sol (3 of 6, with no coherent relay session).
- **A4. Best predictor (exploratory):**
  - **Astra:** the prompted mapping best predicts its forecasts (3.5 and 1.4 points).
  - **Sol:** the named mapping does (4.9 and 2.5 points). For Sol, asking for the rate changed what it said more than what it did.

**Completion answers.** These are descriptive only. In every relay session the agent said the relay rate was unstated and had to be judged from the descriptions. In every disclosure session it said the weight of company profiles or the rate of selective reporting was unclear. None mentioned treating stated and applied rates differently.

## Interpretation

1. **For Astra, being asked for the rate is what produces the 50% default.** With the mechanism named and a base rate asked for, Astra's forecasts returned to its prompted-dossier behaviour, including 50% for descriptions that carry no information. Astra now shows a full three-step pattern:
   - **Unprompted:** neglect.
   - **Named:** discount where a description suggests it.
   - **Named and asked:** a 50/50 default everywhere else.
2. **For Sol, being asked produced a stated rate its relay forecasts did not use.** Sol said that 25–60% of ambiguous outlets relay (about 40% on average), then forecast as if 9–17% did. This is the first stated–applied gap in a frontier configuration: Sol was coherent in 22 of 24 description and dossier sessions before, all of which also had structure probes or the full mechanism statement. The gap resembles Luna's in the formal modules, but here it appears only in one framing.

   For a reader, Sol's base rates when asked, and its forecasts, can diverge when the mechanism is only named. The forecasts are the behaviour to rely on.
3. **The two configurations first differ here.** In the relay description modules and prompted dossiers, Astra and Sol mapped descriptions almost identically. They separate only in this less scaffolded condition, which makes it a candidate passport distinction. It rests on three sessions per cell and needs a retest.
4. **Limits.** Three sessions per cell. Cases come in random order, so some forecasts precede their description's rate question. This design does not separate "asked before forecasting" from "asked at all".

## Next

- **Retest Sol's relay gap:** three fresh asked sessions, plus a variant that also adds the structure probes (the remaining difference from the prompted dossiers). This tests whether probes are what keep Sol's forecasts coherent with its stated rates.
- **Reading guide:** report coherence by condition, so a gap confined to one framing is not averaged away.

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `492001890b60a1c0eb3b4f6debe0332cfc28dc3ccf5149d956473af207531bb3` |
| execution.json | `3cec2e1505c76cb9c0452a1623317043ba84f60ce85eeb1b74a17746bdaa8283` |
| summary.json | `a4f8221e03a84492a7809b51b802d1fd755ff50d4a60dbcf293808f68fc4d21e` |
