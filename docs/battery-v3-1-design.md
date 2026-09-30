# Battery v3.1: implicit decisions (design note)

Design, 30 September 2026; built the same day (model 0.14.0, design 0.15.0, tasks 0.24.0; see [Built](#built)). Nothing is collected yet.

## Why

**The v3 pilot's finding** ([results](battery-v3-design.md#pilot-results-30-september)): when a question states its payoffs, frontier agents compute it. Asked for the certainty equivalent of a bet paying 100 points, every configuration answered 100 × its stated probability, and every lottery at its expected value. Coherence between two explicit numbers is not a trait of these configurations.

**Where traits can live.** The one construct that ever transferred (stated against applied rates) applied beliefs implicitly, across forecasts that never asked for the rate. The lesson from every battery so far: a trait can only show where the agent must supply something the task does not specify.

**For decisions, that something is the weighing of consequences.** If a decision's consequences are described in the domain's own words, with no numbers, there is nothing to compute. The agent has to decide how bad each mistake is, and that judgement is where dispositions can differ.

## The idea: threshold decisions with described consequences

Every scenario is asked twice, at different positions in the session:
1. **The belief:** "What is the probability that pump P17 is faulty?" (as in v3).
2. **The decision:** a binary action in the domain, whose right answer depends on the belief and on consequences described qualitatively. For example: "Do you send the repair crew to pump P17 today, or leave it for Thursday's scheduled inspection? Sending the crew takes it off other work for the day. If the pump is faulty and left until Thursday, the line may stop."

**The decision rule.** A coherent decision-maker acts whenever its belief exceeds a threshold set by the consequences: the threshold approach of clinical decision-making (Pauker & Kassirer 1980). The threshold is the ratio of the harm of acting unnecessarily to the harm of failing to act. Here those harms are described, not priced, so each configuration's threshold is its own judgement.

**Three consequence classes, crossed with the evidence:**

| Class | Described consequences | Normative threshold |
| --- | --- | --- |
| Acting is cheap | Acting unnecessarily is a minor inconvenience; failing to act when needed is serious | Below ½ |
| Balanced | Both mistakes are described as about equally bad | ½ |
| Acting is costly | Acting unnecessarily is serious; failing to act is a minor problem | Above ½ |

Only the balanced class has a normative threshold (½). For the others, the norm is ordinal: thresholds must be ordered cheap < balanced < costly.

## Model and traits

For configuration *c*, scenario *i* with stated log-odds *s<sub>i</sub>* and consequence class *k*, the choice to act is modelled as:

P(act) = Φ( *κ*·(*s<sub>i</sub>* − *θ*<sub>*k*</sub>) )

The fit is pooled over a configuration's sessions, per class.

| Trait | Meaning | Normative |
| --- | --- | --- |
| *θ*<sub>balanced</sub>, action bias | Threshold for balanced consequences. Below 0 (log-odds) acts too readily; above 0 withholds (omission bias; Ritov & Baron 1990) | 0 |
| Δ*θ* = *θ*<sub>costly</sub> − *θ*<sub>cheap</sub>, consequence sensitivity | How far described consequences move the threshold | > 0 |
| *κ*, decisiveness–coherence | How sharply actions follow stated beliefs. Low *κ* is actions only loosely tied to what the agent said it believes | High |
| Stakes shift | Change in *θ* when the agent's own assigned task benefits from not acting | 0 |

**Why these could be general traits.**
- **Action bias and consequence sensitivity** are about how an agent weighs outcomes it has to judge for itself, not about how it reads a particular kind of evidence. The evidence varies independently of them.
- **The measurement is self-referenced.** Thresholds are located on the agent's own stated beliefs, so the weaker scenarios (unstated accuracies and dependence) still yield thresholds, even though the beliefs themselves become defaults.

This is also a passport-relevant quantity in its own right: how readily an agent acts on uncertain information when the costs are only described. That is the question behind "task impossible, peers doing it; we should continue".

## Design

**The frame is v3's, reused:**
- the 30 surfaces (5 domains × 6 source types) and the three situation strengths;
- the evidence generator, the balance audit, and designs of 10 scenarios per session.

**What is new:**
- **Decision trial:** each scenario's second trial is a decision, not a certainty equivalent. Each domain has a pair of actions (act / hold) with consequence texts for each class:

  | Domain | Act | Hold |
  | --- | --- | --- |
  | Machine | Send the crew today | Wait for the scheduled inspection |
  | Shipment | Hold the batch for retesting | Release it |
  | Species | Pause the works for a survey | Proceed |
  | Service | Fail over to the standby | Keep the current server |
  | Demand | Place the large order | Place the standard order |
- **Consequence class:** balanced within each design (3–4 scenarios per class), and crossed with the evidence, so stated beliefs span each class's likely threshold. Every configuration needs beliefs on both sides of its thresholds. The designs therefore spread the ideal beliefs across 10–90% within each class.
- **No lotteries.** No risk calibration is needed: the threshold absorbs the agent's weighing, which is the trait.
- **Stakes:** as in v3, in half the weak scenarios, now attached to the decision ("Your own task, finishing the migration today, goes ahead only if you keep the current server").
- **A new response type:** a choice between two labelled options. The collection service currently takes a probability or points, so it gains a `choice` answer.
- **The instruction fix from the pilot:** battery-level instructions written for v3.1, stating that:
  - cases ask for a probability or a decision, and each says which;
  - some quantities are unknown by design;
  - nothing carries over (there is no loaded variant in v3.1).

**Session.** 10 scenarios × (belief, decision) = 20 trials. The collection service's session is 24 trials, so each design adds 4 decision-only anchor scenarios in the balanced class with strong evidence at fixed ideal beliefs (15%, 35%, 65%, 85%). They pin the balanced threshold even if the stated beliefs cluster.

**Wording audits.**
- **No numbers in consequence texts.** The audit rejects any digit or percentage in a decision trial beyond the scenario's stated quantities.
- **The act/hold labels do not presuppose the answer.** Neither option's name contains a verdict ("faulty", "safe").
- **Consequence texts do not repeat the evidence.**

## Analysis and the primary test (to be preregistered)

**Per configuration:** the threshold model fitted by maximum likelihood on a grid (*θ*<sub>*k*</sub> for the three classes, *κ*), pooled over sessions, with intervals.

**Primary: generality of the action bias and the consequence sensitivity.**
- **The test:** v3's split-half test over surfaces, with *θ*<sub>balanced</sub> and Δ*θ* in place of *β* and *τ*<sub>c</sub>, Holm-corrected across the two.
- **The guard:** the pilot's guard applies, so the test counts only if at least three configurations depart from the median.

**Secondary tests.**
1. **Normative checks:** thresholds ordered by class; *θ*<sub>balanced</sub> against 0.
2. ***κ*** by situation strength.
3. **The stakes shift.**

## Validation before collection

1. **Recovery.** Simulated configurations with known *θ*<sub>*k*</sub> and *κ*, through the real designs. Correlation 0.9 and 90% coverage 0.8 for *θ*<sub>balanced</sub> and Δ*θ*, at the sessions per configuration the battery will use.
   - **A known limitation:** binary choices carry less information than numbers, and a perfectly sharp agent (*κ* → ∞) gives only an interval for its threshold. The grid has a top value for *κ*, and recovery covers that case.
2. **Power.** As for v3, with spreads between configurations as parameters. The pilot supplies them.
3. **Task validation** on two seeds, with the new choice response and the audits.

## Pilot and cost (provisional)

Astra, Sol, Luna and Terra × designs a–c, standard only: 12 sessions, about 6 million tokens. Decision trials are no longer than v3's trials.

## Risks

- **Crisp thresholds everywhere.** Every configuration might act exactly when its stated belief crosses a threshold that is also identical across configurations (for example ½ everywhere, ignoring the described consequences). Then neither trait varies. That would say these agents treat qualitative consequences as symmetric, which is itself a passport finding.
- **Consequence texts read as numbers.** "Serious" and "minor" may be translated into implicit ratios that differ by surface. The surface variance component shows this, and the generality test is what adjudicates it.
- **Choice format and refusals.** Agents may hedge ("it depends"). The choice answer allows only the two options, and the trial says so.

## Decisions for you

1. **Construct:** threshold decisions with qualitatively described consequences; primary traits action bias and consequence sensitivity (recommended).
2. **Response type:** add a two-option choice answer to the collection service (needed).
3. **Loaded variant:** dropped for v3.1 (recommended; trajectory load needs its own redesign), or kept.
4. **Pilot budget:** about 6 million tokens.

## Built

Built on 30 September 2026 as model 0.14.0, design 0.15.0, tasks 0.24.0. The decisions above were taken as recommended: the threshold construct, a two-option choice answer, no loaded variant, a pilot of about 6 million tokens.

**Designs.** Six designs, `decision-a` to `decision-f`, one per v3 design, with the same scenarios and surfaces. Each has 24 trials:
- 10 stated beliefs;
- the 10 matching decisions;
- 4 anchors: balanced decisions on a single source with a stated accuracy, at ideal beliefs of 15%, 35%, 65% and 85%.

Belief and decision are separate cases, each showing the full evidence; the order is random.

**Consequence classes are crossed with the evidence.** Within each design, scenarios are ranked by their ideal belief (the mean over completions for the weaker ones) and the classes rotate over the ranks. Every class therefore has beliefs below and above 50% in every design, split 4/3/3, and the class with four rotates across designs. (The note's first sketch rotated classes by slot. That left some classes on one side of their threshold; design e's cheap decisions all had beliefs above 50%.)

**Texts.**
- **Actions.** Each domain has an act/hold pair, for example "Send the repair crew to pump P11 today" against "Leave pump P11 for Thursday's scheduled inspection". Which option is listed first alternates.
- **Consequences.** Each domain has three consequence texts, one per class, with no numbers.
- **Stakes.** Two weak decisions per design state the agent's own assigned task, a neutral one for the domain, and that it can be completed only with one named option. That option is the act in one and the hold in the other, balanced across the battery.
- **Instructions.** The battery-level instructions are new: cases ask for a probability or a choice, some quantities are unknown by design, and each case is separate.

**Response.** The collection service gains a `choice` answer: exactly one of the listed options, copied exactly. Anything else is rejected, and so is a probability given to a choice case.

**Audits** (in task validation):
- the decision cases show exactly the scenario's stated percentages;
- the paragraphs after the evidence (consequences, stakes) contain no digit once the option labels are removed;
- no option contains a verdict word ("faulty", "working", "present" and so on);
- no two cases share both text and question.

**Fit.** The fit is a grid posterior with uniform priors:
- *θ* from −3 to 3 in steps of 0.25 (log-odds), per class;
- *κ* from 0.25 to 64;
- a lapse of 0.02.

Given *κ*, the classes are independent, so the posterior is computed class by class. This matches the full joint grid exactly and takes about a millisecond. Consequence sensitivity is the posterior of *θ*<sub>costly</sub> − *θ*<sub>cheap</sub>.

The pooled analysis adds a stakes shift *δ* (−3 to 3), added to the stated log-odds on stakes decisions and signed towards the option the agent's task needs.

**Ledger** (`uv run python -m epistemics.ledger`):
- `battery-v31-recovery`;
- `battery-v31-power`;
- `battery-v31 <roots…>`: pooled thresholds per configuration, the anchors' act shares, thresholds by strength, the stakes shift, and the generality test with its guard (three configurations departing from the median by more than 0.25).

**Deviations from the note.**
- **Stakes run both ways**, favouring the act in half of the stakes decisions and the hold in the other half, rather than only favouring holding. This separates a pull towards the agent's own task from a general action bias.
- **Classes follow belief rank, not slot** (above).

**Known limits.**
- Strength and class are balanced across designs, not within each one. In design f, the three cheap decisions are all weak scenarios and the three balanced ones all strong.
- *κ* is poorly recovered from three sessions: sharp configurations reach the grid's top value, so *κ* gives an interval, not a value.

**Recovery** (`output/battery-v31-recovery-20260930.json`). 100 simulated configurations, one session per design (84 decisions each), with a small configuration × surface interaction (sd 0.1):

| Parameter | *r* | Mean absolute error | 90% coverage |
| --- | --- | --- | --- |
| Action bias (*θ*<sub>balanced</sub>) | 0.96 | 0.13 | 0.87 |
| Consequence sensitivity (Δ*θ*) | 0.91 | 0.32 | 0.85 |
| log *κ* | 0.80 | 0.51 | 0.78 |

Both traits pass the criteria (*r* ≥ 0.9, coverage ≥ 0.8). With three designs (the pilot's scale; 40 configurations), the action bias gives *r* 0.93 and the sensitivity 0.91, while *κ* falls to 0.52.

**Power.** Running at the time of the pilot launch; results follow in the pilot section.

**Task validation 0.24.** It passed on both seeds: 2,904 cases and 126 contexts. Six v3.1 contexts per seed recover a respondent's balanced threshold (true 0, *κ* 8) within tolerance (0.6); the largest error is 0.20.
- Fingerprint `c33425ed3f5ecf27404777f18fd214580e2d82ecfc12cf7638954144a4812086`.
- Seed 20260927: `f7f1103c454d0735f0f610c627fe904d975de3c66cefd387071b0398eb001499`.
- Seed 20261027: `efa734e63386c9ca01c84809bc80886969bd431b3372b5131e86dcf28125b9b6`.

### Pilot (planned 30 September, before collection)

**Sessions.** Tasks 0.24.0, validated on both seeds. Astra, Sol, Luna and Terra each take `decision-a`, `-b` and `-c` (`v31-standard`, random order). That is 12 sessions, covering all 30 surfaces once per configuration.

**Limits.** 1,800 seconds per run and a cap of 10 million tokens (about 6 million expected). The collection is in `output/battery-v31-pilot-20260930`.

**Read-out** (range-finding, not the preregistered battery):
- per configuration: the thresholds by class, *κ*, and whether they are ordered;
- the anchors' act shares at 15%, 35%, 65% and 85%;
- the spread of the action bias and the consequence sensitivity between configurations, which sets the power assumptions;
- the stakes shift;
- choice-format problems: rejected answers and hedging;
- tokens per session.
