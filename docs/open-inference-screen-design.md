# Open-inference screen (design note)

Design, 30 September 2026. Built on 1 October (tasks 0.26.0) and revised the same day (model 0.17.0, design 0.18.0, tasks 0.27.0), with families F2 and F5 redesigned and a profile-recovery test added: see [Built](#built) and [Revision](#revision-tasks-027-1-october). Nothing is collected yet.

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

## What the parameters are: a Bayesian observer per family

**Added 1 October, after you asked what parameters a working screen would give.**

Every family's model is a Bayesian observer. It computes the posterior predictive P(answer | data) = Σ<sub>h</sub> P(answer | h)·P(h | data) over hypotheses the item does not state. Its parameters are of two kinds, the same kinds as the original model's (the dependence prior and suspicion of silence were also assumptions about how evidence came to be):

| Family | Structural prior: what it assumes when the task is silent | Diagnosticity: how it thinks the data were generated |
| --- | --- | --- |
| F1 Generalising | *λ*, rules against similarity | *ω*, examples sampled from the concept (the size principle's weight) |
| F2 Reported numbers | *π*, a person's number is exact rather than rounded (*π*<sub>I</sub> for instruments) | *ε*, the precision of an exact report |
| F3 Others' choices | *κ*, others already know | *β*, others act rationally, so their choices are evidence |
| F4 Unlisted causes | *ρ*, the world is open (causes outside the list), by who listed them | none (no evidence in these items) |
| F5 Extrapolating | *w*, the world is linear | *b*, a likelihood weight (how much the readings constrain the curve; below 1 is conservatism) |

- **The profile** a configuration would get is these parameters, from the full observer fitted to its sessions ([Profile recovery](#profile-recovery-tasks-027)), not the contrasts. The contrasts are model-free summaries used only to screen.
- **The general-trait questions become formal:**
  - Is diagnosticity one trait across families? Over-weighting the data would be commitment; under-weighting, conservatism in Edwards' sense.
  - Are the structural priors one "simplicity" trait: rules, literal readings, closed lists, straight lines?
- **What is not part of the observer:** report noise (a response parameter, fitted and marginalised), and nuisance parameters that are marginalised:
  - F1's interval size prior;
  - F3's readings of the cost words.
- **A correction.** Two pieces of the first build drifted from this form, and are replaced in tasks 0.27:
  - F5's "humility" was a multiplier on predictive spread, not a Bayesian parameter; *b* replaces it;
  - F2 mixed its exactness prior with an assumed rounding width and precision in the same items; each parameter now has its own items.

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

## Built

Built on 1 October 2026 as model 0.16.0, design 0.17.0, tasks 0.26.0. The decisions were taken as recommended:
- all five families;
- battery v2's six configurations;
- two stages.

**Code:**
- **Models, designs and scoring:** `dispositions/screen.py`.
- **Texts:** `disposition_tasks/screen_texts.py`.
- **Modules:** `screen-<family>-<form>` for families `gen`, `num`, `choice`, `lists` and `trend`, forms `a` and `b`, with variant `screen`.
- **Stage A preset:** `screen-a`, which is 30 runs.
- **Ledger:**
  - `ledger/screen.py`;
  - `screen-validation`;
  - `screen-a <roots>`, which also writes the stage B groups for the families that pass;
  - `screen-b <roots>`.

**Items.** Each module has 20 open items and 4 anchors, in random order, answered as probabilities. Form `b` has the same structure as form `a` with different data and surfaces. Battery-level instructions: "Cases give limited information; answer each question with your best judgement of the probability."

| Family | Open items | Contrast 1 | Contrast 2 |
| --- | --- | --- | --- |
| F1 `gen` | 6 example sets (a rule and a cluster both fit), each with a far rule probe and a near rule-breaking probe; 4 pairs of one example against four | Rule reliance: rule probes minus near probes | Tightening: one example minus four |
| F2 `num` (tasks 0.26; redesigned in 0.27) | 6 sharp and 6 round numbers from people, 6 round numbers from instruments (±1% windows), 2 wide windows | Halo: sharp minus round (people) | Source: instrument minus person (round numbers) |
| F3 `choice` | Skipped trivial, skipped large, skipped moderate and taken moderate checks, 5 each; half by people, half by agents | Skip informativeness: skipped trivial minus skipped large | Knowledge attribution: level over the moderate items |
| F4 `lists` | 10 lists from manuals and 10 from colleagues (2, 3 or 5 causes), asking about a listed cause or "none of these" | Residual mass: level of the implied unlisted share (1 − *k*·*p* for listed causes) | Source: colleague minus manual |
| F5 `trend` (tasks 0.26; redesigned in 0.27) | 5 decelerating and 5 accelerating series (probe at 8, threshold between the linear and curved projections); 10 linear series with ±10% windows at 5 and at 15 | Linearity: decelerating minus accelerating | Humility: minus the level of all ten windows |

**Audits** (in task validation):
- openness per family and form: open-item medians 3.27/3.32 (F1), 2.28/2.29 (F2), 3.06/3.06 (F3), 1.64/1.64 (F4), 2.15/1.99 (F5), all anchors 0;
- no case shows a percentage;
- no open case uses "probability", "likely", "rate", "accuracy" or "chance";
- every anchor states the sentence that fixes its answer;
- no two cases share both text and question.

### Deviations from the note

1. **Openness is measured in log-odds** (median at least 1.0), not probability (at least 0.3). The contrasts are on the log-odds scale, and a probability threshold penalises items whose answers lie near 0 or 1.
2. **The guard's *δ* is uniform:** the score change from moving a contrast's parameters by an eighth of their plausible range. The note's examples (such as *λ* changing by 0.2) were too large for some parameters: a change of 0.2 in the knowledge prior is a third of its range, and the guard then rejected real differences.
3. **Stage A's noise is estimated across configurations:** the SD of the split-half differences, divided by 2. Each session's own split-half error included the fixed difference between its halves' items, which inflated it (1.05 against 0.36 in one check).
4. **Stage B centres each form across configurations and permutes within forms,** which is exact with no configuration differences. The forms' items differ, so an uncentred ICC is diluted by the form difference.
5. **Two contrasts became levels.**
   - **F3's second contrast** is now knowledge attribution, not the discount for a taken check. The latter depended on the same parameter as skip informativeness.
   - **F5's humility** is minus the level of the window probabilities. Near against far cannot isolate humility, which widens both spreads by the same factor; the difference even moved the wrong way.
6. **Recovery checks reliability and monotonicity, not rank correlation with one parameter.** Several contrasts measure constructs that combine a family's parameters:
   - the halo combines the exactness attributed to people with the rounding width assumed;
   - linearity combines the prior with how sharply the data separate function families.

   Their rank correlations with a single parameter, with the others varying, are 0.5–0.7 (F2, F5, F4's source), and 0.8–1.0 for the rest. The screen asks whether configurations differ on each construct. Separating the parameters is for the full model in a battery.
7. **Stage B's calibration criterion is "not significantly above 5%",** that is, at most 5% plus two binomial standard errors, because its permutation test is exact.

### Validation of tasks 0.26 (`output/screen-validation-20261001.json`; superseded by [tasks 0.27](#revision-tasks-027-1-october))

**Contrast recovery** at report noise 0.3 (log-odds), 200 simulated respondents per family and form, parameters drawn across the plausible ranges:

| Contrast | Reliability | Largest decrease | Rank with its parameter | *δ* |
| --- | --- | --- | --- | --- |
| F1 rule reliance | 1.00 | 0 | 0.78–0.85 | 0.78 |
| F1 tightening | 0.92 | 0.02 (clipping near 0) | 0.84 | 0.31–0.51 |
| F2 halo | 0.98 | 0 | 0.50–0.53 | 0.22–0.25 |
| F2 source | 0.97 | 0 | 0.53–0.54 | 0.15–0.18 |
| F3 skip informativeness | 0.90 | 0 | 1.00 | 0.49 |
| F3 knowledge attribution | 0.99 | 0 | 0.95 | 0.30 |
| F4 residual mass | 0.95 | 0 | 0.94 | 0.29 |
| F4 source | 0.95 | 0 | 0.70 | 0.30 |
| F5 linearity | 0.99 | 0 | 0.58–0.59 | 0.32–0.33 |
| F5 humility | 0.99 | 0 | 0.63–0.67 | 0.18 |

**Calibration.** Six simulated configurations, 200 datasets per family and scenario, report noise 0.3. Session states jitter every parameter by 10% of its range.

| Family | Stage A, no differences | Stage B, session states only | Stage A, differences |
| --- | --- | --- | --- |
| F1 | 0.00 | 0.035 | 0.965 |
| F2 | 0.05 | 0.035 | 0.995 |
| F3 | 0.00 | 0.04 | 0.915 |
| F4 | 0.06 | 0.03 | 0.97 |
| F5 | 0.01 | 0.025 | 1.00 |

All criteria hold:
- stage A without differences passes at most 10% of the time;
- stage B with states only passes at most 8.1% (5% plus two standard errors);
- stage A with differences passes at least 80% of the time.

Session states alone make stage A pass 31–64% of the time. That is expected, and it is why stage B exists.

**Task validation 0.26.** It passed on both seeds: 3,288 cases and 142 contexts.
- **Screen contexts:** ten per seed. Each simulated respondent (middle parameters, report noise 0.05) has its anchors within 5 points and every contrast within 0.3 log-odds of its noiseless score; the largest error is 0.10.
- Fingerprint `cf8d9ce22788072d18b1e41f1100e06383b2073222ef79ac1b8b6934f3ef3fd5`.
- Seed 20260927: `f9581ed85abce3827bee18a414544e89c13b22abf1117e4367f298f8451ae4d5`.
- Seed 20261027: `f5bc2e9338692f5f27584ae4531019ad41ea6b18e2551923a50b3c73549a73f3`.

### Revision: tasks 0.27 (1 October)

You asked whether the screen could give separable parameter profiles. A check across all parameters found two families where it could not:
- **F2:** the halo tracked the assumed measurement precision (−0.84) more than the exactness prior (−0.51), and its two contrasts shared items (correlation 0.67);
- **F5:** both contrasts were driven by the assumed process noise (0.76 and 0.64).

Both were redesigned so that each parameter has its own items, within the Bayesian observer ([What the parameters are](#what-the-parameters-are-a-bayesian-observer-per-family)). Model 0.17.0, design 0.18.0, tasks 0.27.0.

**F2, reported numbers.** The speaker model now has three parameters, each pinned by its own items:
- **round numbers from people** (7 items, windows ±0.2 of the number's unit): *π*, the prior that a person's number is exact;
- **round numbers from instruments** (7 items): *π*<sub>I</sub>;
- **sharp numbers from people** (6 items, ±1% windows): *ε*, the precision of an exact report.

A rounded report comes from anywhere in its unit's bin (rounding width fixed). The contrasts are levels: minus the mean log-odds for people's round numbers (halo, people), and for instruments' (halo, instruments).

**F5, extrapolation.** Bayesian model averaging with a fixed process noise (0.15) and two parameters:
- *w*, the prior on linear functions;
- *b*, a likelihood weight: family weights use *b* times the log-likelihood, and parameter uncertainty grows as 1/*b*.

The items are also new:
- **Linearity:** 10 accelerating (geometric) series, each asking whether the reading at 8 will exceed 1.5 times the linear projection. The exponential projection is far above it, so the answer turns on the weight kept on the straight line (exponential growth bias).
- **Conservatism:** 10 exact proportional lines with ±10% windows at 5 and 10. The families agree on these, so only the spread matters.

The decelerating series and the humility multiplier are gone.

**Contrast cross-talk** (rank correlation of each contrast with each parameter, 300 simulated respondents):

| Contrast | Own parameter | Largest other |
| --- | --- | --- |
| F2 halo, people | −1.00 (*π*) | 0.07 |
| F2 halo, instruments | −0.98 (*π*<sub>I</sub>) | 0.13 |
| F5 linearity | 0.79 (*w*) | −0.46 (*b*) |
| F5 conservatism | −0.91 (*b*) | −0.46 (*w*) |

F5's contrasts still overlap; its full fit separates the parameters (below).

#### Profile recovery (tasks 0.27)

**The test.** Each family's full observer is fitted to a configuration's sessions by a grid posterior over all its parameters and the report noise (flat priors; responses are the model's log-odds plus normal noise). Simulated configurations draw every parameter from its plausible range, with report noise between 0.1 and 0.5.

**Criteria**, per profile parameter:
- recovery correlation at least 0.8;
- 90% coverage at least 0.8;
- the estimate correlates at most 0.3 (absolute) with every other true parameter of the family.

200 configurations per family, `output/screen-validation-20261001-2.json`:

| Family | Parameter | *r* (both forms) | Coverage | Largest confusion | *r* (form a only) |
| --- | --- | --- | --- | --- | --- |
| F1 | rules against similarity *λ* | 0.97 | 0.80 | 0.07 | 0.98 |
| F1 | sampling *ω* | 0.98 | 0.84 | 0.23 | 0.98 |
| F2 | exact prior, people *π* | 0.99 | 0.96 | 0.01 | 0.98 |
| F2 | exact prior, instruments *π*<sub>I</sub> | 0.99 | 0.95 | 0.03 | 0.98 |
| F2 | precision *ε* | 0.98 | 0.91 | 0.02 | 0.98 |
| F3 | attributed rationality *β* | 0.98 | 0.94 | 0.13 | 0.97 |
| F3 | knowledge prior *κ* | 0.97 | 0.82 | 0.18 | 0.98 |
| F4 | open-world prior, manuals *ρ*<sub>M</sub> | 0.99 | 0.96 | 0.03 | 0.99 |
| F4 | open-world prior, colleagues *ρ*<sub>C</sub> | 0.99 | 0.94 | 0.05 | 0.99 |
| F5 | linear prior *w* | 0.99 | 0.96 | 0.03 | 0.98 |
| F5 | likelihood weight *b* | 0.99 | 0.96 | 0.02 | 0.99 |

All pass. At 60 configurations, F4's confusion had read 0.32, a chance correlation, since its two parameters have disjoint items; at 200 it is 0.03–0.05.

**What this does and does not establish.** If a configuration answers like one of these observers, its profile (eleven parameters over five families) can be recovered and the parameters told apart, from the stage A and B sessions (and nearly as well from stage A alone). It does not establish that real configurations answer like these observers. Stage A's anchors, shared-answer check and openness-against-spread per item, and the fits' report noise, are the first evidence on that.

**Screen validation, tasks 0.27** (same file):
- **Contrast reliability:** 0.90–0.99, all contrasts monotone in their parameters.
- **Calibration** (200 datasets):
  - stage A without differences: 0–6%;
  - stage B with session states only: 2.5–6% (limit 8.1%);
  - stage A with differences: 91.5–98%.

**Task validation 0.27.** It passed on both seeds: 3,288 cases and 142 contexts. The screen contexts have their anchors within 5 points and their contrasts within 0.3 of the noiseless scores; the largest error is 0.10.
- Fingerprint `4491e2d5e1e270645532f4467677f1e7ebffba911d3b13c2cdef8075cfa6c1f0`.
- Seed 20260927: `f217dfc292012417ea2778a2fd38cb9782ffac52e35ded5a74e6573b497216af`.
- Seed 20261027: `7f09b896f5d64842c7a1f6cb50e9c8b09c764ba66f7640af838161171a145e44`.

### Stage A (planned, awaiting your go-ahead)

**Sessions.** Preset `screen-a`, tasks 0.27.0 validated on both seeds. Astra, Sol, Astra-low, Sol-low, Luna and Terra each take form `a` of all five families. That is 30 sessions.

**Limits.** 1,800 seconds per run and a cap of 20 million tokens (11–15 million expected).

**Analysis:**

```bash
uv run python -m epistemics.ledger screen-a <root> --output <file>
```

It reports per family:
- the contrasts' scores, spread, noise, *δ* and checks;
- anchor failures;
- the share of items all configurations answer the same;
- openness against observed spread per item;
- the stage B groups;
- the exploratory commitment scores and their correlations across families.

**Stage B** would use the groups `screen-a` writes: form `b` for the families that pass, about 2–3 million tokens each.

### Stage A results (1 October)

All 30 sessions completed with no errors: 14.1 million input tokens (about 0.47 million per session), 27 minutes. The collection is in `output/screen-stage-a-20261001`.

```bash
uv run python -m epistemics.ledger screen-a output/screen-stage-a-20261001 --output output/screen-stage-a-summary-20261001.json
```

**By the criteria fixed in advance, four families pass: F1, F2, F4 and F5.** In no family did all six configurations give the same answer to any open item (shared-answer share 0.00 everywhere).

| Family | Contrast | Spread | Noise | *δ* | Departing | Passed |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | rule reliance | 1.06 | 0.69 | 0.78 | 3 | no (spread) |
| F1 | tightening | 0.59 | 0.24 | 0.31 | 3 | **yes** |
| F2 | halo, people | 0.41 | 0.29 | 0.27 | 1 | no |
| F2 | halo, instruments | 0.72 | 0.22 | 0.28 | 4 | **yes** |
| F3 | skip informativeness | 0.70 | 0.06 | 0.49 | 3 | checks pass, but anchors fail |
| F3 | knowledge attribution | 0.42 | 0.12 | 0.30 | 1 | no (guard) |
| F4 | residual mass | 0.94 | 0.17 | 0.29 | 4 | **yes** |
| F4 | source | 0.64 | 0.29 | 0.30 | 3 | **yes** |
| F5 | linearity | 1.43 | 0.09 | 0.27 | 3 | **yes** |
| F5 | conservatism | 1.64 | 0.11 | 0.25 | 3 | **yes** |

**F3 fails on an anchor, through its wording, not comprehension.**
- All six configurations answered the two "already knew" anchors (a test recorded "an hour earlier") at 0.94–0.97, not 1.00: an hour leaves a little room for change.
- Astra-low's 0.94 is 6 points off, against a tolerance of 5, so by the rule F3 does not go to stage B.
- The fix is wording that makes the anchor determinate (for example, the check finished moments before). That needs a new implementation and its own collection of F3.

**What differs:**
- **Luna is at an extreme in most families:**
  - the highest rule reliance (F1, 3.85);
  - the most literal reading of people's round numbers (F2);
  - the most closed-world reading of lists (F4, residual −3.11);
  - certainty in every extrapolation (F5: 1.00 on 19 of 20 items).
- **Within GPT-6:**
  - Sol and Sol-low treat a colleague's list as much less complete than a manual's (F4 source 1.44 and 1.51, against 0.43 and −0.12 for Astra and Astra-low);
  - Sol is the most conservative extrapolator (F5);
  - low effort reads instruments less literally (F2: −2.38 and −2.45, against −3.15 and −3.19 at medium effort).

**Profile fits (descriptive, form a only; not part of the stage A criteria).** Each family's observer was fitted to each session. The fitted report noise is the check on whether the observer describes the answers: simulated respondents had 0.1–0.5.

| Family | Report noise (6 configurations) | Reading |
| --- | --- | --- |
| F3 | 0.28–0.31 (Luna 0.78) | Fits. Attributed rationality *β*: Astra 3.1, others about 7.6, Luna 12. Knowledge prior *κ*: 0.20–0.28, Luna 0.58 |
| F4 | 0.29–0.80 | Fits moderately. Open-world prior for manuals 0.06–0.29, for colleagues 0.21–0.38 |
| F1, F2, F5 | 0.72–0.80 (the grid's top is 0.8) | Do not fit. Parameters sit at the grid's edges: F5's likelihood weight about 5 for five of six, F1's sampling near 0 |

The differences are there, but in F1, F2 and F5 the observers as specified do not describe how these configurations answer, so their parameters are not yet usable as profiles. This is the limit stated under [Profile recovery](#profile-recovery-tasks-027): recovery holds only if agents answer like the observers. The misfit has two visible forms:
- **Compression:** GPT-6's F5 answers sit between 0.55 and 0.85 whatever the item.
- **Certainty:** Luna's F5 answers are 1.00.

Neither is a pattern the F5 observer can produce.

**The exploratory commitment index was mis-oriented for F5.** It counted the straight line as the simplest model. On geometric series, though, the compact rule that fits is the exponential; Luna committed to it completely, which the index scored as low commitment. With six configurations and Luna at an extreme in most families, the cross-family correlations (−0.93 to 0.85) are not interpretable.

### Revised observers (written before stage B was analysed)

`ledger/screen_fit.py`. These are analysis-side only: the tasks and the frozen implementation are unchanged, and stage B was collected on fingerprint `4491e2d5`.

**What stage A's misfit showed:**
- **Defaults when the model is open:**
  - with a single example in F1, most configurations answered exactly 0.50;
  - Terra answered 0.50 to many F1 items;
  - Luna answered 0.85 to every F2 item and 1.00 to almost every F5 item;
  - GPT-6's F5 answers sat between 0.55 and 0.80 whether a series grew ×2 or ×1.5 (the observer predicted 0.86 against 0.33).
- **F2's round numbers:** answers depended on the window's size relative to the number (200 against 500, for example), which fixed-unit rounding cannot produce.

**The revision:**
1. **Model trust, every family.** On open items, the reported probability is (1 − *m*)·*p*<sub>observer</sub> + *m*·*d*: Bayesian model averaging over "the family's model applies" and an uninformative model whose answer is the fallback *d*. Anchors state their model and are not fitted. *m* is a formal candidate for the cross-family commitment trait: low *m* commits to the family's model.
2. **F2:** a rounded report comes from a bin proportional to the number (width 0.2 × the value), not a fixed unit.
3. **F5:** the assumed process noise is a parameter (0.01–0.3, log scale), so certain extrapolation is expressible.

**In-sample on stage A** (form a; the evidence gain is in log units, with flat priors over the grids):

| Family | Evidence gain | Report noise, original → revised |
| --- | --- | --- |
| F1 | +1.6 to +17.1 | 0.80 → 0.52–0.80 |
| F2 | +0.5 to +54 | 0.72–0.80 → 0.10 (Luna) and 0.55–0.80 |
| F3 | +0.1 to +19 | 0.28–0.78 → 0.10–0.37 |
| F4 | −1.4 to +2.4 | about unchanged |
| F5 | +5.5 to +242 | 0.46–0.80 → 0.28–0.80 |

F1 and F2 remain poorly fitted for most GPT-6 configurations.

**Evaluation on stage B, fixed now:**
1. **Held-out prediction.** Each observer, original and revised, is fitted to a configuration's form a answers and predicts its form b answers (log-odds RMSE on the open items). The revision is supported where its held-out error is lower for most configurations.
2. **Fits to both forms:** report noise and evidence, original against revised.
3. **Recovery of the revised observers** (trust and fallback included), with the profile-recovery criteria: `output/screen-revised-recovery-20261001.json`.

The stage B reliability test of the contrasts is as preregistered, and is independent of these models.

### Stage B results (1 October)

All 24 sessions completed with no errors: 11.3 million input tokens, 24 minutes, on the frozen implementation (`4491e2d5`). The collection is in `output/screen-stage-b-20261001`.

```bash
uv run python -m epistemics.ledger screen-b output/screen-stage-a-20261001 output/screen-stage-b-20261001 --output output/screen-stage-b-summary-20261001.json
```

**By the preregistered test, F5 passes** on linearity: ICC 0.80, *p*<sub>Holm</sub> 0.011, retest *r* 0.78.

| Family | Contrast | ICC | *p* | *p*<sub>Holm</sub> | Retest *r* |
| --- | --- | --- | --- | --- | --- |
| F1 | rule reliance | 0.35 | 0.27 | 0.53 | 0.35 |
| F1 | tightening | 0.48 | 0.17 | 0.50 | 0.48 |
| F2 | halo, people | 0.98 | 0.020 | 0.14 | 0.98 |
| F2 | halo, instruments | 0.78 | 0.038 | 0.19 | 0.74 |
| F4 | residual mass | 0.90 | 0.031 | 0.19 | 0.89 |
| F4 | source | −0.13 | 0.68 | 0.68 | −0.24 |
| F5 | linearity | **0.80** | **0.0014** | **0.011** | 0.78 |
| F5 | conservatism | 0.90 | 0.049 | 0.20 | 0.89 |

- **Consistent but not certified:** four more contrasts rank the configurations consistently across forms (ICC 0.78–0.98), but do not survive the correction.
- **Why the bar is high:** with six configurations, the permutation test's smallest possible *p* is 1/720, and Holm across eight contrasts then requires an almost perfect ordering.
- **Not consistent:**
  - F1, whose stage A differences did not hold across forms;
  - F4's source contrast: Sol's stage A difference (colleagues' lists treated as less complete) did not replicate (1.44 → 0.51, Sol-low 1.51 → 0.03).

**Revised observers on the held-out form.** Each observer was fitted to form a and predicted form b (log-odds RMSE; the evaluation fixed before stage B was analysed):

| Family | Revised better | RMSE, original → revised |
| --- | --- | --- |
| F1 | 5 of 6 | 0.81–2.91 → 0.72–2.53 |
| F2 | 6 of 6 | 1.09–1.40 → 0.72–1.15 |
| F4 | 3 of 6 | unchanged (0.52–1.00) |
| F5 | 6 of 6 | 0.90–4.15 → 0.45–2.49 |

The revision generalises rather than overfits: it predicts unseen items better. But the fits to both forms still leave large misfit for most configurations in F1 and F2, and for three in F5 (report noise at the grid's top, 0.8).

**Recovery of the revised observers** (`output/screen-revised-recovery-20261001.json`, 150 configurations). The mixture trades off against the family parameters, and several fail the profile criteria with both forms:

| Family | Failures |
| --- | --- |
| F3 | trust *r* 0.40; knowledge prior *r* 0.70, confused with the fallback (0.42) |
| F5 | likelihood weight *r* 0.49; fallback *r* 0.34 |
| F2 | fallback *r* 0.60; people's exact prior *r* 0.74 |
| F1 and F4 | hold (0.78–0.95) |

**Where this leaves separable profiles:**
1. **Reliable differences exist:** a certified one for F5 (exponential growth bias), and consistent ones (ICC 0.78–0.98) for F2's two halos, F4's open-world prior and F5's conservatism.
2. **The original observers are separable but do not describe the answers.** The revised ones describe them better, including on unseen items, but are not separable from two sessions.
3. **The missing ingredient is information about the fallback process itself.** Open-looking items whose observer answer is nearly fixed whatever the parameters (low openness, no stated rule) would show how much a configuration falls back on a default, and would pin trust and fallback separately from the family parameters.
4. **Six configurations from two model families are few for stage B.** Adding the high-effort GPT-6 configurations would make eight.

### Fallback round: design and preregistration (1 October, before collection)

**You agreed:** add fallback items for F2, F4 and F5, and two more configurations. Model 0.18.0, design 0.19.0, tasks 0.28.0.

**Form c** (`screen-num-c`, `screen-lists-c`, `screen-trend-c`). Each has fallback items, a few open items and 4 anchors.

The fallback items look like the open items but have a fixed answer under the revised observer, whatever its parameters (openness at most 0.3; largest 0.21):

| Family | Fallback items | Open items |
| --- | --- | --- |
| F2 | 16, at 0.5 ("more than the stated value", symmetric under the speaker model), about 1 (windows of ±50%) and about 0 (windows far from the stated value) | 4 |
| F4 | 16, at 0.2–0.8: "if the cause was one of the listed causes, what is the probability that it was X (or X or Y…)?", which is *j*/*k* by symmetry | 4 |
| F5 | 12, at about 1, about 0 and 0.5 (proportional lines asked about their projection at 3.5) | 8 geometric series at 1.5× and 2× the linear projection |

**Canonical observers (model 0.18).** The revised observers now live in `dispositions/screen.py`:
- **F2:** rounding proportional to the number;
- **F5:** diagnosticity is the assumed process noise alone (likelihood weight 1). With both free, the likelihood weight was not recoverable (*r* 0.35, confused 0.46 with noise).
- **Fallback:** the trust and fallback mixture is fitted in `ledger/screen_fit.py` on 11 × 11 grids. With 6 × 6, values falling between grid points biased F5's noise (coverage 0.70).

**Recovery gate** (`output/screen-revised-recovery-c-20261001.json`, 200 configurations, forms a+b+c; criteria *r* ≥ 0.8, coverage ≥ 0.8, confusion ≤ 0.3). It passes for 13 of 14 parameters:

| Family | Parameters | *r* | Coverage | Largest confusion |
| --- | --- | --- | --- | --- |
| F2 | *π*, *π*<sub>I</sub>, *ε* | 0.89–0.93 | 0.92–0.93 | ≤ 0.16 |
| F2 | trust, fallback | 0.99, 0.96 | 0.92 | ≤ 0.18 |
| F4 | *ρ*<sub>M</sub>, *ρ*<sub>C</sub> | 0.93, 0.96 | 0.94–0.95 | ≤ 0.16 |
| F4 | trust, fallback | 0.97, 0.93 | 0.91–0.94 | ≤ 0.13 |
| F5 | process noise | 0.98 | 0.85 | 0.15 |
| F5 | trust, fallback | 0.98, 0.97 | 0.84–0.89 | ≤ 0.10 |
| F5 | linear prior *w* | **0.79** (fails, against 0.8) | 0.86 | 0.10 |

- **What form c adds:** without it (forms a and b only), trust and fallback recover at 0.56–0.79 for F2 and F5. Form c is what makes the mixture separable.
- **F5's linear prior** is borderline (0.79 here; 0.86 in a 120-configuration check). It is recorded as a failure, and its profile values will carry that caveat; the design was not tuned further to pass it.

**Task validation 0.28.** It passed on both seeds: 3,360 cases and 145 contexts. The fallback contexts are within 0.3 of the observer's fixed answers; the largest error is 0.13.
- Fingerprint `a709e539ab70c4a7a5b48be3c96dd4e163bc8f8abb8ebd1c332d6b4afc836883`.
- Seed 20260927: `407c65979598646e1128dab4a9e6a09fa110ca98d3bf54e3a7e7487b2c6abc6e`.
- Seed 20261027: `29e179dc62ebfba1bb3ace57249ec4dd65f46c0db76528c7a197e6be704145cc`.

**Collection** (preset `screen-c`, 36 sessions, cap 25 million tokens):
- **New configurations:** Astra-high and Sol-high on forms a and b of F2, F4 and F5 (12 sessions);
- **Form c:** all eight configurations (24 sessions).

**Analyses fixed now:**
1. **Stage B with eight configurations.** For F2, F4 and F5, the stage B test (consistency ICC across forms a and b, configuration labels permuted within forms) on all eight configurations, Holm across these families' six contrasts. Pass: ICC ≥ 0.5, *p*<sub>Holm</sub> < 0.05, retest *r* > 0.
2. **Is the fallback constant?** For each configuration and family, trust and fallback are fitted to the form c fallback items alone (where the observer's answer is fixed), and separately to forms a and b under the revised observer.
   - Fallback on the fixed items (trust's 90% interval above 0.1) where forms a and b show it means a constant fallback.
   - Trust near 0 on the fixed items while forms a and b show trust > 0.25 means the fallback is triggered only by open cases, and the mixture model is wrong in form.
3. **Profiles.** The revised observers fitted to forms a+b+c per configuration, with parameters, intervals and report noise. A profile is reported as fitted where report noise is at most 0.5.
4. **Held-out check.** Fit to forms a and c, predict form b (log-odds RMSE), against the stage B held-out figures.

### Fallback round results (1 October)

All 36 sessions completed with no errors: 17.0 million input tokens, 41 minutes. The collection is in `output/screen-fallback-20261001`. The analyses are in `output/screen-fallback-analysis-20261001.json`, from `ledger.screen.stage_b(..., families=("num", "lists", "trend"))`, `screen_fit.fallback_test`, `screen_fit.profiles(..., fit_forms=("a", "b", "c"))` and the held-out fit a+c → b.

**1. Stage B with eight configurations: four contrasts pass (Holm across six).**

| Family | Contrast | ICC | *p*<sub>Holm</sub> | Retest *r* | Passed |
| --- | --- | --- | --- | --- | --- |
| F2 | halo, people (literal reading of people's round numbers) | 0.97 | 0.019 | 0.97 | **yes** |
| F2 | halo, instruments | 0.71 | 0.057 | 0.68 | no |
| F4 | residual mass (open-world prior) | 0.88 | 0.021 | 0.87 | **yes** |
| F4 | source | −0.05 | 0.63 | −0.14 | no |
| F5 | linearity (exponential growth bias) | 0.79 | 0.004 | 0.78 | **yes** |
| F5 | conservatism (extrapolation spread) | 0.91 | 0.032 | 0.90 | **yes** |

These are the screen's positive findings: reliable differences between configurations, on two forms with different surfaces, in three families.

**2. The fallback is triggered by open cases, not constant.**
- **On the fallback items:** trust is 0.00–0.11 in all 24 configuration-family cells. Configurations answer fixed-answer items as the observer does: exactly *j*/*k* in F4; 0.5, 0.95–0.99 and 0.01–0.04 in F2.
- **On the open items:** forms a and b show trust of 0.20–0.81 in most cells.
- **Verdicts:**
  - 9 "triggered by open cases";
  - 11 "undetermined": fixed-item trust is about 0.1, its interval reaching down to 0.05; this is an edge of the grid's resolution, and the substance is the same as triggered;
  - 4 "no fallback on open items";
  - none constant.

The mixture model with a constant trust is therefore wrong in form: the configurations hedge towards a default only when the case leaves the model open.

**An unforeseen reading in F5.** Asked whether a proportional line will be above its own projection at 3.5, the observer says 0.5 whatever its noise. But:
- Luna answered 0.00, and Sol-low about 0.16: they treat the line as exact, so the reading will be exactly the projection and "above" is false;
- Terra, Sol and Sol-high answered 0.48–0.50.

This is a belief in a deterministic process (a point mass), which an observer with continuous noise cannot express.

**3. Profiles (forms a+b+c, revised observers).** Report noise is at most 0.5 for:
- F4, 7 of 8 configurations (not Sol: 0.80);
- F2, 1 of 8 (Luna);
- F5, 2 of 8 (Astra-high 0.50, Astra 0.52).

So only F4 yields fitted profiles:

| Configuration | Open-world prior, manuals | Open-world prior, colleagues |
| --- | --- | --- |
| Luna | 0.05 | 0.11 |
| Terra | 0.12 | 0.31 |
| Sol-high | 0.13 | 0.35 |
| Sol-low | 0.20 | 0.34 |
| Astra | 0.22 | 0.35 |
| Astra-high | 0.28 | 0.37 |
| Astra-low | 0.30 | 0.37 |

Every configuration treats a colleague's list as less complete than a manual's, by 0.07–0.19. That shared difference is why F4's source contrast shows no differences between configurations. The level of the open-world prior differs: Luna closed, the Astra family most open.

**4. Held-out (fit forms a+c, predict form b; log-odds RMSE):**
- F4: 0.53–0.85;
- F2: 0.78–1.13;
- F5: 0.00 (Luna) to 1.81.

These are similar to the stage B figures for F2 and F4, and mixed for F5.

**Where this leaves profiles:**
- **Reliable differences:** four contrasts in three families.
- **Bayesian profiles:** fitted for F4 only. In F2 and F5 the observers, even with a fallback, do not describe the answers, for two reasons the fallback round identified:
  - the fallback depends on how open the case is;
  - some configurations believe in deterministic processes.
- **The next model:** (a) a fallback whose weight grows with the observer's own uncertainty on the item, and (b) in F5, a prior probability that the process is exact. Both can be fitted to the data already collected and judged by held-out prediction across forms. But they are being developed on these data, so a fresh form would be needed to confirm them.

### Observers v3 (1 October, developed on the collected data; exploratory)

`ledger/screen_fit3.py`; results in `output/screen-observers-v3-20261001.json` and `output/screen-observers-hybrid-20261001.json`. These models were developed after seeing the fallback round, so their fit to these data is exploratory, and confirming any of them needs a fresh form.

**Two changes, tested separately.**

**1. Uncertainty-triggered fallback (rejected).** The weight on the fallback is *m*·*o*<sub>*i*</sub>/(*o*<sub>*i*</sub> + 1), where *o*<sub>*i*</sub> is item *i*'s openness, so fixed items get none.
- **F2:** worse for all eight configurations (log evidence −25 to −46; held-out RMSE up).
- **F4:** marginal (+1 to +3; held-out unchanged).
- **Recovery:** with the fallback confined to open items, it trades off against the family parameters again (F2 fallback *r* 0.63; F5 trust 0.63 and linear prior 0.64).

The descriptive finding stands (configurations do not hedge on fixed-answer items), but F2's misfit on open items is not a pull towards a common default. The F2 observer itself misses something, for example GPT-6's nearly flat answers on sharp numbers.

**2. Deterministic processes in F5 (supported).** With prior *δ*, the process is taken as exact: a point mass at the projection of the function family that fits the readings exactly, so "above" is strictly false at the projection itself.

Combined with the constant fallback of model 0.18 (the "hybrid"):

| Configuration | *δ* | Report noise, v2 → hybrid |
| --- | --- | --- |
| Luna | 1.00 | 0.80 → 0.50 |
| Sol-low | 0.72 | 0.80 → 0.80 |
| Terra | 0.63 | 0.80 → 0.80 |
| Astra-low | 0.60 | 0.58 → 0.50 |
| Astra-high | 0.56 | 0.50 → 0.50 |
| Astra | 0.53 | 0.52 → 0.50 |
| Sol-high | 0.43 | 0.80 → 0.79 |
| Sol | 0.41 | 0.80 → 0.80 |

- **Fit:** log evidence improves for all eight configurations (+2.1 to +79.1). Held-out RMSE improves for 5 of 8 on form a and 4 of 8 on form b.
- **Recovery (200 configurations):** *δ* *r* 0.86, trust 0.98, fallback 0.96, all passing. But the linear prior (0.67) and process noise (0.71) fail: determinism absorbs part of what they explained.

**Where profiles stand after v3:**
- **F4:** fitted and separable (open-world priors and fallback), for 7 of 8 configurations.
- **F5 (hybrid):** a separable determinism parameter and fallback; the linear prior and noise are not separable.
- **F2:** separable in simulation, but not fitted (report noise 0.8 for 7 of 8).

The candidate traits with reliable differences remain the four stage B contrasts.

