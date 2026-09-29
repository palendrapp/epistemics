# Structure checks: testing only the hidden structures a consumer names

Specified 29 September 2026, before the validation and the checks ran (`epistemics.structure_check`, structure-check/0.1.0).

## Why

The [hierarchical second layer](structure-inclusion-model.md) found that noticing one hidden structure does not predict noticing another. For Sol, the prediction for an untested structure runs from "considered unprompted" to "considered only once asked for its base rate". Showing that noticing does carry over would take 10–15 structures per configuration, about 115 million tokens for two configurations.

The cheaper alternative, chosen on 29 September, is to test only the structures a consumer names:
- **Collection:** each named structure is collected on the salience ladder.
- **Fit:** each is fitted on its own.
- **Output:** each becomes a prompting recommendation, "what to put in your prompt so that it considers this".

## The catalogue

A structure is a hidden structure in one task format. Each rung of the ladder is realised by one module and variant.

| Key | Structure, as a consumer names it | Setting | Rung 0 (plain) | Rung 1 (named) | Rung 2 (named, asked for its rate) | Rung 3 (named, asked, asked per case) |
| --- | --- | --- | --- | --- | --- | --- |
| relay | Sources repeating another source | Document dossiers | corroboration-unprompted, dossier-a | corroboration-unprompted, named-a | corroboration-asked | corroboration-probed |
| disclosure | Selective silence | Document dossiers | disclosure-unprompted, dossier-a | disclosure-unprompted, named-a | disclosure-asked | disclosure-dossier (full mechanism; no probed version exists) |
| copying | Copied readings | Abstract urn tasks | copying-urn, urn2-plain | copying-urn, urn2-named | copying-urn-asked | copying-urn-probed |
| selection | Selective reporting | Abstract urn tasks | selection-urn, urn2-plain | selection-urn, urn2-named | selection-urn-asked | selection-urn-probed |
| mismatch | Misfiled readings | Abstract urn tasks | mismatch-urn, urn2-plain | mismatch-urn, urn3-named | mismatch-urn-asked, urn3-named | mismatch-urn-probed, urn3-named |

A structure outside the catalogue needs a new task: its texts, a validation, and an entry here.

## The check

**Fit.** The per-structure second layer (`inclusion_joint`: one family, fidelity mixture, 4 chains of 40,000 iterations) is fitted to that structure's sessions. A check is valid only if every R-hat is 1.05 or less; otherwise it makes no recommendation.

**Recommendation.**
- **Inclusion read:** for a case in which nothing hints at the structure (the uninformative description), at each rung.
- **Reliable rung:** one where the 90% interval of inclusion starts at 0.8 or above.
- **Recommendation:** the lowest reliable rung, translated into an action. If no rung is reliable, the reading says it does not reliably consider the structure even with every prompt tested.

| Rung | Action |
| --- | --- |
| 0 | Nothing needed |
| 1 | Mention it: say that it can happen |
| 2 | Mention it and ask how common it is |
| 3 | Mention it, ask how common it is, and ask about it for each case |
| none | Not reliable even with every prompt tested |

## Validation: which protocol is cheap enough to trust

Four collection protocols (sessions per rung 0–3):

| Protocol | Sessions | About |
| --- | --- | --- |
| full | 3, 3, 3, 2 = 11 | 5.8M tokens |
| reduced | 2, 2, 2, 1 = 7 | 3.7M tokens |
| lean | 2, 2, 1, 1 = 6 | 3.2M tokens |
| minimal | 1, 1, 1, 1 = 4 | 2.1M tokens |

Each is tested on 40 synthetic configurations.
- **Structure:** one per configuration, drawn from the catalogue.
- **Parameters:** θ uniform on −0.8 to 3.2, w on 0 to 1, σ on 0.2 to 1.2, φ on 0 to 1.
- **Pipeline:** the real item designs and description fits.

The rung truly needed is computed from the true θ and σ for an uninformative description.

**Gates.** Recommending too little prompting is the costly error. Recommending one rung too much costs the consumer one more sentence of prompt.
- **Unsafe** (less prompting recommended than needed): at most 10%.
- **Within one rung** (exact, or one rung more than needed): at least 80%.
- **Converged:** at least 90%.

The checks use the cheapest protocol that passes all three gates. If none passes, no protocol is adopted and the checks on existing data are reported as provisional.

**On existing data.** Astra and Sol already have ladder sessions for all five structures. The dossiers have more sessions than any protocol, and the urn structures follow the full protocol. So the first checks need no new collection.

## Commands

```bash
uv run python -m epistemics.structure_check validate --output output/structure-check-validation-20260929.json
```

```bash
uv run python -m epistemics.structure_check check --validation output/structure-check-validation-20260929.json --output output/structure-checks-20260929.json
```

For a named structure on a configuration, collection uses the existing validated battery (tasks 0.11.0, unchanged) through the runner:

```bash
uv run python -m epistemics.structure_check collect output/<directory> --configuration sol --structure copying --protocol <chosen> --validation <task validation 1> --validation <task validation 2>
```

## Results (29 September)

### Validation: the minimal protocol is adopted

All four protocols passed every gate (40 synthetic configurations each; largest R-hat 1.026).

| Protocol | Sessions | Exact | One rung more | Two rungs more | Unsafe | Converged | Unprompted inclusion, MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full | 11 | 62% | 32% | 2% | 2% (1 of 40) | 100% | 0.05 |
| reduced | 7 | 50% | 45% | 5% | 0% | 100% | 0.06 |
| lean | 6 | 45% | 48% | 8% | 0% | 100% | 0.09 |
| minimal | 4 | 40% | 45% | 15% | 0% | 100% | 0.08 |

**Adopted: minimal.** This is the rule set in advance: the cheapest protocol that passes. It uses one session per rung, 4 sessions, about 2.1 million tokens per structure and configuration.
- **What fewer sessions cost:** more cautious advice, not unsafe advice. The minimal protocol recommends two rungs more prompting than needed in 15% of cases, against 2% for the full protocol.
- **When to prefer the reduced protocol:** a consumer who wants the lightest prompt that works can pay about 1.6 million tokens more for it (7 sessions).

### Checks on existing sessions

Astra and Sol already had ladder sessions for all five structures, so no collection was needed. The dossier structures have more sessions than any protocol, including formal-case sessions at rung 3. The urn structures follow the full protocol.

**Inclusion at each rung** (unprompted → mentioned → asked how common → asked per case), for a case in which nothing hints at the structure, **and the resulting advice:**

| Structure | Configuration | Sessions | Inclusion (mean) | Advice |
| --- | --- | --- | --- | --- |
| Sources repeating another source (dossiers) | Astra | 23 | 0.06, 0.72, 0.99, 1.00 | Mention it and ask how common it is |
| | Sol | 26 | 0.07, 0.41, 0.90, 0.99 | Mention it, ask how common it is and ask about each case |
| Selective silence (dossiers) | Astra | 14 | 0.39, 0.96, 1.00, 1.00 | not determined (R-hat 1.43; the two-mode disclosure mapping seen in the hierarchical fit) |
| | Sol | 14 | 0.26, 0.91, 0.99, 1.00 | Mention it and ask how common it is |
| Copied readings (urns) | Astra | 11 | 0.94, 0.99, 1.00, 1.00 | Mention it |
| | Sol | 11 | 0.44, 0.95, 1.00, 1.00 | Mention it and ask how common it is |
| Selective reporting (urns) | Astra | 11 | 0.75, 1.00, 1.00, 1.00 | Mention it |
| | Sol | 11 | 0.76, 1.00, 1.00, 1.00 | Mention it |
| Misfiled readings (urns) | Astra | 11 | 0.02, 0.06, 0.32, 0.76 | Not reliable (known wording issue) |
| | Sol | 11 | 0.05, 0.62, 0.97, 1.00 | Mention it and ask how common it is |

All valid checks had R-hat of 1.011 or less.

**What the table says.**
- **Unprompted:** neither configuration reliably considers any of these structures. The highest unprompted inclusion is Astra's 0.94 for copied readings, and its 90% interval starts at 0.74, below the 0.8 bar.
- **Mentioning is enough for** selective reporting (both), and for copied readings (Astra).
- **Asking how common it is:** needed for most other structures.
- **Asking about each case:** needed for Sol with sources repeating another source.
- **Across configurations:** the advice differs by configuration for the same structure, so it cannot be carried from one configuration to another.

**Cautions.**
- **Behaviour on these tasks:** these recommendations describe behaviour on these tasks, with prompts like the ones tested. A consumer's own wording may work better or worse.
- **Misfiled readings:** the tested prompt contained an ambiguous accuracy sentence. Astra read it as covering misfiling, so its "not reliable" may reflect the wording rather than the configuration. The guide shows this as a known issue.

**For the guide** (reading-guide/0.3.0): each valid check becomes a reading under "Which hidden structures it considers". It gives how often the configuration considers the structure unprompted, and the prompt that makes it reliable. The noticing and carry-over readings moved to the same topic.

| File | SHA-256 |
| --- | --- |
| Protocol validation | `cb10e22f7ab194b0198c3350d0ab6c28ba2bde33f7ff07c4f37ac27d7a2a06b8` |
| Structure checks | `c7a928c922d34274fff388ad206cc90d3f6104ac9b175373c7e9e83362b01d5c` |

## Misfiled readings reworded (tasks 0.12.0)

**The problem.** The misfiled-readings check used the corrected urn wording (urn2): "a sensor's stated accuracy applies to readings of the urn it is filed under". That can be read as saying accuracy already covers misfiled readings. Astra read it that way in 6 of its 8 named sessions ([abstract transfer](disposition-abstract2-2026-09-29.md)), which is why its check said "not reliable".

**The new variant** (`urn3-named`, mismatch modules only) replaces that one sentence with:

> In any round, a reading on file may come from a different urn than the one it is filed under; a sensor's stated accuracy applies only when the reading does come from that urn, and a reading from a different urn says nothing about this one.

**What stays the same.**
- **The rest of the text:** everything else is byte-identical to urn2-named, including the questions (checked for all 72 cases).
- **Plain cases:** unchanged, so the existing urn2-plain sessions stay the check's rung 0.
- **Other structures:** copying and selection do not take the new variant.

**Validation.**
- **Battery:** disposition-tasks/0.12.0, implementation fingerprint `704367d40d6dc3fdf6505d79c7eb3a0f42b8a8b2aba74eaeca45988e2c94fe11`.
- **Task validation 0.12:** passed on both seeds, with 1,632 rendered cases and all 70 contexts.

| Artifact | SHA-256 |
| --- | --- |
| Task validation 0.12, seed 20260927 | `b07735902e7bc4a0b55eb8f49f1096669afd40031346aa17968b4afdd0402150` |
| Task validation 0.12, seed 20261027 | `1ae0d3fd3e74a83ee92ce4f470c477f6933faa31523a9a130a6d53a2b9b20a0d` |
| Structure checks rerun (misfiled readings withdrawn) | `15a6f7e7a9977bd57d53e2cda42fa89f26342b64c3e8f96857f73bcee9d1b750` |

**The old results are withdrawn.**
- **Catalogue:** the misfiled-readings entry now points at the new wording.
- **Checks:** a check records the format it was fitted to, and the guide reads only checks that match the catalogue.
- **Rerun:** the checks were rerun (`output/structure-checks-20260929-2.json`). The other eight are unchanged, and the guide lists misfiled readings as "not yet checked" for both configurations.

**Collecting the reworded check.** The minimal protocol at rungs 1–3 only, since rung 0 already has three plain sessions per configuration. That is 6 contexts, about 3.2 million tokens:

```bash
uv run python -m epistemics.structure_check collect output/structure-check-mismatch3-<date> --configuration astra --configuration sol --structure mismatch --protocol minimal --rung 1 --rung 2 --rung 3 --validation output/disposition-tasks-v0.12-validation-20260927.json --validation output/disposition-tasks-v0.12-validation-20261027.json
```

### Preregistration: the reworded check (written before collection)

**Design.** The collection is the minimal protocol at rungs 1–3 for Astra and Sol: 6 contexts, cap 3.8 million tokens. The existing plain sessions stand as rung 0. The check's fit and recommendation rule are unchanged.

**Criteria.** The rewording works for a configuration if:
- **R1.** Its mean implied prior for the strongly suggestive sensor ("shared by 50 urns and moves between them") is at least 0.50 at rung 1. Astra gave 0.00 under the old wording; Sol gave 0.97.
- **R2.** Its check converges and recommends a rung. A "not reliable" recommendation counts against the rewording.

**Expectations.**
- **E1.** Both configurations meet R1 and R2.
- **E2.** If Astra's old result came from the wording, its advice is no longer "not reliable".
- **E3.** Sol's advice is unchanged ("mention it and ask how common it is"), within one rung. Sol's sessions were not affected by the old ambiguity in the same way.

With one session per rung, the mapping at a single rung is noisy, so R1 is read on that one session.

### Results: the reworded check (29 September)

**Collection.** All 6 contexts completed with no errors: 3.16 million input tokens (2.93 million cached), 6 minutes in all.

```bash
uv run python -m epistemics.ledger cues-summary output/structure-check-mismatch3-20260929
```

**Implied priors per level** (strongly reassuring → strongly suggestive, the last being "shared by 50 urns and moves between them"). One session per cell; stated rates agreed with these within 0.05 in every asked and probed session.

| | Named (rung 1) | Named and asked (2) | Named, asked and probed (3) |
| --- | --- | --- | --- |
| Astra, reworded | 0.00, 0.10, 0.10, 0.20, 0.40 | 0.00, 0.50, 0.13, 0.90, 0.97 | 0.05, 0.05, 0.06, 0.12, 0.22 |
| Astra, old wording (mean of 3, 3, 2) | 0.00 at every level | 0.00–0.03 | 0.03–0.17 |
| Sol, reworded | 0.00, 0.50, 0.25, 0.90, 0.96 | 0.00, 0.00, 0.05, 0.05, 0.10 | 0.00, 0.50, 0.50, 0.90, 0.95 |

**Checks** (`output/structure-checks-20260929-3.json`; both converged, R-hat 1.011 or less):

| | θ [90%] | Inclusion, rung 0 → 3 (mean) | Lower end at rung 3 | Advice |
| --- | --- | --- | --- | --- |
| Astra | 1.02 [0.38, 1.93] | 0.08, 0.54, 0.90, 0.97 | 0.79 | Not reliable |
| Sol | 1.22 [0.33, 2.45] | 0.09, 0.46, 0.80, 0.93 | 0.66 | Not reliable |

Under the old wording, Astra's per-structure fit gave θ 2.42 and inclusion when asked of 0.32.

**Against the preregistration:**
- **R1:**
  - **Sol** meets it (0.96 at rung 1).
  - **Astra** does not (0.40, up from 0.00).
- **R2:** both converged, but neither recommends a rung.
- **E1:** not supported.
- **E2:** not supported as stated. Astra's advice is still "not reliable", although the rewording moved it a long way.
- **E3:** not supported. Sol's advice moved from "mention it and ask how common it is" to "not reliable".

**What happened.**
1. **The rewording removed the misreading.** No completion answer (descriptive only) called the accuracy sentence ambiguous. Astra's instead said "the unstated rate of readings filed under the wrong urn" was the main ambiguity, as Sol's had before. Astra applied misfiling fully in its asked session (0.97), which it never did under the old wording.
2. **Both configurations now switch by session between applying misfiling and judging it rare.** In the low sessions they stated a low rate for the 50-urn sensor (Astra 0.20, Sol 0.10) and forecast with it. They considered the structure and judged it uncommon for the sensors described. The case never states how often misfiling happens. Sol did the same in 2 of 5 asked and probed sessions under the old wording.
3. **With one session per rung, one low session keeps the interval below the bar.** This is the minimal protocol's known cost: in validation it recommended more prompting than needed in 60% of cases, and two rungs more in 15%. Here the result is honest but coarse. It does not show whether inclusion when asked is about 0.7 or about 0.95.

**For the guide.** "Not reliable" is accurate for what a consumer controls: none of the prompts tested makes either configuration reliably take misfiled readings into account. The reading now says "does not reliably take it into account", not "does not consider it", because when asked it did consider misfiling and judged it rare.

**Options.**
- **Top up to the full protocol at rungs 1–3:** 5 more contexts per configuration, about 5.3 million tokens. This would say whether asking is enough most of the time.
- **Add a rung that states the rate** ("about one reading in five on file comes from a different urn"). If the variation is a judged rate, stating the rate is the consumer action that would fix it. It needs a new variant and validation.

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `ae546bedf7986f83e09559ac53d4ee32eb8e21f2d7f59fb1013d967910ffb553` |
| execution.json | `0da4bf982b7da07bf93cbe7f378868d4bfcf6ee6494e09d123c35b7be66a83c9` |
| summary.json | `b373d051bdfd995f8eb584fa2e3153482279296f3f31347b3ba9733f68857282` |
| Structure checks with the reworded mismatch | `86609ff759267d0058b1667fcd2eb775752e95bd0ac3a0039a2dfc9d3af31fe2` |
