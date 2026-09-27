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
| [Meyer, Garcia & Wulff 2026](https://arxiv.org/abs/2606.20205) | Questionnaire-style LLM profiles are dominated by response bias, which accounts for 81–90% of between-model variation. This is why the generative model estimates dispositions from choices and forecasts, never from self-description. Only the abstract was read, and the design leans on it: the first item to read in full. | 27 Sep, sidebar reply; [model](epistemic-generative-model.md) §4 | [A] |
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
