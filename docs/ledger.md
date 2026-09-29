# Experiment ledger

Every number in a results doc should be reproducible from frozen artifacts by a versioned command. The ledger (`epistemics.ledger`, ledger/0.2.0) does that and feeds a private dashboard.

## Parts

- **Registry:** [`docs/experiments.json`](experiments.json), maintained by hand. It records each experiment's question, preregistered prediction, outcome, status, document and collection roots, plus the project's decision log and next steps. It holds no computed numbers.
- **Facts:** the plan, execution and per-run files of every root under `output/`. These give status, contexts completed, tool errors, token use and SHA-256 commitments.
- **Verified estimates:** for disposition collections. Each root's reports are re-verified and read in a subprocess using that root's own implementation snapshot, `output/<root>/implementation/src`, which checks exact bytes, reconstruction and recomputed analysis. Version-specific designs are therefore interpreted by the code that collected them. Tables are computed from those records with current, tested code: tie-aware ranks, retest differences, relative-judgement contrasts and per-description fits.
- **Passport so far:** per-configuration parameters pooled over verified contexts:
  - default priors;
  - value of certainty, and the share of checks priced at decision value;
  - evidence sensitivity and report noise;
  - learning;
  - description mappings, retest differences and the relative-judgement contrast.

- **Model views** (`epistemics.ledger.models`, the `models` block of `ledger.json`), for the dashboard's Models tab:
  - **Grid posteriors.** For every verified disposition session, full grid posteriors are recomputed from its responses and its collected item design, using the current model code (mirroring `fit.fit_reports`, `fit.fit_checks` and `fit.fit_cues`). Each session records `recorded_difference`: the largest gap between the recomputed posterior means and the verified report's own, as a share of the grid's range. It is 0 for every session except the six version-0.1 checks sessions of the first acceptance run, which were fitted under an earlier model and are marked in the page.
  - **Posterior predictive checks.** Each report's predictive distribution mixes the whole-percentage (or whole-point) report likelihood over the joint grid posterior. Each session stores the 5/25/50/75/95% predictive quantiles of every report and the number of reports inside the central 90%.
  - **Recovery sample.** 100 simulated respondents per module (relay and disclosure probe designs; checks under the linear certainty function), drawn from the validation study's generating ranges with seed 20260928 and fitted by the real fits. Intervals are widened to grid-cell edges, as in the validation study. The sample is cached under `output/ledger-recovery-v2-<model fingerprint>-…json`.
  - **Designs.** Each distinct item design, with case labels and reference observer values. The page's JavaScript port of the relay and disclosure observers is checked against these on load, and the page reports the largest difference.

- **Hierarchical fit:** the latest `output/inclusion-hier-fit-*.json`, with its SHA-256, and the sensitivity fit of the same date. The Models tab draws it as section 6.
- **Analyses:** the formal-to-dossier transfer and the noticing comparison (unprompted against prompted dossiers), computed over every verified record in the registry.
- **Reading guide** (`epistemics.ledger.guide`, reading-guide/0.3.0; written to `output/guide.json` by `build`): the passport in plain language, per configuration.
  - **Readings.** Fixed rules turn each measured parameter into a reading. Each reading has a claim, a detail line, the evidence behind it (module and number of sessions), a short fact for the label, and a caution where a behaviour could mislead a reader. Examples: "treats a missing base rate as 50/50"; "its probabilities carry about ±10 points of noise"; "states sensible base rates, but its forecasts often use different ones".
  - **Thresholds.** They live in the code, so the guide changes only when the evidence does.
  - **Scope.** Readings describe behaviour in these tasks; they are not claims about internal beliefs.
  - **Coherence exclusions.** The first urn run's selection asked and probed conditions (variant `urn-named`) are left out. Their design makes stated and applied rates diverge by construction ([abstract transfer](disposition-abstract-2026-09-28.md)). The corrected variant (`urn2-named`) is included.
  - **Structure checks** (0.3.0). These come from the latest `output/structure-checks-*.json` ([structure checks](structure-checks.md)). Each valid check gives one reading under "Which hidden structures it considers": how often it considers the structure unprompted, and the prompt that makes it reliable (nothing, mention it, ask how common it is, ask about each case). The noticing and carry-over readings moved to the same topic.
  - **Carry-over of noticing** (0.2.0). This reading comes from the latest hierarchical second-layer fit (`models.hierarchy`), and only when that configuration's fit meets its validity rule (every R-hat of 1.05 or less). It states whether noticing one hidden structure predicts noticing another, and the range of prompting an untested structure might need ([hierarchical thresholds](structure-inclusion-model.md)).
  - **Page.** [`src/epistemics/ledger/assets/guide.html`](../src/epistemics/ledger/assets/guide.html) renders the guide as its own private artifact, separate from the dashboard, with `guide.json` published alongside: https://claude.ai/artifact/FxwAGdpF1ZLYDgxvAPeQXZ. Republish it after each rebuild, as for the dashboard.

## Commands

```bash
uv run python -m epistemics.ledger build
```

writes `output/ledger.json` (private, not in Git). The table commands print the tables used in the docs:

```bash
uv run python -m epistemics.ledger runs output/disposition-range-20260928
```

```bash
uv run python -m epistemics.ledger retest output/disposition-cues-20260928 output/disposition-cues-retest-20260928
```

```bash
uv run python -m epistemics.ledger contrast output/disposition-range-20260928
```

```bash
uv run python -m epistemics.ledger noticing output/disposition-transfer-20260928 output/disposition-unprompted-20260928
```

## Dashboard

The page is [`src/epistemics/ledger/assets/dashboard.html`](../src/epistemics/ledger/assets/dashboard.html). It reads `ledger.json` published alongside it and is hosted as a private claude.ai artifact: https://claude.ai/artifact/EsX4sqwbZ5eTKXFSo3Wbx8.

After each run:
1. Update the registry entry (outcome, status, next).
2. Rebuild the ledger.
3. Republish the page together with the new `ledger.json`.

The page has two tabs:
- **Ledger:** the passport, experiments and token use.
- **Models:** five views in Bayesian-workflow order.
  1. The generative model, drawn as a Kruschke-style diagram whose parameter nodes are sliders. It feeds response curves and a prior-predictive ridgeline, onto which any session's reports can be overlaid with their log-likelihood.
  2. Parameter recovery on simulated respondents.
  3. Half-eye grid posteriors for each session, set against the uniform prior.
  4. Posterior predictive interval checks, with a calibration strip over all sessions.
  5. Ridgelines of the implied prior for each description level, comparing formal presentations with dossiers.

The page never contains transcripts or prompts, only summary figures, item designs and the fitted posteriors derived from the verified reports.

## Tables regenerated so far

- Description-to-prior retest ([record](disposition-cues-acceptance-2026-09-28.md#retest)): matches the published table exactly.
- Relative-judgement contrast ([record](disposition-range-2026-09-28.md#results)): the first results table produced by the ledger rather than a scratch script.

Earlier tables were produced by scratch scripts. The ledger reproduces their inputs from the verified reports, and any discrepancy found when a doc is next revised will be recorded in that doc.
