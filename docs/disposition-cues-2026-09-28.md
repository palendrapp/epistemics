# Description-to-prior modules (0.3) — 28 September 2026

Build and validation record. [Round 2](disposition-round2-2026-09-28.md) showed that frontier configurations share a 50% default and Laplace learning. They differ in how a qualitative description of a source becomes a prior. Version 0.3 measures that mapping directly, for relaying (T2) and for selective disclosure (T3):
- disposition-model/0.3.0;
- disposition-design/0.3.0;
- disposition-tasks/0.3.0.

No respondent has answered it yet.

## Design

**Five description levels.** Each module grades descriptions from strongly reassuring to strongly suggestive, with a description that should not matter in the middle. Two paraphrase sets let the level be separated from the particular sentence. No description states or implies a number.

| Level | Relay, set A | Relay, set B | Disclosure, set A | Disclosure, set B |
| --- | --- | --- | --- | --- |
| Strongly reassuring | employs twenty reporters who interview customers and suppliers before every call | has a research desk that visits the company's factories before every call | updates are checked by an independent auditor before release | is owned by a customer cooperative that publishes all its data a month later |
| Mildly reassuring | sometimes runs its own surveys of retailers | has a few analysts who occasionally speak to suppliers | has a reputation among investors for plain, complete reporting | finance team has worked with the same outside accountants for twenty years |
| Irrelevant | is based in a city on the coast | prints its stories in a blue-and-white layout | moved its headquarters to a new building last year | sponsors a local football team |
| Mildly suggestive | is a small newsletter with two analysts | usually publishes shortly after larger outlets | is hoping to raise new financing later this year | share price has fallen for three quarters in a row |
| Strongly suggestive | is an aggregator site with no reporters that posts dozens of market calls a day | is a one-person blog that posts within minutes of larger outlets | chief executive will lose a large bonus unless these indicators look good this quarter | is in talks to be sold, and the buyer's price depends on these indicators |

**Checkpoints.** Each context has 24, in the open framing: no two-way sentence. Each level gets four:
- **Stated base rate:** "Among outlets like X, what proportion relay another outlet's call instead of checking for themselves?" (for disclosure: what proportion share every on-target indicator and withhold every off-target one). This asks for a population proportion, answered as a probability.
- **Structure probe:** a matching pair, or a partial update, followed by "how likely is it that X relayed?" (or "is the kind that withholds").
- **Two forecasts**, with the same evidence structure at every level.

Four anchor cases carry no description and pin evidence sensitivity, bias and noise:
- **Relay:** two single reports and two conflicting pairs.
- **Disclosure:** two updates without omissions and two that reveal a non-selective sender.

**Model.** Each level has its own implied disposition, estimated from its probe and forecasts. Evidence sensitivity γ, forecast bias and report noise are shared, and the level dispositions are marginalised exactly. The stated base rates are not used in the fit. They are returned beside the implied values, so the per-context analysis reports:
- **the implied mapping itself:** five dispositions with 90% intervals;
- **coherence:** the mean absolute difference and rank correlation between stated and implied priors, that is, whether the respondent uses the prior it states;
- **ordering:** the rank correlation between the designed level order and the implied priors;
- **the irrelevant control:** its shift from 50%, flagged as moved when it exceeds one grid step and its interval excludes 50%;
- **range:** the difference between the highest and lowest implied prior, as a sensitivity measure.

**No real-world base rates.** I could not find real-world base rates for descriptions like these, such as the share of two-analyst newsletters that relay calls, so the mapping cannot yet be scored for calibration against the world. It is scored for ordering, sensitivity, the irrelevant control and coherence. Its main use is descriptive and comparative: between configurations, between paraphrase sets and, later, against people.

## Other changes in 0.3

- **Wall-clock timeout.** The runner's per-run and total limits now use wall-clock time, checked at least every five seconds, so a sleeping machine fails a run promptly on waking instead of stalling for hours, as happened in round 2. A test confirms that a respondent that never answers fails at a one-second limit within seconds.
- **Visibility rule in the pipeline validation.** Learning must now be detected only when the revealed rate differs from the starting value by at least 0.25, the same condition the recovery study scores. At one seed, a revealed rate of 62% against a 50% start left learning invisible.

## Validation

**Model recovery.** Both seeds passed every gate, including the new cue gates. 200 simulated respondents per module, each with an independent disposition at every level. Agent-like noise band:

| Module | Implied level priors: r | Error | 90% coverage | Stated base-rate error |
| --- | --- | --- | --- | --- |
| Relay | 0.984–0.986 | 0.036 | 0.92–0.93 | 0.035–0.037 |
| Disclosure | 0.988 | 0.032–0.033 | 0.93 | 0.031–0.038 |

All earlier gates still pass: fixed dispositions, rival models, learning, and value of certainty.

**Task pipeline.** Both seeds passed:
- **Audit:** 720 rendered cases, including 96 cue cases, for displayed probabilities, private labels and framing.
- **Synthetic contexts:** 32, including a respondent with a known mapping (0.1, 0.3, 0.5, 0.7, 0.9) in each cue module and set. Its mapping was recovered within 0.15 at every level.

Plan preparation for the new `cues` preset was dry-run with no model calls.

## Proposed acceptance

| Setting | Proposal |
| --- | --- |
| Configurations | GPT-6 Astra and Sol, medium effort |
| Modules | relay cues, disclosure cues |
| Contexts | set A and set B, markets |
| Runs | 8 fresh contexts of 24 checkpoints |
| Tokens | about 4.3 million input tokens, mostly cached; cap 8 million |

**Readouts:**
- each configuration's five-level mapping for each module;
- agreement between the two paraphrase sets;
- stated against implied priors;
- ordering and the irrelevant control;
- differences between Astra and Sol. Round 2 suggests Sol responds to reassuring institutional detail on disclosure and Astra does not.

Weaker configurations and a repeat of each context would follow if the mapping is informative.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Model implementation fingerprint | `604a9b5c6e0167c7dcb55d454a5f03fe33b39061a140eababc825a37738f183a` |
| Model recovery, seed 20260927 | `a57e2b0b57644e951596688069bf76a71c46ce0f5515f8cab676710bbba383b5` |
| Model recovery, seed 20261027 | `7a3c0a54d41ebaea956702fc5e9c4277e2ba2f9e526776b66940e7aec957e370` |
| Tasks implementation fingerprint | `3c52a37088c4c2b1740837f8f4631ea49c7d0d9b81a4952b07e4b5d9e9015ea5` |
| Task validation, seed 20260927 | `e52bf7a04116907ebfbe036b0feafc12c0d6b5de1d30314021d3865958e97eb3` |
| Task validation, seed 20261027 | `a39b78cd17bbb40b8ee0e69638d5eedb0d49bfdae24dc6a60ad0ce313b8acba8` |

Validation outputs remain in the ignored `output/` directory.
