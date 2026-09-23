# Company investigation 0.3: initial reports and portable evidence

Implemented 23 September 2026. This revision addresses wording and initial-response assumptions identified in the [0.2 acceptance run](investigation2-acceptance-2026-09-21.md). It retains the 12 cases, 48 checkpoints, 198 probability reports and matched price/correction design. The [passport adapter](investigation-passport.md) exposes the resulting observations to people and machine consumers.

The implementation lives in `epistemics.investigation3`. Battery, evaluator and analysis versions advance to `company-investigation/0.3.0`, `investigation-evaluator/0.3.0` and `investigation-analysis/0.3.0`; manifest, trial and report schemas have `.v3` identifiers. The 0.1 and 0.2 implementations and completed reports remain unchanged. The [36-episode real-agent pilot](investigation3-results-2026-09-23.md) is now complete; actual human completion remains pending.

## Participant-facing changes

- A source probe now explicitly concerns one additional historical report, separate from the displayed archive.
- Transcription verification at entry and a completed review are separate public fields. The final stage says that the review is complete, including when it discovers an actual error. This avoids a stale “not yet checked” statement without falsely changing the initial prior.
- MCP instructions explicitly use 0–1 probabilities in increments of 0.01; the human form asks for whole percentages. Both feed the same accepted-answer contract.

Generation, query costs, branch outcomes, payoffs and research selection remain the [0.2 design](company-investigation-v2.md). These wording changes still warrant a separate battery version. Human carryover remains different from an agent's fresh context per case.

## Three declared initial-response models

Let \(z\) be the existing 480-state world, \(q_A(z)\) the archive/analogue working prior, and \(f(z)\) the three queried event probabilities. First reports \(r_0\) are observations; they need not be a noiseless description of a persistent internal prior.

1. **Working prior:** use \(q_A\), without using the initial reports to set persistent state.
2. **Hard report:** retain the previous minimum-KL projection matching the three reported marginals as closely as the state support allows.
3. **Noisy report:** condition a distribution over possible initial states on the reports.

For the noisy model, define 27 states by independent log-linear tilts:

\[
q_u(z)=\frac{q_A(z)\exp[u^\top f(z)]}{\sum_{z'}q_A(z')\exp[u^\top f(z')]},
\qquad u_j\in\{-\log 3,0,+\log 3\}.
\]

Each coordinate has prior masses \((1/4,1/2,1/4)\). Using the existing rounded logistic-normal observation model \(L_\sigma\), with endpoint censoring and initial logit SD fixed at 0.8:

\[
\pi_u(r_0)\propto w_u\prod_{j=1}^{3}L_{0.8}(r_{0j}\mid E_{q_u}f_j).
\]

These are evaluator assumptions, not a fitted population distribution. The finite support and fixed noise levels limit their scope. The archive-only baseline is still not selection-adjusted before the operating record is visible.

The existing source-feedback parameter \(\rho\) interpolates joint and cut-source inference; \(\alpha\) controls smoothing of the predicted reports. Exactly resolved events override smoothing. Neither coefficient is labeled as an internal cognitive mechanism. For later main reports and prospective forecasts \(r_{1:}\), integrate one initial state over the entire episode:

\[
p(r_{1:}\mid r_0,D,\rho,\alpha)
=\sum_u\pi_u(r_0)\prod_k L_{0.3}(r_k\mid\widehat r_k(u,D,\rho,\alpha)).
\]

The sum is outside the product: one persistent initial state generates an episode. Summing separately for each answer would describe a different model. Predictive means use only \(\pi_u(r_0)\), never weights updated using future answers. Fits condition on the supplied evidence and chosen research branch; they do not fit a research-choice policy.

The grid remains 11 source-feedback values and nine response-rate values. All three initialization alternatives are reported. Noisy initialization is the development default, not an empirically selected winner. Conditional grid intervals are not calibrated trait uncertainty. This is an authored extension to the [previous mathematical model](company-investigation-v2.md#interpretable-model-components), informed by the [literature review](cognitive-modeling-review-2026-09-20.md), not a replication of a published instrument.

## Synthetic checks

Two runs use seeds 20260923 and 20260924, each with 24 fitting cases, 24 separate-world test cases, four parameter settings and four repetitions per initialization. Whole matched pairs stay within a partition. Branches are fixed by the public reference. Each run contains 48 generated datasets, with all three initialization alternatives fitted to each.

Predeclared implementation gates are coupling MAE ≤0.25 and response-rate MAE ≤0.15 for every generating initialization. Both runs pass. The initialization likelihood comparison recovers the generating family in 16/16 datasets per family per seed; this is model-family recovery under the declared generators.

| Generating initialization | Coupling MAE, seed 20260923 / 20260924 | Response-rate MAE | Mean new-case RMSE, points |
| --- | ---: | ---: | ---: |
| Working prior | 0.106 / 0.131 | 0.013 / 0.013 | 6.24 / 6.18 |
| Hard report | 0.063 / 0.112 | 0.013 / 0.013 | 5.80 / 5.83 |
| Noisy report | 0.131 / 0.112 | 0.013 / 0.019 | 9.49 / 9.59 |

New-case error and initialization confusion are reported diagnostics, not additional gates or a product-model selection rule. These errors come from different generating processes and are not a ranking on one common dataset. The noisy generator's irreducible initial uncertainty raises predictive-mean error even under the correct model. The inherited eight-point absolute-RMSE status is an uncalibrated development screen; it is not a calibrated goodness-of-fit test for the mixture model. We retain that limitation visibly rather than tuning a threshold to the observed agent.

Implementation fingerprint: `02a4ee6924f28297b96d5d754ea2d75d8f3b6c00f7a148e23d787cd76dc2cd69`. Private validation JSON hashes:

- Seed 20260923: `7c821732b59e3349b2fe00d9028b2c513fd9ec2fa3d960c1608232b282695881`.
- Seed 20260924: `371795885886ec5197d4e723f4bc712391cdda22b9b1687673f24c18225f7ced`.

This does not establish empirical prediction, interval coverage, research-policy recovery, human validity or intervention benefit.

## Exploratory reanalysis of the existing agent run

The unchanged 0.2 observations were compared separately using 0.3 analysis. All fits use 162 later/prospective reports and exclude the 36 initial reports from their fitted likelihood. This is post-hoc development data, not a new evaluation or held-out validation.

| Initialization | RMSE, points | Conditional log likelihood | Best coupling / report rate |
| --- | ---: | ---: | ---: |
| Working prior | 7.50 | −600.84 | 0.0 / 1.0 |
| Hard report | 11.86 | −695.50 | 0.0 / 1.0 |
| Noisy report | 8.46 | −537.32 | 0.0 / 1.0 |

The noisy model improves on hard conditioning and has the strongest likelihood; the working prior has the lowest predictive-mean error. Different loss functions give different rankings. The noisy model also permits much wider coupling uncertainty than hard conditioning. These are reasons to keep initial-report uncertainty explicit and compare frozen predictions on new cases. They do not establish that this agent has a zero-coupling trait or needs a particular intervention.

The original-run passport retains its original 0.2 model diagnostics. The reanalysis is a separate artifact binding the exact source collection hash `98a0d7c541c1cca4d8a1adc72b010e01e8bf4a7ac57c8dba4999ef43e9c112c4`.

## Operator commands

```sh
uv run epistemics investigation3 create --directory output/investigation3 --participant participant.json
EPISTEMICS_INVESTIGATION3=output/investigation3 EPISTEMICS_ASSIGNMENT=CASE_ID \
  uv run python -m epistemics.investigation3.mcp_server
uv run epistemics investigation3 serve --directory output/investigation3-human --port 8768
uv run epistemics investigation3 export --directory output/investigation3
uv run epistemics investigation3 validate-synthetic --seed 20260923 --worlds 24 --repetitions 4 --output output/recovery.json
uv run epistemics investigation3 compare-initialization --report output/source.json --output output/comparison.json
```

Create the human collection with a human participant descriptor before serving it. The agent tool interface remains case-bound; agents must not receive the collection directory or evaluator-side truth. The source artifact used by `compare-initialization` is built with the [passport bundling command](investigation-passport.md).
