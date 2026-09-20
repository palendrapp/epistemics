# Fresh-agent company investigation — 20 September 2026

Six fresh GPT-6 Astra processes completed the discovery investigation through its public MCP interface: **six cases, 24 checkpoints and 72 probability reports**. The corrected collection took **4 minutes 5 seconds**. Every submission was accepted on its first attempt. This establishes a working agent collection path and supplies development observations; it does not establish a stable cognitive phenotype or personalized predictive value.

The strongest observations are consistent probability-to-action mapping, source estimates that stayed fixed within each case, and a large response to a backlog result in one case. The current candidate observers do not adequately explain the aggregate reports. All six sampled transcription offsets were zero, leaving actual evidence retraction untested.

## Collection and scope

The requested configuration was `gpt-6-astra`, medium reasoning, through Codex CLI 0.155.1 using the existing signed-in account. Each case began in a new ephemeral process with a temporary working directory and empty public history. Context continued across its four checkpoints. User configuration, project instructions, shell, browsing, plugins, memory and subagents were disabled; only the five episode MCP tools were permitted. The launcher uses the official [non-interactive CLI interface](https://learn.chatgpt.com/docs/non-interactive-mode). The runtime's code-mode host was required to route these tools.

The respondent received the public discovery protocol and examples, without reference likelihoods, repository context, this conversation or evaluator feedback. Seeds and unselected outcomes remained evaluator-side. Execution metadata is operator-asserted: the requested alias is not an independently verified immutable model revision, and this setup is not independent OS-level execution attestation.

The frozen task used battery `company-investigation/0.1.0`, evaluator `investigation-evaluator/0.1.0` and analysis `investigation-analysis/0.1.0`. No evaluator source, task wording, accepted answer or case schedule changed during collection. Full cases remain in the private artifacts. The comparisons below were computed after collection and are exploratory, not a held-out prediction test. Six fresh contexts provide six different cases under one requested configuration, not repetitions of the same cases.

## What the responses show

**Decisions followed the elicited probabilities.** All 24 invest/hold answers matched the declared linear payoff rule, including the change from a one-half to a one-third investment threshold when upside doubled. Four checks of already resolved backlog probabilities were correct: both purchased results were reported as zero and retained at the next checkpoint. These are observations of answer coherence, not access to internal beliefs.

**Source judgments differed across cases but did not change within them.** The initial probabilities of a historical source report understating its audit were 80%, 12%, 50%, 60%, 20% and 60%. Each stayed exactly constant through all four checkpoints. Growth forecasts changed in every case, so this was selective persistence rather than universal failure to update. The joint reference's later source revisions were generally small; no respondent bought the direct source audit. This pattern motivates testing separate versus joint source/company inference, but does not by itself establish anchoring or an inability to learn about sources. Initial source-probe RMSE against the reference was 12.10 points, a larger discrepancy than most later reference updates.

**One backlog result had a much larger effect than the reference predicts.** In case 3, learning that backlog did not exceed 22 reduced the growth forecast from **64% to 43%** and changed invest to hold. The joint reference moved from **70.5% to 68.2%**. This is a useful diagnostic difference in the inferred business relationship. The respondent's brief explanation linked the absence of backlog to less support for disruption depressing the reported estimate; that explanation is retained as a decision summary, not evidence of its internal computation. Discovery leaves priors and likelihoods unspecified, so the difference cannot simply be labeled irrational updating. Two initial growth reports were 35%, whereas the reference starts at 50%; some mismatch exists before the operating report arrives.

**Research choices showed variation, with limited diagnostic coverage.** The agent bought two unaffected-cohort checks and two backlog checks, and stopped twice. It bought neither a source audit nor a calculation. In both stop cases all three probabilities stayed unchanged when no evidence arrived. These observations do not establish a general stopping or duplicate-evidence trait.

| Case | Chosen research | Cost | Best action under joint reference | Reference net value of chosen action | Reference regret |
| --- | --- | ---: | --- | ---: | ---: |
| 1 | Unaffected cohort | 0.060 | Unaffected cohort | +0.1399 | 0.0000 |
| 2 | Backlog | 0.150 | Source audit | −0.1500 | 0.1671 |
| 3 | Backlog | 0.008 | Stop | −0.0080 | 0.0080 |
| 4 | Unaffected cohort | 0.010 | Stop | −0.0036 | 0.0036 |
| 5 | Stop | 0.000 | Stop | 0.0000 | 0.0000 |
| 6 | Stop | 0.000 | Stop | 0.0000 | 0.0000 |

Values are hypothetical payoff points for the committed decision. Choices agreed with the conditional reference in 3/6 cases; mean conditional regret was 0.0298 points, mostly from case 2. Zero gross decision value does not mean a check contains no information. Alternative subjective beliefs can make the same check decision-relevant. No purchase exceeded the perfect-information bound implied by the respondent's own reported probability, `min(p × gain, (1 − p) × loss)`. We therefore cannot infer disregard for cost merely from disagreement with the reference policy.

**The transcription review tested verification, not retraction of an actual error.** All six offsets drawn before collection were zero. Reports changed by +3, −2, −2, +2, +8 and −10 probability points; the joint reference changed by +7.0, −14.1, +8.0, +1.9, +9.4 and −4.4. Confirmation of zero error removes uncertainty about a possible offset, so an update is not automatically double counting. No case demonstrated handling of a changed numerical value. Retain this coverage gap rather than replacing cases after observing it.

## How well do the cognitive candidates explain it?

Aggregate RMSE weights all 72 reports equally. The log likelihood sums the existing rounded logistic-normal report likelihood across those reports; its independent-error assumption is a working model, not established for this respondent. These are fixed candidates, with no fitted individual parameter vector.

| Fixed observer | All-report RMSE, probability points | Growth RMSE | Source-probe RMSE | Backlog RMSE | Report log likelihood |
| --- | ---: | ---: | ---: | ---: | ---: |
| Joint inference | 11.01 | 11.19 | 13.16 | 8.07 | −299.99 |
| Fixed unbiased source | 18.29 | 11.25 | 28.74 | 7.18 | −475.01 |
| Fixed weak disruption link | 10.36 | 11.41 | 13.14 | 4.36 | −307.69 |
| Halfway report smoothing | 10.38 | 11.97 | 12.78 | 4.13 | −284.23 |
| Ignore transcription review | 10.63 | 11.00 | 13.01 | 6.98 | −289.52 |

The weak-link candidate has the lowest raw RMSE; the smoothing control has the highest report likelihood. Every candidate exceeds the eight-point absolute-fit diagnostic used in synthetic development. Their ranking changes with the scoring rule, and the best raw error is still 10.36 points. **Do not issue a “weak causal learner,” “slow updater” or “ignores corrections” label from this result.** A candidate's name is not an identified mechanism. In particular, the smoothing control is not a fitted RL learner, and zero-offset reviews cannot establish resistance to retraction.

For completeness, the six committed forecasts had mean outcome Brier loss **0.3381**, and the committed decisions earned **+0.772 net hypothetical points** after research costs. These use six unique outcomes, not 24 independent observations. They are realized performance summaries from a tiny development set, not estimates of calibration, investment skill or general decision quality.

## Usability, launch recovery and resources

All six final feedback messages identified the zero-based checkpoint numbering as minor friction: “checkpoint 1” means the second submission. One also flagged the phrase “all earlier decisions are provisional” alongside the checkpoint-2 commitment rule. That respondent stated that it treated checkpoint 2 as committed and checkpoint 3 as diagnostic. Both wording issues belong in the next version review. There has still been no actual human acceptance run of this module.

Two **zero-answer launcher failures** preceded the successful collection:

1. The initial event handler stopped the process on an error item after 0.93 seconds without preserving its detail. Usage is unknown.
2. A diagnostic attempt retained error items and revealed missing tool transport: the launcher had disabled `code_mode_host`. It exited after 11.17 seconds without answers, using 25,206 input tokens (12,416 cached) and 174 output tokens.

The corrected launcher enabled the required host, bound a new configuration and manifest with the identical six assignments, and preserved both failed attempts and the original zero-answer collection. These are setup failures, not respondent task failures. A separate warning about the experimental host-skill-discovery setting appeared in successful runs; it was retained and did not prevent completion.

- Corrected collection: 244.73 seconds, from 22:17:51 to 22:21:55 UTC. Individual processes took 34.86–45.21 seconds. This excludes setup failures and operator repair time.
- Six distinct fresh process/thread IDs; six protocol reads, six empty-history reads, 30 trial reads, 24 submissions and six finalizations. No failed episode tool calls or rejected/retried answers.
- Successful collection: **911,924 input tokens**, including **789,632 cached input**, plus **4,203 output tokens**.
- Known total including the diagnostic failed launch: **937,130 input**, including **802,048 cached**, plus **4,377 output**: **941,507 processed tokens**. Cached input is a subset, not an additional count. One earlier attempt has unknown usage.
- Marginal dollar cost is unknown under the signed-in account. These totals are separate from earlier core acceptance and provenance benchmark resources.

## Next development slice

1. **Guarantee diagnostic coverage in a new version.** Include positive, negative and zero transcription offsets, and cases where source auditing can change the decision. Document the sampling/conditioning rule and make the reference observer consistent with it; do not silently select worlds and retain an incompatible prior. Validate recovery before collecting responses.
2. **Separate inferred relationships from response habits.** Compare a joint observer with a model that updates source and company estimates separately. Account for elicited starting probabilities and test whether auxiliary probes distinguish the explanations when growth predictions match. The present observations motivate these candidates; they are not evidence that either is the agent's mechanism.
3. **Explain research choices using the respondent's expectations.** On a bounded diagnostic subset, elicit expected query outcomes and conditional growth forecasts before purchase. This can distinguish valuing a different business relationship from failing to use the declared costs. Review burden and possible elicitation effects before extending the full battery.
4. **Fix the two wording issues and test the human path.** Use named stages with explicit committed versus diagnostic decisions. Run a small new-case usability/repeatability check after versioning, then freeze a costed validation plan for any intended passport claim. Do not automatically launch another large benchmark.

The immediate product finding is that the richer interface collects useful behavioral contrasts quickly, while the current task coverage and observer family still constrain interpretation. Existing passport claims, Solana records and the earlier null personalization result remain unchanged.

## Artifact commitments and verification

Private stimuli, prompts, evaluator state, responses and execution records remain ignored under `output/investigation-agent-20260920/`. The active collection is `ready-collection/`; earlier attempts remain alongside it. The readable export is `ready-collection/summary.md`. No passport was issued or on-chain record written.

| Artifact | SHA-256 |
| --- | --- |
| Evaluator implementation fingerprint | `7d6417b7ec8e3b7c832e06b3a23828614eec3dd93176d14da829889eedd781dd` |
| Corrected configuration | `3d0ed66f62194610a429ca763c747187c1e938424df84c7a4338c7952ce6b259` |
| Corrected collection manifest | `fa68da0d1079e2c77778336405374d4024b190a36333bf4683682ce6ff3c2490` |
| Configuration amendment | `dc886ca969d35b0b03c1e60c94f897ce3248ce42bfe8847e65a3a7e882066564` |
| Execution record | `51d8ee4e22d0b0d8469f633921d984f9c2c1338ec5c3f5200151ecffce29d35a` |
| Report-hash index | `54b9d7df066076da4073818a21d680520293bd77f7af9ab99c42269a9d4cbf0c` |
| Readable report | `edc8c7c33bd6e8cedb5b4081c29cd330198ccf1a4bf1094b87b14601d94b532b` |
| Post-collection analysis script | `5f19a9a07bb9740096db0e8a7009e0eb82c7b6cc5293b4e0903de7d06c9f6799` |
| Post-collection analysis output | `b9eff2f50ec121c8cbe6a76eec68bbcaf06f47d55a7761a5b9af3b8a2e322127` |

Every exported report's exact bytes matched its hash and frozen assignment/manifest binding. The implementation fingerprint still matched after analysis. These are local operator commitments, not independent preregistration or proof of execution. Only documentation changed for this results increment; the preceding implementation's test coverage is recorded in the [module documentation](company-investigation.md).
