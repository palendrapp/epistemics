# Frozen offline value-audit plan

27 September 2026, before execution of either main simulator batch. The [audit specification](decision-value-audit.md) defines the information boundaries, exact expectations, synthetic controls, calibration bins, paired policies and interpretation rules.

- Analysis version: `source-value-audit/0.1.0`.
- Two seeds: 20260927 and 20270927; 512 worlds per seed, 12 later companies per world.
- Total: **1,024 independent worlds / 12,288 later-company cases**, eight synthetic reporters and three policies on each case.
- No respondent contexts, provider calls, account tokens, transactions or changes to existing evidence.
- Primary quantities: expected and realized cost-aware-minus-none gain; compare with always-check; purchase/action regret; separate starting-report reliability and privileged-reference Brier loss.
- Report both batches and pooled results, fixed public-information opportunity strata, and negative realized contrasts in 512 nonoverlapping two-world pairs.
- The earlier .01 points/company effect floor is a design feasibility screen, not a newly claimed real-agent success gate. No automatic respondent collection is authorized by simulator success.
- No adaptive exclusions or stopping. A calculation failure must be reported and corrected with a new implementation commitment before rerunning; do not overwrite frozen artifacts.

| Commitment | SHA-256 |
| --- | --- |
| Audit implementation | `3d319809603942f47a6bfb96d2640d04cbdba92779c667706524d9de443ec39b` |
| Exact private plan.json bytes | `bf3240c334dcedf1df460392758e10c09fdb2da07e19484afb1e3d3b2d9dfe97` |
| Existing selective implementation, unchanged | `6de0cedddc97d4f74507badee93d430970eb4bd01135d748a21f7096d4481367` |
| Existing blanket implementation, unchanged | `259cfd9cf81d1b8d389085142110be3c0c2fc7dcb65cfec9a859a5d4c59ba35a` |

Private directory: `output/value-audit-20260927/`. The exclusive plan already exists before main execution; only aggregate results and commitments will be published. Development validation used separate test seeds. Fifteen new offline tests passed, including independent rational enumeration, a 100,000-draw Monte Carlo check, calibrated/distorted controls, public-information isolation, history timing and artifact immutability. The original participant behavior and report contract require no version change; this independently versioned audit estimates no new cognitive parameters.
