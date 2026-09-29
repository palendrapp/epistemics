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

## Joint fit

The two-stage fit above plugs in the mapping. The joint fit (`epistemics.ledger.inclusion_joint`) samples everything together:
- the mapping (five levels and a spread per family);
- θ, w and σ;
- a stated-rate channel.

It uses adaptive random-walk Metropolis: four chains of 20,000 iterations, the first 8,000 discarded, every fifth kept. Priors are uniform on the same bounded scales as the grids, with φ uniform on [0, 1]. Every real-data fit converged (R-hat at most 1.02).

**Stated rates as their own channel.** A stated base rate, when asked, can be explained in two ways:
- **Applied:** it is the prior that session's forecasts apply.
- **Considered:** it is the configuration's usual mapping, whatever the session applies.

The mixture adds **φ, stated–applied fidelity**: the probability that a session's stated rates are its applied priors. This is the fidelity parameter proposed above, now estimated directly. Each session also gets a posterior probability of being coherent.

**A specification choice made after seeing the data.** The stated channel uses the three ambiguous levels only. With all five levels, the extreme levels dominated it. There, applied priors sit near 0 and 1, and the log-odds scale magnifies differences of a point or two between a whole-percentage stated rate and the fitted prior.

That version gave Sol φ = 0.57 and marked as incoherent many formal and dossier sessions that pass the plain coherence check (every level within 10 points). With the ambiguous levels only, the sessions it marks are exactly the ones the descriptive analysis found. Both results are recorded below.

**Recovery** (final specification: synthetic configurations through the real designs and fits, 4 chains of 10,000 iterations):

| | Correlation | MAE | 90% coverage |
| --- | --- | --- | --- |
| θ (30 datasets) | 0.98 | 0.11 | 0.90 |
| w | 0.96 | 0.07 | 0.90 |
| σ | 0.88 | 0.12 | 0.83 |
| Mapping (all levels) | — | 0.014 | 0.90 |
| φ (20 datasets) | 0.94 | 0.07 | 0.90 |

- **The joint fit fixes w's coverage** (0.90, against 0.68–0.75 with the plug-in mapping).
- **Model recovery:** the paired WAIC picked the generating stated-rate hypothesis in 24 of 24 synthetic configurations (12 each way).
- **Convergence:** six of 30 recovery datasets had R-hat between 1.05 and 1.18. Restricted to the 24 converged ones, θ has correlation 0.99, MAE 0.09 and coverage 0.92.
- **All-levels specification:** φ recovered with correlation 0.97 and MAE 0.06.

**Estimates** (shared threshold; mixture for stated rates):

| | Astra | Sol |
| --- | --- | --- |
| θ, inclusion threshold | 0.47 [0.17, 0.73] | 0.74 [0.28, 1.08] |
| w, cue-driven inclusion | 0.22 [0.08, 0.38] | 0.26 [0.12, 0.41] |
| σ, session drift | 0.39 [0.09, 0.81] | 0.74 [0.46, 1.09] |
| φ, stated–applied fidelity | 0.97 [0.91, 1.00] | 0.87 [0.75, 0.96] |
| Inclusion for an uninformative description, rungs 0 → 3 | 0.17, 0.85, 0.99, 1.00 | 0.18, 0.62, 0.94, 0.99 |
| Default d, relay and disclosure | 0.43, 0.41 | 0.40, 0.32 |
| Description sensitivity κ, relay and disclosure | 5.8, 2.1 | 6.2, 2.7 |
| φ with the stated channel at all five levels | 0.91 [0.81, 0.98] | 0.57 [0.41, 0.73] |

**Model comparisons** (paired WAIC differences on the deviance scale; negative favours the first model):

| Comparison | Astra | Sol |
| --- | --- | --- |
| Applied minus considered | −457 ± 66 | +117 ± 113 |
| Mixture minus applied | −3 ± 5 | −197 ± 77 |
| Mixture minus considered | −460 ± 65 | −80 ± 55 |
| Threshold by family minus shared (mixture's stated model: applied for Astra, considered for Sol) | −6 ± 5 | +2 ± 5 |

**Sessions the fidelity mixture marks as incoherent** (posterior probability below 0.5):
- **Astra:** none of 25.
- **Sol:** three of 28, all from the default-induction study.
  - Two relay sessions, both at probability 0.00. These are the two with wide stated–applied gaps.
  - One disclosure session, at 0.43.

**What the joint fit adds.**
- **Astra's stated rates are its working priors.** Stated-rate noise is τ = 0.02 on the log-odds scale, φ is near 1, and the pure "applied" model is as good as the mixture.
- **Sol's stated rates are usually its working priors, not always.** The mixture beats both pure hypotheses (by 197 ± 77 and 80 ± 55), and it locates the exceptions in the sessions already known to have wide gaps.
- **Sol also varies more between sessions** in whether it considers a named structure (σ 0.74 against 0.39), and needs slightly more prompting (θ 0.74 against 0.47; the intervals overlap).
- **Copying against selective silence:** a separate threshold for each still gets at most weak support (Astra −6 ± 5; Sol +2 ± 5).

## Hierarchical thresholds (specified 29 September, before fitting)

**Why.** In the corrected abstract run, fits one structure at a time converged but gave thresholds that differ by structure. The question becomes how much a configuration's threshold varies between structures, and what that predicts for a structure it has not been tested on.

**Model** (`epistemics.ledger.inclusion_hier`, `inclusion-hier`).
- **Structures:**
  - relay dossiers, including the formal cue modules;
  - disclosure dossiers;
  - the corrected urn tasks' copying, selection and mismatch.

  The first urn run is excluded: two of its three named wordings were flawed, and all three differ from the corrected ones.
- **Per structure:** each keeps the model of the per-structure analysis: mapping μ and spread ω, cue weight w, session drift σ, stated-rate noise τ, and fidelity φ under the mixture stated channel.
- **Pooling:** only the thresholds are tied. θ_k ~ N(θ̄, τ_θ²), truncated to [−1, 4]. θ̄ is uniform on [−1, 4]. τ_θ is half-normal with a scale of one rung, on [0.02, 3]. With five structures a flat prior leaves a long upper tail (seen in trial fits on synthetic data); the half-normal says spreads beyond two rungs are unlikely (Gelman, 2006).
- **Reported quantities:**
  - θ̄, the typical threshold;
  - τ_θ, the spread between structures, in rungs;
  - θ for an untested structure (posterior predictive), which is the product-relevant quantity.
- **Sampling:** given (θ̄, τ_θ) the structures are independent. Each structure's block gets its own adaptive Metropolis step. Shift and scale moves act on all thresholds at once, so chains can cross the funnel near τ_θ = 0. The fit uses 4 chains of 30,000 iterations, with 12,000 burn-in.

**Decision rule for τ_θ.** The limit is 0.5 rung, the tolerance used in P1 of the abstract transfer.
- **Generalises:** the 90% interval lies below 0.5.
- **Structure-specific:** the 90% interval lies above 0.5.
- **Undetermined:** otherwise.

**Validity.** Estimates are reported only if every parameter has R-hat of 1.05 or less.

**Recovery gates.** These use 30 synthetic configurations at the collected session counts. Each gate must pass before the corresponding real estimate is reported.
- **R1, θ_k:** correlation of at least 0.9, and 90% coverage of at least 0.8.
- **R2, θ̄:** 90% coverage of at least 0.8.
- **R3, τ_θ:** 90% coverage of at least 0.8.
- **R4, wrong-direction readings:** at most 3 of 30. A wrong-direction reading is "generalises" when the true τ_θ is above 0.75, or "structure-specific" when it is below 0.25.
- **R5, convergence:** at least 27 of 30 datasets converged.

**Expectations.** This is a specified re-analysis, not a blind test. The per-structure urn thresholds are already known (Astra −0.25, −0.77, 2.42; Sol −0.26, 0.07, 0.86).
- **E1.** Astra's spread reads structure-specific.
- **E2.** Sol's spread is undetermined.
- **E3.** Sensitivity analysis without mismatch, whose corrected wording was misread: Astra's spread is undetermined.

## Hierarchical thresholds: results (29 September)

These are the fits specified above. They use the relay and disclosure dossier sessions and the corrected urn sessions.

```bash
uv run python -m epistemics.ledger inclusion-hier-validate --output output/inclusion-hier-recovery-20260929.json
```

```bash
uv run python -m epistemics.ledger inclusion-hier --output output/inclusion-hier-fit-20260929.json
```

```bash
uv run python -m epistemics.ledger inclusion-hier --family relay --family disclosure --family copying --family selection --output output/inclusion-hier-sensitivity-20260929.json
```

**Recovery: all five gates pass.** 30 synthetic configurations, all converged (largest R-hat 1.028).

| Gate | Result | Required |
| --- | --- | --- |
| R1, θ_k | correlation 0.97, coverage 0.93, MAE 0.21 | at least 0.9 and 0.8 |
| R2, θ̄ | coverage 1.00 (correlation 0.84, MAE 0.32) | at least 0.8 |
| R3, τ_θ | coverage 0.93 (correlation 0.82, MAE 0.32) | at least 0.8 |
| R4, wrong-direction readings | 0 of 30 | at most 3 |
| R5, converged | 30 of 30 | at least 27 |

**The design's limit.** With five structures, the model never reached a "generalises" reading: 0 of the 5 synthetic configurations whose true spread was below 0.25 got one. All five read undetermined, and τ_θ is overestimated when it is small. A large spread is detected more often: 13 of 18 above 0.75 read structure-specific. So "undetermined" is the most this design can show for a configuration whose noticing does generalise.

**Estimates** (90% intervals):

| | Astra (exploratory, see below) | Sol |
| --- | --- | --- |
| Relay dossiers | 0.73 [0.37, 1.06] | 1.01 [0.49, 1.42] |
| Disclosure dossiers | 0.10 [−0.40, 0.45] | 0.28 [−0.12, 0.64] |
| Copying, urns | −0.75 [−0.98, −0.36] | 0.14 [−0.53, 0.66] |
| Selection, urns | −0.25 [−0.51, 0.00] | −0.22 [−0.48, 0.03] |
| Mismatch, urns | 2.19 [1.52, 2.91] | 0.79 [0.35, 1.23] |
| Typical threshold θ̄ | 0.08 [−0.87, 1.23] | 0.25 [−0.67, 0.96] |
| Spread τ_θ (rungs) | 1.41 [0.79, 2.25] | 0.84 [0.33, 1.65] |
| P(τ_θ > 0.5) | 1.00 | 0.78 |
| Reading | structure-specific | undetermined |
| θ for an untested structure | 0.61 [−0.83, 2.70] | 0.46 [−0.72, 1.94] |
| Largest R-hat | 1.69 (disclosure mapping); thresholds 1.018 | 1.013 |

**Astra's fit misses the validity rule.** The failure is confined to its disclosure mapping. Pairs of chains settled in two modes for the irrelevant description's prior, 0.50 or about 0.41, and did not cross.
- **At twice the chain length (a check, not a replacement):** the modes persisted (R-hat 1.61).
- **The quantities of interest:** every threshold, θ̄ and τ_θ converged in both runs (R-hat 1.018 or less).
- **Status:** Astra's estimates are therefore exploratory, and E1 is not assessable.

**Without mismatch** (sensitivity; both fits converged, R-hat 1.012 or less):

| | τ_θ | Reading | θ̄ | θ for an untested structure |
| --- | --- | --- | --- | --- |
| Astra | 0.92 [0.39, 1.70] | undetermined | −0.23 | [−0.88, 1.70] |
| Sol | 0.87 [0.31, 1.73] | undetermined | 0.12 | [−0.79, 1.93] |

**Against the expectations:**
- **E1** (Astra structure-specific): not assessable under the validity rule. The exploratory reading is structure-specific (P(τ_θ > 0.5) = 1.00), driven by mismatch.
- **E2** (Sol undetermined): holds.
- **E3** (Astra undetermined without mismatch): holds.

**Interpretation.**
1. **Noticing one hidden structure does not predict noticing another.**
   - **Sol:** the spread is at least 0.33 rungs and possibly more than 1.5.
   - **Astra:** exploratory, 0.79–2.25 rungs.
   - **An untested structure:** for both configurations the 90% prediction runs from "considered unprompted" (below 0) to "considered only once asked for its rate" (about 2, Sol) or later (Astra).
   - **Consequence:** a consumer cannot infer from these five structures whether a configuration will raise a new hidden structure on its own. Each structure that matters has to be tested.
2. **The design cannot show that noticing generalises.** That would need more structures per configuration. With five, even a true spread near zero reads undetermined.
3. **Astra's large spread rests on mismatch,** whose corrected wording Astra read as covering misfiling. Without mismatch, the two configurations look alike (τ_θ about 0.9).
4. **Relay dossiers need more prompting than disclosure dossiers** under this model: Astra 0.73 against 0.10; Sol 1.01 against 0.28. This is not a clean test of that difference. Here w and σ also differ by structure, and the earlier dossier-only comparison, with shared w and σ, found only weak support for separate thresholds.

| File | SHA-256 |
| --- | --- |
| Hierarchical recovery | `863440dabb8f6ddb727a95653ffb3b2357f38e98c6554a875b11328d60e97838` |
| Hierarchical fit | `91b57546f3363d8abf30e65b1ace07365854fe1c033b85c88a8fb5b2ac6209aa` |
| Hierarchical fit without mismatch | `d0a0931d061efcc91077d803b131c39031e78d76d25ca7687c0b19ce562e9d03` |

## How many structures would show that noticing generalises? (29 September)

```bash
uv run python -m epistemics.ledger inclusion-hier-power --output output/inclusion-hier-power-20260929.json --spot-structures 10 --spot-spread 0.1 --spot-datasets 8
```

**Method.** Running the full model for each cell of a power grid would take hours, so the grid uses a surrogate.
- **Per structure:** each structure's full model is replaced by a normal estimate of its threshold. Its posterior SD is uniform on 0.15–0.45 rungs, the range the unpooled per-structure fits gave (0.15–0.47).
- **Pooled part:** the same priors and decision rule, on a grid. The truncation of θ_k to [−1, 4] is ignored.
- **Checked against the full model twice:**
  - **At five structures,** on the recovery study's true thresholds. Reading counts agree band by band: structure-specific 12.3 against 13 of 18 when the true spread is above 0.75; generalises 0.1 against 0 of 5 below 0.25. Spread estimates correlate at 0.94; the surrogate's are 0.2 rung lower on average.
  - **At ten structures,** true spread 0.1, 8 datasets with full fits. The pass mark, set before the run, was at least 4 of 8 "generalises", the lower end of the surrogate's 90% binomial range. Result: 5 of 8 (surrogate prediction 6.2), all converged (R-hat 1.019 or less). **It passes.** The full model is slightly more conservative than the surrogate.

**Power** (share of 400 synthetic configurations per cell reading "generalises", or "structure-specific" for the last row):

| True spread (rungs) | 5 | 8 | 10 | 15 | 20 | 30 |
| --- | --- | --- | --- | --- | --- | --- |
| 0.0 | 0.05 | 0.62 | 0.81 | 0.97 | 1.00 | 1.00 |
| 0.1 | 0.03 | 0.52 | 0.78 | 0.93 | 0.99 | 1.00 |
| 0.25 | 0.00 | 0.23 | 0.36 | 0.61 | 0.74 | 0.90 |
| 0.5 (at the limit), any definite reading | 0.04 | 0.07 | 0.07 | 0.11 | 0.06 | 0.07 |
| 1.0, structure-specific | 0.50 | 0.72 | 0.78 | 0.89 | 0.96 | 0.99 |

**What it means.**
- **Numbers of structures:**
  - If noticing truly generalises almost perfectly (spread 0.1 rung or less), about 10 structures per configuration would show it most of the time, and 15 would show it reliably.
  - A modest spread of 0.25 rung needs about 30.
  - The current five cannot show it at all.
- **Cost:** each structure takes 11 sessions per configuration on the ladder, about 5.8 million tokens at the urn run's rate. Ten more structures for two configurations would be about 115 million tokens, plus designing and validating ten new tasks.
- **For the product,** that is the price of the reading "noticing carries over". Testing only the hidden structures a given consumer cares about is cheaper. For now the guide reports that carry-over is not shown.

| File | SHA-256 |
| --- | --- |
| Power study and spot check | `0ebd6a478599ff1dc49fb9b3a0ab0db526e7de5db13cedf24eda8d7a969db0ce` |

## What it would add to the passport

The candidate readings are more general than the current task-level ones:
- "It does not consider hidden structure (copying, selective silence) unless the situation names it."
- "Once a structure is named, it considers it in about three of four sessions (Astra) or one in two (Sol)."
- "Asked about the structure, it states a rate, but in some sessions its forecasts do not use it" (Sol: φ = 0.87; Astra: φ = 0.97).

These become passport readings only if they transfer. In the corrected abstract run they did not transfer as configuration-level readings: thresholds differed by structure. Noticing readings therefore stay per structure.

## Next

1. **Joint fit.** Done (above). It fixes w's coverage and estimates stated–applied fidelity directly.
2. **Abstract transfer task (confirmatory).** Run on 28–29 September ([record](disposition-abstract-2026-09-28.md)). The preregistered fit did not converge because of two design flaws in the urn cues. Exploratory fits on the mismatch structure alone reproduced the dossier thresholds (θ 0.69 for both configurations). The parameters above stay dossier-specific until a corrected task is run. The original plan follows. Build contentless urn versions of copying (some draws are copies of earlier draws) and selection (a sampler shows only some draws). Add a third hidden structure, such as a common cause or survivorship. Each runs on the same four rungs, cued by structure alone. Preregister that the dossier θ predicts inclusion rates in the abstract tasks.
   - **The shared-trait claim** predicts that the configurations' ordering and rung profiles carry over.
   - **The family-specific alternative** predicts that the relay-like structure needs more prompting in every format.
3. **Corrected abstract transfer.** Run on 29 September ([record](disposition-abstract2-2026-09-29.md)).
   - **Preregistered fit:** did not converge (R-hat 1.96 and 1.15), so P1–P4 are not assessable.
   - **Per structure:** every fit converged, and θ differs by structure.
     - Selection: about −0.25 for both configurations; the records make it self-evident.
     - Copying: −0.77 for Astra and 0.07 for Sol.
     - Mismatch: 2.42 for Astra, whose reading was affected by the wording, and 0.86 for Sol.
   - **Against the dossiers:** only Sol's mismatch threshold is within 0.5 of its dossier value.
   - **Shared against structure-specific:** where both fits converged (Sol), structure-specific thresholds fit better by 3.5 SE.
   - **Conclusion:** the family-specific alternative is favoured. θ is a property of a structure, a cue format and a configuration together.
4. **Hierarchical thresholds.** Done (above). Recovery passed. Sol's spread is undetermined, and Astra's is exploratory (structure-specific, driven by mismatch). For both, an untested structure's threshold is unpredictable within about −0.8 to 2 rungs.
5. **How many structures would show generalisation?** Done (above): about 10–15 per configuration if the true spread is 0.1 rung or less, and about 30 for 0.25. The reading guide now says carry-over is not shown.
6. **Luna and Terra.** Collect rungs 0–2, so their θ is identified.

## Commands

```bash
uv run python -m epistemics.ledger inclusion
```

```bash
uv run python -m epistemics.ledger inclusion-validate --output output/inclusion-recovery-20260928.json
```

```bash
uv run python -m epistemics.ledger inclusion-joint
```

```bash
uv run python -m epistemics.ledger inclusion-joint-validate --output output/inclusion-joint-recovery-20260928.json
```

```bash
uv run python -m epistemics.ledger fidelity-validate --output output/inclusion-fidelity-recovery-20260928.json
```

| File | SHA-256 |
| --- | --- |
| Two-stage recovery | `18df6002a962ac6e664fa9beba29e10abbcfb585f2765515568399e65a77016e` |
| Joint fits | `eddcf0e00d564a535b52ac1ecdcd23f10db06200521e3d3e179d410bd05e9901` |
| Joint recovery | `8454492a1937a2f45cbec7713e7326862d6743a86ccd398d70cf408901a81673` |
| Fidelity recovery | `4ab83b87000e51d0f7f8b0f400d029a5e4547a5caa36ab4353b0792c5a2fa7bb` |
| Fidelity recovery, all-levels specification | `f6c469406047a2f56764ac677f8c3d47412706810064f36f9c44f24528dd8f4c` |
| Corrected urn fit (preregistered) | `514b71f280484d931f08d5b91674085abd9d07518a2456186bca04731d39d9ee` |
