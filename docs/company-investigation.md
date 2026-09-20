# Company investigation: attribution and active research

Implemented development module, 20 September 2026. Battery `company-investigation/0.1.0`, evaluator `investigation-evaluator/0.1.0`, analysis `investigation-analysis/0.1.0`. This is the first implementation following the [cognitive-modeling review](cognitive-modeling-review-2026-09-20.md).

The question is whether an unchanged company forecast reflects a source explanation, a business explanation, a reporting tendency or failure to incorporate a correction. The participant also chooses which evidence to buy. This is a bounded investigation with competing conditional observers; it does not yet establish a general cognitive phenotype.

Joint attribution is inspired by [Gershman (2019)](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf); simulation and model/parameter recovery follow the methodological guidance of [Wilson and Collins (2019)](https://elifesciences.org/articles/49547). This authored company task is an adaptation, not a replication of either paper.

## Public task

Each episode has four checkpoints. Context stays continuous within an episode and starts fresh for the next company case.

| Checkpoint | Information and action |
| --- | --- |
| 0. Background | Two resolved source reports and two sector analogues. Forecast the company outcome and two auxiliary events. |
| 1. Operating report | A noisy renewal-supported growth estimate and a broker headline explicitly derived from it. Forecast again, then choose one research option. |
| 2. Research result | Reveal only the purchased result, or a deterministic calculation, or no new evidence after stopping. Commit an invest/hold decision. |
| 3. Transcription review | Reveal a verified offset in the original report, including zero-offset controls. Replace the original value and its derivatives, preserve independent evidence, and elicit revisions. |

The three probability reports concern next-year growth above 12%, whether a selected historical source report understates its audited value by more than two percentage points, and whether the company's backlog reading exceeds 22. Probabilities use increments of 0.01; endpoints are allowed. When a purchase resolves one of the exact auxiliary events, it stays known at later checkpoints. Optional explanations are retained but are not scored as evidence of an internal mechanism.

Research options are a source audit, a backlog check, an unaffected customer-cohort check, an arithmetic projection using existing data, and stopping. Relative prices, overall cost scale and decision payoffs vary before collection. Sources and measurements share uncertain company/source states; query results are not independent evidence about every variable.

The checkpoint-2 decision earns the declared hypothetical payoff minus the research cost, paid once whether investing or holding. The later correction is an unpaid diagnostic review. This keeps the research reference's one-query-then-act horizon explicit; it does not pretend that an agent should buy information while ignoring a future payoff-relevant disclosure. The calculation has no information value to the exact observer but may help a bounded respondent derive an implication.

**Discovery** provides examples and qualitative relationships without the reference likelihoods. **Calibration** additionally discloses the generative assumptions. Both are supported by the same state machine; mode is operator-bound. The hypotheses are scaffolded in both conditions. This module does not test unrestricted hypothesis generation or Ullman-style theory search. The reference's probabilities and decision values are conditional on its assumptions, especially in discovery mode.

## Joint model and diagnostic alternatives

The new observer reuses the existing discovery world's growth grid, source states and exact rounded-normal measurement likelihood. It projects that model onto one recurring source: fundamentals \(F\), disruption \(A\), disruption relationship \(K\), source bias/precision \((b,\sigma)\), plus a transcription offset \(C\). There are **288 joint states**: 4 × 2 × 2 × 6 × 3.

\[
y=\operatorname{round}_{0.1}[F-d(K)A+b+\epsilon]+C,
\qquad \epsilon\sim N(0,\sigma^2),
\]

where \(d(K)\) is 2 or 8 growth points, and \(C\in\{-6,0,6\}\) with prior probabilities \((1/6,2/3,1/6)\). Fundamentals take values 6, 10, 14 or 18; source bias is −3, 0 or 3 and source SD is 1.5 or 4. The remaining latent priors are independent uniform distributions. The outcome is \(F+N(0,2^2)>12\). See the calibration protocol for the other observation distributions.

Resolved source errors and sector analogues constrain the joint state. All possible query results are sampled once before collection. A selected result updates that state; unselected results never enter the observer. A correction conditions the same measurement on the verified \(C\), rather than adding another likelihood for the corrected value. A numerical test compares the corrected model's marginal predictions with the existing 6,912-state discovery enumerator.

The initial fixed candidates are:

- Joint inference over company, source, disruption and transcription.
- A source fixed at zero bias and SD 4.
- A fixed weak disruption relationship.
- A descriptive report-smoothing control that moves halfway toward each joint forecast; directly resolved probes remain known.
- A joint observer that fails to incorporate the transcription correction.

These are candidate explanations of reported behavior, not an exhaustive process model set. In particular, the smoothing control is not a claim to have implemented a complete RL learner. Local hypothesis search, source intent, dynamic noise/change learning, memory and metacognition remain separate extensions.

For parameter recovery, resolved source-history log likelihoods receive a weight \(\lambda\). Nonunit weights describe generalized-Bayes weighting; they are not normalized observation models. The simulation fits \(\lambda\) on a 0–2 grid in steps of 0.05 with a uniform grid prior, using generating values both on and off the grid. Report gain is fixed at one to avoid introducing an unconstrained evidence/report-gain tradeoff. Real episode exports compare fixed candidates; they do not issue a fitted stable-trait vector.

Reports follow a logistic-normal working model with latent SD 0.3 and 0.01 rounding bins. Predicted exact endpoints map to latent logits of 10⁻⁶ and 1−10⁻⁶. The observed endpoints remain valid bin events. Reports are not silently clipped or discarded. The independent error assumption is explicit and receives a correlated-error stress check; it is not known to describe real respondents.

Research values enumerate both outcomes of each binary query:

\[
V(q)=\sum_o P(o\mid D,q)\max_a E[U(a,Z)\mid D,q,o]
-\max_a E[U(a,Z)\mid D]-c(q).
\]

Stopping has value zero. The observer conditions only on visible evidence. Its value calculation cannot consult an unchosen query's pre-sampled result or the future correction. The chosen research action is recorded, but no free research-policy parameter is fitted.

## What the synthetic checks actually established

Two final development runs used seeds 20260920 and 20260921, each with 24 randomly sampled training worlds, 24 new worlds, five fixed candidates and 20 repetitions per generating candidate. Research branches were balanced and preassigned for this discrimination check. They are not simulated choices from a recovered policy. All worlds remain in their preassigned partition; seeds were not selected for large model differences.

| Check | First seed | Second seed |
| --- | ---: | ---: |
| Correct fixed-candidate identification | 100/100 | 100/100 |
| Mean report RMSE on new worlds | 6.026 probability points | 5.819 probability points |
| Mean absolute archive-weight recovery error | 0.0326 | 0.0275 |
| Generating archive weight inside conditional grid interval | 130/140 | 128/140 |
| Worlds with a matched-forecast attribution contrast | 23/24 | 20/24 |
| Correct attribution from auxiliary probes across matched worlds | 40/40 | 40/40 |

The fixed-candidate check is deliberately limited: **final growth forecasts alone also separated all five coarse candidates in both runs**. That success does not establish incremental benefit from the new probes.

The more relevant diagnostic adds a source-bias prior tilt \(\gamma(-b/3)\) or a disruption prior tilt \(\delta A\). For each training world, set \(\gamma=1.25\) and find a \(\delta\in[-6,6]\) that matches its checkpoint-1 growth forecast, without looking at simulated answers. These two explanations have matching growth probabilities to within 10⁻⁶ probability points, but different source-audit and backlog predictions. The additional probes distinguished them under the simulated report model. One and four worlds, respectively, could not be matched and are explicitly retained in the counts. This selected diagnostic subset is not a population result or proof that real respondents use either prior.

Uniformly random reports fail the eight-point absolute-fit check (best errors 37.09 and 37.64 points). With unmodeled episode-correlated response offsets, the best of the five candidates is still named "joint", despite absolute errors of 10.34 and 16.24 points. This demonstrates why a winner among candidates must not be presented as an adequate explanation automatically.

Research coverage remains uneven. Across the first run's 48 worlds, the reference chose source audit 0 times, operations check 2, segment check 17 and stop 29; the second gave 1, 1, 13 and 33. A broader 384-world development check gave 2, 26, 110 and 246. Do not claim reliable individual source-audit or research-policy parameters from six episodes. Relative-price changes make the options available for development; improving diagnostic purchase opportunities remains an empirical design question. Exact-observer calculation purchases have no positive net value by construction, which does not establish their uselessness to bounded participants.

These are synthetic checks, including conditional recovery and an exploratory matched-forecast contrast. They do not establish nominal interval coverage, real-agent repeatability, human usability, general transfer or intervention benefit. The two final runs followed development of the contrasts; they are not a preregistered empirical holdout. Full artifacts stay in ignored private output directories.

Repository verification passed: Ruff checks, 212 Python tests including a real stdio MCP round trip, and TypeScript type/lint checks with 33 tests. Existing localhost HTTP tests required running with local-listener permission. Solana/consumer tests retain their mocked RPC boundary; this implementation increment made no live-network call or payment. The six-episode end-to-end example is explicitly synthetic; the subsequent actual agent run is recorded separately below.

## First actual agent collection

A [six-case fresh-agent development run](investigation-acceptance-2026-09-20.md) completed all 24 checkpoints in 244.73 seconds after two preserved zero-answer launcher failures. Every decision agreed with the reported probability and payoff. Source-probe reports stayed fixed within each case; one backlog result moved the growth forecast much more than the joint reference. All candidate aggregate RMSEs exceeded the eight-point synthetic diagnostic, so no cognitive label or stable parameter vector was issued.

All six pre-sampled transcription offsets were zero, leaving actual evidence retraction untested. Research choice agreed with the conditional reference in 3/6 cases, but discovery respondents did not receive that reference's likelihoods. The results note records exact resource usage, uncertainty, wording feedback and a version-reviewed next design with guaranteed correction coverage and stronger source/company contrasts. Human acceptance and real-agent repeatability remain pending.

## Collection, artifacts and versions

The default development collection has six fresh episodes, **24 checkpoints**. Each private manifest freezes the participant, mode, schedule, costs, versions and implementation fingerprint. Participant descriptors support agents and pseudonymous humans; this module currently has an MCP/JSON interface, not an addition to the existing human browser form.

MCP exposes only `describe_battery`, `get_trial`, `get_history`, `submit_answer` and `finish_evaluation`. There are no participant seed, model, price or branch-outcome selectors. Only the submitted research choice controls the revealed branch. Transactional answers are immutable, identical retries are idempotent, and accepted public history supports resume. Completion returns a receipt; outcomes and analysis remain private until the operator exports after **all** planned episodes finish. Unknown or unfinished assignments cannot disappear from export.

Exports produce exact-byte JSON report hashes and a readable `summary.md` with probability trajectories, correction revisions, research values and candidate fits. Private outcomes are included only in operator reports. Issuer, subject/configuration and execution assurance remain distinct: this module provides operator-asserted metadata and does not issue a passport or Solana record.

This new experimental behavior has its own battery, evaluator and analysis versions, implementation fingerprint and recovery checks. The existing company, discovery-study, shared-core and provenance protocols remain at their previous versions. Existing report schemas and signature domains are unchanged. The additional schemas are `investigation.v1.json`, `investigation-trial.v1.json` and `investigation-report.v1.json`, generated by the standard schema command. Changes to this module's behavior require its own version/recovery review; active manifests refuse a changed implementation.

## Running it

Bootstrap with `uv sync --locked` and `pnpm install --frozen-lockfile`. All commands below are local; validation and demos make no model-provider, RPC or payment calls.

```sh
uv run epistemics investigation validate-synthetic --output output/investigation-validation.json
uv run epistemics investigation demo --directory output/investigation-demo
```

For an actual respondent, replace every placeholder in `examples/investigation-participant.json`, including the actual configuration digest, and save it privately. A human descriptor can be `{"kind":"human","subject_id":"private:participant-01"}`.

```sh
uv run epistemics investigation create --directory output/investigation-agent --participant output/actual-participant.json
uv run epistemics investigation status --directory output/investigation-agent
uv run epistemics investigation client --directory output/investigation-agent --assignment ASSIGNMENT_ID
uv run epistemics investigation export --directory output/investigation-agent
```

Use one fresh respondent context per assignment. The [respondent protocol](../examples/investigation-respondent-protocol.md) documents the JSON-lines bridge; [the MCP configuration example](../examples/mcp-investigation.json) launches the bound stdio server directly. Calibration requires a separately created collection with `--mode calibration`. Do not expose private manifests, code, outcomes or earlier real responses to a discovery respondent. Local file permissions do not isolate an agent that shares the evaluator's OS account.

The first small agent development/usability run is complete. Next revise and validate diagnostic coverage and stage wording, then collect a bounded new-case usability/repeatability pass and add a human interface/acceptance pass. Freeze an independent validation plan before making predictive passport claims. The [results note](investigation-acceptance-2026-09-20.md#next-development-slice) specifies the design gaps; this module does not justify automatically repeating the earlier 432-episode benchmark.
