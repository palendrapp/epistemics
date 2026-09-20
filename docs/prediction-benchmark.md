# Frozen multi-configuration prediction benchmark

`provenance-benchmark/0.1.0` turns the [provenance collector](provenance-collection.md) into a costed, staged comparison. Its immediate question is whether a configuration-specific profile predicts later reported probabilities better than simpler predictors. Assistance efficacy is a separate next increment; this benchmark does not issue a validated passport or establish intervention benefit.

The [20 September development run and frozen budget](prediction-budget-2026-09-20.md) provide actual token/latency measurements and include failed setup attempts. Full-plan profile collection [stopped after 55 completed episodes and one failed attempt](prediction-profile-stop-2026-09-20.md); no prediction lock or final empirical result exists.

## Planned comparison

The initial configuration set is GPT-5.6 Luna, GPT-5.6 Terra and GPT-6 Astra, each at medium reasoning effort. All use the same respondent prompt, public MCP tools and context policy. These are requested provider aliases, not independently verified immutable model revisions. The frozen configuration includes the CLI version, prompt, requested settings and disabled tools. Unknown sampling/provider settings remain unknown.

Two repetitions of the complete factor grid produce the following budget:

| Partition | Episodes per configuration | Checkpoints per configuration | Use |
| --- | ---: | ---: | --- |
| Profile | 48 | 192 | Fit parameters and comparators |
| Policy | 48 | 240 | Reserved development observations, excluded from prediction fitting/scoring |
| Held-out | 48 | 288 | Score locked predictions |
| Total, one configuration | 144 | 720 | Fresh context per episode |
| Total, three configurations | **432** | **2,160** | Sequential, round-robin configurations within each case |

Matched twins remain together in one partition. Every configuration sees the same factor grid and assignments. Two repetitions provide repeated task observations; they do not establish population norms or broad domain transfer. Company labels and dependency structures vary only within the existing binary-source task family.

## Cost before final collection

A separate `development_costing` benchmark predeclares one longest-graph matched pair per configuration: six episodes / 36 checkpoints. Its entire design is retired from empirical evaluation. Costing and prediction runs cannot be relabeled into one another.

The Codex runner uses the signed-in ChatGPT account, with no API key or purchase. It captures provider-reported input tokens, cached input tokens and output tokens, plus episode duration. Processed tokens are `input_tokens + output_tokens`; cached input is already part of input and is not added twice. These counts are not a direct conversion to account quota percentages or dollars. Marginal dollar cost is explicitly unknown.

The cost command projects the full run using observed mean episode usage and duration. Suggested resource ceilings use twice the observed maximum per episode. With two observations per configuration these are planning allowances, not confidence bounds, billing quotes or guaranteed upper bounds. Longest-graph costing deliberately does not assume shorter episodes will cost the same, though the projection applies its observed rate across the plan.

The manifest freezes attempt, processed-token and cumulative episode-time budgets, and each invocation also limits its number of episodes. Admission is checked **between** episodes; one episode may overshoot a token/time ceiling. A per-episode timeout limits wall-clock exposure but cannot promise a token maximum or prove the provider stopped billing immediately. Unknown usage is retained as unknown and blocks further admission. Failures stop collection and remain visible; there are no automatic inference retries or hidden exclusions. A failed benchmark must be inspected and retired or handled by a future explicit recovery policy; current analysis requires every planned episode and complete execution/usage records.

## Freeze predictions before final cases

The benchmark MCP endpoint exposes only the collector's four public tools. It additionally checks the benchmark stage on startup and every call. Profile collection comes first. The `lock` command requires every configuration's profile cases to finish and rejects a design if any later episode has already been opened. It saves exact prediction-lock bytes in the benchmark database.

The lock contains:

- Each configuration's four effective reporting weights, with matched-group bootstrap intervals.
- A pooled four-weight fit over all configurations' profile cases, using one common coefficient vector.
- A two-parameter reference-calibration comparator: intercept and slope on the evaluator reference log odds.
- An individual three-parameter comparator that treats all reports as evidence: intercept, prior weight and one gain on originals plus copies.
- Static predictions for every held-out checkpoint from those models and the predeclared source-inference sensitivity model.
- A fixed persistence rule: predict the last accepted probability in the same episode, or the supplied prior before any answer.

The reference-calibration comparator measures a simple conditional mapping to reported responses, not empirical forecast calibration against realized outcomes. Persistence is evaluated causally from preceding held-out responses; it never uses the response currently being predicted. All other held-out predictions are fixed before held-out responses exist. Policy observations are collected only after locking, and held-out access additionally requires the policy partition to finish. No policy responses enter prediction fits or scores in this version.

This is an operator-controlled stage boundary and source/data drift check. A trusted operator with arbitrary filesystem/database access can bypass or rewrite it. It is not cryptographic proof of preregistration or independent execution verification.

## Endpoints and decision rule

The primary endpoint is probability RMSE over **post-evidence checkpoints only**, averaged equally across configurations. Prior-only answers remain in the profile fit and descriptive data but cannot inflate the main prediction score. Report each configuration separately as well as the cohort average.

The provisional product criterion requires:

1. At least **0.01 absolute RMSE improvement** over each of pooled behavior, reference calibration, all-reports one-gain and persistence, on the cohort average.
2. A positive lower bound of the paired 95% bootstrap interval for each improvement.
3. Individualized held-out RMSE no greater than **0.05 in every configuration**.
4. Every planned case completed, no imputation/exclusions, and complete execution and usage accounting.

These are pragmatic pilot targets: a one-percentage-point reduction in probability error and a five-point absolute adequacy ceiling. They are fixed before final data, not derived from the earlier smoke-test results, and are **not power validated**. Passing remains conditional on this task and model set. Identical profiles that provide no gain over pooling should yield `criteria_not_met`, even if all predictions are accurate. Null results are retained rather than relabeled as product validation.

For comparative uncertainty, 2,000 paired bootstrap draws resample whole held-out matched groups with both twins, every checkpoint and the same selected groups across configurations. Intervals describe case reweighting conditional on these fixed configurations and fitted predictors. They do not include training-fit uncertainty or establish population coverage. Profile intervals use up to 1,000 matched-group bootstrap draws separately. The fit, draw counts, seed and criteria are frozen before final cases.

Probability MAE, threshold-based decision agreement and terminal expected task scores are secondary. Decisions are predicted as `act` above 0.5 and `defer` otherwise. Terminal Brier/regret calculations remain conditional expectations under the evaluator's source model, not realized outcomes, investment returns or an assistance benefit.

## Source-inference sensitivity

The primary model retains the existing Beta(1,1) source-accuracy reference. A predeclared sensitivity fit uses raw source success rates instead. Both fit only profile cases and predict the same held-out checkpoints. The sensitivity result does not replace the primary model after seeing scores and does not count as a passing primary comparison.

This addresses the [smoke-test observation](provenance-smoke-2026-09-20.md) that responses were compatible with raw-frequency source inference. A larger effective evidence weight under the smoothed reference need not imply generalized overreaction. Neither parameterization uniquely identifies an internal cognitive mechanism.

## Commands

Use the [development specification](../examples/benchmark-development.json), a fresh private design and the installed Codex CLI:

```sh
uv run epistemics predictive create --output output/cost-design
uv run epistemics benchmark create --design output/cost-design --spec examples/benchmark-development.json --output output/cost-run
uv run epistemics benchmark run --benchmark output/cost-run --split heldout --max-episodes 6
uv run epistemics benchmark cost --benchmark output/cost-run --replicates 2 --output output/cost-estimate.json
```

Before a full pilot, set `purpose` to `prediction_pilot`, use a new design with `--replicates 2`, replace the development resource ceilings with the costed full budget, and record the estimate artifact/hash in `cost_basis`. Creating the benchmark freezes those choices and the participant bindings. Then collect in stages:

```sh
uv run epistemics benchmark run --benchmark PRIVATE_BENCHMARK --split profile --max-episodes 144
uv run epistemics benchmark lock --benchmark PRIVATE_BENCHMARK --output output/prediction-lock.json
uv run epistemics benchmark run --benchmark PRIVATE_BENCHMARK --split policy --max-episodes 144
uv run epistemics benchmark run --benchmark PRIVATE_BENCHMARK --split heldout --max-episodes 144
uv run epistemics benchmark analyze --benchmark PRIVATE_BENCHMARK --output output/prediction-results.json
uv run epistemics validate output/prediction-results.json
```

Use smaller `--max-episodes` values to collect in bounded batches. Reinvoking skips completed episodes and retains accepted answers. A failed attempt blocks further admission; this version deliberately does not silently retry it. Status reports all planned assignments and retained execution attempts.

The runner starts a fresh ephemeral Codex process in a temporary directory, ignores user configuration, requests read-only sandboxing, disables shell, browser, plugins, memory and subagent tools, and supplies only the assigned MCP server. It explicitly authorizes the four local evaluation tools through per-tool approval settings; unrelated tool approval requests remain disabled. It records unexpected tool actions as failures. This narrows the execution surface but is not independent attestation of the provider's model, hidden instructions or OS isolation. Agent final messages and failure diagnostics are private; private reasoning events are not retained by the runner. Raw artifacts stay outside Git.

The implementation uses locally verified Codex CLI behavior and the official [non-interactive JSON event interface](https://developers.openai.com/codex/noninteractive) and [configuration settings](https://developers.openai.com/codex/config-reference). The recorded CLI version is checked before collection.

## Version and test boundary

This adds a separate benchmark/analysis version and three schemas: `prediction-benchmark-spec.v1`, `prediction-benchmark.v1` and `prediction-benchmark-report.v1`. The underlying stimuli, payoffs, response fields and conditional feature model remain provenance pilot 0.1. Existing core/passport/signature contracts and previous collection artifacts are unchanged. Benchmark source fingerprints additionally bind the task implementation and runner.

Offline tests cover full synthetic parameter recovery and scoring, a null personalization result, phase gating, premature exposure detection, budget/unknown-cost stops, real MCP collection from a synthetic process, retained failures, source/configuration drift and schema snapshots. These tests do not count as empirical predictive validity. An assistance comparison still needs its own frozen intervention protocol, comparators, resource accounting and held-out outcome analysis.
