# Modeling how an agent interprets sources

Detailed design proposal, 24 September 2026. **Simulator/discrimination milestone implemented on 25 September; source-learning collection and synthetic acceptance completed on 26 September. Fresh-agent and actual human acceptance remain next.** The [laboratory specification](source-inference-lab.md), [laboratory results](source-inference-results-2026-09-25.md) and [collection specification](source-learning.md) distinguish the implemented subset from the broader design below. This extends the [earlier review](cognitive-modeling-review-2026-09-20.md) in response to the narrative results. Existing batteries, active human sessions and issued evidence remain unchanged.

## Recommendation

Build a small, persistent company-research environment in which a participant learns about sources, encounters deliberately diagnostic conflicts, buys research and makes decisions. Model the participant's construction of source likelihoods and causal explanations from public experience. Predict subsequent reports and choices without supplying the model with the participant's new likelihood judgments as inputs.

The principal product should be a **conditional behavioral profile**: what this configuration is likely to do when source history, selection, provenance, stakes or available support changes. A compact cognitive model is useful when it explains and predicts that response function. Model identity and fitted coefficients remain qualified explanations of behavior.

The first implementation should focus on **source competence versus selective reporting**, with source-label crossover, attribution tests and diagnostic research. This is more specific than adding another general narrative task. Dynamic source changes and unrestricted theory discovery follow as separate extensions.

## 1. What changes relative to our current approach

The current narrative model starts from an elicited joint distribution and four elicited likelihoods. It evaluates what follows from those inputs. Successful fits therefore leave unexplained the transformation from source history and prose to those initial numbers. The latest research task also admits an opposite-of-corroboration heuristic that makes the same choices as information maximization.

The proposed pipeline is:

**Documents and experience → interpretation of the reporting process → inference about the company and sources → research and decision → observable reports.**

Each arrow needs a comparison that can fail. The evaluator should separately ask:

1. Can it predict the participant's next answer from public history?
2. Can it predict how a controlled change to that history changes the answer?
3. Does the explanation transfer across wording and company examples?
4. Does a support intervention improve performance at an acceptable cost?

We should retain consistency controls, but stop treating their completion as evidence that the interpretation layer has been modeled. A participant can be consistently good, with few detectable biases. The evaluation must support that result without manufacturing distinctions.

## 2. Literature commitments and their limits

This is an original synthesis, not a replication or an existing validated instrument. Human findings motivate candidate behavioral explanations; their applicability to our agents must be tested.

| Primary work | Design commitment | Boundary |
| --- | --- | --- |
| [Gershman, 2019, *How to never be wrong*](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf) | An anomaly can change the company thesis, an auxiliary explanation or trust in the measurement. Obtain discriminating predictions about these alternatives. | Persistence alone cannot identify defensiveness or irrationality. |
| [Shafto, Eaves, Navarro & Perfors, 2012](https://papers.djnavarro.net/2012_epistemictrust.pdf) | Separate information available to a source from its reporting policy. | Their implemented deception example concerns an always-lying informant. Our selective-disclosure mechanism is an extension. |
| [Frank & Goodman, 2012](https://langcog.stanford.edu/papers/FG-science2012.pdf) | Interpret a message partly through the alternatives the speaker could have selected. | Their referential language game does not validate our financial-source task. |
| [Kamenica & Gentzkow, 2011](https://web.stanford.edu/~gentzkow/research/BayesianPersuasion.pdf) | Information provision itself can be chosen to influence a decision. Include truthful but selective sources. | Their sender commits to an information structure and honestly reveals its realization. Our post-observation selection task has different assumptions; we are not importing their equilibrium result as its solution. |
| [Ullman, Goodman & Tenenbaum, 2012](https://www.tomerullman.org/papers/tlss-final.pdf) | Distinguish constructing an explanation from updating within one already offered. | The proposed task initially searches a bounded explanation space. It does not identify a language model's internal search algorithm. |
| [Dasgupta, Schulz & Gershman, 2017](https://gershmanlab.com/pubs/Dasgupta17.pdf); [Bramley et al., 2017](https://www.bramleylab.ppls.ed.ac.uk/pdfs/bramley2017neurath.pdf) | Compare maintaining and locally revising a limited explanation set with integrating over alternatives. Test interventions and predictions that separate them. | Sudden revision or order dependence alone is insufficient evidence for sampling or local search. |
| [Piray & Daw, 2021](https://www.nature.com/articles/s41467-021-26731-9) | Separate noisy observations from changes in the process that generates them. | Estimating both needs a temporal design; an isolated reversal is inadequate. This belongs in a later extension. |
| [Gershman, 2018](https://gershmanlab.com/pubs/Gershman18.pdf); [Lieder & Griffiths, 2020](https://cocosci.princeton.edu/papers/liederresource.pdf) | Create research choices on which uncertainty-sensitive policies and cheaper heuristics disagree; make information cost and decision benefit explicit. | We adapt the experimental logic, rather than claim to reproduce their exploration or resource-allocation models. |
| [Fleming & Daw, 2017](https://www.princeton.edu/~ndaw/fd17.pdf) | Separate an event forecast from the participant's ability to detect an error and request useful review. | We will not infer metacognitive quality from confident language or distance from 50%. |
| [Myung, Cavagnaro & Pitt, 2013](https://cpb-us-w2.wpmucdn.com/u.osu.edu/dist/0/91362/files/2020/06/ADOTutorial.pdf) | Choose cases by expected discrimination between explicit models. | Design optimization is conditional on the candidate set; fixed controls and challenges outside that set remain necessary. |
| [Wilson & Collins, 2019](https://elifesciences.org/articles/49547); [Palminteri, Wyart & Koechlin, 2017](https://pubmed.ncbi.nlm.nih.gov/28476348/) | Recover models as well as parameters, simulate failures, and test absolute adequacy as well as relative fit. | A winner among inadequate models does not justify a cognitive interpretation. |
| [Hedge, Powell & Sumner, 2018](https://link.springer.com/article/10.3758/s13428-017-0935-1) | Measure within-configuration repeatability separately from between-configuration differences. | A strong experimental effect need not support reliable individual ranking. |
| [Binz & Schulz, 2023](https://doi.org/10.1073/pnas.2218523120); [Coda-Forno et al., 2024, CogBench](https://arxiv.org/abs/2402.18225) | Use behavioral experiments, perturbations and configuration comparisons to study agents. | Their historical model results do not establish the behavior of the current evaluated configuration. |

These commitments change the design, rather than merely provide citations for another evidence-weight coefficient.

## 3. A learnable company world

### Persistent sources, changing companies

The participant acts as an analyst assessing a sequence of fictional companies. Each case has a resolvable state H, initially a binary strong/weak demand state. The same sources recur. Memory persists **within a source environment**; fresh contexts begin between independently generated environments. Resetting after every company would remove much of the source learning we want to measure.

Three recurring sources are sufficient initially. Internally, vary measurement quality and reporting selection independently. A source might have accurate access and publish representative records, accurate access and publish favorable records, or noisy access with representative reporting. Source names, apparent institutional status and visual polish are crossed with those mechanisms across assignments. A later provenance module introduces shared upstream records; correlated sources are not silently treated as independent in the first version.

Participant-visible material consists of short headlines, the underlying customer records when inspected, source archives, simple model calculations and eventual company resolutions. Documents are rendered from a frozen factual ledger. The first release uses literal, unambiguous claims; ambiguous language and paraphrase transfer are separate probes. An author should not invent a persuasive sentence and then attach an arbitrary likelihood to it after collection.

The initial learning archive contains resolved cases and dated source reports. Some records reveal what was sampled and what was omitted. Company outcomes and occasional source-process audits supply different information. A source may report a true fact yet provide poor evidence about the company. Operationally describe selection behavior; do not infer malicious intent merely from an unrepresentative sample.

### Three experimental modes

| Mode | What is available | Purpose |
| --- | --- | --- |
| Disclosed control | Sampling and reporting rules are given, with a worked practice example | Check understanding and computation under specified assumptions |
| Guided discovery | Resolved experience and source-process evidence; no likelihood tables; a small explanation menu | Test learning and comparison of reporting mechanisms |
| Less prompted discovery | Same evidence; company forecasts, research and decisions, without routinely presenting the explanation menu | Test behavior with less help from our questions |

Use separate matched environments or participant groups for the modes. A participant who has just learned the exact mechanism from the disclosed condition cannot subsequently supply a clean discovery observation about that mechanism. Randomize probe burden too: dense conditional elicitation versus sparse forecasts and choices. It is an empirical question whether the questions improve, impair or leave performance unchanged.

### Private truth and public uncertainty

The generator knows the company state and source mechanism. The cognitive observer must infer from exactly the public record. Its predictions integrate over unknown source parameters. Discovery participants may have reasonable prior differences; evaluate sensitivity to plausible priors and forecasts of subsequent observable events. Hidden generator parameters are not a privileged answer key for what the participant should believe before sufficient evidence arrives.

Keep two case banks: deliberately selected diagnostic contrasts for identifying behavior, and fresh cases sampled from a declared distribution for outcome scores. Calibration or expected task value on the latter must not be inferred by averaging the former's artificial balance.

## 4. A concrete contrast with a calculable answer

Consider a source reporting the exact fact **“Four of five sampled customers expanded their orders.”** The sampling frame and period are identical across conditions. In an illustrative evaluator world:

- Under strong demand, each customer's expansion probability is 0.7; under weak demand it is 0.3.
- Customers and the candidate five-customer panels are independent conditional on the company state.
- The prior probability of strong demand is 0.5.
- In one condition, the source reports one random panel. In another, it examines J panels and reports the panel with the largest expansion count, truthfully. The recipient knows that this is the maximum, not merely an unspecified selected panel.

Let K follow Binomial(5, p_H), and let F_H be its cumulative distribution. For a maximum-of-J report:

\[
P(K_{\max}=4\mid H,J)=F_H(4)^J-F_H(3)^J.
\]

The exact implications, calculated from this proposed toy world, are:

| Reporting rule | P(report \| strong) | P(report \| weak) | Likelihood ratio | P(strong \| report) |
| --- | ---: | ---: | ---: | ---: |
| One random panel | 0.360150 | 0.028350 | 12.704 | 92.70% |
| Best of four panels | 0.429473 | 0.107867 | 3.982 | 79.93% |
| Best of ten panels | 0.158260 | 0.244448 | 0.647 | 39.30% |

The last row is diagnostic: if ten opportunities produced no five-of-five panel, that absence itself matters. A literal-accuracy rule, a blanket distrust rule and a model of the selection process make different predictions. Also test five-of-five reports and unfavorable-selection counterparts. A rule that discounts every statement by a selected source should fail on some of those contrasts.

These numbers are **not empirical agent findings** and are normative only under the stated toy assumptions. In discovery mode, the participant learns about sampling from experience and audits, so the observer integrates over its uncertainty about J and the company process. An unspecified “best customers” phrase is not enough to warrant the 39.30% answer. The sharp calculation first verifies that the proposed manipulation can separate candidate policies.

## 5. Explicit model architecture

Distinguish environment parameters θ from participant/configuration parameters ψ. A source's actual accuracy belongs to θ; a participant's prior sensitivity to an institutional label belongs to ψ. Mixing these would recreate the original attribution problem.

### A. Generating a document

Let D₁:J be a source's private candidate samples, I its selected sample index, O whether it publishes, and Y its message. A bounded source model factorizes as:

\[
P(D_{1:J},I,O,Y\mid H,M,\theta_s)
=P(D_{1:J}\mid H,M,\theta_s^{\mathrm{measure}})
P(I,O\mid D_{1:J},\theta_s^{\mathrm{select}})
P(Y\mid D_I,\theta_s^{\mathrm{report}}).
\]

M specifies the business/measurement relationship. Include explicit null values when O = 0. Start with faithful rendering of the selected private sample, so measurement quality and publication selection are the two uncertain source processes. Add transcription or fabrication only when a separate inspection makes those parameters distinguishable.

For a simpler publication gate, let a private binary signal X have accuracy r_s and publication probability σ(a_s + b_s X). If the evaluation exposes a known reporting opportunity, the observation is (O,Y):

\[
P(O=1,Y=y\mid H,\theta_s)
=P(X=y\mid H,r_s)\,\sigma(a_s+b_s y).
\]

If the data are sampled *only from published messages*, the likelihood must instead condition on publication and divide by P(O=1 | H, θ_s). Specify which sampling protocol is in use. This distinction matters: selectivity does not automatically weaken every report under every observation scheme. The maximum-of-J example is a different, explicit selection policy, not an interchangeable use of this gate formula.

### B. Inferring the source and the company

For public history h_t, the joint learner maintains a behavioral belief distribution:

\[
b_t(M,H,\theta)\propto
P(o_t\mid M,H,\theta,q_t,h_{t-1})\,
b_t^-(M,H,\theta).
\]

Within a static company, b_t^- is the previous posterior. A new company draws a new H while retaining learned source parameters. A later dynamic extension introduces an explicit transition kernel for changing source regimes. It cannot be emulated by silently changing the meaning of H.

The source-label hypothesis enters a prior, for example:

\[
r_s\sim\mathrm{Beta}(\nu\mu_s,\nu(1-\mu_s)),\qquad
\operatorname{logit}\mu_s=\beta_0+\beta_{\rm label}L_s.
\]

L_s is a randomized source feature; ν governs prior concentration. Label effects on competence and label effects on selection are distinct candidate hypotheses. Begin with one such pathway per comparison. Do not repeatedly reapply the label prior at every report.

Initial forecasts and source predictions are **outputs of this learner**. They enter the observation likelihood when fitted, but they do not replace its source/world inference state with unconstrained per-case numbers. This is the essential difference from the present narrative model.

### C. A small set of competing accounts

| Candidate | Core computation | Discriminating test |
| --- | --- | --- |
| Flat source accuracy | Learns one correctness propensity per source; treats presented evidence as representative | Accurate but selective sources; omitted samples; changes in publication coverage |
| Joint source-process learner | Integrates company state, measurement quality and selection | Cross-source predictions and selective revision after process audits |
| Persistent label influence | Source identity affects a prior, or repeatedly gates evidence in a competing descriptive model | Same history with labels crossed; increasing contrary experience; sign reversal |
| Error-driven learner | Updates source expectations using rₜ₊₁ = rₜ + α(yₜ − rₜ), when correctness y is actually revealed | Equal latest error after histories with different sample sizes; ordering and transfer |
| Limited explanation set | Maintains one or a few reporting mechanisms and revises locally | Neutral opportunity to reconsider, candidate explanations, and predictions under counterfactual source behavior |

Use a common observation model where possible. Compare pairwise or nested additions on the cases that distinguish them. Do not fit the Cartesian product of every hypothesis. A label-weighted flat-accuracy account can be an explicit challenge model if neither base account captures the data.

For the limited-set candidate, a bounded formalization is:

\[
\mathcal H_{t+1}\sim K_{\psi}(\cdot\mid\mathcal H_t,o_t,B),\qquad
\widetilde b_t(M)\propto P(h_t\mid M)P_\psi(M)\mathbf1[M\in\mathcal H_t].
\]

B is the available deliberation budget. The implemented likelihood must integrate over unobserved search paths. Begin with an enumerable mechanism library; allow public free-text hypotheses as secondary evidence. This formalization is a behavioral approximation, not a statement that the agent literally executes that search.

### D. Research and final decisions

For a one-query-then-act task with explicit payoff U(a,H), define:

\[
\operatorname{VOI}(q;b)=
\mathbb E_o[\max_a\mathbb E_{b^{q,o}}U(a,H)]
-\max_a\mathbb E_bU(a,H)-c(q).
\]

Compare a policy using this value with expected information gain about a declared target, lowest-price research, checking the uncorroborated explanation, and stopping. A stochastic choice layer can use P(q | b) ∝ exp(τ V(q)); fix payoff units before interpreting cost sensitivity or choice temperature. Those scales otherwise trade off.

Use cases where an audit resolves much uncertainty about an irrelevant quantity, while a smaller query can change the investment decision. Vary price and whether the source will be used again. The latter creates potential value in learning source quality for future cases; initially evaluate that in a separately specified two-step horizon, not against the one-step formula above.

### E. Reports and confidence

A minimal response model for an interior model forecast p* is:

\[
\ell_t=b_{\rm report}+g\operatorname{logit}p_t^*+u_{\rm episode}+\epsilon_t,
\qquad \widehat p_t=\mathcal R_\Delta[\sigma(\ell_t)].
\]

Use the probability of the observed rounding bin, including endpoint bins. Exact logical 0/1 predictions need an explicitly declared endpoint/report-error mechanism. Model episode-correlated errors; do not count four constrained joint entries as four independent observations. A separate declared error mixture can accommodate occasional failures, retaining every response and checking whether that mixture actually predicts their pattern.

Reporting gain can trade off with evidence sensitivity; prior concentration can trade off with feedback learning rate. Use disclosed controls to constrain the former, and compare fixed-Bayesian versus error-driven families for the latter. Carry calibration uncertainty forward. If meaningful parameter ranges remain confounded, merge the interpretation or report a response contrast rather than a parameter.

Keep event probability separate from confidence that one's reasoning or choice is correct. Add occasional review allocation and error detection tasks with verifiable outcomes. Do not add a generic “confidence” box to every checkpoint without specifying what its number means.

## 6. Diagnostic manipulations

### Identity and experience crossover

Cross institutional label with source mechanism and archive strength. Include a novel neutral source. Revisit the same evidence after a clearly described brand change that preserves the source's identity, and separately introduce a genuinely new source. This separates response to a label from appropriate transfer of known history.

Cross favorable/adverse factual content with positive/negative wording and with agreement/disagreement with the participant's preceding forecast. “Negative,” “disconfirming” and “skeptical source” cannot share one coefficient when the design always changes them together. Start with one clean label manipulation; add the valence factorial only after its structural contrasts pass simulation.

### Responsibility for an anomaly

Present a report that conflicts with an established company forecast. Create matched continuations containing a measurement audit, an independent customer sample, or evidence of a shared upstream source. Before seeing the outcome, predict a new report from the original source and from an independent source, using sparse probes on assigned cases.

Different explanations should change those forecasts differently. Lowering the company forecast, lowering trust in the original source, and discovering shared provenance are testable accounts when they constrain future observations. An unconstrained free explanation after every answer is not enough.

### Evidence-preserving retraction

Reveal that one document was derived from another or that a transcription error affected specified records. Keep unaffected independent evidence visible. Measure which conclusions change, and whether predictions about unaffected evidence are preserved. A generic “be more skeptical” response should make different predictions from targeted correction.

### Discovery versus recognition

First collect a decision and a forecast without listing mechanisms. In separately assigned continuations, provide a plausible mechanism, an equally salient irrelevant mechanism, or neutral additional deliberation. A hypothesis earns evidential credit by predicting an unseen audit or counterfactual, rather than merely appearing in fluent prose. Distinguish accepting a supplied explanation from proposing one and using it successfully.

### Public-history branches

For agents, replay the same accepted public history into fresh contexts and vary one next document, price or source feature. These are matched **public-history** continuations, not identical copies of an unobserved internal state. Repeat control branches to estimate ordinary response variability. For humans, use counterbalanced analogous cases or randomized groups; do not pretend a human can unsee a branch outcome.

### Memory and deliberation

Compare a ledger reorganizing already available evidence with the original document stream and with an equally substantial generic review. A calculator/model table can contain exactly the same information but reduce computational demands. Record the assistance as a distinct configuration. Improvements would support an operational recommendation even if their internal cause remains ambiguous.

### Later temporal extension

Once static source selection is interpretable, introduce sustained source-quality changes, isolated noisy mistakes and returns to an earlier source context. Company state remains fixed within each case; source properties can change between cases. Sequences must be long enough for the candidate models to predict different patterns. A fixed learning rate, inferred change point and context-specific memory can then be compared without adding unidentifiable dynamics to the first module.

## 7. Choosing trials and deciding whether the model is adequate

Generate many candidate histories before real collection. For each, compute the response distributions predicted by the candidate models over plausible parameters and response noise. Select a compact set with substantial disagreement. For adaptive selection, a possible utility is:

\[
d^*=\arg\max_{d\in\mathcal D}
I(C,\psi;Y\mid d,\mathcal E)-\lambda\,\operatorname{cost}(d),
\]

subject to coverage constraints. C indexes **cognitive candidate models**, distinct from the business mechanism M. Y is the forthcoming participant response, and ℰ is the accumulated evaluation record. Initially use this objective offline to choose a fixed battery; introduce online adaptation only after auditing it.

Retain common anchor cases, repeated cases and unpredictable challenge cases outside the fit family. Record the selection policy and every selection probability where randomized. A model can confidently explain only the corner of behavior its designer chose to inspect; untested regions must remain visibly uncovered. Any adaptive likelihood conditions on the actual selection policy, and final predictive assessment uses a separately frozen case distribution.

Required development checks:

1. **World correctness:** enumerate likelihoods, sampling denominators and provenance. Verify that rendered facts match the private ledger. Manually solve cases such as the panel-selection example.
2. **Model discrimination:** produce confusion matrices across plausible parameter regions, especially near behavioral equivalences. Simulate heuristics and error patterns outside the fitted family. Report “indistinguishable” when warranted.
3. **Parameter/contrast recovery:** include off-grid parameters, correlated report error, endpoint reports and occasional parsing failures. Recover the practical contrasts we plan to put in passports, not only abstract coefficients.
4. **Identification audit:** inspect predictive sensitivity and parameter tradeoffs. Remove coefficients that the chosen observations cannot constrain. A narrower estimand is preferable to a precise-looking arbitrary decomposition.
5. **Prospective prediction:** freeze fits and model weights before new companies or continuations. Later public evidence may update the observer; new participant reports may not be inserted as free priors or likelihoods during the primary prediction test.
6. **Absolute adequacy:** test the joint pattern of company forecasts, source predictions, choices and corrections. A low average error must not conceal systematic wrong-direction predictions. Permit all candidate models to fail.
7. **Repeatability and transfer:** distinguish exact-repeat variation, wording effects, new-company transfer and new-domain transfer. A label such as “source selective” needs its own scope and reliability evidence.
8. **Practical value:** compare predicted behavior and support selection with fixed observers, simple recent-performance summaries and pooled profiles. Individual fitting is optional if a shared model predicts just as well.

Numerical release thresholds should follow a declared practical tolerance, then be frozen before confirmation. For example, if a passport consumer changes its action for a five-point forecast shift, simulations should assess recovery and interval coverage at that scale. Five points is a proposed policy tolerance, not a literature-established universal cutoff. No fixed episode count alone guarantees identification.

Outcome forecasting, behavior prediction and decision performance need separate scores. Report Brier/log score against outcomes on the sampled test distribution; predictive likelihood and error against participant responses; and expected/payoff performance net of research cost under the declared task. Uncertainty calculations group dependent observations by source environment, not by individual probability entry.

## 8. Cognitive security through support experiments

The actionable product is an observed response to a support, alongside its baseline scope. Candidate mechanisms guide which support to test:

| Observed pattern and competing explanation | Candidate support | Required discriminating check |
| --- | --- | --- |
| Selected truthful evidence treated like random evidence | Show sampling coverage and unselected records | Compare new information from the audit with a ledger of already known selection facts; distinguish learning from accessibility |
| Identity influence persists despite contrary experience | Present a source-history summary beside each report | Cross labels and records; test whether useful source information is retained |
| Multiple headlines receive excess weight after common provenance is known | Show the evidence lineage | Preserve independent corroboration; measure overcorrection as well as correction |
| Useful alternatives are recognized but rarely considered unaided | Ask for one discriminating alternative and an observable prediction | Compare generic review and an equally salient unhelpful alternative; score later predictions |
| Research continues when it cannot change the decision | Display remaining budget and the decision threshold | Include cases where further research is valuable, so indiscriminate stopping cannot pass |

Allocate supports on development evidence, freeze the selection rule, and evaluate fresh cases. Compare no support, generic review, the candidate support offered universally, and profile-selected support. Include support cost and harms such as excessive distrust or lost independent evidence. An improvement from universal support is a useful result; personalization needs its own incremental benefit.

For human use, preserve voluntary review and legible explanations. The desired outcome is improved reasoning and decision performance under the person's task objectives. A security profile should not become a publicly exposed collection of personalized persuasion instructions; detailed vulnerabilities and private transcripts need selective disclosure. This is a product access-design proposal, not a claim that current artifacts enforce it.

## 9. The passport that would result

Prefer a small set of conditional findings over one broad quality score. Examples below are **illustrative statements, not current results**:

- “Institutional labels affect first impressions; the difference diminishes with resolved source history.”
- “Responds to inaccurate statements, but under-adjusts for favorable sample selection when the sampling denominator is absent.”
- “Corrects conclusions that depend on a retracted document while preserving independent evidence.”
- “Chooses useful source audits when a source will be reused; purchases fewer when only the immediate decision remains.”
- “A source-history ledger improves outcome forecasts in the tested cases; additional generic review does not show the same improvement.”

Each finding should carry its measurement and units, uncertainty, case and source counts, repeatability, protocol/configuration scope, counterexamples, competing explanations, predictive status and evidence digests. Report the dense-versus-sparse elicitation condition and any assistance explicitly. Machine consumers should be able to distinguish **observation**, **supported predictive explanation**, and **measured support benefit**.

A machine policy can request a versioned capability such as sensitivity to known sample selection under sparse prompting, with coverage and evidence requirements. It should not consume a naked `trust_bias = 0.2` with no definition. The identity/signature layer can bind this claim and its configuration; it cannot turn an unresolved model interpretation into a verified fact.

## 10. Bounded implementation sequence

**First: prove the design discriminates before collecting agents.** Implement the static company generator, representative versus selective source processes, a flat-accuracy learner, a joint source-process learner, the shared report model and a few fixed research policies. Produce an auditable simulation notebook/report, likelihood examples, disagreement map and model-confusion matrix. This is the next coding milestone, ahead of another narrative collection or a large passport adapter.

**Second: a small feasibility collection.** A starting budget proposal is four source environments, each with 12 resolved learning cases and four unrevealed test companies: 48 learning cases and 16 tests. A learning case can require one company forecast plus outcome feedback; test companies add a bounded query and revised forecast. Use one recurring context per environment. Compare sparse and diagnostic prompting on separate matched assignments. Counts and source exposure must be revised by simulation if the proposed contrasts cannot be recovered; this is a budget sketch, not a sufficient sample-size claim. Measure human burden before promising a completion time.

**Third: repeat and challenge the interpretable effects.** Repeat a subset with the same configuration, cross source labels, and test unfamiliar wording plus new companies. Add a second configuration to determine whether the measurement can distinguish behavior, without assuming it must. Lock the first fit before confirmation. Keep human and agent observation models and context policies explicit.

**Fourth: one targeted support experiment.** Choose a repeatable limitation or a valuable general support. Test the frozen intervention comparison with cost included. If all variants perform well, publish the capability and its tested boundary; move to a genuinely different contrast rather than intensifying a task solely to induce failure.

**Then: broaden coverage.** Add source drift versus noise, provenance, bounded explanation search and a second domain, one identification problem at a time. The company module supplies a domain profile; it does not by itself establish a general human/agent epistemic phenotype.

## Decision

The proposed change in direction is concrete: invest next in a model of **how the participant learns the evidence-generating process**, and choose observations that can falsify its competing explanations. The near-term deliverable is a working source-inference design with demonstrated model discrimination. Passport integration should follow the first useful predictive contrasts, while preserving the bounded descriptive evidence we already have.
