# Fresh-agent core acceptance — 20 September 2026

One fresh GPT-6 Astra process, requested at medium reasoning effort through Codex CLI 0.154.0, completed the shared **34-checkpoint core** through its public MCP interface. This is a usability/completion check, separate from the frozen provenance prediction benchmark. An actual human completion and repeatability checks remain pending.

The respondent had no task conversation or repository context, used a temporary working directory, ignored user configuration and was given the five core MCP tools only. Shell, browsing, memory, plugins and subagent features were disabled using the existing isolated-runner conventions and the official [non-interactive CLI interface](https://developers.openai.com/codex/noninteractive). It supplied the recorded configuration metadata and answered in continuous context. The requested alias is not an independently verified immutable model revision; execution metadata remains operator-asserted.

## Completion and resources

- 10 discovery checkpoints followed by 24 disclosed-likelihood calibration questions.
- 34 `get_trial` and 34 `submit_answer` calls, one start, one guide read and one finalization. All tool calls completed; no rejected submissions or retries were observed.
- Core session elapsed time: **186.77 seconds**. Full process including setup and final feedback: **218.65 seconds** (3 minutes 39 seconds).
- Provider-reported input: **1,322,078** tokens, including **1,275,520** cached input tokens; output: **4,004**. Total processed: **1,326,082**. Cached input is not counted twice.
- Used the existing signed-in account. Marginal dollar cost is unknown. These resources are separate from the benchmark totals.
- One attempt with a 900-second operator watchdog. The core protocol itself remained untimed; the watchdog did not activate.
- Exact-byte report and passport exports completed. Python verified that the passport's source bytes and deterministic interpretation match. It remains a private draft with operator-asserted agent origin.

## Descriptive observations

Numeric prior and evidence weights were both effectively **1.00**; reference-probability RMSE was approximately `3.06e-11`. This is consistent with computing the supplied Bayesian reference on these 24 numeric questions. Tiny fitting/rounding differences and narrow within-run intervals are not evidence of a stable cognitive difference or between-run certainty.

In the single discovery company, the derived-model item produced no probability change, the source audit a 2-percentage-point absolute change, and the provenance reveal a 1-point absolute change. Decisions agreed with the elicited probabilities under the supplied payoff at all 10 checkpoints. These are observations from one case, not a diagnosis of general dependency awareness, source trust or investment ability.

## Usability feedback and next revision

After finalization, the respondent reported three points of friction:

1. The enclosing core trial ID differs from the nested task trial ID. The instructions correctly require the enclosing ID, but two identifiers invite mistakes.
2. Conditional questions alternate between “at or below” and “exceeds.” This makes direction important; the next UI/transport revision should make the requested event explicit without accidentally removing an intended contrast.
3. The final response was large enough to truncate the displayed output. The collector retained complete byte-stable artifacts, but the participant would benefit from a concise completion summary plus separate authorized artifact retrieval.

Record these for a version-reviewed core revision after the current frozen collection. No task wording, scoring, protocol hash or active evaluator source was changed during this run. The agent's feedback is one user observation, not a demonstrated human usability result.

## Artifact commitments

Detailed stimuli, responses, private evaluator state and execution messages remain ignored local artifacts under `output/core-acceptance-20260920/`.

| Artifact | SHA-256 |
| --- | --- |
| Run manifest | `9c12f8200905e309d55cdc791d1548172f0a27dac7ba95cea3d870fceacaa186` |
| Configuration | `e30d85c544774139bc9a0e2d5c7fd5080e5728be707f848d00dceb3dc59a6ba1` |
| Core protocol | `8f6391a6886a3ee27c8683261deb982b6206ef79244151bfeaed947d8baa64ef` |
| Report bytes | `fd3aedc5e002316888b44f4661824e0952d77123acf5aaacb26e732766af2b8d` |
| Passport bytes | `d688a02499bad05d387e2b72265407603dbfef52ed3acbbd77df1ebb098fc00e` |
| Execution record | `ca7a5191e76c43a156f4a56894f4ec10c6ad8da555422f13d2f1caf173e70851` |

The configuration hash binds the recorded prompt template, requested alias/effort, CLI version, disabled features, allowed tools, context policy, watchdog and protocol digest. The instantiated subject/request ID are in the exact run manifest. Hashes are operator-created commitments, not independent preregistration or model attestation.
