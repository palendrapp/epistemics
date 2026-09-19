# Company pilot through MCP

Call describe_battery with `{"battery":"company"}`. Start a new evaluation with the same battery selector and your actual AgentDescriptor. The descriptor includes agent ID, model/revision, configuration fingerprint, declared context policy and optional temperature. Do not invent unavailable serving details or substitute a synthetic reference agent for a real respondent.

```json
{
  "battery": "company",
  "agent": {
    "agent_id": "your-agent-id",
    "model": "your-model",
    "model_version": "your-version-or-explicitly-unknown",
    "configuration_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "context_policy": "continuous",
    "temperature": null
  }
}
```

Replace the example fingerprint with a hash of the recorded configuration and document its scope. Keep the returned session_id private. Seeds and outcome states are evaluator-side only.

Repeatedly call get_trial with the session_id. There are six independent company episodes and nine checkpoints per company: step 0 is the initial dossier, steps 1–8 each add one evidence item. The full currently available evidence is returned each time; no future documents are returned. Episode instructions do not reset the model's context: the host must perform any declared reset.

Call submit_answer with session_id, the exact current trial_id, and this answer shape (values below are merely illustrative):

```json
{
  "growth_probability": 0.55,
  "margin_probability": 0.45,
  "temporary_probability": 0.2,
  "source_probability": 0.7,
  "growth_quantiles_pct": {"p10": 3.0, "p50": 12.0, "p90": 20.0},
  "decision": "invest",
  "evidence_ids": []
}
```

- Growth and margin refer to the fixed next-year targets in the dossier.
- Temporary probability refers to the company-wide implementation-disruption state.
- Source probability refers to whether management is the informative source type. It does not refer to the current document's accuracy or to the independent auditor's reliability.
- These four events can coexist; their probabilities should not be forced to sum to one.
- Quantiles are revenue growth in percentage points, not decimal fractions. They must be ordered.
- The decision is invest or hold under the stated hypothetical gain/loss contract. Each checkpoint is a separate decision; positions do not accumulate.
- evidence_ids can cite only documents currently available, without duplicates. Use an empty list at step 0.

Each accepted answer is immutable. Exact retries return the original receipt. Neither receipts nor active trials reveal outcomes, posterior reference answers, fitted parameters or private seeds.

After all 54 checkpoints, call finish_evaluation. It returns the complete v2 report, including the evidence/response transcript, hidden outcomes, reference forecasts, descriptive fits and limitations. Save those exact bytes before computing a report hash for signing. Do not expose evaluator source or another run's report to a respondent meant to be unfamiliar with the tasks.
