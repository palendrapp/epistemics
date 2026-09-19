# Matched discovery studies and parameter profiles

Evaluator 0.4.0. Study battery `company-discovery-study/0.4.0`; analysis `discovery-profile/0.4.0`. This is a separate experiment from the unchanged ten-checkpoint `company-discovery/0.3.0` protocol. Existing report v1/v2/v3 contracts remain supported.

## What is implemented

The study pipeline freezes a matched schedule and analysis plan, collects real responses through MCP, exports immutable episode reports, fits a joint behavioral model on training worlds, evaluates predictions on held-out worlds, and produces a JSON/Markdown profile. The same fitter runs synthetic recovery and model-misspecification checks. Synthetic results never count as agent responses.

The first fitted parameters are source-profile impressions, weighting of resolved source histories, two business-prior terms, and response wording. Negative-evidence weighting, confirmation, memory, free reporting gain, risk preferences and active research are not fitted. They require additional experimental contrasts and recovery validation before being added. This is one authored business mechanism with different numerical worlds; it is not validation on new business mechanisms or a general cognitive diagnosis.

## Frozen experiment

Each world has eight matched assignments: skeptical/optimistic source-profile swap × short/long archives × growth/failure wording. Every assignment receives a fresh respondent context; context remains continuous for its eleven checkpoints. Replicates repeat the whole episode in another fresh context. All assignments for one world, including repeats, remain in one partition. The first two thirds of independently sampled worlds train the model; the remaining worlds are held out. Presentation order is randomized before collection.

The new first checkpoint shows source profiles without archives. Checkpoint 1 reveals the archives; checkpoints 2–10 deliver the previous discovery case's nine documents. Source probes at 0, 1 and 7 separate the profile-only assessment from archive learning and later reweighting. Company forecasts, ordered growth quantiles and decisions are elicited at every checkpoint; conditional and extraction probes retain their original document timing.

Archives vary in length, and source mean error and noise are independently drawn from the existing finite generator. They are not independently factorially assigned within every world. Shared/independent provenance is balanced across worlds and fixed within a world's source/history/wording contrasts. That factor does not identify a provenance coefficient in this release.

Seeds, partitions, assignments and private state are evaluator-side. Participants cannot select a seed or condition. Finishing an episode returns only a completion receipt, not its outcome or model analysis. Export and fitting require every planned assignment to finish; incomplete cases are not silently discarded. An interrupted respondent can resume with its accepted public trial/answer history restored, and accepted answers are never elicited again.

The default design is **12 worlds × 8 assignments × 2 replicates = 192 episodes, 2,112 checkpoints**, including eight training worlds and four held-out worlds. This is a starting design, not a power claim. Compare recovery at alternative sizes before committing to an expensive real study.

## Joint inference model

The observer retains the previous finite state space: fundamentals F, disruption A, relationship K, each source's bias b and precision state σ, and provenance G. It uses only public trials. Sources remain dependent through the uncertain company state. Repeated observations from a source share uncertainty about its bias/noise.

For source s, profile tone T_s is +1 for skeptical, −1 for optimistic, and 0 for neutral:

\[
\log\frac{P(\sigma_s=1.5)}{P(\sigma_s=4)}=\alpha T_s.
\]

This prior enters once per source. The source's bias prior remains uniform. Its resolved archive contributes

\[
\lambda\sum_{r\in\mathcal A_{s,t}}
\log P(y_{sr}-x_{sr}\mid b_s,\sigma_s).
\]

λ=1 processes each resolved error once; λ=0 ignores resolved archive evidence. It does not turn off source learning from current company measurements. Nonunit λ is a descriptive generalized-Bayes weighting rule, not a claim about a normalized sampling likelihood.

Business priors have two nuisance parameters:

\[
\log\frac{P(K=\mathrm{strong})}{P(K=\mathrm{weak})}=\kappa,
\qquad P(F)\propto\exp[\eta(F-12)/6].
\]

Sector analogues, company evidence and provenance then update the entire joint distribution. Bias and noise are distinct source properties. The broker calculation contributes no additional measurement; a later source audit can change the interpretation of earlier company evidence. Conditional forecasts are computed by conditioning the joint state on A=0, rather than deleting inconvenient observations.

The implementation eliminates source states conditionally before integrating the 32 company/provenance states. Tests compare it against the original 6,912-state enumerator. This changes computational cost, not the baseline posterior.

The report mapping for the common growth event is

\[
E[\operatorname{logit}\widehat p_t]=\operatorname{logit}m_t+\beta W_t,
\]

where W is +1 for growth wording and −1 for complementary wording. Report gain is fixed at one. Source and conditional probes do not receive this wording shift. This is a modeling convention; wording could affect deliberation as well as expression.

## Fitting and uncertainty

The observation vector contains growth probabilities, requested source and conditional probabilities, and all three growth quantiles. Probabilities are clipped at 10⁻⁶ and mapped to logits; quantiles remain in growth percentage points. A fixed correlated Gaussian **working likelihood** has logit SD 0.35, quantile SD 1.5, a shared episode component of 0.15, and an additional same-checkpoint component of 0.20. These assumptions are frozen in the manifest. This is not an exact censored/rounded-report likelihood; endpoint counts are reported.

The coarse candidate comparisons use finite grids with explicit priors: α on −2..2 in steps of 1; λ on 0..2 in steps of .5; κ on −2..2 in steps of 1; η on {−1,0,1}. Prior weights are proportional to normal densities with means (0,1,0,0) and SDs (1.25,.75,1.5,1). β has a continuous N(0,.75²) prior and is integrated analytically conditional on each grid point. Grids and parameter bounds are in the manifest and may be changed **before** creating a study. The full model is then refined continuously within these bounds, initialized from the best training grid point. A bounded Gauss–Newton optimizer uses all training channels and the same priors. Its local curvature supplies approximate Laplace intervals and parameter correlations. Optimization traces and convergence are retained; unconverged or boundary solutions cannot be marked resolved.

Six candidates distinguish fixed assumptions, flexible business priors, archive learning, source impressions, response wording and their joint extension. Training marginal likelihoods use equal model priors. Held-out predictive density integrates the frozen training posterior; held-out observations never tune parameters, priors, noise, grids or model selection. The candidate evidence comparisons remain explicitly coarse-grid comparisons. Parameter estimates in the profile come from the continuously refined full model, with its separate linearized held-out predictive density. The model-ranking table does not claim exact continuous-model Bayes factors.

The profile includes approximate conditional 95% posterior intervals, parameter correlations, boundary diagnostics, practical effects, separate whole-world bootstrap intervals, absolute held-out errors by channel, extraction errors, and probability/decision agreement. The continuous uncertainty check uses a linearized MAP refit after resampling whole training worlds, preserving all matched assignments/repeats. Exact coarse-grid bootstrap intervals and coarse-grid parameter summaries are retained separately for comparison. Displayed trajectories are plug-in predictions at the continuous MAP, not posterior means of probabilities. The additional held-out predictive density integrates a local linear/Gaussian parameter approximation across episodes.

**The continuous refinement avoids reporting a collapsed coarse-grid interval as exact knowledge of a bias magnitude.** Off-grid generating parameters are included in recovery to test this distinction. Local Gaussian intervals can still fail for multimodal, boundary, rounded-response or misspecified models. Nominal 95% coverage is not established by a small recovery study. Review the optimization trace, coarse-grid alternatives, cluster intervals, absolute fit and coverage counts together.

`resolved_under_model` requires enough training worlds, no excessive boundary mass, a sufficiently narrow interval, a stable world bootstrap when requested, acceptable absolute held-out error, and mean numerical-extraction error at most 0.1 percentage points. It does not establish a nonzero effect, independent replication, or psychometric validity. `unidentified` is emitted when these gates fail. An adequate fit cannot rule out an unmodeled explanation.

Source-profile and response-wording matched differences are also reported without fitting the observer. Source-profile contrasts use Beacon's pre-archive accuracy prediction; archive-length contrasts use its first post-archive prediction; wording contrasts use the final company probability mapped to the common event. Intervals resample worlds. The sign of an archive-length effect depends on the records and is not intrinsically a bias. Forecast outcome scores are separate and count distinct worlds as independent outcomes.

The interpretation of auxiliary explanations is inspired by [Gershman (2019)](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf), not a replication. Simulation, parameter recovery, competing-model checks and out-of-sample prediction follow the methodological motivation of [Wilson and Collins (2019)](https://elifesciences.org/articles/49547).

## Running the pipeline

Bootstrap with `uv sync --locked` and `pnpm install --frozen-lockfile`.

An offline synthetic demonstration exercises storage, export and the real-report fitting path:

```sh
uv run epistemics-study simulate output/study-demo --worlds 4 --replicates 1
uv run epistemics-study fit output/study-demo
uv run epistemics-study recovery output/study-recovery --worlds 12 --repetitions 3
```

Recovery retains the schedule, response vectors, generating parameters, posterior intervals, coverage counts, model comparisons, and failures. It checks in-family recovery, predictive adequacy, a business-prior alternative without spurious source/wording effects, and rejection of one deliberately incompatible predictive family. Off-grid behavior is reported separately. Recovery gates cover parameter error, candidate discrimination, absolute fit, source/wording misattribution under a business-prior alternative, off-grid recovery, and rejection of the deliberately incompatible family. Small recovery runs do not establish nominal interval coverage. These commands create new study directories; they never replace an existing manifest.

For real respondents, write the actual `AgentDescriptor` configuration to an ignored file; see `examples/study-agent.json`. Then:

```sh
uv run epistemics-study create --agent output/actual-agent.json --directory output/agent-study --worlds 12 --replicates 2
uv run epistemics-study status output/agent-study
uv run epistemics-study run output/agent-study --respondent output/respondent-command.json --max-episodes 1
# Repeat collection, or increase max-episodes for a deliberate larger run.
uv run epistemics-study export output/agent-study
uv run epistemics-study fit output/agent-study
```

`respondent-command.json` contains an argv list and optional environment variable names:

```json
{"command":["/absolute/path/to/respondent-program"],"pass_environment":["MODEL_API_KEY"]}
```

The command starts afresh per episode, receives public JSONL messages on stdin, and emits `{"answer": <DiscoveryAnswer>}` lines on stdout. The initial `start` message includes the protocol, answer schema and any accepted public history for recovery. `trial` messages request an answer; `receipt` messages acknowledge immutable acceptance; `complete` ends the episode. Log diagnostics to stderr, not stdout. There is no shell expansion. Secrets are read from explicitly allowed environment names, never written into the manifest. The command bytes are bound on first collection; a changed command requires another study. Record model revision, prompt/tool/configuration identity and decoding settings accurately in the descriptor and preserve the corresponding configuration artifact. The runner cannot independently attest these declarations.

A provider-neutral adapter is intentional: no specific model SDK, account or credential is required by the evaluator. A real adapter must maintain message history within its process and invoke the chosen model. `examples/study-respondent-template.py` documents the adapter contract; its answer function is deliberately unimplemented, not a hidden synthetic replacement for a real model. No real-model requests occur in default tests.

For an existing fresh agent that can use tools directly, an operator can assign one pending episode and launch:

```sh
uv run epistemics-study client output/agent-study ASSIGNMENT_ID
```

This prints actual MCP tool schemas and forwards JSON lines such as `{"tool":"get_trial","arguments":{}}`. The agent calls `submit_answer` and `finish_evaluation`, then closes the transport with `{"close":true}`. Use this on an untouched assignment; the automated runner restores accepted history for interrupted episodes.

Alternatively expose `epistemics-study-mcp` with evaluator-side `EPISTEMICS_STUDY` and `EPISTEMICS_ASSIGNMENT`. This server exposes only the bound assignment, without seed/condition selectors or access to other participants. It does not change the original `epistemics-mcp` server.

## Artifacts and trust boundaries

- `manifest.json` and its exact-byte hash freeze the private schedule, descriptor and analysis plan.
- `responses.sqlite3` stores transactional accepted answers and completed episodes.
- `attempts.jsonl` retains started, failed and completed external-respondent attempts; failures do not erase accepted answers.
- `reports/*.json` and `report-hashes.json` bind exact exported bytes. Imports check assignments, public material replay, configuration, probe contracts and hashes.
- `profile.json`, its exact-byte hash, and `profile.md` contain the fitted profile and prediction checks.
- `recovery.json` and its hash identify the separate synthetic validation artifact; `recovery-runs.jsonl` checkpoints each completed fit so an interrupted validation retains its attempts.

All should stay under ignored `output/` or `.epistemics/`. Operator manifests and exported reports contain private seeds/truth and must never be supplied to active respondents. Private file permissions and fresh processes do not create OS isolation; use a separate evaluator host/container for stronger execution assurances. The MCP tools themselves withhold private fields throughout the study.

Study schemas are generated by `uv run epistemics schema` alongside the original report schemas. Study artifacts are not yet accepted by the Solana record CLI; no new signature domain, schema acceptance, wallet operation or publication is introduced here. Preserve issuer, subject, configuration and execution claims separately.
