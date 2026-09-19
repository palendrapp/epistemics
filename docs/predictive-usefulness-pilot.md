# Predictive usefulness pilot

Status: [provenance pilot 0.1](provenance-pilot-v1.md) implements a matched-case generator, frozen three-way design, public checkpoint views, behavioral fitting and synthetic validation. The [sequential MCP collector](provenance-collection.md) now supports real respondents with frozen metadata, immutable answers and restart history. Complete empirical prediction and intervention comparisons remain pending. This document defines the full product demonstration; the implementation specifications make their narrower current scope explicit.

## Product question

Can a profile predict how a particular agent configuration responds to copied versus independent evidence on unseen cases, and can using that prediction improve a subsequent assistance decision relative to its cost?

This demonstrates the proposed loop: **measure → predict → choose support → evaluate benefit → record scope**. It runs alongside registry and machine-consumer integration. A synthetic demonstration checks software and model recovery; real-agent observations are required for claims about an evaluated agent.

## Bounded first slice

Use several distinct agent configurations with repeated runs and multiple fictional company cases. Define a configuration by model/revision, prompt, tools, sampling settings and context/memory policy. Hold it fixed within a comparison. Complete the current core's real human/fresh-agent usability acceptance separately; the initial predictive pilot concerns agents and supplies no human population norms.

The implemented generator builds matched evidence sequences in which apparent corroboration comes either from independent observations or from copies of a common source. It crosses evidence direction and track-record strength, preserving substantive content within pairs. Provenance is explicit; uncertain provenance and corrections remain separate future contrasts. The first claim concerns the declared dependence contrast; it does not establish a general vulnerability to adversarial content.

Participants receive public task material, provenance cues and declared decision payoffs. Evaluator truth, seeds, future evidence and assignment remain private during a run. Preserve accepted answers, idempotent retries and attempted-run records. Collect reported probabilities/confidence and decisions; neither explanations nor reported probabilities provide direct access to internal beliefs.

## Separate development from the final test

| Case partition | Allowed use | Boundary |
| --- | --- | --- |
| Profile estimation | Fit a behavioral model for each configuration and quantify uncertainty | Do not use later test responses to revise the fitted profile |
| Policy development | Choose prediction models, intervention-selection rules, thresholds and budgets | Freeze these choices before opening the final test outcomes |
| Held-out evaluation | Score frozen predictions and compare assistance policies | New evidence structures with separate case groups; current graph/cover-story transfer stays within one binary-source model |

Use repeated runs to estimate variability, and declare which kinds of transfer the held-out cases test. Record all configuration attempts, failures and exclusions. Reusing final-test cases for revisions turns them into development data and requires a new held-out set.

Before final-test collection, freeze an evaluation manifest with case partitions, configurations, primary endpoints, comparator policies, sample/run budget, stopping rule, exclusions and minimum useful effect. Set numerical thresholds from a costed design and development-run variance estimates; do not choose them after seeing final-test results. Those quantities are open design decisions, not implied by this roadmap.

The current operator manifest fixes 72 episodes / 360 checkpoints per configuration at one replicate and supplies engineering tolerances for synthetic validation. It does not yet fix real-agent configurations, inference cost, an empirical minimum useful effect or an assistance policy. The policy-development partition is generated but reserved from the current fitter and prediction comparisons.

## Two separate tests

**Behavior prediction.** Predict the participant's next reported probability/update and specified decision on each test sequence. Compare the individualized model with a pooled model without subject-specific parameters, a persistence baseline and a model using only simple calibration/performance summaries. Use predictive scores appropriate to the response being predicted and report uncertainty across cases and repeated runs. An environment's normative reference can assess evidence use but is not itself a model of participant behavior.

**Decision benefit.** Use the frozen profile and policy to select assistance on new cases. Start with a provenance/evidence ledger; an independent reviewer is a separately costed extension. Compare the chosen policy with no assistance, generic review and the same assistance offered without profile selection. Where possible match resource budgets and also show the performance/cost frontier, so added computation is visible.

Evaluate forecasts against the task's outcome process using proper scores and decisions against declared payoffs. Keep those results distinct from accurately predicting the participant's responses: a model can predict a mistake well. Include regimes where changing less is appropriate, and report harmful effects as well as gains. Merely changing a fitted coefficient does not establish improvement.

For reviewer comparisons, distinguish a second actor from genuinely independent information. Record reviewer access to the first answer, shared sources and extra tools. Estimate whether the review adds useful evidence in this task family before recommending reviewer selection from profile differences.

## Deliverables and release criteria

- Versioned task/analysis manifest, recovery checks and auditable run accounting.
- Held-out prediction report with the simple baselines, uncertainty and relevant exceptions.
- Assistance-policy comparison with forecast/decision outcomes, completion, latency, inference/review costs and regressions.
- A scoped passport statement: what was predicted, on which cases/configuration, with what uncertainty, and whether the recommended support was tested.
- A machine policy example that refers to the validated result and returns review when its evidence requirements are unmet. Payment authorization remains a separate bounded decision.

Completion means the frozen comparisons are executed and reported, including null results. A positive product claim requires the predeclared improvement over prediction baselines and practically useful decision benefit after accounting for cost. If prediction works but assistance does not, release only the supported predictive claim. If support helps everyone equally, report general support value without claiming personalization. Inconclusive results retain provisional status.

The experiment does not identify a unique internal mechanism, certify future behavior in all environments, or authorize general autonomy. Further information-search tasks, historical replay, continuous observation and team allocation each need their own data and validation. See the [roadmap](mvp.md) and [intervention framework](cognitive-security.md).
