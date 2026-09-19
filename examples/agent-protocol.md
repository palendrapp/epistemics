# Evaluated-agent protocol

Describe the actual agent configuration to the evaluator. Fingerprint the system prompt, available tools and relevant runtime settings together, using a stable serialization and SHA-256. Record the serialization convention with your study. The evaluator records your supplied fingerprint; it does not verify your runtime.

Example `start_evaluation` arguments (replace the illustrative fingerprint):

```json
{
  "agent": {
    "agent_id": "example:research-agent",
    "model": "provider/model-name",
    "model_version": "provider-revision",
    "configuration_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "context_policy": "continuous",
    "temperature": 0
  }
}
```

After receiving `session_id`, call `get_trial`. Read its instructions and stimulus, then return a probability report through `submit_answer`:

```json
{
  "session_id": "RETURNED_SESSION_ID",
  "trial_id": "RETURNED_TRIAL_ID",
  "answer": { "probability": 0.7 }
}
```

For source-reliability trials, include both fields:

```json
{
  "session_id": "RETURNED_SESSION_ID",
  "trial_id": "RETURNED_TRIAL_ID",
  "answer": { "probability": 0.7, "source_probability": 0.6 }
}
```

These numbers only illustrate the format. They are not recommended answers. Report the requested marginal probabilities; `source_probability` is the probability that the source is valid. It is not certainty in your first answer.

Continue until `get_trial` returns `complete: true`. Call `finish_evaluation` and persist the returned structured JSON. Numeric answers must be finite and in [0,1]; quoted numeric strings and extra fields are rejected. Exact retries of an accepted answer return the original receipt. Different answers to an accepted trial are rejected.

The session ID is sufficient to resume after reconnecting to the same database. Preserve it privately. Do not request or inspect the evaluator's database, private trial state or hidden outcomes during the evaluation. Run independent cases under the context policy agreed for the study; the MCP protocol records but does not enforce context resets.
