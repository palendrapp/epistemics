# Corroboration and research acceptance, 24 September 2026

Eight fresh agent contexts completed the [narrative 0.2 task](narrative-inference-v2.md): **32 checkpoints and 160 probability entries in 7 minutes 26 seconds**. All three predeclared coverage criteria passed. Demand audits were more informative under the preceding reports in four cases, pipeline audits in four, and the agent selected the more informative audit in every case.

This resolves the original task's observed always-pipeline coverage gap. It supports a scoped observation of evidence-sensitive research choices. It does not uniquely identify an information-gain algorithm: choosing the audit opposite the corroborating evidence would also explain all eight choices.

## Frozen collection and execution

The plan, configuration and task implementation were committed to private artifacts before collection. Eight cases crossed subscription/distributor businesses, rising/falling dashboards, and independent customer/pipeline corroboration. Matched cases shared base facts and final truths but differed in corroborating evidence. These contrasts change evidence, not merely presentation. No source likelihoods or population frequencies were supplied.

The requested configuration was Astra, medium reasoning, unspecified temperature, CLI `0.155.1`, with eight distinct fresh contexts. Respondents received only the assigned five-tool MCP protocol; project access, shell, browsing and memories were disabled in the operator configuration. Exact provider model revision and execution isolation remain unverified/operator-asserted. No model-training blindness is claimed.

Budget: one attempt per case, at most 300 seconds per case and 900 seconds overall, concurrency one. Collection started **12:37:43.477089 UTC**, finished **12:45:09.112301 UTC**, and took **445.602 seconds**. No cases failed or remained unattempted; there were no retries, rejected submissions, fit exclusions or missing usage. All 96 MCP calls stayed within the assigned protocol: eight descriptions, eight histories, 40 trial reads, 32 submissions and eight completions.

## Research choices and coverage

| Predeclared coverage criterion | Observed | Result |
| --- | ---: | --- |
| Demand audit exceeds pipeline information by more than 0.01 bits in at least two cases | 4/8 | Pass |
| Pipeline audit exceeds demand information by more than 0.01 bits in at least two cases | 4/8 | Pass |
| Each audit is selected at least once | Demand 4; pipeline 4 | Pass |

All four matched pairs switched choice: customer corroboration prompted a pipeline audit; pipeline corroboration prompted a demand audit. No case stopped. Audits were free and the stated objective was reducing uncertainty about the joint business/pipeline state, so this collection does not test price sensitivity or realistic stopping behavior.

| Policy evaluated against each case's preceding joint report | Mean foregone information, bits per case |
| --- | ---: |
| Observed choices | 0 |
| Always demand audit | 0.285 |
| Always pipeline audit | 0.190 |
| Always stop | 0.978 |

These comparisons measure consistency with stated uncertainty and the declared objective. They do not establish forecasting accuracy, realized investment value or a uniquely identified search mechanism.

## Interpretation and subsequent updating

Customer corroboration produced an initial demand-event probability of **80% in all four cases**, with pipeline-event probabilities of **40–47%**. Pipeline corroboration produced an initial pipeline-event probability of **80% in all four cases**, with demand-event probabilities of **45–50%**. The stories describe partial, fallible evidence rather than an audit of the whole population. These reports show how this configuration interpreted that evidence; their numerical calibration is unknown.

| Matched case | Initial demand difference | Initial pipeline difference | Post-signal demand difference | Post-signal pipeline difference |
| --- | ---: | ---: | ---: | ---: |
| Subscriptions fall | +35 | −35 | +32 | −39 |
| Subscriptions rise | +30 | −40 | +28 | −42 |
| Distributor rise | +35 | −35 | +31 | −37 |
| Distributor fall | +30 | −33 | +27 | −36 |

All differences are percentage points, customer-corroboration minus pipeline-corroboration. With one response per version, these are descriptive contrasts that also contain response variability. The [separate exact-wording repeat](narrative-repeat-2026-09-24.md) demonstrates why variability needs its own measurement.

The mean total-variation discrepancy from updates implied by the respondent's own earlier reports was **0.486 points after the dashboard** (maximum 0.769) and **0.206 after the selected audit** (maximum 0.444). All 16 comparisons overlapped conservative coordinate-wise rounding bounds; overlap does not prove exact joint coherence. Every final resolution was incorporated exactly.

A small literal inconsistency remains: the forecast for the dashboard under both logically sufficient events was **98–99% in all eight cases**, rather than 100%. The mean shortfall was 1.25 points, maximum two. This should remain visible alongside the close subsequent update consistency.

All five conditional report families minimized at **w = κ = α = 1**, with **0.244-point coordinate RMSE** over 96 coordinates / 72 simplex degrees of freedom. The flexible family offered no improvement over the fixed reference. This is an in-sample fit conditional on elicited reports; it neither accesses internal beliefs nor validates stable cognitive parameters or new-case predictions.

## Cost and usability

Input usage was **1,225,880 tokens**, including **1,030,144 cached**; non-cached input was **195,736**, output **5,145**, and total processed **1,231,025**. No attempt has missing usage. Marginal dollar cost is unknown under the account arrangement.

No context reported the old numbering mismatch. Three reported that repeating the full protocol at each checkpoint was verbose, and one reported initial tool-discovery friction. The known CLI skill-discovery warning remained without an observed tool failure. Protocol repetition is a candidate for a subsequent version-reviewed usability change; this frozen collection is unchanged.

The separate private human flow is prepared, with named stages, checkpoints 1–4 and retained history. Synthetic browser interaction verified validation and stage progression, but actual human completion and feedback remain pending.

## Verification and next product step

Operator auditing checked distinct contexts, completed records, tool boundaries, usage, frozen artifact bindings and reproduction of analysis from accepted answers. Both declared synthetic recovery seeds passed before collection. Repository checks passed **284 Python tests and 37 TypeScript tests**, plus Ruff; the main report schema had no drift. These include offline and local transport checks, not live blockchain validation. Raw prompts, reports, evaluator seeds and databases remain private.

The next product increment should carry these separate observations into readable and machine-readable passports: interpretation contrasts, repeat variability, update consistency, literal inconsistencies and research coverage. Each needs its evidence, denominator, task/configuration scope and limitations. Conditional model diagnostics should remain separate. Human usability, unrestricted hypothesis generation, predictive usefulness and intervention benefit remain unfinished.

## Exact private-byte commitments

| Artifact | SHA-256 |
| --- | --- |
| Evaluator implementation | `fd8826c78830e66f6e3bbeda4911838e83bdc8ee2caafde61aa3a50d31bd1a28` |
| Run plan | `ea862b295c01208e35001aa938b3aec33ea39dba3680776408776b8a04b401dd` |
| Configuration | `83a8a616cbbc95c5a8ad6b1f7605d2fd0a8273314dd19ecda78c95b447eeaf71` |
| Collection manifest | `478cea7e1c348995555a7f1f9246f32bfbc8a10e1c6a6f44977f3b6fc3b557b4` |
| Report | `793b14dcb8de1cdcaaef75385568a4091e85a2a4a822b264daba857354bf7ed3` |
| Execution record | `7d9a201beba274028892416df5302d0ca9d4cce127750f2f5ed7638ba2fc1574` |

Commitments bind exact private bytes; they do not independently attest model identity, execution or collection time.
