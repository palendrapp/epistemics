# Shared source-learning instructions, version 0.2

The 26 September panel found repeated confusion about research scope, the accuracy quantity, provisional decisions and where to find resolved outcomes. The browser already supplied some descriptions absent from MCP. `source-learning/0.2.0` now provides one clarified public protocol to both interfaces, without changing the generator, source mechanisms, available checks, prices, answers or inference engine.

## What changes

Before purchase, every research option states what it reveals. A customer check accurately records five new, independent, randomly sampled customers; it is **not an oracle for company demand**. A selection audit reveals the recurring source's exact selection rule. A measurement audit reveals its per-customer recording accuracy. Both audits apply to past and future reports from that source, without revealing an unpurchased source property in advance.

The diagnostic definition distinguishes per-customer recording accuracy from company demand and sample representativeness. Each checkpoint explains whether the decision is provisional or final. Stop still leads to a final checkpoint with no new evidence. A successful final-answer receipt now includes that company's outcome; a provisional-answer receipt does not. Identical retries return identical feedback, even after later answers.

Structured and packet MCP presentations remain available. The browser uses the structured presentation and the same definitions. All original history remains accessible. This increment retains the packet's full history; it does not claim to have solved long-packet reading burden.

## Versions and evidence

The implementation lives in `epistemics.source_delivery`. The original `source_learning` and `source_panel` implementations, fingerprints, reports and active human sessions are unchanged. The base `source-learning-report.v1` remains a **canonical factual ledger**, not evidence that the respondent received the old wording. New collections require their separate `source-delivery-evidence.v1` artifact, binding:

- The exact public description, presentation, canonical manifest and implementation before collection.
- Every rendered checkpoint and digest before the corresponding answer.
- The deterministic post-answer resolution associated with each accepted index.

The report and delivery evidence must travel together. The public descriptions contain no evaluator seeds, unselected audits, future company outcomes or model predictions. Transport reconstruction is operator evidence, not proof of model execution. The fourth completion question checks whether the participant understands that the independent panel is fallible about demand.

Experimental behavior may change because explanations and feedback are more explicit. Old and new responses must not be pooled as equivalent conditions. Synthetic recovery reuses the unchanged generator/inference assumptions and cannot simulate a psychological wording effect. Fresh respondent acceptance checks the revised path and comprehension; it cannot establish that the changes improve decisions.

## Commands

```sh
uv run python -m epistemics.source_delivery create \
  --directory output/source-delivery \
  --participant path/to/private-participant.json --condition sparse
uv run python -m epistemics.source_delivery serve \
  --directory output/source-delivery --port 8777
```

MCP: command `uv`, arguments `run python -m epistemics.source_delivery.mcp_server`, environment `EPISTEMICS_SOURCE_DELIVERY` pointing to the private collection directory. Only the five public collection tools are exposed. `--presentation packet` selects prose when creating an MCP collection; the browser requires structured presentation.

After finishing:

```sh
uv run python -m epistemics.source_delivery export --directory output/source-delivery
uv run epistemics passport bundle-source \
  --directory output/source-delivery --output output/source-delivery/source.json
uv run epistemics passport create \
  --report output/source-delivery/source.json --output output/source-delivery/passport
uv run epistemics passport verify output/source-delivery/passport/passport.json \
  --report output/source-delivery/source.json
```

Use a new output directory for each collection. The original interfaces remain available for their existing sessions; no existing human answers should be fabricated to complete acceptance.
