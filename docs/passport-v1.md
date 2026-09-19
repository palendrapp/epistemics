# Local draft passport 0.1

This release implements the first [roadmap milestone](mvp.md): shared human/agent metadata contracts, a draft passport contract and deterministic readable profiles derived from existing completed evaluation reports. It does not yet run a new core battery or accept live human sessions.

## Create a passport

From a completed agent evaluation:

```sh
uv run epistemics passport create --report output/report.json --response-origin agent --output output/passport
uv run epistemics passport verify output/passport/passport.json --report output/report.json
```

Open `output/passport/passport.html` locally. The same directory contains `passport.json` and `passport.md`. Creation refuses to overwrite an existing destination. No source report is modified or copied into that directory, no files are uploaded and no signing or chain transaction occurs.

For a self-contained synthetic demonstration:

```sh
uv run epistemics demo --evidence-weight 0.4 --output output/passport-demo-source.json
uv run epistemics passport create --report output/passport-demo-source.json --response-origin synthetic --output output/passport-demo
```

Legacy reports do not distinguish synthetic responses from agent responses. The origin flag is an operator assertion, not a verification mechanism. Omission yields `unspecified`, prominently displayed; use `synthetic` for demo/recovery output. Imports preserve the source's agent identity and cannot relabel responses as human.

To render or structurally validate an existing passport:

```sh
uv run epistemics passport render output/passport/passport.json --format html --output output/passport-copy.html
uv run epistemics validate output/passport/passport.json
uv run epistemics validate examples/human-participant.json
uv run epistemics schema
```

`render` validates structure only; it does not check source provenance. `verify` checks the source's exact byte digest and reconstructs the deterministic interpretation, including identity, measurements, evidence pointers and candidate supports. It does not verify execution, origin, the source's scientific correctness, an issuer signature or on-chain inclusion. The generated timestamp is metadata, not an authenticated time.

## Contracts

| Contract | Purpose |
| --- | --- |
| `epistemics.participant.v1` | Discriminated human/agent metadata. Humans need only a pseudonymous subject ID; agents additionally require model revision and configuration digest. |
| `epistemics.session-context.v1` | Common public metadata: participant, protocol, recorded conditions, completion, timestamps and response origin. Contains no evaluator seed, hidden truth or future tasks. |
| `epistemics.passport.v1` | One completed source report, six profile dimensions, evidence pointers, source byte digest and optional untested supports. Always a private, unsigned draft with partial profile coverage in this release. |

Python models live in `participants.py` and `passport/models.py`; `epistemics schema` exports their schemas alongside the unchanged legacy schemas. This document describes the original single-report passport release. The subsequent [core 0.1 release](live-core.md) adds shared live collection through browser and MCP, using report.v4 and passport.v2. Human interpretation thresholds remain unestablished.

Missing condition metadata is represented as unknown (`null` or `unspecified`), not inferred. In particular, importing an agent report does not establish which interface or tools were used. Existing report versions, source bytes, task generation, fitting methods and record signatures are preserved. New interpretation behavior is versioned as `passport-interpretation/0.1.0`; the battery/evaluator versions remain unchanged because this release does not change experimental behavior.

## Interpretation coverage

| Source | What the draft can say | Material limit |
| --- | --- | --- |
| `report.v1` — original battery | Prior/evidence and source update weights, sequential model comparisons and task forecast scores | Numeric likelihoods are disclosed; no dependency or decision probes. Within-run intervals do not establish repeatability. |
| `report.v2` — company pilot | Conditional positive/negative weights, source/auxiliary revisions, redundant-item responses, interval performance and decision agreement | Six company outcomes, fixed output assumptions; rank-deficient weight fits do not receive directional interpretations. |
| `report.v3` — discovery case | Observed source revisions, provenance/derived-document responses, observer comparisons, final forecast and decisions | One case/outcome; no evidence-weight, stable source-bias or general calibration diagnosis. |

Every dimension is provisional or insufficiently measured. Numeric reference values come from the source's declared model or task definition; no population percentile or aggregate quality score is introduced. Comparison to reference 1 uses displayed precision of 0.001, not a validated clinical or population threshold. Source bootstrap intervals are displayed with their original scope. A weight whose interval spans 1 is not labeled under/overweighting.

Example selection is explicit: the original evidence task shows its largest reference discrepancy; the company dependency section shows its largest redundant-item change; other company examples use the first episode; discovery examples use the protocol's fixed audit and provenance checkpoints. Discovery source estimates are probed initially and at the audit, so their difference includes intervening evidence. Observer comparisons are not unique diagnoses of cognitive mechanisms.

The first untested support rule suggests an evidence ledger when the original battery's evidence weight is below reference to displayed precision and its within-run interval is wholly below 1. This is a candidate selected under the fitted model, not evidence that the intervention helps. No intervention benefit estimate is produced.

The v1 passport adapter accepts one v1–v3 report at a time. The CLI also supports core v4 reports through a separate passport.v2 adapter. Neither combines configurations or aggregates sessions. Matched-study profiles need their manifest/episode context and are not imported. The existing Solana signer accepts legacy reports only, not either passport format. Publishing and identity association remain roadmap work.

## Privacy and inspection

The rendering contains subject/configuration identifiers, selected response/outcome observations and profile measurements. It omits full prompts, transcripts, private world states and source paths. These summaries can still be sensitive; output remains local and private by default. Evidence pointers resolve against the separately retained source report, whose SHA-256 binds exact bytes including whitespace.

HTML is standalone, escapes imported strings, contains no scripts or remote assets, and uses a restrictive content policy. JSON and Markdown provide inspectable alternatives. The tests cover both participant kinds, invalid session metadata, all three adapters, known synthetic tendencies, interpretation ambiguity, target-probability complements, tampered bytes/descriptions, rendering and CLI overwrite protection.
