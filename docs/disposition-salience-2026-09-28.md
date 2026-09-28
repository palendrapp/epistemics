# Salience: one sentence naming the mechanism — 28 September 2026

Preregistration, written and committed before collection.

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
