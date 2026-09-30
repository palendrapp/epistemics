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

## Built (30 September)

**Versions.** Model 0.13.0 and design 0.14.0 (`dispositions/coherence.py`); tasks 0.23.0 (`disposition_tasks/surfaces.py`, modules `coherence-a` to `coherence-f`, variants `v3-standard` and `v3-loaded`).

**Changes from the design above.**
- **Surfaces and session length.** There are 30 surfaces (5 domains × 6 source types, without the urn domain), and 10 scenarios per session, not 12. The collection service's session is 24 trials: 10 scenarios × (stated, revealed) + 4 lotteries. Six designs each hold 10 scenarios, and every surface appears in two designs at two different strengths.
- **The weak level has no separate payoff framing,** because the certainty-equivalent trial already carries the payoff. Stakes are in 2 of the 4 weak scenarios per design (12 in all), with the goal-congruent hypothesis balanced (6 and 6).
- **Unstated properties are stated as unknown,** not simply left out: "No accuracy figure is available for sensor B14", "sometimes relays sensor A14's reading".

**Checks built into the design and the audit.**
- **Situation strength grades how much unstated properties matter.** Over independent completions of every unstated property (accuracies 0.6, 0.75 and 0.9; copy rates 0.2 and 0.5), the ideal answer's span in log-odds is:
  - strong: 0;
  - intermediate: median 1.25 (0.20–1.79);
  - weak: median 2.08 (1.06–3.58).
- **Balance.** Across the battery, the sources with unstated accuracy report the hypothesis 20 times and its negation 25; copy pairs with an unstated rate, 11 and 10; stakes, 6 and 6. The audit allows a difference of at most 2 or 15% of the total.
- **Copy pairs agree when their rate is unstated,** so the rate always bears on the answer.
- **Every trial shows exactly the percentages its scenario states,** and no others.
- **Loaded revealed-belief trials** show no evidence and refer back by name.
- **The runner orders loaded sessions** so that each revealed trial comes 6–12 trials after its stated one (the `refer-back` policy, required for and only allowed with `v3-loaded`).
- **Load size.** A loaded trial carries about 8,500 tokens of unrelated log lines.

**Fits** (`coherence.fit_coherence`, in every v3 analysis):
- **Calibration:** the risk exponent *ρ* for utility *x*<sup>*ρ*</sup>, from the four lotteries (probabilities 0.2–0.8).
- **Revealed log-odds:** the certainty equivalent inverted through *ρ*.
- **The coherence line** (*α*, *β*, *τ*<sub>c</sub>).
- **Each pair's distance in trials.**
- **The stated answers' error** against the ideal in strong scenarios.

The ledger pools pairs per configuration (`ledger battery-v3`) and runs the split-half generality test, with Holm correction across *β* and *τ*<sub>c</sub>.

**Recovery** (`ledger battery-v3-recovery`): 100 simulated configurations, six sessions each, with a configuration × surface interaction of 0.1.

| Parameter | Correlation with truth | Mean absolute error |
| --- | --- | --- |
| *β* | 0.99 | 0.02 |
| log *τ*<sub>c</sub> | 0.93 | 0.25 |

Recovery SHA-256: `88f8d325f2d37afa255ce1d631570a7897187c7e4a12a5031ba2af34d8afaf83`.

**Power** (`ledger battery-v3-power`): 8 configurations × 6 sessions, 100 data sets per scenario. The assumed spread between configurations is 0.15 for *β* and 0.4 for log *τ*<sub>c</sub>.

| Scenario | Pass rate | Median split-half *r* (*β*, *τ*<sub>c</sub>) |
| --- | --- | --- |
| General (interaction 0.1) | 1.00 | 0.96, 0.82 |
| General, strong interaction (0.3) | 1.00 | 0.92, 0.46 |
| Surface-bound (no trait, interaction 0.3) | 0.03 | −0.02, −0.03 |
| None | 0.03 | 0.05, 0.04 |

Power SHA-256: `f330f96c422479242dcfa64e1d2e008fc73b19155a703d5530b50f34ecebb646`.

**The spreads are assumptions:** nothing is yet known about how much coherence varies between configurations. The pilot measures them.

**The pilot** (awaiting your go-ahead):
- **Standard:** Astra, Sol, Luna and Terra on designs a–c in `v3-standard`. That is 12 sessions, covering every surface once per configuration, about 6 million tokens.
- **Loaded:** one `v3-loaded` session each on design d. That is 4 sessions, about 3 million tokens each, so about 12 million, because context reaches about 220 thousand tokens and is resent every turn.
- **Total:** about 18 million tokens, cap 25 million.
- **A risk:** if the agent's command-line tool compacts its context near its limit, earlier evidence is summarised. That would itself be a compression load, but it would be recorded as a deviation.

**Task validation 0.23.** It passed on both seeds: 2,760 cases and 120 contexts. Twelve v3 contexts per seed (six designs × two variants, the loaded ones in refer-back order) recover a respondent with known coherence (*β* 0.8) and risk exponent (*ρ* 0.8) within tolerance: the largest error is 0.075.
- Fingerprint `aaf9f30f9fd571be4039d1f9cd65ec752bec13a90ddeb13227b7d8fa6094ae98`.
- Seed 20260927: `5bab4739918760ab8d7187d577dbf366c8f701f602da6e9772fb65b73e950cfb`.
- Seed 20261027: `14bf0ecb68dc2fab31038fc690105be445a96c1889324670f17ceecb8a4f849b`.

### Pilot (planned 30 September, before collection)

**Sessions.** Tasks 0.23.0, validations 0.23 on both seeds.
- **Standard:** Astra, Sol, Luna and Terra on `coherence-a`, `-b` and `-c` (`v3-standard`, random order). That is 12 sessions, covering all 30 surfaces once per configuration.
- **Loaded:** one session each on `coherence-d` (`v3-loaded`, refer-back order). That is 4 sessions.

**Limits.** 3,600 seconds per run and a cap of 25 million tokens. The collection is in `output/battery-v3-pilot-20260930`.

**Read-out** (range-finding, not the preregistered battery):
- the spread of *β*, *τ*<sub>c</sub> and *α* between configurations, which sets the power assumptions;
- coherence by strength, and the stakes shifts;
- coherence under load against standard;
- whether the calibration mapping is stable;
- tokens per session;
- whether any loaded session's context was compacted.

**Tasks 0.23.1 (before collection).** The first preparation of the pilot failed: the refer-back ordering used numpy's random interface, but preparation passes Python's `random.Random`. Nothing was collected; the partial root, containing only the implementation snapshot, is kept as `output/battery-v3-pilot-20260930-failed-prepare`. The ordering now uses only calls that both provide. A test now prepares a real loaded group, and the battery was re-validated on both seeds before the pilot.

### Pilot results (30 September)

All 16 sessions completed with no errors: 11.8 million input tokens, 17 minutes. Standard sessions used about 0.5 million tokens each; loaded ones used 0.9–2.4 million.

```bash
uv run python -m epistemics.ledger battery-v3 output/battery-v3-pilot-20260930 --output output/battery-v3-pilot-summary-20260930.json
```

**Coherence is at ceiling.** On every standard session:
- **Astra, Luna and Terra** answered every bet question with exactly 100 × their stated probability, and every lottery at its expected value (*β* 1.00, *α* 0.00, *τ*<sub>c</sub> 0.00, *ρ* 1.00).
- **Sol** did the same except in one session (*β* 0.94, *τ*<sub>c</sub> 0.05).
- **Across strengths:** the same at strong, intermediate and weak.
- **Stakes** shifted nothing (0.00).

Luna's closing message states the policy: "for lotteries, I used expected value". The certainty equivalent is not a revealed belief for these agents. It is one more explicit calculation, so the design placed the strong situation one step further on.

**The generality "pass" is an artefact, and the guard now says so.** The split-half test gives *r* 1.00 (*p* = 0.004), but the configurations do not differ: the between-configuration spread of *β* is 0.01, and no configuration departs from the others by more than 0.05. The statistic is driven by one Sol session. `ledger battery-v3` now marks generality as not interpretable unless at least three configurations depart from the median. It is not interpretable here.

**Load: one departure, under a confound.**
- **Luna's loaded session** decoupled: *β* 0.33, *τ*<sub>c</sub> 1.48, mean gap 1.04 log-odds. Its strong-scenario stated answers were also off (0.18).
- **Astra, Sol and Terra** were perfectly coherent under load.

Two problems qualify this.

1. **The battery's general instructions were not adapted for v3.** They say:
   - "Answer each question with a probability";
   - "Each case states the relevant probabilities, including how reliable each source is";
   - "Each case is separate… nothing carries over between cases".

   The last directly contradicts the loaded condition's back-references. Agents followed each trial's own instruction, but Astra and Luna both reported the conflict in their closing messages. This is a build error of mine.
2. **The load delivered was smaller than designed.** Loaded sessions used 0.9–2.4 million input tokens, where about 3.7 million were expected if every log stayed in context. The agent tool most likely shortened long tool outputs in its history. No compaction message was logged, so how much of each log the models saw is unknown.

**What the pilot shows.**
- **When a revealed-belief question states its payoffs, frontier agents compute it.** Coherence between an explicit probability and an explicit bet is not a trait of these configurations. The one construct that transferred before (stated against applied rates) was different: the application there was implicit, spread over forecasts.
- **The only candidate is coherence across a trajectory** (Luna's loaded session). It needs corrected instructions and a load the agent tool does not strip before it can be read.

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `5582835a147fe936809c9b2a1d8d2a38f75572aebfb3a95d7af6c085405a365b` |
| execution.json | `374b4f4142558b3bc2573229006c3cc1f3f8c1500f49d552d0afa6c3294ea394` |
| Summary (with the guard) | `1f9c4efc14a2bbf63640ddf26fafcf732ec42d933a3275397e0529478b264bd3` |

**Next, designed 30 September:** [battery v3.1, implicit decisions](battery-v3-1-design.md).
