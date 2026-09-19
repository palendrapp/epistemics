# Discovery case through MCP

Select `battery="discovery"` in describe_battery and start_evaluation. Use actual available agent metadata, explicitly unknown serving details where appropriate, and a configuration hash with its scope recorded. Do not choose evaluator seeds or inspect source, databases or completed reports during an unfamiliar-subject evaluation.

The case has ten checkpoints. Use get_trial to obtain the current dossier and currently available documents. Source archives describe resolved historical measurements; the current company's state and eventual outcome are hidden.

Answer the current requested event, which can be growth >12% or growth ≤12%. Quantiles always concern revenue growth itself in percentage points. Investment always pays +2 for growth >12%, otherwise -1; holding pays zero.

```json
{
  "target_probability": 0.55,
  "growth_quantiles_pct": {"p10": 4.0, "p50": 12.5, "p90": 20.0},
  "decision": "invest",
  "evidence_ids": [],
  "source_accuracy": {},
  "conditional_growth_probability": null,
  "extracted_values": {},
  "alternative_explanation": null
}
```

This is only the answer shape, not an answer to a trial. Fill source_accuracy with exactly source_probe_ids when requested: the probability of a future raw estimate falling within two points of its audit. For conditional_probe=true, answer the explicitly stated growth >12% conditional. Include exactly extraction_keys in extracted_values. Use empty objects/null otherwise. Cite available document IDs only, without duplicates. An optional short alternative explanation is retained without private reasoning-trace requirements.

Submit the answer with session_id and the current trial_id. Accepted answers cannot be revised; identical retries return their original receipt. Repeat until all ten checkpoints finish, then call finish_evaluation to receive the v3 report. Record exact artifact bytes before signing/hashing. The report's observer fits are conditional model comparisons, not an answer key that establishes a unique rational assessment.
