# Exact-wording narrative repeat, 24 September 2026

Eight fresh contexts repeated all eight cases from the [first narrative acceptance](narrative-acceptance-2026-09-24.md), preserving wording, assignment IDs, order, evidence and resolutions. The run completed **32 checkpoints and 160 probability entries in 6 minutes 37 seconds**.

Starting joint distributions differed by **4.375 total-variation percentage points on average** between identical-wording repetitions, compared with a **3.75-point** average between the first run's prose and fact presentations. This small check supports caution about the earlier apparent presentation differences. It does not establish that formatting has no effect.

## Frozen comparison

The plan preceded collection and specified all eight cases, initial-joint TV distance, likelihood-forecast mean absolute difference, post-signal TV distance, research-choice agreement, and post-audit TV only when the query matched. It also specified within-run format contrasts and contrasts between the two-repetition format means. No significance or trait-release threshold was declared.

The requested Astra alias, medium reasoning, unspecified temperature, CLI `0.155.1`, prompt, evaluator fingerprint, process recorder and tool/isolation settings matched the original configuration exactly. The only configuration-object changes were purpose and operator-script hash; participant/run metadata changed. Eight fresh process/context IDs were used, with no accepted history at entry. Exact provider model revision and execution isolation remain unverified/operator-asserted.

Budget: one attempt per case, at most 300 seconds each and 900 seconds overall, concurrency one. Started **12:27:31.495006 UTC**, finished **12:34:08.121132 UTC**, elapsed **396.627 seconds**. No failed or unattempted cases, retries, rejected submissions, fit exclusions or missing usage. All 96 MCP calls stayed within the assigned five-tool protocol.

## Repeat variation

| Observable distance between identical cases | Mean | Maximum | Comparable cases |
| --- | ---: | ---: | ---: |
| Initial joint distribution, TV points | 4.375 | 10 | 8 |
| Prospective signal forecasts, mean absolute points | 1.156 | 2.75 | 8 |
| Post-signal joint distribution, TV points | 4.5 | 6 | 8 |
| Post-audit joint distribution, TV points | 3 | 9 | 8 |

Research choices agreed in **8/8 cases**, all pipeline audits. Each again maximized information under that case's preceding joint report. This preserves the earlier coverage gap: an always-pipeline policy remains indistinguishable from information-sensitive choice in these cases.

| Case, in original and repeat order | Initial repeat TV | Post-signal repeat TV | Post-audit repeat TV |
| --- | ---: | ---: | ---: |
| Subscriptions fall, prose | 10 | 6 | 9 |
| Distributor rise, facts | 5 | 5 | 4 |
| Subscriptions rise, prose | 5 | 6 | 1 |
| Subscriptions fall, facts | 5 | 6 | 4 |
| Distributor rise, prose | 5 | 5 | 1 |
| Distributor fall, facts | 0 | 1 | 0 |
| Distributor fall, prose | 0 | 1 | 0 |
| Subscriptions rise, facts | 5 | 6 | 5 |

The repeat run's within-run format contrast averaged **6.75 initial-joint TV points**; comparing format means across the two repetitions gives **4.25 points**. These quantities have different sampling properties and are reported descriptively, not as a causal estimate or statistical test.

The narrative-minus-facts demand difference reversed from **+5 to −5 points for subscription rises**, and from **−5 to +5 for subscription falls**. The distributor-fall difference stayed −5; the distributor-rise difference changed from 0 to +10. Two repetitions per wording are insufficient for a stable framing or valence label. The evidence supports reporting starting-judgment variability separately from within-episode update consistency.

## Within-episode consistency

The repeat's mean own-report discrepancy was **0.554 TV points after the signal** (maximum 0.818) and **0.169 after the audit** (maximum 0.5). All comparisons overlapped the conservative rounding bounds; overlap is not proof of exact joint coherence. All final audits were incorporated exactly. The forecast under both logically sufficient events ranged from 98% to 100%, retaining a small literal-consistency shortfall in some cases.

All five conditional report families again minimized at **w = κ = α = 1**, with **0.369-point coordinate RMSE**. This is an in-sample fit conditional on the initial reports, not recovered internal beliefs or held-out predictive validation. The starting numbers vary while their subsequent use remains closely consistent in these scaffolded tasks.

## Cost, usability and audit

Input usage was **1,198,247 tokens**, including **1,047,808 cached**; non-cached input was **150,439**, output **5,081**, total processed **1,203,328**. No usage attempt is missing; marginal dollar cost is unknown under the account arrangement.

All eight contexts again mentioned the one-based prose versus zero-based index mismatch. This repeat deliberately preserved that wording. The new [0.2 corroboration task](narrative-inference-v2.md) uses named stages, public checkpoint numbers 1–4 and opaque named trial IDs instead. The known CLI skill-discovery warning remained; no tool failure occurred.

The comparison command validates frozen protocol/assignments, requested model metadata and identical public stimuli, computes distances from response rows rather than trusting stored analysis, and hashes both exact input reports. Operator auditing separately verified configuration equivalence, context IDs, timestamps, tool boundaries, usage and byte commitments. Raw reports, prompts and databases remain private.

```sh
uv run python -m epistemics.narrative_repeat \
  --first-report output/first/collection/report.json \
  --repeat-report output/repeat/collection/report.json \
  --output output/repeat/comparison.json
```

## Exact private-byte commitments

| Artifact | SHA-256 |
| --- | --- |
| Unchanged evaluator | `89a971dc11790af2e7137ed4ce4ccc42546e4cbc9f97401e83faf147c2ff3fd7` |
| Original report | `7bdbae35326f0daf4e168aae9a41a9c548891438f7520db9cb1b6d0635f9ef0e` |
| Repeat plan | `ecec654f2671acc95e3235f6ac456641f7a397a8d86e7c48c9aa941afc6b0436` |
| Repeat configuration | `f1b799843421b192cf50bc83343165bf76c369c08b0a6f81b067b727f76015ea` |
| Repeat manifest | `26adcc228c6a22b3a13d3e9e2ea61dfc64f92fc0d056b8e767104e36d572f1a2` |
| Repeat report | `55250cadec4ec910ab089356adffb85dde738dd4fc1f07750ee892553275e807` |
| Repeat execution | `6cf734ec24af32bf72eb940fbd6c3fa767faf007200c4b3a5df264166a31f358` |

These commitments bind private bytes; they are not independent timestamps or attestations of the underlying model.
