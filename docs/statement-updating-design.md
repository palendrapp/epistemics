# Central-bank statements as sequential evidence (design note)

Design, 1 October 2026. Nothing is built or collected. The coherence-set work is parked after its stage A ([results](screen-coherence-design.md#stage-a-results-1-october)).

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

  ℓₜ = ℓₜ₋₁ + *β*·λₑₜ − (1 − *α*)·(ℓₜ₋₁ − ℓ₍₀₎) + noise

where ℓ₍₀₎ = *c* + *γ*·ℓ₀ + noise is the agent's own answer before any change. With *α* = *β* = 1 and *η* = 0, the final stepwise answer equals the whole-statement answer.

| Parameter | What it is | Bayesian value |
| --- | --- | --- |
| Readings λ | How much each kind of change moves the agent: one weight per slot (activity, inflation, risks, forward guidance, vote) and one dovish–hawkish asymmetry | None: this is the agent's model of the committee |
| Prior use *γ* | Weight on the stated market prior | 1 if the agent adopts the market prior |
| Averaging *η* | 0 adds the evidence; 1 averages it, so more changes do not move the answer further, and stylistic changes dilute it (Anderson 1981; Nisbett, Zukier & Lemley 1981) | 0 |
| Step gain *β* | Stepwise steps relative to the agent's own whole-statement reading | 1 |
| Retention *α* | 1 keeps earlier evidence; below 1 it fades, giving recency | 1 |
| Noise *τ* | Report noise on the log-odds scale | — |

**Identification.**
- Readings and prior use come mainly from the whole-statement answers. The changes vary across sequences, and the stated prior is varied (15, 30, 50 and 70%).
- *η* comes from sequences with different numbers of changes (2, 4 and 6).
- *β* and *α* come from comparing the steps with the agent's own whole-statement reading, and from the two orders.

This is the key move: **there is no true λ for natural text, so the agent's own whole-statement answers define its reading, and the stepwise process is measured against them.** Accuracy is never needed. *β* and the readings are separated because both orders and the whole statement share the same λ.

**The parameters describe answers, not internal states.** The readings say how the agent's answers move with each kind of change, under these instructions. They are not a claim about what the agent believes.

**Additivity is an assumption of the model, not of the laws.** Readings that interact (a dovish dissent meaning more when the guidance is also dovish) would show as misfit. The order, path and content laws do not depend on it.

## Design per form

- **Six sequences per form.** Each has a previous statement, a new statement, and its own stated prior.
- **Statements are composites.** They are built from a bank of sentences adapted from real FOMC statements (US government works, so public domain). The committee belongs to an unnamed central bank; dates, rate levels and named events are removed; and a phrase tied to one period is paraphrased. See [Contamination](#contamination).
- **Changes per sequence:** 2, 4 or 6 (two sequences each). Each sequence has at least one stylistic change. About half have conflicting directions.
- **Slots** (changed in the dovish or hawkish direction):
  - economic activity;
  - inflation;
  - risks to the outlook;
  - forward guidance;
  - the vote (a dissent preferring a cut or a rise).
- **Sessions:** three per configuration per form.
  - Each session has two sequences in order A, two in order B and two whole, rotating across the three sessions.
  - The pairing keeps every session at 24 sequence cases, plus 2 anchors, so 26 cases.
  - Each sequence's cases are consecutive, and the anchors sit between sequences.
- **Anchors:** "the probability that the committee changed its policy rate at this meeting", where the statement says it held (0), or that it lowered (1). They check comprehension.
- **Two parallel forms**, `a` and `b`, with different statements, for the retest.
- **Configurations:** the eight of the screen (Astra, Sol, each at low, default and high effort; Luna; Terra).

**The display of a stepwise case** (decision 3): the previous statement, the stated prior, and the newest change only. The earlier changes are in the agent's earlier cases. This makes the final stepwise answer an integration across the agent's own trajectory, where agents are limited, rather than a recomputation from a list on screen. The instructions say plainly that cases in a sequence continue, and that each answer should use every change revealed so far.

## Contamination

The models will know what followed famous statements, so the "update" could be recall.
- **Composites** match no real statement, so there is no outcome to recall.
- **A datability probe** (validation): for each previous statement, the probability that it was issued in each of four periods (before 2005, 2005–2012, 2013–2019, 2020 or later). Any statement that a configuration places in one period with more than 0.6 is rewritten.
- **No market truth** exists for composites. The task measures the laws and the differences between configurations, not accuracy. A benchmark against market reactions would need real statement pairs with published surprise series (Kuttner 2001; Gürkaynak, Sack & Swanson 2005). Those are exposed to recall, so this is left as an optional later stage (decision 2).

## Analysis (to be preregistered before collection)

**Per configuration:** the three laws, each against the noise floor, and the model's parameters by grid posterior. The readings and *γ* enter linearly given (*η*, *β*, *α*, *τ*), so they are integrated analytically on a grid over the other four.

**Stage A hypotheses (form `a`):**
1. **Readings differ.** For at least one slot, configurations' readings spread by at least twice the noise, and at least three configurations depart from the median by *δ* (1/8 of the plausible range), as in the screen's stage A.
2. **Laws.** At least one configuration departs from the order or path law beyond the calibrated noise. If none does, path-independent integration is at ceiling, and that is reported as a finding.
3. **Content.** Whether any configuration moves on stylistic changes beyond noise.

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

- **Stage A:** 8 configurations × 3 sessions = 24 sessions of 26 cases. The cases are longer than the screen's (a full previous statement each), so about 15 million tokens.
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

## Decisions for you

1. **Unit of evidence:** changes to the previous statement (recommended), or the new statement streamed sentence by sentence. Streaming is closer to your first idea, but its order cannot be varied naturally and it has no clean stylistic controls.
2. **Source:** composite statements from a public-domain sentence bank, with an unnamed central bank (recommended). Or edited real statements, or real consecutive pairs with a market benchmark (exposed to recall; an optional later stage).
3. **Stepwise display:** the newest change only (recommended), or the cumulative list of changes. The cumulative list isolates reading from memory but invites recomputation, which makes the laws likely to be at ceiling.
4. **Outcomes:** the probability of a cut at the next meeting only, in stage A (recommended). Later options:
   - cut, hold and raise as a partition, which adds the coherence check;
   - a growth question, which tests the information effect: whether a hawkish change is read as news about the economy (Nakamura & Steinsson 2018);
   - a trade after the final change, which tests stated against revealed belief.
5. **Datability probe:** two configurations (recommended, about 1 million), all eight, or none.
6. **Budget:** about 16 million for stage A with the probe.
