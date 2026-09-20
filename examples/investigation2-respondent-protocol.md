# Investigation 0.2 respondent protocol

Connect through the operator-bound MCP server or `epistemics investigation2 client`. The operator creates the participant/configuration binding and selects the assignment. Start each agent case in a fresh process; retain context within it. Do not expose evaluator files, seeds, hidden outcomes, model-comparison code or earlier respondents' answers.

1. Call `describe_battery` and `get_history`. Restore accepted history if resuming.
2. Call `get_trial`. Use its named stage and outer `trial_id`.
3. Submit the three probabilities and invest/hold decision. Use probability values from 0 to 1 in increments of 0.01. Explanations are optional brief decision summaries; no private reasoning is requested.
4. At **Evidence and research** only, also submit `query`. If `expectation_queries` is nonempty, submit exactly those three entries in `expectations`; each has `yes_probability`, `growth_if_yes`, and `growth_if_no`.
5. Repeat until `get_trial` says complete, then call `finish_evaluation`. It returns a completion receipt; private analysis and outcomes remain operator-only.

An illustrative research answer has this shape. Values are examples, not recommended answers:

```json
{
  "growth_probability": 0.50,
  "audit_understatement_probability": 0.30,
  "backlog_high_probability": 0.40,
  "decision": "hold",
  "query": "stop",
  "expectations": {
    "source_audit": {"yes_probability": 0.30, "growth_if_yes": 0.70, "growth_if_no": 0.41},
    "operations_check": {"yes_probability": 0.40, "growth_if_yes": 0.60, "growth_if_no": 0.43},
    "segment_check": {"yes_probability": 0.50, "growth_if_yes": 0.80, "growth_if_no": 0.20}
  }
}
```

Omit `expectations` when not requested and omit `query` outside the research stage. Identical retries are idempotent. An accepted answer cannot be revised. Do not try to choose later trials or request evaluator feedback. Model parameters and cognitive labels are not part of the participant protocol.

The JSON-lines bridge accepts `{"tool":"get_trial","arguments":{}}` and corresponding calls for the other four tools. It prints protocol/history/tool metadata on connection. MCP and browser participation share the same transactional service and answer schema; the browser converts whole percentages to probabilities.
