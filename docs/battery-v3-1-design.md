# Battery v3.1: implicit decisions (design note)

Design, 30 September 2026. Nothing is built or collected. The decisions for you are listed at the end.

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
