# Second-layer model: structure inclusion — draft, 28 September 2026

Design note and first estimates. The model was built after seeing the data it is fitted to here, so every estimate below is exploratory. The confirmatory test is proposed under [Next](#next).

## Why a second layer

The first layer, the [generative model](epistemic-generative-model.md), is a rational-analysis observer. Behaviour is Bayes-optimal given assumptions about the environment, and the free parameters are those assumptions: how often outlets relay (δ) and how often silence is selective (σ), per description. That makes them environment-specific content, like the rarity assumption in [Oaksford & Chater 1994](https://doi.org/10.1037/0033-295X.101.4.608).

The last five studies found a pattern that is not a change in any of those values:

| Condition | Rung | What Astra and Sol did |
| --- | --- | --- |
| [Unprompted](disposition-unprompted-2026-09-28.md): the mechanism is never mentioned | 0 | Relay prior 0 for every outlet, even an aggregator with no reporters |
| [Named](disposition-salience-2026-09-28.md): one sentence says it exists | 1 | Obvious copiers discounted. Ambiguous outlets near 0 or at 0.50, by session |
| [Named and asked](disposition-asked-2026-09-28.md) for each description's rate | 2 | Astra at 50/50 for ambiguous outlets. Sol intermittent: 2 of 6 sessions stated about 40% but forecast as if about 10% |
| [Named, asked and probed](disposition-probed-2026-09-28.md), or the full mechanism statement | 3 | The full description mapping, with a 50% default |

What changes across the ladder is whether the hidden-structure hypothesis is in the agent's model at all. The first layer cannot tell "δ = 0" from "never considered relaying". Three signatures point to a discrete inclusion step, not a continuous prior:
- **Bimodal ambiguous levels:** at rung 1, sessions sat near 0 or at 0.50, not in between.
- **Co-movement within a session:** a session's ambiguous levels moved together.
- **Intermittent gap:** Sol's stated–applied gap appeared in some sessions and not others.

## Model

For configuration k, session s in condition c (rung S_c ∈ {0, 1, 2, 3}) and description level l:

- **Inclusion.** The hypothesis is in the model for this level with probability Φ((S_c + w·c_l + ε_s − θ) / ς).
  - ε_s ~ N(0, σ²) is a state shared by the session's levels.
  - c_l = logit μ_l − logit μ_irrelevant is how strongly the description itself suggests the structure.
  - ς = 0.3 is fixed level noise.
- **Prior given inclusion.** δ_sl is logit-normal around μ_l with spread ω. Without inclusion, δ_sl = 0.
- **Data.** Each session enters through its own grid likelihood for each level's prior: the first layer's description fit under uniform priors. The model never sees raw answers twice.

**Parameters, with the reading each would carry in a passport:**

| Parameter | Reading |
| --- | --- |
| **θ, inclusion threshold** | How much prompting a hidden structure (copying, selective silence) needs before the agent considers it. On the ladder: 0 means considered unprompted; 1, once named; 2, once asked about. |
| **w, cue-driven inclusion** | How far a suggestive description, by itself, brings the structure in. |
| **σ, session drift** | How much the agent's readiness to consider it varies from session to session. |
| **d, default** (μ at the irrelevant description) | The prior given to a considered but unquantified structure: 50/50 (indifference) or lower. |
| **κ, description sensitivity** (logit μ, strongly suggestive minus strongly reassuring) | How strongly descriptions move the prior once the structure is considered. |

"Stated–applied fidelity" is not a separate parameter here. It is the inclusion probability at rung 2. A stated rate reflects the mapping μ whenever the agent is asked; the forecasts apply it only if the structure is included. Sol's intermittent gap is then inclusion failing at rung 2 in some sessions.

**Related work (inspiration, not replication):**
- **Hypothesis generation:** judgement depends on which hypotheses are generated, not only on how they are weighed ([Thomas et al. 2008](https://doi.org/10.1037/0033-295X.115.1.155)).
- **Latent causes:** inference of hidden causes with a propensity to posit a new one ([Gershman, Blei & Niv 2010](https://doi.org/10.1037/a0017808)).
- **Arguments from ignorance:** silence is evidence only given a model of what would have been reported ([Hahn & Oaksford 2007](https://doi.org/10.1037/0033-295X.114.3.704)).
- **Metacognitive efficiency:** measured separately from performance ([Fleming & Lau 2014](https://doi.org/10.3389/fnhum.2014.00443)).

## Estimation

Implementation: `epistemics.ledger.inclusion`, numpy only.
1. **Mapping.** Per family (relay, disclosure), μ for each level and one spread ω, by grid maximum likelihood from the rung-3 sessions, where inclusion is assumed certain.
2. **Inclusion parameters.** A grid posterior over θ (−1 to 4, step 0.1), w (0 to 1.5, step 0.1) and σ (0.05–2), under uniform priors. ε_s is integrated by 15-point Gauss–Hermite quadrature.
3. **Sharing variants.**
   - **Shared:** one θ and w for both families.
   - **θ by family:** separate thresholds for copying and for selective silence.
   - **w by family:** separate cue weights.

   The variants are compared by grid log evidence.

**Sessions used:** random-order set-A sessions only (formal, prompted dossier, unprompted, named, asked, probed), because set-B descriptions differ.

**Assumptions to revisit:**
- **Ladder spacing:** equal steps are assumed.
- **Rung-3 inclusion:** assumed certain.
- **Level noise:** ς is fixed.
- **Plug-in mapping:** the mapping is treated as known when fitting θ, w and σ.
- **Stated rates:** not yet used.

## Recovery

Synthetic configurations with known parameters were run through the real item designs for each rung and the real per-session description fit:
- **Session counts:** Sol's collected counts.
- **Noise and spread:** report noise 0.05–0.3 and mapping spread 0.4.
- **Generating ranges:** θ 0.3–2.7, w 0–1, σ 0.2–1.2.
- **Datasets:** 40 per seed.

| Variant | Seed | θ: correlation, MAE, 90% coverage | w | σ |
| --- | --- | --- | --- | --- |
| Shared | 20260928 | 0.975, 0.16, 0.88 | 0.94, 0.14, 0.75 | 0.86, 0.18, 0.95 |
| Shared | 20261028 | 0.977, 0.21, 0.90 | 0.86, 0.13, 0.75 | 0.81, 0.22, 0.88 |
| θ by family | 20260928 | relay 0.92, 0.27, 0.88; disclosure 0.91, 0.24, 0.93 | 0.87, 0.16, 0.68 | 0.81, 0.20, 0.90 |

- **θ:** recovers well.
- **σ:** recovers moderately.
- **w:** its intervals are too narrow (coverage 0.68–0.75), most likely because the plug-in mapping's uncertainty is ignored. Treat w as provisional until the mapping is fitted jointly.

## First estimates (exploratory)

Only Astra and Sol have sessions on every rung; Luna and Terra have only rung 3, so their θ is not identified.

| | Astra | Sol |
| --- | --- | --- |
| θ, shared | 0.65 [0.4, 0.9] | 0.96 [0.6, 1.3] |
| w | 0.37 [0.3, 0.5] | 0.26 [0.2, 0.4] |
| σ | 0.46 [0.25, 0.75] | 0.76 [0.5, 1.0] |
| Inclusion for an uninformative description, rungs 0 → 3 | 0.12, 0.74, 0.99, 1.00 | 0.12, 0.52, 0.90, 0.99 |
| Default d, relay and disclosure | 0.48, 0.50 | 0.40, 0.50 |
| Description sensitivity κ, relay and disclosure | 5.5, 2.2 | 6.2, 2.5 |
| θ by family: relay, disclosure | 0.91, 0.40 | 1.32, 0.46 |

**In plain words:**
- Neither configuration considers an unnamed structure for an uninformative description (inclusion 0.12 at rung 0).
- Sol needs slightly more prompting than Astra (θ 0.96 against 0.65; the intervals overlap).
- Sol varies more between sessions (σ 0.76 against 0.46).
- Sol includes the structure at rung 2 about 90% of the time, against 99% for Astra. That is its intermittent stated–applied gap.

**Model comparison.** Log evidence differs by at most 1.1 nats between the three variants. The data do not reject one shared threshold for copying and for selective silence, but they don't favour it either.

**Fit check.** The share of description levels whose data favour inclusion, observed against predicted by the shared model:

| Family, rung | Astra observed | Astra predicted | Sol observed | Sol predicted |
| --- | --- | --- | --- | --- |
| Relay, 0 | 0.00 | 0.27 | 0.08 | 0.21 |
| Relay, 1 | 0.92 | 0.80 | 0.67 | 0.62 |
| Relay, 2 | 1.00 | 0.99 | 0.75 | 0.93 |
| Disclosure, 0 | 0.44 | 0.22 | 0.11 | 0.16 |
| Disclosure, 1 | 1.00 | 0.83 | 0.89 | 0.59 |

The shared model over-predicts unprompted inclusion for relays and under-predicts it for disclosure. That is the pattern a family-specific threshold captures: copying needs more prompting than selective silence. The comparison above is not decisive, so this is the first question for new data.

## What it would add to the passport

The candidate readings are more general than the current task-level ones:
- "It does not consider hidden structure (copying, selective silence) unless the situation names it."
- "Once a structure is named, it considers it in about three of four sessions (Astra) or one in two (Sol)."
- "Asked about the structure, it states a rate, but in some sessions its forecasts do not use it."

These become passport readings only if they transfer.

## Next

1. **Joint fit.** Fit the mapping jointly and add stated rates as their own channel, so that w's uncertainty is right. That also tests the assumption that stated rates reflect μ whatever is included.
2. **Abstract transfer task (confirmatory).** Build contentless urn versions of copying (some draws are copies of earlier draws) and selection (a sampler shows only some draws). Add a third hidden structure, such as a common cause or survivorship. Each runs on the same four rungs, cued by structure alone. Preregister that the dossier θ predicts inclusion rates in the abstract tasks.
   - **The shared-trait claim** predicts that the configurations' ordering and rung profiles carry over.
   - **The family-specific alternative** predicts that the relay-like structure needs more prompting in every format.
3. **Luna and Terra.** Collect rungs 0–2, so their θ is identified.

## Commands

```bash
uv run python -m epistemics.ledger inclusion
```

```bash
uv run python -m epistemics.ledger inclusion-validate --output output/inclusion-recovery-20260928.json
```

Recovery file SHA-256: `18df6002a962ac6e664fa9beba29e10abbcfb585f2765515568399e65a77016e`.
