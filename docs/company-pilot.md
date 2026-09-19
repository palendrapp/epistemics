# Company dossier pilot: implemented protocol

Evaluator version: 0.2.0. Battery: company-dossier/0.2.0. Report: epistemics.report.v2. The original belief-battery/0.1.0 and its v1 report remain available.

This is the first implementation of the [proposal](sequential-company-evaluation-proposal.md) and a deliberately constrained subset of the [mathematical model family](sequential-company-models.md). It is one authored scenario family with six generated companies, not six independently validated domains. It is a controlled inference condition with disclosed calibration and structured claims; realistic discovery and natural-language extraction are later conditions.

Discovery is the intended main assay. Keep this disclosed-model battery as a calibration and integration check; the proposed next experiment is specified in [Discovery inference](discovery-inference-proposal.md).

## Episode and document design

Each company has a fixed target horizon and four binary states: growth H, margin M, temporary implementation disruption A and management source validity V. The respondent sees all prior/calibration assumptions but not sampled states, outcomes or future evidence. H, A and V start independent; M depends on H and A.

| H | A | P(M=1) | P(positive operating reading) |
| ---: | ---: | ---: | ---: |
| 0 | 0 | 0.35 | 0.20 |
| 0 | 1 | 0.15 | 0.10 |
| 1 | 0 | 0.75 | 0.85 |
| 1 | 1 | 0.40 | 0.30 |

The six (P(H), P(A), P(V)) priors are (0.3,0.15,0.6), (0.7,0.15,0.9), (0.3,0.5,0.9), (0.7,0.5,0.6), (0.5,0.3,0.75), (0.5,0.3,0.75). States are sampled from these priors before observations. Outcomes are not selected to produce balanced signs or successful recoveries.

| Step | Evidence | Mechanism |
| ---: | --- | --- |
| 0 | Initial dossier | Priors and mandate only |
| 1 | Management headline | H reported with 85% accuracy if V=1; fair coin otherwise |
| 2 | News summary or independent customer panel | Mechanical copy of step 1, or independent 80%-accurate H observation |
| 3 | Customer operating table | Depends on H and A through the table above |
| 4 | Inspectable broker model | 8 + 7 × management signal + 4 × operating signal, in percentage points; no new observation |
| 5 | Unit-economics panel | Independent 80%-accurate M observation |
| 6 | Management source audit | Independent 90%-accurate V observation |
| 7 | Implementation review | Independent 90%-accurate A observation |
| 8 | Second customer panel | Independent 80%-accurate H observation |

Independence of primitive measurements is conditional on the latent states. The two copy/independent arms are balanced within each pair of episodes, including the held-out pair. An evaluator-only generator override can replay the same underlying world and all other primitive observations under either arm. The independent measurement can disagree with management; this is not a manipulation that holds the second document's content fixed. Each document has a stable ID, timestamp, machine-readable signal, parent IDs and SHA-256 of its exact UTF-8 text.

Realized revenue growth is Uniform(0,12) if H=0 and Uniform(12,24) if H=1, in percentage points. Its randomness is conditionally independent of observations given H. The event H therefore agrees with the >12% revenue target. M denotes whether next-year margin exceeds 18%.

## Responses and decision task

At all 54 checkpoints, collect growth, margin, temporary-disruption and management-validity probabilities; revenue-growth 10th/50th/90th percentiles; invest/hold; and optional citations to currently available document IDs. Quantiles must be ordered; all probabilities must be finite numbers in [0,1]. Values outside the declared forecast support are allowed in answers and scored, rather than silently corrected.

The hypothetical contract pays G if H=1 and minus L if H=0; holding pays zero. The (G,L) pairs are (2,1), (1,2), (3,1), repeated across the six companies. The mandate is linear expected payoff, no switching cost, and no accumulated positions. Thus a reference decision invests iff pG-(1-p)L > 0; ties hold. A numerical tolerance of 1e-12 is used in synthetic decisions and the report-alignment diagnostic. This is a decision probe, not an equity-return simulator.

Full currently available materials are returned at every checkpoint. The host controls actual context resets; an instruction to treat companies independently is not a technical context boundary. Rich source/auxiliary questions are deliberate in this pilot and may cue the intended reasoning.

## Implemented inference and fits

The reference enumerates all 16 states (H,M,A,V) and updates their joint probability. Source and auxiliary beliefs are marginals of that same update; posterior source trust is not reused to process an observation a second time. Copies and model calculations with available parents have conditional likelihood one and leave the posterior unchanged.

Three models are compared using growth-probability reports:

1. Fixed joint reference, with public priors and no fitted coefficients.
2. Weighted evidence accumulation: separate nonnegative positive/negative evidence weights in [0.05,4], and a shared duplicate-counting weight on the grid [0,1] in steps of .01. For each duplicate weight, constrained least squares fits logit-report increments. Output gain and retention are fixed at one. The reported negative log multiplier is log(negative_weight/positive_weight).
3. Joint auxiliary-prior alternative: shift the initial log odds of A by a value on [-3,3] in steps of .1. Fit growth-probability levels, with source and growth priors fixed. Report a near-optimal range at train MSE <= minimum + .0001; it is not a confidence interval.

The first four episodes train each model; the last two episodes are held out for trajectory RMSE. Held-out answers never choose fitted parameters. Models 1 and 3 agree at zero auxiliary shift; the weighted model also nests reference behavior. Near-tied reference-run model selections are therefore expected.

Negativity is operationalized here by the sign of the incremental likelihood ratio for H, falling back to the standalone sign for redundant items. This is a versioned refinement of the proposal's standalone-sign coding: an audit may be good or bad news about H depending on the earlier management claim. It is a target-relative diagnosticity effect, not an estimate of lexical sentiment or a universal negativity trait.

Source-framing coefficients, reporting-gain effects, retention, congruence, loss weighting and research acquisition are not fitted in this pilot. Confidence reports are evaluated as predictions from the declared continuous mixture, not as direct observations of internal precision. The Gaussian uncertainty model in the proposal remains an alternative for later tasks.

## Scoring and validation

- Brier/log scores and reference RMSE for each probability target, plus separate final-checkpoint scores. Log scores/logit fitting clip only for numerical evaluation at [1e-6,1-1e-6]; submitted endpoint answers remain unchanged.
- Proper 80% interval score and quantile pinball loss for revenue growth; final interval coverage across six company outcomes.
- Decision/report agreement and expected regret relative to the reference with the same public information and mandate.
- Absolute forecast changes on redundant items. No global epistemic or reputation score.

Checkpoints share outcomes within each episode. No population confidence intervals are reported from these six episodes. A rank check flags weighted-model designs that do not identify all three fitted quantities. A successful fit is still conditional on the assumed reporting scale and model restrictions.

The recovery command uses 20 evaluator-side seeds by default for five response policies: reference, asymmetric evidence weighting, duplicate counting, conservative weighting, and an altered auxiliary prior. It adds logit-report noise (SD .015), retains all attempts, reports parameter errors and held-out model-selection counts, and exits nonzero if its declared recovery gates fail. It records evaluator/spec fingerprints and the simulation-source hash. Synthetic recovery is not an LLM or psychometric validation study.

Synthetic demos select either the weighted-evidence family or the auxiliary-prior family. Combining a nonzero auxiliary shift with altered evidence weights is rejected because this pilot does not specify or fit that combined policy.

Offline tests cover joint calculations by hand, provenance/dependence, source and auxiliary discrimination, matched world replay, quantiles, noisy recovery, held-out exclusion, schema drift, persistence, concurrency/idempotency, truth withholding and full real MCP stdio runs. TypeScript tests validate/sign both report versions and verify exact-byte hashes; RPC coverage remains mocked.

## Running and exporting

```sh
uv sync --locked
pnpm install --frozen-lockfile
uv run epistemics company-preview --output output/company-pilot/episode.md
uv run epistemics company-demo --output output/company-pilot/reference-report.json
uv run epistemics company-recovery --seeds 20 --output output/company-pilot/recovery.json
uv run epistemics schema
uv run epistemics validate output/company-pilot/reference-report.json
```

Through MCP select battery="company" in describe_battery and start_evaluation, then use the existing get_trial / submit_answer / finish_evaluation lifecycle. See the [answer protocol](../examples/company-agent-protocol.md). Reports/databases and generated private study artifacts remain Git-ignored. No outcomes are disclosed until all checkpoints are complete.

The first useful review is the authored episode preview alongside its model and reference trajectory. After reviewing the realism and elicitation burden, run actual agents in isolated sessions and add crossed source/output framing or a less explicit discovery condition as a separately versioned experiment.
