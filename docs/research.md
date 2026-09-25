# Research basis and measurement choices

The [20 September cognitive-modeling review](cognitive-modeling-review-2026-09-20.md) revisits Gershman, Ullman, Bayesian/RL models, active learning and individual measurement after the completed provenance benchmark. It proposes a discovery-task revision; the implemented tasks described below remain unchanged.

The [24 September source-inference proposal](source-inference-design-2026-09-24.md) develops the next design in detail after the narrative results: persistent source learning, competence versus selection, explicit competing models, diagnostic contrasts, less prompted discovery and tested support. Its first [offline design laboratory](source-inference-lab.md) is implemented, with [synthetic discrimination results](source-inference-results-2026-09-25.md). Participant collection and the wider extensions remain proposed; no current task or active session is changed.

The first resulting implementation is the separately versioned [company investigation](company-investigation.md): joint attribution, active research and correction, with conditional synthetic recovery and a matched-forecast diagnostic. Its protocol and remaining measurement limits are documented separately from the legacy tasks below.

The product is an [epistemic passport](epistemic-passport.md). These models explain and check the measurements beneath its readable behavioral profile. The tasks draw on cognitive science, but the customer's workflow is a standard evaluation and a useful identity artifact. This document retains the original battery's measurement details; newer company and discovery protocols have their own specifications.

## What we mean by a belief parameter

A parameter is a compact description of reported probabilities under a task model and prompting protocol. An LLM can calculate a posterior on request without using that representation in other decisions. We therefore report task-conditional estimates, their model assumptions, and the complete observations. No single task identifies general epistemic quality.

## Foundations

| Primary source | Contribution to this project | Scope of use |
| --- | --- | --- |
| Gershman (2019), [How to never be wrong](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf), *Psychonomic Bulletin & Review* 26, 13–28, [DOI](https://doi.org/10.3758/s13423-018-1488-8) | Belief revision can occur in auxiliary assumptions as well as a central hypothesis; resistance to disconfirmation need not imply defective updating. | Motivates the joint claim/source-validity task. Our binary sensor design is new. |
| Gershman, Norman & Niv (2015), [Discovering latent causes in reinforcement learning](https://gershmanlab.com/pubs/GershmanNormanNiv15.pdf) | Learning can involve discovering hidden structure, rather than only changing the strength of a fixed association. | Motivates distinguishing latent-state inference from a delta rule. The MVP fixes the state space; it does not fit latent-cause discovery. |
| Wilson, Nassar & Gold (2013), [A Mixture of Delta-Rules Approximation to Bayesian Inference in Change-Point Problems](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003150), with the [2018 correction](https://doi.org/10.1371/journal.pcbi.1006210) | Adaptive learning in changing environments can be compared with computationally simpler learning rules. | Motivates sequential forecast tasks and model comparison. We implement a binary HMM and a fixed delta rule, not their continuous change-point model. |
| Bhui, Lai & Gershman (2021), [Resource-rational decision making](https://gershmanlab.com/pubs/Bhui21.pdf), *Current Opinion in Behavioral Sciences* 41, 15–21 | Performance should be interpreted relative to computational costs and constraints. | Drives the next experiment: information acquisition and performance under explicit budgets. Not claimed as a fitted MVP construct. |

The literature motivates the experimental questions. It does not validate this battery for LLM agents. The repository's parameter-recovery tests establish behavior of the implementation under specified synthetic agents, not psychometric validity.

## Task 1: prior and evidence integration (24 trials)

Each independent trial presents a binary hypothesis H, an explicit prior π, a symmetric sensor accuracy a, and one signal s. The full factorial crosses π ∈ {0.2, 0.5, 0.8}, a ∈ {0.6, 0.85}, and s ∈ {0, 1}, with two repetitions and randomized order.

The reference is `logit P(H=1|s) = logit π + (2s−1) logit a`. Fit the descriptive regression:

`logit reported_p = bias + prior_weight × logit π + evidence_weight × (2s−1) logit a`.

The reference parameter vector is (0, 1, 1). Orthogonal manipulations separate prior and evidence weighting within this model. They cannot separate instruction interpretation, arithmetic ability and internal inference mechanisms. Reports of 0/1 remain valid; only log loss and logit computations clip them to [10⁻⁶, 1−10⁻⁶]. Endpoint counts are reported.

For a balanced design we select signal conditions first, then draw the hidden H from its conditional posterior. Thus Brier/log scores refer to this experimental distribution, not a naturally sampled population of cases. No truth feedback is given during these trials.

## Task 2: claim and source reliability (16 trials)

H and source validity V begin independent. A valid source is 90% accurate; an invalid source outputs a fair coin independent of H. Cross priors P(H=1) ∈ {0.2, 0.8}, P(V=1) ∈ {0.25, 0.75}, and both signals, with two repetitions.

The agent reports both `P(H=1|s)` and `P(V=1|s)`. The reference enumerates the four (H,V) states and normalizes their joint probability. This makes attribution of unexpected evidence observable. An agent holding H strongly can reasonably lower its estimate of source validity after a contradictory signal.

Report RMSE against both reference marginals and proper scores against a joint conditional draw of H,V. Fit source bias, prior weight, and update weight:

`logit reported_v = source_bias + source_prior_weight × logit prior_v + source_update_weight × (logit reference_v − logit prior_v)`.

These are descriptive sensitivities, not a diagnosed tendency toward rationalization. We need transfer to unfamiliar source models and contrasting generative assumptions before interpreting any broad trait.

## Task 3: sequential reversal learning (48 forecasts)

A binary hidden regime begins with equal probability and emits outcome 1 with probability 0.2 or 0.8. Between trials it switches with probability 0.1. These statistics are disclosed. The agent predicts each outcome before it is revealed; the complete past sequence is supplied to avoid accidental confounding with context-window loss.

Compare two families fitted to the agent's reported probabilities:

- Delta rule: `q(t+1) = q(t) + α × (y(t) − q(t))`, `q(0)=0.5`, α ∈ [0,1].
- Two-state HMM: update the regime posterior with the current emission, then mix it using a fitted effective hazard h ∈ [0,0.5]. Forecasts use the resulting pre-outcome regime belief.

Fit each parameter over 501 grid points using only the first 32 reports. Evaluate prediction error against the remaining 16 reports, with observed outcome history available as it would be online. The test block is used once for comparison, not optimization. This is model fit to behavior, separate from Brier/log predictive performance against actual outcomes.

A near-optimal parameter range includes grid values with training MSE at most 0.0001 above the minimum. It is a sensitivity diagnostic, **not a confidence interval**. Broad or boundary ranges flag that interpretation may be weak. The small run can contain few or no switches; do not discard such runs silently. Replicate across evaluator-assigned seeds.

## Uncertainty and validation

The independent-task regressions use 200 paired bootstrap resamples, discarding rank-deficient draws. Their percentile intervals describe within-run variation under that resampling scheme. Repeated conditions, deterministic agents, floor/ceiling reports and small sample sizes can produce misleadingly narrow intervals. Population uncertainty requires repeated runs, paraphrases and a hierarchical analysis.

Implemented tests cover analytic Bayesian solutions, recovery of multiple prior/evidence weights, noisy synthetic reports, effective hazard recovery, and exclusion of held-out reports from fitting. The MCP integration test uses the same public prompts available to an agent. It cannot read the server's trial state.

For the passport, validation is part of releasing each measurement and interpretation:

1. Use known synthetic policies and confusing alternatives to check recovery, failed fits and misattribution. The newer [discovery study tooling](discovery-study.md) implements additional checks for its own model family.
2. Check real-agent repeatability under recorded configuration and context policies. Record refusals and incomplete runs as outcomes, and distinguish within-run uncertainty from stability across executions.
3. Test irrelevant label/wording sensitivity and material tool or budget conditions before making claims that span those conditions.
4. Define readable behavioral anchors and versioned evidence criteria. Show insufficient evidence where a dimension is not supported; report supported observations at their actual scope.
5. Add information acquisition as a separate measured dimension when its tasks and interpretation are ready.

A compact public profile is the product surface being built now. Its coverage and strength of claims should grow with the supporting evidence; an exhaustive scientific study is not a prerequisite to displaying useful, bounded observations.
