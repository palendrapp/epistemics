# Source-panel implementation validation — 26 September 2026

The [bounded comparison](source-panel.md) adds fact-preserving prose packets and a profile that is frozen across collections. It leaves `source-learning/0.1.0`, its generator/observer assumptions, previous artifacts and active human sessions unchanged. Panel/packet versions are independent; no main Pydantic report schema changes.

Two predeclared recovery runs used seeds 20260926 and 20261026, eight repetitions per generating family, three families and gains 0.83, 1 and 1.17. Each dataset fits four calibration contexts (two source worlds, two independent noise draws per world), then predicts a third world. The 48 datasets share sixteen triples of source worlds across families; they are not 48 independent empirical participants or independent environments.

| Generating family | Family recovered, A / B | Gain MAE, A / B | New-world latent RMSE, points, A / B |
| --- | --- | --- | --- |
| Joint source process | 8/8 / 8/8 | 0.0213 / 0.0200 | 0.278 / 0.318 |
| Flat accuracy | 8/8 / 8/8 | 0.0150 / 0.0138 | 0.244 / 0.215 |
| Fixed discount | 8/8 / 8/8 | 0.0288 / 0.0300 | 0.385 / 0.378 |

Both runs passed their declared engineering gates: at least 90% family recovery, gain MAE at most 0.15 and new-world latent RMSE at most five points. An excluded direction-reversal control placed every candidate outside its conditional adequacy boundary in both runs. A separate uninformative-data test retains ambiguity rather than forcing a family identity.

These simulations test the specified models and noise, including pooling and new-world prediction. They do not establish empirical repeatability, effects of asking more questions, language interpretation, intervention benefit or a real respondent's internal mechanism. The prose renderer has no synthetic psychological effect by construction.

Ten added tests cover the public/private boundary; factual equivalence through all research branches; sparse/dense contracts; independent profile freezing; transactional presentation/prediction locks; concurrent immutable retries and restart; calibration-only fitting; model recovery and ambiguity; a complete sixteen-collection synthetic comparison; and an actual 36-checkpoint stdio MCP packet collection. The original source-learning fingerprint remains `d222e34b05736bf934ba04adaf63ad8a4350213e351f92a249d3898855656ade`.

The full repository checks passed: Ruff lint/format, **321 Python tests**, and **37 TypeScript tests** with type/format checks. Local browser tests used loopback access; Solana coverage remains mocked RPC, without a validator, live-network transaction, registry write or payment.

| Artifact | SHA-256 |
| --- | --- |
| Panel implementation | `8ecfeca196c023826fe0c461ca4a4e54c1d68094269d8d9548921f46ad41676d` |
| Recovery A plan | `76e2df8d1b9576c821e899b2d04842bea65d4a7532d6d3e9d860cb21838e59d1` |
| Recovery A result | `c3e743be4ee9dfb91a59628578bf709f349e9402adbeb22bae9fa890b77c17af` |
| Recovery B plan | `5662ff73b4bf7e416dab3f898b66df0148d5914ff52cc0dc152a2268072f6ee6` |
| Recovery B result | `873962ec9953bdd2f33e51bceeed8fbefa291170fec2fea88f7ee3eccfba38f9` |

Plans/results remain private local artifacts under `output/`. These are operator-created commitments, not independent preregistration or execution attestation. Empirical results belong in a separate document after the actual panel finishes.
