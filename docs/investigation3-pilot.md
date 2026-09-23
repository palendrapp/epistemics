# Investigation 0.3 repeatability and conditional prediction pilot

The 23 September 2026 pilot is a bounded test of the [revised initial-response models](company-investigation-v3.md), using one requested agent configuration. The intended result is a clearer account of which observed tendencies repeat, and which model predictions survive new cases. It cannot establish individualized superiority over population pooling or identify a unique internal cognitive mechanism.

## Frozen design

The private run manifest was written before the first respondent process started. It commits the evaluator and pilot implementation, configuration, three complete assignment schedules, presentation order, losses, baselines and resource cap. Commitments are local and operator-created, not independent preregistration or execution attestation.

- **Development:** 12 fresh-context cases used to fit the three initialization alternatives.
- **Repeat:** the same 12 underlying cases in a separately randomized presentation order and fresh contexts. Identifiers are new; public evidence, prices and pre-sampled outcomes match. Different query choices can reveal different evidence.
- **New:** 12 newly generated cases. Whole matched price pairs remain in their partition.

Each collection has nine unique company worlds, 48 checkpoints and 198 probability reports. The full plan is 36 episodes, 144 checkpoints and 594 reports. Development estimates use 162 later/prospective reports; the first 36 reports condition the initialization models. Repeated and new cases each supply 162 reports for prospective scoring.

Requested configuration: `gpt-6-astra`, medium reasoning, unspecified temperature, Codex CLI 0.155.1. Every case runs in a fresh ephemeral process, in an empty temporary directory, with project instructions and unrelated tools disabled. Only the assigned five evaluation MCP tools are enabled. This narrows access but does not constitute independent OS isolation or verification of the model revision. The requested alias is recorded as unverified.

The runner follows [OpenAI's non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode): explicit read-only sandbox, required MCP initialization, JSONL action/usage accounting and ephemeral sessions. It uses the existing local ChatGPT login; credentials and private reasoning are not copied into the pilot artifacts or repository.

The total collection budget is 45 minutes, one process at a time, at most ten minutes per episode and one attempt per episode. Failure or budget exhaustion stops the run and retains accepted answers, failed-attempt metadata and unknown usage. Incomplete cases must not be silently omitted. Provider usage is recorded; marginal dollar cost under the account is unknown.

## Predictions before responses

After development completes, three grid maximum-likelihood parameter pairs are frozen: working-prior, hard-report and noisy-report initialization. The fixed controls use working-prior initialization with joint inference or cut source feedback, both with full report adjustment. The persistence comparator retains the three initial reports, overriding a source/backlog event only after it is explicitly resolved; its unelicited segment-result forecast is 0.5 and its conditional growth forecasts equal initial growth.

For each repeat/new case, the MCP adapter saves all six models' predictions immediately after the first accepted answer and before any later answer. It saves one predictive object for each of the five query branches. Forecast files bind the initial answer, manifest, frozen model file, plan and exact public-trial sequence. Identical retries reuse the original commitment; missing forecasts cannot be created after later responses exist.

These are predictions of **responses conditional on the scripted public evidence**, including the eventual purchased result and review. The evaluator knows that script in advance. They are not forecasts of hidden company outcomes or predictions of which query the agent will choose. Unchosen results, forecasts and private world information are never sent to the respondent. The prediction function consumes public trials and the first report, not later answers or the latent truth.

All three models retain their declared observation assumptions. The noisy model integrates one persistent latent initial state per episode. Future responses cannot revise its initial mixture weights or its frozen parameter estimates.

## Scoring and adequacy diagnostics

Report both predictive-mean RMSE in probability points and the joint episode log score, normalized by the number of later/prospective reports. The mixture log score integrates over the entire episode. Different losses may prefer different models; no product model is selected automatically.

Before seeing later responses, draw 1,000 synthetic report sequences from each frozen episode/model/branch distribution. Save their error and log-score distributions. Their central 95% reference ranges and tail ranks provide a model-conditional check that accounts for initial-state uncertainty and declared reporting noise. The reference-distribution implementation was checked on a separate synthetic sample before real collection. These are not empirical confidence intervals for a person's or agent's cognitive traits, and multiple case-level departures are not corrected significance tests. The old eight-point RMSE screen is not used as this pilot's pass/fail rule.

For each partition report errors for all 12 cases, plus aggregate error and log score. An exploratory 2,000-draw bootstrap resamples the nine whole company worlds, preserving matched price pairs, to describe RMSE differences from the fixed joint observer. With nine groups and deliberately balanced offsets this is a limited uncertainty summary, not a population-level release test.

Repeatability uses the 72 main probability reports before the query result, choice agreement across 12 cases, and later main-report differences only for cases that selected the same branch. This prevents changes in available evidence being misreported as pure response instability. No human carryover or intervention effect is estimated.

This pilot has implementation/completion acceptance checks but **no empirical success threshold or validated-trait release**. All models, errors, failures and limitations remain visible. A later claim of predictive usefulness or improved delegation needs a separately frozen comparison appropriate to that claim.

## Commitments and reproducibility

Run directory, ignored by Git: `output/investigation3-pilot-20260923/`.

- Evaluator fingerprint: `02a4ee6924f28297b96d5d754ea2d75d8f3b6c00f7a148e23d787cd76dc2cd69`.
- Pilot fingerprint: `320268a9ea63f7b2d5781ae3706541a4949db9898e4b1a8234da03ebb9d21da8`.
- Precollection plan SHA-256: `4f8703ea0face6b0f159dd476c4655544a7037263573e8b38415b6cae8312ff1`.

The frozen source snapshot and dependency lockfiles are retained privately with all reports and prediction commitments. The base 0.3 evaluator remains unchanged. The pilot adapter separately fingerprints its transport and analysis, including the corrected 0.3 MCP display name; the frozen standalone adapter's stale 0.2 display name is not used in this run.

```sh
uv run python -m epistemics.investigation_pilot.runner output/NEW_PRIVATE_RUN
```

This command launches real model usage and refuses to overwrite a run. Default tests are offline. The full synthetic dry run completed 36 cases and audited all 24 prospective commitments before launching real collection.

A separate private 0.3 human collection is served on loopback. It uses the same task and response contract, with its continuous human context policy; no automated response is entered on the human's behalf. Human completion and interpretation review remain a separate acceptance item.
