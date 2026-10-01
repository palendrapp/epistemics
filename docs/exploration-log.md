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
