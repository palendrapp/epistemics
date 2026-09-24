# Relationship diagnostic 0.2: fresh-agent acceptance

On 24 September 2026, one requested `gpt-6-astra` configuration completed the [0.2 relationship diagnostic](auxiliary-diagnostic-v2.md) in **16 fresh contexts, 64 checkpoints and 160 probability reports**. Collection took **11 minutes 46 seconds**, with one attempt per case, no rejected submissions and no failed tool calls. The post-run audit rederived the analysis exactly and verified the frozen configuration, assignments, implementation and report hashes.

The agent extracted the same relationships from numerical company records and summary counts, interpreted the imperfect growth signal using the empirical plug-in probabilities, and propagated that uncertainty consistently. These added controls revealed no representation or propagation difficulty in this configuration. They do not explain the earlier richer investigation's poor model fit or establish a general cognitive phenotype.

## What was observed

| Observation | Coverage | Result |
| --- | --- | --- |
| Conditionals match archive proportions | 16 reports from summaries; 16 from records | 32/32 exact |
| Records versus summary presentation | 8 matched comparisons | Zero difference in conditional spread or absolute mixture gap |
| Growth probability after an imperfect reading | 8 signal cases | 0.75 after high, 0.25 after low, matching the empirical plug-in reference |
| Related judgment follows its own earlier conditionals and reported growth probability | 16 cases after evidence and again on repetition | Zero gap at elicitation precision |
| No new information produces no revision | 32 growth/related reports | 32/32 unchanged |
| Final definitive audit is reflected in both reports | 32 reports | 32/32 exact, at 0 or 1 |
| Earlier definitive growth audit remains reflected | 16 reports | 16/16 exact |

Both initial marginals were 0.5 in every case. The maximum computed mixture gap was approximately `1.1e-14` probability points, a floating-point artifact rather than a report discrepancy. All four presentation/evidence combinations show the same consistency, with four cases per combination.

In the associated cases, related-event reports moved 30 points from 0.5 after a definitive growth audit, but only 15 points after an imperfect signal. That smaller change was exactly implied by the respondent's earlier conditionals and its remaining growth uncertainty. It is not evidence of slow updating. Independent archives appropriately produced no indirect related-event change.

These are consistency and extraction observations. The authored cases always resolve growth in the signal's direction; they cannot estimate out-of-sample instrument accuracy or calibration from those final outcomes. The archive proportions are finite empirical evidence, not disclosed population likelihoods or uniquely mandatory Bayesian posteriors. There is no negativity/framing contrast, population norm or decision-quality comparison here.

## Fitted explanation and its limits

All four declared model families tie at the same parameter values:

| Parameter | Selected grid value |
| --- | ---: |
| Summary association scale | 1.0 |
| Records association scale | 1.0 |
| Signal weight | 1.0 |
| Propagation fraction | 1.0 |
| Auxiliary report adjustment | 1.0 |

Each family fits all 112 modeled observations with 0-point RMSE and rounded-report log likelihood −204.1833. Each has one maximizing grid point, but the full, shared-representation, full-propagation and immediate-report families overlap at that point. The tie does not discriminate internal mechanisms. The selected-model structural-identifiability flag is not a calibrated uncertainty statement. Both `model_parameters_are_passport_traits` and `empirical_predictive_validation` remain false; no empirical held-out prediction was tested.

Together with the [0.1 acceptance](auxiliary-acceptance-2026-09-23.md), this gives us a useful control result: the evaluated configuration can extract explicit numerical relationships, interpret this uncertain measurement and maintain the elicited relationships through later reports. We should stop expanding these arithmetic controls merely to seek a difference. The unresolved measurement problem is now how expectations are constructed from richer narratives and competing causal explanations. That is a development priority suggested by the contrast, not a cause established by this run: the richer investigation uses different tasks, scaffolding and configurations.

For the passport, the defensible statement is a scoped capability observation under these conditions. A good in-sample fit does not justify a general trait, an intervention recommendation or increased authority. Human acceptance and the owned-identity provider flow remain separate product work.

## Usability

All eight record-format contexts mentioned that repeating the complete archive made new evidence harder to scan or was otherwise cumbersome. Two summary/backlog contexts mentioned an unnecessary reference to an initial bulletin in the instrument description. The other six contexts reported no significant friction. This is qualitative feedback from one configuration, not an independent estimate of human burden.

The next interface revision should distinguish new evidence from retained background, preserve access to the full archive/history and remove the irrelevant cross-target wording. Any effect on task exposure needs version review. Nothing was changed during this collection. The existing human session was untouched, and a separate synthetic browser preview was closed after inspection. Actual human completion remains pending.

## Execution and cost record

The requested configuration was `gpt-6-astra`, medium reasoning effort, Codex CLI 0.155.1, using existing signed-in account authentication. The immutable model revision was not independently verified. Each case used a fresh ephemeral process, a temporary working directory, excluded saved user/project context, a read-only sandbox and only the five assigned MCP tools. Shell, browsing, plugins and further agents were disabled. Context continued within each case. This remains **operator-asserted execution**, without independent environment or model attestation. The setup follows the [official non-interactive execution documentation](https://learn.chatgpt.com/docs/non-interactive-mode).

The private plan and configuration were committed before the first respondent, with one attempt per case, five minutes per attempt and twenty minutes overall. Collection ran **09:59:14.416–10:11:00.107 UTC**; monotonic elapsed time was 705.670 seconds. All 16 distinct recorded contexts completed. There were 192 MCP calls: 16 descriptions, 16 history reads, 80 trial reads, 64 submissions and 16 completions. No case was excluded or retried, and no attempt has unknown usage. The only recorded CLI diagnostics were warnings that the feature used to skip host skill discovery was under development.

| Resource | Recorded usage |
| --- | ---: |
| Input tokens, including cached input | 2,441,650 |
| Cached input, already included above | 2,071,936 |
| Noncached input | 369,714 |
| Output tokens | 8,593 |
| Total processed input + output | 2,450,243 |

Marginal dollar cost is unknown under account billing. These figures include the respondent harness and repeated context; they are not a price quote for a paid evaluation service. The eventual service quote must distinguish evaluator fees from participant inference responsibility.

## Reproducibility boundary

The audit checked all planned assignments, 64 accepted answers, 16 distinct contexts, allowed-tool completions, chronology after the frozen plan, exact analysis derivation and unchanged implementation. It also checked the original 0.1 evaluator fingerprint remained unchanged. Source checks passed: 266 Python tests and 37 TypeScript tests; the browser/MCP tests use synthetic responses and the existing Solana RPC tests remain mocked. No live registry read, transaction or payment was made in this increment.

Raw prompts, answers, databases and execution logs stay private and ignored by Git. The following hashes commit to file bytes, without making private artifacts publicly reproducible or independently timestamped:

| Artifact | SHA-256 |
| --- | --- |
| Implementation fingerprint | `231248e45c2433a5c22077043746cfe5b2f892f1880d5e2ad39a229dfe0dee95` |
| Precollection run manifest | `ce108089ead6cbd94a90acebfe99feae8d865884e9f10efaf4bf4190e27b7c14` |
| Configuration | `541e55ec7f75c7b39e193963700046c55978a86e7fa7b102ca46705a9e5fb040` |
| Execution record | `1647fe33c83aa07838321d026e63e0ef450aa3ad844b69a43031195f66fb3df2` |
| Collection manifest | `42dee59d1aa13dcab0ccb42a016e0d2ead4f01229932a05262cbd2f83abe158e` |
| Exported report | `a0bf6de1f990557c773c34e344aef295ac22841dd24a9d97d878857b03f7e172` |
