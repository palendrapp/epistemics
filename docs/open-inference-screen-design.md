# Open-inference screen (design note)

Design, 30 September 2026. Nothing is built or collected. The decisions for you are listed at the end.

## Why a screen

**Five times now, a battery has been built first and found at ceiling afterwards:**
- the capacity ladders;
- stated social structure;
- battery v3 (certainty equivalents computed as expected value);
- battery v3.1 (described consequences read as rules);
- and, before those, the explicit description tasks.

Each cost a build, a validation and a pilot before we learned that every configuration answers the same way.

**The common cause, sharpened by CogGym** ([Ying et al. 2026](https://arxiv.org/abs/2609.21259); see the [reading list](reading-list.md#task-choice-inference-the-task-leaves-underdetermined-30-september)). Our tasks state the model that produces the answer: which sources, how accurate, who copies whom, what each mistake costs. At most one number is left to the agent, and frontier agents fill it with the norm or a rule.

The experiments that separate models in CogGym are those where the agent must supply the model itself:
- **a hypothesis space:** which rule produced these numbers;
- **a model of the speaker:** did "$51" mean exactly $51;
- **a model of another agent:** why did the pirates walk past the map.

CogGym also found that frontier models mostly fail on the same experiments (their Fig. 11). The experiments where models disagree are where different priors show.

**What that means for us.** Rational models still define the parameters when a task has no answer key; this is the rational-analysis move (Oaksford & Chater). The trait is the prior the agent brings, located by its behaviour. We don't need a ground truth, but we do need tasks whose answers depend on that prior, and a cheap way to find out whether configurations differ on them before building a battery.

**The screen** measures, for several candidate task families, whether configurations differ reliably, before any is built into a trait battery.

## What makes an item open

An item is **open** when its answer depends on a model the item does not state. Each family below has a rational model with prior parameters. An item's **openness** is the spread of the model's predicted answer across the plausible range of those parameters: the difference between the 90th and 10th percentiles of the predicted probability, with parameters drawn from a stated plausible range.

- **Open items:** openness of at least 0.3 in the family's median item.
- **Determinate items (anchors):** openness below 0.02. The item states enough to fix the answer.

This turns "weak situation" into an audit that is computed before collection, not discovered after a pilot. It is a property of the items under the family's model, and the audit reports it per item.

**A computability audit** as well: no open item states a rate, accuracy or likelihood that could be combined into an answer. Digits appear only as the data themselves: the examples, the readings, the reported number.

## Five candidate families

Each family has two primary contrasts. Each contrast is a signed average of item responses (on the log-odds scale), with signs set by the direction the family's model moves each item when its parameter increases. The contrasts are model-guided but computed without fitting, so the screen does not depend on a model being right.

### F1. Generalising from examples (hypothesis breadth)

- **The item:** "A process produced these values: 16, 8, 2, 64. What is the probability that it could also produce 10?" Surfaces: a generator's outputs, codes a lock accepts, identifiers a system issues.
- **The model:** Bayesian concept learning (Tenenbaum 2000). Hypotheses are mathematical rules (odd, multiples of *k*, powers of *k*, squares, ending in *d*) and magnitude intervals. The parameters:
  - *λ*, the prior weight on rules against intervals;
  - *ω*, the sampling assumption (how much generalisation tightens as consistent examples accumulate, from strong to weak sampling; Navarro, Dry & Lee 2012).
- **Contrasts:**
  - **Rule reliance:** probes that fit a rule but are far away, against probes that are near but break the rule.
  - **Tightening:** the same probe after one example against after four.
- **Anchors:** "The process outputs exactly the multiples of 4 up to 100…"
- **Why it's promising:** CogGym's first misaligned case. Given 15, 39 and 35, every run of three frontier models said 41 fits, because all are odd; 18% of people did. Human individual data are public (Bigelow & Piantadosi 2016).

### F2. Reading reported numbers (literalness)

- **The item:** "A colleague reports that the transfer took 30 minutes. What is the probability that it actually took between 28 and 32 minutes?" It is crossed with:
  - round against sharp numbers ("31 minutes");
  - a person against an instrument ("the meter shows 30");
  - window widths.
- **The model:** a listener who inverts a speaker with a precision goal (rational speech act models: Frank & Goodman 2012; imprecision and the round-number halo: Kao, Wu, Bergen & Goodman 2014). The parameters:
  - *h*, the halo width attributed to round numbers;
  - the difference in literalness between a person and an instrument.
- **Contrasts:**
  - **Halo:** exact-window probability for round numbers against sharp ones.
  - **Source sensitivity:** the halo for people minus the halo for instruments.
- **Anchors:** "The display rounds to the nearest 10 and shows 30…"
- **Why it's promising:** CogGym's pragmatics case ("It cost $51" read as exact by frontier models). It bears on how agents read other agents' and people's reports, next to our findings that unstated relays are taken at face value and that confidence persuasion is surface-specific.

### F3. Inference from others' choices (rationality attribution)

- **The item:** "The inspector could have run a quick test of batch B17 on the way, did not, and signed it off as sound. How likely is it that they already knew it was sound?" It varies:
  - the cost of the skipped check (trivial, moderate, large, in words);
  - whether the check was skipped or taken;
  - whether the decision was confident or hedged.
- **The model:** inverse planning with a naive utility calculus (Baker, Saxe & Tenenbaum 2009; Jara-Ettinger, Gweon, Schulz & Tenenbaum 2016). The observed agent checks when the expected value of checking exceeds its cost. The parameters:
  - *β*, how rational the observer assumes others are;
  - the prior that others know.
- **Contrasts:**
  - **Skip informativeness:** knowledge inferred from a skipped cheap check against a skipped costly one.
  - **Taken-check discount:** a taken check signals less prior knowledge.
- **Anchors:** "The inspector's log shows they tested the batch yesterday…"
- **Why it's promising:** CogGym's theory-of-mind case (pirates who walk past a map knew where to dig; two of three frontier models missed it; Aboody, Davis, Dunham & Jara-Ettinger 2025). It is the multi-agent question directly: does an agent read a peer's unverified confidence as knowledge?

### F4. Unlisted alternatives (open-world prior)

- **The item:** "Pump P17 stopped. Known causes of this are a blocked intake, a failed seal and a power fault. What is the probability that the cause was a failed seal?" It is crossed with:
  - list length (two, three or five causes);
  - who compiled the list (a manual against a colleague's suggestions);
  - direct questions ("…that the cause was none of these?").
- **The model:** support theory (Tversky & Koehler 1994), with a residual weight *r* for causes not listed. A closed-world reader gives 1/*k* to each listed cause; an open-world reader holds some mass back. The parameters:
  - *r*;
  - its dependence on the list's source.
- **Contrasts:**
  - **Residual mass:** from the list-length scaling and the direct questions.
  - **Source dependence:** a colleague's list against a manual's.
- **Anchors:** "…these are the only three causes that can stop this pump…"
- **Why it's promising:**
  - **The consumer question:** whether an agent considers that none of the offered explanations is right is central to diagnosis and research agents (Fischhoff, Slovic & Lichtenstein 1978 on fault trees that omit branches).
  - **A risk:** the equal split 1/*k* may be a strong default.

### F5. Extrapolating from a few readings (function prior)

- **The item:** "A gauge read 10 after one hour, 18 after two and 24 after three. What is the probability that it will read above 45 after eight hours?" Series are linear, decelerating or accelerating; probes are near or far.
- **The model:** Bayesian function learning with a mixture of function families (linear, saturating, exponential) and noise (Lucas, Griffiths, Williams & Kalish 2015). The parameters:
  - the prior weight on linear functions;
  - extrapolation uncertainty.
- **Contrasts:**
  - **Linearity bias:** the probability of exceeding the linear projection on decelerating series.
  - **Far-field humility:** the spread of probability across windows far from the data against near.
- **Anchors:** "The gauge rises by exactly 5 every hour…"
- **Why it's promising:** forecasting from short trends is everyday agent work. People are strongly biased towards linear functions (Lucas et al. 2015), so the prior is where configurations could differ.

### Considered and deferred

- **Causal induction from contingencies** (causal support against Δ*P*; Griffiths & Tenenbaum 2005). The items are small contingency tables, and frontier agents are likely to compute a textbook test on them, which would make it a strong situation. Deferred unless the others fail.
- **Moral and blame judgements.** Values, not inference; out of the passport's current scope.
- **Physical and visual reasoning.** Not text.

## A general trait these families could share

CogGym's diagnosis of its failures is "over-confident, under-dispersed judgments": committing to the first compact model. The same disposition would show in every family here:
- the first rule that fits (F1);
- the literal reading (F2);
- taking a skipped check as knowledge, or as nothing (F3);
- the closed-world list (F4);
- the straight line (F5).

If configurations differ in how much belief they reserve for models other than the simplest, that would be a **general trait of hypothesis commitment**, interpretable in each family's own parameters. The screen gives a first, exploratory look: the correlation of configurations' scores across families. Only the battery that follows could test it.

## Design

**Sessions.** One module per family and form, 24 trials each:
- 20 open items;
- 4 anchors (determinate answers, which check comprehension and calibrate the noise);
- random order;
- probability answers, the collection service's existing format.

Each family has two parallel forms, `a` and `b`, with the same item structure on different surfaces. Session 2 is on the other form, so the retest is also a first check across surfaces.

**Instructions.** Neutral: "Cases give limited information; answer with your best judgement of the probability." Nothing signals that answers lack a key, since that could itself shift behaviour.

**Configurations.** Battery v2's six: Astra, Sol, Astra-low, Sol-low, Luna and Terra.

**Two stages.**
- **Stage A (spread):** one session per family and configuration, on form `a`. That is 30 sessions.
- **Stage B (reliability):** a second session on form `b`, only for the families that pass stage A. That is 6 sessions per passing family.

Two stages are valid for this purpose: session noise only adds to the observed spread, so a family with a large true spread will not fail stage A except by chance.

## Analysis (to be preregistered before stage A)

**Per session:** the two contrast scores. Their standard errors come from a within-session split half, using two halves of the open items matched on structure.

**Anchors first.** Each configuration's anchors should be within 5 points of their determinate answers. If a family's anchors fail, its texts are broken; that is fixed before stage B and not counted as spread.

**Stage A: a contrast passes when all three conditions hold.**
1. **Spread:** the between-configuration SD of the score is at least twice the median within-session standard error.
2. **Guard:** at least three of the six configurations depart from the median by more than *δ*. *δ* is set per contrast in advance, as the score change produced by a meaningful change in the family's parameter (for F1, *λ* changing by 0.2).
3. **No shared rule:** fewer than 80% of open items get the same answer (within 2 points) from all six configurations.

A family passes if either of its contrasts passes.

**Stage B: a contrast passes when both conditions hold.**
1. **Reliability:** the intraclass correlation of configurations' scores across the two sessions is at least 0.5, with a permutation *p* below 0.05 (configuration labels shuffled across the 12 sessions; Holm across the contrasts that entered stage B).
2. **Consistency:** the configurations' differences have the same sign on both forms (retest *r* > 0).

**Reported for every family, whether it passes or not:**
- variance components for configuration, session and item;
- openness against observed spread per item (do the open items open, and do the anchors close);
- the family-level split: GPT-6 against GPT-5.6.

**Exploratory:** correlations of configurations' scores across families (the hypothesis-commitment question).

**What passing means.** A family that passes shows reliable differences between configurations within one family, on two surfaces. It is a candidate for a trait battery (many surfaces, the generality test, parameter recovery), not yet a trait.

## Validation before collection

1. **Openness audit** per item, and the computability audit, in task validation.
2. **Contrast recovery.** Simulated respondents with known parameters, through the real items: each contrast must order respondents by their parameter (rank correlation at least 0.8 over the plausible range), and anchors must come out determinate.
3. **Screen calibration.** Six simulated configurations with no parameter differences, at the report noise of our configurations: stage A passes no more than 10% of the time and stage B no more than 5%. With plausible differences, stage A passes at least 80% of the time.
4. **Task validation** on two seeds, as for every battery.

## Cost (provisional)

- **Stage A:** 30 sessions. The items are shorter than v3's, so about 0.35–0.5 million tokens each, or 11–15 million in total.
- **Stage B:** 6 sessions per passing family, about 2–3 million each. With two or three families passing, that is 5–9 million.
- **Total:** about 16–24 million tokens, against about 6 million for each battery pilot that found a ceiling, and 77 million for battery v2.

## Risks and limits

- **Shared biases.** CogGym's frontier models failed together. Our six configurations may all commit to the rule, read "30" literally and draw the line, with no differences between them. The screen then says so cheaply, before a battery. It would also be a passport finding shared by all six: "commits to the simplest model; offer it alternatives".
- **Two model families.** Only GPT-6 and GPT-5.6 can be run through the Codex harness. CogGym's largest disagreements were between vendors. A null result here says nothing about other families.
- **Session states.** Some CogGym models split between two readings across runs (Gemini on the pirates, Opus on "$51"). A single session can land on either. Stage B separates stable differences from these states.
- **Openness depends on the model.** An item is open under the family's model. An agent with a model outside the family (for example, a lookup of a famous puzzle) can make an open item determinate. The items are generated fresh, with no published stimuli, to limit recognition (CogGym found some models recognise source studies).
- **Contrasts approximate the parameters.** A signed average can mix two parameters. Recovery checks each contrast's ordering, and the family's full model is fitted only in the battery that follows.

## Relation to battery v3.2

The two are independent. Battery v3.2 opens the cost side of decisions (graded and incommensurable consequences). The screen opens the belief side (hypotheses, speakers, other agents, unlisted causes, functions). v3.2's pilot (about 6 million tokens) can run before, alongside or after the screen.

## Decisions for you

1. **Families:** the five proposed (F1–F5), or a subset. My order of interest is F3, F1, F2, F4, F5.
   - **F3 first:** it is the multi-agent question.
   - **F1 and F2 next:** CogGym's clearest cases.
2. **Configurations:** battery v2's six (recommended), or the four medium-effort ones to halve the cost.
3. **Two stages** (recommended) or a single stage with retests for every family (about 25–30 million tokens, and no selection step).
4. **Budget:** about 11–15 million for stage A. Stage B is decided after stage A.
5. **Battery v3.2's pilot:** run it now, after the screen, or drop it in favour of the screen.
