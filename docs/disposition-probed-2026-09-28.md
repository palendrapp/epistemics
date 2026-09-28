# Sol's stated–applied gap: retest and structure probes — 28 September 2026

Preregistration, written and committed before collection; the results follow below.

**Result.** The gap did not replicate at the preregistered size. In three fresh asked sessions, Sol's stated rates at the ambiguous levels exceeded its applied priors by 0.04 on average, against at least 0.15 predicted.

Across all six asked relay sessions, Sol's forecasts departed widely from its stated rates in two: by 0.48 and 0.27 on average at the ambiguous levels. In the other four the difference was 0.07 or less. The gap is intermittent, not a stable trait at this sample size.

With structure probes, both Astra and Sol were coherent and close to their prompted mappings. The fresh asked sessions were nearly aligned without probes, so this study cannot attribute the alignment to the probes.

In the [default-induction test](disposition-asked-2026-09-28.md), the relay dossiers named the mechanism and asked for each description's base rate. Sol stated about 40% for ambiguous outlets (25–60% across sessions), then forecast as if 9–17% relayed. None of its three sessions was coherent; before that, it had been coherent in 22 of 24 description and dossier sessions. Every one of those earlier sessions also asked structure probes: "What is the probability that B relayed A's call?".

This study asks two questions:
- **Replication:** does the gap replicate in fresh sessions?
- **Probes:** do structure probes make Sol's forecasts use the rates it states?

## Design

**Retest.** Three fresh Sol sessions on the asked relay dossiers (`corroboration-asked`, variant `named-a`), unchanged from the default-induction test.

**Probed dossiers** (`corroboration-probed`, disposition-tasks/0.9.0, design 0.7.0). Each relay description level has:
- the base-rate question;
- one structure probe in the named-dossier format, with the second outlet's track record at 90%;
- two forecasts: the two unprompted forecasts with a 95% second outlet, one with the reports high and one low.

The four anchors are unchanged, and every brief carries the named sentence. The probed design differs from the asked design only in replacing one forecast per level with the probe. Astra gets three probed sessions as a reference; Sol gets three.

**Validation.**
- **Offline recovery** (design 0.7.0): passed every gate on both seeds, with probed relay correlation 0.99, MAE 0.03–0.04 and 90% coverage 0.93. All earlier results are identical to 0.6. On three pilot seeds, the probed design recovered implied priors with correlation 0.99 and MAE 0.03. Probes identify the prior far better than forecasts do.
- **Task validation** (0.9): passed on both seeds. Earlier contexts reproduce 0.8 exactly, and the probed context recovered within tolerance.
- **Rendering audit:** each probed case names the mechanism once in its text. Only base-rate and probe questions mention it again.

**Collection** (preset `probed`):

| Group | Configurations | Module | Sessions |
| --- | --- | --- | --- |
| Retest | GPT-6 Sol, medium effort | asked relay dossiers | 3 fresh |
| Probes | GPT-6 Astra and Sol, medium effort | probed relay dossiers | 3 each |

That is 9 contexts at about 0.55 million input tokens each, with a cap of 7 million.

**Analysis.** `uv run python -m epistemics.ledger noticing <roots>`:
- **Asked block:** it pools every asked session given. The retest is read from the new root, with the transfer root supplying the prompted reference.
- **Probed block:** it reports the mapping, the stated rates, coherence, distances and predictive errors, and adds the asked mapping as a candidate prior. Per session it adds two diagnostics:
  - **Probe-implied prior** per level: the relay prior at which an exact observer gives the probe answer.
  - **Forecast-only prior** per level: the description fit refitted without the probes.

The joint fit uses probes and forecasts together, and probes dominate it. Whether Sol's forecasts use its stated rates is therefore judged on the forecast-only priors.

## Predictions

The three ambiguous levels are mildly reassuring, irrelevant and mildly suggestive.
- **R1. The gap replicates.** In the three fresh asked sessions, Sol's mean stated rate at the three ambiguous levels exceeds its mean implied prior there by at least 0.15. At most one of the three sessions is coherent (every stated rate within 0.10 of the implied prior).
- **R2. Probes align Sol's forecasts.** In at least two of Sol's three probed sessions, the forecast-only priors at the three ambiguous levels lie within 0.15 of its stated rates on average.
- **R3. Probes restore Sol's mapping.** Sol's probed mapping (joint fit) lies within 0.10 of its prompted-dossier mapping on average across levels.
- **R4. Astra is unchanged.** Astra's probed mapping lies within 0.10 of its asked mapping on average. Astra is coherent in at least two of three probed sessions.
- **R5. Exploratory.** For each session and level, how the stated rate, probe-implied prior and forecast-only prior relate. In particular, whether Sol's probe answers follow its stated rates when its forecasts do not.

## Commitments (preregistration)

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint (0.9.0) | `0dc4d5d92b57cd4dac9589da93dd01005a0a507d5cdb0d69714253e1c2880a0b` |
| Model and design fingerprint (dispositions, design 0.7.0) | `76950d970f3771b691d6cee18ef0fdef1ea142b613b2a3d0122f44ca83d0e776` |
| Recovery validation 0.7, seed 20260927 | `9f10c2a0048fc4c2edea661ab78855f14f49ac46b79f4d6f45a14c265453ed0a` |
| Recovery validation 0.7, seed 20261027 | `698ca84277d3e7eaa69a3b59867953b4ea92c58b888b4f3452a1abe4a28e5cbb` |
| Task validation 0.9, seed 20260927 | `69782a9defa3973b707e50d0f4369679c140d9715e102d226b450e6cb909132f` |
| Task validation 0.9, seed 20261027 | `6734843dad560001f9c8bca6523c58a00c16a6528f5273991483883b9edc59f7` |

## Results

**Collection.**
- **Completion:** all 9 contexts completed with the minimum 27 calls and no tool errors, in 92–370 seconds each.
- **Tokens:** 5,013,304 input tokens in total (4,748,672 cached).

The tables regenerate with:

```bash
uv run python -m epistemics.ledger noticing output/disposition-transfer-20260928 output/disposition-unprompted-20260928 output/disposition-salience-20260928 output/disposition-probed-20260928
```

That command gives the retest alone. Adding `output/disposition-asked-20260928` pools all six asked sessions and all probed sessions. Levels run from strongly reassuring to strongly suggestive.

**Retest (Sol, asked relay dossiers).**

| Sessions | Implied | Stated | Ambiguous levels: stated minus implied | Coherent |
| --- | --- | --- | --- | --- |
| Fresh (3) | 0.02, 0.35, 0.29, 0.19, 0.89 | 0.01, 0.38, 0.32, 0.25, 0.96 | +0.04 | 1 of 3 |
| First run (3) | 0.01, 0.17, 0.09, 0.14, 0.78 | 0.01, 0.38, 0.37, 0.40, 0.93 | +0.25 | 0 of 3 |
| All six | 0.01, 0.26, 0.19, 0.16, 0.84 | 0.01, 0.38, 0.34, 0.33, 0.95 | +0.15 | 1 of 6 |

The average stated-minus-implied gap at the ambiguous levels, by session:
- **First run:** +0.48, +0.00 and +0.27.
- **Fresh sessions:** +0.05, +0.07 and +0.01.

The two fresh sessions counted incoherent each had one level just over the 0.10 criterion (0.12).

**Probed relay dossiers.**

| Configuration | Implied | Stated | Irrelevant level | Distance to prompted | Distance to own asked mapping | Coherent |
| --- | --- | --- | --- | --- | --- | --- |
| Astra | 0.05, 0.39, 0.44, 0.49, 0.95 | 0.03, 0.38, 0.42, 0.47, 0.95 | 0.44 | 0.040 | 0.045 | 3 of 3 |
| Sol | 0.04, 0.43, 0.28, 0.40, 0.95 | 0.00, 0.40, 0.23, 0.38, 0.95 | 0.28 | 0.080 | 0.127 | 2 of 3 |

**Diagnostics for the probed sessions (R5).**
- **Probe answers:** the prior implied by each probe answer matched the stated rate within 0.01 at almost every level, in every session of both configurations. There were two exceptions, both Sol's: one session's irrelevant outlet (0.45 from the probe against 0.30 stated), and another session's strongly reassuring outlet (0.20 against 0.01).
- **Forecast-only priors:** at the ambiguous levels these differed from the stated rates by 0.00–0.03 on average for Sol, and 0.00–0.04 for Astra.

In these sessions, the stated rate, the probe answer and the forecasts all agreed.

Mean absolute error of the probed answers under each set of priors:

| Configuration | Prompted | Asked (all sessions) | Named | 50% | Neglect |
| --- | --- | --- | --- | --- | --- |
| Astra | 0.039 | 0.046 | 0.067 | 0.123 | 0.282 |
| Sol | 0.073 | 0.065 | 0.072 | 0.157 | 0.256 |

**Against the predictions:**
- **R1. The gap replicates:** not supported. At most one fresh session was coherent, as predicted, but the ambiguous-level gap was +0.04, not at least +0.15.
- **R2. Probes align Sol's forecasts:** supported, in all three sessions. Forecast-only priors were within 0.15 of the stated rates, in fact within 0.03. Because R1 failed, this does not show that probes cause the alignment: the fresh asked sessions were nearly aligned without them.
- **R3. Probes restore Sol's mapping:** supported. Sol's probed mapping lies within 0.080 of its prompted mapping.
- **R4. Astra unchanged:** supported. Astra's probed mapping lies within 0.045 of its asked mapping, and all three sessions were coherent.
- **R5 (exploratory):** in probed sessions, stated rates, probe answers and forecasts agreed, apart from two probe answers in Sol's sessions.

**Completion answers.** These are descriptive only. All nine sessions named the unstated relay rate as the main ambiguity. Two probed sessions said they kept similar assumptions consistent across cases.

## Interpretation

1. **Sol's stated–applied gap is intermittent.** Sol has now completed six sessions of the asked relay dossiers. Two show a wide gap, and four show little or none. That is enough to say Sol can decouple what it states from what it applies in this framing. It is not enough to call this a stable property of Sol.

   The [default-induction](disposition-asked-2026-09-28.md) record is updated to say so. The reading guide now counts sessions with a wide gap, not sessions failing a strict criterion at any single level.
2. **Session-to-session variation is the larger finding for Sol.** Its applied priors for ambiguous outlets were 0.09–0.17 in the first run and 0.19–0.35 in the retest. That is consistent with the bimodal defaults of the salience study, where each session either did or did not adopt a default for unquantified relays. A per-session discrete state fits this better than a fixed prior. It is the central idea of the [second-layer model](structure-inclusion-model.md).
3. **Probes did no harm and may help.** With probes, both configurations were coherent and near their prompted mappings. Whether probes prevent the intermittent gap needs more sessions than two-in-six events allow.

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `2d86ea8101b537b9d63e2c76d73aa69133ee807772f8625c19ab9e6aef7918ad` |
| execution.json | `90e5f635ad5ebf315d83fb7592f5e84eb010b708c381ec25e84578a2e4f10aed` |
| summary.json | `e65784ca34fea6f3eededca80b818d4d50160c3782d0963d91ca284555671173` |
