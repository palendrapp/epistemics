# Source-inference laboratory: first synthetic results

25 September 2026. **Offline task-design validation. No agents or humans were evaluated in this increment.**

The first milestone of the [source-inference roadmap](source-inference-design-2026-09-24.md) is implemented. The [laboratory specification](source-inference-lab.md) gives the model equations and reproduction commands. Source measurement quality and selective reporting now have separate generative roles. Observers learn from public resolved histories and predict a new company judgment without using that respondent's freshly elicited likelihoods as model inputs.

The result is encouraging but narrow: the proposed inputs can separate three specific behavioral accounts under the tested synthetic reporting processes. They do not establish how a real agent interprets sources. The balanced comparator performs well enough that more elaborate design optimization is not the immediate bottleneck.

## What was run

Each run uses six source histories crossing accurate/noisy measurement with random/favorable/unfavorable panel selection. Business expansion rates are disclosed controls. The observer must infer the source process; learning business semantics is outside this milestone.

Three candidate accounts predict company probabilities:

- **Joint process:** infer both measurement accuracy and panel selection from the resolved source archive.
- **Flat accuracy:** infer measurement accuracy, while treating every report as a randomly sampled panel.
- **Fixed discount:** ignore source history and apply 35% of the literal report's log evidence.

The candidate bank contains 648 probes. Each diagnostic design selects 24: two fixed anchors and two probes ranked by marginal model information for each source. The matched-random design retains the same anchors and samples the other twelve. Thirty-two heldout templates are disjoint from both, with a fresh public archive. Design selection uses a third archive. Plans and predictions are written before synthetic responses are generated.

Each run has 32 repetitions per generating family at each of two response-noise levels: 192 synthetic datasets. Reports include correlated source-block offsets and whole-percentage rounding. Generating reporting gains are 0.83, 1 and 1.17; two lie between fitted grid values. Higher noise is supplied to the inference model, so that condition does not test noise misspecification.

Three seeds were run: A = 20260925, B = 20260926, C = 20261025, for **576 datasets**. These integers are random seeds, not collection dates. A and B reuse some streams across different roles because the implementation offsets its base seed; they are not independent replications. C was added after inspecting that overlap and uses nonoverlapping seeds. The implementation and screens were unchanged across the runs. Screens are recorded prospectively within each run, not externally preregistered.

## A concrete distinction the task can express

Suppose a perfectly measuring source reports exactly four of five customers expanding. Under the toy world's 70% versus 30% expansion rates and equal company prior:

| Known reporting process | Probability of strong demand |
| --- | ---: |
| One random panel | 92.70% |
| Highest count among four panels | 79.93% |
| Highest count among ten panels | 39.30% |

The last observation includes the absence of any five-of-five panel across ten opportunities. A source can report its selected measurement faithfully while the selection process reverses what the count implies. These are exact model calculations under known processes; they are not empirical participant judgments or the required discovery response under uncertain measurement.

## Discrimination and recovery

For the information-selected design, **all 576 datasets select the generating family**, and all exceed the declared 0.8 conditional model-probability threshold. This covers only the three specified families, finite source supports and tested reporting gains. Relative model probability is not evidence that a candidate adequately describes an unmodeled respondent.

The balanced comparator correctly distinguishes the primary joint-versus-flat pair in every run and noise condition. Its three-family accuracy is also perfect except in A's higher-noise condition: one flat-accuracy dataset selects fixed discount and one fixed-discount dataset selects flat accuracy. Seven datasets there fall below the 0.8 threshold, including those two errors. They are reported as ambiguous.

The following ranges cover A, B and C at baseline noise. Parameter errors condition on knowing the generating family. Prediction errors are means of per-dataset RMSE against noiseless synthetic response targets on the 32 heldout inputs; they are not outcome accuracy or empirical agent-prediction scores.

| Generating account | Gain MAE, selected | Gain MAE, balanced random | Heldout RMSE, selected (points) | Heldout RMSE, balanced random (points) |
| --- | ---: | ---: | ---: | ---: |
| Joint process | 0.025–0.033 | 0.018–0.025 | 0.33–0.47 | 0.25–0.37 |
| Flat accuracy | 0.037–0.040 | 0.024–0.032 | 0.61–0.69 | 0.38–0.52 |
| Fixed discount | 0.099–0.136 | 0.022–0.030 | 1.65–2.46 | 0.41–0.51 |

**The information ranking trades parameter precision for family separation.** It is a marginal ranking, not a joint optimization over the whole battery or all parameters. Balanced random probes estimate reporting gain better in these runs. Under higher noise, selected-design gain error rises to 0.131–0.201 for the fixed-discount account, despite perfect family identification. The engineering gates require joint-family recovery, not uniformly strong recovery for every family; all declared gates pass without implying that broader result.

Reporting gain is a nuisance parameter describing how synthetic predictions become reports. This increment has not recovered source-label bias, negativity, learning rate, search depth or an internal cognitive mechanism. Actual source accuracy is an environment parameter; its posterior summary must not be relabeled as a participant trait.

## The analysis can decline an explanation

Three controls pass in every run:

1. Neutral predictions leave all families equally likely and all thirteen reporting gains tied. The result is ambiguous.
2. Establishing random sampling makes the joint and flat accounts mathematically equivalent, even when the company report is informative. Their model evidence agrees to numerical precision.
3. A deliberately excluded direction-reversal policy causes all three candidates to fail an independent heldout adequacy screen. Selecting the least-bad training model does not turn it into an adequate explanation.

The third check compares heldout error with a 99th-percentile simulation envelope at each fitted candidate's parameters. It is a conditional development diagnostic, not a calibrated general-purpose hypothesis test. This strong failure case does not establish sensitivity to subtler misspecification.

## Research choices are now diagnostically different

The simulator computes customer research, source-selection audits, measurement audits, irrelevant information and stopping under explicit costs and investment thresholds. Decision-value and company-information policies have disjoint optimal action sets in 112/144 contrasts for A, 111/144 for B and 106/144 for C. Ties are retained. These are computed policy contrasts, not 432 observed decisions.

This addresses a design problem in the earlier narrative run: if every plausible policy prefers the same query, repeated selection of that query explains little. Here, research price and decision relevance can change which query is useful. Actual search-policy fitting is still unimplemented.

## Consequences for the next milestone

Proceed to a bounded participant protocol, starting from balanced coverage rather than assuming marginal information selection is superior. Before collection:

1. Bind each source's history, new report and actual audit to one consistent private world. The current diagnostic bank contains counterfactual audit/history combinations; it is not itself a ready-to-administer collection. Clearly distinguish any hypothetical probe from an actual audit and re-run discrimination after imposing this consistency.
2. Separate unaudited discovery from disclosed controls. Some current differences arise directly because the flat and fixed-discount accounts ignore audits. Successful discrimination here does not establish that experience alone identifies source-learning behavior.
3. Keep the public source history available across company episodes. Show new company evidence sequentially, and collect sparse forecasts, research choices and actions. Compare a separately assigned dense-elicitation condition to measure the help or interference supplied by our questions.
4. Freeze candidate predictions before unseen cases are answered. Assess adequacy against simple alternatives and allow an inconclusive result. Run a small fresh-agent acceptance before a larger collection, and complete actual human usability separately.

Source-label crossover, dynamic changes, broader hypothesis search, individualized assistance and passport integration follow once those contrasts work. Existing batteries and human sessions remain unchanged. No new passport claim is issued.

## Verification and provenance

The full repository check passes: **297 Python tests and 37 TypeScript tests**, plus formatting, lint and TypeScript checks. The thirteen new Python tests include independently enumerated generator probabilities, sampled ledgers, source-ID exchangeability, numerical likelihood integration, design separation, research costs, failure controls and exact-byte reproducibility. Solana integration tests use mocked RPC; no live transaction or payment was made.

The new world, design and analysis use versions `source-world/0.1.0`, `source-design/0.1.0` and `source-discrimination/0.1.0`. The main report schema is unchanged. Generated private worlds and result bundles remain outside Git; the exact commitments below identify the local reproducible runs. A hash identifies bytes, not execution attestation or proof of when those bytes were created.

Implementation fingerprint: `46da0ced2322c89971c833e0e657517ff166de86cb6ba1b51674ecbc6f0a535d`.

### Run A — seed 20260925

- plan.json: `382f7b2bda40c3a55f9a7a87a55b01d37d37b972fbf7c0efa747f65a5e638e35`
- public-inputs.json: `6daf873bec75265fcd6cc99ebd31e7e05ade1e22d6beb35da7b1f8666d496ef0`
- prediction-lock.json: `b4a3ca825b11270a24f181e15dd2a83a2a1262fed58ae8fae20f2890a3fd6b2c`
- report.json: `45e0412f7863c43e68b5ae9077a31029edae6c2d1a683d66039f77ccab71925d`

### Run B — seed 20260926

- plan.json: `739be74f3343b6b0a116abc48f33d5713be94404eae9ef2e739202c703296a4b`
- public-inputs.json: `1152957b94139a0ea8f6465704da7df872e37fa4ce42b55bd0c313855d7c5b9b`
- prediction-lock.json: `eee41195bfa8de9f53d6c44e0d1d2ab2d4d65641b9c83cd620aa79307090ef21`
- report.json: `bf96b5f5c24499217bddee4d4059da0041bab884a9f4abbd3a28b01c32f7eb1c`

### Run C — seed 20261025

- plan.json: `90aed77c677dacc06e492415b0a4849ced2d02316e21a563bf3d8c7bbaf46b7c`
- public-inputs.json: `beb799a9d5fbc0b00e173691c08b8cbf431dfb367cc42e92b4ccefe49f8749d5`
- prediction-lock.json: `69bc9db1679ffbab93f9717d6ddd898a4fd647a5fca077bb9c5f766333203b56`
- report.json: `165b5a5f17b3a9f729594e831049ffe29fb8065cb1c354a79b5621a872d3814d`
