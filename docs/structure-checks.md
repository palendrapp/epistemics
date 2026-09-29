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
| mismatch | Misfiled readings | Abstract urn tasks | mismatch-urn, urn2-plain | mismatch-urn, urn2-named | mismatch-urn-asked | mismatch-urn-probed |

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
