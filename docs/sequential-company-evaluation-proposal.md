# Proposal: sequential company evaluation

Status: research design proposal. The [company dossier pilot](company-pilot.md) now implements the first controlled subset with a separate battery/report version and synthetic recovery checks. The broader conditions below remain proposed; the original v0.1 battery and its scoring remain available.

The intended primary condition is now explicitly discovery, with the disclosed-model condition retained for calibration. See the [discovery inference proposal](discovery-inference-proposal.md) for source learning, causal explanations, observation models and identifying contrasts.

## Research question

How does an agent construct, revise and act on an investment thesis when it encounters heterogeneous, incomplete and sometimes dependent evidence?

The unit of evaluation is an episode about one fictional company. An episode contains an initial dossier, successive evidence arrivals, repeated responses and a final outcome reveal. The primary object is the trajectory of forecasts, uncertainty, assumptions, source assessments and decisions. A final recommendation alone misses most of the interesting behavior.

Our initial runs establish that agents can implement explicit Bayesian calculations through MCP. This design would test interpretation, evidence integration and decision making under richer conditions. Calling it a portfolio task does not by itself establish ecological or psychometric validity.

## Example episode

Consider a fictional industrial-software company, Meridian Systems. Its investment thesis is that a product transition will sustain growth without damaging margins. Set a fixed forecast horizon and observable targets before the episode: next-year revenue growth above 12%, and operating margin above 18%.

| Arrival | Material | Question made observable |
| --- | --- | --- |
| Initial dossier | Historical financials, product/customer mix, peer base rates and a fixed decision mandate | What starting forecasts and assumptions does the agent adopt? |
| 1 | Headline reporting a major customer win | How much does an attention-grabbing but incomplete signal change forecasts? |
| 2 | Earnings-call excerpt: management reports strong demand but limited contract detail | How does the agent use management claims and uncertainty? |
| 3 | Independently sourced customer-cohort table showing weaker retention | Does counterevidence change the central thesis, a subgroup assumption or source trust? |
| 4 | Broker model projecting margin expansion | Does the agent inspect the assumptions? Can it recognize inputs already present in earlier material? |
| 5 | Two news summaries traced to the same management announcement | Does repackaging the same observation create apparent corroboration? |
| 6 | A correction to a material fact in the earlier announcement | Does the agent revisit downstream conclusions that depended on it? |
| 7 | An operational update that helps distinguish a temporary onboarding delay from lasting customer loss | Does the agent distinguish noise, temporary disruption and structural change? |
| 8 | A choice among further research items, followed by the selected item | What does it choose to investigate, and is the expected benefit worth the cost? |

This is an illustrative episode, not a template in which every headline must be weak or every model must be misleading. Cross favorable/unfavorable evidence, source quality and presentation format across cases. Include genuinely informative models, correct management explanations and justified persistence.

For presentation-order experiments, reorder dated documents about a fixed underlying period while preserving their timestamps. For regime-change experiments, advance simulated time. Reversing genuine chronology changes information and cannot be interpreted simply as an order effect.

## Response design

Separate company forecasts, uncertainty, investment value and action. A favorable company forecast does not determine whether a security is attractive at a particular price. Position size also depends on payoffs, risk preferences and portfolio constraints.

After every arrival, obtain a compact, stable core response:

1. Probabilities for the two fixed, objectively resolvable fundamental targets.
2. A median and 10th/90th percentiles for one numeric target, such as revenue growth.
3. A decision under the specified mandate: a target exposure, or defer and purchase research where that is available.
4. IDs of the evidence items chiefly responsible for any revision. This is a short attribution, not a required private reasoning trace.

Use additional probes at selected, randomized checkpoints: current assumptions, source accuracy assessments, conditional forecasts under a competing explanation, the most useful next observation, or a price at which the decision would change. Let explanations coexist; an ordinary list of overlapping hypotheses is not automatically a probability simplex. Only require probabilities to sum to one when the modeled states are explicitly mutually exclusive and exhaustive.

An event probability is not a generic confidence rating. A 50% forecast can reflect a well-understood balanced risk or poor understanding of the situation. Predictive intervals describe uncertainty about outcomes; their width does not by itself distinguish uncertainty about the model from irreducible outcome noise. Record assumption sensitivity and information-seeking separately. A free-standing confidence label, if included, should initially be descriptive rather than a scored measure of epistemic uncertainty.

Frequent elicitation can change behavior. Repeatedly requiring a defended thesis may induce commitment; asking about source independence may teach the agent what to check. Keep core responses short and compare rich-probe, minimal-probe and end-only conditions in separate, randomized arms. The relevance of presentation order and step-by-step versus end-of-sequence responding is motivated by [Hogarth and Einhorn (1992)](https://www.sciencedirect.com/science/article/pii/001002859290002J); effects in agents remain empirical questions.

## Highest-priority contrasts

### 1. Independent evidence versus repeated evidence

Compare several genuinely independent observations with several documents derived from one observation. Include explicit-provenance and provenance-discovery variants separately. Measure the additional forecast movement caused by duplication and whether the agent can identify shared origins.

Maintain a hidden evaluator-side provenance graph linking documents, claims, underlying observations and model inputs. The graph should distinguish a new observation from a new calculation on existing data. A deterministic model can help a bounded reasoner extract implications without becoming an independent source of empirical confirmation.

### 2. Revision of the business thesis versus supporting assumptions

Present disappointing evidence with competing explanations: demand deterioration, an unrepresentative sample, a temporary operational problem or unreliable reporting. Later provide evidence that discriminates among them. Obtain conditional forecasts or selective assumption probes before the discriminating evidence arrives.

This is the most direct connection to [Gershman (2019), *How to never be wrong*](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf): disconfirmation can be allocated to a central hypothesis or auxiliary assumptions. Changing an auxiliary belief can be reasonable. Keeping a thesis after one adverse observation is not enough to diagnose rationalization. The proposed task must include conditions where persistence is justified and conditions where the supporting explanation becomes untenable. This is an original experiment inspired by that framework, not a replication.

### 3. Source and format effects

Render matched claims as a headline, narrative excerpt, table or model output. Cross format with actual evidence quality and documented source track record. Do not interpret greater trust in an audited source as a prestige bias when its reliability is genuinely higher.

Separate extraction from integration: first verify that paired materials encode the same relevant quantities and qualifications. Report comprehension failures separately from differences in how successfully extracted facts are weighted. Broader presentation tests can subsequently include length, chart design and model complexity.

### 4. Buying information and deciding when to stop

Offer a small research menu with explicit costs and enough description to anticipate what each item could resolve. Include redundant, diagnostic and irrelevant options. Measure choice, stopping and forecast or decision improvement per unit cost. Resource constraints should be fixed and recorded, following the motivation of [Bhui, Lai and Gershman (2021)](https://gershmanlab.com/pubs/Bhui21.pdf).

Keep passive evidence integration and active acquisition as distinguishable experimental blocks. Otherwise agents receive different information sets because of their own choices, complicating comparisons of their updating behavior.

Additional later contrasts could include favorable/unfavorable evidence, assigned existing holdings, source corrections and temporary versus persistent regime changes. Assigning a portfolio position may create measurable role effects; it does not establish that a model experiences financial motivation.

## Environment and ground truth

Start with synthetic companies generated from a small, coherent model of demand, retention and margins. Generate numeric data first, then render documents from a controlled claim ledger. Check arithmetic, units, timestamps and cross-document consistency. Plausible prose generated without an underlying world is insufficient for evaluating inference.

Use two explicitly different conditions:

- **Controlled inference:** disclose the world model or enough calibration examples to justify the relevant likelihood assumptions. Compare against a reference that has exactly the information available to the respondent, not privileged access to the hidden state.
- **Discovery and transfer:** withhold source accuracy and some causal structure, providing opportunities to learn them. Evaluate observable predictions, decisions and matched-condition sensitivities. A posterior computed using the evaluator's undisclosed true model is an information-advantaged ceiling, not a uniquely correct answer the agent should reproduce.

For the first decision task, use a transparent toy payoff linked to the simulated fundamentals, a fixed price and a specified risk constraint. Do not equate a fundamentals forecast with an equity-return forecast. More realistic price, discount-rate and market-return processes can be added later as their own uncertainty sources.

Eventually use timestamped historical dossiers or prospective cases to study transfer. Historical issuer names and public events may trigger memorized outcomes; anonymization alone cannot guarantee their removal. Live cases introduce delayed ground truth, inconsistent evidence availability and harder attribution. They should follow a controlled pilot.

## Analysis and validation

Keep three outputs separate:

1. **Predictive performance:** Brier/log scores for fixed binary events; proper quantile or interval scores for numeric forecasts. Evaluate coverage over many independent episodes. Proper scoring provides an expected-score incentive for truthful reports under its assumptions; it does not reveal internal beliefs. See [Gneiting and Raftery (2007)](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).
2. **Updating behavior:** matched-condition effects of duplication, source reliability, presentation and disconfirmation; source-assumption trajectories; and adaptation after change or correction. Do not label every small update as conservatism: uninformative evidence should sometimes cause little change.
3. **Decision quality:** expected utility and regret under the specified mandate and information set, research value net of cost, and consistency with the agent's own stated forecasts. A fully informed oracle belongs in a separate upper-bound comparison. Realized profit alone confounds decision quality with luck and preferences.

Analyze the episode as the main replication unit. Eight successive reports about the same eventual outcome are correlated observations, not eight independent successes. Hold out entire scenario families and presentation templates. Register primary contrasts before evaluating held-out agents and report incomplete runs.

Start with a few identifiable effects. Fit richer learning-rate, source-trust or hypothesis-switching models only after recovering their parameters and distinguishing the candidate models on simulated respondents. Include a reference updater, a recency heuristic, a duplicate-counting policy and policies that revise supporting assumptions excessively or insufficiently. This validation follows [Wilson and Collins (2019)](https://elifesciences.org/articles/49547); recovery does not by itself validate the psychological interpretation.

## Proposed MVP

- One domain: fictional listed companies, initially using a common business structure to limit domain-knowledge confounds.
- A small library of scenario families, initially around six, each with roughly eight evidence arrivals and multiple generated instances. This is a pilot workload, not a claim of adequate sample size for stable agent traits.
- Two fixed fundamental targets, one numeric forecast distribution and one constrained decision per checkpoint.
- Headline, management excerpt, operating table and inspectable model as the initial document types. Full spreadsheet manipulation and PDFs can follow after ingestion is validated.
- Two primary scientific contrasts: independence versus duplication; central-thesis versus auxiliary-assumption revision. Cross presentation in a limited robustness check and add one separately analyzed information-choice block.
- Matched experimental variants assigned across fresh agent sessions. Preserve context within an episode; reset between episodes initially. If studying source learning across episodes, make that a separate declared condition.
- Fix tool access, budgets and model/configuration metadata. Permit arithmetic; making computation difficult is not the central objective.
- A pilot should determine whether cases separate the intended strategies, whether parameters are identifiable and whether effects survive paraphrase and repeated seeds. Use simulation to determine the eventual number of independent episodes and configurations.

## Interface and records

Extend the current MCP session flow with evidence delivery, structured checkpoint submission and an optional research menu/purchase action. Evidence should have stable IDs, timestamps, document versions and references to accessible artifacts. Preserve evaluator-side latent state, seeds, future evidence and outcome keys. Keep accepted answers immutable and make retries idempotent; an acquisition receipt must also avoid charging twice.

The first deliverable should be one authored end-to-end episode and several matched variants reviewed for internal consistency. Then implement a new versioned battery and report contract, with recovery tests, before scaling the scenario generator.

An eventual verifiable record should bind the scenario version, artifact hashes, precise evidence/response sequence, chosen research, tool/budget configuration and analysis version. Full content remains an inspectable off-chain artifact; commitments and evaluator signatures preserve provenance. A signed record authenticates the recorded claims and execution assertions, not the truth of a broad epistemic-trait interpretation.
