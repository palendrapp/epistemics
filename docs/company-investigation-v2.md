# Diagnostic company investigation 0.2

Implemented 21 September 2026. This version addresses the coverage and interpretation gaps in the [first six-case agent run](investigation-acceptance-2026-09-20.md). It provides **12 cases / 48 checkpoints**, a human browser flow, an episode-bound MCP server, prospective research forecasts and a small conditional model family. It remains development measurement; it does not add validated traits to a passport.

The earlier `investigation` commands and 0.1 source remain unchanged. New work lives in `epistemics.investigation2` and uses the `investigation2` command. Battery, evaluator and analysis versions are separately `company-investigation/0.2.0`, `investigation-evaluator/0.2.0` and `investigation-analysis/0.2.0`. Manifest, trial and report schemas have `.v2` identifiers. Existing passport signatures and Solana records are unaffected.

## What the participant does

Each case retains four stages, now named and numbered visibly from one:

| Stage | Required response |
| --- | --- |
| Background | Forecast company growth, a source-audit event and a backlog event; make a provisional decision. |
| Evidence and research | Revise those forecasts; choose one research option or stop. In the six research cases, also forecast each check's result and growth conditional on either result. |
| Result and commitment | See only the selected result, a deterministic calculation, or no evidence after stopping. Commit the decision that earns the hypothetical payoff. |
| Transcription review | Receive the verified original value, preserve independent checks, and revise forecasts and a separate unpaid diagnostic decision. |

Every main forecast uses whole percentages, represented as 0–1 probabilities in the API. Endpoints are valid. Saved responses are immutable; identical retries return the original receipt. Optional explanations are short decision summaries, never scored as direct observations of internal mechanisms.

The full battery requests **144 main probabilities plus 54 prospective research probabilities: 198 probability reports**, 48 decisions and 12 research choices. Only the 12 committed decisions earn payoffs. This doubles the preceding development form's checkpoints; human completion time and actual model-provider cost remain unmeasured for 0.2.

## Guaranteed coverage and coherent sampling

**Six review cases** contain two offsets of −6, two of zero and two of +6 growth points. Offset signs are balanced and randomly assigned before collection; the case order is shuffled. Each independent review episode has a uniform marginal offset prior, replacing 0.1's prior that put two-thirds of its mass on zero. The source original is the published value minus the offset. All query results and outcomes are sampled before participation.

**Six research cases** form three matched low/high-price pairs, one each for source audit, backlog check and unaffected-cohort check. Transcription is already verified as zero and publicly marked as such. The generator retains a case only when the focused query's gross decision value under the joint reference is at least 0.025 payoff points. The low price is 0.005, the high price is 1.0, and the other empirical checks cost 1.0. Gain and loss are both one. Consequently the focused check is the reference's preferred low-price action, and stopping is preferred at the high price. The paired evidence, hidden world and pre-sampled branch outcomes are identical; choices can reveal different branches. A paid calculation remains available as a bounded-computation control, with zero new information to the exact reference.

Selection examines **only the public archives, analogues and operating estimate**. It cannot inspect realized query results, company outcomes or participant answers. The rejection rule and number of attempts are retained; a 10,000-attempt limit fails without saving a partial collection. Given the full operating record, selection adds no further likelihood: the selection event is a deterministic function of that record. This differs from selecting on an unrevealed outcome and then pretending the sample was random.

There are two limits to this argument. Before the operating record is visible, the archive-only reference is a working baseline, not a selection-adjusted prior for the selected research population. Starting reports are therefore conditioning variables and are excluded from the fitted report likelihood. Also, matched price pairs and balanced offset slots are not independent population samples. They remain together within a synthetic train/test partition, and a case's comparison is conditional on its supplied evidence and chosen branch.

Agents should receive a fresh process per case and only that case's history. The human flow serves the same stimuli, probabilities and state machine, but a person can remember earlier cases. Its manifest explicitly records `human_continuous_separate_company_cases`; agent manifests record independent contexts. Pair recognition, learning the offset schedule and other human carryover are not modeled by the current observer. Human results must not be interpreted as if memory was erased or as directly comparable population norms. The interface does not disclose pair identities, remaining offset counts or earlier case history.

## Interpretable model components

The joint state remains company fundamentals, implementation disruption, disruption strength, source bias/precision and transcription error. Source bias support expands to −6, −3, 0, 3 and 6 points, with SD 1.5 or 4. The **480 states** are 4 fundamentals × 2 disruption states × 2 relationship strengths × 10 source states × 3 offsets. The wider source support can represent more of the source-probe reports observed in the previous run.

The model retains the rounded measurement likelihood and conditional observation structure described in [0.1](company-investigation.md). Joint inference about sources and auxiliary explanations is inspired by [Gershman (2019)](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf); recovery and model criticism follow [Wilson and Collins (2019)](https://elifesciences.org/articles/49547). This is an authored adaptation, not a replication of either paper. The following projection, cut and report model are explicit design choices for this evaluator, not claims that the papers validate this instrument.

**Starting reports.** Let `q_archive` be the archive/analogue baseline and `f(z)` the three event probabilities in state `z`. We use a minimum-KL projection onto the participant's three initial reported marginals:

\[
q_0(z)\propto q_{archive}(z)\exp[\beta^\top f(z)],
\qquad E_{q_0}[f(z)]\approx r_0.
\]

At this stage the three relevant latent factors are independent, so each tilt can be solved separately by bisection. This is one declared way to condition on starting reports, not recovery of a uniquely identified internal prior. Finite-state support can prevent an exact match; each report exposes the starting-projection residual. The nuisance projection uses no later answers.

**Source feedback.** The joint observer allows evidence about the company to change the inferred source state. A modular alternative keeps the source marginal tied to its archive and any direct source audit, while retaining the company distribution conditional on that source:

\[
q_{cut}(s,x\mid D)=q_{source}(s\mid archive,audit)\,q_{joint}(x\mid s,D).
\]

This is a cut-feedback alternative, not ordinary Bayes under the same joint model. Direct audits still teach it about the source. A bounded interpolation supplies the conditional source-feedback parameter:

\[
q_{\rho,t}=\rho q_{joint,t}+(1-\rho)q_{cut,t},\qquad 0\leq\rho\leq1.
\]

**Reported adjustment.** A separate report-rate parameter controls movement toward those model predictions:

\[
\widehat r_t=(1-\alpha)\widehat r_{t-1}+\alpha E_{q_{\rho,t}}[f(z)],
\qquad 0<\alpha\leq1.
\]

An exactly resolved source/backlog event overrides smoothing and stays known. This is a descriptive observation model, not a complete RL learner or a claim about internal update speed. The joint likelihood incorporates the original operating measurement once. Review conditions its existing transcription state; it never adds an independent likelihood for the corrected value.

The four fixed controls are joint inference, separate-source inference, halfway report adjustment and a joint observer that ignores the review. A two-dimensional exploratory grid fits `rho` from 0 to 1 in steps of 0.1 and `alpha` from 0.2 to 1 in steps of 0.1. The working report model is the existing independent rounded logistic-normal model with SD 0.3. Fits condition on initial reports and the realized research branch; they do not fit a research-choice policy. A best-fit RMSE above eight probability points is explicitly marked inadequate. Eight points is a development diagnostic, not an empirically calibrated product threshold.

The model does not fit every plausible causal relationship, reporting gain, source intent or cognitive bias. The prospective conditional forecasts provide additional observable evidence about inferred relationships without pretending that two parameters fully phenotype a decision maker.

## Research choice from reported expectations

For each empirical check in a research case, the participant reports `P(yes)`, `P(growth success | yes)` and `P(growth success | no)` before submitting the research choice or seeing its result. This adds nine reports at that stage. The same source/backlog event probabilities also occur among the main probes, allowing a direct consistency check.

With `u(p) = max(0, (gain + loss)p − loss)`, the report-implied value is:

\[
\widehat V(q)=s_q u(p_{q,yes})+(1-s_q)u(p_{q,no})-u(p)-cost(q).
\]

We also retain the total-probability discrepancy `s_q p_yes + (1 − s_q) p_no − p` and repeated-event discrepancies. A 1.5-probability-point tolerance allows rounding. Inconsistent responses are accepted and reported; values are not silently repaired, normalized or clipped. The result is descriptive arithmetic from elicited expectations, not access to internal utility. Incoherence prevents confidently interpreting a purchase as an identified preference.

The matched pair report records choices and forecast differences across prices. Price-dependent forecasts and carryover can matter, so a single pair is not a stable cost-sensitivity estimate. Prospective questioning may itself change attention or decisions; this version does not yet estimate that elicitation effect or the value of an intervention.

## Validation and remaining evidence

Two development simulations use seeds 20260921 and 20260922, each with 24 training cases, 24 new cases and ten repetitions. Full matched pairs remain within a partition. Query branches are fixed by the public reference before synthetic reports are generated. This checks inference conditional on a branch, not recovery of a choice policy.

| Check | First seed | Second seed |
| --- | ---: | ---: |
| Correct fixed-model identification | 40/40 | 40/40 |
| Mean absolute coupling error | 0.0925 | 0.0725 |
| Mean absolute report-rate error | 0.0150 | 0.0125 |
| New-world mean report RMSE, probability points | 6.032 | 5.989 |
| Generating coupling within conditional grid interval | 39/40 | 39/40 |
| Generating report rate within conditional grid interval | 32/40 | 34/40 |

Generating parameters include `(rho, alpha) = (0.75, 0.45)`, which are off the fitted grid. The report-rate interval counts show why the grid intervals must **not** be advertised as calibrated 95% uncertainty for continuous parameters. These simulations assume the model family and independent reporting noise; they do not establish recovery in real agents, human repeatability or cross-domain transfer. Random reports fail the eight-point absolute-fit diagnostic. Successful discrimination with all probes does not establish their incremental value over growth-only reports; that ablation remains pending.

Repository checks passed: **230 Python tests**, including actual stdio MCP transport, a 48-checkpoint browser HTTP flow, retry/advance idempotence, prospective-probability conversion and privacy guards; plus TypeScript type/lint checks and **33 tests**. Local HTTP tests required localhost listener permission. RPC remains mocked; this work makes no live Solana transaction or payment. A browser walkthrough used explicitly synthetic responses and visually checked the evidence, probability fields, query expectations and completion. It is not a human acceptance result.

The final validation artifacts remain private in `output/investigation2-final-validation-20260921.json` and `output/investigation2-final-validation-20260922.json`. Both bind implementation fingerprint `b1901b04d1bf94b1eddb9318dda199de8e7669c6cd3900745ea601ba170f30be`; their exact-byte SHA-256 hashes are `045131b3f8deede604fef7bb2f712c766dac0de841f74f4bfa47c20c6ecd1ce1` and `4eefe680624d9fb402eace4a8389c355c588357f944ef781f1707a5741f2f4cb`. The completed synthetic CLI example in `output/investigation2-final-demo-20260921/` exported all 12 report hashes and fitted the expected joint/full-adjustment grid point. None of these synthetic artifacts is an actual agent or human evaluation.

The next empirical step is a bounded fresh-agent usability run of this version, recording comprehension, completion time, actual usage and the fit/residuals. Follow with repeated configurations on new cases and an actual human acceptance pass. Any further model development must be evaluated on separately frozen cases before predictive passport claims. One targeted-support comparison comes after a repeatable difficulty is identified; no assistance benefit is currently established.

## Run locally

Install with `uv sync --locked` and `pnpm install --frozen-lockfile`. The following commands are offline and do not call a model provider:

```sh
uv run epistemics investigation2 demo --directory output/investigation2-demo
uv run epistemics investigation2 validate-synthetic --worlds 24 --repetitions 10 --output output/investigation2-validation.json
```

For actual participation, save an operator-owned participant descriptor privately. Agents can use the structure in [the participant example](../examples/investigation-participant.json), with the actual configuration digest. For a human, use `{"kind":"human","subject_id":"private:participant-01"}`. No wallet or model identity is required for a human.

```sh
uv run epistemics investigation2 create --directory output/investigation2-person --participant output/person.json
uv run epistemics investigation2 serve --directory output/investigation2-person
```

Open the private localhost link printed by the server. It grants access to this collection; the capability is exchanged from the URL fragment for an HttpOnly cookie and removed from the visible URL. The page starts with instructions and acknowledgment, has blank probability fields, preserves earlier evidence within a case, and offers a next-company button after completion. Server restarts restore the first unfinished case and print a new link. `--assignment ASSIGNMENT_ID` restricts the browser to one case. Human memory and assistance must still be considered when interpreting the results.

For agents, bind one fresh respondent to each operator-selected assignment using [the v2 MCP configuration](../examples/mcp-investigation2.json) or the JSON-lines bridge:

```sh
uv run epistemics investigation2 status --directory output/investigation2-agent
uv run epistemics investigation2 client --directory output/investigation2-agent --assignment ASSIGNMENT_ID
uv run epistemics investigation2 export --directory output/investigation2-agent
```

The five MCP tools match the original investigation, with the additional expectation object described in [the respondent protocol](../examples/investigation2-respondent-protocol.md). There are no participant-side seed, mode, pair, price or outcome selectors. Calibration requires a separately created collection with `--mode calibration`.

Export is unavailable until all 12 cases finish. It writes exact-byte report hashes, per-case JSON, readable `summary.md`, and `analysis.json` with source hashes, matched choices and the conditional fit. Existing files must agree byte-for-byte; they are never overwritten. All raw artifacts are private and ignored by Git. No passport, signature or on-chain record is issued by this module. Local capabilities and permissions do not provide OS isolation from an agent sharing the evaluator's account.
