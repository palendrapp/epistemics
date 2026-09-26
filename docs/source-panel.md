# Bounded source-learning comparison

`source-panel/0.1.0` implements the [decision-value roadmap's](decision-value-pilot.md) repeatability, elicitation and presentation-transfer comparison. It reuses the unchanged `source-learning/0.1.0` generator, immutable response store, observers and payoff rules. The new prose adapter is independently versioned as `source-packets/0.1.0`. No existing evaluator, active human collection or passport contract is changed.

## Questions and fixed allocation

1. Are differences between two configurations larger than their variation across fresh repeated contexts?
2. Does explicitly asking about source accuracy/selection change the company reports?
3. Do earlier configuration-specific or shared profiles predict a new environment when evidence is presented as research packets?

| Phase | Allocation | Collections | Forecast/decision checkpoints |
| --- | --- | ---: | ---: |
| Sparse baseline | Astra and Sol, medium effort; two new worlds; two fresh contexts per configuration/world | 8 | 288 |
| Dense elicitation | Both configurations in both baseline worlds; one fresh context each | 4 | 144 |
| Transfer | Both configurations in one third world; one structured and one packet context each | 4 | 144 |
| Total | 16 independent starting contexts, continuous within each 24-company collection | **16** | **576** |

Dense collections add 48 source reports each, or 192 across the panel. Every collection retains 12 research choices. Six sources recur within each world. The three unique source worlds, sixteen contexts and 576 checkpoints are different units; none should be described as hundreds of independent agents. The requested aliases are `gpt-6-astra` and `gpt-6-sol`, not independently verified immutable model revisions. Their effort, allowed tools and respondent prompt are held constant.

The operator draws and commits three private world seeds and a randomized run order before responses. Baseline runs precede profile freezing; dense runs precede transfer. All conditions use separate fresh processes, preventing within-respondent carryover of private discoveries. Phase order can still be confounded with provider drift; this small panel does not estimate that drift.

## What the packet changes

The adapter takes an existing **public Trial**, never a private world. It preserves the current report, prior, payoffs, ordered resolved source records, disclosed customer rates, already available audit facts, research costs and committed query. It renders these as prose paragraphs instead of the structured archive and source-property fields. It retains the same answer schema and checkpoint sequence.

No new persuasive framing, source prestige, negative wording, business mechanism or evidence is introduced. The numeric business rates and the broad possibility of measurement error/selective reporting remain explicit. This is a narrow presentation-transfer test, not unrestricted natural-language discovery, a new domain, or proof of ecological validity. Packet length and salience can change; those are part of the presentation treatment.

History reads use the same assigned presentation. Each served trial's exact public payload, its digest and external profile predictions are stored transactionally before an answer can be accepted. Retries preserve prior answers. Completed transport evidence is reconstructed and checked against the canonical ledger. A packet run's underlying source-learning report is an analysis ledger; it must be accompanied by the separately versioned panel evidence to establish what the respondent actually saw.

After all answers are committed, both presentations receive the same three factual comprehension questions about resolution timing, carryover of source audits and the distinction between measurement accuracy and random selection. Answers and usability feedback are recorded as completion messages, separate from probability scoring. These questions appear only after collection and cannot train later task responses.

## Frozen prediction

The original collector's within-run fit remains an explicitly labeled diagnostic: twelve initial reports predict the remaining 24 checkpoints. It is not the transfer predictor.

For transfer, fit one profile per configuration using **only the first twelve unaudited forecasts from its four sparse baseline collections** (48 reports). Fit a shared profile using the same subset from all eight (96 reports). No dense or transfer answer enters these fits. Company offset blocks are distinct across contexts. The finite family/gain priors and noise assumptions remain those of the original collection; repeated worlds do not establish that all errors are independent in real participants.

Freeze these distributions, training report hashes and time before any transfer trial. The source observers may learn from public archives, later resolutions and purchased audits in the new environment; respondent probabilities never become new priors or likelihood judgments. Predictions for all 36 transfer checkpoints are locked before delivery using:

- Configuration-specific fitted profile.
- Shared fitted profile.
- Fixed joint-process, flat-accuracy and fixed-discount observers.
- Configuration/shared calibration means and the stated company prior.

The profile's “gain” is a reporting nuisance parameter, not a stable belief-weight or confidence trait. Conditional model probabilities refer only to the implemented alternatives. Shared and individual fits are given the same candidate families and gain support.

## Primary comparisons and limits

Primary comparisons use the **first twelve unaudited company forecasts**. Their evidence is identical across repetitions and matched conditions because no research choices have yet changed the public path.

| Comparison | Recorded quantity | Interpretation limit |
| --- | --- | --- |
| Repeatability | RMS difference between sparse repeats for each configuration/world | Four repeat contrasts, not a population reliability coefficient |
| Between configurations | RMS difference between the two-repeat means in each world | Compare with within-configuration variation; no forced individual ranking |
| Dense elicitation | RMS and mean signed difference from the matching sparse-repeat mean | One dense context per cell; questions and burden change together |
| Transfer prediction | RMSE of each prospectively locked predictor against twelve new reports | One new world; configuration/shared fits must earn improvement over fixed baselines |
| Presentation contrast | Structured versus packet report differences within configuration/new world | No transfer-world repetition; baseline repeat variation is context, not a matched error estimate |

Show each configuration/world result. Do not present a bootstrap over checkpoints as a population confidence interval; there are only two baseline worlds and one transfer world. The entire 36-checkpoint transfer prediction is secondary and conditional on the research actually chosen. Format-dependent research choices may create different later information; that secondary comparison cannot isolate a direct wording effect.

Retain all three families in the conditional adequacy screen: 256 simulated draws under each frozen configuration gain distribution, fixed analysis seed 20260926, and the 99th-percentile RMSE boundary. All may fail. These screens assume the specified report-noise process and are not calibrated composite-model tests. Report resolved-outcome Brier, action/report consistency, research choices and realized fictional payoff separately from prediction errors. No buyer policy or support intervention is tested here.

The [roadmap's decision rules](decision-value-pilot.md#decisions-we-will-make-from-the-evidence) apply: prefer the simpler/shared account when individual fitting adds no useful prediction, restrict a claim that fails transfer, and investigate specific residuals if every candidate is inadequate. This feasibility panel does not authorize a stable trait or optimal-support label.

## Resource and failure boundaries

The preceding acceptance used about 1.44 million processed tokens and 196 seconds. Sixteen comparable collections would use about 23 million processed tokens; dense/prose prompts and configuration differences can change that estimate. Cached input is included in input usage, not added again. Monetary cost under existing account billing is unknown.

The initial operator plan fixes two concurrent processes, a 900-second ceiling per attempt, a 5,400-second panel ceiling and one attempt per run. Admission stops if known processed usage plus a three-million-token reserve per incoming run would exceed 40 million tokens. Usage is reported by the provider at completion, so the token boundary is an admission check, not a hard streaming cap. Time limits terminate the owned process groups. A failed run stops further admission after the already running batch; partial evidence and unknown usage remain recorded. There is no automatic replacement, retry or case exclusion.

The launcher uses the existing account, an empty working directory, ignored user configuration, no project instructions, and five public MCP tools. File/shell access, browsing, memory, plugins and further agents are disabled for the respondent. The snapshot, flags, requested configuration and tool record are operator evidence, not independent execution attestation. Private seeds, source processes, prompts, per-run reports and logs remain under ignored `output/`.

## Validation and operation

Before real collection, use two distinct synthetic recovery seeds. Each recovery dataset pools four calibration contexts over two source worlds and predicts a third world. Vary three generating families and on/off-grid reporting gains with the specified noise; retain an excluded direction-reversal check and an uninformative-data ambiguity test. This checks the implemented families and pooling calculation, not a simulated psychological effect of prose or dense questions.

The comparison adds tests for factual rendering, all purchased research branches, private-data boundaries, history presentation, prospective locks, concurrency/idempotent retries, unchanged earlier fingerprints, calibration-only fitting, complete synthetic panel analysis and actual stdio MCP collection. No Pydantic main-report schema changes, so `schemas/report.v1.json` is unchanged.

The [26 September implementation validation](source-panel-validation-2026-09-26.md) passes both declared recovery seeds and the complete synthetic transport/panel checks. It is separate from real-agent evidence.

After passing and saving two fingerprint-bound recovery results, an operator may start a new private panel:

```sh
uv run python -m epistemics.source_panel.runner output/source-panel-agent \
  --validation output/source-panel-validation-a.json \
  --validation output/source-panel-validation-b.json
```

The runner creates a new directory exclusively, commits the plan before responses, snapshots the implementation, freezes profiles after baseline and exports a private comparison summary. It refuses a changed implementation or validation result. It does not resume a failed collection automatically. Export a scoped aggregate write-up for Git; do not commit the private summary, raw reports or evaluator state.

This increment implements an agent MCP presentation comparison. The existing human browser collection remains available and untouched; actual human completion and human presentation usability remain separate tasks.
