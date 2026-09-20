# Shared core evaluation — 0.1

The browser and a dedicated stdio MCP adapter now use one session engine. Core 0.1 contains **34 checkpoints: 10 company-discovery checkpoints followed by 24 independent probability-calibration questions**. Completion produces a participant-neutral `epistemics.report.v4` and a readable `epistemics.passport.v2` draft. Both human and agent records use the same measurement and interpretation rules.

This is the first shared workflow. It is not a complete phenotype: one company case cannot identify general source-framing, negativity or causal-inference traits. The initial release makes that limited coverage visible. A [fresh-agent acceptance run](core-acceptance-2026-09-20.md) completed all checkpoints with timing/cost and usability feedback. Actual human usability and repeatability remain pending.

## Try the human interface

```sh
uv sync --locked
uv run epistemics serve
# Open http://127.0.0.1:8765
```

The service binds only to loopback. The browser provides the shared instructions, an unscored probability-scale example, optional pseudonym, tools/assistance declarations, current evidence, probability and growth-quantile controls, decisions, progress and accepted-answer history. There are no prefilled probability defaults. The browser displays probabilities as percentages and submits the corresponding values in `[0,1]`; growth percentiles remain growth percentages, including negative values.

Accepted answers are final. Closing the tab pauses a run; return using the same hostname and browser cookie to resume. Unsubmitted form contents are not saved. Keep the cookie private: it is a bearer capability. The default SQLite file is `.epistemics/live.sqlite3`; use `--database PATH` to choose another. The database retains incomplete runs and accepted answers. The UI allows another session after completion, without deleting the previous run; download its artifacts first. There is no session listing or account recovery interface in this local release.

The results page links to an HTML passport and downloadable passport JSON, Markdown and exact-byte report JSON. No report or passport is available before all 34 answers. Downloads remain private unless the participant chooses to share them. The full report contains resolved outcomes, assignment seed, all public materials and answers.

For automated interface exercises, run a separate database with `--synthetic-demo`. Every response collected by that server is explicitly labeled synthetic, including browser form entries. A browser-shaped record does not establish human authorship. Default-server human metadata is also operator-asserted, not independently verified.

## Connect an agent

```sh
uv run python -m epistemics.live.mcp_server
```

Use [the dedicated MCP configuration](../examples/mcp-core.json), replacing its paths. This is separate from the original `epistemics-mcp` server; existing batteries and their five-tool API remain available unchanged. The core adapter exposes:

1. `describe_battery()`: the shared guide, practice example, composition and protocol digest.
2. `start_evaluation(participant, request_id, instructions_accepted, conditions?)`: supply an agent participant with actual configuration metadata and a random request ID of 16–128 characters. Read the guide first. Reuse the same ID and metadata only for a retry. Seeds, assignments and scoring controls are evaluator-side.
3. `get_trial(session_id)`: current public trial, progress, declared conditions and accepted-answer history. `trial.payload` contains the discovery or calibration task. Use the enclosing `trial.trial_id` when submitting.
4. `submit_answer(session_id, trial_id, answer)`: discovery answer or numeric `probability`; identical retries return the original receipt. Conflicting retries cannot change accepted answers.
5. `finish_evaluation(session_id)`: completed report, exact serialized `report_json` string and draft passport. **Write `report_json` verbatim as UTF-8, including its final newline**, to preserve the passport's source hash. Reserializing the parsed `report` object changes those bytes.

`EPISTEMICS_LIVE_DB` selects the database. The MCP adapter records interface `mcp` and agent response origin; the human adapter records `browser` and human origin. `EPISTEMICS_SYNTHETIC_RESPONSES=1` marks MCP test responses synthetic. Unknown tools/assistance remain `null`; explicit absence is `[]`. The protocol has continuous context, no imposed time limit, and elapsed wall time including pauses. Both adapters expose the same task content, order, response semantics and previous answers for a given private seed. Visual controls and transport necessarily differ; shared scoring does not establish identical internal mechanisms.

## Composition and version review

| Component | Release decision |
| --- | --- |
| Protocol | `passport-core/0.1.0`, separate from all existing batteries |
| Evaluator | `shared-evaluator/0.1.0`; old package/evaluator contracts are unchanged |
| Order | Discovery first, then calibration; no outcome feedback between modules |
| Assignment | Domain-separated evaluator-side seeds for the existing generators |
| Materials | Existing discovery sources/documents/analogues and original balanced 24-question prior/sensor grid |
| Instructions | Plain-language discovery and calibration instructions shared across adapters; protocol guide and practice are hashed |
| Timing | Untimed; start-to-final-answer wall time recorded, including pauses |
| Interpretation | `passport/0.2.0`, `passport-interpretation/0.2.0`, schema `epistemics.passport.v2` |
| Compatibility | Legacy v1–v3 reports, passport.v1 and their original entrypoints remain unchanged |

Reworded instructions, combined order and delayed feedback are experimental changes. They receive a new protocol rather than silently changing existing sessions. The protocol digest covers core code/assets and the reused generation, inference and passport code. Active runs reject a changed evaluator; finish a run using its original code. A running service also rejects new runs after its files change: restart to load the new code. Completed report/passport bytes are persisted and subsequent downloads are identical. Reproducing their derivation requires the original interpretation code. Do not modify the evaluator while collecting a run.

The first composition deliberately limits participant burden while exercising both discovery and disclosed-likelihood updating. It omits the 48-step reversal task and six-company disclosed-model pilot. Additional cases and matched contrasts are still needed to separate source impressions, valence, updating and output effects. No estimate of completion time or human/agent norms is claimed yet.

## What the passport can say

| Dimension | Core evidence and interpretation | Limit / candidate support |
| --- | --- | --- |
| Evidence weighting | Fit reported log odds as an intercept plus weighted prior log odds and signed sensor log likelihood ratio. Weights of 1 match the disclosed Bayesian reference. Summaries use within-run bootstrap intervals. | Arithmetic and comprehension may affect weights. A below-reference evidence weight can suggest an **untested** evidence ledger; it does not prove the mechanism or benefit. |
| Source judgment | Source-accuracy reports at checkpoints 0 and 6, with audit/history examples. | Other information arrives between those probes; no isolated audit or framing effect is identified. |
| Revision and persistence | Changes in reported growth probabilities across the discovery sequence and conditional observer comparisons. | One authored case; competing explanations are retained. No general conservatism or negativity parameter. |
| Dependence and causal reasoning | Behavior after the derived model and provenance disclosure; conditional no-disruption probes. | Observed responses and conditional reference models, not a uniquely identified causal reasoning trait. |
| Uncertainty and calibration | Separate Brier/reference scores for 24 numeric cases and one discovery outcome; growth-interval reports. | Ten discovery checkpoints are not ten independent outcomes. No pooled calibration diagnosis or population ranking. |
| Decision consistency | Invest/hold compared with reported probabilities under the supplied linear payoffs. | Task-specific consistency, not investment performance or a general preference diagnosis. |

All six sections remain provisional or insufficiently supported where applicable. No overall score, certified identity, treatment effect or general cognitive diagnosis is produced. Probabilities are elicited behavior, not direct access to internal beliefs. Every measurement/example points into the exact source report; the passport's derivation can be checked with:

```sh
uv run epistemics passport verify PATH/passport.json --report PATH/report.json
uv run epistemics passport create --report PATH/report.json --output output/core-passport
```

The core report binds response origin at collection; passport import cannot relabel it. Imports check structure and deterministic derivation, not honest execution. Agent core passports can receive a separate [offline issuer attestation](passport-attestation.md), preserving their exact bytes and provisional scope. The legacy report/Memo client still accepts v1–v3 only. The [local machine consumer](machine-consumer.md) adds registry reads, signed status and task decisions. Public deployment and paid services remain roadmap work; human profiles remain private.

## Validation and local boundary

Offline tests cover known prior/evidence/intercept recovery on three seeds and three response policies, the synthetic discovery observer, equivalent human/agent service responses, real stdio MCP completion, actual loopback HTTP completion, session resume, concurrent retries, hidden-state boundaries, malformed requests, browser probability conversion and exact-byte passport derivation. These are synthetic software checks, not a human study or a fresh model evaluation. HTTP integration tests require permission to bind a loopback port; they contact no external service.

The HTTP service serves only allowlisted assets/routes, uses an HttpOnly same-site cookie, guards Host/Origin and JSON mutations, and does not log answers or session IDs. It is a local single-machine tool, not a hosted multi-tenant deployment. Anyone with evaluator filesystem access can inspect hidden state; isolate that access for serious agent evaluations. Subject identity, configuration claims and execution remain separate operator assertions. No RPC, validator or chain submission is involved in this workflow.

The first fresh-agent product check is complete; an actual human should next complete core 0.1, review the passport and report unclear questions, burden and usefulness. Together with repeated agent runs, these checks should guide the next composition and interpretation revision.
