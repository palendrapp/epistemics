# Deliberation style: judging against computing (design note)

Design, 1 October 2026; built the same day with the recommended defaults (model 0.21.0, design 0.22.0, tasks 0.32.0; see [Built](#built)). Nothing is collected yet. It follows the [exploration log](exploration-log.md) (ideas 3, 6 and 7).

## Why

**The lead.** Across five collections of open cases, the two GPT-6 variants answer differently at every effort level:
- **Astra** answers open cases mostly in round numbers (62–95% multiples of 5 across the screen and the coherence sets) and writes about half the output per case.
- **Sol** gives fine-grained answers (31–75%).

At the same effort, Astra is rounder than Sol in 13 of 13 comparisons. It is the first consistent difference within GPT-6 after many tasks where they looked alike.

**The reading.** Astra answers open questions by judgement: a coarse, quick impression. Sol computes: it works a number out from some model of the case. The roundness check adds one piece: when Sol does give a round answer, it sits nearer its fitted fallback. So for Sol a round number marks a case it did not compute.

**Why it matters for the passport.** If the reading holds, the two styles fail differently, and each has its own consumer action.
- **A judging agent:** coarse answers that cannot express small differences, and perhaps anchorable. The consumer action is to ask for an explicit calculation, or several nearby quantities.
- **A computing agent:** fine answers built per question, which need not fit together across questions (Sol's five-bin partitions over-summed). The consumer action is to ask the related questions together, or to normalise.

**The test.** This note designs cases where judging and computing predict different behaviour, and measures two parameters with a Bayesian and resource-rational reading:
- **readout grain:** how coarsely an answer is reported;
- **adjustment from an anchor:** how far an answer moves away from a number put in front of it.

## The two parameters

**Readout grain.** An agent's answer to "the probability that the reading exceeds *t*" is its predictive distribution's tail, F(*t*), reported at some grain.
- A computing agent reports F(*t*) to the point.
- A judging agent reports it rounded to 5 or 10, so nearby thresholds share one answer (plateaus).

Rounding of probability answers is well documented in surveys. It can be inferred from the pattern of a respondent's answers (Manski & Molinari 2010), and it rises with the respondent's uncertainty (Ruud, Schunk & Winter 2014).

The model: each answer is F(*t*) rounded to 5 points with probability *ρ* (the judging share), and to 1 point otherwise, plus noise. F comes from the screen's trend observer, with linear weight *w* and noise. So *ρ* is identified separately from the predictive spread.

**Adjustment from an anchor.** In anchoring and adjustment (Tversky & Kahneman 1974), an estimate starts from an anchor and is adjusted, usually insufficiently (Epley & Gilovich 2006). In the resource-rational account (Lieder, Griffiths, Huys & Goodman 2018; Lieder & Griffiths 2020), adjustment is a sequence of costly steps: the fewer the steps, the more the estimate stays near the anchor. Deliberation is the number of steps.

The model, on the log-odds scale:

  anchored answer = (1 − *a*)·(the agent's own unanchored answer) + *a*·(anchor) + noise

- *a* is the anchoring weight, and 1 − *a* the completeness of adjustment.
- The agent's own unanchored answer to the identical question comes from its ladder session (below). So *a* needs no ground truth.
- This is the screen's trust–fallback mixture, (1 − *m*)·*p* + *m*·*d*, with a supplied anchor in place of the agent's own default.

**What the reading predicts:**

| | Judging (Astra?) | Computing (Sol?) |
| --- | --- | --- |
| Readout grain *ρ* | High | Low |
| Plateaus across nearby thresholds | Many | Few |
| Anchoring weight *a* | Higher (fewer adjustment steps) | Lower |
| Effort (low → high) | *a* falls with effort if effort buys adjustment steps | The same |
| Seconds per case on ladder cases | Short | Longer |

The anchoring prediction is the least certain. A computing agent could also be captured by a number put in front of it. Either way, a difference between the variants would be informative.

## The task

Both modules use the screen's trend cases. These are three readings of a growing quantity (a tank level, a ticket queue, archive storage, registered users, processed orders), and a question about a later reading. They are open: linear and exponential continuations disagree, and the agent's answer depends on which it favours. The screen found reliable differences there (linearity, conservatism). The texts and the observer already exist.

**Module L: ladders (readout grain).** Four series, each asked at six nearby thresholds: "What is the probability that it will have more than *t* open tickets after 6 days?", with *t* stepping across the plausible range.
- **Step size.** Steps are chosen so that the observer's answer changes by 4–8 points per step. A 1-point readout then changes every step, and a 5- or 10-point readout often does not.
- **Order.** The six questions about a series are spread at least four cases apart (the coherence sets' `sets` order), so answers are not made by comparing neighbours on screen.
- **Size.** 24 cases.

**Module A: anchors (adjustment).** The same four series and three of each series' thresholds, each asked as a consecutive pair of cases:
1. **The comparison** (a choice): "Consider 85%, a number chosen for this exercise that carries no information about the queue. Is the probability that it will have more than 50 open tickets after 6 days above or below 85%?" The options are "Above 85%" and "Below 85%".
2. **The estimate:** "What is the probability that it will have more than 50 open tickets after 6 days?" It repeats the case and says that the previous case compared it with 85%.

Details:
- This is the classic comparative paradigm (Tversky & Kahneman 1974; Jacowitz & Kahneman 1995), with an honest description of the anchor.
- **Anchor values.** Low anchors are 30 points below the observer's middle answer and high anchors 30 points above, kept within 5–95%.
- **Forms.** Two forms swap low and high, so every threshold is asked with each anchor in a different session.
- **Size.** 12 pairs = 24 cases.

**Sessions per configuration:** one ladder session and two anchor sessions (forms a and b), each a separate session. The configurations are the eight of the screen. The effort levels act as a dose of deliberation within each variant.

## Laws and model-free measures

- **Ladder monotonicity.** P(above *t*) cannot rise with *t*. A violation is incoherence across questions. Sol's five-bin partitions suggest a computing agent may violate it.
- **Plateau index.** The share of adjacent thresholds answered identically, against the share the observer's slope implies at 1-point resolution.
- **Grain.** The share of answers at multiples of 5 and of 10, on ladders and on anchor estimates.
- **The anchoring index** (Jacowitz & Kahneman 1995): (estimate after the high anchor − estimate after the low anchor) / (high anchor − low anchor), per threshold.
- **Choice–estimate consistency.** An estimate of 8% after choosing "above 10%" is inconsistent. This law ties the comparison to the estimate.
- **Seconds per case** (checkpoint to answer) and output tokens per case, per module. They are behavioural measures of deliberation; no agent text is read.

## Analysis

**An exploratory pilot with its predictions written down,** as agreed on 1 October: preregister only for claims.

**Predictions:**
1. **Grain.** Astra's *ρ* is above Sol's at each effort, replicating the exploratory split on new cases.
2. **Plateaus.** Astra has more than Sol, after allowing for each configuration's fitted spread.
3. **Anchoring.** *a* differs between Astra and Sol at matched effort. The reading says Astra's is higher.
4. **Effort.** Within each variant, *a* falls from low to high effort.
5. **Seconds per case.** Sol's exceed Astra's on ladder cases.

**Descriptive:** monotonicity violations, choice–estimate consistency, Luna and Terra, and where Sol's round answers fall on the ladders (idea 6).

**What follows the pilot.**
- If predictions 1–3 show, a confirmatory replication on a fresh form, with its own test, before any passport claim.
- If grain differs but anchoring does not, then style shows in readout only. That narrows the reading: Astra reports coarsely but adjusts as fully as Sol.

## Validation before collection

1. **Recovery.** Simulated agents through the real design:
   - the trend observer's parameters across the plausible ranges;
   - *ρ* 0–1, *a* 0–0.6;
   - report noise 0.1–0.5.

   Criteria: *r* ≥ 0.8 and coverage ≥ 0.8 for *ρ* and *a*, and confusion with the predictive spread ≤ 0.3.
2. **Ladder audit.** The observer's ladder is monotone; the steps change its answer by 4–8 points at the plausible middle; the cases are open by the screen's audit.
3. **Anchor audit.** Every anchor is described as chosen for the exercise and carrying no information; each anchor pair's cases are consecutive; low and high anchors swap between the forms.
4. **The choice response.** The comparison cases use the runner's choice answers (as in battery v3.1). They need a generic option list instead of v3.1's consequence options.
5. **Task validation** on two seeds.

## Cost (provisional)

- 8 configurations × 3 sessions = 24 sessions of 24 cases, about 13 million tokens (the screen's cases are short).
- **To build** (model 0.21.0, design 0.22.0, tasks 0.32.0):
  - the ladder and anchor designs, observer predictions, the fit and simulated agents in `dispositions/deliberation.py`;
  - texts reusing `screen_texts`;
  - generic choice options;
  - `ledger/deliberation.py`.

## Risks

- **Anchors read as informative.** An agent may treat a number put in front of it as a hint. The wording says it carries no information. Consistency between the choice and the estimate, and the anchoring index, show whether it is used.
- **Comparing neighbours.** With six thresholds of one series in a session, an agent may make its ladder smooth by recalling earlier answers. Spreading the questions apart limits this. Recall would produce smoothness, so a plateau is still informative.
- **Ceiling.** Every configuration may compute these cases exactly. Then the variants' style difference does not appear on trend questions, which narrows the reading to the families where it was seen (lists, reported numbers).
- **Effort is not a pure dose.** Effort levels change more than the number of adjustment steps. Prediction 4 is descriptive.

## Decisions (taken 1 October: the recommendations)

1. **Modules:** both ladders and anchors (recommended), or ladders alone first (8 sessions, about 4 million tokens). Ladders alone test the readout reading and leave out adjustment.
2. **Anchor mode:** the comparative paradigm (recommended; strong and classic), or incidental numbers in the case (weaker, and closer to how anchors occur in real documents).
3. **Anchor values:** 30 points either side of the observer's middle answer (recommended), or fixed values (10% and 90%).
4. **Light preregistration:** predictions written down as above and tested descriptively, with confirmation only on a fresh form (recommended), or the full stage A/B machinery.
5. **Budget:** about 13 million.

## Built

Built on 1 October 2026 as model 0.21.0, design 0.22.0, tasks 0.32.0, with the recommended defaults: both modules, comparative anchors 30 points either side of an observer's answer, and light preregistration.

**Code:**
- **Designs, simulated respondents and estimates:** `dispositions/deliberation.py`.
- **Texts:** `disposition_tasks/deliberation_texts.py`, on the screen's trend surfaces.
- **Ledger:** `ledger/deliberation.py`, with the commands `deliberation-validation` and `deliberation-pilot`.
- **Modules:** `deliberation-ladder`, `deliberation-anchor-a` and `deliberation-anchor-b`; variant `deliberation`.
- **Choice cases** use a generic option list (`render.choice_options`); battery v3.1's options are unchanged.
- **Preset `deliberation-pilot`:** 24 runs (the eight configurations × ladder, anchor-a and anchor-b).

**The series.** Four series: a ticket queue at day 6, archive storage at week 5, registered users at month 5, and orders by hour 6. Each grows by about ×1.4 per step, so linear and exponential continuations disagree.

**Deviations from the note above:**
- **Threshold spacing.** The screen's middle observer is bimodal and narrow: almost all its weight sits near the linear and the exponential projections. Its answers barely change between them and then fall steeply. So the thresholds are spaced for a broad observer instead (linear weight 0.55, noise 0.25), whose answer falls 5 points per step (64% to 39%). The middle observer then falls 8–14 points per step, and is monotone too.
- **Anchors** are 30 points either side of the broad observer's answer at ladder ranks 1, 3 and 5: low 29, 19 and 9%, high 89, 79 and 69%. They are the same for every series. In form a, series 1 and 3 start low and series 2 and 4 start high, alternating along the ranks; form b swaps them.
- **The ladder order is cyclic.** A series' six questions are exactly four cases apart (with four series of six, four apart is only possible that way). The rotation is random, and so is the threshold order within a series.
- **Readout grain *ρ*** is estimated from the answers, not from the trend model. It is the share of mid-range answers (0.06–0.94) at multiples of 5, above the 1 in 5 a 1-point readout gives by chance (Beta posterior; after Manski & Molinari 2010). The plateau share is descriptive.
- **Anchoring weight *a*** comes from each threshold's estimates after its high and low anchors, which are in different sessions: (z_high − z_low) / (z_anchor_high − z_anchor_low). The agent's own answer cancels, so no ladder answer or model is needed. The slope against the agent's own ladder answers is reported as a secondary estimate.
- **No comprehension anchors.** Monotonicity of the ladders, and consistency between each comparison and its estimate, serve as the checks.

**Validation** (`output/deliberation-validation-20261001.json`). 300 simulated configurations:
- trend parameters drawn across the screen's plausible ranges;
- *ρ* 0–1, *a* 0–0.6, report noise 0.1–0.5;
- three sessions each.

| Parameter | *r* | 90% coverage |
| --- | --- | --- |
| Readout grain *ρ* | 0.92 | 0.90 |
| Anchoring weight *a* | 0.96 | 0.87 |

- **Confusion** with report noise and with each other is at most 0.17.
- **The secondary estimate of *a*** (against the agent's own ladder answers) recovers at r 0.97, with a mean bias of +0.02.
- All criteria pass.

**Task validation 0.32.** It passed on both seeds: 3,768 cases and 162 contexts.
- One session per module recovered the respondent's grain within 0.07 and its anchoring weight within 0.02, with every comparison consistent with its estimate.
- The audits cover: ladders rising in threshold and falling in both observers' answers; the cyclic order; anchor pairs consecutive; every threshold anchored low in one form and high in the other; and every anchor described as chosen for the exercise and carrying no information.

Hashes:
- Fingerprint `5923831732f8a3514e11373a1d915b0cd58697827b9913615c04bad3b338c83e`.
- Seed 20260927: `f338a5119bc4a969015d18b4be4b3c29b4a84ac172e5539a2f511572b5f9cc1a`.
- Seed 20261027: `d66dc7adb170cbb2c03644eeb4373464e7116936810708d99fd7af0169a12888`.

### Pilot (1 October)

- **Sessions:** preset `deliberation-pilot`, 24 sessions. Cap 16 million tokens (about 13 million expected), 1,800 seconds per run.
- **Analysis:** `uv run python -m epistemics.ledger deliberation-pilot <roots...> --output <file>`. It reports per configuration:
  - *ρ* (all probability answers, and ladders alone);
  - the plateau share and monotonicity violations;
  - *a* with its interval, the Jacowitz–Kahneman index and the secondary estimate;
  - choice–estimate consistency;
  - seconds and output tokens per case.

  It summarises predictions 1–5 across the three effort-matched Astra–Sol pairs.

## Pilot results (1 October)

**Collection.** Root `output/deliberation-pilot-20261001`, tasks 0.32.0.
- 24 of 24 sessions: 11.8 million input tokens (10.9 million cached) and 44,000 output tokens, in 30 minutes.
- No failures.
- Summary: `output/deliberation-pilot-summary-20261001.json`.

**The predictions:**

| Prediction | Result |
| --- | --- |
| P1 grain: Astra's *ρ* above Sol's | **Holds when pooled:** 3 of 3 effort-matched pairs, intervals separate (Astra 0.23–0.40, Sol 0.00–0.03). But it comes from the anchor sessions alone (below) |
| P2 plateaus: Astra's above Sol's | **Fails.** No configuration but Luna (0.20) answered two adjacent thresholds alike |
| P3 anchoring: *a* differs | **Fails: nobody is anchored.** Estimates after the high and the low anchor are equal: *a* −0.03 to 0.05, Jacowitz–Kahneman index −0.01 to 0.05 |
| P4 effort lowers *a* | **Moot,** with no anchoring |
| P5 Sol slower per case | **Fails.** Ladder cases take 2.8–3.6 s for Astra and 2.8–3.1 s for Sol, though Sol writes about twice the output per case (83–108 tokens against 48–50) |

**Checks.**
- The ladders are monotone: one violation in all (Luna).
- Comparisons are consistent with the estimates that follow: 100%, Terra 96%.

**Grain depends on the session for Astra.** Share of mid-range answers at multiples of 5:

| Configuration | Ladder sessions | Anchor sessions |
| --- | --- | --- |
| Astra | 17% | 88% |
| Astra-low | 8% | 67% |
| Astra-high | 8% | 92% |
| Sol | 30% | 8% |
| Sol-low | 14% | 4% |
| Sol-high | 5% | 4% |
| Luna | 91% | 32% |
| Terra | 14% | 30% |

- **Astra** answers the ladders in fine, smooth curves and rounds its estimates after a comparison.
- **Sol** is fine-grained in both.
- **Luna** rounds the ladders and less so the estimates.

**A frame shift (found in the pilot, exploratory).** The anchor sessions' estimates against the agent's own ladder answers at the same thresholds, whatever the anchor. The table gives the change in |log-odds| (negative: less extreme) and the mean estimates.

| Configuration | Change | Ladder | After a low anchor | After a high anchor |
| --- | --- | --- | --- | --- |
| Astra | −0.01 | 0.62 | 0.62 | 0.63 |
| Astra-low | +0.04 | 0.67 | 0.68 | 0.68 |
| Astra-high | −0.19 | 0.70 | 0.66 | 0.66 |
| Sol | −0.26 | 0.72 | 0.68 | 0.68 |
| Sol-low | −0.59 | 0.81 | 0.59 | 0.61 |
| Sol-high | −0.53 | 0.80 | 0.70 | 0.70 |
| Luna | −1.07 | 0.90 | 0.82 | 0.82 |
| Terra | −0.39 | 0.81 | 0.70 | 0.73 |

- When the same threshold is asked after a comparison, Sol, Luna and Terra give more moderate probabilities than on the ladder, by the same amount after a low or a high anchor.
- Astra and Astra-low do not move.
- **The cause is open.** The sessions differ in more than the comparison: three thresholds per series instead of six, and a different order.
- This is also why the secondary anchoring estimate (the slope against the agent's own ladder answers) came out at 0.15–0.39 for Sol, Luna and Terra while *a* was 0. That estimate takes up the shift.

**Reading.** These results are conditional on these cases and instructions.
- **Nobody is anchored.** A number declared to carry no information is ignored by every configuration. The resource-rational anchoring prediction had nothing to work on.
- **Astra's readout depends on the question's frame.** Its answers are fine on a ladder of thresholds, which invites a curve, and round after a comparison. "Astra judges, Sol computes" becomes:
  - Sol always reports computed precision.
  - Astra switches to round reports in some frames.
  - Neither difference shows in time per case or in anchoring.
- **A second Astra–Sol difference.** Sol's probabilities moderate in the comparison frame; Astra's do not move, although their grain does. Each variant responds to the frame, Astra in how it reports and Sol in what it reports.
- **What the passport could claim** (for these cases):
  - no configuration is moved by a number declared uninformative;
  - Astra gives fine-grained answers when asked for a curve, and round ones otherwise;
  - Sol's (and GPT-5.6's) probabilities become more moderate when asked after a comparison.

## Follow-up: which frame does it? (1 October)

**Module `deliberation-bare`** (design 0.23.0, tasks 0.33.0). The twelve anchored thresholds are asked directly, with no comparison: three per series, in random order. Four more series fill the session to 24 cases.

**Collection.** Root `output/deliberation-bare-20261001`: 8 sessions, 3.8 million input tokens, no failures.
- Task validation 0.33 passed on both seeds (3,792 cases, 163 contexts). Fingerprint `1fb7f93a9799a026fd6db73253c63a15bf00f0a7244d2d368ce741fc460444e9`; seeds `d31e856b…` and `31675436…`.
- The comparison: `uv run python -m epistemics.ledger deliberation-followup output/deliberation-pilot-20261001 output/deliberation-bare-20261001 --output output/deliberation-followup-20261001.json`.

**The same twelve thresholds in three frames.** These are single answers per threshold (two after a comparison), so the figures are noisy.

| Configuration | Mean answer (ladder / bare / after a comparison) | Mean \|log-odds\| | Share at multiples of 5 |
| --- | --- | --- | --- |
| Astra | 0.62 / 0.74 / 0.62 | 0.69 / 1.12 / 0.68 | 17% / 33% / 88% |
| Astra-low | 0.67 / 0.78 / 0.68 | 0.79 / 1.34 / 0.83 | 8% / 33% / 67% |
| Astra-high | 0.70 / 0.75 / 0.66 | 0.89 / 1.15 / 0.70 | 8% / 17% / 92% |
| Sol | 0.72 / 0.75 / 0.68 | 1.20 / 1.14 / 0.93 | 25% / 8% / 8% |
| Sol-low | 0.81 / 0.77 / 0.60 | 1.61 / 1.27 / 1.02 | 18% / 25% / 4% |
| Sol-high | 0.80 / 0.69 / 0.70 | 1.61 / 0.87 / 1.08 | 9% / 17% / 4% |
| Luna | 0.90 / 0.84 / 0.82 | 2.74 / 1.77 / 1.67 | 100% / 55% / 32% |
| Terra | 0.81 / 0.86 / 0.72 | 1.57 / 1.98 / 1.17 | 17% / 0% / 30% |

**Reading.**
- **The comparison switches Astra to round answers.** Asked directly, Astra stays mostly fine-grained (17–33%, against 8–17% on ladders). After an above-or-below comparison, 67–92% of its answers are round. Sol is fine-grained in every frame. This is the cleanest result of the deliberation work. Astra's report precision is set by the question's frame, and a binary comparison puts it in a coarse, judgement-like mode.
- **The frame shift in extremity is not one effect:**
  - **Sol and Terra:** the comparison moderates their answers; the bare answers are as extreme as on the ladder, or more.
  - **Luna and Sol-high:** the six-threshold ladder is the extreme frame; bare and after-comparison answers are alike.
  - **The Astra family:** a lone direct question gives the most extreme answers; the ladder and the comparison give the same, more moderate ones.

  Every configuration's extremity responds to the frame, in a configuration-specific way that twelve single answers cannot pin down.
- **For the passport** (for these cases):
  - Astra reports round probabilities after a comparison and fine ones otherwise;
  - Sol reports fine probabilities in every frame;
  - how extreme an answer is depends on the frame for every configuration, in ways not yet characterised.

## Second follow-up: what else switches Astra? (1 October)

**Modules `deliberation-frames-a` and `-b`** (design 0.24.0, tasks 0.34.0). Each session has twelve pairs: a first question about a series, then the probability for one threshold. There are four kinds of first question, three pairs each:
- **comparison:** as in the pilot ("above or below 29%?"), with the estimate case restating the anchor;
- **comparison, plain:** the same comparison, with the estimate case saying only that the previous case asked about the same readings;
- **verbal:** "is it likely or unlikely that…?";
- **model:** "does it grow by about the same amount each step, or by a growing amount?"

The two forms rotate the kinds over the thresholds.

**Collection.** The six GPT-6 configurations took both forms: root `output/deliberation-frames-20261001`, 12 sessions, 6.1 million input tokens, no failures.
- Task validation 0.34 passed on both seeds (3,840 cases, 165 contexts). Fingerprint `954461748d9fe24718ca4e8ed2370a024f122d6b439e2ff5e2b1bde6aae7c35d`; seeds `4a0bf133…` and `500f9b71…`.
- The comparison: `uv run python -m epistemics.ledger deliberation-frames output/deliberation-frames-20261001 --baseline output/deliberation-pilot-20261001 output/deliberation-bare-20261001 --output output/deliberation-frames-summary-20261001.json`.

**Share of mid-range estimates at multiples of 5** (the same twelve thresholds; mid-range answers in brackets):

| | Ladder | Asked directly | After a comparison | After a comparison, plain | After "likely or unlikely" | After the model question |
| --- | --- | --- | --- | --- | --- | --- |
| Astra | 17% (12) | 33% (12) | 100% (6) | 83% (6) | 83% (6) | 67% (6) |
| Astra-low | 8% (12) | 33% (12) | 83% (6) | 83% (6) | 83% (6) | 100% (6) |
| Astra-high | 8% (12) | 17% (12) | 33% (6) | 50% (6) | 50% (6) | 33% (6) |
| Sol | 25% (12) | 8% (12) | 0% (6) | 0% (6) | 0% (6) | 0% (6) |
| Sol-low | 18% (11) | 25% (12) | 17% (6) | 50% (6) | 17% (6) | 33% (6) |
| Sol-high | 9% (11) | 17% (12) | 17% (6) | 33% (6) | 17% (6) | 17% (6) |
| **Astra, pooled** | 11% (36) | 28% (36) | 72% (18) | 72% (18) | 72% (18) | 67% (18) |
| **Sol, pooled** | 18% (34) | 17% (36) | 11% (18) | 28% (18) | 11% (18) | 17% (18) |

**Reading.**
- **Any preceding question about the same case switches Astra to round answers.** The rate is the same after a numerical comparison, a verbal judgement and a question about the growth model (67–72% pooled), against 28% asked directly and 11% on the ladder.
- **It is not the comparison, the anchor or judgement framing.** It is being asked for the probability as a follow-up.
- **Astra-high is the least affected** (33–50%).
- **Sol stays fine-grained in every frame.**
- **What this does not separate.** Every estimate in these sessions followed a first question, and the direct baseline comes from other sessions. So a follow-up within a pair cannot be told apart from a session made of pairs.
- **Extremity.** It does not move consistently with the frame for Astra. Sol-low's answers are more moderate after any first question (|log-odds| 0.57–0.94, against 1.61 on the ladder and 1.27 asked directly).
- **For the passport** (for these cases): Astra reports round probabilities when asked as a follow-up to another question about the same case, and fine ones when asked fresh or for a curve; Sol's precision does not depend on the frame. The consumer action, for Astra in a multi-step exchange: ask for a probability fresh, or as part of a set of thresholds, when precision matters.

## Are Astra's follow-ups worse? (1 October)

Command: `uv run python -m epistemics.ledger deliberation-quality output/deliberation-pilot-20261001 output/deliberation-bare-20261001 output/deliberation-frames-20261001 --output output/deliberation-quality-20261001.json`.

**Measures.** There is no ground truth, so each configuration is judged against its own answers on the twelve anchored thresholds:
- **follow-up answers:** the estimates after a first question (the pilot's anchor sessions and both frame sessions; 48 per GPT-6 configuration, 24 for Luna and Terra);
- **fresh answers:** the same thresholds asked directly (12), and on the ladder.

| Configuration | Distance from own ladder: direct / follow-up / rounding alone | Fall from rank 1 to rank 5: ladder / direct / follow-up | Follow-up retest |
| --- | --- | --- | --- |
| Astra | 0.60 / 0.22 / 0.08 | 1.57 / 1.27 / 1.45 | 0.26 |
| Astra-low | 0.56 / 0.32 / 0.06 | 1.36 / 1.05 / 1.35 | 0.38 |
| Astra-high | 0.35 / 0.22 / 0.08 | 1.20 / 1.07 / 1.19 | 0.33 |
| Sol | 0.41 / 0.53 / 0.08 | 1.66 / 1.01 / 1.30 | 0.49 |
| Sol-low | 0.52 / 1.19 / 0.11 | 1.62 / 1.17 / 2.21 | 0.62 |
| Sol-high | 0.76 / 0.69 / 0.11 | 1.40 / 1.29 / 1.61 | 0.57 |
| Luna | 1.07 / 1.10 / 0.06 | 2.54 / 1.26 / 1.37 | 0.62 |
| Terra | 0.56 / 0.63 / 0.13 | 1.54 / 1.29 / 1.50 | 0.71 |

How to read the table:
- **Distance:** mean |log-odds| from the configuration's own ladder answer at the same threshold. "Rounding alone" is the distance that rounding the ladder answer to 5 points would cause.
- **Fall:** within a session, the drop in log-odds from a series' lowest anchored threshold to its highest; flatter is less discriminating.
- **Retest:** mean |log-odds| between two follow-up answers to one threshold, which come from different sessions and different first questions.
- **Monotonicity:** violations within a session are 0 everywhere, except Luna's direct answers (25%) and Terra's follow-ups (6%).

**Reading** (on these measures, against each configuration's own answers):
- **Astra's rounded follow-ups are not worse.**
  - They sit nearer its own ladder curve (0.22–0.32) than its fresh direct answers do (0.35–0.60). That is beyond what rounding alone would cause (0.06–0.08), but less than a fresh answer moves.
  - They discriminate between thresholds as much as the ladder does, and have no monotonicity violations.
  - They repeat better than any other configuration's (0.26–0.38).
  - The switch to round numbers is a change of readout with no visible cost to content.
- **Sol's follow-ups move further from its own curve** than its fresh answers do (Sol 0.53 against 0.41; Sol-low 1.19 against 0.52) and repeat less well (0.49–0.62). This is the same frame sensitivity in what Sol reports that the pilot found.
- **Caveats.**
  - The ladder is itself a frame, not a truth.
  - The direct answers are twelve single answers from one session.
  - The follow-up retest mixes first questions.
