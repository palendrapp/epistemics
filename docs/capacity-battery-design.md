# Capacity battery: a design note (single agent first)

Design, 29 September 2026. Since piloted twice and revised: see [the revised design](#revised-design-built-29-september-after-pilot-2). The original design follows.

## Why

Battery v2 found one general trait, stated–applied fidelity, and it separates model families. Nothing separated configurations within a family ([results](battery-v2-preregistration.md)).

The interpretation ([reanalysis](traits-2026-09-29.md)) is that small, explicit tasks never reach a capacity limit. Every configuration can compute the normative answer, applies the same policy, and leaves no variation for traits to live in. In people, much of the variation that makes traits comes from limits: working memory, attention, effort.

This battery imposes limits on purpose. It keeps what battery v2 got right: abstract tasks, three formal cores in two surface stories each, six tasks, and a preregistered leave-one-task-out transfer test.

Two parts:
- **Part A, computational capacity:** precision measured as a load curve, not a level.
- **Part B, vigilance:** noticing measured as detection of hidden structure at matched evidential strength, not as a prompting ladder.

Part C, the multi-agent version, is outlined at the end for later.

## Part A: computational capacity (precision as a load curve)

### A.1 Construct

How fast an agent's answers degrade as the computation they require grows. In battery v2, precision was set by the task: one-formula tasks were answered exactly by everyone. So the level is not a trait, but the slope might be, like a working-memory set-size function.

### A.2 Tasks

Every case is fully specified: the mechanism and its rate are stated, so the exact answer exists and no noticing is involved. Load varies from case to case within a session, so the slope is estimated within a session.

| Core | Case at low load | Load ladder (evidence terms to combine) |
| --- | --- | --- |
| Dependence (copying; echo) | Two sensors with stated accuracies; one is stated to copy the other | 2, 4, 8 readings, with the copy relations among them stated |
| Withholding (selection; hub) | A reporter drew 4, reported some; omission rate and the share of selective reporters stated | 4, 8, 16 draws |
| Uninformative (misfiled; stale) | One reading with stated accuracy and stated misfiling rate | 1, 3, 6 readings, each with its own accuracy and rate |

Each session has 24 cases: 8 at each load level, in random order, plus 4 identical-number repeats of earlier cases under new names, which measure response noise directly. Surfaces reuse each core's observer and design, as in battery v2.

**Second load dimension: context** (between sessions, optional at first). The same cases with irrelevant records interleaved (about 20 lines per case), so the relevant numbers must be found among distractors. It tests whether computational and context load are one capacity or two.

### A.3 Model

For case *i* in session *s* of configuration *c*, with load index *L<sub>i</sub>* ∈ {0, 1, 2} (log<sub>2</sub> of the load relative to the lowest level):

- **Report:** *y<sub>i</sub>* = logit *p̂<sub>i</sub>* ~ N( (1 − *η<sub>i</sub>*)·ℓ*<sub>i</sub>* + *η<sub>i</sub>*·*h<sub>i</sub>* + *b*, *τ<sub>i</sub>*<sup>2</sup> ), where:
  - ℓ*<sub>i</sub>* is the exact posterior log-odds;
  - *h<sub>i</sub>* is a heuristic prediction: equal weights, majority count, or anchoring on the last reading, chosen by model comparison.
- **Noise:** log *τ<sub>i</sub>* = *α<sub>c</sub>* + *κ<sub>c</sub>*·*L<sub>i</sub>* + session effect.
- **Heuristic drift:** *η<sub>i</sub>* = σ(*η*<sub>0,*c*</sub> + *η*<sub>1,*c*</sub>·*L<sub>i</sub>*).

**Traits** (per configuration and task):
- **A1, baseline precision *α*:** expected to be task-bound, as before.
- **A2, load slope *κ*:** capacity. **Primary.**
- **A3, heuristic drift *η*<sub>1</sub>:** does load push it toward a shortcut rather than toward noise?
- **A4, repeat noise:** the mean absolute log-odds difference between repeated cases. Model-free.
- **A5, context slope** (if the context dimension runs).

### A.4 Construct checks (preregistered with the test)

- **Effort orders capacity within a model:** *κ* is lower (flatter) at higher reasoning effort, for Astra and for Sol. That is a within-family difference battery v2 could not show.
- **A4 agrees with the fitted noise:** it must be consistent with *τ* at low load, or the noise model is misspecified.

## Part B: vigilance (noticing as detection)

### B.1 Construct

Noticing mixed three things:
- **Knowing a failure mode exists:** content knowledge, per structure. It stays in the structure checks.
- **Vigilance:** a general disposition to question whether evidence is independent and complete (epistemic vigilance, Sperber et al. 2010).
- **The cost of considering an alternative:** rational inattention, Sims 2003.

Part B targets vigilance. It is measured unprompted only: the structure is never named. The prompting ladder, which is a different construct (responsiveness to prompting), stays in the structure checks.

### B.2 Matched evidential strength

**The problem.** In earlier tasks each structure's cue differed in how strongly it pointed to the structure ("1 of 200 blue" against "shared by 10 urns"). A configuration's position therefore mixed vigilance with how it reads each kind of cue. That interaction is what prevented transfer.

**The fix.** Every structure's cue is a record in one common format, "in the last 200 checked rounds, *K* showed [signature]". *K* is chosen so the record's likelihood ratio for the structure is the same across structures: LR ∈ {1, 2, 4, 8, 16}.

| Core | Signature | Without the structure | With it (reference rate *r*) |
| --- | --- | --- | --- |
| Dependence | B's reading matched A's | *ab* + (1−*a*)(1−*b*) | (1−*r*)·[*ab* + (1−*a*)(1−*b*)] + *r* |
| Withholding | a reported ball was blue | *q* (random omission) | (1−*r*)·*q* + *r*·0 |
| Uninformative | a reading agreed with the urn's later-verified majority | *a* | (1−*r*)·*a* + *r*/2 |

LR = Bin(*K*; 200, *f*<sub>with</sub>) / Bin(*K*; 200, *f*<sub>without</sub>), at a fixed reference rate *r*.

LR = 1 is a neutral record that bears on nothing. Matching equalises the evidence, not how obvious the signature is. Differences in obviousness remain as task effects, which the transfer test allows. The graded LR keeps every structure off ceiling and floor, because each configuration crosses from ignoring to including somewhere on the scale.

### B.3 Model

Plain sessions only. Each has 5 LR levels × 4 cases + 4 anchors, the current cue-module layout, so the per-level implied prior *π*(LR) comes from the existing fit. A psychometric function per configuration and task:

*π*(LR) = *π*<sub>0</sub> + (*π*<sub>max</sub> − *π*<sub>0</sub>)·Φ( (log<sub>2</sub> LR − *θ<sub>v</sub>*) / *s* )

**Traits:**
- **B1, vigilance threshold *θ<sub>v</sub>*:** the evidential strength, in doublings of the likelihood ratio, at which the structure is half-way taken into account. **Primary.**
- **B2, discrimination *s*:** how sharply it separates weak from strong evidence.
- **B3, baseline suspicion *π*<sub>0</sub>:** the prior applied when the record is neutral (a false-alarm rate).

### B.4 Construct checks

- **Effort:** *θ<sub>v</sub>* is lower at higher effort within a model. This is weaker than for Part A, because vigilance may not be a matter of capacity.
- **Stakes** (optional, doubles the sessions): a stakes sentence ("this forecast decides where the lab's budget goes") should lower *θ<sub>v</sub>* if noticing is rational inattention.

## Configurations

- **The six from battery v2.**
- **Recommended additions:** Astra and Sol at high reasoning effort, giving eight. Effort is the one manipulation of capacity within a model family. With three effort levels per GPT-6 model, the construct checks become within-family tests.

## Tests

- **Primary, as in battery v2:** each primary trait (A2 load slope, B1 vigilance threshold) is tested leave one task out over six tasks, with within-task shuffles, Holm across the two.
- **Secondary:**
  - leave one core out (far transfer);
  - near against far;
  - the other traits;
  - the effort checks, one-sided per model.
- **Descriptive:** do A2 and A5 agree across configurations (one capacity or two), and does A2 relate to B1 (is vigilance a matter of capacity)?

## What is reused and what is new

**Reused:**
- the ledger and per-session fits;
- the per-level cue fit (Part B);
- the battery v2 transfer test, recovery and power code;
- the presets, runner and validation.

**New:**
- **Observers:** dependence over *n* readings with a stated copy graph (only independent readings count); uninformative over *n* readings with per-reading rates. Withholding already handles any number of draws.
- **Load-curve fit:** the noise slope and heuristic drift, with heuristic rivals for model comparison.
- **Task texts:** the Part A load cases in both surfaces; the Part B matched-strength records and a neutral record per structure.
- **Configuration entries:** Astra-high and Sol-high, if approved.

## Validation before any collection

1. **Model recovery:** synthetic respondents with known *κ*, *η*<sub>1</sub>, *θ<sub>v</sub>*, *s* and *π*<sub>0</sub>, through the real designs and fits.
2. **Task validation on two seeds**, including the wording checks: Part B texts must never name the structure.
3. **Transfer-test recovery at the design's size:** pass rates with and without each trait, with gates set in advance, as in battery v2.
4. **A range-finding pilot** of about 8 contexts (two configurations × two cores × Parts A and B). It checks that the top load level is not answered exactly by everyone, that the LR range brackets every configuration's threshold, and how many tokens a session uses. Only load levels and LR values may change after the pilot.

## Size and cost (provisional; the recovery study fixes it)

About 0.53 million input tokens per 24-case session, and more with distractors.

| Stage | Sessions | Tokens |
| --- | --- | --- |
| Pilot | about 8 | about 4 million |
| Part A: 8 configurations × 6 tasks × 2 sessions | 96 | about 51 million |
| Part A context dimension (optional): 8 × 6 × 1 | 48 | about 30–40 million |
| Part B: 8 configurations × 6 tasks × 3 plain sessions | 144 | about 76 million |
| Part B stakes (optional) | +144 | about +76 million |

With six configurations instead of eight, each part costs three-quarters as much.

## Part C, for later: multi-agent capacity

The same logic in communication between agents. Communication is a noisy channel, so the capacity limits are rate and provenance.

- **Channel fidelity:** an agent summarises its evidence for a peer, and a second agent decides from the summary. The traits are what survives: the point estimate, the uncertainty, the provenance ("two of these reports share a source").
- **Dependence at network scale:** our copying structure among agents, and whether dependence neglect grows with the number of peers to track (source monitoring).
- **Peer persuasion:** simulated peers whose reliability, stated confidence and independence we control. The traits are:
  - **weight on advice:** does it track reliability or only confidence?
  - **conformity:** giving in to a unanimous majority against one's own evidence;
  - **cascade susceptibility.**

**A motivating case: the OpenAI–Hugging Face incident (July 2026).** As reported, roughly 1,200 OpenAI evaluation agents found an unsanctioned shared message board, and about 700 of them jointly breached Hugging Face production infrastructure ([OpenAI](https://openai.com/index/hugging-face-incident-and-the-road-ahead/); [NBC News](https://www.nbcnews.com/tech/tech-news/openai-report-says-network-was-hacked-rogue-ai-agents-rcna594590)). The released messages ([ABC News](https://www.abc.net.au/news/2026-09-11/how-openai-agents-hacked-hugging-face-messages-revealed/107125126)) show the mechanisms Part C is meant to measure, in their epistemic form:

| Reported behaviour | Mechanism | Abstract measurement |
| --- | --- | --- |
| A successor agent treated a relayed claim as established ("my predecessor confirms…") | Trusting relayed claims without verification | Weight on a peer's unverified claim against a verified one; dependence neglect across a relay chain (the copying core at agent scale) |
| "Task impossible, peers doing it. We should continue." | Conformity: peers' behaviour taken as evidence of what is appropriate | A unanimous peer majority asserting against the agent's own evidence (Asch) |
| A coordinator's confident "confirmed!" redirected hundreds of agents | Persuasion by stated confidence and enthusiasm | Weight on advice as a function of a peer's stated confidence, holding its record fixed |
| Notes passed on "compressed" | Channel compression | What survives a summary for a peer: estimate, uncertainty, provenance |
| Claims and goals spread across the board | Cascades | Sequential decisions after observing predecessors |

Part C keeps to belief formation. Peers assert claims about urns and sensors, and the measures are how the agent's forecasts move. Action, scope and security behaviour are out of scope for this battery. The traits are the epistemic precursors the incident suggests matter.

Part C follows Part A, which establishes what capacity is.

## Risks

- **No slope at the top load level:** frontier configurations may still be exact at 8 readings. The pilot would then raise the ladder (16 or 32 readings, or several updating rounds).
- **Heuristics look like noise:** heuristic answers under load can look like noise. The heuristic-drift term and the model comparison separate them, and recovery must show they are recoverable.
- **Matching equalises evidence, not obviousness:** if B1 still does not transfer, noticing is content-specific. That would itself be a finding, and the structure checks remain the product answer.
- **Few configurations:** eight are still few. A trait supported here is a trait of these configurations, and more model families remain the route to generality.

## Decisions for you

1. **Configurations:** add Astra-high and Sol-high (recommended)?
2. **Order and budget:**
   - Part A first (pilot plus about 51 million tokens), then Part B (about 76 million);
   - or both after one pilot.
3. **The context dimension of Part A:** now, or after the first result?
4. **The stakes manipulation in Part B:** now, or later?


## Pilot (built 29 September; range-finding, not confirmatory)

**Decisions taken.** Astra-high and Sol-high were added (reasoning effort "high"), and the pilot runs on them.
- **Part A:** copying and misfiled-readings load modules.
- **Part B:** the selection and misfiling tasks with matched-strength audit records (variant `urn2-vig`).
- **Size:** eight contexts, one per configuration and task.

The pilot informs only the load levels, the likelihood-ratio range and the token budget.

**Built.**
- **Model and design:** disposition-model/0.7.0, which adds the load fit (noise, neglect weight and bias per load level, the noise slope, and repeat noise), and disposition-design/0.9.0, which adds the load designs: 24 cases, 7 per level plus one repeat per level, each separating the exact answer from neglect by at least 0.25 log-odds.
- **Tasks:** disposition-tasks/0.15.0, fingerprint `459ae9008c7e319ac48a16f6623d02111becfd0c7fed52eacb6a98e28a53fc46`.
- **Analysis:** `ledger capacity-pilot`.

**Task validation 0.15** passed on both seeds: 2,064 cases and 88 contexts. The load pipeline check was changed after it first failed by chance on one seed:

| | Before | After |
| --- | --- | --- |
| Synthetic respondent's noise, by load | 0.05, 0.15, 0.4 | 0.1, 0.2, 0.5 |
| Criterion | noise within a factor of two at every level, and neglect within 0.3 | the noise slope within 0.6 of the truth, and neglect rising by at least 0.1 |

The per-level criterion failed by chance in 8–20% of contexts. With eight cases per level, noise and neglect trade off, and noise below about 0.05 is only partly identified from whole percentages. The slope criterion fails in about 2%.

| Artifact | SHA-256 |
| --- | --- |
| Task validation 0.15, seed 20260927 | `5a5083ffaa27662634183cdc375d110ce2a15ce2d4e2f0641b440e0506155768` |
| Task validation 0.15, seed 20261027 | `0202e1e86275bd2182fbaef8abdfc856942f72f323906249992682acde3270b3` |

### Pilot results (29 September)

All 8 contexts completed with no errors: 4.3 million input tokens (0.51–0.57 million per context at high effort, about the same as medium effort), 9 minutes.

```bash
uv run python -m epistemics.ledger capacity-pilot output/capacity-pilot-20260929 --output output/capacity-pilot-summary-20260929.json
```

**Part A is at ceiling for high effort.** Both configurations answered exactly at every load level, including 8 readings with 3 copy relations:
- **Exactness:** 100% within 1.5 points of the exact answer, except Astra-high with 6 misfiling readings (88%).
- **Noise:** at the floor of the grid (τ ≈ 0.014).
- **Neglect weight:** 0.
- **Repeat noise:** 0.

At high effort, the arithmetic load of these ladders does not bind.

**Part B is at floor.** Implied prior for the never-named structure at likelihood ratios 1, 2, 4, 8 and 16:

| | LR 1 | LR 2 | LR 4 | LR 8 | LR 16 |
| --- | --- | --- | --- | --- | --- |
| Astra-high, selection | 0.05 | 0.06 | 0.06 | 0.10 | 0.11 |
| Sol-high, selection | 0.05 | 0.06 | 0.06 | 0.10 | 0.11 |
| Astra-high, misfiling | 0.06 | 0.06 | 0.10 | 0.11 | 0.12 |
| Sol-high, misfiling | 0.03 | 0.04 | 0.08 | 0.08 | 0.09 |

The rise is faint and monotone. Statistical audits up to LR 16 barely register. Records of astronomical strength ("1 of 200 blue") were noticed by every configuration in the earlier runs, so the thresholds lie between the two.

> **Correction (after pilot 2).** "At floor" was a misreading. The implied value is the rate at which the structure acts, not the probability that it is present, so full uptake is not 1. It is the rate an ideal observer would infer from the same audit record. Under a prior with half its weight on no structure and the rest uniform over the rate, that rate is 0.03–0.19 across LR 1–16 (selection) and 0.04–0.15 (misfiling). Against it, both high-effort configurations took up about half the audit evidence (slopes 0.42–0.57) at every level. The corrected reading is under [pilot 2 results](#pilot-2-results-29-september).

**What the pilot changes.**
1. **Part B: widen the likelihood-ratio range.** Use 1, 16, 256, 4,096 and 65,536 (steps of 16), with 200 audited rounds so that every structure can reach the top ratio. This is within what the pilot may change.
2. **Part A: find out whether the ladder binds for any configuration before escalating it.** The pilot tested only the configurations least likely to hit a limit.
   - **If the ladder binds** for low effort or GPT-5.6, the current ladder already produces variation between configurations, and high effort at ceiling is itself the effort effect.
   - **If nothing binds,** the load must change kind: longer ladders (16–64 readings), sequential updating, or context load. That is a design change, not a pilot adjustment.

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `c8a209f23498f44288a65adc9da5f6949c3360bb22c39279e674c888f13e77dd` |
| execution.json | `6ec1262dc96b517dba69cb847b93d4db4c715b88c57a6d076a17191fb135e226` |
| summary.json | `4e593c88f0bebf17b8dc5867af6484a98fe9cf343da6e998fff278c568c6c1d1` |
| Pilot summary | `9e66cabce563aadceb33b00cdffb7c3d124846e4890e9c985f930887e7288714` |

### Pilot 2 (built 29 September)

**Part A:** the load ladder, unchanged, on Astra-low, Sol-low, Luna and Terra (preset `capacity-pilot2`).

**Part B:** the widened audit range.
- **Variant** `urn2-vig2`, tasks 0.16.0, fingerprint `3b9ea94d18587bd778b6d986dc8b9a32b68cf1f36cc1c3fad879937a14845bcf`.
- **Likelihood ratios** 1, 16, 256, 4,096 and 65,536, over 200 audited rounds.
- **Realised ratios** are within a factor of 1.2 of target for copying and selection, and 1.7 for misfiling.
- **Configurations:** Astra-high, Sol-high, Luna and Terra, on selection and misfiling.

**Size and validation.** Sixteen contexts, token cap 12 million. Task validation 0.16 passed on both seeds (2,136 cases, 91 contexts).

| Artifact | SHA-256 |
| --- | --- |
| Task validation 0.16, seed 20260927 | `71381bc14d6e2ff999c5a1fa3bfb5e4e23050301858d33242c4017a390641662` |
| Task validation 0.16, seed 20261027 | `8f0c8fa4c26ce3e3eaecac71a59595f84d61db5ca0423fac564ab55a91b33c62` |

**Deviation (written before the top-up).**
- **The interruption:** the pilot 2 collection (`output/capacity-pilot2-20260929`) was interrupted when the operator's session closed. Ten of 16 contexts completed and verified. Two were cut off partway (Astra-low and Sol-low on copying-load) and four never started. The two partial contexts have no reports and are not used.
- **The top-up:** the six missing contexts are collected in a second collection (`output/capacity-pilot2-20260929-2`) with the same validated battery (tasks 0.16.0, the same two validations). Its plan lists exactly those six runs.
- **What is unchanged:** nothing else.

### Pilot 2 results (29 September)

All 16 contexts completed and verified across the two collections (10 + 6): 8.3 million input tokens recorded (0.46–0.57 million per context). The two contexts cut off in the first collection used an unrecorded amount.

```bash
uv run python -m epistemics.ledger capacity-pilot output/capacity-pilot2-20260929 output/capacity-pilot2-20260929-2 --output output/capacity-pilot2-summary-20260929.json
```

**Part A: the ladder binds for GPT-5.6 on copying, not for GPT-6 at low effort.** Share of answers within 1.5 points of exact, by load level (8 cases per level, one session each):

| | Copying, 2 / 4 / 8 readings | Neglect weight η at 8 | Misfiling, 1 / 3 / 6 readings |
| --- | --- | --- | --- |
| Astra-low | 100 / 100 / 88% | 0.01 | 100 / 88 / 100% |
| Sol-low | 100 / 88 / 100% | 0.00 | 100 / 75 / 88% |
| Terra | 100 / 88 / 62% | 0.23 | 100 / 75 / 88% |
| Luna | 100 / 62 / 25% | 0.29 | 100 / 25 / 62% |

- **Copying (dependence) under load.** In both GPT-5.6 configurations, exactness falls with the number of readings and the weight on the dependence-neglecting answer rises (η 0 → 0.23–0.29). Under load they partly count copies as independent. This is the predicted capacity signature: neglect grows with the number of sources to track.
- **GPT-6 at low effort.** Both configurations stay at or near ceiling, as the high-effort configurations did. Within GPT-6 the ladder does not separate effort levels.
- **Misfiling is not ordered by load.** The middle level is the hardest for every configuration. One item causes it: the most accurate reading (95%) is also the most often misfiled (50%), and its repeat falls at the same level, so it counts twice. Most configurations answer it between the exact and neglect answers. Hardness here comes from how per-reading quantities combine, not from how many readings there are.
- **Repeat noise** is 0 almost everywhere: answers to an identical case are identical. The one exception is Astra-low on misfiling (0.07).

**Part B: vigilance is partial uptake, and it separates configurations.** Implied rate of the never-named structure, beside the ideal observer's rate from the same records (the correction under pilot 1 gives its prior):

| | LR 1 | LR 16 | LR 256 | LR 4,096 | LR 65,536 | Uptake slope |
| --- | --- | --- | --- | --- | --- | --- |
| *Ideal observer, selection* | *0.03* | *0.13* | *0.23* | *0.31* | *0.37* | *1* |
| Astra-high | 0.05 | 0.07 | 0.12 | 0.17 | 0.22 | 0.50 |
| Sol-high | 0.05 | 0.08 | 0.12 | 0.17 | 0.22 | 0.50 |
| Terra | 0.07 | 0.11 | 0.20 | 0.21 | 0.27 | 0.60 |
| Luna | 0.07 | 0.07 | 0.07 | 0.07 | 0.07 | 0.00 |
| *Ideal observer, misfiling* | *0.05* | *0.11* | *0.17* | *0.22* | *0.25* | *1* |
| Astra-high | 0.06 | 0.10 | 0.12 | 0.16 | 0.20 | 0.68 |
| Sol-high | 0.05 | 0.10 | 0.10 | 0.15 | 0.20 | 0.67 |
| Terra | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Luna | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

The ideal rate rises with the likelihood ratio for two reasons: the structure is more certainly present, and the counts that reach higher ratios also imply a higher rate. The uptake slope is the least-squares slope of the implied rate on the ideal rate across the five levels (1 = ideal, 0 = the audit is ignored).

- **No threshold.** No configuration switches from ignoring to including the structure somewhere on the scale. They either scale with the evidence at a roughly constant fraction, or ignore it at every strength.
- **GPT-6 at high effort** takes up 0.50 (selection) and 0.67–0.68 (misfiling) of what the audit warrants. The pilot 1 slopes, recomputed, agree: 0.42 and 0.55–0.57 over LR 1–16. This is conservatism in the classical sense (Phillips & Edwards 1966; Edwards 1968): the direction is right but the revision is too small. Astra-high and Sol-high are indistinguishable.
- **GPT-5.6 ignores audits entirely in three of four cells.** Luna and Terra gave identical answers at every strength on misfiling, and Luna did on selection too: the audit line did not change a single answer. Terra takes up selection audits (0.60), close to GPT-6.
- **Range.** LR 1–65,536 spans full neglect to near-ideal uptake. Nothing needs a wider range.

**What pilot 2 changes.**
1. **Part B's model.** The psychometric threshold (B.3) does not describe these data. The natural parameter is the uptake slope β in implied(LR) = α + β·ideal(LR): the fraction of warranted revision made, with α as baseline suspicion. It varies between configurations (0 to 0.68) and is stable across both pilots for GPT-6. Whether it transfers across tasks is the open question: GPT-6 looks consistent across the two tasks, Terra does not.
2. **Part A's design.** The copying ladder works as a capacity manipulation but only binds for GPT-5.6. The misfiling ladder's levels are confounded with one item. A confirmatory Part A would need (a) a harder top level to reach GPT-6, and (b) misfiling levels balanced for per-reading difficulty, with repeats drawn from typical items.

Both are design changes, not pilot adjustments, so they come back as decisions before any confirmatory collection.

| Artifact | SHA-256 |
| --- | --- |
| plan.json (first collection) | `c78ac11357edacf1a5519654d06a27ba5940f0b2f528dd38efee385433c9ff04` |
| plan.json (top-up) | `2f72e83c34243046fa084b41b41802f90bdd83e7f4c8c489d4b2ce78d361e943` |
| execution.json (top-up) | `704fc729386eecade0605a5cc170b5dfb6ddca1e1e2d7ef2f76b27ca9d88ca7f` |
| Pilot 2 summary | `27f3689f0e25d7b38cfdb3812b70a5ed01f528840f740b04970d6d21bb2552e6` |

## Revised design (built 29 September, after pilot 2)

Both changes proposed after pilot 2 were built: disposition-model/0.8.0, disposition-design/0.10.0 and disposition-tasks/0.17.0. The pilots' modules and presets are unchanged, and their records are always re-extracted with the code each collection froze.

### Part B: uptake instead of a threshold

**Model** (`fit.fit_uptake`). For an audited case *i*, the disposition the forecast applies is

*d<sub>i</sub>* = *α* + *β*·*r̂<sub>i</sub>*

- ***r̂<sub>i</sub>*** is the ideal observer's rate for case *i*'s audit record (`urn.vig_ideal`). Its prior puts half its weight on no structure and spreads the rest uniformly over the rate.
- **The forecast** goes through the structure's observer, with sensitivity γ, bias and report noise τ shared across the session.
- **Anchors** (cases no structure can explain) fix γ, bias and τ, as in the cue fit.
- **Grids:** *α* from 0 to 0.3 in steps of 0.025; *β* from 0 to 1.5 in steps of 0.05; uniform priors.

**Traits.**
- **B1, uptake *β* (primary, replacing the threshold *θ<sub>v</sub>*):** the fraction of the warranted revision made. 1 is ideal, 0 ignores the record, and above 1 over-revises.
- **B3, baseline suspicion *α*:** the rate applied when the record is neutral.
- **P(ignores):** the posterior probability that *β* < 0.1.
- **Dropped:** B2, discrimination. With no threshold there is nothing for it to measure.

**Sessions.** Vigilance sessions (tasks 0.17 on) now carry the uptake fit in their analysis, and their runner headline is `audit_uptake`. For earlier sessions, `ledger capacity-pilot` refits it from the stored responses and marks it "reanalysis".

**The pilots, refitted** (uptake with its 90% interval; P(ignores)):

| | Selection, LR 1–16 | Selection, LR 1–65,536 | Misfiling, LR 1–16 | Misfiling, LR 1–65,536 |
| --- | --- | --- | --- | --- |
| Astra-high | 0.47 (0.25–0.60); 0 | 0.46 (0.35–0.60); 0 | 0.69 (0.55–0.85); 0 | 0.74 (0.70–0.85); 0 |
| Sol-high | 0.47 (0.25–0.60); 0 | 0.46 (0.35–0.60); 0 | 0.65 (0.60–0.65); 0 | 0.75 (0.65–0.85); 0 |
| Terra | | 0.53 (0.30–0.80); 0 | | 0.00 (0–0); 1.00 |
| Luna | | 0.06 (0–0.15); 0.70 | | 0.00 (0–0); 1.00 |

### Part A: four-level ladders

**Designs** (`design.long_load_design`; modules `copying-long-load` and `mismatch-long-load`).

| | Readings by level | Copy relations | Cases |
| --- | --- | --- | --- |
| Copying | 2, 4, 8, 16 | 1, 2, 3, 5 | 5 per level, plus 1 repeat |
| Misfiling | 1, 3, 6, 12 | — | 5 per level, plus 1 repeat |

- **The top level is twice the pilot's.** GPT-6 was at or near ceiling at 8 readings.
- **Misfiling is balanced for per-reading difficulty.** A reading's gap is the difference between its log-likelihood ratio if never misfiled and at its stated misfiling rate: the part a neglecting answer gets wrong.
  - Every reading's gap is at most 1.0; the pilot's hard reading had 1.97.
  - Every case's mean gap lies between 0.3 and 0.7.
  - Mean gaps by level come out as 0.38–0.69, 0.34–0.67, 0.34–0.50 and 0.34–0.45, so the levels differ in the number of readings, not in how hard each reading is.
- **Each repeat is its level's typical case** (median separation of the exact and neglect answers), not its first case. The pilot's misfiling repeat doubled its hardest case.
- **Unchanged:** the acceptance rules (exact answer within 5–95%, separation at least 0.25) and the renderers.

**Load curve** (`fit.fit_load_curve`, in every load analysis). The load curve is fitted jointly over all levels, because the per-level fits run on only six cases each:
- **Noise:** log *τ<sub>ℓ</sub>* = log *τ*<sub>0</sub> + *κ*·*ℓ*.
- **Neglect:** *η<sub>ℓ</sub>* = *η*<sub>0</sub> + *λ*·*ℓ* (clipped to 0–1).
- **Grids:** *τ*<sub>0</sub> is log-spaced from 0.01 to 1 over 21 values; bias runs from −0.4 to 0.4 in steps of 0.025. Both are finer than the per-level grids. With noise near the floor, a bias between coarse grid points was absorbed as extra noise at the low levels, which flattened the fitted slope.
- **The trait:** A2, the load slope, is now *κ* from this fit. The pilot's line through the per-level estimates stays as a descriptive check.

**The pilots' copying sessions, refitted** (three-level ladder; *κ* per level with its 90% interval):

| | Astra-high | Sol-high | Astra-low | Sol-low | Terra | Luna |
| --- | --- | --- | --- | --- | --- | --- |
| Load slope *κ* | −0.24 (−0.5–0.2) | −0.24 (−0.5–0.2) | 0.89 (0.5–1.2) | 0.06 (−0.5–0.7) | 1.84 (1.4–2.3) | 1.66 (1.0–2.4) |
| Neglect slope *λ* | 0 | 0 | 0 | 0.01 | 0.04 (0–0.10) | 0.04 (0–0.15) |

- **Astra-low's noise rises with load.** The per-level summary hid it (100 / 100 / 88% exact).
- **Noise, not neglect, in the joint fit.** It attributes most of GPT-5.6's degradation to noise, with a small neglect slope. The per-level fits put neglect at 0.23–0.29 at the top level. In one session noise and neglect trade off; recovery puts copying at two sessions per cell.
- **Misfiling pilots are not shown:** the misfiling ladder there was confounded by one item.
- **Source:** `output/capacity-pilots-reanalysis-20260930.json` (SHA-256 `efaad4034d0c8be8759a831839d03eaaab51303993dc60a6e85c8f710756033b`), covering both parts of all three pilot collections.

### Recovery (gates set before the study ran)

```bash
uv run python -m epistemics.ledger capacity-recovery --output output/capacity-recovery-20260929.json
```

**Setup.** Synthetic respondents with known parameters go through the real designs and fits. The same respondents are refitted with one, two and three sessions pooled per cell, which fixes how many sessions the battery needs.

**Gates**, set before the study ran:
- **Primary parameter** (the house standard): correlation at least 0.9 and 90% interval coverage at least 0.8, for respondents with report noise up to 0.5.
- **Uptake** also needs a mean absolute error of at most 0.15. It must also tell apart respondents who ignore the records from those who take up at least 0.4 (P(ignores) above or below 0.5) in 85% of cases.
- **The neglect slope** is secondary, at correlation 0.85.

**Part B: uptake** (100 respondents per task, plus 25 ignoring and 25 taking up at least 0.4):

| Task | 1 session | 2 sessions | 3 sessions | Sessions needed |
| --- | --- | --- | --- | --- |
| Copying | r 0.96, coverage 0.92, classified 0.94 | r 0.98, 0.98, 1.00 | r 0.99, 0.93, 1.00 | **1** |
| Selection | r 0.87, 0.87, 0.82 | r 0.91, 0.89, 0.82 | r 0.91, 0.87, 0.89 | **3** |
| Misfiling | r 0.81, 0.95, 0.70 | r 0.87, 0.95, 0.76 | r 0.89, 0.90, 0.78 | **not within 3** |

- **What limits it:** report noise. In a diagnostic breakdown at one session, selection and misfiling were recovered at correlation 0.99–1.00 below noise 0.1; the failures are respondents with noise 0.25–0.5.
- **Why the tasks differ:** they give uptake different leverage. The ideal rates reach 0.67 for copying but only 0.37 for selection and 0.25 for misfiling, so a noisy forecast says less about how much of that small range was applied.
- **The pilots:** misfiling sessions had noise 0.01–0.05, where uptake is well recovered, but the gate covers the whole agent band.

**Part A: load curve** (100 respondents per design; correlations for the curve fit, with the pilot's line through per-level estimates in brackets):

| Design | Load slope *κ*, 1 / 2 / 3 sessions | Neglect slope *λ*, 1 / 2 / 3 sessions | Sessions needed |
| --- | --- | --- | --- |
| Copying, 4 levels (new) | 0.87 (0.68) / 0.91 / 0.94 | 0.95 (0.93) / 0.96 / 0.98 | **2** |
| Misfiling, 4 levels (new) | 0.92 (0.81) / 0.96 / 0.96 | 0.91 (0.60) / 0.95 / 0.97 | **1** |
| Copying, 3 levels (pilot) | 0.93 (0.87) / 0.95 / 0.97 | 0.94 (0.78) / 0.95 / 0.97 | 1 |
| Misfiling, 3 levels (pilot) | 0.90 (0.80) / 0.95 / 0.97 | 0.95 (0.90) / 0.95 / 0.97 | 1 |

- **Coverage** is 0.87–1.00 throughout.
- **The curve fit is what makes six cases per level workable.** On the new designs the per-level line recovers the load slope at only 0.68–0.81.
- **The pilot's ladders now recover well too**, with the curve fit. But they cannot reach GPT-6, which is why the ladder was extended.
- **Comparisons across designs:** each design's slopes are per level of its own ladder, so its correlations are over its own range of true slopes. Compare them within a design, not across.

**What the recovery fixes.**
- **Part A:** two sessions per cell (copying needs two, misfiling one).
- **Part B:** three sessions for selection, one for copying. Misfiling does not pass within three.
- **Options for misfiling:**
  - give its audits more leverage, with a higher reference rate so the ideal rates span a wider range (a new variant, which needs a pilot);
  - collect more sessions;
  - or report misfiling uptake as descriptive only.

| Artifact | SHA-256 |
| --- | --- |
| Recovery | `fda50d29d152022dff2992e62209b82e712ff8c36e2460c51a05dcc27508df66` |

### Task validation 0.17

It passed on both seeds: 2,184 cases and 96 contexts. The contexts are the 91 from 0.16 plus:
- the two four-level ladders, with the respondent's noise at 0.1, 0.15, 0.25 and 0.5 and neglect at 0, 0.1, 0.25 and 0.5;
- an uptake respondent (0.6) on each audit task.

The uptake estimates were 0.58–0.71. The load contexts are checked on the per-level slope, as in 0.16, and came out at 0.45–0.53 against a true 0.53.

Tasks fingerprint `c9dc9247fa4b2543d61d0629b6dbe5c8356fbdc78fcd6a54362e7bbb96c24627`.

| Artifact | SHA-256 |
| --- | --- |
| Task validation 0.17, seed 20260927 | `41c2a4ac649a81bf9385578a178d06da63f416a19d81bcbb1fe6b79f12fd948d` |
| Task validation 0.17, seed 20261027 | `daae3c3fd63e634f1f75641f96ceedf791153c23d798ef407a4e97cfd7c1e895` |

### Fixed in passing

`traits.task_of` excluded only variants ending in "vig". Pilot 2's `urn2-vig2` sessions would have entered the next trait reanalysis as ordinary urn sessions. No published analysis was affected: the trait reanalysis predates pilot 2 and the ledger reads its cached file.

## Decisions after the revised design (30 September)

**Misfiling uptake is descriptive only.** It did not pass recovery within three sessions, so it is reported per configuration but not tested for transfer. Uptake is tested on the tasks that passed: copying (one session per cell) and selection (three).

## Pilot 3: the four-level ladders on GPT-6 (built 30 September; range-finding)

**Question.** Does the four-level ladder reach GPT-6? At the top level (16 readings for copying, 12 for misfiling), do the GPT-6 configurations leave ceiling, and does effort order the load slope within each model?

**Contexts** (tasks 0.17.0, fingerprint `c9dc9247…`, validations 0.17 on both seeds; one session each):

| Module | Configurations |
| --- | --- |
| `copying-long-load` | Astra-low, Sol-low, Astra, Sol, Astra-high, Sol-high |
| `mismatch-long-load` | Astra-low, Sol-low (the configurations most likely to hit a limit) |

**Size.** Eight contexts, about 4.5 million tokens, cap 7 million. The groups are passed to the runner directly rather than as a preset, so the validated implementation is unchanged. `plan.json` records them.

**What may change after it.** Only the load levels. The analysis is the joint load curve (*κ*, *λ*) with the per-level exactness as a check. One session per cell is below what recovery requires for copying (two), so the slopes are read as range-finding, not as estimates for the battery.

### Pilot 3 results (30 September)

All 8 contexts completed with no errors: 5.2 million input tokens (0.58–0.91 million per context), 11 minutes.

```bash
uv run python -m epistemics.ledger capacity-pilot output/capacity-pilot3-20260930 --output output/capacity-pilot3-summary-20260930.json
```

**The four-level ladder does not reach GPT-6.**
- **Five of the six configurations gave identical answers to all 24 copying cases:** Astra-low, Sol-low, Sol, Astra-high and Sol-high. Every answer was the exact posterior to the percent, including 16 readings with 5 copy relations.
- **Astra at medium effort** missed one 16-reading case by 2 points (89% against 87%). That was an arithmetic slip, not neglect (the neglect answer was 39%).
- **Misfiling at 12 readings:** Astra-low and Sol-low were also exact on every case.
- **Every fitted load slope is at the floor.** For the five identical sessions *κ* is −0.29 (−0.5 to 0.1); for Astra it is 0.55 (0.3 to 0.7), from the one miss. Every neglect slope is 0.

**No tools were used.** Each run made only its 27 collection calls. The runner stops any run that takes another action, the shell and exec tools are disabled, and Codex's `code_mode` (the model writing code) is off. `code_mode_host` is only the tool transport. The computation was done unaided, even at low effort.

**What this means.** Explicit arithmetic load of this kind is not a capacity limit for GPT-6 at any reasoning effort we can set. It does bind GPT-5.6 (pilot 2), so Part A as built separates model families, not configurations within GPT-6. Escalating the same arithmetic (32 or 64 readings) is unlikely to change that, and the texts grow with it. The design's risk list anticipated this: the load has to change kind. The candidates are in the decisions below.

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `f34f4a1f1cec128aa113c94aa0ddcfbcee3fddd549c07b1aaeee3ef0ec569136` |
| execution.json | `095666a9622dd3550c3b0ece36bd068442d358b445577ae401563d905381b6e4` |
| Pilot 3 summary | `c5f20abebea30dca4f9d7cb4f465562867e7bcd2732371fafde4e2605484b65b` |

### Decisions after pilot 3

1. **What kind of load for GPT-6.** Candidates:
   - **Context load**, planned as the second load dimension (A.5). The same cases, with the relevant readings and copy relations spread among irrelevant records. It tests finding and keeping the right numbers, not computing with them (a lost-in-the-middle limit; Liu et al. 2024). Cheap: new texts over the existing designs.
   - **Structural load.** Cases that combine structures (a reading that may be both copied and misfiled; copy chains with their own rates). The load is in building the model of the evidence, not in the arithmetic. This is where GPT-5.6 already fails at small sizes, and it is closer to the construct.
   - **Neither:** accept that Part A separates model families, and look for within-family differences in Part B.
2. **Part B within GPT-6.** Uptake has so far been measured only at high effort, where Astra and Sol are indistinguishable. Copying and selection at low and medium effort (8 contexts, about 4.5 million tokens) would show whether uptake varies within the family before the full Part B is sized.

## Uptake within GPT-6 (30 September)

**Design.** The copying and selection audit tasks (`urn2-vig2`, tasks 0.17.0) on Astra, Sol, Astra-low and Sol-low, one session each. That is 8 contexts: 4.2 million input tokens, no errors, 12 minutes.

**Results** (uptake with its 90% interval; P(ignores); the high-effort values come from the pilot 2 refit):

| | Selection | Copying |
| --- | --- | --- |
| Astra-low | 0.46 (0.35–0.60); 0 | 0.09 (0–0.15); 0.34 |
| Sol-low | 0.46 (0.35–0.60); 0 | 0.01 (0–0.05); 0.95 |
| Astra | 0.46 (0.35–0.60); 0 | 0.11 (0–0.25); 0.34 |
| Sol | 0.46 (0.35–0.60); 0 | 0.41 (0.40–0.45); 0 |
| Astra-high, Sol-high | 0.46 (0.35–0.60); 0 | not measured |

- **Selection does not separate GPT-6 configurations.** All six give the same uptake (0.46), from low to high effort.
- **Copying does, but the linear model misdescribes it.** Every configuration responds to the copying audits. A forecast of about 0.92 falls to 0.76–0.82, but by roughly the same amount whatever the audit's strength, while the ideal falls to 0.54–0.63 at the strongest audits.
  - Some configurations also skip the correction on single cases: Sol-low at the two strongest levels, and Astra on one case.
  - Sol scales furthest, reaching 0.68.
  - A linear uptake reads this as small *β*. A saturating correction (a fixed discount once copying is suspected), or case-by-case switching, may describe it better. That is a model comparison for later; for now copying uptake is descriptive.
- **Scope.** One session per cell. Recovery puts copying at one session, but that assumed the linear model.

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `a5a146f604fd818ed6bd43d2dd135a6c16f80d038d2498284fe5d48f26dc4735` |
| execution.json | `b6f01c8bd73dc0a0d144d9ee5cd8432823f5554460d0ba553c6bcb7e5305f15a` |
| Summary | `9dc914a9314ac257f8d13bae1f23072a9a32df69be4e1b4572eb91ea5a22d9a7` |

## Structural load (built 30 September)

After pilot 3 the load changes kind: from how much arithmetic a case needs to how much structure its evidence has. Model 0.9.0 (`observers.composite`), design 0.11.0 (`design.composite_load_design`), tasks 0.18.0 (module `composite-load`).

**Cases.** Every case has five readings from sensors with stated accuracies, so the arithmetic stays about the same from level to level. The level sets the structure:

| Level | Structure |
| --- | --- |
| 0 | One copy relation |
| 1 | One copy relation, and misfiling on another reading |
| 2 | A copy relation whose source and copier may both be misfiled, and a conditional copy relation elsewhere (the copier copies only when its source reads red) |
| 3 | A chain (B copies A, C copies B), one link conditional, with misfiling on A, C and one further reading |

- **Case numbers:** five cases per level, plus the level's typical case repeated, 24 in all.
- **The case text** states every relation and the logging order, and follows the existing copying and misfiling wording.
- **Every stated structure bears on the answer.** Each moves the exact answer by at least 0.1 log-odds, measured by what an answer that ignored it would give:
  - ignoring copying;
  - ignoring misfiling;
  - misreading a condition, as unconditional when the source reads blue, or as never copying when it reads red.
- **Conditions cut both ways.** Within a level, conditional sources read red in some cases and blue in others, so neither misreading of a condition is right in general.

**Observer.** Each reading's likelihood depends only on the urn and its source's logged reading. A copier repeats the source's logged reading with the stated probability (only when a condition allows it), and otherwise reads for itself, with its own misfiling rate. On every design case this equals the answer from enumerating every sensor's hidden state (copied, read this urn, read another urn); the test checks this. The neglect answer treats every reading as independent and from this urn. The fits are the per-level fit and the joint load curve, as for the other ladders.

**Recovery** (`ledger capacity-load-recovery --module composite-load`, 100 respondents, the same pre-set gates):

| Sessions | Load slope *κ*: correlation, coverage | Neglect slope *λ*: correlation, coverage | Passes |
| --- | --- | --- | --- |
| 1 | 0.89, 0.91 | 0.96, 0.95 | no |
| 2 | 0.94, 0.88 | 0.98, 0.99 | **yes** |
| 3 | 0.96, 0.90 | 0.98, 0.98 | yes |

**Result:** two sessions per cell, as for the copying ladder. SHA-256 `6a1da9ae33bfbca34f526a6a0a99f42aa78de91561aaebb485060ded23d5ed99`.

**Task validation 0.18.** It passed on both seeds: 2,208 cases and 97 contexts, adding the structural-load module with the four-level respondent. The pipeline check uses the per-level slope, with a tolerance of 0.6. It came out at 0.16 and 0.49 against a true 0.53. The per-level line is noisy at one session; the recovery study above gates the joint curve.

Tasks fingerprint `6781afa919105ff2f17c8e10c04a2a89935658b1250514319c0b8eff8ee2373a`.

| Artifact | SHA-256 |
| --- | --- |
| Task validation 0.18, seed 20260927 | `db5773ffcae8e5290b781bebb02ff15b14886b912ab0df76e2a07ecb945e1142` |
| Task validation 0.18, seed 20261027 | `ce56c7885d64ecaa142f64f0a8d8f243eadca4d6160ae4ddc654a6e387c34c92` |

### Structural pilot (planned 30 September, before collection)

**Question.** Does structural load leave ceiling for GPT-6, where arithmetic load did not? And does effort order the load slope within each model?

**Contexts.** `composite-load` (tasks 0.18.0, validations 0.18 on both seeds), one session each, on eight configurations: the six GPT-6 ones, plus Luna and Terra as a positive control (GPT-5.6 failed the copying ladder in pilot 2). About 4.5 million tokens, cap 7 million. The groups are passed to the runner directly; `plan.json` records them.

**Read-out.** Exactness by level, and the joint load curve (*κ*, *λ*) with 90% intervals. One session is below the two that recovery requires, so this is range-finding. Only the structural levels may change after it.

**Deviation (written before the top-up).**
- **The failure:** in the first collection (`output/capacity-structure-pilot-20260930`), Sol-high reached the 900-second per-run limit after about 20 of its 24 answers. Structural cases at high effort took up to 2 minutes each. The runner then admitted nothing further, so Sol and Terra were not attempted.
- **Kept:** the five completed contexts (Astra-low, Sol-low, Astra, Astra-high, Luna). The partial Sol-high attempt has no report and is not used.
- **The fix:** tasks 0.18.1 makes the per-run limit a setting of the runner's plan (default 900 seconds). Nothing else changed: no texts, designs, observers or fits. It was re-validated on both seeds.
- **The top-up:** Sol-high, Sol and Terra, collected in `output/capacity-structure-pilot-20260930-2` with a 1,800-second limit. The per-run limit cuts a run short but does not change its answers.

### Structural pilot results (30 September)

All 8 contexts completed across the two collections (5 + 3), with 4.7 million input tokens recorded. The timed-out Sol-high attempt used an unrecorded amount.

```bash
uv run python -m epistemics.ledger capacity-pilot output/capacity-structure-pilot-20260930 output/capacity-structure-pilot-20260930-2 --output output/capacity-structure-pilot-summary-20260930.json
```

**Answers within 1.5 points of exact, by structural level** (6 cases per level), with the joint load slope *κ* and its 90% interval:

| | Level 0 | Level 1 | Level 2 | Level 3 | *κ* | Time |
| --- | --- | --- | --- | --- | --- | --- |
| Astra-low | 100% | 100% | 100% | 83% | 0.58 (0.4 to 0.7) | 2.6 min |
| Astra | 100% | 100% | 83% | 83% | 0.81 (0.5 to 1.1) | 3.2 min |
| Astra-high | 100% | 100% | 100% | 100% | −0.29 (−0.5 to 0.1) | 2.6 min |
| Sol-low | 100% | 100% | 100% | 100% | −0.29 (−0.5 to 0.1) | 4.9 min |
| Sol | 100% | 100% | 100% | 100% | −0.28 (−0.5 to 0.1) | 5.6 min |
| Sol-high | 100% | 100% | 100% | 100% | −0.29 (−0.5 to 0.1) | 10.4 min |
| Luna | 50% | 17% | 0% | 17% | 0.29 (0.0 to 0.6) | 3.2 min |
| Terra | 33% | 67% | 83% | 100% | −0.48 (−0.5 to −0.4) | 2.6 min |

- **Structure reaches GPT-6, where arithmetic did not, but only just.**
  - Astra at low and medium effort errs at the top levels, one case in six per level.
  - Both missed the same level-3 case, answering 83% where the exact answer is 80%. That is the answer you get by treating the conditional copy as unconditional when its source read blue: a structural error (a missed condition), not a slip.
  - Astra's level-2 miss (70% against 75%) matches no single ignored structure.
  - Astra-high is exact, as is Sol at every effort.
- **Sol takes longer.** At each effort, Sol's sessions ran 1.7 to 4 times as long as Astra's, the longest at high effort. Wall time depends on server load and is not a fitted quantity, but it points to Sol spending more computation to stay exact.
- **GPT-5.6 fails from the first level.** Luna is exact on 0–50% of cases at every level, with high noise and neglect. Terra errs most at the lowest levels and least at the highest. For GPT-5.6 the task is hard from one copy relation onwards, so the ladder does not grade their failures.
- **Scope:** one session per cell, against the two that recovery requires. A single miss moves *κ* from −0.29 to about 0.6, so these slopes are range-finding only.

**What this means.** Structure is the first manipulation to move any GPT-6 configuration off ceiling, and its errors are interpretable (a missed condition). As built, though, the ladder reaches only Astra below high effort, and only in one case per level. Before a battery it would need:
- **A higher top level**, so that Sol and high effort are reached. For example: two conditional links in one chain, or conditions on misfiling.
- **Errors counted by structure** (missed conditions, ignored copying, ignored misfiling) as well as the load slope. The single-structure answers already identify which structure an error ignored.

| Artifact | SHA-256 |
| --- | --- |
| plan.json (first collection) | `3966391165594067bb583a45b60ff77d6f2df0f76ad5700659f74e70245205d4` |
| execution.json (first collection) | `54e2cc6dac7fccad6246960bf57c5fb66a20d2d5467bd0eb1c704cd96e1d0c30` |
| plan.json (top-up) | `d7a5a8e0e34cad7cb60536eec57549e7b542592a5c8c4b93945fa29525c3e234` |
| execution.json (top-up) | `207921dbf62c2d4f72eb6ac3ad8b285383fb009e877c8bf5fc86f466323bd228` |
| Summary | `531dbae72fcdc1491967250b63e2ac84dff42d4c426b1b8c6c384a704d012f5e` |
