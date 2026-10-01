# Deliberation style: judging against computing (design note)

Design, 1 October 2026. Nothing is built or collected. It follows the [exploration log](exploration-log.md) (ideas 3, 6 and 7).

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

## Decisions for you

1. **Modules:** both ladders and anchors (recommended), or ladders alone first (8 sessions, about 4 million tokens). Ladders alone test the readout reading and leave out adjustment.
2. **Anchor mode:** the comparative paradigm (recommended; strong and classic), or incidental numbers in the case (weaker, and closer to how anchors occur in real documents).
3. **Anchor values:** 30 points either side of the observer's middle answer (recommended), or fixed values (10% and 90%).
4. **Light preregistration:** predictions written down as above and tested descriptively, with confirmation only on a fresh form (recommended), or the full stage A/B machinery.
5. **Budget:** about 13 million.
