# Auxiliary diagnostic: fresh-agent acceptance

On 23 September 2026, one requested `gpt-6-astra` configuration completed the new [auxiliary diagnostic](auxiliary-diagnostic.md) in eight separate contexts: **8 cases, 32 checkpoints and 80 probability reports in 5 minutes 33 seconds**. Every submitted answer was accepted on its first attempt. The agent distinguished the associated and independent archives, carried its conditional forecasts through to later reports, made no change on the no-information repeat and fully incorporated the definitive audits.

This is a successful, small acceptance run. It shows no selective propagation or sluggish report adjustment **under these explicit diagnostic controls**. It does not establish a general cognitive trait, uniquely identify an internal model or resolve the poor new-case fit in the richer company investigation.

## Observations

All differences below are absolute probability points. These are consistency checks on reported probabilities, not population calibration estimates or direct observations of internal beliefs.

| Check | Cases or reports | Result |
| --- | --- | --- |
| Initial marginal agrees with the mixture of reported conditionals | 8 cases | Mean and maximum gap 0 points |
| Auxiliary report after the growth audit equals the earlier conditional for that outcome | 8 cases | Mean and maximum gap 0 points |
| No new information produces no report change | 8 cases | Mean and maximum change 0 points |
| Definitive auxiliary audit receives its resolved probability, 0 or 1 | 8 cases | Mean and maximum error 0 points |
| Growth stays consistent with its definitive audit | 24 reports | 24/24 exact; maximum error 0 points |

The four matched pairs also show the intended relationship contrast. In both backlog pairs, the associated archive elicited auxiliary probabilities of 0.8 conditional on growth and 0.2 conditional on no growth, a +60-point spread. In both source-understatement pairs, the corresponding probabilities were 0.2 and 0.8, a −60-point spread. All four independent cases elicited 0.5 for both conditionals. Initial auxiliary marginals were 0.5 throughout, matching this diagnostic model's baseline assumption.

The association signs are confounded with target. This run cannot estimate negativity, source-label or framing sensitivity. The archive contains empirical counts without disclosed population likelihoods; its structure and the subsequent definitive audits nonetheless make this a much more constrained task than the company investigation.

## Model interpretation

All four declared families—association-only, selective propagation, report smoothing and the full model—meet at the same fitted special case:

| Parameter | Selected grid value | Task-conditional description |
| --- | --- | --- |
| Association scale β | 1.0 | Reported conditionals match the archive proportions |
| Propagation fraction ρ | 1.0 | Later auxiliary reports fully reflect the relevant earlier conditional |
| Report adjustment α | 1.0 | Reports reach the model's updated value immediately |

Each fit uses 40 observations, has 0-point fitted RMSE and a rounded-report log likelihood of −80.9635. The log likelihood need not be zero when point predictions match reports: it reflects probability mass assigned to rounding bins under the fixed noise model. Each family has one maximizing grid point, but **the families tie**. This is not successful discrimination between four internal mechanisms. The reported structural-identifiability flag is conditional on the candidate family; no calibrated parameter uncertainty or held-out predictive comparison was obtained here. Both `model_parameters_are_passport_traits` and `empirical_predictive_validation` remain false.

The [earlier prospective investigation](investigation3-results-2026-09-23.md) showed stable source impressions and relatively small backlog changes despite larger company revisions. The present result demonstrates that a fresh agent configuration can propagate explicitly elicited relationships consistently. It therefore weakens a blanket interpretation of the earlier pattern as an inability to update related judgments. It does **not** establish why those earlier reports stayed stable: the evidence, scaffolding, elicitation and execution configuration differ, and the richer task still has inadequate model fit.

A useful next measurement contrast would retain matched underlying relationships while varying how explicitly those relationships are presented and how uncertain the new evidence is. It should separate what relationship the respondent expects from how it updates through that relationship. Define the observable claim and budget first, review the version and test recovery before collecting new cases. This acceptance result alone does not warrant a broad collection or a new passport trait.

## Execution and resource accounting

The requested model was `gpt-6-astra` with medium reasoning effort, using the existing signed-in account and Codex CLI 0.155.1. The immutable model revision was not independently verified. Each case ran in a fresh ephemeral process and temporary working directory, with user/project configuration excluded, a read-only sandbox, shell/web/other tools disabled and only the five assigned MCP tools available. Each context continued through its own four checkpoints. Execution verification remains **operator asserted**, not an independent sandbox or model attestation. The setup follows the CLI's [non-interactive execution documentation](https://learn.chatgpt.com/docs/non-interactive-mode).

The private run plan committed to the configuration, collection manifest and implementation before the first answer. It allowed one attempt per case, five minutes per attempt and twenty minutes overall. Collection ran from **21:08:31.982 to 21:14:04.747 UTC**; monotonic elapsed time was 332.737 seconds. All eight distinct recorded context IDs completed, with no exclusions, retries, failed MCP calls or rejected submissions. There were 96 MCP calls: 8 descriptions, 8 history reads, 40 trial reads, 32 submissions and 8 completions.

| Resource | Recorded usage |
| --- | ---: |
| Input tokens, including cached input | 1,177,190 |
| Cached input, already included above | 994,560 |
| Noncached input | 182,630 |
| Output tokens | 4,234 |
| Total processed input + output | 1,181,424 |
| Attempts with unknown usage | 0 |

Marginal dollar cost is unknown under the signed-in account. This is actual acceptance-run usage, not the proposed paid evaluation price.

A precollection setup attempt failed because a private script named `operator.py` shadowed Python's standard library. It was renamed before starting the successful run. That setup attempt made no respondent calls and accepted no answers; its failure record is retained separately. Each successful process also recorded the CLI's warning that the feature used to skip host skill discovery was under development. No task or evaluator change was made during collection.

## Usability and integrity

Seven contexts reported no confusing wording or significant interface friction. One noted that “understated … by at least 5%” does not specify the percentage's denominator. Clarify that event definition in a future version; the frozen task and prepared human session were left unchanged. Actual human completion and human carryover remain untested.

The post-run audit rederived the analysis exactly from the immutable report, verified all planned assignments and accepted-answer counts, checked configuration/manifest/report hashes and confirmed the implementation fingerprint remained unchanged. Raw prompts, responses, evaluator databases and execution artifacts remain private and ignored by Git. Publishing their hashes records byte commitments; it does not make the underlying data publicly reproducible or independently timestamped.

| Artifact | SHA-256 |
| --- | --- |
| Implementation fingerprint | `3e5584987011181d97894a2af47a0a15fc967a1e0f127b5551424075055b29e1` |
| Precollection run manifest | `17baf774fb610fefab912659a6abb5891de11005963bc5e9740fc86d893a5e35` |
| Configuration | `f0af29ac071d142e32f6b0f466a195d58b332cf11bca3d8ec4f6a4afc8318552` |
| Execution record | `90bb5b5d90101f6c103ffc1b89a5531ef3ea52c49f206b8b92bf7b51e892b2fd` |
| Collection manifest | `0d45d7136af06b097c341eb600394c3bbc623a862b8e0e71ccc5bffdfe455356` |
| Exported report | `faa63c381cf4c54af5384b1e8f005798ec81c0a72237c1eb967530a890d5f0e5` |

Battery, evaluator and analysis versions remain `auxiliary-diagnostic/0.1.0`, `auxiliary-diagnostic-evaluator/0.1.0` and `auxiliary-diagnostic-analysis/0.1.0`. The existing implementation checks covered 259 Python tests and 37 TypeScript tests before collection. This increment adds results and roadmap documentation only; it changes no experimental behavior, schema or signed artifact contract.
