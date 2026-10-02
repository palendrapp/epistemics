# Exploration log

Post hoc exploration of data already collected, to find ideas worth an experiment. Nothing here is a test or a claim.

- **Rules.** Behaviour only: answers, timing, tool calls and token counts, never agent text. Every table comes from a ledger command.
- **What becomes of an idea.** If one looks promising, it becomes a design with its own preregistered test.
- **Status.** Entries are dated, and each ends with the ideas it suggests.

## 1 October: statements stage A, post hoc

Command: `uv run python -m epistemics.ledger statements-explore output/statements-stage-a-20261001 --output output/statements-explore-20261001.json`.

**Scope.** One form, six statements, eight configurations. Each announced count is a single statement, so count and content are partly confounded.

**The announced number of changes sets the weight of each change.** Each case says up front how many places the new statement differs in. The mean step on a substantive change, in log-odds, signed so that a step in the change's direction is positive:

| Changes announced | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| Every substantive step | 1.93 | 0.88 | 0.70 | 0.57 | 0.63 | 0.49 |
| The first substantive step only | 1.93 | 0.88 | 0.75 | 0.54 | 0.58 | 0.51 |

- **The first step of a long statement is already small,** before any other change is seen. So this is not redundancy among the changes revealed so far.
- **Within one slot:**
  - a guidance change moves the answer 1.93 when it is the only change, 0.70 among four and 0.60 among six;
  - inflation moves 0.88, 0.79 and 0.49 among two, five and six;
  - risks 0.66, 0.66 and 0.36 among four, five and six.
- **A simple rule fits.** Step = constant + *b*/*n* (with a term for the starting probability) fits each GPT-6 configuration and Terra with R² 0.78–0.87 and *b* 1.24–1.79. Luna fits less well (R² 0.56, *b* 1.95).
- **Neither Bayesian account predicts it.** If the changes were independent, the first step would not depend on *n*. If they were positively correlated (one stance behind them), the first step should grow with *n*, since more changes in the same direction are expected.
- **Two readings fit.**
  - *A fixed budget:* a statement carries a set amount of news, shared across the announced changes.
  - *A pragmatic one:* if the committee changed one sentence, that sentence is the message; among six edits, each is minor.
- It echoes the coherence sets, where Terra, Sol-low and Luna gave each of the *n* listed causes exactly 1/*n*.

**Configurations are nearly interchangeable.** The GPT-6 configurations and Terra, compared pairwise on identical cases:
- 36–52% of answers are identical to the percentage point;
- the mean gap is 0.09–0.17 log-odds.

Prior cases, a quarter of the answers, repeat the stated prior for everyone. Luna departs most: 35–39% identical, gaps 0.20–0.30.

**Other observations:**
- No session called the history tool. Agents integrated from what was already in their context.
- Stylistic changes took as long to answer as substantive ones.
- Once *n* is in the model, steps are better described in log-odds than in probability points.
- There is no consistent hawkish–dovish asymmetry at a given *n*.

**Ideas:**
1. **Vary the announced count.** Use the same changes with the count announced as 1 or 6, or not announced at all, and the answer after the first change only. This separates the budget from content, and the budget from the pragmatic reading. The pragmatic reading is a model of the speaker, where configurations might differ.
2. **A redundancy manipulation.** Show the same changes from one statement or from independent sources (statement, minutes, speech). A Bayesian should add independent signals but not redundant ones.

## 1 October: sweep across every collection

Command: `uv run python -m epistemics.ledger sweep --output output/sweep-20261001.json`.

**Coverage.** 44 battery collections: 755 verified sessions and 17,728 probability answers.

**Signatures** (defined in `ledger/sweep.py`):
- **grain:** share of answers at multiples of 5 points;
- **extremity:** mean |log-odds|;
- **boldness:** extremity beyond the other configurations' median on the same case;
- **departure:** distance from the others' median;
- **modal:** share of answers equal to the others' most common answer;
- **latency:** median seconds per case;
- **output:** output tokens per case;
- **retest:** the gap between repeated runs.

**Stability across collections.** Spearman correlation of the configurations' ordering, between every pair of collections that share at least four configurations. Mean rank: 0 is the lowest configuration in a collection, 1 the highest.

| Signature | Collection pairs | Mean ρ | Share positive | Highest | Lowest |
| --- | --- | --- | --- | --- | --- |
| Output per case | 160 | 0.81 | 1.00 | Sol-high, Luna, Sol | Astra-low, Astra |
| Departure | 146 | 0.39 | 0.80 | Luna (0.97), Terra | Astra-low, Sol-low |
| Boldness | 146 | 0.30 | 0.71 | Luna (0.87), Terra | Astra-high |
| Latency | 168 | 0.26 | 0.68 | Sol-high, Sol | Terra |
| Grain | 168 | 0.24 | 0.66 | Luna (0.87) | Astra |
| Modal | 146 | 0.21 | 0.65 | Sol-low | Luna (0.15) |
| Extremity | 168 | 0.11 | 0.57 | Luna | Astra-high |

Retest is left out: only four collections have repeated runs.

**What the table shows:**
- Output per case is a property of the configuration's effort, as expected.
- Departure and boldness separate the families:
  - GPT-5.6 (Luna, then Terra) answers further from the others, and more extremely, in most collections.
  - The consensus is mostly GPT-6, so this partly restates that the families differ.

**Within GPT-6: Astra rounds, Sol does not, on open cases.** Grain on open cases (screen, coherence-set and statement cases whose answer depends on an unstated model):

| Collection | Astra | Astra-low | Astra-high | Sol | Sol-low | Sol-high | Luna | Terra |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Coherence sets, stage A | 84% | 86% | 82% | 75% | 48% | 64% | 86% | 64% |
| Screen, fallback round | 62% | 81% | 88% | 56% | 31% | 43% | 94% | 88% |
| Screen, stage A | 95% | 91% | — | 72% | 52% | — | 96% | 78% |
| Screen, stage B | 95% | 86% | — | 75% | 34% | — | 94% | 51% |
| Statements, stage A | 35% | 46% | 42% | 23% | 21% | 38% | 98% | 60% |

- **Astra is rounder than Sol at the same effort in 13 of 13 comparisons.** Astra and Sol are two GPT-6 variants, `gpt-6-astra` and `gpt-6-sol`.
- **Sol also writes about twice the output per case.** Medians over collections: Sol 111, Sol-low 87 and Sol-high 138 output tokens per case, against Astra 53, Astra-low 50 and Astra-high 64.
- One reading: Astra answers open questions as round judgements, and Sol works numbers out.

**Is roundness a marker of judgement?** Grain on open against determinate cases (anchors, fixed and computable cases) in the same sessions:
- **Yes for Astra and Luna:** open cases are rounder, for example 95% against 70% for Astra in screen stage A.
- **No for Sol-low, and often Sol:** open cases are *less* round, for example 34% against 75% for Sol-low in screen stage B.
- **Mixed for Terra.**

So roundness marks judgement for some configurations only. The style difference itself is the more stable finding.

**Ideas:**
3. **Deliberation style as a trait.** Astra appears to answer by judgement (round, short, fast) and Sol by computation (fine-grained, long). Two consequences to test:
   - **Coherence.** Does computing each question separately produce the partition incoherence seen in Sol and Sol-low (the F5 five-bin over-sums, and Sol-low's incoherence in all three families of the coherence sets)?
   - **Robustness.** Does computing make answers more sensitive to irrelevant numbers in a case (anchoring)?
4. **Roundness as an uncertainty report.** For Astra and Luna, the share of round answers could index where an agent stops computing. Calibrate it against the screen's fallback weight *m*, using the existing data.
5. **GPT-5.6 boldness.** Its stability across tasks (departure ρ 0.39, boldness 0.30) makes it a candidate general trait. In which tasks does it reverse?

## 1 October: is a round answer a report of uncertainty? (idea 4)

Command: `uv run python -m epistemics.ledger roundness --output output/roundness-20261001.json`.

**Data.** The open-inference screen's F2, F4 and F5 sessions: stage A, stage B and the fallback round. That is 72 sessions on forms a, b and c, all on the current designs.

**Three checks:**
- **(A)** roundness by how open the case is;
- **(B)** whether round answers sit nearer the fitted fallback than the observer's answer;
- **(C)** roundness against the fitted fallback weight *m*.

The fits are the fallback round's revised-observer profiles (forms a and b).

**A confound.** Near-certain answers (0.01–0.04, 0.96–0.99) are mostly not multiples of 5. Fixed cases and fine-grained answers are often near-certain, so roundness is confounded with extremity. (A) and (B) are therefore shown on mid-range answers (0.06–0.94).

**(A) Share of round answers by case, mid-range answers only.** The open cases are split into thirds by the screen's openness audit.

| Configuration | Fixed | Open, least | Open, middle | Open, most |
| --- | --- | --- | --- | --- |
| Astra | 82% | 94% | 95% | 95% |
| Astra-low | 79% | 82% | 88% | 82% |
| Astra-high | 67% | 88% | 86% | 93% |
| Sol | 71% | 83% | 91% | 80% |
| Sol-low | 53% | 33% | 47% | 53% |
| Sol-high | 62% | 47% | 46% | 35% |
| Luna | 82% | 85% | 83% | 95% |
| Terra | 85% | 67% | 63% | 71% |

- **Within open cases, roundness does not rise with openness** for any configuration.
- **Open against fixed cases depends on the configuration:**
  - rounder on open cases: the Astra family and Sol;
  - less round on open cases: Sol-low, Sol-high and Terra.

**(B) Fallback-likeness of open answers, mid-range only.** |z − z_observer| − |z − z_fallback| in log-odds, where higher means nearer the configuration's fitted fallback than the observer's answer.

| Configuration | Round answers | Other answers |
| --- | --- | --- |
| Sol | −0.72 (90) | −1.71 (12) |
| Sol-low | −0.68 (48) | −1.82 (59) |
| Sol-high | −0.68 (46) | −1.00 (66) |
| Astra-low | −0.95 (96) | −1.39 (18) |
| Astra-high | −0.74 (109) | −1.29 (9) |
| Terra | −1.06 (70) | −0.75 (38) |
| Luna | −1.89 (62) | −0.96 (9) |

Astra is left out: it gave only 2 mid-range answers that were not round.

- **In the Sol family, a round answer marks a case it did not compute.** Its round answers sit 0.3–1.1 log-odds nearer the fallback than its fine-grained answers. The samples are good for Sol-low and Sol-high.
- **Terra and Luna show the reverse.**
- **In the Astra family**, almost every open answer is round, so roundness carries little information.

**(C) Against the fitted trust *m*.** This is uninformative. Within F2 and F4 the fitted trust barely varies across configurations (0.10 for all eight in F2; 0.02–0.09 in F4). The rank correlations (−0.41 overall) mostly reflect that lack of spread.

**Reading.**
- Roundness is not a general uncertainty report: it does not track openness, and it means different things in different configurations.
- It is informative where a configuration usually computes. For the Sol family, a round answer flags a case where it fell back on a default instead of working the number out.
- That supports the deliberation-style reading (idea 3) more than idea 4.

**Ideas:**
6. **A per-answer marker of defaulting, for Sol.** Use round answers to locate Sol's defaults in other data. For example, were Sol's over-summing five-bin partitions (the coherence sets, F5) built from round, defaulted inner bins or from computed ones? That can be checked on existing data.
7. **Check the deliberation-style reading by design.** Use cases where computing and judging give different answers, for example a case with an irrelevant but computable number. Does Sol compute with it where Astra ignores it?

## 1 October: deliberation pilot, what it adds

See the [pilot results](deliberation-style-design.md#pilot-results-1-october).

- **Declared-uninformative anchors are ignored** by every configuration (*a* ≈ 0).
- **Astra's rounding is frame-dependent:** 8–17% on ladders, 67–92% after comparisons. Sol is fine-grained in both.
- **The frame shift is new:** Sol, Luna and Terra give more moderate probabilities after a comparison than on a ladder, whatever the anchor. Astra does not.

**Ideas:**
8. **Isolate the frame shift.** Ask the same thresholds three per series, with and without a preceding comparison, and on six-step ladders with and without comparisons. Is it the comparison, the number of thresholds per series, or the order?
9. **Undeclared anchors.** Numbers in a case that are not said to be uninformative, as they occur in real documents (an unrelated percentage in a report), described honestly as part of the case. Declared anchors are at ceiling; undeclared ones are the realistic risk.
10. **What triggers Astra's rounding?** The same estimate cases with and without the comparison before them, and single thresholds against ladders. If a comparison frame alone switches Astra to round answers, that is a precise, testable account of its readout mode.

## 1 October: deliberation follow-up

See [the follow-up](deliberation-style-design.md#follow-up-which-frame-does-it-1-october).

- **Idea 10 is answered.** A preceding above-or-below comparison switches Astra to round answers (67–92%, against 17–33% asked directly). Sol never rounds.
- **Idea 8 is answered only in part.** The moderation after a comparison holds for Sol and Terra. For Luna and Sol-high the six-threshold ladder is the extreme frame. For Astra a lone direct question is.

**Ideas:**
11. **Astra's readout mode as a switch.** What else switches it, beyond a binary comparison? For example, a verbal estimate first ("likely or unlikely?"), or a range question. A switch between computed and judged reports, set by the frame, is a candidate trait of how a configuration reads a question.
12. **Extremity by frame, with enough answers.** Several answers per threshold and frame, to characterise each configuration's frame sensitivity, if it seems worth it. On present evidence it is configuration-specific and noisy.

## 1 October: what switches Astra's readout

See [the second follow-up](deliberation-style-design.md#second-follow-up-what-else-switches-astra-1-october).

- Any preceding question about the same case switches Astra to round answers: a comparison, "likely or unlikely", or a question about the growth model (67–72% pooled, against 28% asked directly and 11% on ladders). Astra-high is the least affected. Sol never rounds.
- The trigger is being asked as a follow-up, not the content of the first question.

**Ideas:**
13. **Follow-up within a pair, or a session made of pairs?** Mix paired and fresh estimates in one session.
14. **Does a follow-up change only the readout, or also the reasoning?** Astra's rounded follow-up answers might be cheaper second looks. Compare them with the same configuration's fresh answers threshold by threshold, and check whether a follow-up's error relative to the ladder curve grows.
15. **Multi-turn use.** If round follow-up answers are a general Astra trait, it matters for agents in conversations: the second probability in an exchange is coarser. Test it on other families (screen F2 and F4) as fresh against follow-up questions.

## 1 October: are Astra's follow-ups worse? (idea 14)

See [the analysis](deliberation-style-design.md#are-astras-follow-ups-worse-1-october).

**No.** Judged against Astra's own ladder curves:
- its round follow-up answers are closer to the curve than its fresh direct answers;
- they discriminate between thresholds as well as the ladder;
- they have no monotonicity violations;
- they repeat better than any other configuration's.

The switch is a change of readout, not of content. Sol's follow-ups instead move away from its own curve and repeat less well.

**Ideas:**
16. **Two styles of frame sensitivity.** Astra changes how it reports (precision) and keeps what it reports; Sol keeps its precision and changes what it reports. A frame-sensitivity profile with two axes, readout and content, is a candidate passport entry for both variants.
17. **Why are Astra's fresh direct answers the outliers?** A lone question gave Astra its most extreme answers, further from its ladder than its follow-ups. Is a cold, single question Astra's least considered answer?

## 1 October: follow-up rounding on the peer-advice cases (ideas 13 and 15)

See [the results](deliberation-style-design.md#follow-up-rounding-on-another-family-1-october).

- **Computed answers are exempt.** On the stated peer-advice cases every configuration gives the exact answer fresh or as a follow-up.
- **On open cases Astra's follow-ups are rounder** (25% → 42% pooled), much less than on the trend cases (28% → 72%). Sol's are not.
- **The family and the session mix are confounded.** These sessions mixed fresh and follow-up cases; the trend sessions were all follow-ups.

**Ideas:**
18. **Session against pair, on one family.** Trend cases in mixed sessions (fresh and follow-up interleaved). If Astra's follow-ups fall from 72% towards 42%, the session sets the mode; if they stay at 72%, the family does.
19. **Stop here?** The effect is real for Astra on open trend cases but modest elsewhere, and it never costs accuracy (follow-ups are not worse; computed answers are exact). As a passport claim it may matter less than the readout and content split itself.

## 2 October: announced count, tested (idea 1)

See [the experiment](statement-updating-design.md#announced-count-2-october).

**The exploratory finding largely dissolves under control.** With the content held fixed:
- a single change moves 0.6–0.9 log-odds;
- the same change among three or six moves about 20% less (none less for Terra).

Stage A's 1.93 for its one-change statement came from that statement's change: neutral guidance became a further rise, the strongest signal against a cut.

**What remains is pragmatic, not a budget.** For Astra and Sol, disclosing that the other changes are rewordings restores the full step.

**Lesson for exploration.** A regularity across six statements, each with its own count, was mostly the statements' content. Factors confounded one-for-one with items need a controlled test before they are believed, as the entry's caveat said.

**Ideas:**
20. **Guidance as its own reading.** Guidance changes carry the most weight in every configuration. "Which kind of central-bank language moves it most" is a passport reading, but it may be a shared reading rather than a trait.
21. **Expected correlation among changes.** A change counts for less when other substantive changes may come. Do agents treat a statement's changes as correlated? That could be tested by revealing a second change that agrees or disagrees with the first.

## 2 October: are changes treated as correlated? (idea 21)

See [the experiment](statement-updating-design.md#correlated-changes-2-october).

- **No.** Two revealed changes add as independent evidence for Astra (*a* = 1.04, *b* = 0.01) and nearly so for Sol (0.85, −0.05).
- **Luna** shows a hint of correlation (*b* = −0.16, interval including 0).
- **Terra** discounts the second change by a third whichever way it points (primacy), so its final answers depend on order.
- **Correction.** Together with the announced-count result, this overturns stage A's "strong sub-additivity". That reading compared one strong change with different changes; with content controlled, revealed changes add.

**Ideas:**
22. **Terra's primacy as a trait.** A second change counts two-thirds whichever way it points, and Terra's final answers depend on order. Is that general across sequences (screen, coherence, statements)? The stage A order gaps (Luna 0.42 and Terra 0.29, against GPT-6's 0.10–0.20) point the same way.
23. **What the statement family now offers the passport:**
    - a reading order shared by every configuration (guidance moves most);
    - additivity for Astra;
    - primacy for Terra;
    - a modest, pragmatic count discount.

## 2 October: is Terra's primacy general? (idea 22)

Command: `uv run python -m epistemics.ledger primacy --statements output/statements-stage-a-20261001 --correlated output/correlated-changes-20261002 output/correlated-changes-20261002-topup --output output/primacy-20261002.json`.

**Measure.** The same change's |step| when it comes later against when it comes first.
- In statements stage A, a sequence's first change in one order is its last in the other.
- In the correlated changes, every change comes once first and once second.
- A ratio below 1 is primacy. Stylistic changes are left out.

| Configuration | Statements stage A: last / first (changes) | Correlated changes: second / first (changes) |
| --- | --- | --- |
| Astra | 0.91 [0.83, 0.99] (7) | 1.03 [0.97, 1.10] (48) |
| Astra-low | 0.88 [0.73, 1.02] (7) | — |
| Astra-high | 1.10 [0.94, 1.24] (7) | — |
| Sol | 0.97 [0.88, 1.07] (7) | 0.98 [0.88, 1.08] (48) |
| Sol-low | 0.94 [0.78, 1.10] (7) | — |
| Sol-high | 0.87 [0.73, 1.04] (7) | — |
| Luna | 1.11 [0.93, 1.32] (7) | 0.99 [0.82, 1.21] (48) |
| **Terra** | **0.79 [0.64, 0.97] (7)** | **0.78 [0.68, 0.88] (48)** |

**Reading.**
- **Terra's primacy replicates across the two designs.** In separate sessions, with multi-change sequences in one and two-change statements in the other, a change counts about 20% less when it comes later, and both intervals exclude 1.
- **No other configuration shows a consistent position effect.** Luna's stage A recency (an index of +0.33) does not recur.
- **The limit.** Both datasets are central-bank statements, so "general" here means general across two designs within one family.

**Ideas:**
24. **Terra's primacy beyond statements.** Sequences in another family: readings of a series revealed one at a time (the screen's trend cases), or two analysts' calls in turn (the peer-advice cases), in both orders. If Terra discounts later evidence there too, primacy is a candidate trait for the passport ("weighs what it hears first more"), with a consumer action: put the most important evidence first, or present evidence all at once.

## 2 October: primacy beyond statements (idea 24)

**Modules `calls-a` to `-d`** (design 0.28.0, tasks 0.38.0). An urn with a stated prior and two analysts' calls, each phrased in one of three ways and given without a record, so the agent judges what a call is worth.
- A pair of consecutive cases reports one call, then both.
- The calls agree in twelve items and disagree in twelve.
- Every item appears in both orders.

The design mirrors the correlated changes, so the same analyses apply.

**Collection.** Astra, Sol, Luna and Terra at default effort took all four forms: root `output/calls-order-20261002`, 16 sessions, 7.7 million input tokens, no failures.
- Task validation 0.38 passed on both seeds (4,224 cases, 181 contexts). Fingerprint `b5ffef158c18cdf2938d72270007e564b0f335ca66ca94393a55e6a4cf4883af`; seeds `fee45fb4…` and `7da48c46…`.
- Commands:
  - `uv run python -m epistemics.ledger correlated-changes output/calls-order-20261002 --key calls --output output/calls-order-summary-20261002.json`;
  - `uv run python -m epistemics.ledger primacy … --calls output/calls-order-20261002 --output output/primacy-20261002.json`.

**Results:**

| Configuration | Calls: *a* | Calls: *b* | Calls: order gap | Later / first: statements stage A | Later / first: correlated changes | Later / first: calls |
| --- | --- | --- | --- | --- | --- | --- |
| Astra | 0.88 [0.78, 0.99] | −0.00 | 0.37 | 0.91 [0.83, 0.99] | 1.03 [0.97, 1.10] | 0.96 [0.85, 1.07] |
| Sol | 1.01 [0.98, 1.05] | −0.00 | 0.11 | 0.97 [0.88, 1.07] | 0.98 [0.88, 1.08] | 1.02 [0.99, 1.05] |
| Luna | 0.68 [0.50, 0.86] | +0.02 | 0.72 | 1.11 [0.93, 1.32] | 0.99 [0.82, 1.21] | 1.02 [0.79, 1.33] |
| Terra | 0.85 [0.76, 0.97] | −0.03 | 0.55 | 0.79 [0.64, 0.97] | 0.78 [0.68, 0.88] | 0.95 [0.86, 1.06] |

*a* is the second step on the call's own first-position step; *b* is the second step on the other call's.

**Reading.**
- **Terra's primacy does not clearly carry over to the calls.** A later call counts 0.95 of a first one (interval including 1), against 0.78–0.79 for statement changes. The regression's partial *a* (0.85) suggests at most a mild discount.
- **So far, Terra's primacy is a property of how it reads statements,** not a general trait.
- **Two calls are independent evidence for everyone** (*b* ≈ 0), as statement changes were.
- **Sol adds them exactly** (*a* = 1.01, order gap 0.11).
- **Luna's measures disagree:** *a* = 0.68 in the regression but 1.02 in the ratio of means, with large noise (order gap 0.72). Its later call is not reliably discounted.
- **Terra's steps on calls are about twice the others'** (1.3–1.4 log-odds for a single call, against about 0.7). It takes an analyst's call at more face value.

**Ideas:**
25. **Stop the primacy line?** It does not generalise on present evidence.
26. **What the order work leaves for the passport:**
    - every configuration treats separate pieces of evidence as independent (no averaging, no correlation);
    - Sol adds them most exactly;
    - Terra discounts later statement changes;
    - Terra reacts about twice as strongly to an analyst's call. That last one, a strong reaction to unverified calls, may be worth a look across the peer-advice data already collected.

## 2 October: Terra's reaction to analysts' calls (idea 26)

Command: `uv run python -m epistemics.ledger call-reaction --advice output/multi-agent-pilot-20260930 output/multi-agent-open-20260930 output/confidence-transfer-20260930 output/confidence-transfer-20260930-2 --calls output/calls-order-20261002 --output output/call-reaction-20261002.json`.

**Measure.** A call's weight is the answer's log-odds minus the stated prior's, signed by the call's direction. Only cases without the agent's own reading are used, so the call is the only evidence.

**Mean weight by source:**

| Source | Astra | Sol | Luna | Terra |
| --- | --- | --- | --- | --- |
| Analyst, record stated (multi-agent pilot) | 1.44 | 1.44 | 1.44 | 1.44 |
| Analyst, no record (multi-agent open) | 0.69 | 0.88 | 0.45 | **1.39** |
| Analyst, no record (calls in order) | 0.74 | 0.76 | 0.67 | **1.34** |
| AI agent, no record (confidence transfer) | 0.99 | 0.88 | 0.62 | 0.78 |
| Relay, no record | 0.85 | 0.61 | 0.00 | 0.85 |
| Sensor, no record | 1.23 | 0.93 | 1.22 | 0.00 |

**The weight of a "definitely… confirmed" call:**

| Source | Astra | Sol | Luna | Terra |
| --- | --- | --- | --- | --- |
| Analyst, no record (multi-agent open) | 0.69 | 1.39 | 0.74 | **2.45** |
| Analyst, no record (calls in order) | 0.95 | 1.23 | 1.41 | **2.60** |
| AI agent, no record | 1.73 | 1.39 | 1.12 | 1.47 |
| Sensor, no record | 2.19 | 1.73 | 2.27 | 0.00 |

**Reading.**
- **With records stated, every configuration gives a call exactly the weight its record implies** (ratio 1.00 for all four).
- **Without a record, Terra takes an analyst's confident wording at face value.**
  - A "definitely… confirmed" call moves it about 2.5 log-odds, from 50% to about 92%.
  - That is roughly twice the other configurations, in two independent collections nine days apart.
  - Plain calls are also weighted more (1.06–1.25, against 0.39–0.85). "I think…" calls are not.
- **It is specific to human analysts' wording.** The same confidence from an AI agent gets an ordinary weight, and from a sensor no weight at all.
- **Two more idiosyncrasies, without records:**
  - Terra gives a sensor's call no weight;
  - Luna gives a relayed call none.
- **For the passport** (for these cases): "Without a track record, it takes an analyst's confident wording at face value: a 'definitely… confirmed' call moves it about twice as far as other configurations. With the record given, it weighs calls exactly." The consumer action is to give track records, or to discount confident wording yourself.

**Ideas:**
27. **Write it into the passport as a reading.** It has replicated across two collections.
28. **Confident wording as a trait across families.** Does Terra take confident language at face value elsewhere, for example confidently worded documents or reports?

## 2 October: analysts' calls in the passport (idea 27)

Reading guide 0.6.0 adds a reading under "How it weighs evidence": how far an analyst's confident call moves the configuration without a record.

**Inputs.** The build pools the two analyst collections without a record: multi-agent open and calls in order. It compares each configuration's "definitely… confirmed" weight with the median of the other configurations, using the median so that Terra does not inflate the comparison for the rest.

**Rules.**
- **Face value:** the confident call moves the answer at least 1.5 times as far as the others' median.
- **Wording barely matters:** a confident call moves it less than 0.3 log-odds further than an "I think…" call.
- **Like the others:** neither.
- Where the record-stated cases were collected, the reading adds that the configuration weighs a call exactly as the record implies.

**Readings:**

| Configuration | Confident call, no record | Others' median | "I think…" | Reading |
| --- | --- | --- | --- | --- |
| Terra | 2.53 (to 93%) | 1.07 | 0.53 | Face value (2.4×) |
| Sol | 1.31 (to 79%) | 1.07 | 0.42 | Like the others (1.2×) |
| Luna | 1.07 (to 75%) | 1.31 | 0.28 | Like the others (0.8×) |
| Astra | 0.82 (to 69%) | 1.31 | 0.63 | Wording barely matters |

All four weigh a call exactly as a stated record implies.

**Astra's reading is new and weaker than Terra's.** Astra gave every analyst's call the same weight in multi-agent open (0.69 whatever the wording). In calls in order the gap between confident and "I think…" was 0.39. Pooled, the gap is 0.20. It does not extend to other sources: with an AI agent's or a sensor's call, Astra responds to wording like the others (0.40 to 1.73 and 2.19).

**Scope.** Only Astra, Sol, Luna and Terra have analyst data without a record, so the other configurations carry no reading. The caution names the source-specificity.

## 2 October: confident wording across families (idea 28)

**Question.** Without a record, Terra took an analyst's "definitely… confirmed" call at face value, about twice the other configurations, in two urn collections. Is that a trait of confident wording, or of the urn family and that phrase?

**Modules `wording-{urn,policy,report}-{a..d}`** (design 0.29.0, tasks 0.39.0). One person's claim without a record, against a stated prior:
- **urn:** an analyst's call on an urn, as in the original family.
- **policy:** an economist's note on whether a central bank's committee lowers its rate at its next meeting. The note's conclusion carries the claim.
- **report:** an inspector's report on whether a batch of goods meets its standard. The report's conclusion carries the claim.

The claim takes one of four wordings: "I think…", plain, "definitely…", and the original "definitely… confirmed". In the urn family that also splits confidence from a claim of verification.

**Design.**
- The three families share one skeleton: priors of 40, 50 or 60%, the claim's direction and its wording. Only the texts differ.
- Each family takes four forms in a Latin square: every item appears at every wording, and a form holds six items at each wording, with directions balanced.
- Each case is separate, in random order.
- Measure: weight = (logit(answer) − logit(prior)) × direction.

**What would count** (exploratory; no claim before a confirmatory run):
- **A trait:** Terra's "definitely… confirmed" weight is at least 1.5 times the median of the other configurations, with the interval above 1, in the policy and report families as well as the urn.
- **Family-specific:** face value in the urn family only.
- **Verification, not confidence:** Terra's excess sits in "confirmed": "definitely" alone is like the others, and "confirmed" adds much more for Terra than for the others.

**Collection.** Preset `wording-families`: Astra, Sol, Luna and Terra at default effort, each taking the four forms of each family (48 sessions). Analysis: `uv run python -m epistemics.ledger wording-families <roots> --output <file>`.

### Results

**Collection.** Root `output/wording-families-20261002`: 48 of 48 sessions (Astra, Sol, Luna and Terra × three families × four forms), 22.9 million input tokens, no failures.
- Task validation 0.39 passed on both seeds: 4,512 cases, 193 contexts, wording recovery error at most 0.05 against a tolerance of 0.15.
- Fingerprint `0c30480df0dbd8d3…`.
- Command: `uv run python -m epistemics.ledger wording-families output/wording-families-20261002 --output output/wording-families-summary-20261002.json`.

**Mean weight (log-odds toward the claim), "I think…" / plain / "definitely…" / "definitely… confirmed":**

| Family | Astra | Sol | Luna | Terra |
| --- | --- | --- | --- | --- |
| urn | 0.51 / 0.76 / 1.15 / 1.43 | 0.61 / 0.91 / 1.38 / 2.08 | 0.28 / 0.35 / 1.15 / 1.70 | 0.37 / 0.54 / 1.28 / 2.19 |
| policy | 0.50 / 0.77 / 1.07 / 1.26 | 0.68 / 0.90 / 1.43 / 1.76 | 0.76 / 1.06 / 2.68 / **3.86** | 0.52 / 1.03 / 2.37 / **3.07** |
| report | 0.88 / 1.57 / 2.18 / 2.36 | 0.96 / 1.70 / 2.71 / 3.31 | 0.81 / 1.99 / 3.71 / 4.60 | 0.91 / 1.92 / 3.52 / 4.24 |

**"Definitely… confirmed" against the median of the other three** (90% bootstrap interval):

| Family | Astra | Sol | Luna | Terra |
| --- | --- | --- | --- | --- |
| urn | 0.69 [0.63, 0.77] | 1.22 [0.94, 1.51] | 0.82 [0.53, 1.17] | 1.29 [0.97, 1.68] |
| policy | 0.41 [0.35, 0.50] | 0.57 [0.48, 0.70] | **2.20 [1.96, 2.46]** | **1.75 [1.42, 2.10]** |
| report | 0.55 [0.51, 0.60] | 0.78 [0.69, 0.88] | 1.39 [1.24, 1.57] | 1.28 [1.14, 1.45] |

**Ceiling.** Share of answers at 99% or more on a "definitely… confirmed" claim:
- report: Astra 0%, Sol 38%, Luna 100%, Terra 50%;
- policy: Terra 50%, Luna 42%, the others 0%;
- urn: Luna 25%, the others 0%.

Where answers sit at the ceiling, the measured weight understates how far the configuration would go. So the report ratios, and Luna's and Terra's policy ratios, are lower bounds.

**Reading.**
- **Terra's face value in the urn family did not replicate in this design.**
  - Its "definitely… confirmed" call moves it 2.19 log-odds, against 2.45 and 2.60 before.
  - The others now give the same phrase much more than before: Sol 2.08 against 1.23–1.39, Astra 1.43 against 0.69–0.95. So the ratio fell from about 2.4 to 1.29, with the interval reaching 1.
  - The likeliest difference is the phrase set:
    - Before, the combined phrase was the top of three wordings.
    - Here "definitely" alone is also offered, so "confirmed" stands apart as a claim of verification.
    - The collections ran within hours of each other on the same day, so drift is unlikely, but this is post hoc.
- **Most of the weight on the top phrase comes from "confirmed".** It adds to "definitely" for every configuration in every family (+0.18 to +1.18). Terra's increment is largest in the urn family (+0.92), but not distinctively so (Sol +0.69).
- **In the policy family Terra and Luna take confident wording at face value; Astra and Sol barely move with it.**
  - An economist's "definitely… confirmed" forecast moves Luna 3.86 and Terra 3.07 log-odds, and half of Terra's answers go to 99% or more.
  - The same note moves Astra 1.26 and Sol 1.76.
  - The widest gap between configurations in this experiment is on a forecast. A forecast is the claim least open to confirmation.
- **Inspection reports move everyone a lot**, which makes sense for a tester's verdict. Luna and Terra still move furthest, near the ceiling.
- **Wording sensitivity, ordered, holds across families:**
  - Astra's spread from "I think…" to "definitely… confirmed" is the smallest in every family: 0.92, 0.76, 1.48.
  - Terra's is in the top two in every family: 1.83, 2.55, 3.33.
  - Luna is top in policy and report but third in urn.
- **Consequences for the passport readings written this morning (reading guide 0.6.0):**
  - **Terra, "takes an analyst's confident wording at face value":** replicates in the policy family, not in the urn family under a four-wording set. As written it overstates a design-conditional effect.
  - **Astra, "wording barely matters":** contradicted. Astra is the least sensitive to wording in every family, but its spread is 0.8–1.5 log-odds, not flat.
  - **A sounder reading is ordinal across families:** Astra reacts least to confident wording, Terra and Luna most, with the gap largest on forecasts.

**Ideas:**
29. **Replace the calls reading with a cross-family wording-sensitivity reading.** Use each configuration's spread and its top-phrase weight against the others, pooled over the three families, with a ceiling-aware measure (the share of answers at 99% or more) beside it.
30. **Phrase-set dependence.** Rerun the urn family with the original three-wording set beside the four-wording set in matched sessions. That would show whether Terra's face value depends on "definitely… confirmed" being the top of the scale.
31. **Forecasts against verifiable claims.** Does the policy-family gap come from the claim being a forecast? An economist reporting a decision already announced would be confirmable; a forecast is not.

## 2 October: confident wording in the passport (idea 29)

Reading guide 0.7.0 replaces the analysts'-calls reading (`confident-calls`, 0.6.0) with one reading across kinds of claim, `confident-wording`, under "How it weighs evidence". The passport field `call_reaction` gives way to `wording_sensitivity`, built from the wording-families collection. The record-stated ratio from the multi-agent pilot is kept beside it.

**Rules.**
- In each family, a configuration's "definitely… confirmed" weight is compared with the median of the other configurations. It counts as above or below only when the 90% interval excludes 1; otherwise it is like the others.
- **Moved more:** above in some family and below in none. **Moved less:** the reverse. **Like the others:** neither. Otherwise **it depends on the kind of claim**.
- The reading names the share of answers at 99% or more when that is at least 40%, because the weights there are lower bounds.
- It adds that an analyst's stated record is weighed exactly when the ratio is within 0.05 of 1.
- The dashboard's passport table shows the geometric mean of the three ratios, marked "least" where the spread from "I think…" is the smallest in every family.

**Readings:**

| Configuration | Reading | Across the three |
| --- | --- | --- |
| Terra | Moved more: further for forecasts and reports, about as far for analysts' calls; half its answers at 99% or more on both | 1.43× |
| Luna | Moved more: the same pattern; 42% and 100% of answers at 99% or more | 1.36× |
| Sol | Moved less: less for forecasts and reports, about as far for analysts' calls | 0.82× |
| Astra | Moved less in every kind of claim, and its answers change least with the wording | 0.54× |

All four weigh an analyst's call exactly as a stated record implies.

**Why intervals rather than point ratios.** On point ratios, Terra would read as moved further in every family and Sol as further on analysts' calls. Both urn intervals include 1 (Terra 0.97–1.68, Sol 0.94–1.51), so the reading says "about as far" there.

## 2 October: phrase-set dependence in the urn family (idea 30)

**Question.** Terra's face value on an analyst's "definitely… confirmed" call came from collections with three wordings. In the wording-families run, which offers four, the others gave that phrase much more weight and Terra's lead fell from about 2.4 to 1.29. Is that the phrase set?

**Modules `wording-urn3-{a,b,c}`** (design 0.30.0, tasks 0.40.0). These are the urn family's cases and texts with the original three wordings: "I think…", plain and "definitely… confirmed". The analyst "phrases each call in one of three ways".
- They run in three forms, a Latin square with eight items per wording in a form, directions balanced.
- Apart from the phrase set, the texts match the four-wording urn modules word for word; the audit checks this.

**Collection.** Preset `wording-phrase-set`: Astra, Sol, Luna and Terra take the three urn3 forms and, in the same collection, the four urn forms again (28 sessions, random order within a session). The rerun also replicates the four-wording urn result. Analysis: `uv run python -m epistemics.ledger wording-phrase-sets <roots> --output <file>`.

**What would count** (exploratory):
- **Phrase-set dependence:** with three wordings Terra's "definitely… confirmed" weight is again well above the others' median (about 2× or more), and its ratio with three wordings over its ratio with four has an interval above 1.
  - The likely mechanism: with "definitely" offered alone, the others read "confirmed" as a separate claim of verification and give it more.
- **No dependence:** Terra's ratio is about the same with three and four wordings. The earlier face value would then come from the original collections' other features: cases where the agent had its own reading, or two calls per urn.

### Results

**Collection.** Root `output/wording-phrase-set-20261002`: 28 of 28 sessions (Astra, Sol, Luna and Terra × three urn3 forms and four urn forms), 13.4 million input tokens, no failures.
- Task validation 0.40 passed on both seeds: 4,584 cases, 196 contexts, wording recovery error at most 0.05.
- Fingerprint `4e8eff8c529988e2…`.
- Command: `uv run python -m epistemics.ledger wording-phrase-sets output/wording-phrase-set-20261002 --output output/wording-phrase-sets-20261002.json`.

**"Definitely… confirmed" with three wordings against four, in the same collection** (log-odds; ratio to the others' median, 90% interval):

| | Three wordings | Four wordings | Weight, three − four | Ratio, three ÷ four |
| --- | --- | --- | --- | --- |
| Astra | 1.02 (0.68× [0.62, 0.79]) | 1.33 (0.83× [0.64, 0.98]) | −0.31 [−0.48, −0.14] | 0.83 [0.69, 1.14] |
| Sol | 1.49 (1.46× [1.03, 1.59]) | 1.91 (1.19× [1.00, 1.60]) | −0.42 [−0.69, −0.14] | 1.23 [0.75, 1.43] |
| Luna | 0.98 (0.66× [0.35, 1.02]) | 1.60 (1.00× [0.63, 1.47]) | −0.62 [−1.36, 0.13] | 0.66 [0.33, 1.24] |
| Terra | 1.68 (**1.65×** [1.08, 1.98]) | 1.60 (1.00× [0.68, 1.40]) | **+0.08** [−0.50, 0.67] | **1.65** [0.93, 2.46] |

Pooling both four-wording urn collections (48 cases each): Terra 1.15× [0.89, 1.48], Sol 1.21× [1.01, 1.49], Luna 0.87×, Astra 0.73×.

**Reading.**
- **The phrase set changes how the others read the top phrase, not how Terra reads it.**
  - With three wordings, Astra, Sol and Luna give "definitely… confirmed" less (0.3–0.6 log-odds; intervals exclude 0 for Astra and Sol). They treat it as the top of the analyst's scale.
  - With "definitely" also on offer, they read "confirmed" as something more, a claim of verification, and give it more.
  - Terra gives the phrase the same weight either way (+0.08). It reads the words, not their place among the analyst's wordings.
- **So Terra's lead with three wordings comes from the others discounting, not from Terra inflating.**
  - With three wordings Terra stands 1.65 times the others' median (interval above 1). With four it is at the median.
  - The shift's interval just reaches 1 (0.93–2.46), so the dependence is supported but not settled.
- **Three wordings alone do not restore the earlier 2.4×.** The rest of that gap belongs to the earlier designs or to session-to-session variation.
  - The earlier designs had cases with the agent's own reading in the same session, and two calls per urn.
  - Terra's top-phrase weight on the four-wording urn was 2.19 this morning and 1.60 here, the largest drop between the two collections.
- **A candidate trait for the passport: set-relative reading of wording.** Most configurations read a confidence phrase against the range the source uses; Terra reads it as worded. That is one collection with four configurations, exploratory.
- **The current passport reading stands:** "about as far as the others for analysts' calls" is measured with four wordings. Its caution should now say that with three wordings Terra stands further from the others.

**Ideas:**
32. **Set-relative reading as a passport dimension.** For each configuration, how much a phrase's weight changes when the source's other wordings change. Test it across families, for example an economist with three wordings against four.
33. **Session-to-session variation on the urn.** Terra's top-phrase weight moved 0.6 log-odds between two four-wording collections run the same day. A retest of one form across several sessions would size that before any reading leans on the urn ratios.

## 2 October: the three-wording result in the passport caution

Reading guide 0.7.1. The `confident-wording` reading's caution now carries each configuration's phrase-set result from `output/wording-phrase-set-20261002`, in place of "whether the analyst result depends on the wordings offered is untested". The ledger build adds `phrase_sets` to `wording_sensitivity` from the registry's `wording-phrase-set` roots.

Each caution gives, for that configuration:
- how its weight on "definitely… confirmed" changes when an analyst uses three wordings rather than four: less, more, or no clear change, by whether the 90% interval excludes 0;
- the call's ratio to the others' median with three wordings and with four, both from that collection.

Terra's caution reads: no clear change (+0.08), 1.65 times the others with three wordings against 1.00 with four. Astra and Sol give the phrase less as the top of three. Luna shows no clear change.

## 2 October: set-relative reading in the policy family (idea 32)

**Question.** On the urn, Astra and Sol gave "definitely… confirmed" less when it was the top of three wordings than when "definitely" was also on offer. Terra gave it the same either way: it reads the words, not their place among the analyst's wordings. Does this hold for an economist's forecast? That is the family where Terra and Luna moved furthest and half of Terra's answers reached 99% or more.

**Modules `wording-policy3-{a,b,c}`** (design 0.31.0, tasks 0.41.0). These are the policy family's notes with the three original wordings: the economist "phrases each conclusion in one of three ways". Otherwise they match the four-wording policy modules word for word, and the audit checks this.

**Collection.** Preset `wording-phrase-set-policy`: Astra, Sol, Luna and Terra take the three policy3 forms and, in the same collection, the four policy forms again (28 sessions). Analysis: `uv run python -m epistemics.ledger wording-phrase-sets <roots> --family policy --output <file>`.

**What would count** (exploratory):
- **Set-relative reading is general:** the configurations that read the urn phrase against the analyst's range (Astra and Sol) also give the economist's top phrase less as the top of three. Terra's weight does not change.
- **Specific to the urn:** no configuration's weight changes with the set.

**Caveat.** Many policy answers sit at 99% or more. If Terra's are at that ceiling, its weight cannot rise and a fall would show only as fewer answers there, so the analysis reports the share at the ceiling for each set.

### Results

**Collection.** Root `output/wording-phrase-set-policy-20261002`: 28 of 28 sessions (Astra, Sol, Luna and Terra × three policy3 forms and four policy forms), 13.8 million input tokens, no failures.
- Task validation 0.41 passed on both seeds: 4,656 cases, 199 contexts, wording recovery error at most 0.05.
- Fingerprint `06a050254e705989…`.
- Command: `uv run python -m epistemics.ledger wording-phrase-sets output/wording-phrase-set-policy-20261002 --family policy --output output/wording-phrase-sets-policy-20261002.json`.

**An economist's "definitely… confirmed" forecast with three wordings against four, in the same collection** (log-odds; ratio to the others' median; share of answers at 99% or more):

| | Three wordings | Four wordings | Weight, three − four |
| --- | --- | --- | --- |
| Astra | 1.45 (0.67×; 0%) | 1.09 (0.40×; 0%) | **+0.36** [0.23, 0.49] |
| Sol | 1.69 (0.79×; 0%) | 1.90 (0.69×; 0%) | −0.20 [−0.36, −0.06] |
| Luna | 2.94 (1.74×; 0%) | 3.94 (2.07×; 42%) | −0.99 [−1.27, −0.71] |
| Terra | 2.16 (1.27×; 0%) | 2.77 (1.46×; 4%) | **−0.61** [−0.92, −0.32] |

**Set-relative reading across the two families** (weight on the top phrase, three − four):

| | Urn | Policy |
| --- | --- | --- |
| Astra | −0.31 (less) | **+0.36 (more)** |
| Sol | −0.42 (less) | −0.20 (less) |
| Luna | −0.62 (no clear change) | −0.99 (less) |
| Terra | +0.08 (no clear change) | **−0.61 (less)** |

**Reading.**
- **Set-relative reading is not a stable trait of Terra or Astra.**
  - On the urn, Terra read the top phrase as worded. On the economist's forecast it gives the phrase less as the top of three, like Sol and Luna.
  - Astra reverses. With four wordings it barely tells "definitely" from "definitely… confirmed" on a forecast (1.05 against 1.09). With three it gives the top phrase, and the lower wordings, more.
- **Sol and Luna read the top phrase against the source's range in both families.** That is the only consistent part, and with two families it is thin.
- **So the urn's "Terra reads the words, others read the range" was specific to the urn.** I would not add set-relative reading as a passport dimension on this evidence.
- **The forecast ordering in the passport replicates.** With four wordings, rerun hours later:
  - Luna 2.07×, Terra 1.46× [1.31, 1.62], Sol 0.69×, Astra 0.40×.
  - Pooled over both collections: Luna 2.13×, Terra 1.60×, Sol 0.63×, Astra 0.40×.
  - The `confident-wording` reading's "moved more" for Terra and Luna, and "moved less" for Sol and Astra, holds for forecasts.
- **Terra's answers vary between sessions.**
  - On the same four-wording forecasts, half of Terra's "definitely… confirmed" answers reached 99% or more this morning; here 4% did. Its mean weight changed less (3.07 against 2.77).
  - Luna was steady: 42% both times, 3.86 against 3.94.
  - That supports idea 33: size session-to-session variation before leaning on single-collection ratios.
- **For the passport caution** (currently the urn's three-wording result): it should add that the phrase set's effect differs by family. On forecasts Terra gives the top phrase less as the top of three, and its lead over the others shrinks rather than grows (1.27× against 1.46×).

## 2 October: the family note in the passport caution

Reading guide 0.7.2. The `confident-wording` caution now carries each configuration's phrase-set result for both kinds of claim measured both ways: the analyst's call (`wording-phrase-set`) and the economist's forecast (`wording-phrase-set-policy`). The ledger build reads both from the registry and stores `phrase_sets` by family.

Each caution says whether the configuration's results go the same way in both families or not. For each family it gives:
- the change in its weight on "definitely… confirmed" when the source uses three wordings rather than four: less, more, or no clear change;
- its ratio to the others' median with three wordings and with four.

**Results by configuration:**
- **Terra:** no clear change on the analyst's call (1.65× against 1.00×); less on the forecast (−0.61; 1.27× against 1.46×).
- **Astra:** less on the call (−0.31), more on the forecast (+0.36).
- **Luna:** no clear change on the call, less on the forecast (−0.99).
- **Sol:** less on both (−0.42 and −0.20), the only configuration whose caution says "in the same direction for both kinds of claim measured".
