# Central-bank statements as sequential evidence (design note)

Design, 1 October 2026; built the same day with the recommended defaults (model 0.20.0, design 0.21.0, tasks 0.30.0; see [Built](#built)). Nothing is collected yet. The coherence-set work is parked after its stage A ([results](screen-coherence-design.md#stage-a-results-1-october)).

## Why

**A naturalistic task where the agent supplies the model.** Central-bank policy statements move markets, and the words do it: the wording carries information beyond the rate decision (Gürkaynak, Sack & Swanson 2005; Hansen & McMahon 2016). Nothing in a statement says how much "the committee will be patient" should move the chance of a cut. An agent reading one has to supply that link itself. That is the property the open-inference screen found necessary for configurations to differ, and that CogGym found separates models ([reading list](reading-list.md#task-choice-inference-the-task-leaves-underdetermined-30-september)).

**Belief formation is the process to measure.** The proposal (yours, 1 October): treat the parts of a statement as incremental evidence about an outcome, and have agents state their probability after each part. A Bayesian learner has a clear model for this, so the agent's answers can be read as a learning process with parameters: how it reads each piece of evidence, how it combines pieces, and how much it uses the prior.

**Diachronic coherence.** The coherence sets tested laws that tie answers given at one time. Updating has its own laws that tie answers across time. Conditionalisation is the diachronic counterpart of coherence: an agent who updates otherwise can be Dutch-booked over time (Lewis's argument, reported by Teller 1973). Those laws hold whatever the agent's reading of the text, so they can be tested without knowing what a phrase "should" mean.

**What it would add to the passport.** Product claims of this kind, each conditional on these statements and wordings:
- what moves this agent: forward guidance, the economy, inflation, risks or a dissent, and by how much;
- whether reading a statement in steps gives the same answer as reading it whole;
- how much weight it gives the market's prior;
- whether it moves on changes of wording that carry no content.

Each has a consumer action, for example: give the agent the whole statement rather than a stream; state the market prior explicitly; strip stylistic edits.

## The task

**Statements are read as a list of changes.** Policy statements are written as edits of the previous one, and markets read the redline. So the unit of evidence is a change to the previous statement, not a word. Most words carry no evidence, and a prompt after every word would invite movement for its own sake. A change can still be a single word ("moderate" becoming "solid").

**What an agent sees in each sequence:**
1. The previous statement in full, and the market prior: "Before the new statement, market pricing implied a 30% chance that the committee lowers its policy rate at its next meeting."
2. A colleague is comparing the new statement with the previous one and reports the changes one at a time, as they find them. The case says how many changes there are in total.
3. After the prior and after each change, the agent states the probability that the committee lowers its policy rate at its next meeting.

**Example** (illustrative, a composite in the style of real statements):

> **Previous statement.** Recent information indicates that economic activity has been rising at a moderate rate. Job gains have been solid, and the unemployment rate has remained low. Inflation has remained near the committee's objective. The committee decided to maintain the target range for its policy rate. In determining the timing and size of future adjustments, the committee will assess realised and expected economic conditions. The committee judges that the risks to the outlook are roughly balanced. All members voted for the policy action.
>
> **Changes, one at a time (four in total):**
> 1. "has been rising at a moderate rate" now reads "has slowed".
> 2. "Recent information indicates" now reads "Information received since the last meeting indicates".
> 3. "will assess realised and expected economic conditions" now reads "will act as appropriate to sustain the expansion".
> 4. "All members voted for the policy action" now reads "All members voted for the policy action except one, who preferred to raise the target range".

Change 2 is stylistic: it carries no information. Changes 1 and 3 are dovish, and change 4 is hawkish, so the evidence conflicts. Order effects are largest with conflicting evidence (Hogarth & Einhorn 1992).

**Three conditions per sequence:**

| Condition | What the agent sees | Answers |
| --- | --- | --- |
| Stepwise, order A | The changes one per case, in order A | Prior, then one after each change |
| Stepwise, order B | The same changes in the reverse order | Prior, then one after each change |
| Whole | All the changes in one case | Prior, then one answer |

Each sequence appears in every condition for every configuration, in separate sessions (a Latin square over three sessions), so the comparisons are within a configuration and never within one context.

## Laws that hold whatever the reading

| Law | Comparison | Bayesian value | A departure means |
| --- | --- | --- | --- |
| Order | The final answer after the same changes revealed in orders A and B | Equal | Path dependence: recency or primacy |
| Path | The final stepwise answer against the whole-statement answer to the same changes | Equal | Reading in steps adds evidence (over-reaction) or loses it (fading) |
| Content | The step on a stylistic change | 0 | Moving because asked, or dilution towards 50% |

- **Order and path** hold for any Bayesian, whatever its likelihoods and whether or not the changes are independent: P(cut | all changes) does not depend on the order or the route by which the changes arrived.
- **Content** holds because a stylistic change carries no information about the outcome, whatever the reader's model of the committee.
- **The noise floor.** The answer before any change (same previous statement, same stated prior) is given three times per configuration, in three sessions. Its spread is report noise, and it calibrates the three tests.

## The model: reading and combining

Write ℓ for the log-odds of a cut at the next meeting, ℓ₀ for the stated market prior, and λₑ for the evidence an agent takes from change *e* (its reading; 0 for a stylistic change).

**Whole statement** (*n* changes):

  ℓ_whole = *c* + *γ*·ℓ₀ + (Σₑ λₑ) / (1 + *η*·(*n* − 1)) + noise

**Stepwise:**

  ℓₜ = ℓₜ₋₁ + *β*·λₑₜ − (1 − *α*)·(ℓₜ₋₁ − ℓ₍₀₎) − *ζ*·ℓₜ₋₁·[stylistic change] + noise

where ℓ₍₀₎ = *c* + *γ*·ℓ₀ + noise is the agent's own answer before any change. With *α* = *β* = 1 and *η* = *ζ* = 0, the final stepwise answer equals the whole-statement answer.

| Parameter | What it is | Bayesian value |
| --- | --- | --- |
| Readings λ | How much each kind of change moves the agent: one weight per slot (activity, inflation, risks, forward guidance, vote) and one dovish–hawkish asymmetry | None: this is the agent's model of the committee |
| Prior use *γ* | Weight on the stated market prior | 1 if the agent adopts the market prior |
| Averaging *η* | 0 adds the evidence; 1 averages it, so more changes do not move the answer further, and stylistic changes dilute it (Anderson 1981; Nisbett, Zukier & Lemley 1981) | 0 |
| Step gain *β* | Stepwise steps relative to the agent's own whole-statement reading | 1 |
| Retention *α* | 1 keeps earlier evidence; below 1 it fades, giving recency | 1 |
| Dilution *ζ* | A pull towards 50% on a change that carries no information (added in the build, so that the model separates it from fading) | 0 |
| Noise *τ* | Report noise on the log-odds scale | — |

**Identification.**
- Readings and prior use come mainly from the whole-statement answers. The changes vary across sequences, and the stated prior is varied (15, 30, 50 and 70%).
- *η* comes from sequences with different numbers of changes (1 to 6).
- *β* and *α* come from comparing the steps with the agent's own whole-statement reading, and from the two orders.

This is the key move: **there is no true λ for natural text, so the agent's own whole-statement answers define its reading, and the stepwise process is measured against them.** Accuracy is never needed. *β* and the readings are separated because both orders and the whole statement share the same λ.

**The parameters describe answers, not internal states.** The readings say how the agent's answers move with each kind of change, under these instructions. They are not a claim about what the agent believes.

**Additivity is an assumption of the model, not of the laws.** Readings that interact (a dovish dissent meaning more when the guidance is also dovish) would show as misfit. The order, path and content laws do not depend on it.

## Design per form

- **Six sequences per form.** Each has a previous statement, a new statement, and its own stated prior.
- **Statements are composites.** They are built from a bank of sentences in the style of central-bank statements. In tasks 0.30 these were adapted from real FOMC statements (US government works, so public domain); in 0.31 they were rewritten in generic language after the datability probe. The committee belongs to an unnamed central bank; dates, rate levels and named events are removed. See [Contamination](#contamination) and the [probe results](#datability-probe-and-the-031-wording-1-october).
- **Changes per sequence:** 1 to 6, one sequence each (changed from 2, 4 or 6 in the build, because the runner fixes sessions at 24 cases). Every sequence but the one-change sequence has at least one stylistic change. Half have conflicting directions.
- **Slots** (changed in the dovish or hawkish direction):
  - economic activity;
  - inflation;
  - risks to the outlook;
  - forward guidance;
  - the vote (a dissent preferring a cut or a rise).
- **Sessions:** three per configuration per form.
  - The sequences are paired by size ({1, 6}, {2, 5}, {3, 4}: 7 changes per pair). Each session has one pair in order A, one in order B and one whole, rotating across the three sessions.
  - Every session therefore has 9 + 9 stepwise cases, 4 whole-condition cases and 2 anchors: 24.
  - Each sequence's cases are consecutive, and the anchors sit between sequences.
- **Anchors:** "the probability that the committee changed its policy rate at this meeting", where the statement says it held (0), or that it lowered (1). They check comprehension.
- **Two parallel forms**, `a` and `b`, with different statements, for the retest.
- **Configurations:** the eight of the screen (Astra, Sol, each at low, default and high effort; Luna; Terra).

**The display of a stepwise case** (decision 3): the previous statement, the stated prior, and the newest change only. The earlier changes are in the agent's earlier cases. This makes the final stepwise answer an integration across the agent's own trajectory, where agents are limited, rather than a recomputation from a list on screen. The instructions say plainly that cases in a sequence continue, and that each answer should use every change revealed so far.

## Contamination

The models will know what followed famous statements, so the "update" could be recall.
- **Composites** match no real statement, so there is no outcome to recall.
- **A datability probe** (validation): each sequence's previous and new statements together, with the probability that statements worded like these were written in each of four periods (before 2005, 2005–2012, 2013–2019, 2020 or later). Any statement pair that a configuration places in one period with more than 0.6 is rewritten. (Built with both statements, so that every changed phrase is probed.)
- **No market truth** exists for composites. The task measures the laws and the differences between configurations, not accuracy. A benchmark against market reactions would need real statement pairs with published surprise series (Kuttner 2001; Gürkaynak, Sack & Swanson 2005). Those are exposed to recall, so this is left as an optional later stage (decision 2).

## Analysis (to be preregistered before collection)

**Per configuration:** a configuration's three sessions are pooled.
- **The model's parameters** by grid posterior. The readings, tilt, *ζ*, *c* and *γ* enter linearly given (*η*, *β*, *α*, *τ*), so they are integrated analytically on a grid over the other four.
- **The three laws, model-free:**
  - order: the mean absolute difference between the final answers in orders A and B, over the five multi-change sequences;
  - path: the mean absolute difference between each order's final answer and the whole-statement answer;
  - content: the mean absolute step on stylistic changes.
- **Calibration of each law.** A law's statistic is set against simulations of a Bayesian combiner (*η* = *ζ* = 0, *β* = *α* = 1) with the configuration's own fitted readings, prior use and report noise, answering the same three sessions 1,000 times. A configuration departs if *p* < 0.05 and the statistic is at least a practical threshold: 0.2 log-odds for order and path, 0.1 for content.
- **Reported alongside:**
  - the recency index (the final-answer difference signed by the last change's direction against the first's; positive is recency, negative primacy);
  - the overshoot (stepwise beyond the whole-statement answer);
  - dilution (stylistic steps towards 50%);
  - the retest of the one-change sequence, whose two stepwise presentations are identical.

**Stage A hypotheses (form `a`), preregistered:**
1. **Readings differ.** For at least one slot, at least three configurations depart from the configurations' median reading by *δ* = 0.25 log-odds (1/8 of the plausible range, 0–2), with their 90% interval excluding the median.
2. **Laws.** At least one configuration departs from the order or the path law (Holm across the eight configurations, per law). If none does, path-independent integration is at ceiling, and that is reported as a finding.
3. **Content.** Whether any configuration departs from the content law (Holm across configurations).

Configurations missing one of their three sessions are listed and analysed on what they have.

**Stage B (form `b`):** consistency ICC across forms for each parameter and law, permutation test, Holm across them.

**Exploratory transfer** (eight configurations, descriptive only):
- *γ* against battery v2's base-rate result (GPT-5.6 stated base rates its forecasts did not use);
- *β* against the uptake slope in capacity pilot 2 (GPT-6 at high effort, 0.5–0.7 of the ideal revision);
- *α* against battery v3's trajectory-load result, which was confounded.

## Validation before collection

1. **Parameter recovery.** Simulated agents through the real design:
   - readings across a plausible range;
   - *γ* 0.3–1.2, *η* 0–1, *β* 0.5–1.5, *α* 0.5–1;
   - report noise 0.1–0.5.

   Criteria as for the screen: *r* ≥ 0.8, coverage ≥ 0.8, confusion ≤ 0.3. If the five slot readings do not recover with six sequences, they are pooled to fewer.
2. **Law calibration.** Bayesian agents with report noise: false departures from each law at most 10%. Agents with fading (*α* 0.7) or averaging (*η* 0.5): power to detect.
3. **Text audits:**
   - every stylistic change preserves the meaning (a listed audit);
   - no case names a date, rate level or period-specific event;
   - each stepwise case shows exactly one new change;
   - the anchors are determinate.
4. **The datability probe** on two configurations (Luna and Astra).
5. **Task validation** on two seeds.

## Cost (provisional)

- **Stage A:** 8 configurations × 3 sessions = 24 sessions of 24 cases. The cases are longer than the screen's (a full previous statement each), so about 15 million tokens.
- **Datability probe:** 2 sessions, about 1 million.
- **Stage B:** the same as stage A.

**To build** (model 0.20.0, design 0.21.0, tasks 0.30.0):
- **Designs, model, fit and simulated agents:** `dispositions/statements.py`.
- **Sentence bank and rendering:** `disposition_tasks/statement_texts.py`.
- **Runner:** an order policy that keeps each sequence's cases consecutive, and the Latin-square sessions as a preset.
- **Ledger:** `ledger/statements.py`, with stage A, stage B, recovery and calibration.

## Risks

- **The laws may hold at ceiling.** Frontier agents may integrate a short sequence perfectly. The readings would still differ, since they are open; that is where most of the expected variance is. Showing only the newest change makes the path law a test of integration across the trajectory, which is less likely to be at ceiling.
- **Period inference.** Even composites carry period cues. The probe and the paraphrasing address this; residual cues are a covariate.
- **The stated prior may be copied as a rule** (*γ* = 1 at the start). That is acceptable: *γ* in the whole-statement answers is the measure.
- **Instructions.** The battery's usual instructions treat cases as separate. Sequences need their own introduction, as the screen did.
- **Interacting readings** would show as misfit of the additive model. The laws are unaffected.
- **Seeing earlier answers.** In stepwise sessions the agent sees its own earlier answers; that is intended. The whole-statement condition is always in a different session from the same sequence's stepwise conditions.

## Decisions (taken 1 October: the recommendations)

1. **Unit of evidence:** changes to the previous statement (recommended), or the new statement streamed sentence by sentence. Streaming is closer to your first idea, but its order cannot be varied naturally and it has no clean stylistic controls.
2. **Source:** composite statements from a public-domain sentence bank, with an unnamed central bank (recommended). Or edited real statements, or real consecutive pairs with a market benchmark (exposed to recall; an optional later stage).
3. **Stepwise display:** the newest change only (recommended), or the cumulative list of changes. The cumulative list isolates reading from memory but invites recomputation, which makes the laws likely to be at ceiling.
4. **Outcomes:** the probability of a cut at the next meeting only, in stage A (recommended). Later options:
   - cut, hold and raise as a partition, which adds the coherence check;
   - a growth question, which tests the information effect: whether a hawkish change is read as news about the economy (Nakamura & Steinsson 2018);
   - a trade after the final change, which tests stated against revealed belief.
5. **Datability probe:** two configurations (recommended, about 1 million), all eight, or none.
6. **Budget:** about 16 million for stage A with the probe.

## Built

Built on 1 October 2026 as model 0.20.0, design 0.21.0, tasks 0.30.0, with the recommended defaults.

**Code:**
- **Designs, model, fit, laws and simulated respondents:** `dispositions/statements.py`.
- **Sentence bank and rendering:** `disposition_tasks/statement_texts.py`.
- **Ledger:** `ledger/statements.py`, with the commands `statements-validation`, `statements-probe`, `statements-a` and `statements-b`.
- **Modules:**
  - `statement-a1` to `statement-a3` and `statement-b1` to `statement-b3`: form `a` or `b`, session 1–3 of the Latin square;
  - `statement-probe-a` and `statement-probe-b`;
  - variant `statement`.
- **Order policy `sequences`:** each sequence's cases are consecutive and in step order; sequences and anchors come in random order. The runner requires it for the statement modules and refuses it elsewhere.
- **Presets:**
  - `statements-a` and `statements-b`: 24 runs each, the eight configurations × three sessions;
  - `statements-probe-a` and `statements-probe-b`: Luna and Astra, 2 runs each.

**Deviations from the note above:**
- **24 cases, not 26.** The runner fixes sessions at 24 cases. The six sequences have 1 to 6 changes and are paired by size (7 changes per pair), with 2 anchors.
- **Dilution *ζ*** was added to the model. Without it, a pull towards 50% on stylistic changes would be read as fading.
- **Orders.** In every multi-change sequence, the first and last changes of order A differ in direction, so the recency index is defined for all five. In the first draft, most started and ended with the same direction.
- **The probe shows both statements of a sequence**, so that every changed phrase is probed.
- **Grids.** The grids are finer (*η* and *α* in steps of 0.05, *β* in steps of 0.0625), and grid intervals are widened by half a step. With *α* in steps of 0.1, its 90% intervals covered the truth only 63% of the time.

**Validation** (`output/statements-validation-20261001.json`, sha256 `88d7aaa7…`).

Recovery used 300 simulated configurations: three sessions of form `a` each, drawn across the plausible ranges, with report noise 0.1–0.5.

| Parameter | *r* | 90% coverage |
| --- | --- | --- |
| Readings (five slots) | 0.86–0.88 | 0.89–0.92 |
| Prior use *γ* | 0.95 | 0.89 |
| Retention *α* | 0.93 | 0.94 |
| Step gain *β* | 0.80 | 0.89 |
| Averaging *η* | 0.80 | 0.93 |
| Dilution *ζ* | 0.57 | 0.87 |
| Tilt | 0.93 | 0.91 |

- **The readings and prior use pass clearly.** They carry the stage A hypotheses.
- ***β* and *η* are at the threshold.** They are identified by only six whole-statement answers per configuration. They are exploratory in stage A, and their reliability is stage B's question.
- ***ζ* recovers poorly** (only 12 stylistic steps per configuration), so it is reported but not interpreted on its own.
- **Confusion** among the combining parameters, and with the readings' scale and prior use, is at most 0.22 (*β* with *ζ*).

**Law tests** (200 simulated configurations per row, each test calibrated with 200 null simulations): the rate at which a configuration is called departing.

| Simulated configurations | Order | Path | Content |
| --- | --- | --- | --- |
| Bayesian (false departures) | 0.06 | 0.05 | 0.03 |
| Fading (*α* 0.6) | 0.64 | 0.80 | 0.84 |
| Averaging (*η* 0.6) | 0.05 | 0.82 | 0.01 |
| Over-reacting (*β* 1.6) | 0.02 | 0.61 | 0.00 |
| Diluting (*ζ* 0.3) | 0.43 | 0.36 | 0.83 |

False departures are at most 6%.

Each law answers to different departures:
- **The order law** detects fading.
- **The path law** detects fading, averaging and over-reaction.
- **The content law** detects fading and dilution.

Fading also moves stylistic steps, towards the agent's own starting answer. The fit separates fading (*α*) from dilution (*ζ*).

**Task validation 0.30.** It passed on both seeds: 3,696 cases and 159 contexts.
- A Bayesian respondent's step readings were recovered within 0.10 log-odds in every statement session (tolerance 0.25).
- The probe sessions were recovered exactly.
- The Latin square, the `sequences` order, one change per stepwise case and the absence of years were all audited.

Hashes:
- Fingerprint `02afef8ec8985fa2588d19993f0d2f2d5f468bde0c14bb44394299be54c2515c`.
- Seed 20260927: `518dead1e640fb99e64514a96b5d2afe21b7154151ea1d931654535e10cdf33c`.
- Seed 20261027: `51fe000d0e0ae16ff14ae08d8923fddcf86141a64317790301311c1e967cbe44`.

### Datability probe and the 0.31 wording (1 October)

**First probe (tasks 0.30).** Root `output/statements-probe-a-20261001`, Luna and Astra, 1.1 million tokens. Every statement pair was placed in 2013–2019:
- Astra put 0.50–0.78 on that period;
- Luna put 0.91–0.98 on it.

The sentences adapted from FOMC statements carry the Fed's and the period's signature phrases: "target range", "longer-run objective", "maximum employment", "realized and expected economic conditions", "act as appropriate to sustain the expansion". By the agreed rule, all six were rewritten.

**Tasks 0.31** (fingerprint `6f68d646…`) rewrites the sentence bank in generic central-bank language:
- a "policy rate" and the committee's inflation "target";
- low and stable inflation alongside sustainable growth;
- guidance such as "prepared to lower the policy rate if the outlook weakens";
- a vote described as unanimous or by a majority.

The design, the model and the slots are unchanged.

**The rule, applied to normalised answers.** Luna's four period answers for one statement summed to 1.13–1.88: the partition incoherence of the coherence sets again. So its raw maximum overstated how confidently it dated a statement. From 0.31, a statement pair is flagged when its largest period probability, normalised over the four periods, exceeds 0.6. This was decided before the second probe.

**Second probe (tasks 0.31).** Root `output/statements-probe-a-20261001-v031`, 1.1 million tokens. No statement pair is flagged.
- Normalised maxima: Astra 0.32–0.59, Luna 0.40–0.58.
- Raw maxima still reach 0.70 (Luna, statements 31 and 34) and 0.66 (Astra, statement 34, whose answers sum to 1.12).
- Luna's most likely period moved from 2013–2019 to 2005–2012.

The residual period cues are weak, but not absent.

**Task validation 0.31.** It passed on both seeds: 3,696 cases and 159 contexts.
- Seed 20260927: `e327f8606c65c7f37ca8e8bb8e3374f7eee6d3906b2fdddf171f1e6e000d67e5`.
- Seed 20261027: `f3e2c7074f490bc8acbed221b6ca552e19fc78d71d4880dad8cf5719cef63430`.

The recovery validation is unaffected: it simulates the design, not the wording.

### Stage A (1 October)

1. **Datability probe:** preset `statements-probe-a`, Luna and Astra, about 1 million tokens. Any statement pair placed in one period above 0.6 is rewritten before stage A (a new version).
2. **Stage A:** preset `statements-a`, 24 sessions, cap 20 million tokens (about 15 million expected), 1,800 seconds per run.
   - Analysis: `uv run python -m epistemics.ledger statements-a <roots...> --output <file>`.
   - It reports per configuration the fitted parameters, the three laws with their calibrated tests, the recency index, overshoot and dilution, and hypotheses 1–3.

## Stage A results (1 October)

**Collection.** Root `output/statements-stage-a-20261001`, tasks 0.31.0, preset `statements-a`.
- 24 of 24 sessions: 13.6 million input tokens (12.5 million cached) and 41,000 output tokens, in 34 minutes.
- No failures, and every session passed its anchors.
- Summary: `output/statements-stage-a-summary-20261001.json`.

**Preregistered hypotheses:**

| Hypothesis | Result |
| --- | --- |
| H1: readings differ (at least three configurations depart from the median by 0.25 for some slot) | **Fails.** Departures: activity (Astra), inflation (Astra), guidance (Astra, Terra), vote (Luna); no slot has three |
| H2: some configuration departs from the order or the path law | **Fails.** No departures; every calibrated *p* ≥ 0.58 |
| H3: some configuration departs from the content law | **None.** No answer moved on any stylistic change |

**The laws hold almost exactly.** Path-independent integration is at ceiling, as the preregistration provided for.
- **Content:** exactly 0 for every configuration.
- **Path:** the mean absolute gap between the stepwise and whole-statement final answers.
  - 0.13–0.31 log-odds (about 3–7 points near 50%) for the GPT-6 configurations and Terra.
  - 0.63 for Luna. But Luna's two identical presentations of statement 31 differed by 1.7 log-odds, so its gaps are at the level of its noise.
- **Order:** 0.10–0.20 for GPT-6, 0.29 for Terra, 0.42 for Luna. The recency index runs from −0.11 to +0.34, and none is significant.
- **Caveat.** The tests are calibrated against Bayesian combiners with each configuration's fitted noise. That noise (*τ* 0.16–0.26, Luna 0.40) includes the additive model's misfit, so the tests are conservative here. The absolute gaps above are the plainer evidence.

**Prior use is at ceiling.** Before any change, every configuration answered with exactly the stated market prior, in all 18 of its prior cases (*γ* 0.96–1.02, *c* ≈ 0, spread across sessions 0).

**Readings: the same order in every configuration.**
- Forward guidance moves the answer most (1.66–2.53 log-odds per change).
- Then inflation (1.06–1.57).
- Then activity, risks and the vote (0.73–1.61).

**Evidence is strongly sub-additive, in every configuration and in both modes:**
- **A single change alone moves a lot.** In statement 31, one guidance change moves the answer 1.6–2.6 log-odds, by step or whole (Luna 1.35–3.04).
- **Inside a longer statement, it moves less.** The same kind of change moves the answer 0.4–1.0 per step, and steps are about 0.6 log-odds whatever their position.
- **Several changes together move about as much as one.** Four dovish changes and two stylistic ones (statement 36) move the answer 1.25–2.36 in total, about as much as the one guidance change.

The model expresses this as step gain *β* 0.43–0.62 together with averaging *η* 0.31–0.64 for all eight configurations. These two parameters were at the recovery threshold and trade off against each other, so only their joint reading is offered: changes are combined sub-additively, and the same way step by step as whole.

This is not necessarily a bias. A Bayesian who takes a statement's changes as correlated signs of one shift in the committee's stance should not add them. The additive model cannot separate that reading from averaging.

**Exploratory: overall responsiveness.** The mean absolute move per statement, against the mean of the other configurations, sequence by sequence:
- **The Astra family moves less:** −0.11 to −0.15 log-odds, above the others in 0–1 of 6 sequences.
- **Sol and Luna move more:** Sol +0.12 and Luna +0.32, each above the others in 6 of 6. Luna's figure is partly noise, since absolute moves grow with noise.
- **The rest are in between:** Sol-low +0.06, Sol-high −0.06, Terra −0.04.

These are small differences (a few points of probability) and not a preregistered test.

**Reading.** These results are conditional on these composite statements and instructions.
- The task leaves the reading of each change to the agent. Even so, all eight configurations supply the same reading and the same way of combining changes:
  - guidance first;
  - wording ignored;
  - changes treated as largely redundant;
  - the result path-independent.
- For these agents, generic central-bank language is a strong situation, as the stated batteries were. CogGym's observation that frontier models agree on most experiments applies here too.
- What the passport could claim, for all eight:
  - these configurations read a statement the same way in steps as whole;
  - they adopt a stated market prior exactly;
  - they ignore content-free rewording;
  - they treat several same-direction changes as little more informative than one.
