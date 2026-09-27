# Where capable agents deviate: task design and modeling review

Literature review and reflection, 27 September 2026, following the [cost-aware verification results](cost-aware-results-2026-09-26.md). It extends the [20 September cognitive-modeling review](cognitive-modeling-review-2026-09-20.md), whose material (Gershman, Ullman, hypothesis sampling, adaptive Bayesian learning, epistemic trust, resource rationality, Hedge et al., Wilson & Collins, adaptive design optimization) is not repeated. This document changes no battery, evaluator, report contract or issued evidence. Section 6 records the direction decided on 27 September after review of this synthesis; Section 7 lists what remains open.

**Method and status.** Five parallel searches covered LLM belief updating and calibration; information acquisition and verification; belief-updating models and parameter reliability in psychology, computational psychiatry and behavioral economics; AI measurement science and agent consistency; and source credibility, dependent evidence and naturalistic evaluation. BayesBench was read in full. Each cited work was checked against an arXiv, publisher, proceedings or index page. Tags give the depth of reading: **[F]** full text or the main design/results sections; **[S]** full text read through an automated summarizer, so numbers need rechecking before reuse; **[A]** abstract or metadata only. An automated summary of the BayesBench PDF invented its tasks and models and was discarded, and a summarizer also fabricated content for one economics paper; numbers below come from extracted text or are tagged. Most 2026 items are unreviewed preprints. Much LLM evidence concerns open-weight or earlier models: it indicates where to look, not how our configurations behave. This is not a systematic review.

## Summary

1. **Our results are what this literature predicts for the regime we measured.** Frontier models look Bayesian when the hypothesis space, priors and evidence format are supplied and a report follows each item. Individually fitted profiles rarely beat pooled predictions among configurations of similar capability. The completed collections sat in both regimes.
2. **The consequential deviations arise when the agent must construct the problem, not compute within it:** inferring likelihoods from prose, learning source reliability through prestige cues, noticing copied or selected evidence, noticing what is missing, generating a check rather than choosing one, staying invariant to framing and social engagement, and carrying beliefs into actions.
3. **The verification comparisons could not show much.** Free information never lowers an expected proper score, so an always-check Brier gain is guaranteed rather than diagnostic. Checks have decision value only where they can flip the optimal action, and our cases mostly did not sit near that margin.
4. **Precision is the most promising configuration-level property.** Noise parameters are the most reliable and transferable computational parameters in the human literature, and run-to-run consistency varies between AI systems independently of accuracy. Its transfer and decision value have not been validated for any agent.
5. **Information-equivalent contrasts are the cleanest measurement design.** Presenting identical information in two structures isolates a bias without a reference posterior and without treating reports as internal beliefs.
6. **Prior-free trajectory tests** (excess movement, martingale, invariance/sufficiency regressions, commutativity) extend analysis to naturalistic tasks lacking an exact reference.
7. **Handing profiles to an LLM orchestrator does not by itself improve delegation.** A passport should parameterize an explicit decision rule evaluated by regret.
8. **Several contrasts appear untested in LLMs:** selection neglect, disclosure skepticism, information-equivalent correlation neglect with textual provenance, signal-strength nonlinearity, willingness-to-pay for information against decision value, and horizon-dependent verification of recurring sources.

## 1. Why our results look the way they do

### 1.1 We measured computation within a supplied representation

Our source tasks disclosed business rates, gave each source a tabulated archive of reports and resolved outcomes, named the candidate source processes (measurement error, selective panels), offered definitive audits for them, and elicited a probability after each new item. The respondent estimated parameters inside a hypothesis space we provided.

That is the regime in which recent studies find capable models close to Bayes:

- [Chen et al. (2026)](https://arxiv.org/abs/2605.06915) [S] elicit priors, likelihoods and posteriors. With supplied components and stepwise updating, GPT-5.1 is described as near-optimal; with all evidence at once, the same model is frequently far from optimal.
- [Cekinmez, Wu & Griffiths (2026)](https://arxiv.org/abs/2608.12387) [S] find step-by-step elicitation suppresses the strong order effects that end-of-sequence elicitation produces in GPT-4o and Claude models; the effect is larger in newer models and opposite to the human pattern.
- [Krishnamurthy et al. (2024)](https://arxiv.org/abs/2403.15371) [F] obtained satisfactory bandit exploration only with externally summarized per-arm statistics plus chain of thought.
- [Gupta et al. (2025)](https://aclanthology.org/2025.acl-long.377/) [S] and [Zhang, Yang & Wang (2025)](https://arxiv.org/abs/2512.18489) [S] attribute most residual error to miscalibrated priors or misspecification rather than the update step, although fitted discounting (γ < 1) is systematic in open models.
- In humans, [Enke & Zimmermann (2019)](https://academic.oup.com/restud/article/86/1/313/4772809) [F] find correlation neglect disappears with two signals or a side-by-side contrast: the failure is noticing the structure, not computing with it.

Our own exceptions fit this reading. Variation appeared where the respondent had to construct something: starting distributions under identical wording differed by 4.375 TV points ([narrative repeat](narrative-repeat-2026-09-24.md)), and initialization remained the unresolved modeling question in [investigation 0.3](investigation3-results-2026-09-23.md). The near-ideal-observer agreement is a genuine result about computation. It says little about whether these configurations would notice the same structure unprompted.

### 1.2 Pooling wins among configurations of similar capability

- [Zhou et al. (2026), ADeLe](https://doi.org/10.1038/s41586-026-10303-2) [S] predict instance-level success from rated instance demands (held-out-benchmark AUROC about 0.75). Predictive power lies mainly in the instances.
- [Pacchiardi, Cheke & Hernández-Orallo (2024)](https://arxiv.org/abs/2409.03563) [A]: a generic assessor given about 100 reference items from a new model matches model-specific assessors in distribution.
- [Ge et al. (2026)](https://arxiv.org/abs/2604.00594) [S]: agent-specific ability adds roughly 0.09 AUROC over pooled task difficulty, across agents of widely varying ability.
- Capability structure is low-dimensional ([Burnell et al. 2023](https://arxiv.org/abs/2306.10062) [F]; [Ruan, Maddison & Hashimoto 2024](https://arxiv.org/abs/2405.10938) [F, partial]). Skill-conditional reputation helps only under high heterogeneity ([Xia & Wang 2026](https://arxiv.org/abs/2606.14200) [A]).
- Questionnaire-style LLM profiles are dominated by response bias: 81–90% of between-model variation in [Meyer, Garcia & Wulff (2026)](https://arxiv.org/abs/2606.20205) [A].

Two medium-effort frontier configurations should therefore show little between-configuration variation in evidence-weight parameters. The [prediction benchmark](prediction-results-2026-09-20.md), [source panel](source-panel-results-2026-09-26.md) and source-learning nulls are expected. For the product, shared expectations should be the default. A configuration-specific claim has to earn its place by improving prediction or a decision.

### 1.3 Precision is the parameter that tends to be reliable

In humans, exploration and noise parameters generalized across tasks where learning rates did not ([Eckstein et al. 2022](https://elifesciences.org/articles/75474) [A]). Decision noise was the most reliable parameter in an HGF advice-taking retest ([Karvelis et al. 2024](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0312255) [S]). Joint hierarchical fitting raised inverse-temperature retest ICCs to 0.80–0.91, while lapse parameters had near-zero reliability ([Mkrtchian, Valton & Roiser 2023](https://cpsyjournal.org/articles/10.5334/cpsy.86) [S]). A group difference that looked like a sampling-cost difference in the beads task was better explained by decision noise ([Moutoussis et al. 2011](https://www.tandfonline.com/doi/abs/10.1080/13546805.2010.548678) [A]).

For AI systems, [Rabanser et al. (2026)](https://arxiv.org/abs/2602.16666) [F/S] find outcome consistency varies across 15 models and is only weakly coupled to accuracy. [Zhai et al. (2026)](https://arxiv.org/abs/2602.23271) [S] locate most deep-research run-to-run variance in the inference stage. [Smolin & Wilder (2026)](https://arxiv.org/abs/2609.07943) [F] find an intraclass correlation of about 0.5 across continuations of a shared reasoning prefix: about half the within-case variance in elicited probabilities depends on the reasoning path taken.

The panel's reproducibility difference (sparse repeats differing by 2.83–2.87 versus 10.78–10.82 points RMS) is the kind of parameter this literature expects to be trait-like. It has not been shown to transfer across task families, and it has not been split into decision-relevant belief variance and reporting variance.

### 1.4 Verification value was small by construction

- Under a proper scoring rule, free information cannot lower expected score (Blackwell's comparison of experiments; cited here as a standard result, not re-read). Always-check Brier gains in [Stage A](verification-stage-a-results-2026-09-26.md) were therefore expected. In the [cost-aware run](cost-aware-results-2026-09-26.md), always-check Brier improved in world A and worsened in world B, consistent with realized sample variation.
- A check has decision value only if some result would change the optimal action. The cost-aware rule was expected-value-optimal under the respondent's own report, so its losses on two worlds mix sample luck with starting-report miscalibration.
- The [1,024-world decision-value audit](decision-value-audit-results-2026-09-27.md), completed separately on the same day, confirms this. Selective checking has positive expected value for oracle and public-information reporters, yet loses on about 27% of two-world samples. About 67% of cases have no positive public net value of sample information, while the 28% with at least 0.01 carry most of the benefit. The archived agents' starting reports differed from the public-information observer by about 9–10 points RMS. That is consistent with the LLM finding that residual error lies mainly in starting judgments rather than updates.
- Our check was a menu item. Generating a useful question is harder than recognizing one: [Rothe, Lake & Gureckis (2018)](https://link.springer.com/article/10.1007/s42113-018-0005-5) [A]; [QuestBench (Li, Kim & Wang 2025)](https://arxiv.org/abs/2503.22674) [A]; [Grand et al. (2026)](https://arxiv.org/abs/2510.20886) [S].
- Verification pays when errors are rare, structured and flagged by a cheap signal. [AI Control (Greenblatt et al. 2024)](https://arxiv.org/abs/2312.06942) [S] and costly-state-verification contracts ([Townsend 1979](https://ideas.repec.org/a/eee/jetheo/v21y1979i2p265-293.html) [A]) both verify selectively on the report itself. Our worlds had neither strategic misreporting nor report-triggered risk.

## 2. Where capable agents deviate

| Family | What the agent must construct | LLM evidence | Human paradigm and benchmark | Apparent gap |
| --- | --- | --- | --- | --- |
| Likelihoods from prose | How strongly each item bears on the hypothesis | Chen et al. 2026 batch mode [S]; [Pal et al. 2025](https://arxiv.org/abs/2511.13240): direct posteriors diverge from Bayes on own components [S]; [BASIL](https://arxiv.org/abs/2508.16846) [S] | Grether regressions; [Benjamin 2019](https://www.nber.org/papers/w25200) [F] | Frontier coverage thin |
| Reliability from experience | Source reliability from outcomes, not labels | [Ashkinaze et al. 2026](https://arxiv.org/abs/2607.19355) [S]: source discernment ρ ≈ 0.03; popularity weighted ~2× reliability; scale improved truth but not source discernment | Bovens–Hartmann reliability; [Madsen, Hahn & Pilditch 2020](https://doi.org/10.1037/xlm0000846) [A]; [Harris et al. 2016](https://doi.org/10.1111/cogs.12276) competence/intent [A] | Outcome-learned reliability with prestige decoupled |
| Dependence and copying | Whether corroboration is independent | [Schuster, Gautam & Markert 2026](https://arxiv.org/abs/2601.03746) [S]: same-source repetition shifts preference ~30 points; [Xie et al. 2024](https://arxiv.org/abs/2305.13300) [F]: absolute evidence count matters | [Enke & Zimmermann 2019](https://academic.oup.com/restud/article/86/1/313/4772809) [F]; [Pilditch et al. 2020](https://doi.org/10.1016/j.cognition.2020.104343) [A]; [Mercier & Miton 2019](https://www.sciencedirect.com/science/article/abs/pii/S1090513818303581) [A] | Information-equivalent test with textual provenance cues |
| Selection and absence | What was withheld and why | [AbsenceBench (Fu et al. 2025)](https://arxiv.org/abs/2506.11440) [A]; [CROWN-QA (Min et al. 2026)](https://arxiv.org/abs/2608.04591) [A] | [Enke 2020](https://academic.oup.com/qje/article-abstract/135/3/1363/5821301) [F]; [Jin, Luca & Martin 2021](https://www.aeaweb.org/articles?id=10.1257/mic.20180217) [F] | No LLM selection-neglect or disclosure test found |
| Register versus validity | Whether numbers are credible | [Pradhan & Goley 2026](https://arxiv.org/abs/2606.05403) [S]: fabricated statistics retain ~74% of valid pull in synthesis; [Wan, Wallace & Klein 2024](https://aclanthology.org/2024.acl-long.403/) [A] | [Fréchette, Lizzeri & Perego 2022](https://doi.org/10.3982/ECTA18585) label effects [F] | Link to a verification decision |
| Framing and engagement | Which latent generated the style | [BayesBench (Samanta et al. 2026)](https://arxiv.org/abs/2606.30850) [F]; BASIL; [Geng et al. 2025](https://arxiv.org/abs/2511.01805) [S] | [Hahn & Oaksford 2007](https://doi.org/10.1037/0033-295X.114.3.704) [A] | Research-agent setting |
| Order and batch integration | Commutative accumulation | Cekinmez et al. 2026 [S]; [Chlon et al. 2025](https://arxiv.org/abs/2507.11768) [S] | Order-effect literature | Frontier agents under batch dossiers |
| Belief to action | Actions consistent with stated probabilities | Pal et al. [S]: betting consistency ≤ 79%, calibration negatively related to betting consistency; Geng et al.: stated and behavioral shifts diverge | [Fan, Liang & Peng 2026](https://www.econometricsociety.org/publications/econometrica/2026/07/01/The-Inference-Forecast-Gap-in-Belief-Updating) inference–forecast gap [A] | Belief-to-purchase coherence |
| Search and stopping | What to ask, when to stop | Grand et al. [S]; [BATS](https://arxiv.org/abs/2511.17006), [CostBench](https://arxiv.org/abs/2511.02734), [EcoAgent-Bench](https://arxiv.org/abs/2608.05519) [A]; [AbstentionBench](https://arxiv.org/abs/2506.09038) [A] | [Juni, Gureckis & Maloney 2016](https://people.psych.ucsb.edu/juni/mordechai/papers/JuniGureckisMaloney-Decision-InPress.pdf) [F, partial]; [Wilson et al. 2014](https://collaborate.princeton.edu/en/publications/humans-use-directed-and-random-exploration-to-solve-the-explore-e) [A] | Horizon-dependent verification |
| Signal strength | Weight as a function of diagnosticity | Untested | [Augenblick, Lazarus & Thaler 2025](https://arxiv.org/abs/2109.09871) [F] | Weak-signal overinference in agents |

The common thread is **noticing and constructing structure**. It matches Enke and Zimmermann's distinction between noticing and computing, Rothe et al.'s generation-versus-evaluation gap, and BayesBench's finding that larger models infer a latent better without reliably using it in prediction. It also restates the [20 September review](cognitive-modeling-review-2026-09-20.md)'s point that interpretation, not evidence weighting, is the passport's object.

Coverage of GPT-5-class or later models is partial: Chen (GPT-5.1), Ashkinaze (GPT-5), Pradhan & Goley (GPT-5.4, Claude Opus 4.5), Geng (GPT-5) and Smolin & Wilder include frontier systems; Schuster, Zhang, Gupta and BayesBench do not. Whether our configurations show any of these deviations requires our own bounded check.

## 3. Task-design principles

**3.1 Generate a latent world, then render the evidence.** The world should include the fact ledger, a provenance graph (who observed, copied, summarized or averaged whom), each sender's incentive and disclosure rule, and each document's normative likelihood ratio. Render it into realistic documents, as [MuSR](https://arxiv.org/abs/2310.16049) [A] and [DRBench](https://arxiv.org/abs/2510.00172) [S] do. Make dependence and selection recoverable only from textual cues (wire attribution, shared quotation, same dataset, timestamps), never from instructions. The current packet bridge is a first step in this direction.

**3.2 Use information-equivalent pairs as the backbone.**
- Examples: correlated versus independent relay (Enke & Zimmermann); selected versus fully shown evidence (Enke 2020); one record versus split records (Schuster et al.; [Liu, Zhou & Wang 2026](https://arxiv.org/abs/2609.08698) [S]); a framing latent the target should not depend on (BayesBench); posterior-equivalent messages with different labels (Fréchette et al.); sequential versus batch and order permutations (Chen et al.; Cekinmez et al.).
- The within-pair difference estimates the distortion without a reference posterior and without reading reports as internal beliefs. Decisions and point estimates can be scored directly.
- Equivalence of the pair must be audited, as our bridge specification already requires.

**3.3 Separate noticing from computing.** Run an unprompted arm, a hinted arm and an explicit-structure arm. Our completed tasks are the explicit arm. A research buyer cares most about the unprompted arm; the gap between arms is itself a portable fact.

**3.4 Scale the structure, not the arithmetic.** In humans, neglect grows with the number of relays, signals and documents while the normative computation stays fixed (Enke & Zimmermann; Enke 2020; [Ba, Bohren & Imas 2025](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4274617) [A, introduction read]). If near-Bayesian agents break, this is the likely place.

**3.5 Place items where decisions and differences can appear.**
- Concentrate cases near action indifference, where pooled and individual accounts can disagree.
- Cross the expected value of a check with its price. Estimate P(buy) against (EVOI − price): the slope is value sensitivity, the intercept is over- or under-purchase ([Ambuehl & Li 2018](https://econpapers.repec.org/RePEc:eee:gamebe:v:109:y:2018:i:c:p:21-39) [A] report stable individual responsiveness to informativeness).
- Include checks that cannot change the decision ([Bastardi & Shafir 1998](https://pubmed.ncbi.nlm.nih.gov/9686449) [A]; [Eliaz & Schotter 2010](https://ideas.repec.org/a/eee/gamebe/v70y2010i2p304-324.html) [A]).
- Dissociate information gain from decision value ([Meder & Nelson 2012](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/information-search-with-situationspecific-reward-functions/658C3FC2CF6A7C5B031D417DCC2315B3) [F, auto-extracted]; [Nelson 2005](https://pubmed.ncbi.nlm.nih.gov/16262476/) [A]). An agent can look excellent on EIG, which most LLM information-gathering benchmarks optimize, while being poor on decision value.
- Sweep signal strength down to weak signals (Augenblick, Lazarus & Thaler), where humans over-infer and over-buy.

**3.6 Make verification valuable by construction.** Use rare strategic misreports in high-stakes states, corroboration with a shared upstream origin, and bias by commission versus omission ([Charness, Oprea & Yuksel 2021](https://academic.oup.com/jeea/article/19/3/1656/6122590) [A, introduction]). Add a horizon manipulation: the same check on a one-off claim versus a recurring source, where it also buys future reliability information. Replace the fixed five-customer sample with optional sequential sampling at a per-sample price.

**3.7 Ask the agent to propose the check** as well as choose from a menu, and score the proposal's information and decision value.

**3.8 Elicit actions and several formats.** Include payoff-equivalent framings (threshold, costs, bet; Smolin & Wilder) and interval elicitation. [Hobor et al. (2026)](https://arxiv.org/abs/2604.01896) [A] report 95% intervals covering the truth only 9–44% of the time, where point probabilities looked calibrated.

**3.9 Replicate identical cases and use replay.** Keep a stateless arm (fresh context each step, full evidence) and a stateful arm (the agent sees its own previous reports). Reporting noise becomes belief only in the stateful arm.

**3.10 Keep counter-evidence coherent and graded.** Incoherent substitutions measure incoherence detection, not source weighting (Xie et al.). Graded perturbation gives dose–response curves ([ClashEval (Wu, Wu & Zou 2024)](https://arxiv.org/abs/2404.10198) [A]).

## 4. Modeling and analysis principles

### 4.1 Prior-free and prior-robust trajectory tests

- **Excess movement** ([Augenblick & Rabin 2021](https://academic.oup.com/qje/article-abstract/136/2/933/6127317) [F, author version]).
  - For a Bayesian under any data-generating process, expected squared belief movement equals expected uncertainty reduction. X_norm = movement / reduction, with a CLT test.
  - It needs enough total movement (their rule of thumb is at least 3 across the dataset) and cannot see moves starting at 0.5.
  - Additive reporting noise inflates expected excess movement by 2σ². Replicate runs let us estimate and subtract that term, which human studies cannot do.
  - In the Good Judgment Project, individual excess movement persisted across halves of the year (r = 0.23, higher for active forecasters).
- **Martingale slope** ([He et al. 2025](https://arxiv.org/abs/2512.02914) [S]): regress the update on the current belief. A noisy current belief biases the slope negative through regression to the mean, so instrument it with an independent replicate's report.
- **Invariance, sufficiency and stability regressions** ([Möbius et al. 2022](https://pubsonline.informs.org/doi/abs/10.1287/mnsc.2021.4294) [F, 2014 working paper]). The evaluator's reference posterior or the random evidence sequence can instrument the reported prior.
- **Commutativity and batch invariance**: the same evidence multiset in different orders, or sequentially versus at once, should give the same posterior under any prior. Score permutation-averaged predictions separately from order variance (Chlon et al.).
- **Directional sign tests**: manipulate cue reliability and check that weights move the Bayes-predicted way ([Ma, Wang & Fountas 2025](https://arxiv.org/abs/2512.02719) [S], also titled BayesBench).
- **Coherence with the respondent's own components** (Pal et al.; BASIL; Chen et al.). Coherence is not accuracy: Chen et al. report that non-Bayesian batch posteriors often outperform exact Bayes applied to the model's own elicited likelihoods, and [Murphy (2026)](https://arxiv.org/abs/2604.18576) [S] found explicit Bayes over LLM-estimated likelihoods much worse for forecasting. Score against generator truth wherever it exists.
- **Arbitrage checks** across logically related questions ([Paleka et al. 2025](https://arxiv.org/abs/2412.18544) [S]). Some checks track Brier; training on the targeted checks did not improve held-out checks or accuracy.

### 4.2 Contrast parameters with explicit structure

- **Correlation neglect:** Enke & Zimmermann estimate an individual naivety weight χ. Its distribution is bimodal (about Bayesian or fully naive), so a two-type mixture can fit better than a continuous parameter.
- **Selection neglect:** Enke (2020) models reports as a mixture of the Bayesian and naive posteriors. χ rises with complexity and is explicitly environment-dependent.
- **Signal-strength compression:** perceived strength Ŝ = k·S^β (Augenblick, Lazarus & Thaler: β ≈ 0.76, crossing from over- to underinference near p ≈ 0.64). A constant reporting gain cannot represent this.
- **Disclosure:** Jin, Luca & Martin set-identify the naive share of receivers.
- **Normative models:** dependence requires the full network over structure and observations. Pilditch et al. show dependent reports can be more informative than independent ones, so "discount duplicates" is not a valid score. Competence and intent need separate nodes (Harris et al. 2016; [Young & de-Wit 2025](https://doi.org/10.1111/cogs.70141) [A] add an agenda-bias node).

### 4.3 Separate belief from report

- Smolin & Wilder fit one latent per case with format-specific links and Beta-distributed probability reports. For capable models, one latent predicted all sixteen elicited outputs across framings and domains. The HGF's separation of perceptual and response models ([Mathys et al. 2014](https://www.frontiersin.org/articles/10.3389/fnhum.2014.00825/full) [S]) is the same principle as our reporting layer.
- Decompose variance into case, configuration, context (reasoning path) and report. Replay from a shared prefix versus fresh contexts separates reasoning-path variance from context sampling. The latent remains a measurement construct, not access to internal belief.

### 4.4 Treat precision as first-class

- Compare "shared bias, configuration-specific σ" against "configuration-specific bias" by held-out log score.
- Represent state-dependent noise: larger after bad news in humans ([Eil & Rao 2011](https://www.aeaweb.org/articles?id=10.1257/mic.3.2.114) [A]), or coupled to estimated volatility ([Diaconescu et al. 2014](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003810) [S]).
- Model non-updates as a separate component ([Coutts 2019](https://link.springer.com/article/10.1007/s10683-018-9572-5) [A]). Avoid lapse parameters.

### 4.5 Report reliability as part of the measurement

- Fit sessions jointly and hierarchically, and report parameter recovery beside test–retest (Mkrtchian et al.; [Waltmann et al. 2022](https://link.springer.com/article/10.3758/s13428-021-01739-7) [A]). Retest well below recovery indicates state variation; for agents, the likely sources are seed, paraphrase and snapshot ([Schurr et al. 2024](https://www.nature.com/articles/s41562-024-01814-x) [A]).
- Test cross-task generalization of σ as Eckstein et al. did for humans.
- Avoid difference scores; estimate contrasts inside one model ([Zorowitz & Niv 2023](https://www.biologicalpsychiatrycnni.org/article/S2451-9022(23)00042-3/abstract) [F]).

### 4.6 Score decisions ex ante

- Replace realized outcomes with their expectation under the generator's true parameters. Use common random numbers across policies and many independent worlds, and report realized payoff as secondary. Outcome bias is a known evaluator failure ([Baron & Hershey 1988](https://pubmed.ncbi.nlm.nih.gov/3367280/) [A]).
- Compute a check's value from the respondent's report and from the reference observer, to separate belief error from purchase-policy error.
- For a fresh-context report with mean μ and standard deviation σ, E[(p − y)²] = (μ − y)² + σ². Averaging k independent runs divides the second term by k. That prices "resample and average" against "verify" and "accept" as explicit alternatives (see [Jiang et al. 2022](https://arxiv.org/abs/2106.13799) [A] and [Liu 2026](https://arxiv.org/abs/2605.03379) [A] for second-moment/ensemble links).

### 4.7 Model discovery comes after a noise ceiling

LLM-assisted discovery has succeeded with large datasets: [Peterson et al. 2021](https://www.science.org/doi/10.1126/science.abe2629) [A]; [Centaur (Binz et al. 2025)](https://www.nature.com/articles/s41586-025-09215-4) [A]; [GeCCo (Rmus et al. 2025)](https://arxiv.org/abs/2502.00879) [A]; [CogFunSearch (Castro et al. 2025)](https://proceedings.mlr.press/v267/castro25a.html) [A]; closed-loop systems such as [AutoCog (Jagadish et al. 2026)](https://arxiv.org/abs/2606.26448) [A]. Critiques caution that such systems can exploit shortcuts or absorb state fluctuations ([Orr et al. 2025](https://arxiv.org/abs/2510.03311) [A]).

Sequence:
1. Estimate a noise ceiling from replicated cases.
2. Fit a small flexible benchmark against ideal observer plus noise.
3. Search for new models only if a gap remains, on held-out cases with a frozen evaluator.

Given our near-Bayesian fits, headroom on the current tasks is probably small; representation-construction tasks may change that.

## 5. Implications for the passport

**Decision rules, not cards.**
- In [DecisionBench (Gao et al. 2026)](https://arxiv.org/abs/2605.19099) [S], giving orchestrators peer profile cards left end-task quality statistically unchanged, and preloaded cards often reduced routing fidelity.
- Recalibrating risk scores improved prediction without reducing control regret ([Zhang et al. 2026](https://arxiv.org/abs/2606.21399) [A]).
- In human–AI reliance, information helped only in combination ([Spitzer et al. 2025](https://doi.org/10.1145/3710999) [S]), and explanations raised reliance regardless of correctness ([Bansal et al. 2021](https://arxiv.org/abs/2006.14779) [A]).
- The [machine consumer](machine-consumer.md)'s explicit task policy over stable metric IDs is the right shape. Its value must be measured as regret against simple policies.

**A passport as the consumer's likelihood model.**
- [Papamarkou et al. (2026)](https://arxiv.org/abs/2605.00742) [S] argue for placing Bayesian decision theory in the orchestrator. Agent outputs become noisy observations with learned likelihoods, pooled with dependence awareness, and escalation is decided by information value. This is a position paper without empirical results.
- A passport could supply the evaluated prior for that likelihood: how to read this configuration's reports under stated conditions, through calibration, precision and identified blind spots. That fits our rule that reports are observations rather than internal beliefs, and it gives each claim a direct "useful action".

**Consistency and resample pricing.** A precision field per task family, with uncertainty, lets a consumer choose between resampling, verifying and accepting. It adds nothing about bias, so it must sit beside calibration evidence. Existing proposals ([τ-bench pass^k](https://arxiv.org/abs/2406.12045); Rabanser et al.'s promotion thresholds) are descriptive; no study found here validates configuration-level consistency as transferable or decision-improving.

**Naming.** Workday announced an "Agent Passport" of signed security-test attestations on 2 June 2026, and an IETF individual draft proposes an "Agent Trust and Execution Passport" with success-rate track records. Neither carries calibrated epistemic or consistency fields. External positioning should distinguish them.

## 6. Direction decided on 27 September

| Decision | Outcome |
| --- | --- |
| Passport core | A **reading guide** for consumers: how to read this configuration's outputs under stated conditions (calibration, precision and identified blind spots), each with the conditions under which it holds and a recommended consumer action. Cognitive models are an explanatory layer, retained only where they improve prediction. |
| Task realism | **Naturalistic tasks are the goal.** A latent research world is rendered as realistic documents, with dependence and selection recoverable only from textual cues. Current explicit tasks remain as the control arm. |
| First families | **Selective disclosure** and **shared-origin corroboration**, each with unprompted, hinted and explicit arms, coupled to the verification decision. |
| Human comparison | Use published human benchmarks and public replication data where available (for example Enke & Zimmermann; Enke 2020; Jin, Luca & Martin; Fréchette et al.). **No fresh human collection for at least several weeks.** Human usability acceptance remains a separate item. |
| Output | **Product, not publication.** Findings, including the pooled-versus-individual null, become product defaults and scoped claims. |

The workstreams below implement those decisions.

**0. Reanalyze existing collections before new runs.** The [decision-value audit](decision-value-audit-results-2026-09-27.md) already supplies ex ante scoring, purchase-versus-action regret and starting-calibration diagnostics. Remaining items:
- excess movement and martingale slopes with replicate instruments;
- decomposition of σ using existing repeats;
- signal-strength-dependent weights.

These use only data already held privately and need no account-backed collection. Results are exploratory development evidence on previously analyzed data.

**A. Representation battery.** Build information-equivalent pairs rendered from a latent research world, with unprompted, hinted and explicit arms. Candidate first families are selective disclosure and shared-origin corroboration: both are directly relevant to research buyers, have human economic benchmarks with estimable parameters, and appear untested in LLMs.

**B. Precision as a core passport measurement.** Use a measurement model separating reasoning-path, context and report variance. Test transfer across task families and evaluate resample, verify and accept as costed decisions.

**C. Verification economics redesigned.** Place items near indifference and cross check value with price to get a P(buy) curve. Include zero-value and information-rich-but-useless checks, a recurring-source horizon, strategic sources, sequential sampling and agent-proposed checks. Score by ex ante regret over many independent worlds.

**Coupling A with C** is the most promising product idea found in this review. Verification is most valuable exactly when a dossier contains structure an agent fails to notice. An illustrative, **unmeasured** claim would read:

> Under unprompted conditions this configuration treats shared-origin corroboration as independent; require verification when a conclusion rests on reports sharing an upstream source.

That claim has a buyer action, a generic alternative ("always deduplicate provenance") and a profile-dependent alternative. Humans show bimodal naivety in these paradigms. If configurations likewise split between noticing and not noticing, configuration-specific profiles could beat pooling here, which the evidence-weight profiles never did. That is a testable prediction, not a finding.

Sequence:
1. Direction 0.
2. A small pilot of one disclosure pair and one dependence pair across two configurations, with more independent worlds and fewer repeats, to establish whether our configurations show either deviation unprompted.
3. If they do, couple with a redesigned verification decision.
4. Carry direction B's measurement model throughout.

If the pilot finds no deviation, report that scope and move to the next family (register versus validity, or reliability learned through prestige cues) rather than scaling.

## 7. Still open

1. **Automated model discovery.** Worth a bounded attempt only after a noise ceiling shows headroom.
2. **Buyer loss weights.** The coupled verification comparison needs declared costs for false acceptance, missed opportunities and verification before its gate is frozen.
3. **Configurations.** Whether the pilot keeps the two existing configurations or adds one that differs more in tools, effort or model, which would raise the chance of observing between-configuration differences.
4. **Research-world domain.** Whether to keep fictional company research or also render a second domain early, to limit presentation-specific findings.

## 8. Cautions

- Frontier coverage is partial. Several cited deviations were observed in open-weight or earlier models, and our configurations may not show them.
- Canonical economics paradigms are published and may be recognizable. Use fictional content and novel structure, and follow contamination and shortcut controls ([Ivanova 2025](https://www.nature.com/articles/s41562-024-02096-z) [F, preprint]).
- Information-equivalent pairs must be audited for equivalence of content, not only of arithmetic.
- Coherence tests reward internal consistency, which can diverge from accuracy; generator truth takes precedence.
- Human benchmarks are task-conditional: dependency sensitivity appears in some framings ([Whalen, Griffiths & Buchsbaum 2018](https://doi.org/10.1111/cogs.12485) [A]) and not others ([Xie & Hayes 2022](https://doi.org/10.1111/cogs.13144) [A]).
- Numbers tagged [S] or [A] should be rechecked against the primary text before appearing in results, design specifications or external material.
- No claim here is a replication. The cited work motivates designs; our own evidence remains conditional on the tasks and configurations we test.

## Further references

Additional works consulted, grouped by theme, beyond those linked above:

- **LLM belief updating and calibration:**
  - [Imran et al. 2025](https://arxiv.org/abs/2507.17951) [S]: Bayesian coherence rising with scale, updates below 1 in pre-trained models.
  - [Qiu et al. 2026, Bayesian teaching](https://arxiv.org/abs/2503.17523) [S]: plateau after one round; fine-tuning on a Bayesian assistant transfers.
  - [Falck, Wang & Holmes 2024](https://arxiv.org/abs/2406.00793) [F].
  - [Laban et al. 2025](https://arxiv.org/abs/2505.06120) [A].
  - [Xiong et al. 2024](https://arxiv.org/abs/2306.13063) [A]; [Tian et al. 2023](https://arxiv.org/abs/2305.14975) [A].
  - [Yoon et al. 2025](https://arxiv.org/abs/2505.14489) [A] and [Mei et al. 2025](https://arxiv.org/abs/2506.18183) [A], with conflicting reasoning-model calibration findings.
  - [Kim & Kang 2026](https://arxiv.org/abs/2605.27752) [A]: protocol sensitivity of confidence calibration.
  - [Kalai et al. 2025](https://arxiv.org/abs/2509.04664) [A]; [Leng et al. 2024](https://arxiv.org/abs/2410.09724) [A].
  - [Prophet Arena (Yang et al. 2025)](https://arxiv.org/abs/2510.17638) [S]; [ForecastBench (Karger et al. 2025)](https://arxiv.org/abs/2409.19839) [A].
- **Information acquisition:**
  - [Coenen, Nelson & Gureckis 2019](https://link.springer.com/article/10.3758/s13423-018-1470-5) [A]; [Gureckis & Markant 2012](https://journals.sagepub.com/doi/10.1177/1745691612454304) [A]; [Nelson et al. 2010](https://journals.sagepub.com/doi/10.1177/0956797610372637) [A].
  - [Schulz & Gershman 2019](https://gershmanlab.com/pubs/SchulzGershman19.pdf) [A]; [Hunt et al. 2021](https://www.nature.com/articles/s41593-021-00866-w) [A].
  - [Gabaix et al. 2006](https://www.aeaweb.org/articles?id=10.1257%2Faer.96.4.1043) [A]; [Dean & Neligh 2023](https://www.journals.uchicago.edu/doi/full/10.1086/725174) [A].
  - [BED-LLM (Choudhury et al. 2026)](https://arxiv.org/abs/2508.21184) [A]; [BoxingGym (Gandhi et al. 2025)](https://arxiv.org/abs/2501.01540) [A]; [MediQ](https://arxiv.org/abs/2406.00922) [A]; [Pan, Xie & Wilson 2025](https://arxiv.org/abs/2501.18009) [A].
  - [Mozannar & Sontag 2020](https://proceedings.mlr.press/v119/mozannar20b.html) [A]; [Kamath, Jia & Liang 2020](https://aclanthology.org/2020.acl-main.503/) [A]; [Vasconcelos et al. 2023](https://arxiv.org/abs/2212.06823) [A].
  - [Liu et al. 2026, search stopping](https://arxiv.org/abs/2608.01913) [A]; [Xie et al. 2026, retrieval and abstention](https://arxiv.org/abs/2601.05503) [A].
- **Belief-updating models and reliability:**
  - [Grether 1980](https://academic.oup.com/qje/article-abstract/95/3/537/1934441) [A]; [Enke & Graeber 2023](https://academic.oup.com/qje/article-abstract/138/4/2021/7181327) [A].
  - [Mathys et al. 2011](https://www.frontiersin.org/articles/10.3389/fnhum.2011.00039/full) [S]; [Behrens et al. 2007](https://www.nature.com/articles/nn1954) [A]; [Behrens et al. 2008](https://www.nature.com/articles/nature07538) [A].
  - [Baker et al. 2019](https://academic.oup.com/brain/article/142/6/1797/5400582) [A]; [Shah et al. 2016](https://www.sciencedirect.com/science/article/pii/S0010028516301177) [A]; [Jardri et al. 2017](https://www.nature.com/articles/ncomms14218) [A].
  - [Karvelis, Paulus & Diaconescu 2023](https://www.sciencedirect.com/science/article/pii/S0149763423001069) [A]; [Agrawal, Peterson & Griffiths 2020](https://www.pnas.org/doi/10.1073/pnas.1915841117) [A]; [Ji-An, Benna & Mattar 2025](https://www.nature.com/articles/s41586-025-09142-4) [A].
  - [CogBench (Coda-Forno et al. 2024)](https://proceedings.mlr.press/v235/coda-forno24a.html) [A].
- **Measurement science:**
  - [Wallach et al. 2025](https://arxiv.org/abs/2502.00561) [S]: predictive and consequential validity lenses.
  - [Bean et al. 2025](https://arxiv.org/abs/2511.04703) [F]: only 16% of 445 benchmarks report uncertainty or statistical tests.
  - [HAL (Kapoor et al. 2025)](https://arxiv.org/abs/2510.11977) [S]; [Sclar et al. 2024](https://arxiv.org/abs/2310.11324) [A]; [PromptEval (Polo et al. 2024)](https://arxiv.org/abs/2405.17202) [A]; [Atil et al. 2024](https://arxiv.org/abs/2408.04667) [A].
  - [Zhou et al. 2024](https://doi.org/10.1038/s41586-024-07930-y) [A]; [Dominguez-Olmedo, Hardt & Mendler-Dünner 2024](https://arxiv.org/abs/2306.07951) [A].
  - [Tailor et al. 2024, learning to defer to a population](https://proceedings.mlr.press/v238/tailor24a.html) [A]; [Tomašev, Franklin & Osindero 2026](https://arxiv.org/abs/2602.11865) [S].
- **Source credibility and naturalistic evaluation:**
  - [Sperber et al. 2010](https://doi.org/10.1111/j.1468-0017.2010.01394.x); [Mercier & Morin 2019](https://www.cambridge.org/core/journals/evolutionary-human-sciences/article/majority-rules-how-good-are-we-at-aggregating-convergent-opinions/4EF8411F0637FFA1C0ADEFFB631A4874) [A]; [Young, Madsen & de-Wit 2025](https://doi.org/10.1016/j.cognition.2025.106126) [A].
  - [Kawada & Kellis 2026](https://arxiv.org/abs/2609.04290) [A]; [Xu et al. 2024](https://aclanthology.org/2024.acl-long.858/) [A]; [Sharma et al. 2024](https://arxiv.org/abs/2310.13548) [A].
