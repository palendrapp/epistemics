# Sol's stated–applied gap: retest and structure probes — 28 September 2026

Preregistration, written and committed before collection.

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
