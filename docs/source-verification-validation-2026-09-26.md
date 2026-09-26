# Assigned-verification validation — 26 September 2026

Implementation `source-verification/0.1.0`, committed as `26f59de`, passed its engineering and synthetic gates before the fresh acceptance and Stage A comparison. The [task contract](source-verification.md) separates evaluator-assigned checks from voluntary research; original source-learning, panel and clarified-delivery implementations remain unchanged.

| Seed | Assigned policy | Datasets | Primary-pair accuracy | Joint gain MAE | Joint later latent RMSE, points |
| --- | --- | ---: | ---: | ---: | ---: |
| 20260926 | None | 96 | 100% | 0.03156 | 0.42785 |
| 20260926 | Always | 96 | 100% | 0.03156 | 0.40014 |
| 20261026 | None | 96 | 100% | 0.02813 | 0.42239 |
| 20261026 | Always | 96 | 100% | 0.02813 | 0.39710 |

Every generating family was selected in all 32 replicates per policy and seed. Recovery uses the unchanged family/gain fitter and predeclared original thresholds, but now follows each complete assigned path. Initial calibration occurs before verification, so its gain recovery and family discrimination match across the two policies. Later prediction checks exercise their different evidence paths. No language effect, intervention benefit or research-choice policy is recovered by these simulations.

All **343 Python tests**, **40 TypeScript tests**, Ruff, formatting, TypeScript compilation and Biome passed. The nine new tests exercise:

- Complete no-check and always-check collections, correctly timed resolutions, immutable and concurrent retries.
- Strict public answers without a query field; unavailable source audits and hidden evaluator state.
- Cost accounting for declined investments, exact matched-world contrasts and the fixed feasibility gate.
- Assignment, presentation, chronology, analysis and feedback tampering.
- Complete stdio MCP paths for both policies and private authenticated browser HTTP collection.
- Prospective plan/configuration/policy locks, implementation snapshots and stopping admission after failure.
- Refusal to import assigned checks as voluntary research in the passport adapter.

A separate synthetic browser preview was inspected at a provisional checkpoint: it displayed the check, its price and the provisional/final distinction, with only probability and decision inputs. This is a UI check, not human acceptance. The preview was closed; existing human sessions were untouched. TypeScript integration tests use mocked RPC and authorize no payment; no validator or live-network validation was performed for this increment.

| Commitment | SHA-256 |
| --- | --- |
| Verification implementation | `259cfd9cf81d1b8d389085142110be3c0c2fc7dcb65cfec9a859a5d4c59ba35a` |
| Validation A plan | `100ff27dd937368c39306e6ebc9ebb185240fc6b37db7e806a34bd3e3ce46b2f` |
| Validation A result | `f686f7d67472bac8ee4a324cbd5c8e33f1642e781457c5eb6b7b988da39cc148` |
| Validation B plan | `9b81b574b4e34043d74688c0e611adb88f24d6c8982860553e4dc1603a8509b7` |
| Validation B result | `91a022f06c631d2a2d0d1ff39e5caafefd2db1b060943400cd9b41ea6bd8a1af` |

Private result files are `output/verification-validation-a.json` and `output/verification-validation-b.json`, with their plans alongside. Hashes bind exact operator-held bytes; they are not independently attested timestamps.
