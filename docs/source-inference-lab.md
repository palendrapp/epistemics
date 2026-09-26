# Source-inference design laboratory

The first implementation milestone from the [source-inference proposal](source-inference-design-2026-09-24.md) is an offline simulator and model-discrimination laboratory. It predicts judgments from public source histories, rather than taking freshly elicited priors and likelihoods as unconstrained inputs. It does **not** yet collect responses from agents or humans or issue passport traits.

## The implemented world

Companies have a binary strong/weak demand state. Independent customers expand with probability 0.7 under strong demand and 0.3 under weak demand. A source measures five-customer panels with a fixed accuracy r: each binary observation is independently recorded correctly with probability r. It then faithfully reports the count in one panel, selected randomly or as the maximum/minimum among J candidates.

The effective measured expansion rate is r p_H + (1 − r)(1 − p_H). For a panel count K with CDF F_H, selection gives:

\[
P(\max_{j\leq J}K_j=k\mid H)=F_H(k)^J-F_H(k-1)^J.
\]

The analogous minimum distribution uses survival probabilities. Exact distributions are checked against independent enumeration of true records and measurement errors, as well as sampled private ledgers. Measurement noise occurs before selection. Faithfulness to the selected measurement does not guarantee that the measurement is correct or representative.

The default archive crosses accuracies 0.65/0.95 with random, maximum-of-ten and minimum-of-ten selection: six source histories, twelve resolved observations each. Outcomes are deliberately balanced; every observer conditions on those publicly resolved outcomes. Public records omit true panels, measured candidate panels, selected indices and source parameters. The generator retains a separate private ledger.

Source processes are uncertain to the observer. **Business expansion rates are currently known controls.** Learning the business mechanism from examples and interpreting less specified prose are not implemented by this milestone.

## Three behavioral accounts

| Account | What it learns and predicts |
| --- | --- |
| Joint process | Joint uncertainty over measurement accuracy and the reporting rule; integrates both when predicting the company state |
| Flat accuracy | Uncertainty over measurement accuracy, with every report treated as a random panel; ignores selection audits |
| Fixed discount | Ignores source history and selection; applies 35% of the log evidence from a perfectly measured random panel, added to prior log odds |

The accuracy support is {0.5, 0.65, 0.8, 0.95, 1}. Joint selection support is random, maximum/minimum of four, and maximum/minimum of ten. Each family starts uniformly over its finite source support. These are specific competing approximations, not an exhaustive taxonomy of agent cognition.

Given resolved public history D and a new report k, the joint learner computes:

\[
P(H,r,J,s\mid D,k)\propto P(k\mid H,r,J,s)P(H)P(r,J,s\mid D).
\]

A disclosed process audit restricts the joint observer to the audited rule. If it establishes random sampling, the joint and flat models become observationally equivalent in this implementation. This remains true with informative company reports; the implementation checks it explicitly. No false distinction should be created by fitting those cases.

Candidate audit conditions include alternative reporting rules applied to the same public history. These are diagnostic counterfactual inputs; some are very unlikely under the history generator. They are not all observations from one fixed private source process. A live collection must bind each actual audit to its own consistent private world, and can identify hypothetical questions explicitly.

## Response likelihood and parameter recovery

Each family predicts a company probability p*. The synthetic reporting process is:

\[
\ell_t=g\operatorname{logit}p_t^*+u_s+\epsilon_t,
\quad u_s\sim N(0,0.12^2),\quad\epsilon_t\sim N(0,0.18^2),
\quad\widehat p_t=\operatorname{round}_{0.01}\sigma(\ell_t).
\]

The source-block offset u_s induces correlation among reports about the same source. Fitting integrates it using 15-point Gauss–Hermite quadrature; a separate numerical integration test checks this calculation. Report likelihoods use whole-percentage rounding bins, including 0% and 100%, rather than treating these reports as exact continuous numbers.

Gain g is a reporting nuisance parameter. It is fitted on 13 points from 0.7 to 1.3, with a uniform prior; generating gains 0.83, 1 and 1.17 include off-grid values. Equal family priors and marginalized gain likelihoods produce conditional model probabilities. A probability below 0.8 for every family is reported as ambiguous. This threshold is a design convention, not an empirical confidence calibration.

The higher-noise simulation changes independent logit SD to 0.4 and supplies that value to inference. It tests stronger known response noise, not robustness to unknown noise misspecification. All candidate families may fail an independent adequacy check even when one has the largest relative likelihood.

## Design selection and prospective checks

The candidate bank has 648 probes: six sources × six report counts × three company priors × six audit conditions (none or one of the five rules). No participant answers enter design selection.

Each probe is ranked by its marginal expected information about model family, integrating gain and response noise. The selected design has four probes per source: two fixed unaudited anchors and two information-ranked probes. A comparator retains the same anchors and adds two randomly selected probes per source. This is a coverage-constrained marginal ranking, not a globally optimal joint design.

Design, calibration and heldout histories use separate seeds. The 32 heldout templates are disjoint from both selected calibration sets. Model predictions for calibration and heldout inputs are committed before synthetic reports are drawn. Fits use calibration reports only. Prediction errors on heldout inputs compare with the generating model's noiseless response means; they are not empirical forecasting accuracy.

Each seed runs 32 repetitions per family at baseline and higher noise: 192 synthetic datasets. The same simulated responses are used for shared probes in the two designs. Reports contain full confusion matrices, ambiguous cases, gain recovery conditional on the generating family, and heldout error after both conditional and selected-family fitting.

Development screens, recorded before simulations, require at least 90% correct discrimination in the primary joint-versus-flat comparison; joint-family gain MAE ≤ 0.15 and new-input RMSE ≤ five probability points; neutral ambiguity; equivalence after a random-sampling audit; and rejection of a deliberately excluded direction-reversal process. These limited screens are engineering criteria. They do not cover all model pairs or all parameter regimes.

The direction-reversal control fits the candidate models, freezes the fit, then tests fresh simulated reports. Observed RMSE is compared with a 99th-percentile envelope from 256 simulations at each candidate's fitted parameters. This is a conditional adequacy diagnostic, not a calibrated composite-model hypothesis test or protection against every possible misspecification.

## Research policy contrasts

The laboratory computes one-query-then-act decisions. Investing pays 1 − threshold if demand is strong and −threshold otherwise; declining pays zero. Available research is an independent customer panel, a definitive selection-rule audit, a definitive measurement-accuracy audit, an irrelevant coin audit, or stopping.

Compare expected decision improvement minus price, company information gain, and information gain about company/source state plus the irrelevant coin. The last policy is an explicit foil. Prices and decision thresholds vary; ties are retained. These are policy predictions under the joint observer, not observed research behavior or a recovered search parameter.

## Reproduce

```sh
uv run python -m epistemics.source_inference \
  --output output/source-design-a --seed 20260925 --repetitions 32
uv run python -m epistemics.source_inference \
  --output output/source-design-c --seed 20261025 --repetitions 32
```

The output directory must be empty. Artifacts are written without overwriting existing bytes: plan, private worlds, public inputs, prediction lock, JSON result and readable Markdown. The result binds exact input-artifact bytes and the implementation fingerprint. A failed screen exits nonzero while preserving the result. Output directories remain ignored by Git.

Versions are `source-world/0.1.0`, `source-design/0.1.0`, and `source-discrimination/0.1.0`, with independent development artifact identifiers. Earlier evaluators and the main Pydantic report contract are unchanged. There is no new active battery, MCP endpoint, human form or passport issuance adapter.

The [first results](source-inference-results-2026-09-25.md) guided the separate [source-learning collection](source-learning.md), now implemented with consistent actual audits, browser/MCP access and sparse/dense assignments. Source-label priors, error-driven source learning, drift, semantic interpretation, empirical elicitation effects, human usability and measured support remain future work. The laboratory's inference is an original bounded adaptation of the literature reviewed in the [proposal](source-inference-design-2026-09-24.md), not a replication of those experiments.
