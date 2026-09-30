# Multi-agent battery (Part C): a design note

Design, 30 September 2026. Nothing is built or collected. The decisions for you are listed at the end.

## Why

**The capacity battery closed a door.**
- Explicit load does not produce a graded capacity limit in GPT-6, whether arithmetic (16 readings) or structure (chains, conditions, two-source copies). Sol is exact at every effort.
- Astra errs on particular cases at every effort. That is a model difference, not a load curve ([capacity battery](capacity-battery-design.md)).
- Single-agent traits so far separate model families (stated–applied fidelity) or models (structural reliability), not configurations within a model.

**Multi-agent settings add what single tasks lack.**
- Evidence arrives through other agents' messages, which are compressed, relayed and dependent.
- Agents weigh peers by their records, their confidence and their number.

The OpenAI–Hugging Face incident (July 2026) showed these failure modes at scale:
- a relayed claim treated as established ("my predecessor confirms…");
- peers' behaviour taken as evidence ("peers doing it");
- a confident coordinator redirecting hundreds of agents;
- compressed hand-offs.

**Scope.** Belief formation only, as in the capacity note. Peers make claims about urns, and the measures are how the agent's forecasts move. No actions, tools or security content.

## The idea: the formal cores at agent scale

Each multi-agent construct is one of the single-agent formal cores with peers in place of sensors. The traits can then be tested for transfer across levels: does how a configuration handles copying sensors predict how it handles relaying peers? That is the passport's original question, general traits, asked of the setting where the failures matter.

| Construct | Single-agent analogue | Multi-agent form | Normative answer exists? |
| --- | --- | --- | --- |
| Dependence neglect | Sensors that copy (copying core) | Peers who pass on another peer's call; a unanimous majority that repeats one source | Yes (dependence observer) |
| Weight on evidence from others | Evidence weight *γ* on stated accuracies | A peer's call with a stated track record | Yes |
| Relay discount | Misfiled readings (uninformative-evidence core) | A claim that reaches the agent through a chain of relays, each of which may garble it | Yes |
| Evidence-free influence | None | A peer's stated confidence beyond its record; a majority whose calls carry no evidence | Yes: zero |

## Stage 1: scripted peers (receiver traits)

The peers' messages are written by the evaluator, so every quantity is controlled and the ideal answer exists. Stage 1 uses the existing infrastructure (probability answers, 24-case sessions, the collection service, the runner and the ledger). It needs only new tasks, observers and fits.

**Common setup.** An urn is red-majority or blue-majority, with a stated prior. The agent may have its own reading, with a stated accuracy. Other lab analysts send messages: their calls ("red-majority"), sometimes with a confidence phrase, and their records. The agent reports the probability that the urn is red-majority; *y* = logit *p̂*, binned to whole percentages as before.

### T1. Advice: weight and confidence

**Case.** One analyst's call, with a confidence phrase:
- hedged: "I think it's red-majority";
- plain: "It's red-majority";
- emphatic: "It's definitely red-majority — confirmed."

The analyst's record is stated per phrase: "Its emphatic calls have been right in 30 of its last 40; its hedged calls in 36 of 40." In some cases the phrases are equally accurate; in others the emphatic calls are less accurate (an overconfident analyst). The agent has its own reading in half the cases, agreeing or disagreeing.

**Model.**

*y* = logit *π* + *β*<sub>own</sub>·*s*<sub>own</sub>·logit *a* + *β*<sub>rec</sub>·*s*·logit *q<sub>h</sub>* + *β*<sub>conf</sub>·*s*·*z<sub>h</sub>* + *b* + *ε*, with *ε* ~ N(0, *τ*²)

- *q<sub>h</sub>* is the record's accuracy for the phrase used: (*K* + 1)/(*N* + 2).
- *z<sub>h</sub>* ∈ {−1, 0, 1} is the phrase's strength.
- *s* is the call's direction (+1 red, −1 blue); *s*<sub>own</sub> is the direction of the agent's own reading.
- The ideal is (*β*<sub>own</sub>, *β*<sub>rec</sub>, *β*<sub>conf</sub>) = (1, 1, 0).

**Traits.**
- ***β*<sub>rec</sub>, deference:** below 1 is egocentric discounting of advice (Yaniv 2004).
- ***β*<sub>conf</sub>, confidence persuasion:** movement with the phrase beyond what its record warrants (the confidence heuristic; Price & Stone 2004).

**Identification.** Phrase varies at fixed record accuracy, and record varies at fixed phrase, so the two weights separate.

### T2. Peer dependence

**Case.** Two to four analysts' calls.
- **Named variant:** the dependence is stated: "Analyst Q sees P's call before making its own; in 60% of rounds Q passes on P's call instead of using its own reading."
- **Audit variant:** dependence is shown only by a record, as in Part B: "Q's call has matched P's in 46 of their last 50 rounds." Its likelihood ratio is graded.

**Model.** The dependence observer: the copying core with analysts in place of sensors.
- **Named variant:** the implied relay disposition and the stated–applied gap.
- **Audit variant:** uptake *β* against the ideal observer (Part B's model).

**Transfer link.** The same observer and designs as the sensor copying tasks, so the comparison across levels is exact.

### T3. Conformity

**Case.** The agent's own reading (accuracy *a*) against *n* ∈ {1, 3, 5} analysts who all call the opposite. What the analysts' calls are worth is stated:
- **independent:** each read the urn with accuracy *b*;
- **dependent:** all repeat one analyst's call, so together they carry one reading;
- **evidence-free:** "these analysts had no readings; their calls are guesses". The ideal weight is zero.

**Model.**

*y* = *ℓ*\* + *κ*·*s*<sub>maj</sub>·log<sub>2</sub> *n* + *b* + *ε*, with *ℓ*\* = (1 − *η*)·*ℓ*<sub>exact</sub> + *η*·*ℓ*<sub>counted</sub>

- *ℓ*<sub>counted</sub> counts every analyst as an independent reading.
- *η* is dependence neglect at agent scale.
- *κ* is conformity: movement toward the majority that grows with its size beyond anything its evidence warrants. It is identified mainly from the evidence-free majorities.

**Traits.** *κ* (evidence-free influence) and *η* (dependence neglect among peers).

### T4. Relay chains

**Case.** A claim reaches the agent through a chain: "D reports that C reports that B reports that A read red." The chain has *k* ∈ {0, 1, 2, 3} relays. The original reading has accuracy *a*.
- **Stated fidelity:** "each analyst passes on the call it received unchanged in 80% of rounds; otherwise it passes on a coin flip". The call's accuracy after *k* relays is *q<sub>k</sub>* = ½ + (*a* − ½)·*f<sup>k</sup>*.
- **Unstated fidelity:** only the chain is shown. This is the "my predecessor confirms" case.

**Model.** The implied per-relay fidelity *f̂*, on a grid, with report noise and bias.
- ***f̂* = 1:** treats relayed claims as first-hand.
- **Stated-fidelity sessions:** the stated–applied gap.
- **Unstated sessions:** the default discount per relay.

**Traits.** Relay discount (unstated), and fidelity to a stated relay rate.

### Later: cascades (T5)

Sequential calls, where the agent sees predecessors' calls but not their readings (Bikhchandani et al. 1992; the urn paradigm of Anderson & Holt 1997). The ideal depends on assumptions about the predecessors' rationality, which must be stated for an ideal answer to exist. It is deferred until T1–T4 show which traits vary.

## Stage 2, later: live channels (sender traits)

A sender agent receives the full evidence for a case and writes a message to a peer in a fixed structured format: a probability, how many independent readings support it, and whether any readings may repeat others. A receiver agent, another configuration, answers from the message alone.
- **Channel fidelity:** the information lost relative to the full evidence, decomposed into estimate, uncertainty and provenance.
- **Design:** a round robin (senders × receivers) separates sender, receiver and pairing effects (the social relations model; Kenny 1994).
- **Why structured:** structured fields keep the messages behavioural and parseable, with no free-text self-report.
- **Infrastructure:** it needs a new answer type and a two-stage runner.

## The transfer test

Three candidate traits, each measured on at least three tasks, across levels:

| Trait | Single-agent tasks | Multi-agent tasks |
| --- | --- | --- |
| Dependence neglect | Sensor copying (uptake; structural errors on copying) | T2 (peer relays), T3 dependent majorities, T4 relay chains (as *f̂* against *f*) |
| Weight on evidence from others | Evidence weight *γ* | T1 *β*<sub>rec</sub>, T3 independent majorities, T4 stated fidelity |
| Evidence-free influence | None | T1 *β*<sub>conf</sub>, T3 *κ* |

- **Primary** (to be preregistered): leave one task out, as in battery v2, over all tasks of a trait. The held-out task includes single-agent tasks, so a pass means a trait carries across levels.
- **Secondary:** within the multi-agent tasks only; and the three traits' correlation across configurations.

## Configurations

All eight: Astra, Sol, Astra-low, Sol-low, Astra-high, Sol-high, Luna and Terra.
- **GPT-5.6** provides variation where GPT-6 is uniform.
- **Evidence-free influence** is the one construct not tied to computation, so it is the best chance of differences within GPT-6.

## Human anchors (descriptive only; no new human data)

- **Correlation neglect:** Enke & Zimmermann (2019). The data are already downloaded (`output/human-benchmarks/enke-zimmermann2019/`). Their correlated-message design is closest to T3 with dependent majorities.
- **Advice weight:** about 0.3 in human advice taking (Yaniv 2004; Bonaccio & Dalal 2006).
- **Cascades:** Anderson & Holt (1997), for T5 when it is built.

These are different populations and designs. They show where agents sit relative to people; they are not norms.

## Validation before any collection

1. **Observers** with exact answers for T1, T3 and T4, and tests against enumeration where the latent structure allows it. T2 reuses the dependence observer.
2. **Designs:** 24 cases per session, each parameter identified by the crossing described above. Every stated quantity must bear on the answer.
3. **Recovery** at one to three sessions per cell, with the house gates set in advance (correlation 0.9, coverage 0.8), for *β*<sub>rec</sub>, *β*<sub>conf</sub>, *κ*, *η* and *f̂*. Recovery fixes the sessions per cell.
4. **Task validation** on two seeds, including the wording audits:
   - unprompted variants never name the structure;
   - confidence phrases appear only as analysts' words.
5. **A range-finding pilot:** the four tasks on Astra, Sol, Luna and Terra, one session each.

## Size and cost (provisional)

About 0.55 million input tokens per 24-case session.

| Stage | Sessions | Tokens |
| --- | --- | --- |
| Pilot: 4 tasks × 4 configurations × 1 | 16 | about 9 million |
| Stage 1: 4 tasks × 8 configurations × 2 sessions (if recovery needs two) | 64 | about 35 million |
| Stage 2 (later): round robin of structured messages | to be designed | — |

## Risks

- **Uniformity within GPT-6 again.** Selection uptake and most load tasks were identical across GPT-6 configurations. Evidence-free influence (confidence, conformity) is the construct least tied to computation, so it is the likeliest to vary.
- **Confidence phrases read as information.** An emphatic call can reasonably suggest better information. So the record is stated per phrase, which makes the ideal weight on the phrase exactly what its record warrants.
- **Scripted peers may be discounted as fictional.** This is the same abstraction every battery has used. Stage 2's live peers address it.
- **Few configurations.** Eight, as before. A trait supported here is a trait of these configurations.

## Decisions for you

1. **Order:** Stage 1 (scripted peers) first, with the live channel later (recommended).
2. **Tasks:** T1–T4 now, and cascades later (recommended).
3. **Primary test:** transfer across levels, with single-agent tasks included (recommended), or within the multi-agent tasks only.
4. **Configurations and budget:** all eight; the pilot at about 9 million tokens first, Stage 1 at about 35 million after recovery.

## Stage 1 built (30 September)

**Decisions taken.** Stage 1 first; T1–T4 now and cascades later; the primary test across levels; all eight configurations.

**Versions.**
- Model 0.11.0 and design 0.13.0 (`dispositions/social.py`).
- Tasks 0.20.0: the texts are in `disposition_tasks/peers.py`, and four modules are wired into the battery, runner and ledger.

| Module | Variants | Design | Fit (headline parameter) |
| --- | --- | --- | --- |
| `advice-peer` (T1) | `peer-a` | 4 record levels for the phrase used (22, 28, 34, 38 right of 40) × 3 phrases × (no own reading, own reading against the call). The other phrases' records vary, so the phrase used must be matched to its own record. | Weights on the own reading, the record and the phrase, with bias and noise (*β*<sub>conf</sub>) |
| `copying-peer` (T2) | `urn2-vig2` | The copying design, with analysts in place of sensors and audit records at likelihood ratios 1–65,536 | Uptake against the ideal observer, exactly as for sensor copying |
| `conformity-peer` (T3) | `peer-a` | 6 cases with the own reading only, then majorities of 1, 3 and 5 analysts under each status (independent, passing on one call, guessing), 2 each | Weight on the own reading, dependence neglect *η*, conformity *κ*, with bias and noise (*κ*) |
| `relay-peer` (T4) | `chain-stated`, `chain-open` | 0–3 relays × fidelity 60% or 80% × 3 | Stated: the exponent *ω* applied to the stated fidelity. Open: the implied fidelity per relay. Both with the call's weight *γ*, bias and noise |

**What the texts look like:**
- **T1:** "Analyst P31 phrases each call in one of three ways, and the lab keeps its record for each: "definitely… confirmed" calls right in 28 of its last 40; plain calls right in 34 of its last 40; "I think…" calls right in 22 of its last 40. … Analyst P31's call on urn U101: "I think it is red-majority.""
- **T3, evidence-free majority:** "Analyst P47, analyst Q47 and analyst R47 did not read the urn and had no other information about it; each guessed, and all three called it red-majority."
- **T4:** "It reached you through analysts who each passed on what they were told: analyst P51 → analyst Q51 → analyst R51 → analyst S51 → you. The call as it reached you: blue-majority." In `chain-stated` it is preceded by the fidelity sentence; in `chain-open` there is no such sentence.
- **T2:** calls and an audit of how often analyst Q's call matched P's. The audit checks that the text never mentions copying, passing on, repeating or relaying.

**Checks.**
- The ideal answers are tested against independent derivations: each phrase's record, each majority status, and relay accuracy by enumerating every garble.
- Every stated number is displayed.
- Each fit recovers a low-noise respondent.

**Recovery** (`ledger social-recovery`, 100 respondents per task, the house gates fixed before the study; correlation, 90% coverage):

| Task | Parameter | 1 session | 2 sessions | 3 sessions |
| --- | --- | --- | --- | --- |
| T1 | *β*<sub>rec</sub> (primary) | 0.99, 0.95 | 1.00, 0.97 | 1.00, 0.94 |
| T1 | *β*<sub>conf</sub> (primary) | 0.98, 0.95 | 0.99, 0.97 | 0.99, 0.95 |
| T1 | *β*<sub>own</sub> | 0.95, 0.98 | 0.97, 0.92 | 0.98, 0.90 |
| T3 | *κ* (primary) | 0.99, 0.97 | 0.99, 1.00 | 0.99, 0.97 |
| T3 | *η* | 0.95, 0.98 | 0.98, 0.95 | 0.98, 0.88 |
| T3 | *β*<sub>own</sub> | 0.98, 0.92 | 0.99, 0.93 | 0.99, 0.93 |
| T4 stated | *ω* (primary) | 0.96, 0.90 | 0.97, 0.88 | 0.98, 0.87 |
| T4 open | fidelity (primary) | 0.97, 0.97 | 0.99, 0.99 | 0.99, 0.99 |

- **All four fits pass at one session per cell.** These designs identify their parameters better than the capacity designs did, because each parameter has its own crossing.
- **T2** passes at one session: it has the same design, ideal observer and fit as sensor copying, which the capacity battery's uptake recovery already covered.
- **Recovery SHA-256:** `2a92d26e9dd7ce8eecea52cc85c96d3ededa4fad88522a0dfb5efcc4f40b3a8a`.

**Task validation 0.20.** It passed on both seeds: 2,352 cases and 103 contexts. The five peer contexts use respondents with known parameters:
- T1: *β*<sub>rec</sub> 0.8, *β*<sub>conf</sub> 0.4;
- T3: *η* 0.5, *κ* 0.4;
- T4: *ω* 0.5, and fidelity 0.7;
- T2: uptake 0.6.

All were recovered within tolerance.

The first validation of 0.20 was redone before any collection. The runner's expected case count left out the peer modules, so preparing a collection would have refused the validations. The count is now tested against the audit.

Tasks fingerprint `3e18c2f391fa541f61f045e68df872aa61720dad6a76c71d7dfaf85f12dd3d98`.

| Artifact | SHA-256 |
| --- | --- |
| Task validation 0.20, seed 20260927 | `f9a772ff8f27610dbae5919ae9e4190bc9b3ea04f0c335a808d61db2d78194c0` |
| Task validation 0.20, seed 20261027 | `076be901f7f0f3dbce4d399c84c7608ff97c64961ec91f21aa2822e1470600b6` |

**Next: the range-finding pilot.**
- **Contexts:** the four tasks on Astra, Sol, Luna and Terra, one session each, with T4 in both variants. That is 20 contexts, about 11 million tokens.
- **What it checks:** that no parameter sits at a grid edge for every configuration, that the texts are read as intended, and how many tokens a session uses.
- **Then:** Stage 1 at one session per cell (recovery allows it) on all eight configurations. That is 5 contexts × 8 = 40 sessions, about 22 million tokens.

### Pilot (planned 30 September, before collection)

**Contexts.** Tasks 0.20.0, validations 0.20 on both seeds. Astra, Sol, Luna and Terra, one session each, on:
- `advice-peer` (`peer-a`);
- `copying-peer` (`urn2-vig2`);
- `conformity-peer` (`peer-a`);
- `relay-peer` (`chain-stated` and `chain-open`).

That is 20 contexts. Limits: 1,800 seconds per run, and a cap of 15 million tokens.

**Read-out.** Per configuration and task, the fitted parameters with 90% intervals:
- T1: *β*<sub>rec</sub> and *β*<sub>conf</sub>;
- T2: uptake;
- T3: *κ* and *η*;
- T4: *ω* and the implied fidelity.

Also whether any parameter sits at a grid edge for every configuration, and tokens per session.

**What may change after it.** This is range-finding: only the designs' ranges (record levels, majority sizes, relay lengths and fidelities) may change.
