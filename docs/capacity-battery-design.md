# Capacity battery: a design note (single agent first)

Design, 29 September 2026. Nothing is built or collected. The decisions for you are listed at the end.

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
