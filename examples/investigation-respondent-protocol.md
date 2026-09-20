# Fresh investigation respondent

Use only the assigned MCP's public protocol, current trial and accepted public history. Do not inspect evaluator code, operator manifests, outcome files or other participants. Keep context continuous within this episode, and use a fresh context for another episode. These instructions are a behavioral boundary; stronger isolation requires a separate evaluator host/container.

Call `describe_battery`, then `get_history` to restore accepted responses if interrupted. Repeat `get_trial` and `submit_answer` through four checkpoints. At checkpoint 1 choose exactly one listed research option in the answer's `query` field. At other checkpoints omit `query` or set it to null. Probabilities use increments of 0.01; 0 and 1 are valid. Accepted answers are immutable; after a transport interruption an identical retry is safe. Never revise a previously accepted response. Call `finish_evaluation` after checkpoint 3. It returns a receipt and does not disclose outcomes or analysis.

The protocol supplies the forecast events, hypothetical payoffs and evidence. Optional explanations are not scores or evidence of an internal process. Answer from the available information. Do not attempt to infer hidden evaluator seeds or optimize for an imagined trait label.

The operator prepares the participant/configuration descriptor and assigns the episode. A local transport bridge is:

```sh
uv run epistemics investigation client --directory /private/collection --assignment ASSIGNMENT_ID
```

It accepts JSON lines such as `{"tool":"get_trial","arguments":{}}` and `{"tool":"submit_answer","arguments":{"trial_id":"...","answer":{...}}}`. Finish the episode, then close the bridge with `{"close":true}`. This bridge communicates with a real MCP process; it contains no respondent logic.
