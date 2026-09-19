# Fresh-context provenance smoke test — 20 September 2026

Two fresh Codex subagents completed a predeclared matched pair through the real sequential MCP server: **12 accepted answers, two finished episodes, two normally closed transport attempts, no restarts or reported transport problems**. This is a `transport_smoke` collection, not a balanced phenotype or an empirical predictive-validation result.

## Setup

The pair was selected before responses as the first matched group in the randomized design's interleaved-chain partition. One respondent received original independent reports; the other received matched claims whose later reports explicitly relayed earlier sources, including a copy of a copy. Both saw the same base rate, claims, source histories, order and payoffs. The entire smoke design is retired from subsequent empirical final evaluation.

Each subagent started without this conversation's history and used only a JSON-lines bridge to its assigned MCP process. Respondents received current public checkpoints and supplied their own answers; the bridge did not generate answers or reveal reference probabilities. This was fresh conversational context with a shared filesystem and instructions restricting access, not OS isolation or independently verified execution. The model inherited the session default; an exact provider model version was not independently exposed or verified. The configuration hash covers the stored respondent instruction template and operator declarations, not hidden system instructions or unknown provider settings.

The collector implementation was frozen at commit `664e396`; the additional CLI/full-collection tests are in `06a41fd`. Private configuration material, raw reports, design seeds and the database remain in ignored local output. This document summarizes public task observations and transport status.

## Observed responses

Reported probability that the company meets its target:

| Checkpoint | New assessment | Copied-report episode | Independent-report episode |
| --- | --- | ---: | ---: |
| 0 | Base rate only | 80.00% | 80.00% |
| 1 | Negative; history 12/18 correct | 66.67% | 66.67% |
| 2 | Positive; history 15/18 correct | 90.91% | 90.91% |
| 3 | Positive; relay of document 2 versus new sample | 90.91% | 98.04% |
| 4 | Negative; relay of document 1 versus new sample | 90.91% | 96.15% |
| 5 | Positive; relay of document 3 versus new sample | 90.91% | 99.21% |

The copied-report respondent made no further probability change after checkpoint 2, including when the final document relayed a previous copy. The independent-report respondent continued to update with the direction of each new assessment. All 12 decisions were `act`, so this pair shows a probability contrast but no decision contrast or demonstrated decision benefit.

Both trajectories numerically match likelihood updates using the raw 12/18 and 15/18 source success rates as fixed accuracies, within response rounding. That is compatibility with a calculation, not identification of internal reasoning. The evaluator reference instead uses the declared Beta(1,1) source-accuracy model; those reference assumptions are not uniquely determined by the public materials. Do not turn this difference into an unqualified cognitive-bias label.

No profile parameters, confidence intervals, empirical prediction score or intervention effect are estimated from this pair. In particular, it does not establish a stable zero-copying bias, robustness to concealed dependence, or performance across priors and evidence strengths. Recorded episode durations were approximately 64 and 65 seconds; token usage and monetary inference cost were not measured.

## Validation and traceability

The private export validates as `epistemics.predictive-responses.v1` and remains explicitly agent-origin, operator-asserted, execution-unverified and smoke-scoped. Its exact-byte SHA-256 is `3b0c0dacaacc2f17847f7e16b2f6b87983a4f28958695ee81163a41cff5e39ef`. This digest identifies the local artifact; it is not a signature or an independently published execution attestation.

Separately, all 18 synthetic engineering checks passed on this design. Repository verification comprises 159 Python tests, including real MCP restart/immutability tests and a synthetic 72-episode / 360-checkpoint collection/export, plus 20 TypeScript tests. TypeScript RPC coverage remains mocked; no network transaction or payment was made for this test.

Next cost and freeze a complete multi-configuration run, empirical prediction baselines and success criteria. Fit only on profile cases, develop support selection on policy cases, and reserve a fresh final partition for the locked comparison. The evidence-ledger intervention comparison is still pending.
