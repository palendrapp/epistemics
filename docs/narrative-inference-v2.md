# Narrative inference 0.2: independent corroboration and research choice

Version 0.1 revealed a design limitation: the pipeline audit was most informative under every collected report, so consistently choosing it could not distinguish adaptive research from an always-pipeline rule. Version 0.2 changes the evidence that informs the initial interpretation, aiming to create useful opportunities for **both** audits. It also fixes the checkpoint-numbering mismatch. Original task versions and their repeat data remain frozen.

## Design change

Eight cases cross two domains, two directions and two corroboration conditions. Every case uses prose. Within each domain/direction pair, the basic story and final resolutions match; the independent check differs:

- **Demand corroboration:** an external reviewer checked customer confirmations and underlying records for a substantial subset. Most reviewed accounts showed the defined demand change.
- **Artifact corroboration:** an external reviewer reproduced the pipeline problem on a substantial subset; reconstructing those records changed its apparent growth by at least five points in the relevant direction.

Both checks are explicitly partial, fallible and not guaranteed representative. Neither resolves either event for the full cohort. These are substantive evidence differences, **not framing contrasts**. There are no supplied likelihoods, reliability frequencies or normative starting probabilities. The agent must interpret the check, make initial joint reports and predict the dashboard under each event combination.

The four stages and answer burden remain: background/forecasts, dashboard/research choice, chosen audit, final resolution; **32 checkpoints, 160 probability entries and eight choices**. Audits are free and definitive within the task; the declared research objective is uncertainty reduction about the joint state, not profit or decision utility. Stop remains available but has zero information value. No stop preference is measured reliably by this design.

The initial note's uncertainty is explicitly dated before the independent check, avoiding a simultaneous claim that the reproduced problem is unconfirmed. Instructions refer to named stages. The public `checkpoint` field is 1–4, and trial IDs use opaque stage names. The browser and MCP retain only-new-document presentation with accepted history available. No response or query can be revised after acceptance; retries remain idempotent.

## Analysis and coverage

The joint-state consistency references, rounding sensitivity, zero-support handling and three-parameter conditional report model are unchanged from [0.1's mathematical specification](narrative-inference.md). The same fixed-grid least-squares families are reported. No internal priors, causal graphs, posterior intervals or general traits are recovered by this procedure. A corroboration effect enters through elicited initial reports and likelihood expectations; this revision does not fit a separate reliability-learning coefficient to the prose.

New matched contrasts report demand-corroboration minus artifact-corroboration differences in initial and post-signal demand/artifact marginals, plus the two research choices. Later update consistency is evaluated within each case rather than treating different selected audit results as matched evidence.

For a definitive binary query Q, information value remains **H(Q)** under the preceding joint report. The new coverage report counts which audit is more informative by over 0.01 bits, counts observed choices, and compares mean foregone information for the actual choices with fixed demand, fixed pipeline and stop policies. This comparison uses reported uncertainty and the declared task objective; it does not establish an optimal policy under a known population distribution.

The bounded acceptance criteria are declared before collection:

1. At least two reports favor the demand audit by more than 0.01 bits.
2. At least two favor the pipeline audit by more than 0.01 bits.
3. Both audits are chosen at least once.

Failure of 1 or 2 is a task-coverage finding, not an agent deficit. Failure of 3 limits observed branch coverage and does not by itself identify a cognitive preference. All cases, criteria and fixed-policy comparisons are retained, with no adaptive replacement. Even passing these checks does not identify a unique search algorithm: an opposite-of-corroboration heuristic may make the same choices.

## Versions and validation

The separate module is `epistemics.narrative2`; battery `narrative-inference/0.2.0`, evaluator `narrative-evaluator/0.2.0`, analysis `narrative-analysis/0.2.0`, and collection/trial/report schemas v2. Its fingerprint binds its own files and the frozen narrative helpers it imports. Earlier fingerprints and the main report contract are unchanged.

Synthetic inputs now vary which marginal is strongly supported (0.82–0.94 before rounding), while the other ranges from 0.35–0.60; the audit is chosen from the resulting signal posterior. These numbers are evaluator-side synthetic generators, **not facts shown to respondents or validated interpretations of the stories**. Both research branches are represented. Six declared parameter profiles, 16 noisy repetitions each, the same noise/rounding process, separate new-input predictions, nonidentifiability checks and out-of-family checks are retained.

| Synthetic check | Seed 20260924 | Seed 20260925 |
| --- | ---: | ---: |
| Datasets | 96 | 96 |
| All six clean profiles uniquely recovered | Yes | Yes |
| Signal-weight MAE | 0 | 0 |
| Dependence-retention MAE | 0.002604 | 0.005208 |
| Report-adjustment MAE | 0 | 0 |
| Mean new-input latent prediction RMSE, points | 0.004136 | 0.006718 |
| Zero-adjustment nonidentifiability exposed | Yes | Yes |
| Both audit branches in synthetic inputs | Yes | Yes |
| Incompatible-pattern best-fit RMSE, points | 33.307 | 32.863 |

Both runs pass the inherited gates: parameter MAE ≤ 0.1, mean new-input latent prediction RMSE ≤ 1 point, exact clean-profile recovery, exposed α = 0 ambiguity and incompatible-pattern RMSE ≥ 8. These results are conditional on coarse-grid synthetic generators and small report noise; they do not validate real-agent mechanisms or off-grid parameter recovery.

Tests exercise the actual MCP transport, whole-collection local HTTP flow, concurrent retries, accepted query immutability, selected-audit disclosure, exact trial reconstruction, schema snapshots, research coverage and preservation of previous evaluator fingerprints. Synthetic browser interaction additionally checked probability-total validation, named stages, chosen demand-audit display and retained history. Actual human usability requires a human participant.

## Local use

```sh
uv run python -m epistemics.narrative2 create \
  --directory output/private-narrative2 --participant output/participant.json
uv run python -m epistemics.narrative2 serve --directory output/private-narrative2 --port 8774
uv run python -m epistemics.narrative2 export --directory output/private-narrative2
uv run python -m epistemics.narrative2 schema
uv run python -m epistemics.narrative2 validate-synthetic \
  --seed 20260924 --repetitions 16 --output output/narrative2-recovery.json
```

The assigned MCP server is `python -m epistemics.narrative2.mcp_server`, with private `EPISTEMICS_NARRATIVE2` and `EPISTEMICS_ASSIGNMENT` values supplied by the evaluator. The default local browser port is 8773; choose a separate free port when preserving an existing human session. Public hosting, tenant isolation and a narrative passport issuance adapter remain outside this module. Human participation is private and wallet-free.
