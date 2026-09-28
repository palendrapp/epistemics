# Dossier transfer of description priors — 28 September 2026

Preregistration, written and committed before collection. Results will follow below. This is the first transfer test in the [generative model](epistemic-generative-model.md#6-transfer-layer-naturalistic) plan. It asks whether the description-to-prior mappings measured in the formal modules predict answers when the same cases arrive as realistic documents.

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
