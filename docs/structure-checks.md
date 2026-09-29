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
