# Discovery evaluation: proposed inference model and experiment

Status: broader design proposal. The [single-case discovery pilot](discovery-pilot.md) is extended by the [matched-study pipeline](discovery-study.md), which fits source-profile, archive-weight, business-prior and response-wording parameters jointly. It includes MCP collection, frozen world-level splits, uncertainty diagnostics and synthetic recovery. Negative-evidence weighting, cross-company learning, broader structural transfer and active research remain proposed. Discovery is the intended main assay; company-dossier/0.2.0 remains a calibration condition.

The fresh company subagent completed all 54 checkpoints using its independently authored calculator and reproduced the disclosed finite-state posterior to numerical precision. This establishes a successful tool-assisted run of the controlled condition. It does not establish how the agent constructs source assessments or business explanations when those relationships are unspecified.

## 1. Two distinct models

The **world generator** produces fundamentals, source observations, documents, dependence and eventual outcomes. Its parameters and truth are private during the evaluation.

The **behavioral inference model** predicts the agent's reports and choices from the public history. It integrates over uncertain source properties and business explanations. Its fitted parameters describe responses in this experiment; they are not recovered neural representations or privileged access to private beliefs.

Merely hiding the current calibration table while still scoring every forecast against a reference that knows the hidden table would create an information advantage. A discovery benchmark must either integrate parameter uncertainty using the same available evidence and declared modeling assumptions, or assess outcome performance and experimental contrasts without declaring one posterior uniquely correct.

## 2. What the respondent receives

- Fictional company dossiers with fixed targets and horizons, financial history, and a simple decision mandate.
- Recurring sources with profiles and historical claims paired with audited resolutions. Track records vary in length and informativeness. The exact reliability/bias parameters are not disclosed.
- Successive headlines, operating tables, analyst notes and inspectable models rendered from a consistent hidden claim ledger. No machine-readable truth bits, target-relative likelihood ratios or evaluator-defined hypothesis labels are supplied.
- Later documents that distinguish temporary operating disruption, underlying demand weakness and source error. Relevant explanations may coexist.
- Source corrections or resolved historical claims that can revise trust and, through that revision, change the interpretation of earlier company evidence.

The first discovery condition should make evidence learnable rather than simply obscure. Use a disclosed sampling/selection policy for historical claims where practicable. Otherwise the behavioral model needs an additional selection process; an archive selected to flatter a source is not an unbiased accuracy sample.

The primary task is business assessment. Avoid instructions that ask the agent to infer the simulator or implement Bayes. Permit arithmetic and document inspection as in a portfolio research workflow. The behavioral model lives on the evaluator side.

## 3. A concrete generative family

Let F_i be company fundamentals, A_i auxiliary operating conditions, K a candidate business relationship/causal structure, and phi_s=(b_s,tau_s) source bias and measurement precision. These are unknown quantities, distinct from the fitted behavioral coefficients psi.

For a genuine primitive measurement j:

$$
x_{ij}\mid F_i,A_i,K\sim\mathcal N(h_j(F_i,A_i;K),\sigma_j^2),
\qquad
y_{sj}\mid x_{ij},b_s,\tau_s\sim\mathcal N(x_{ij}+b_s,\tau_s^{-1}).
$$

For example, an operating reading can have h(F,A)=mu(F)-dA: low underlying demand and a temporary implementation disruption can both lower it. A second measure can depend strongly on A but weakly on demand. Their combination discriminates explanations.

Bias and precision are different: a source can be consistently optimistic yet informative after allowing for the offset, or unbiased on average but very noisy. Historical comparisons must refer to the same quantity and horizon. Errors in predicting a stochastic future outcome are not interchangeable with errors in measuring an already realized quantity.

A provenance graph G identifies shared primitive measurements. Copied stories and deterministic model outputs descend from existing observations. They do not receive independent measurement likelihoods merely because they are separately presented. If provenance is uncertain, marginalize over G; later lineage disclosures can revise earlier inferences. Conditional zero information from a copy also requires no informative selection/republication process.

Documents are controlled renderings of these measurements and their qualifications. In the first version, semantic extraction is evaluated with selected factual probes against the claim ledger. A free-form language likelihood is not assumed to be available. Extraction failure must not automatically become a fitted distrust or negative-evidence parameter.

## 4. Explicit inference over explanations and sources

Let X=(F,A,K,phi,G), and let D_1:t denote only public documents, track records and feedback delivered by step t. The core behavioral model is:

$$
q_t^\psi(X)=
\frac{L_\psi(D_t\mid X,D_{<t})q_{t-1}^\psi(X)}
{\int L_\psi(D_t\mid X',D_{<t})q_{t-1}^\psi(X')\,dX'}.
$$

Sums replace integrals for discrete variables. Initialize with an explicit subjective prior family; process calibration records once. Static company/source states suffice initially. Any later regime-change condition needs a transition model before the observation update.

A target forecast is a posterior predictive quantity, for example:

$$
m_t=\int P(Y_i>c\mid F_i,A_i,K)q_t^\psi(X)\,dX.
$$

Company forecasts, source forecasts and conditional forecasts come from this joint distribution. Updating a source-reliability marginal from an item and then independently reprocessing that item would double count evidence. Shared uncertainty about a recurring source also creates dependence across its reports and across companies; it must remain in the state.

The model must allow a source audit to alter the weight of an earlier company observation, without requiring that observation to be shown again. This retroactive reinterpretation is a useful contrast with a simple fixed-weight accumulator.

The thesis/auxiliary distinction is inspired by [Gershman (2019), How to never be wrong](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf). Maintaining a thesis after counterevidence can follow coherent joint inference; experiments must test the auxiliary explanation's predictions. Structural uncertainty is motivated by [Gershman, Norman and Niv (2015)](https://gershmanlab.com/pubs/GershmanNormanNiv15.pdf). These proposed business/source models are original task specifications, not replications of those papers.

A finite evaluator-side set of candidate structures is a tractable first approximation. It does not imply the respondent was given that set or cannot invent another explanation. Collect a brief alternative hypothesis at selected points and test whether every candidate model misses the response pattern. Unmodeled explanations should appear as lack of fit rather than being forced into a preferred psychological account.

## 5. Source impressions and output terms

A minimal source-prior model is:

$$
b_s\sim\mathcal N(\mu_b,\sigma_b^2),\qquad
\log\tau_s\sim\mathcal N(\alpha_0+\alpha_T T_s+\alpha_F^\top f_s,\sigma_\tau^2).
$$

T_s is an experimentally assigned skeptical versus optimistic source-profile framing; f_s contains prespecified source attributes. These cues must be crossed with actual accuracy, direction of the claim and public track record. alpha_T>0 means greater prior expected precision for the skeptical profile, conditional on the model. With informative track records, Bayesian updating can override that initial impression.

This source-profile effect enters a prior once, when that source is introduced. Actual bad news is not inserted into a pre-evidence trust prior and then counted again as evidence. Claim-direction asymmetry is a separate candidate integration model, introduced only after source inference is recoverable. Document-specific presentation effects require their own observation/encoding model.

Use a separate probability-report model:

$$
U_t=b_{out}+\gamma\operatorname{logit}(m_t)+\beta_{out}W_t+\epsilon_t,
\quad \epsilon_t\sim\mathcal N(0,\sigma_{out}^2),
\qquad \hat p_t=\mathcal R_\Delta[\sigma(U_t)].
$$

W_t is randomized response wording, mapped back to a common target; the grid-rounding operator accommodates endpoint reports through interval probabilities. A wording effect could change deliberation as well as expression. Calling this an output term is a modeling convention, not an established mechanism.

Keep report gain fixed in the primary model and fit constrained alternatives. Global evidence sensitivity and reporting gain can trade off exactly. Calibration probes and additional outputs constrain the problem under explicit assumptions, but do not automatically identify input versus output mechanisms.

The corresponding utility probe can use expected payoffs under q_t and a constrained choice rule. Initially report decision/report alignment separately. Holding investment payoff rules simple leaves discovery uncertainty in the evidence rather than simultaneously introducing unknown risk preferences and security pricing.

## 6. Elicitation and identifying contrasts

Core after every arrival: target forecasts, one predictive interval, a decision, and evidence IDs. Add randomized probes rather than requiring an exhaustive explanation at every step:

- Before selected claims, predict how well this source's next comparable measurement will agree with a later audit, using a fixed tolerance and horizon.
- After ambiguous evidence, elicit a specific conditional forecast: what should the next operating reading look like if the disruption clears? This tests an explanation through its consequences.
- At selected points, extract the relevant number/qualification or identify whether a model contains any new observations.
- Include matched minimal-probe and richer-probe runs to assess whether questioning teaches the intended strategy.

| Mechanism | Required comparison |
| --- | --- |
| Prior source impression | Same track record and claim; randomized source profile |
| Source learning | Different track-record strength; matched source framing |
| Systematic optimism vs noise | Independently vary mean error and error variance in historical measurements |
| Unfavorable-content weighting | Matched source quality and diagnosticity; separately vary factual direction |
| Auxiliary inference | Evidence that separately discriminates disruption and underlying demand |
| Dependence discovery | Independent origins versus shared origin; delayed provenance revelation |
| Output wording | Same information; randomized elicitation framing across matched runs |
| Structural transfer | New company mechanism/template, not simply a new name and random seed |

Source trust forecasts need an operational target; a generic 0–100 trust score is ambiguous. Auxiliary hypotheses can coexist, so do not require their probabilities to sum to one unless the queried categories are explicitly exclusive.

## 7. First fitted model family and validation

Compare small candidates, rather than jointly freeing every coefficient:

1. Fixed source assessments and a fixed business relationship.
2. Learned source bias/precision with joint company/auxiliary inference.
3. Model 2 plus one source-profile prior effect.
4. A structural-mixture alternative, representing uncertainty about the business relationship.
5. A restricted output-framing alternative, with the inference parameters constrained.

Any negative-evidence or duplicate-counting extension should be compared against these explanations, not diagnosed directly from small forecast movement. Estimate parameters from the sequential likelihood of observed reports and choices. Use appropriate dependence/measurement models for outputs from the same checkpoint; multiplying conditionally dependent probes as independent observations overstates evidence.

Fit behavioral coefficients on designated training runs, freeze them, and predict fresh sequences. The predicted learner can continue to update its source beliefs using delivered evidence during held-out runs; that is part of the frozen learning rule, not parameter refitting. Separate within-source transfer from new-source transfer, and hold out entire company templates/mechanisms. Reusing source history means source-linked episodes are not independent statistical clusters.

Perform parameter recovery across plausible ranges, model-confusion checks, and posterior predictive checks before interpreting agent fits. Test whether distinctive behaviors such as retroactive reweighting, conditional forecasts and source-learning curves are reproduced, not just average forecast error. These practices follow [Wilson and Collins (2019)](https://elifesciences.org/articles/49547).

Score eventual forecasts and decisions separately from the behavioral model fit. An excellent fit to an inaccurate agent is explanatory success for the model, not good forecasting by the agent. A reference with the true hidden parameters is an explicitly labeled oracle; it is not the discovery correctness target.

## 8. Proposed next implementation boundary

Retain the current disclosed-model condition. Author one complete discovery episode and its matched variants before expanding the battery:

- Three recurring fictional sources with short and long audited histories.
- Continuous business measurements, one identifiable temporary-disruption explanation and two candidate business relationships.
- Conflicting evidence, a source audit, one derived model and a delayed provenance reveal.
- A source-profile framing contrast crossed with actual record quality and factual direction.
- Core forecasts/intervals/decisions plus a few randomized source and conditional probes.

Simulate the candidate observers over multiple independent runs to choose how many companies and histories support recovery. Source learning needs continuity inside a run; replicate entire runs with explicit context resets. Broader company families and genuinely novel hypotheses are subsequent transfer conditions, not validation claims attached to the first authored case.

Add active research in a separate block once passive discovery is identifiable. Predict research choice using expected decision improvement under the fitted uncertain model, research cost and a constrained choice rule. Do not use the simulator's true reliability parameters to value research for the agent.

Next deliverables: authored dossier/track-record archive, hidden generative graph, public-visibility specification, candidate observer implementations and recovery/model-confusion results. A new battery version and report review precede real discovery evaluations.
