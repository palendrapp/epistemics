# Battery v3: general traits in weak situations (design note)

Design, 30 September 2026. Nothing is built or collected. The decisions for you are listed at the end.

## Why

**The record so far.** Every battery so far has looked for general traits. One construct transferred: stated–applied fidelity, the gap between a stated rate and the rate a configuration's forecasts implied, at the level of model families. Every other candidate either sat at the normative ceiling or was specific to its surface. The confidence transfer test was the latest: verbal confidence separated Sol from Astra, but on one surface only ([results](confidence-transfer-preregistration.md#results-30-september)).

**The designs themselves were a limit.** Three features of them, in particular:

1. **Strong situations.** Our explicit tasks state the evidence, its structure and the question, then ask for a probability. Strong situations, in the sense of clear norms, suppress individual differences (Mischel 1977). Frontier configurations answer them exactly, however much arithmetic or structure is loaded on.
2. **Few surfaces, measured very reliably.** Where variance appeared (defaults, noticing, how a hedge is read), it depended on how a configuration read one kind of text. Stable if–then signatures that are specific to their situation are the expected form of dispositions (Mischel & Shoda 1995). A general trait is the common factor across many heterogeneous items (generalizability theory; Cronbach et al. 1972). We measured 4–6 items very reliably, where a trait needs many.
3. **Load of the human kind.** For a reasoning agent, working memory within a case is effectively unbounded. Agents are more plausibly limited over a trajectory: clutter, distance, compression. Those were not loaded.

**Sizing the third point.** A reanalysis of every existing session with a normative answer per case (`ledger position`: 52 sessions, 1,248 answers) found no effect of position in the session.
- **GPT-6:** exact on 96–98% of cases in each third of the session; slope −0.01 log-odds over 24 cases (*p* = 0.09).
- **GPT-5.6:** +0.09 (*p* = 0.20).
- **No module** has a reliable slope.
- **Context size:** a session's cumulative input is about 0.5 million tokens, but its context at the last case is only of the order of 30 thousand. Trajectory load has not been tested at the scale where agents might be limited.

## The construct: coherence between stated and revealed belief

**Reasons for choosing it.**
- **It transferred.** It generalises the only construct that has transferred so far.
- **It works in weak situations.** It is measured against the agent's own statement, not an external norm, so it stays well defined however underdetermined a situation is. Our open variants, by contrast, could only report defaults.

**Measurement.** Each scenario is presented twice in a session, at different positions:
- **Stated belief:** "What is the probability that H?" (a probability).
- **Revealed belief:** "A bet pays 100 points if H and nothing otherwise. What is the smallest sure number of points you would accept instead of the bet?" (points, 0–100). This is a certainty equivalent, a standard belief-revealing measure (Charness, Gneezy & Rasocha 2021).
- **Calibration for risk attitude:** each session also has four calibration lotteries with stated probabilities (for example, "a bet that pays 100 points with probability 60%"). These fit the configuration's mapping from probability to certainty equivalent, so revealed beliefs are read through it, not through an assumed risk neutrality (the logic of Holt & Laury 2002).

**Model.** For scenario *i*, with stated log-odds *s<sub>i</sub>* and revealed log-odds *r<sub>i</sub>* (the certainty equivalent inverted through the session's calibration):

*r<sub>i</sub>* = *α* + *β*·*s<sub>i</sub>* + *e<sub>i</sub>*, with *e<sub>i</sub>* ~ N(0, *τ*<sub>c</sub>²)

| Trait | Meaning | Coherent value |
| --- | --- | --- |
| *β*, coupling | How strongly actions follow stated beliefs | 1 |
| *α*, offset | Actions systematically bolder or more cautious than the statements | 0 |
| *τ*<sub>c</sub>, incoherence | Scatter between saying and doing | 0 |

The stated answers keep their own fits (report noise, and ideal answers in strong scenarios). A configuration that computes exactly but acts inconsistently is then distinguishable from one that is uncertain.

## Frame 1: many surfaces (within sessions)

**The surface generator.** About 36 surfaces: 6 domains × 6 source types.
- **Domains:** urns, machine faults, shipment quality, species presence, service outages, market demand.
- **Source types:** instruments, witnesses, written reports, logs and databases, automated agents, analysts.

Every surface renders the same abstract scenario: a binary hypothesis with a prior, and 1–4 sources whose properties (accuracy, dependence, relevance) are specified to the degree the situation strength sets. Wording is templated per surface and audited as before.

**Session layout.**
- **Per session:** 12 scenarios from 12 different surfaces, each presented twice (stated and revealed), plus 4 calibration lotteries. That is 28 trials.
- **Across sessions:** every surface is covered for every configuration.
- **Order:** random, with the separation between a scenario's two trials recorded.

**Analysis.** Variance components for each coherence parameter:
- configuration;
- surface;
- configuration × surface;
- residual.

The primary quantity is **generality**: the share of configuration variance in configuration plus configuration × surface variance.

## Frame 2: situation strength (within sessions)

Each scenario has a strength level, balanced within a session:

| Level | Evidence | Relevance | Response context |
| --- | --- | --- | --- |
| Strong | The generative model fully stated | Only relevant sources | Plain |
| Intermediate | One property unstated (a source's accuracy, or whether it depends on another) | One irrelevant source mixed in | Plain |
| Weak | Two or more properties unstated | Irrelevant and mutually inconsistent sources | Payoff framing |

**Weak is not misleading.** Unstated properties and distractors are balanced so that, averaged over the design, they point to neither hypothesis. An audit checks this against the ideal answers computed under each completion of the unstated properties.

**The prediction** (Mischel): configuration differences in coherence grow as situations weaken. That is a secondary test, and a check that the battery is measuring dispositions, not noise.

## Secondary: stakes, an early probe of motivated updating

In half the weak scenarios, the decision is framed inside an assigned task: "Your assigned task can proceed only if H." Two shifts are measured, relative to matched scenarios without stakes (the optimism-bias paradigm; Sharot, Korn & Dolan 2011):
- the shift of revealed belief towards the goal-congruent hypothesis;
- the shift of stated belief.

This is deliberately light. If the shifts are large, motivated updating gets its own battery.

## Between sessions: trajectory load

Two conditions, the same scenarios:

| Condition | The revealed-belief trial | Context |
| --- | --- | --- |
| Standard | Re-shows the scenario | As now (about 30 thousand tokens at the end) |
| Loaded | Refers back ("For the machine in case 5…") without re-showing it, 6–12 trials after the stated trial | Each trial carries about 8 thousand tokens of irrelevant logs, so the context passes 200 thousand tokens |

**The test.** Coherence decay with distance and context size, per configuration: whether *τ*<sub>c</sub> rises and *β* falls under load. This is where a capacity limit specific to agents would show: the action drifts from the belief the agent stated earlier.

**Cost.** Loaded sessions are expensive. Each turn resends the context, so cumulative input grows roughly with the square of the context: about 3–5 million tokens per session, against 0.5 million now.

## The primary test (to be preregistered)

**Generality of coherence.** Split the surfaces into random halves, many times over. In each split, correlate the configurations' coherence parameters between the halves. The primary statistic is the mean split-half correlation, with a permutation *p* that shuffles configurations within surface. This is a leave-many-surfaces-out version of the transfer test that uses all 36 surfaces.

**Pass:** the mean split-half correlation of *τ*<sub>c</sub> or *β* is above 0 with *p* < 0.05, Holm-corrected across the two. The primary test uses standard sessions only.

**Secondary tests.**
1. Configuration variance by situation strength (widening as strength falls).
2. The stakes shifts.
3. Coherence decay under load.
4. Generality of the stated-answer fits (report noise, and bias in weak scenarios) as a comparison.

## Subjects

Eight configurations, as before. More model families would add the variance where traits have appeared, but they need other agent command-line tools under the same runner: an infrastructure decision, separate from this design.

## Build and validation

1. **Surface generator:** 36 surfaces, each rendering the scenario grammar at three strengths. Wording audits: no unstated property is described, and distractors are uninformative by construction.
2. **The balance audit for weak scenarios** (see above).
3. **Observers:** the ideal answers for strong scenarios, and for each completion of the unstated properties in weaker ones.
4. **Response format:** the certainty-equivalent trial, the calibration lotteries, and the referring-back trials for the loaded condition. This is new, because a trial currently shows its own case.
5. **Fits:** the calibration fit (the probability-to-certainty-equivalent mapping), the coherence model, and variance components.
6. **Recovery and power at the design's size**, with gates fixed in advance, before preregistration.
7. **Task validation** on two seeds.

## Pilot and cost (provisional)

| Stage | Sessions | Tokens |
| --- | --- | --- |
| Pilot: Astra, Sol, Luna and Terra × 3 standard sessions | 12 | about 6 million |
| Pilot: the same four × 1 loaded session | 4 | about 15–20 million |
| Battery: 8 configurations × 6 standard sessions (every surface covered twice) | 48 | about 25 million |
| Battery: 8 × 2 loaded sessions | 16 | about 60–80 million |

The loaded condition dominates the cost. It could run on a subset of configurations, or after the primary test.

## Risks

- **Coherent at ceiling.** If every configuration acts exactly on its statements even in weak scenarios, coherence is not a trait. That would be informative in its own right: the one transferring construct would have been specific to rates.
- **Risk attitude against belief.** The calibration lotteries separate them only if the probability-to-certainty-equivalent mapping is stable within a session. The pilot checks that.
- **Uneven surfaces.** Some generated surfaces may be read in unintended ways. The wording audits and surface variance components catch the worst; the pilot shows the rest.
- **Load cost.** See above.

## Decisions for you

1. **Construct and frame:** coherence, within many surfaces × situation strength (recommended).
2. **Stakes:** as a light secondary manipulation in weak scenarios (recommended), or deferred.
3. **Trajectory load:** in the pilot on four configurations (recommended), in the battery on a subset, or deferred until coherence is shown to generalise.
4. **Budget:** the pilot at about 21–26 million tokens with the loaded sessions, or about 6 million without them.
