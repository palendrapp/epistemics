# Source-learning collection

`source-learning/0.1.0` is the participant collection built from the [source-inference laboratory](source-inference-lab.md). It has one continuous history, six recurring sources, 24 companies and 36 checkpoints. Browser and MCP adapters use the same transactional service. The [implementation and synthetic acceptance results](source-learning-results-2026-09-26.md) and [first fresh-agent acceptance](source-learning-acceptance-2026-09-26.md) are complete. Actual human usability and the [repeatability/transfer comparison](decision-value-pilot.md) remain next.

This is a development evaluation of learning about measurement accuracy and selective reporting. Business expansion rates are disclosed: 70% under strong demand and 30% under weak demand. No likelihood table for source reports is supplied. The task does not yet test learning an unfamiliar business mechanism or unconstrained interpretation of natural language.

## Participant experience

Each source initially has twelve resolved archive records, deliberately balanced between strong and weak company outcomes. The participant sees what the source reported and what later happened. Sources measure five-customer panels; their measurement accuracy and panel-selection rule remain constant. Neutral source names are randomly assigned to generating processes.

| Part | Companies | What is requested | Feedback |
| --- | ---: | --- | --- |
| Initial source learning and reporting calibration | 12, two per source | Company probability and investment decision | Company outcome after commitment |
| New-company prediction and research | 12, two per source | Initial probability, provisional decision and one research choice; then revised probability and final decision | Only the purchased research before revision; company outcome after the final answer |

The collection therefore has 36 company-probability reports, 36 decisions and 12 research choices. The original archive contains 72 records to inspect, not 72 additional response checkpoints. Completed cases extend the source's track record. Earlier public evidence, accepted answers, company resolutions and purchased audits remain available throughout the run.

Research offers an accurate independent customer panel, a definitive selection-process audit, a definitive individual-measurement-accuracy audit, or stopping. Source audits apply to the archive and subsequent reports from that same source. Unpurchased research remains private. Research prices and investment thresholds vary; payoffs use fictional points. Investing earns `1 − threshold` for strong demand and loses `threshold` for weak demand. Declining earns zero, with purchased research deducted from either action.

Every new company outcome is drawn using its stated prior. The source report and independent panel are then generated from that outcome. Reports are not selected for extreme disagreement, and actual audits always match the private source that generated the archive. This removes the counterfactual audit/history combinations used in the earlier design laboratory.

## Sparse and dense assignments

The sparse condition asks only for company forecasts, actions and research. The dense condition additionally asks, at the 24 initial company checkpoints, for:

- The probability that an individual source measurement is recorded correctly.
- The probability that the source selects a panel randomly rather than by its measured result.

These add 48 reports. They are observable source judgments, not direct measurements of an internal cognitive state. The primary prediction model never takes these answers as free inputs.

Condition is randomly assigned unless the operator specifies it, and the manifest records which method was used. Using the same private design seed in two separate collections creates matched worlds. Use separate fresh agents or participant groups for that comparison: a human or agent that has completed one condition cannot unlearn its audits and resolutions before a second run.

The conditions change the content and burden of prompting together. A difference would identify the effect of this bundled elicitation treatment, not the isolated causal effect of asking more questions. The present simulations generate the same reporting policy in both conditions; they cannot establish a human or agent treatment effect.

## Inference and prospective prediction

The joint source-process, flat-accuracy and fixed-discount accounts retain the finite supports described in the [laboratory specification](source-inference-lab.md). Each account sees only resolved public history and already delivered research. The joint account learns measurement and selection together. The flat account learns measurement accuracy and accepts measurement audits but ignores panel-selection audits. The fixed-discount account ignores source history/audits and applies 35% of the literal company evidence, including an independent panel when purchased.

All models receive the stated company prior. Purchased process audits restrict compatible source states for the accounts that represent them. Independent customer evidence supplies a separate likelihood. These are bounded competing assumptions; the reference is not an omniscient observer of evaluator truth.

The reporting layer is:

\[
\ell_t=g\operatorname{logit}p_t^*+u_{c(t)}+\epsilon_t,
\qquad u_c\sim N(0,0.12^2),\quad\epsilon_t\sim N(0,0.18^2).
\]

Reports are rounded to whole percentages. The likelihood integrates the shared company offset, including dependence between initial and revised reports. Unlike the laboratory's source-block error model, this collection assumes report error is independent between companies. Persistent source-specific report bias is unmodeled and could contribute to inadequate fit.

The fit uses only the first twelve company reports. It freezes posterior weights over the three candidate families and thirteen reporting-gain values from 0.7 to 1.3. Later predictions average over that gain uncertainty. A gain is a reporting nuisance parameter, not a measured evidence-weight trait. A conditional family probability below 0.8 for every family is reported as ambiguous.

Before each checkpoint is returned, the service stores its model predictions and exact trial hash in the same private transactional store. Submission requires an existing prediction lock; the accepted receipt binds its bytes. After the twelfth calibration answer, the fit is frozen before any heldout checkpoint can be read. Later public evidence can update the source observer; later participant reports cannot change the frozen parameters or become new model priors. Locks are sequential because subsequent public information depends on the chosen research branch.

The completed report separates:

- Prediction of later probability reports: frozen mixture, fixed joint observer, calibration mean and last-calibration-report baselines.
- A report likelihood that treats the public research path as given. It does not model the selection induced by the participant's research policy or provide a joint likelihood of forecasts and choices.
- Conditional adequacy screens from 256 simulations per family under the frozen calibration gain distribution. These can reject all candidates, but are not calibrated composite-model tests.
- Forecast Brier scores against resolved company outcomes, realized payoffs and decision consistency with reported probabilities.
- Research choices compared with myopic decision value and company information gain, with ties retained.

Research audits can benefit later companies. The current one-company value calculation omits that future value and must not be interpreted as a general rationality score or a recovered search strategy. Source-question answers are retained as descriptive observations. No stable bias, causal cognitive mechanism, individualized support benefit or passport trait follows from these fits alone.

The intellectual basis remains the [source-inference proposal and its primary bibliography](source-inference-design-2026-09-24.md): auxiliary assumptions in [Gershman (2019)](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf) and costs and constraints in [Bhui, Lai & Gershman (2021)](https://gershmanlab.com/pubs/Bhui21.pdf) motivate the questions. This is an original bounded task, not a replication of either work.

## Run locally

Create a private human collection. A pseudonym is sufficient; edit the example participant identifier as appropriate. Omitting the condition randomizes it.

```sh
uv run python -m epistemics.source_learning create \
  --directory output/source-learning-human \
  --participant examples/human-participant.json --condition sparse
uv run python -m epistemics.source_learning serve \
  --directory output/source-learning-human --port 8776
```

The server prints a private loopback link. Its access token stays in the URL fragment and browser session storage. The browser requires instruction acceptance before revealing the first checkpoint. The human completes the answers; automated previews must use an explicitly synthetic collection.

For an agent, provide actual subject/model/configuration metadata using the structure in `examples/investigation-participant.json`, create one collection, then bind the stdio server using [the MCP example](../examples/mcp-source-learning.json). Keep one continuing context across the whole collection. Exposed tools are `describe_battery`, `get_trial`, `get_history`, `submit_answer` and `finish_evaluation`. Operator creation, seeds, future company outcomes, private worlds, fitted models and export are not MCP tools.

After all checkpoints and `finish_evaluation`, the operator exports privately:

```sh
uv run python -m epistemics.source_learning export \
  --directory output/source-learning-human
```

This writes the full JSON report, readable Markdown, report hash, frozen fit and prediction locks. The JSON includes evaluator-only design data and is not a public passport. Existing different artifact bytes are never overwritten. Original answers are immutable; identical retries return the original receipt, including after restart or completion.

For automated synthetic acceptance and recovery:

```sh
uv run python -m epistemics.source_learning simulate \
  --directory output/source-learning-demo --seed 20260925 --condition sparse
uv run python -m epistemics.source_learning validate-synthetic \
  --output output/source-learning-recovery-a.json --seed 20260925 --repetitions 32
uv run python -m epistemics.source_learning validate-synthetic \
  --output output/source-learning-recovery-b.json --seed 20261025 --repetitions 32
```

Each recovery run records its gates and implementation fingerprint before generating responses. Synthetic research rotates across branches to test coverage; it is not an inferred research policy. The second seed range does not overlap the first run's world seeds.

## Version and privacy boundary

The battery is `source-learning/0.1.0`, evaluator `source-learning-evaluator/0.1.0`, with independent collection/trial/report v1 schemas. Earlier batteries, active human sessions, laboratory versions, signed records and the main report contract are unchanged.

The private manifest and evaluator fingerprint bind a run to exact inputs and implementation. Local files and SQLite state have restrictive permissions, and the browser allows only guarded loopback routes. This is not process isolation: a respondent with unrestricted filesystem access could inspect evaluator files. Controlled acceptance must restrict respondent access to the public MCP/browser interface and record configuration and actual execution conditions. Issuer identity, subject identity, configuration metadata and execution verification remain separate.

The first fresh-agent acceptance completed all 36 checkpoints. The frozen joint-process account predicted later reports more closely than the flat-accuracy/fixed-discount candidates, but did not beat the fixed joint observer. Its conditional adequacy screen was not exceeded; one run does not validate the mechanism or a stable profile. The next bounded comparison targets repeatability, elicitation and one presentation-transfer bridge, with actual human usability separate. Use the [decision-value plan](decision-value-pilot.md) to connect any supported claim to verification/support benefit before broader task expansion. Source labels and drift remain later contrasts.
