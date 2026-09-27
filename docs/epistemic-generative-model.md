# A generative model of epistemic dispositions

Design proposal, 27 September 2026. It follows the [literature review](literature-review-2026-09-27.md), three templated dossier acceptances, and the [positive control](research3-positive-control-2026-09-27.md). Nothing here is implemented. It changes no battery, evaluator or evidence. Section 10 lists the decisions it needs.

## 1. Stance: from "how far from Bayes?" to "which Bayesian?"

Every task so far fully specified the environment. Reference rates were numeric, and background facts settled dependence, disclosure and reliability. That leaves one correct answer, so individual variation can only appear as error.
- **Capable configurations** made almost none: every neglect weight was zero.
- **Weaker configurations** showed errors, such as GPT-5.6 Luna taking fabricated figures at face value. Those are capability measurements, likely specific to a model generation.

Computational psychiatry parameters are identifiable for the opposite reason. The task leaves the rational response dependent on the subject's own assumptions or costs:
- a volatility prior in the hierarchical Gaussian filter (HGF);
- a sampling cost in the beads task;
- a prior over an adviser's intentions.

Two ideal observers with different parameters behave differently, and neither is wrong. Rational analysis makes the same move: apparent biases become rational under different environmental assumptions, as with the rarity assumption in optimal data selection ([Oaksford & Chater 1994](https://doi.org/10.1037/0033-295X.101.4.608)).

**The framework models a respondent (agent or human) as an approximately Bayesian observer and decision maker with individual parameters of three kinds.** A fourth, measurement layer describes how reports relate to the modelled posterior.

| Class | What the parameters are | Normative status |
| --- | --- | --- |
| Environmental assumptions | Priors about how evidence is produced: source reliability, dependence, disclosure, volatility | Neutral when the task leaves them unspecified |
| Valuation | Worth placed on certainty beyond decision value | Neutral; a preference |
| Computational fidelity | Weight given to evidence relative to its likelihood ratio; recognition of invalid evidence | Deviations are errors; capability phenotypes live here |
| Measurement | Response precision and bias of reports and choices | Describes the report channel |

Reported probabilities remain observations of this model, not access to internal belief. Parameters are behavioral descriptions under stated task conditions. Psychiatric analogies are interpretive aids, never diagnoses.

## 2. The model

A company's demand is \(H \in \{0, 1\}\) with public prior \(\pi\). Evidence arrives as reports from sources, with provenance and disclosure structure that may be stated, partly cued or unspecified. The respondent's posterior log-odds after the evidence \(E\) is

\[
\ell(E) = \operatorname{logit}\pi + \gamma \sum_j w_j(\theta)\,\Lambda_j ,
\]

where:
- \(\Lambda_j\) is the log-likelihood ratio of item \(j\) under its stated or learned likelihoods;
- \(w_j(\theta) \in [0, 1]\) is the item's effective weight given the respondent's environmental assumptions (below);
- \(\gamma\) is evidence sensitivity, the Grether-style weight: below one is conservatism, above one overreaction.

When structure is fully stated, every \(w_j\) is fixed by the task, which is the regime we have tested so far.

### 2.1 Credulity: default trust in unvetted sources

A source is correct with probability \(r_s\). Where no track record is given, the respondent's prior is \(r_s \sim \mathrm{Beta}(\mu_r \kappa_r, (1-\mu_r)\kappa_r)\). After \(k\) correct reports in \(n\), the expected reliability is

\[
\mathbb{E}[r_s \mid k, n] = \frac{\mu_r \kappa_r + k}{\kappa_r + n},
\qquad
\Lambda_j = \pm \log\frac{\mathbb{E}[r_s]}{1 - \mathbb{E}[r_s]} .
\]

- **\(\mu_r\) (default trust):** a high value is credulous, a low value sceptical.
- **\(\kappa_r\) (inertia of trust):** how many observations it takes to overrule the default.

Human analogues are advice-taking ([Behrens et al. 2008](https://www.nature.com/articles/nature07538)) and Bayesian testimony models (Bovens & Hartmann).

### 2.2 Dependence prior: are matching reports independent?

Two reports carry matching content with ambiguous provenance. The respondent's prior probability of a shared origin is \(\delta\). Provenance cues \(c\) (attribution, identical figures, timing) update it by their likelihood ratio \(\mathrm{LR}_c\):

\[
\operatorname{logit}\hat\delta = \operatorname{logit}\delta + \log \mathrm{LR}_c ,
\qquad
w_2 = 1 - \hat\delta .
\]

- \(\delta \to 0\) treats all corroboration as independent evidence: "correlation neglect" appears as a prior rather than an error.
- \(\delta \to 1\) assumes echoes by default, which is scepticism of corroboration.

When the text makes dependence certain, \(\mathrm{LR}_c\) dominates and \(\delta\) is unidentifiable. That was the situation in the 0.1–0.2 dossiers.

### 2.3 Suspicion of silence: what an omission implies

A sender may withhold an item \(x \in \{\text{good}, \text{bad}\}\). With prior probability \(\sigma\) the sender is strategic and withholds exactly the bad items. Otherwise it omits items at a base rate \(\rho\), independent of \(x\). Then

\[
P(\text{omit} \mid \text{bad}) = \sigma + (1-\sigma)\rho,
\qquad
P(\text{omit} \mid \text{good}) = (1-\sigma)\rho ,
\]

and an omission contributes \(\Lambda_{\text{omit}} = \log\frac{P(\text{omit}\mid\text{bad})}{P(\text{omit}\mid\text{good})}\), passed through the item's own likelihoods. This is the argument from ignorance in Bayesian form ([Hahn & Oaksford 2007](https://doi.org/10.1037/0033-295X.114.3.704)): absence of evidence is as informative as the prior that evidence would have appeared. \(\sigma\) reads as suspicion of silence. The 0.2 background fact "companies never omit a KPI that met guidance" fixed \(\sigma = 1\) and removed the parameter.

### 2.4 Volatility: how fast reliability is expected to change

Source reliability can drift or switch. We use the binary three-level HGF ([Mathys et al. 2011](https://www.frontiersin.org/articles/10.3389/fnhum.2011.00039/full), [2014](https://www.frontiersin.org/articles/10.3389/fnhum.2014.00825/full)):
- \(x_1\): whether the source is correct on a trial;
- \(x_2\): the logit tendency of the source to be correct;
- \(x_3\): log-volatility.

The perceptual parameters are:
- **\(\omega_2\) (tonic volatility of reliability):** a high value is "labile trust", quick revision after a surprise.
- **\(\vartheta\) (meta-volatility):** how strongly the respondent believes volatility itself changes.
- **\(\kappa\) (coupling):** fixed at one, following the HGF identifiability guidance.

The learning rate on \(x_2\) is precision-weighted and rises with estimated volatility. This separates "this source is noisy" from "this source has changed", as in [Piray & Daw (2021)](https://www.nature.com/articles/s41467-021-26731-9). A single change-point observer with hazard \(h\) is the simpler competing model. Human analogues are volatility learning ([Behrens et al. 2007](https://www.nature.com/articles/nn1954)) and inferring an adviser's intentions ([Diaconescu et al. 2014](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003810)). Overestimated volatility is studied in anxiety and autism; that is an analogy only.

The HGF is fitted to trial-wise probability reports and choices. Reported probabilities make the perceptual model far better identified than binary choices alone.

### 2.5 Value of certainty

Beyond payoff, the respondent values certainty in its final belief. With a final posterior \(p\), payoff \(U(a, H)\) and certainty \(C(p) = |2p - 1|\) (alternatively \(1 - \mathcal{H}(p)\)), actions maximize

\[
\mathbb{E}_p[U(a, H)] + \lambda_c\, C(p) .
\]

For a purchasable check with outcomes \(s\) and price \(q\), the subjective net value is

\[
V(p) = \mathbb{E}_s\!\left[\max_a \mathbb{E}_{p_s} U(a, H) + \lambda_c C(p_s)\right]
- \left[\max_a \mathbb{E}_p U(a, H) + \lambda_c C(p)\right] - q .
\]

Because \(C\) is convex, a check has positive value to anyone with \(\lambda_c > 0\), even when no result could change the action. **A check with zero decision value is therefore bought only through \(\lambda_c\).** That is the direct identification (compare paying for confidence: [Eliaz & Schotter 2010](https://ideas.repec.org/a/eee/gamebe/v70y2010i2p304-324.html)). \(\lambda_c > 0\) reads as intolerance of uncertainty: over-checking, reluctance to decide at intermediate probabilities. \(\lambda_c < 0\) reads as impatience or information aversion. The positive control's under-buying by Luna, 3 surveys where 8 were worth buying, would sit on the negative side. The same term can also govern abstention and deferral when those options are offered.

### 2.6 Evidence sensitivity and recognition of invalid evidence

\(\gamma\) scales all likelihood ratios. An optional signal-strength nonlinearity \(\gamma(S) = k S^{\beta - 1}\) allows overinference from weak signals and underinference from strong ones ([Augenblick, Lazarus & Thaler 2025](https://arxiv.org/abs/2109.09871)). Recognition of invalid evidence (the fabricated reports of 0.3) enters as a per-type detection probability \(d_t\): an undetected fabrication receives \(w_j = 1\). These are computational-fidelity parameters, reported separately from dispositions.

### 2.7 Response model

Reports are \(\hat p = \mathcal{R}_{0.01}\!\left[\operatorname{sigmoid}(\ell + b + \varepsilon)\right]\), with \(\varepsilon \sim N(0, \tau^2)\) and rounding to whole percentages. Choices are a softmax over subjective values with temperature \(\beta_d\).
- **Precision \(1/\tau\)** was our most robust configuration difference (repeat differences of 2.8 against 10.8 points). It is the most reliable parameter class in human computational work.
- **Bias \(b\)** captures a shift in the report channel.

## 3. Parameters at a glance

| Parameter | Reads as | Class | Identified by |
| --- | --- | --- | --- |
| \(\mu_r\), \(\kappa_r\) | Default trust; inertia of trust | Assumption | Reports on unvetted sources, then track records (T1) |
| \(\delta\) | Prior that matching reports share an origin | Assumption | Ambiguous corroboration with graded cues (T2) |
| \(\sigma\) | Suspicion of silence | Assumption | Withholding with unstated sender type (T3) |
| \(\omega_2\), \(\vartheta\) | Expected change in reliability; volatility of volatility | Assumption | Advisers whose accuracy changes across stable and volatile phases (T4) |
| \(\lambda_c\) | Value of certainty | Valuation | Checks with zero decision value; varied prices; abstention (T5) |
| \(\gamma\), \(\beta\) | Evidence sensitivity; nonlinearity | Fidelity | Signal-strength sweep (T6) |
| \(d_t\) | Recognition of invalid evidence by type | Fidelity | Fabricated reports (existing 0.3 families) |
| \(\tau\), \(b\), \(\beta_d\) | Response precision, bias, choice noise | Measurement | Every task; replicated cases |

## 4. Identifiability principles

1. **Underdetermination by design.** Each parameter must be the only thing that changes the rational response in some condition. Conditions where it is irrelevant serve as controls. The fully stated tasks we already have become calibration controls for \(\gamma\), \(\tau\) and \(b\).
2. **Separate the assumption from the update.** Elicit prior predictions before evidence where it is natural, as a behavioral commitment rather than self-description: for example, "how likely is it that the next outlet's figure repeats an earlier report?". The model predicts both the stated expectation and the later update.
3. **Cross parameters orthogonally.** Vary prices independently of decision value to separate \(\lambda_c\) from misestimated value. Vary cue strength independently of prior prominence to separate \(\delta\) from \(\gamma\). Only the ratio of a free cost and a free utility scale is identifiable, so fix one.
4. **Recovery before collection.** For each module and for the joint hierarchical fit:
   - parameter recovery, including boundaries and nearby values;
   - model recovery against competing families;
   - posterior-predictive adequacy.
   
   These use the existing synthetic machinery ([Wilson & Collins 2019](https://elifesciences.org/articles/49547)).
5. **Reliability as part of the measurement.** Report test–retest across fresh contexts alongside recovery. Estimate parameters jointly and hierarchically across modules and sessions, where that improves reliability ([Mkrtchian et al. 2023](https://cpsyjournal.org/articles/10.5334/cpsy.86)).
6. **Behavior, not self-report.** Questionnaire-style LLM traits are dominated by response bias ([Meyer et al. 2026](https://arxiv.org/abs/2606.20205)). Parameters come from choices and probability reports under paraphrase and format variation, never from stated self-descriptions.

## 5. Identification battery (formal layer)

Short modules in the style of classic paradigms, delivered through the compact interface (one call per checkpoint). Each module is usable by humans, with fictional content and structural novelty to limit contamination.

| Module | Design | Primary parameters | Human reference |
| --- | --- | --- | --- |
| T1 Unvetted testimony | New sources report on binary states with no stated reliability; outcomes reveal their record over trials; probability reports each trial | \(\mu_r\), \(\kappa_r\) | Advice-taking; Bayesian testimony |
| T2 Ambiguous corroboration | Pairs of matching reports whose provenance cues are graded from clearly independent to clearly relayed | \(\delta\), with \(\gamma\) from the clear ends | Correlation neglect ([Enke & Zimmermann 2019](https://academic.oup.com/restud/article/86/1/313/4772809)); downloaded data |
| T3 Silence | A sender of unstated type reveals or withholds binary items; estimate the hidden state; optional feedback | \(\sigma\) (and learning of \(\sigma\) with feedback) | Disclosure games ([Jin, Luca & Martin 2021](https://www.aeaweb.org/articles?id=10.1257/mic.20180217); [Farina et al. 2026](https://doi.org/10.5281/zenodo.18825108)); argument from ignorance |
| T4 Volatile reliability | Adviser accuracy switches across stable and volatile blocks; trial-wise reports and choices; HGF fit | \(\omega_2\), \(\vartheta\) (against a hazard model) | [Behrens et al. 2008](https://www.nature.com/articles/nature07538); [Diaconescu et al. 2014](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003810) |
| T5 Value of certainty | Sequential sampling with per-draw prices, checks with zero decision value, and an abstain/defer option | \(\lambda_c\) | Beads task with costs; paying for confidence |
| T6 Signal strength | Bookbag trials sweeping weak to strong diagnosticity | \(\gamma\), \(\beta\) | [Augenblick, Lazarus & Thaler 2025](https://arxiv.org/abs/2109.09871) and the [Benjamin 2019](https://www.nber.org/papers/w25200) pooled data (public, not yet downloaded) |

Each module aims for 12–24 checkpoints. At the 0.3–0.4 million input tokens measured per nine-case dossier context, the whole battery should cost about one to two million tokens per respondent context.

## 6. Transfer layer (naturalistic)

The existing research-world dossiers become the out-of-sample test, **with the background facts removed**, so the same ambiguities recur in realistic form:

| Dossier feature | Predicted by |
| --- | --- |
| Unattributed or rounded relays with ambiguous provenance | \(\delta\) (T2) |
| KPIs dropped from a letter with no stated practice | \(\sigma\) (T3) |
| Coverage from outlets with no track record | \(\mu_r\) (T1) |
| Survey purchases, including zero-decision-value checks | \(\lambda_c\) (T5) |
| Trust after a source is caught fabricating, across a dossier sequence | \(\omega_2\) (T4) |
| Fabricated figures of each type | \(d_t\) |

The transfer criterion is held-out predictive gain of the formal-layer parameters over two baselines:
- **pooled parameters** (a shared "typical respondent");
- **the normative observer** with neutral assumptions.

It is measured by log score on reports and by regret on the buyer's verification decision. This is the passport's claim structure: parameters estimated in controlled tasks predict behavior in realistic material and change a decision. Without the background facts there is no single correct answer, so scoring moves from error rates to parameter estimation and prediction.

## 7. Relation to what exists

- **Reused as built:**
  - the compact interface, transactional collection, locks and runners;
  - the synthetic validation and recovery pattern;
  - the research-world generator and extraction audit;
  - the priced-check analysis.
- **Earlier results reinterpreted:**
  - **Source learning (0.1):** the joint source-process observer is a special case of T1 with stated structure.
  - **Precision:** the source-panel precision result is \(\tau\).
  - **Neglect weights:** the neglect weights of the dossier acceptances measure fidelity under fully stated structure. They are zero for capable configurations and nonzero for weaker ones, and remain valid measurements of that class.
- **New:**
  - the HGF implementation (binary three-level, with the change-point competitor);
  - modules T1–T6;
  - de-scaffolded dossier variants;
  - a hierarchical joint fit across modules.

## 8. Development sequence

1. **Specify and simulate.** Write the joint likelihood. For each module, show parameter and model recovery on synthetic respondents across the plausible range, including the ideal observer and boundary cases. No respondent collection.
2. **First modules: T2, T3, T5.** They map directly onto the dossier families already built (dependence, disclosure, verification) and give the fastest transfer test.
3. **T4, the HGF module.** Next, with the change-point model as competitor. It needs longer sequences and is the most expensive to validate.
4. **Agent acceptance and test–retest.** Astra and Sol at medium and low effort, Luna and Terra, with repeated fresh contexts for reliability.
5. **Transfer.** De-scaffolded dossiers, with predictions frozen before collection.
6. **Human arm.** When fresh human collection resumes, run the same modules. Use the downloaded replication data now for T2 and T3 references. T6 needs the 262 MB Augenblick–Lazarus–Thaler package, not yet downloaded.

## 9. Risks

- **Priors confounded with misread likelihoods.** Mitigation: clear-structure controls within every module to anchor \(\gamma\) and \(\tau\); elicited expectations; model comparison against misreading accounts.
- **Assumptions tied to format rather than to the respondent.** If an agent's \(\delta\) or \(\sigma\) shifts with wording, it is not a disposition. Paraphrase and format variation are part of the reliability check.
- **Refusal to assume.** Agents may ask for the missing fact or decline to commit. The protocol requires a probability, and the explanation of that requirement is itself a controlled condition.
- **Small dispositional differences among capable configurations.** Near-identical training may yield near-identical assumptions. That is a result, not a failure; it would still separate them from weaker configurations and from humans.
- **Many parameters.** Nothing is fitted jointly from one module. Each module identifies its own subset, and the hierarchical joint model is tested for recovery before use.

## 10. Decisions needed

1. **HGF depth.** Is the binary three-level HGF with \(\kappa\) fixed and \(\omega_2\), \(\vartheta\) free acceptable, with a change-point observer as competitor, or do you want \(\kappa\) estimated?
2. **Certainty function.** The proposal uses \(|2p-1|\), which is linear and interpretable. Negative entropy is smoother and has a stronger theoretical pedigree. Or should both be fitted and compared?
3. **Elicited expectations.** Are behavioral commitments before evidence (for example "probability the next figure repeats an earlier one") acceptable as model inputs, or should parameters come only from forecasts and choices?
4. **First modules.** T2, T3 and T5 first, as proposed, or T4 first given its centrality?
