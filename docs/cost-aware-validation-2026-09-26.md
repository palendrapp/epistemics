# Cost-aware verification validation and acceptance commitment — 26 September 2026

The [0.2 protocol](cost-aware-verification.md) is a separate implementation with independently randomized offered prices and a fixed expected-decision-value rule. Original source-learning, delivery and verification 0.1 code is unchanged. The 0.1 fingerprint remains `259cfd9cf81d1b8d389085142110be3c0c2fc7dcb65cfec9a859a5d4c59ba35a`.

## Offline validation

The full Python suite passed **358 tests**; all **40 TypeScript tests**, type checking, Biome, Ruff lint and format checks passed. The new fifteen-test module includes all three full 36-checkpoint MCP paths, the human HTTP flow, immutable/concurrent conditional assignment, exact price/net accounting, tamper and premature-feedback rejection, passport exclusion, order balance, and all 24 comparison cells with explicitly mocked execution. Loopback tests initially encountered sandbox restrictions and passed with local listening enabled. RPC coverage remains mocked; no validator or network transaction was tested.

An independent enumeration of all 32 binary five-customer outcomes checks the expected-value calculation, endpoint behavior and tie rule. Price tests establish four offers per price, all three prices under every prior, two offers per price under each threshold, and invariance to changing private world content while holding public strata and price seed fixed. This does not imply full crossing or absence of chance outcome associations.

Two prospective recovery plans each specify 32 repetitions per observer family per policy: **288 datasets per seed, 576 total**. Off-grid gains 0.83, 1.00 and 1.17 and company-correlated report noise are retained. Both runs pass all original recovery gates separately under all three policies. Best-family recovery is 100% in every family/policy/seed cell. Joint-process gain MAE is 0.0253125 and 0.0271875. The cost-aware branches buy 448/1,152 and 407/1,152 available checks respectively, so both conditional paths are exercised.

| Recovery seed | No-check joint held-out RMSE | Always-check RMSE | Cost-aware RMSE |
| --- | ---: | ---: | ---: |
| 20260927 | 0.324813 pp | 0.306445 pp | 0.319039 pp |
| 20261027 | 0.429730 pp | 0.397074 pp | 0.425469 pp |

These are synthetic latent-target prediction errors under the assumed observer families. They establish implementation/recovery, not real cognitive identification, report calibration or useful verification.

## Prospective acceptance

Before launching real respondents, a separate acceptance plan binds one requested Astra-medium context per policy on one common newly generated world and price schedule. Order: cost-aware and always-check concurrently, then no-check. All three contexts remain separate, continuous internally, with only five public MCP tools. Comprehension and engineering determine admission to the main comparison; payoff does not. Acceptance responses and outcomes will not enter the main estimates.

Bounds: one attempt per context, 900 seconds each, two concurrent, 1,800 seconds overall, 12 million known processed-token admission ceiling, three million reserved per incoming context. No automatic retry or replacement. Exact model revisions and marginal monetary account cost remain unknown; execution is operator-asserted.

| Commitment | SHA-256 |
| --- | --- |
| Implementation | `6de0cedddc97d4f74507badee93d430970eb4bd01135d748a21f7096d4481367` |
| Recovery A | `f378635582b301a72601a960539d360eb21c7f75f67e19e32c9decf0e4dcbbcf` |
| Recovery B | `5d3137e696f75a540a853547d4e7dda133b0201224bbdef03361c0fb1ad5a063` |
| Acceptance plan | `171b499d0bea1a36b2f9a9fd2ad2ed8593007379d0220fe51beec4d473b64708` |

Private roots: `output/selective-validation-20260927-{a,b}.json` and `output/selective-acceptance-20260926/`. These hashes bind operator-held exact bytes and do not constitute independent timestamps or provider attestations. The main plan will be committed separately after acceptance review, before any main responses.

Acceptance subsequently passed. The [frozen main plan](cost-aware-plan-2026-09-26.md) records its full accounting, comprehension review and commitments before confirmation responses.

The implementation also passed [remote CI](https://github.com/palendrapp/epistemics/actions/runs/36265444514). The [completed main results](cost-aware-results-2026-09-26.md) retain the failed benefit gate and document the independent arithmetic/assignment audit.
