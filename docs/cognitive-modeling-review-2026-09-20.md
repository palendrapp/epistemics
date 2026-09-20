# Cognitive modeling for an epistemic passport

Focused literature review and design recommendation, 20 September 2026. This is a research/design document, not a new battery, validated instrument or revised analysis of the completed benchmark. It draws on primary papers and author manuscripts, with focused reading of the relevant formal models, experiments and limitations. It is not an exhaustive systematic review. Bibliographic years refer to publication years where established, not search-engine crawl dates.

## Assessment of our current approach

The literature gives concrete reasons to revise the latest provenance benchmark for the passport objective. It does **not** establish that misspecification caused its null personalization result. Low stable variation between the tested configurations, estimation error, response variability and limited transfer remain alternatives. Preserve the [completed result](prediction-results-2026-09-20.md).

The central design issue is that **our latest benchmark mostly asks how much weight a respondent gives evidence after much of its interpretation has been supplied**. The more relevant cognitive-modeling question is how a respondent constructs, selects and revises an interpretation of the evidence, and uses it to choose what to do next.

This distinction applies to the latest provenance benchmark, not to every component in the repository. The earlier [sequential-company models](sequential-company-models.md) and implemented [matched discovery study](discovery-study.md) already represent uncertain fundamentals, disruption, source bias/precision and provenance jointly. They are a better starting point for this objective, though they cover one authored business mechanism and lack active research and broader model-search alternatives.

| Verified feature of the provenance benchmark | What it limits |
| --- | --- |
| Explicit original/copy relationships and supplied source success counts | Little opportunity to infer hidden dependence, source intent or a causal explanation |
| One binary-source model with varied cover stories and graph order | Transfer remains within a narrow representation of the world |
| Three-to-five evidence arrivals, with no outcome-feedback source-learning phase | Cannot characterize adaptation to source drift or distinguish environmental change from measurement noise |
| Regression on cumulative prior/original/copy log-odds features | Contains no evolving hypothesis set, search process, latent context or retraction mechanism |
| Fixed presentation; participants cannot buy evidence, inspect a source or stop research | Does not measure information acquisition or a research policy |
| Logit least squares with a single effective response mapping | Cannot assign residuals uniquely to inference, reporting, comprehension or occasional strategy changes |
| Three requested configurations and repeated fresh episodes | Does not establish stable traits across sessions, configurations, task families or humans |

We should have established the suitability of this narrow task for the broader passport claim before scaling collection. Its engineering controls remain useful; a successful in-family recovery test does not establish that real participants differ in the ways simulated agents were made to differ.

## What the literature contributes

### 1. Gershman: inference distributes responsibility across explanations

In [*How to never be wrong* (Gershman, 2019)](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf), contradictory observations can change beliefs about a central claim, its auxiliary assumptions, or both. Persistence need not require a special resistance parameter. The account is conditional on the hypothesis space and probabilistic assumptions; the paper explicitly discusses falsifiability and independently constraining those assumptions.

For our design, a headline should sometimes be compatible with weak fundamentals, a temporary bottleneck or a misleading source. Subsequent evidence should discriminate those explanations. The participant's forecasts about an audit or an unaffected business segment would then constrain the fitted account. A single final probability cannot do that.

### 2. Ullman: learning a theory differs from updating within one

[Ullman, Goodman and Tenenbaum (2012)](https://www.tomerullman.org/papers/tlss-final.pdf) model theory acquisition through stochastic search over structured hypotheses. Their model separates theory-level laws from their particular instantiations, and distinguishes the effect of more data from more search on existing data. Individual learning trajectories can contain discrete changes that disappear in averages. [Ullman and Tenenbaum (2020)](https://www.annualreviews.org/content/journals/10.1146/annurev-devpsych-121318-084833) develop the broader account of learning as constructing probabilistic generative models.

Our adaptation should separately test recognizing an explanation when offered and discovering it without that prompt. Hypotheses should entail testable forecasts or interventions. Counting plausible-sounding explanations would measure verbal production without establishing useful causal discovery.

### 3. Hypothesis search and approximate inference

[Dasgupta, Schulz and Gershman (2017)](https://gershmanlab.com/pubs/Dasgupta17.pdf) distinguish generating a subset of hypotheses from evaluating them. Their sampling account offers a process-level alternative to an ideal observer that considers all possibilities. [Bramley, Dayan, Griffiths and Lagnado (2017)](https://www.bramleylab.ppls.ed.ac.uk/pdfs/bramley2017neurath.pdf) formalize a learner that maintains one causal model and revises it through local search. They also model experiments selected to resolve local uncertainties.

These are useful competing explanations for persistence, order effects and abrupt revision. A small fitted evidence coefficient is not sufficient to choose among them. Providing a diagnostic alternative, additional computation or an external evidence record produces different tests of the accounts. A fitted search parameter would remain a behavioral approximation, not a measurement of a transformer's literal internal search steps.

### 4. Bayesian learning and RL are not opposing labels

Error-driven updating can arise inside a Bayesian account. [Nassar, Wilson, Heasly and Gold (2010)](https://pubmed.ncbi.nlm.nih.gov/20844132/) connect an approximate Bayesian learner to a delta rule whose learning rate responds to uncertainty and change. [Piray and Daw (2021)](https://www.nature.com/articles/s41467-021-26731-9) explicitly separate latent environmental change from observation noise; these have opposite effects on the appropriate learning rate. Their model estimates both using sequential observations.

For our task, an isolated bad reading and a persistent deterioration should sometimes warrant different reactions despite equal initial surprise. A fixed learning-rate label loses that distinction. Longer sequences with feedback and independently manipulated noise/change are needed; simply appending more news items to a static target does not provide them.

[Gershman, Blei and Niv (2010)](https://www.princeton.edu/~yael/Publications/GershmanEtAl2009.pdf) add another possibility: observations can be assigned to different latent causes. Their conditioning model accounts for contextual effects through inference over an unbounded set of causes. Our bounded adaptation could compare revising an existing company/source model with inferring a changed regime, then test whether a return to an earlier context reinstates earlier predictions.

RL also concerns action selection, beyond adjusting a forecast. [Daw, Gershman, Seymour, Dayan and Dolan (2011)](https://gershmanlab.com/pubs/Daw11.pdf) distinguish predictions of cached action values from planning with learned transition structure in a two-stage task. A later passport module could test whether a participant changes its decision after learning that an action's consequences have changed, before receiving new rewards for that action. This needs a dedicated design and competing heuristics: success on one planning contrast does not uniquely identify an internal algorithm, and model-based control is not automatically preferable at every computational cost.

### 5. Source judgment includes competence and intent

[Shafto, Eaves, Navarro and Perfors (2012)](https://papers.djnavarro.net/2012_epistemictrust.pdf) jointly model an informant's knowledge, helpfulness and the world's state. They explicitly limit their implemented deception example to an informant who always lies; strategic truth-telling is a further extension.

For an agent-economy passport, a noisy source, a systematically biased source and a source that selectively discloses accurate facts are distinct conditions. Competence and selection should have separately informative observations before we fit separate parameters. An analyst's historical accuracy alone cannot identify the effect of selective reporting. Unknown provenance should also have a scored inspection option, rather than being settled by the prompt.

### 6. Information acquisition is part of the cognitive profile

[Gershman (2018)](https://gershmanlab.com/pubs/Gershman18.pdf) distinguishes exploration driven by uncertainty bonuses from sampling-based exploration, using manipulations that separate relative uncertainty from total uncertainty. Their different behavioral predictions illustrate how experimental design can distinguish algorithms that otherwise look similar.

[Lieder and Griffiths (2020)](https://cocosci.princeton.edu/papers/liederresource.pdf) evaluate cognitive strategies relative to resource constraints and the value of improved decisions. This makes compute budget, evidence cost and decision stakes part of the conditions under which behavior should be interpreted.

Our participant should choose between another headline, a provenance check, a diagnostic operating metric, a model calculation and stopping. Vary their cost and relevance. Seeking the most information and seeking the most useful information are different policies; a purchase can reduce uncertainty about a question that cannot change the decision.

### 7. Representation, learning and reporting must remain distinct

[Gershman (2025), *Bridging computation and representation in associative learning*](https://gershmanlab.com/pubs/Gershman25.pdf), derives a rate-estimation account using learning machinery resembling a classical associative rule. A key distinction appears in the response rule. This is a conditioning model, not direct evidence about LLMs, but it sharply illustrates why a familiar update equation does not identify the represented quantity or its expression.

[Collins and Frank (2012)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3390186/) show how omitting working memory can misattribute human learning behavior to RL parameters. [Dasgupta, Schulz, Tenenbaum and Gershman (2020)](https://gershmanlab.com/pubs/Dasgupta20.pdf) model learned, resource-constrained approximations to inference whose errors depend on the distribution of queries and past experience.

Our adaptation should manipulate memory access and query format explicitly. A deterministic model calculation over existing data supplies no new observation to an ideal observer, but may help a bounded respondent compute an implication. Its effect should not automatically be classified as duplicate counting. Equally, a wording effect may alter interpretation or deliberation, not just the final verbal readout.

### 8. Confidence and useful self-evaluation

[Fleming and Daw (2017)](https://www.princeton.edu/~ndaw/fd17.pdf) distinguish second-order assessment of a decision from a readout of the same state that produced it. Their framework separates confidence, error detection and performance.

For the passport, measure whether confidence or a request for review predicts subsequent correctness, conditional on difficulty and available evidence. Event probability, uncertainty about the source model and confidence in one's calculation are different quantities. Define each question operationally, score it where possible, and avoid treating confident language or distance from 0.5 as a general metacognitive score.

### 9. Individual measurement needs its own validation

[Hedge, Powell and Sumner (2018)](https://link.springer.com/article/10.3758/s13428-017-0935-1) demonstrate that robust experimental effects need not yield reliable individual differences. Low between-participant variation can make ranking unstable even without unusually high measurement noise.

[Wilson and Collins (2019)](https://elifesciences.org/articles/49547) distinguish parameter recovery from model recovery and require simulations to test what a design can identify. [Palminteri, Wyart and Koechlin (2017)](https://pubmed.ncbi.nlm.nih.gov/28476348/) emphasize falsifying candidate models, rather than treating the best of an inadequate set as an adequate explanation.

For our product, repeated matched observations, parameter uncertainty and stability across sessions belong beside the profile. We should allow two agents to have similar profiles. A passport need not uniquely identify its owner through behavior; identity primitives already serve that purpose. The product question is whether the measurements support useful expectations or decisions at their stated scope.

## Relevant bridges to contemporary agents

[Binz and Schulz (2023)](https://doi.org/10.1073/pnas.2218523120) demonstrate cognitive experiments on GPT-3, including informative perturbations of standard tasks. Those results concern the tested historical model; they do not establish limitations of our current configurations. [Coda-Forno et al.'s CogBench (2024 preprint)](https://arxiv.org/abs/2402.18225) offers seven experiments and ten behavioral metrics across 35 LLMs. It is a relevant comparison point and potential source of calibration adapters, not evidence that any transferred metric is automatically valid for our passport.

[Tsividis et al. (2026)](https://gershmanlab.com/pubs/Tsividis26.pdf) combine symbolic theory learning, exploration and planning in novel games. The model receives structured symbolic input; the work does not demonstrate unrestricted world learning from raw sensory input. Its relevance here is the coupling between model construction and action selection, rather than a recommendation to build a game-playing benchmark first.

[Liu, Xiang and Gershman (2026)](https://pubmed.ncbi.nlm.nih.gov/42113206/) is especially relevant to a later portfolio module: it studies forecasting structural asset-performance dynamics to guide selection and switching. The abstract and publication record were checked; the author-site PDF link returned 404, so its detailed likelihoods and experimental implementation were **not** reviewed here. It should be read fully before borrowing its design. Its assets can change with continued investment, which differs from merely estimating a company's fixed future outcome.

## Proposed model architecture

These equations are **our proposed bounded adaptations**, not transcriptions of one paper or implemented changes. Use separate modules and a small set of competing models. Do not fit every parameter below simultaneously from one short episode.

### A. A joint observer over a small, learnable world

Let \(M\) identify a candidate causal mechanism, \(z_t\) the current business state, and \(\theta\) persistent source parameters. Observations \(o_t\) arrive through a selected query \(q_t\). Define a joint belief state:

\[
b_t(M,z_t,\theta)\propto
p(o_t\mid M,z_t,\theta,q_t)
\sum_{z_{t-1}}p(z_t\mid z_{t-1},M)
b_{t-1}(M,z_{t-1},\theta).
\]

Static cases use an identity transition. Dynamic source states, if introduced, must also be transitioned rather than silently treated as persistent parameters. Correlated sources, deterministic calculations and selective disclosure require corresponding likelihoods; conditional independence is a modeling choice to test.

The target forecast integrates over the fitted joint state and future dynamics. A forecast about an unaffected segment or an audit is another prediction from that same state. We should not update company beliefs a second time using a source-reliability posterior already obtained from the same evidence.

The environment generator's hidden state determines eventual outcomes. The observer must infer from the public evidence, not read that hidden state. In discovery mode, its priors and likelihood assumptions are conditional references to compare, not privileged knowledge that the respondent was instructed to use.

### B. Competing update algorithms

Use a deliberately small comparison set, with matched observation models:

| Candidate | Behavioral hypothesis | Diagnostic opportunity |
| --- | --- | --- |
| Static evidence regression | A fixed mapping of evidence features explains responses | Existing benchmark control |
| Fixed delta rule | Recent prediction errors receive a constant gain | Matched surprise after stable versus changing histories |
| Adaptive Bayesian learner | Gain changes with inferred noise and environmental change | Cross noise and change; include enough temporal observations |
| Joint causal/source observer | Surprises revise several coupled explanations | Audit, auxiliary test and cross-source forecasts |
| Bounded local-search observer | A restricted set of explanations is maintained and locally revised | Offered alternative versus unprompted discovery; same data with more search opportunity |

For a simple continuous dynamic control, define \(z_t=z_{t-1}+\epsilon_t\), \(\epsilon_t\sim N(0,v)\), and \(o_t=z_t+\eta_t\), \(\eta_t\sim N(0,s)\). If the previous posterior variance is \(P_{t-1}\), its Kalman gain is

\[
K_t=\frac{P_{t-1}+v}{P_{t-1}+v+s},\qquad
m_t=m_{t-1}+K_t(o_t-m_{t-1}).
\]

This illustrates why a low gain can follow from high observation noise rather than slow learning. Learning unknown \(v,s\) requires an additional inference model. Continuous diffusion and abrupt change points are different environments; do not substitute one for the other merely because each has a change parameter.

A local-search candidate can instead generate a finite number of transitions among causal graphs after each observation. Compare its predictions with an exact observer on the same small graph space. Its output distribution must integrate over unobserved search paths. A response jump alone does not prove local search; it could also reflect a change-point inference or a reporting error.

### C. An information-acquisition policy

For a one-query-then-act reference, let \(V(b)=\max_a E_b[U(a,Z)]\). The net value of buying query \(q\) is

\[
\operatorname{VOI}(q;b)=E_{o\sim p(o\mid b,q)}[V(b^{q,o})]-V(b)-c(q).
\]

Compare this with expected information gain about the task state/model, a cheap-source heuristic and an uncertainty-independent policy. Define stop as an explicit option. Longer query sequences require planning beyond this one-step reference; results against it do not prove globally optimal search.

Cross information value, immediate reward, price and remaining decision horizon. Otherwise curiosity, instrumental research and random exploration can be confounded. Avoid fitting both a free cost multiplier and a free utility scale when only their ratio is observable.

### D. A response model and repeated-run hierarchy

If \(p_t^*\in(0,1)\) is a model's forecast, an initial report model could introduce a latent report variable \(L_t\):

\[
L_t\sim
(1-\pi)N\!\left(b_{\rm report}+g\operatorname{logit}p_t^*+\beta_W W_t,\sigma^2\right)
+\pi\,G_{\rm broad}.
\]

The observed report is \(\widehat p_t=\mathcal R_\Delta[\operatorname{sigmoid}(L_t)]\), where \(\mathcal R_\Delta\) rounds to the protocol's declared probability increments. Use the probability mass of those rounding bins so reported 0 and 1 remain valid. Specify how any exact 0/1 model forecasts are handled before fitting. \(G_{\rm broad}\) is a specified alternative error distribution on the latent report scale, not a justification for discarding observations. Compare it with an episode-level strategy mixture and correlated residuals. An estimated mixture rate cannot distinguish parsing failures from cognitive lapses without separate evidence.

The free reporting gain \(g\) can trade off with an evidence-weight parameter; fixing or calibrating one may be necessary. Source forecasts and conditional predictions help constrain the state but do not guarantee identification. Confidence and choices should have their own operational definitions and observation assumptions; several answers at one checkpoint are not independent samples of the same latent state.

For an estimable parameter on an appropriate transformed scale, use a hierarchy such as

\[
\psi_{i,r,k}=\mu+u_i+v_{i,k}+e_{i,r},
\]

where \(i\) is configuration, \(r\) a repeated run and \(k\) a task family. Compare complete pooling, partial pooling and independent fitting. The interaction \(v_{i,k}\) makes transfer a measured question. Three configurations are insufficient to establish a broad population distribution; with sparse data, retain wide uncertainty and narrowly scoped estimates.

## A concrete discovery task

Start with one small simulated company system whose causal possibilities can be enumerated. Training examples and observed outcomes let participants learn how measurements relate to the company. An explicit-model companion supplies a computational calibration condition. The discovery condition requires inference and does not show likelihood ratios or an answer key.

A representative episode could proceed as follows. This sequence is illustrative; conditions and budgets need simulation and freezing before collection.

1. Present the company, a few resolved analogues and source histories. Obtain a starting forecast and a prediction about a new source's accuracy.
2. Deliver a disappointing operating report compatible with weak demand, a temporary bottleneck or source error. Ask for the outcome forecast and one discriminating auxiliary prediction.
3. Offer a budgeted choice: verify the original measurement, inspect an unaffected segment, inspect backlog, read another headline, run a calculation on existing data, or act now.
4. Reveal the selected evidence. In matched branches, vary whether it addresses the source, the operating explanation or neither. Record whether the participant changes its subsequent information choice and forecasts coherently.
5. Introduce a provenance finding or correction, with enough information to determine which earlier documents are affected. Score correction propagation and persistence in unaffected evidence separately.
6. Request a decision under declared payoffs, permit abstention/review, and reveal the outcome at the scheduled point.

Use additional small mechanisms before claiming company-general behavior. The first module should favor source-versus-auxiliary attribution and diagnostic research choice. Noise/change learning needs a longer feedback sequence and should be a separate module; model-based control can later use a dedicated transition/revaluation task rather than an unidentifiable extra coefficient in this one.

| Contrast | What it can help distinguish | Candidate support to test later |
| --- | --- | --- |
| Source verification versus an operational test | Source distrust versus a business explanation | Provide the specific missing verification |
| Unsupported versus explicitly offered alternative | Hypothesis availability versus evaluation | Supply one testable alternative |
| Same data with extra computation versus a new observation | Deriving implications versus acquiring evidence | Calculation or structured model aid |
| Selective but accurate disclosure versus random sampling | Selection inference versus raw accuracy weighting | Show the sampling/disclosure process |
| Stable noisy history versus genuine persistent change | Noise attribution versus adaptation | Separate a noise summary from a change diagnostic |
| Evidence history available versus constrained recall | Retrieval/memory dependence | External evidence ledger |
| Cost/horizon changes with matched information | Research value and stopping policy | Budget-aware query recommendation |

The offered-alternative condition changes the task and must not contaminate the unprompted-discovery condition. A listed hypothesis space is appropriate for recognition/calibration, but cannot establish free hypothesis generation. For open responses, score executable causal commitments or predictions using a versioned rubric; do not infer mechanisms from a persuasive explanation alone.

A human can perform the same core operations. Keep instructions, available facts and hypothetical payoffs comparable, while measuring comprehension and burden separately. Human reaction time, LLM token use and service latency are different resource measures. Shared tasks do not imply shared parameter distributions, neural mechanisms or population norms.

## Validation and implementation order

1. **Build the model-discrimination sandbox first.** Reuse the joint enumerator and collector; implement a few plausible alternatives and compare simulated trajectories. Include nearby parameter values, boundaries, correlated errors, misinterpreted task rules and out-of-family behavior. Test model recovery as well as parameter recovery and posterior-predictive adequacy.
2. **Choose informative contrasts before scaling.** Bayesian design optimization selects experiments for expected discrimination, rather than repeating convenient conditions. [Cavagnaro et al. (2010)](https://pubmed.ncbi.nlm.nih.gov/20028226/) and [Myung, Cavagnaro and Pitt (2013)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3755632/) give the relevant framework. Begin with an offline-selected fixed short form plus common anchor items. A future adaptive form must log its selection policy and retain independent validation; model-based selection can miss unmodeled failures.
3. **Run a small human/agent usability and costing pass.** Establish whether the alternatives are understood, source histories are usable, and trajectories differentiate the proposed accounts. Repeat configurations with fresh cases and contexts. This is development evidence; size the next stage from its uncertainty and cost, not an arbitrary large trial count.
4. **Freeze the task, model set, observation likelihood and release claims.** Set useful effects in behavioral/decision units. Validate on new mechanisms or cases at the claimed transfer level. Keep the old held-out set retired. Experimental changes require version review and recovery validation under repository rules.
5. **Release interpretable conditional measurements.** Report effects such as audit-driven revision, selection of a discriminating source, correction propagation, adaptation under noise/change and confidence-linked review. Include representative trajectories, uncertainty, repeatability and alternative explanations. A complex coefficient vector need not be the public product.
6. **Then test support selection.** Randomize a narrowly specified aid against no aid and the same aid without personalization. Measure decision outcomes, time/cost and harm. If support helps everyone equally, that can still be a useful product result; it does not establish personalization.

The nearest practical increment is therefore **a compact discovery-and-diagnosis module built on our existing joint observer, with an active research choice and competing process models**. Source intent, longer dynamic learning, metacognition and broader domains can follow as separately identifiable increments. The literature supports this direction; it does not supply a ready-made, fully validated epistemic passport.
