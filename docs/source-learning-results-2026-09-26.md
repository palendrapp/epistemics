# Source-learning collection: implementation and synthetic acceptance

Completed 26 September 2026; implementation and validation began on 25 September. **This document reports synthetic acceptance only.** A subsequent [fresh-agent run](source-learning-acceptance-2026-09-26.md) completed the new battery later on 26 September; actual human acceptance remains pending.

The [source-learning collection](source-learning.md) now implements the second milestone of the [source-inference roadmap](source-inference-design-2026-09-24.md): consistent private source processes, persistent public learning, sparse/dense assignments, browser/MCP collection and prospective prediction. This document reports software and synthetic acceptance, not empirical cognitive profiles.

## What changed from the laboratory

All archives, current reports and purchased audits now belong to the same generating source. Current company reports are natural draws from that source, not diagnostic counterfactuals. The first twelve company forecasts occur before any audit is offered. Their reports fit the candidate-family and reporting-gain distributions, which freeze before twelve new companies are encountered. Public resolutions and purchased research can update the observer, but later reported probabilities and dense source judgments never enter the model as free priors or likelihoods.

The battery has six sources, 24 companies, 36 probability/decision checkpoints and twelve research choices. Dense assignments add 48 source questions. Matched seeds supply identical underlying worlds across conditions; treatment effects require separate actual participants or fresh agent runs.

## Recovery on the collection design

Two runs use seeds 20260925 and 20261025. Each generates 32 different worlds, with a dataset from each of the three response families in every world: 96 datasets per run, 192 total. Within a run, the families share worlds; these are 192 simulated datasets, not 192 independent source environments or participants. Generating gains cycle through 0.83, 1 and 1.17, with two off the fitted grid. Noise is independent between companies and correlated within a company's initial/revised pair. Research branches rotate independently of the simulated policy.

Every dataset selects its generating family, and every selection exceeds the declared 0.8 conditional probability threshold. Thus this collection distinguishes the implemented accounts using twelve unaudited forecasts; it does not depend on asking the flat model to ignore a newly disclosed selection rule.

| Generating account | Gain MAE, seed A | Gain MAE, seed B | Later latent RMSE, A (points) | Later latent RMSE, B (points) |
| --- | ---: | ---: | ---: | ---: |
| Joint source process | 0.027 | 0.030 | 0.369 | 0.386 |
| Flat source accuracy | 0.033 | 0.036 | 0.491 | 0.556 |
| Fixed discount | 0.045 | 0.039 | 0.739 | 0.566 |

These recovery errors condition on the generating family. Later prediction averages over the frozen gain distribution and compares with noiseless synthetic response probabilities. It is not prediction error against actual agent answers. The declared engineering screens pass in both runs: at least 90% primary joint/flat discrimination, joint gain MAE at most 0.15 and joint later latent RMSE at most five points.

An earlier 16-repetition development check also passed. The two reported 32-repetition runs use the final implementation fingerprint below. Finite candidate supports, matched response-noise assumptions and the tested gain range constrain the result. Unknown noise, missing hypotheses, persistent source-specific response bias and empirical adequacy remain open.

## Whole-collection acceptance

Complete synthetic sparse and dense runs each accepted all 36 checkpoints, used all four research branches three times, froze calibration before heldout collection and produced byte-stable reports on repeated export. Their observed-report prediction errors differ from the noiseless recovery errors above:

| Synthetic preview | Frozen mixture RMSE (points) | Fixed joint observer RMSE (points) | Calibration mean RMSE (points) |
| --- | ---: | ---: | ---: |
| Sparse, seed 20260925 | 2.270 | 2.247 | 38.204 |
| Dense, seed 20261025 | 3.785 | 3.753 | 36.545 |

These previews use a joint synthetic generator with reporting gain one, so a fixed joint observer is already well specified. The frozen fit provides no RMSE improvement over that baseline here. The previews use different worlds and random response draws; their difference is not an elicitation effect.

All decisions in these generated previews were consistent with their reported probabilities by construction. Research was rotated for branch coverage, not chosen by a recovered search policy. A separate excluded direction-reversal response test causes every candidate to fail the heldout conditional adequacy screen. A random-selection audit makes the joint and flat observers equivalent where their assumptions coincide.

## Transport, privacy and regression checks

The full repository check passes: **311 Python tests and 37 TypeScript tests**, plus lint, formatting and TypeScript checks. Fourteen new tests cover coherent generation, private evidence boundaries, persistent audits, sparse/dense contracts, prediction locks, concurrent immutable retries, restart, frozen-fit exclusions, exact export bytes, model recovery, adequacy failure, schemas and complete local transports.

An actual stdio MCP connection completed the entire synthetic collection with the five public tools. An actual loopback HTTP flow completed the collection and checked private-link authorization, cross-origin rejection and instruction acceptance. A browser inspection additionally verified the rendered source archive, committing a forecast, outcome feedback and purchasing a selection audit. Browser inspection used an explicitly synthetic fixture; it is not human usability acceptance.

Earlier evaluators and active human sessions are unchanged. The original laboratory fingerprint is also unchanged. Solana tests remain mocked-RPC coverage; this increment made no registry write, transaction, payment or passport issuance.

## Next acceptance

The subsequent [fresh-agent acceptance](source-learning-acceptance-2026-09-26.md) records one continuing public-only context, configuration, duration, usage, comprehension feedback and frozen forecasts. The [current delivery plan](decision-value-pilot.md) now calls for a compact repeated-configuration comparison, matched elicitation subset and a controlled transfer bridge, with actual human usability separate. A single successful run does not establish stable bias, treatment benefit or a general epistemic phenotype.

## Exact-byte commitments

Implementation fingerprint: `d222e34b05736bf934ba04adaf63ad8a4350213e351f92a249d3898855656ade`.

The generated private collections and reports remain outside Git. The hashes below identify reproducible local artifacts; they are not execution attestation or independent evidence of creation time.

| Artifact | SHA-256 |
| --- | --- |
| source-learning-validation-a.plan.json | `f57bd43bce8a309d42d0ca7c9b9f3389897db7da20ae73772df4777a4772cd9b` |
| source-learning-validation-a.json | `4e1c16d5b924a3234394b19aa1b5444c2b9003cbe0476bf977ff3ef02575e384` |
| source-learning-validation-b.plan.json | `e2b08142f52163d4849dfbf9e7af138a4671e2753c1ed6f3628581938a23576a` |
| source-learning-validation-b.json | `61dc8f023603175935253ced4fb7092c10a5d22012605946d884c724f038cc71` |
| source-learning-preview-sparse/report.json | `b04a4135eb97db43163d86af68d403bfdfaef47a9ae2e4aa3b56fab563af7cbe` |
| source-learning-preview-dense/report.json | `aa5c2e02b9fa0a1097f3dccb61584ff162b7273ad6028ed4b2cee2d19481fe02` |
