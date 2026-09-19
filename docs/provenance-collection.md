# Sequential provenance collection

`provenance-collector/0.1.0` supplies a persistent, sequential MCP interface for the [provenance pilot](provenance-pilot-v1.md). It uses the same public checkpoints and response model as the synthetic validation. Each server is assigned exactly one company episode by the operator. The participant cannot choose the seed, variant, partition, next index, configuration identity or response origin through MCP.

## Freeze a collection

Create a fresh design with the current implementation, then prepare a collection specification using [the example](../examples/predictive-collection-spec.json):

```sh
uv run epistemics predictive create --output output/provenance-design-current
uv run epistemics predictive validate-synthetic --design output/provenance-design-current --output output/provenance-validation-current.json
uv run epistemics predictive bind --design output/provenance-design-current --spec PRIVATE_SPEC.json --output output/provenance-collection
```

The operator fills in participant identity, model/configuration metadata, origin, allowed tools, assistance, execution notes and the scope of the configuration hash. Hash a documented configuration artifact; do not imply that a hash of a short launch prompt covers unknown provider settings or hidden system instructions. `agent`, `human` and `synthetic` origins remain distinct. Metadata is explicitly operator asserted and execution is not independently verified.

Declare every assignment before collection. `full_pilot` requires all design assignments in their original order: 72 episodes / 360 checkpoints per configuration at one replicate. `transport_smoke` allows an explicitly chosen subset and remains labeled as such in the export. A completed smoke subset is not a completed balanced pilot. Collection specifications cannot quietly drop failed or unattempted assignments.

The collection owns an exact-byte copy of the design and a separate frozen participant manifest. Their hashes are bound into the response database. A changed participant/configuration, modified design, changed instructions, different source fingerprint or missing database prevents continuation. This is drift detection, not protection against an operator who can rewrite all files and software. Existing design files remain unchanged; designs created with an earlier source fingerprint require that original implementation.

## Run one fresh respondent per assignment

The MCP server is `python -m epistemics.predictive.mcp_server`, configured with `EPISTEMICS_COLLECTION` and `EPISTEMICS_ASSIGNMENT`. [Example MCP configuration](../examples/mcp-predictive.json). Start a fresh respondent context for each assignment, retain context within that episode, and expose only this server's public tools:

- `describe_battery()` supplies instructions and the answer schema.
- `get_trial()` returns the current evidence prefix and accepted public history.
- `submit_answer(checkpoint_id, answer)` accepts a probability and `act`/`defer` decision.
- `finish_evaluation()` returns a completion receipt after every checkpoint is answered.

For a respondent operating through a shell tool, a transport-only JSON-lines bridge connects to the **real MCP server**:

```sh
uv run epistemics predictive client --collection output/provenance-collection --assignment ASSIGNMENT_ID
```

The bridge prints protocol/tool definitions. Send one JSON request per line:

```json
{"tool":"get_trial"}
{"tool":"submit_answer","arguments":{"checkpoint_id":"ASSIGNMENT_ID:0","answer":{"probability":0.5,"decision":"defer"}}}
{"tool":"finish_evaluation"}
{"close":true}
```

The answer above illustrates syntax only; the respondent supplies its own answer to the displayed checkpoint. Finish only after the server reports all answers accepted. The bridge contains no answer-generation logic, provider API, automated inference runner or payment integration.

SQLite transactions serialize submissions. Identical retries return the original timestamped receipt, including after restart/completion. Conflicting retries and future-checkpoint submissions fail without advancing the episode. On restart the server returns only previously accepted material plus the current checkpoint; it never re-elicits accepted responses. This restores the visible record, not the provider's hidden context or state. Source/reference probabilities, evaluator parameters, seeds, partitions and other assignments are withheld throughout the participant interface, including after finishing.

Every MCP process records an attempt and its restored-answer count. An attempt left `open` may indicate interrupted execution; a `closed` transport does not imply a completed episode. Operator status shows incomplete and unattempted cases. Attempts are retained even when a later connection resumes successfully. These records do not independently verify which model generated the answers.

The server protects the protocol boundary. A local respondent with filesystem or shell access can still inspect private evaluator files if allowed to do so. A fresh subagent instructed to use only the bridge has fresh conversational context, not an OS sandbox or independent execution attestation. Production collection needs appropriate process/filesystem isolation and provider/configuration verification.

## Inspect and export

```sh
uv run epistemics predictive status --collection output/provenance-collection
uv run epistemics predictive export --collection output/provenance-collection --output output/provenance-responses.json
uv run epistemics validate output/provenance-responses.json
```

Export is operator-only and requires every predeclared assignment to finish. It snapshots the participant/configuration binding, every accepted checkpoint/answer with timestamps, assignment metadata and attempt history. The database retains exact export bytes for repeatable retrieval; output file creation refuses overwrite. Once exported, no new transport attempts can start. An export made with an open transport retains that then-open status in the snapshot, even if the process subsequently closes.

These private exports contain evaluator assignment details and must stay outside Git and participant tool responses. Schemas are `predictive-collection-spec.v1`, `predictive-collection.v1` and `predictive-responses.v1`. Structural JSON validation does not authenticate execution. Exports are not passports or accepted signing inputs. The exporter neither fits partial cases nor promotes a smoke test to a phenotype.

## Version review and acceptance

This addition versions collection separately. Public task stimuli, payoffs, response fields and analysis equations remain `provenance-pilot/0.1.0` / `provenance-analysis/0.1.0`; additional public instructions describe sequencing and retries. Shared core, report.v1–v4, passports and signature domains remain unchanged. The source fingerprint intentionally changes, requiring fresh designs for this implementation.

Offline checks cover immutable answers, concurrent submissions, resume, withheld future information, premature completion/export, origin and configuration binding, source/design drift, retained attempts, exact export bytes and real MCP stdio round trips. Synthetic parameter recovery and structural holdout checks are rerun; a real transport smoke test is reported separately from them.

The [20 September fresh-context smoke test](provenance-smoke-2026-09-20.md) completed one predeclared matched pair: two respondents, 12 accepted checkpoints and two successful MCP closures. It supplies a descriptive probability contrast, not a full profile or predictive-validity claim.

Before empirical predictive validation, cost and freeze a complete multi-configuration run, including prediction baselines, uncertainty, failure handling and success criteria. Keep final evaluation cases unused during development. Then execute profile/policy/final comparisons and the separately planned assistance experiment. Transport success alone supports no claim about general cognitive traits, individualized prediction or intervention benefit.
