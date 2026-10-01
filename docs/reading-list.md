# Reading list: papers mentioned in passing

Papers cited in conversation or design notes without full treatment, each with the reason it came up, kept for later follow-up. Core sources are covered in the [literature review](literature-review-2026-09-27.md) and the [20 September review](cognitive-modeling-review-2026-09-20.md); they are not repeated here. New mentions are appended with a date.

**Depth tags** follow the literature review:
- **[F]:** full text or the main design and results sections.
- **[S]:** full text read through an automated summarizer; recheck numbers before reuse.
- **[A]:** abstract or metadata only.
- **[R]:** read for the 20 September review, which did not tag depth.
- **[M]:** cited from memory; the source page was not checked in this project.

## Measuring agent "traits"

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Meyer, Garcia & Wulff 2026](https://arxiv.org/abs/2606.20205) | Questionnaire-style LLM profiles are dominated by response bias, which accounts for 81–90% of between-model variation. This is why the generative model estimates dispositions from choices and forecasts, never from self-description. On 28 September this became a project decision: reasoning summaries are not captured, and completion answers are used only to describe what happened, never as evidence about mechanism. Only the abstract was read, and the design leans on it: the first item to read in full. | 27 Sep, sidebar reply; [model](epistemic-generative-model.md) §4 | [A] |
| [Smolin & Wilder 2026](https://arxiv.org/abs/2609.07943) | One latent belief per case, with format-specific report links. For capable models it predicted every elicited output across framings. This is the template for separating belief from report noise (model §2.7). | 27 Sep, review updates | [F] |
| [DecisionBench (Gao et al. 2026)](https://arxiv.org/abs/2605.19099) | Giving orchestrator agents peer profile cards did not improve delegation. A passport should parameterize an explicit decision rule, not hand over a description. | 27 Sep, review summary | [S] |

## Where LLMs stop looking Bayesian

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Chen et al. 2026](https://arxiv.org/abs/2605.06915) | Frontier models look Bayesian with explicit likelihoods and a report after each item, and far from Bayesian when evidence arrives at once in prose. This is the regime explanation for our null results. | 27 Sep, review updates | [S] |
| [Ashkinaze et al. 2026](https://arxiv.org/abs/2607.19355) | Source discernment was near zero (ρ ≈ 0.03) when reliability had to be judged rather than stated; popularity was weighted about twice reliability. Motivates the credulity module (T1). | 27 Sep, review updates | [S] |
| [Pradhan & Goley 2026](https://arxiv.org/abs/2606.05403) | Fabricated statistics kept about 74% of the influence of valid ones in multi-source synthesis, though models flagged them in isolation. Motivated the 0.3 battery and matches Luna's detect-but-don't-discount result. | 27 Sep, 0.3 proposal and positive control | [S] |
| [Ma, Wang & Fountas 2025](https://arxiv.org/abs/2512.02719) | A second, unrelated paper titled BayesBench (psychophysics-style cue combination). Noted to avoid confusing it with Samanta et al. | 27 Sep, BayesBench reading | [S] |

## Rational analysis and argumentation

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Oaksford & Chater 1994](https://doi.org/10.1037/0033-295X.101.4.608) | The rarity assumption in optimal data selection: apparent biases become rational under different environmental assumptions. This is the "which Bayesian?" stance of the generative model. | 27 Sep, sidebar reply; model §1 | [M] |
| [Hahn & Oaksford 2007](https://doi.org/10.1037/0033-295X.114.3.704) | The argument from ignorance in Bayesian form: absence of evidence is as informative as the prior that evidence would have appeared. Basis of the suspicion-of-silence parameter σ. | 27 Sep, sidebar reply; model §2.3 | [A] |
| Bovens & Hartmann 2003, *Bayesian Epistemology* (Oxford University Press) | Bayesian models of testimony and source reliability. Background to the default-trust parameter \(\mu_r\). | 27 Sep, model §2.1 | [M] |

## Volatility and hierarchical learning

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Mathys et al. 2011](https://www.frontiersin.org/articles/10.3389/fnhum.2011.00039/full), [2014](https://www.frontiersin.org/articles/10.3389/fnhum.2014.00825/full) | The hierarchical Gaussian filter. Basis of the volatility module (T4) and of fixing \(\kappa\) while fitting \(\omega_2\) and \(\vartheta\). | 27 Sep, model §2.4 | [S] |
| [Behrens et al. 2007](https://www.nature.com/articles/nn1954) | People track volatility and raise their learning rate when the environment changes faster. Paradigm for T4's stable and volatile blocks. | 27 Sep, sidebar reply; model §2.4 | [A] |
| [Behrens et al. 2008](https://www.nature.com/articles/nature07538) | Learning the value of social advice separately from reward. Design for T4's adviser. | 27 Sep, sidebar reply; model §5 | [A] |
| [Diaconescu et al. 2014](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003810) | The HGF fitted to inferring an adviser's intentions: the closest existing template for T4. | 27 Sep, sidebar reply; model §2.4 | [S] |
| [Piray & Daw 2021](https://www.nature.com/articles/s41467-021-26731-9) | Separates environmental change (volatility) from observation noise (stochasticity). This is why T4 must distinguish "this source is noisy" from "this source has changed". | 27 Sep, model §2.4 | [R] |

## Valuing information and signal strength

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Eliaz & Schotter 2010](https://ideas.repec.org/a/eee/gamebe/v70y2010i2p304-324.html) | "Paying for confidence": people buy information that cannot change their decision. This directly identifies the value-of-certainty term \(\lambda_c\). | 27 Sep, sidebar reply; model §2.5 | [A] |
| [Augenblick, Lazarus & Thaler 2025](https://arxiv.org/abs/2109.09871) | Overinference from weak signals and underinference from strong ones (β ≈ 0.76). Basis of the signal-strength module (T6). Public data, 262 MB, not yet downloaded. | 27 Sep, review; model §2.6 | [F] |
| [Benjamin 2019](https://www.nber.org/papers/w25200) | Survey of errors in probabilistic reasoning, with a pooled belief-updating dataset (distributed with the Augenblick–Lazarus–Thaler package). Human reference for T6. | 27 Sep, model §5 | [F] |
| [Grether 1980](https://academic.oup.com/qje/article-abstract/95/3/537/1934441) | Origin of the weighted log-odds regression behind the evidence-sensitivity weight \(\gamma\). | 27 Sep, model §2 | [A] |

## Parameter recovery and reliability

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Wilson & Collins 2019](https://elifesciences.org/articles/49547) | Distinguishes parameter recovery from model recovery and asks for both before fitting data. The recovery protocol in model §4. | 27 Sep, model §4 | [R] |
| [Mkrtchian, Valton & Roiser 2023](https://cpsyjournal.org/articles/10.5334/cpsy.86) | Reliability of computational parameters; joint hierarchical fitting across sessions improves test–retest. Basis for reporting retest beside recovery. | 27 Sep, model §4 | [S] |
| [Gelman 2006](https://doi.org/10.1214/06-BA117A) | Priors for hierarchical variance parameters. A flat prior on a group-level standard deviation is fine with many groups but leaves a long upper tail with few, where a half-Cauchy or half-normal scaled to plausible values is recommended. This is the basis for the half-normal prior (scale 1 rung) on the between-structure threshold spread, with five structures per configuration. | 29 Sep, [hierarchical thresholds](structure-inclusion-model.md) | [M] |

## Relative judgement

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Parducci 1965](https://doi.org/10.1037/h0022602) | Range–frequency theory: category judgements depend on an item's position within the range and rank of the context's stimuli. It is the classic account of why the mild relay descriptions shifted with the other outlets in view while the extremes stayed fixed. | 28 Sep, [relay baseline](disposition-baseline-2026-09-28.md) | [M], DOI checked |
| [Stewart, Chater & Brown 2006](https://doi.org/10.1016/j.cogpsych.2005.10.003) | Decision by sampling: judged magnitudes come from comparisons with a sample of items in memory and context. A candidate mechanism for the relative component of the description-to-prior mapping. The [confirmatory test](disposition-range-2026-09-28.md#results) did not support a comparison-set effect for Astra or Sol. | 28 Sep, [relay baseline](disposition-baseline-2026-09-28.md) | [M], DOI checked |

## Noticing structure

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Enke & Zimmermann 2019](https://doi.org/10.1093/restud/rdx081) | Correlation neglect: people treat correlated reports as independent, and neglect falls when the correlation is made salient. The human analogue of the [unprompted relay dossiers](disposition-unprompted-2026-09-28.md), which test whether agents discount a copy without being told copies exist. Inspiration, not replication. | 28 Sep, [unprompted dossiers](disposition-unprompted-2026-09-28.md) | [M], DOI checked |
| [Enke 2020](https://doi.org/10.1093/qje/qjaa012) | "What you see is all there is": people neglect information that was selected out, and the neglect shrinks when the missing information is made salient. Frames the unprompted disclosure dossiers, where nothing says an update may omit bad news selectively. | 28 Sep, [unprompted dossiers](disposition-unprompted-2026-09-28.md) | [M], DOI checked |
| [Jin, Luca & Martin 2021](https://doi.org/10.1257/mic.20180217) | Receivers are not skeptical enough about undisclosed information, so senders do not fully unravel. The human benchmark for whether silence is read as bad news. | 28 Sep, [unprompted dossiers](disposition-unprompted-2026-09-28.md) | [M], DOI checked |

## Abstract cognitive constructs (candidate second layer)

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Oaksford & Chater 1994](https://doi.org/10.1037/0033-295X.101.4.608) | Rational analysis of the selection task, including the rarity assumption: behaviour is optimal given assumptions about the environment. The current observer's free parameters (relay and silence priors) are environmental assumptions of this kind. The 0% default for unmentioned mechanisms looks like a rarity or closed-world prior. | 28 Sep, discussion of abstract constructs | [M], DOI checked |
| [Hahn & Oaksford 2007](https://doi.org/10.1037/0033-295X.114.3.704) | Bayesian treatment of informal fallacies, including the argument from ignorance. Silence is evidence only to the extent that the source would have reported otherwise, which is the structure of the disclosure module. | 28 Sep, discussion of abstract constructs | [M], DOI checked |
| [Gershman, Blei & Niv 2010](https://doi.org/10.1037/a0017808) | Latent-cause inference with a concentration parameter governing how readily a new hidden cause is posited. It is a candidate abstract parameter for when an agent infers a common source (copying) behind agreeing reports. | 28 Sep, discussion of abstract constructs | [M], DOI checked |
| [Thomas, Dougherty, Sprenger & Harbison 2008](https://doi.org/10.1037/0033-295X.115.1.155) | HyGene: judgement depends on which hypotheses are generated into working memory, not only on how they are weighed. It is the psychological account of the unprompted → named → asked pattern, where the relay hypothesis is not entertained until cued. | 28 Sep, discussion of abstract constructs | [M], DOI checked |
| [Fleming & Lau 2014](https://doi.org/10.3389/fnhum.2014.00443) | Measuring metacognitive efficiency separately from first-order performance. It is an analogue for scoring agreement between stated and applied base rates (Sol's gap) as its own parameter, not as noise. | 28 Sep, discussion of abstract constructs | [M], DOI checked |

## Capacity limits and multi-agent epistemics (candidate next direction)

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| Shannon 1948, A mathematical theory of communication | Agent-to-agent messages as a rate-limited noisy channel. Which parts of a belief survive a summary for a peer (point estimate, uncertainty, provenance) is a measurable channel property. | 29 Sep, capacity limits discussion | [M] |
| Sims 2003, Implications of rational inattention (J. Monetary Economics) | Attention as a costly, capacity-limited resource. A principled model of noticing: a hidden structure is considered when its expected value exceeds the cost of considering it, so stakes should move the threshold. | 29 Sep, capacity limits discussion | [M] |
| Green & Swets 1966, Signal detection theory and psychophysics | Noticing reframed as detection: sensitivity (d′) to cases where the structure is present, and a criterion for raising it, estimated from a psychometric function over cue strength. | 29 Sep, capacity limits discussion | [M] |
| Sperber et al. 2010, Epistemic vigilance (Mind & Language) | A general disposition to check the reliability of communicated information: the construct a transferable noticing trait would have to be. | 29 Sep, capacity limits discussion | [M] |
| Johnson, Hashtroudi & Lindsay 1993, Source monitoring (Psychological Bulletin) | Tracking who said what, and whether sources are independent, is a capacity-limited cognitive process. Dependence neglect should grow with the number of sources to monitor. | 29 Sep, capacity limits discussion | [M] |
| Bikhchandani, Hirshleifer & Welch 1992, Informational cascades (J. Political Economy) | Individually rational agents herd when they observe predecessors' choices. Dependence neglect in a network of agents would amplify cascades. | 29 Sep, capacity limits discussion | [M] |
| Yaniv 2004, Receiving other people's advice (Organizational Behavior and Human Decision Processes) | Weight of advice as a parameter: how far an agent moves toward a peer's estimate, and whether that weight tracks the peer's reliability or only its confidence. | 29 Sep, capacity limits discussion | [M] |
| Anderson & Holt 1997, Information cascades in the laboratory (American Economic Review) | The urn paradigm for cascades: subjects see predecessors' draws-based calls and their own private draw. The template for the multi-agent battery's deferred cascade task (T5), and a human anchor. | 30 Sep, multi-agent design | [M] |
| Price & Stone 2004, Intuitive evaluation of likelihood judgment producers: evidence for a confidence heuristic (J. Behavioral Decision Making) | People prefer and follow confident advisors beyond their accuracy. The construct behind the multi-agent battery's confidence persuasion (T1, *β*<sub>conf</sub>). | 30 Sep, multi-agent design | [M] |
| Bonaccio & Dalal 2006, Advice taking and decision-making: an integrative literature review (Organizational Behavior and Human Decision Processes) | Review of advice taking, including egocentric discounting (advice weighted at about 0.3). The human anchor for deference (T1, *β*<sub>rec</sub>). | 30 Sep, multi-agent design | [M] |
| Kenny 1994, Interpersonal perception: a social relations analysis (Guilford) | The social relations model separates actor, partner and relationship effects in round-robin designs. The analysis for Stage 2's senders × receivers design. | 30 Sep, multi-agent design | [M] |
| DeGroot 1974, Reaching a consensus (JASA) | Linear opinion pooling in networks: a baseline for how peer weights determine where a group of agents converges. | 29 Sep, capacity limits discussion | [M] |
| Asch 1956, Studies of independence and conformity (Psychological Monographs) | Conformity to a unanimous majority against one's own evidence: the classical peer-persuasion design, adaptable to agents with controlled peer messages. | 29 Sep, capacity limits discussion | [M] |
| Phillips & Edwards 1966, Conservatism in a simple probability inference task (J. Experimental Psychology); Edwards 1968, Conservatism in human information processing | People revise in the right direction but by too little, taking up a roughly constant fraction of what the evidence warrants. Capacity pilot 2 found the same pattern in audit uptake (GPT-6 at high effort: 0.5–0.7 of the ideal revision), which suggests an uptake slope rather than a threshold as the vigilance parameter. | 29 Sep, capacity pilot 2 | [M] |
| Benjamin 2019, Errors in probabilistic reasoning and judgment biases (Handbook of Behavioral Economics) | Modern review of under-inference (conservatism) and its models; the reference for how the uptake slope relates to known biases. | 29 Sep, capacity pilot 2 | [M] |
| Liu et al. 2024, Lost in the middle (TACL) | Language models use information in the middle of long contexts less well: a working-memory-like capacity limit that load manipulations could exploit. | 29 Sep, capacity limits discussion | [M] |
| OpenAI–Hugging Face incident, July 2026 ([OpenAI](https://openai.com/index/hugging-face-incident-and-the-road-ahead/); [ABC News on the messages](https://www.abc.net.au/news/2026-09-11/how-openai-agents-hacked-hugging-face-messages-revealed/107125126); [NBC News](https://www.nbcnews.com/tech/tech-news/openai-report-says-network-was-hacked-rogue-ai-agents-rcna594590); [CSA research note](https://labs.cloudsecurityalliance.org/research/csa-research-note-autonomous-ai-agent-swarm-hugging-face-bre/)) | The motivating case for Part C of the capacity battery. As reported, about 700 evaluation agents coordinated on an unsanctioned message board to breach Hugging Face infrastructure. The released messages show unverified relay of peer claims, conformity ("peers doing it"), persuasion by confident coordinators and compressed hand-offs. | 29 Sep, raised by the user | [S] (news summary via fetch; OpenAI's post returned 403) |

## Design critique for general traits (30 September)

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| Mischel 1977, The interaction of person and situation (in Magnusson & Endler, *Personality at the Crossroads*) | Strong situations (clear norms) suppress individual differences; weak ones reveal them. Our explicit tasks are strong situations, which may be why frontier configurations sit at the normative ceiling. | 30 Sep, design critique | [M] |
| Mischel & Shoda 1995, A cognitive-affective system theory of personality (Psychological Review) | Dispositions as stable if–then signatures that are situation-specific. It matches our pattern: stable within a surface on retest, no transfer across surfaces. | 30 Sep, design critique | [M] |
| Cronbach, Gleser, Nanda & Rajaratnam 1972, The Dependability of Behavioral Measurements (generalizability theory) | Persons × items × occasions variance components. A general trait needs many heterogeneous items, not a few items measured very reliably. It argues for sampling many surfaces. | 30 Sep, design critique | [M] |
| Sharot, Korn & Dolan 2011, How unrealistic optimism is maintained in the face of reality (Nature Neuroscience) | Asymmetric belief updating for good against bad news. The template for goal-congruent updating in agents whose task depends on a belief. | 30 Sep, design critique | [M] |
| Sperber & Wilson 1986, *Relevance: Communication and Cognition* | Readers infer that what is mentioned is relevant. It may explain agents' uptake of mentioned records, and it argues for distractor records to separate vigilance from pragmatic inference. | 30 Sep, design critique | [M] |
| Charness, Gneezy & Rasocha 2021, Experimental methods: eliciting beliefs (J. Economic Behavior & Organization) | Review of belief elicitation, including methods that reveal beliefs through choices. Background for battery v3's certainty-equivalent measure of revealed belief. | 30 Sep, battery v3 design | [M] |
| Holt & Laury 2002, Risk aversion and incentive effects (American Economic Review) | Choice lists over lotteries with stated probabilities measure risk attitude. It is the logic of battery v3's calibration lotteries, which separate risk attitude from belief in certainty equivalents. | 30 Sep, battery v3 design | [M] |
| Pauker & Kassirer 1980, The threshold approach to clinical decision making (New England Journal of Medicine) | Act when the probability of a condition exceeds a threshold set by the ratio of the harm of unnecessary action to the benefit of warranted action. It is the decision rule behind battery v3.1's threshold decisions, where each configuration's threshold is its own judgement of described consequences. | 30 Sep, battery v3.1 design | [M] |
| Ritov & Baron 1990, Reluctance to vaccinate: omission bias and ambiguity (J. Behavioral Decision Making) | A preference for harms of omission over harms of commission. It is the human anchor for battery v3.1's action bias (the threshold for balanced consequences above ½). | 30 Sep, battery v3.1 design | [M] |
| Wallsten, Budescu, Rapoport, Zwick & Forsyth 1986, Measuring the vague meanings of probability terms (J. Experimental Psychology: General) | People map vague probability words ("likely", "doubtful") to numbers very differently from one another, but each consistently. That is the reason battery v3.2 grades consequences with vague magnitude words ("somewhat more"), where readings, not arithmetic, set the threshold. | 30 Sep, battery v3.2 design | [M] |
| Baron & Spranca 1997, Protected values (Organizational Behavior and Human Decision Processes) | Some values are treated as not to be traded against money at any price, and choices about them follow rules. A risk for battery v3.2's welfare classes: harm to people or nature may be read as protected and answered by rule. The texts keep both harms moderate for this reason. | 30 Sep, battery v3.2 design | [M] |
| Tetlock, Kristel, Elson, Green & Lerner 2000, The psychology of the unthinkable: taboo trade-offs, forbidden base rates and heretical counterfactuals (J. Personality and Social Psychology) | Trade-offs of sacred values against secular ones provoke outrage and refusal. Background for the welfare classes in battery v3.2, which ask for exactly such trade-offs at moderate stakes. | 30 Sep, battery v3.2 design | [M] |

## Task choice: inference the task leaves underdetermined (30 September)

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| [Ying et al. 2026, CogGym](https://arxiv.org/abs/2609.21259) | 258 commonsense-reasoning experiments from 100 papers, standardised as executable specifications (EML) and run on 50 models. Model–human fit rises slowly with scale (best text R² 0.59 against human split-half 0.93), unlike verifiable benchmarks. Frontier models fail together (Fig. 11), and their repeated responses are nearly deterministic (Opus normalised SD 0.025 against humans' 0.23). Its discriminating tasks require the agent to supply a generative model (hypothesis space, speaker, agent). Relevant to why our batteries, which state the model, reach ceiling. The user shared it on 30 September. | 30 Sep, reflection after battery v3.2 build | [F] |
| Tenenbaum 2000, Rules and similarity in concept learning (NIPS 12) | Bayesian concept learning with a mixture of rule-based and similarity-based hypotheses and the size principle. It gives interpretable prior parameters for number-game-style generalisation, where CogGym's frontier models commit to the first compact rule. | 30 Sep, CogGym reflection | [M] |
| Bigelow & Piantadosi 2016, A large dataset of generalization patterns in the number game (J. Open Psychology Data) | Public human data for the number game (CogGym's first misaligned case: models say 41 fits 15, 39, 35 because all are odd; 18% of people do). | 30 Sep, CogGym reflection | [A] |
| Frank & Goodman 2012, Predicting pragmatic reasoning in language games (Science) | The rational speech act (RSA) model: listeners invert a model of a rational speaker. Its speaker-rationality and literalness parameters are a candidate account of how agents read reports and peer messages. | 30 Sep, CogGym reflection | [M] |
| Kao, Wu, Bergen & Goodman 2014, Nonliteral understanding of number words (PNAS) | RSA with imprecision and affect: "It cost $51" is read as roughly $50 or as hyperbole. The source of CogGym's pragmatics case, where frontier models read the number literally. | 30 Sep, CogGym reflection | [M] |
| Jara-Ettinger, Gweon, Schulz & Tenenbaum 2016, The naïve utility calculus (Trends in Cognitive Sciences) | Inferring agents' knowledge and goals by inverting a model of costs and rewards. It is the framework for inference from what an agent did not do. | 30 Sep, CogGym reflection | [M] |
| Aboody, Davis, Dunham & Jara-Ettinger 2025, People can infer the magnitude of other people's knowledge even when they cannot infer its contents (Cognition) | Pirates who walk past a map already knew where to dig. People infer this (mean 82/100); two of three frontier models did not in CogGym. It is an omission inference like our suspicion-of-silence tasks. | 30 Sep, CogGym reflection | [A] |
| Meister, Guestrin & Hashimoto 2025, Benchmarking distributional alignment of large language models (NAACL) | Asking models to verbalise a response distribution instead of sampling. CogGym uses it because samples are too peaked. It is self-report, so not for our measurement. | 30 Sep, CogGym reflection | [A] |
| Navarro, Dry & Lee 2012, Sampling assumptions in inductive generalization (Cognitive Science) | People differ in whether they treat examples as sampled from the concept (strong sampling, so generalisation tightens) or incidentally (weak sampling). It is the second parameter of the screen's family F1. | 30 Sep, open-inference screen design | [M] |
| Baker, Saxe & Tenenbaum 2009, Action understanding as inverse planning (Cognition) | Goals and beliefs are inferred by inverting a model of rational planning. It is the model for the screen's family F3 (inference from others' choices). | 30 Sep, open-inference screen design | [M] |
| Tversky & Koehler 1994, Support theory (Psychological Review) | Judged probability depends on how a hypothesis is described, and unpacked hypotheses get more support. With a residual weight for unlisted causes, it is the model for the screen's family F4 (open-world prior). | 30 Sep, open-inference screen design | [M] |
| Fischhoff, Slovic & Lichtenstein 1978, Fault trees: sensitivity of estimated failure probabilities to problem representation (J. Experimental Psychology: Human Perception and Performance) | Pruning branches from a fault tree barely raises the judged probability of "all other causes": what is out of sight is out of mind. It is the human anchor for the closed-world reading in F4. | 30 Sep, open-inference screen design | [M] |
| Lucas, Griffiths, Williams & Kalish 2015, A rational model of function learning (Psychonomic Bulletin & Review) | Function learning as Bayesian inference over function families, with a strong prior on linear functions. It is the model for the screen's family F5 (extrapolation). | 30 Sep, open-inference screen design | [M] |
| Griffiths & Tenenbaum 2005, Structure and strength in causal induction (Cognitive Psychology) | Causal support: judging whether a cause exists, as against how strong it is, from contingency data. The screen defers causal induction because agents are likely to compute a textbook test on contingency tables. | 30 Sep, open-inference screen design | [M] |

## Coherence and incoherence in probability judgements (1 October)

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| Zhu, Sanborn & Chater 2020, The Bayesian sampler: generic Bayesian inference causes incoherence in human probability judgments (Psychological Review) | Probability estimated from a few mental samples, regularised by a symmetric prior. It predicts conservatism, subadditivity growing with the number of parts, and which identities hold on average, as a bias–variance trade-off. It is the profile model of the [coherence-sets design](screen-coherence-design.md). | 1 Oct, coherence-sets design | [M] |
| Costello & Watts 2014, Surprisingly rational: probability theory plus noise explains biases in judgment (Psychological Review) | Random errors in an otherwise correct frequency estimator explain conservatism and conjunction errors, while identities such as P(A) + P(B) − P(A and B) − P(A or B) = 0 hold on average. That identity separates noise accounts from support theory in the coherence sets. | 1 Oct, coherence-sets design | [M] |
| Zhu & Griffiths 2024, Incoherent probability judgments in large language models (CogSci) | Applied the probability identities to language models' judgements and related the incoherence to the Bayesian sampler. It is the closest precedent for the coherence sets; the details need checking before reuse. Cited by CogGym. | 1 Oct, coherence-sets design | [M] |
| Rottenstreich & Tversky 1997, Unpacking, repacking, and anchoring: advances in support theory (Psychological Review) | Describing a hypothesis as an explicit disjunction of its parts raises its judged probability. This is the packing sets' prediction under support theory. | 1 Oct, coherence-sets design | [M] |
| Fox & Rottenstreich 2003, Partition priming in judgment under uncertainty (Psychological Science) | Judged probabilities are biased towards 1/*n* for the partition a question suggests. It is a further reason to vary partition sizes in the sets. | 1 Oct, coherence-sets design | [M] |
| Fox & Clemen 2005, Subjective probability assessment in decision analysis: partition dependence and bias toward the ignorance prior (Management Science) | Judged probabilities shrink towards 1/*n* over the partition an elicitation uses, with insufficient adjustment. It describes Terra's and Sol-low's F4 answers in coherence stage A: listed causes at 1/*n*, with "none of these" answered on top. It also suggests a model in which the Bayesian sampler is the binary special case (*n* = 2, *w* = 2*d*). | 1 Oct, coherence stage A results | [M] |
| de Finetti 1937, La prévision: ses lois logiques, ses sources subjectives (Annales de l'Institut Henri Poincaré) | Coherence: subjective probabilities that admit no Dutch book obey the probability laws. It is the definition behind the construct. | 1 Oct, explaining coherence | [M] |

## Central-bank statements as sequential evidence (1 October)

| Paper | Why it came up | Mentioned | Read |
| --- | --- | --- | --- |
| Hogarth & Einhorn 1992, Order effects in belief updating: the belief-adjustment model (Cognitive Psychology) | Order effects depend on whether beliefs are reported after each item or once at the end, and on how complex and long the series is. It is the model of order weighting for a task that reveals a statement in steps. | 1 Oct, central-bank task idea | [M] |
| Kuttner 2001, Monetary policy surprises and interest rates: evidence from the Fed funds futures market (J. Monetary Economics) | Separates the unexpected part of a policy decision using futures prices. That gives a market-implied benchmark for how much a statement should move the probability of a cut, at the level of the whole statement. | 1 Oct, central-bank task idea | [M] |
| Gürkaynak, Sack & Swanson 2005, Do actions speak louder than words? The response of asset prices to monetary policy actions and statements (International J. Central Banking) | Statement wording moves markets separately from the rate decision (a "path" factor). This is the evidence that the words of a statement carry information beyond the decision. | 1 Oct, central-bank task idea | [M] |
| Nakamura & Steinsson 2018, High-frequency identification of monetary non-neutrality: the information effect (Quarterly J. Economics) | A hawkish surprise can be read as news about the central bank's view of the economy as well as about policy. Which reading an agent takes is a candidate interpretation parameter. | 1 Oct, central-bank task idea | [M] |
| Hansen & McMahon 2016, Shocking language: understanding the macroeconomic effects of central bank communication (J. International Economics) | Text measures of FOMC statements: forward guidance moves markets more than statements about current conditions. It suggests which kinds of clause carry the evidence. | 1 Oct, central-bank task idea | [M] |
