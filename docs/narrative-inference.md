# Narrative inference 0.1

This development module asks a respondent to construct a predictive interpretation of a short business story before seeing the evidence. It separates three observable questions: **what did each explanation predict, how did the reported joint distribution change, and which uncertainty did the respondent investigate?** No numerical likelihood table or population prior is supplied.

It is a scaffolded bridge from the numerical controls to richer discovery. It does not yet measure unrestricted hypothesis generation, identify an internal causal graph or release validated passport traits. The earlier core, investigation and auxiliary batteries remain unchanged.

## Eight cases, four checkpoints

Two domains (subscription seats and distributor orders) cross two directions (rise and fall). Each appears as a prose paragraph and as separate facts containing **exactly the same sentences**. These four matched pairs have the same final resolutions within each pair, with all four final event combinations represented across pairs. Assignment IDs and order are seeded evaluator-side and hidden; agents use fresh contexts per case. Humans use a continuous private collection, so carryover differs.

- **D:** independently reconciled demand changed by more than 10% in the stated direction, using the same cohort and period.
- **S:** a reporting error exaggerated the dashboard change in that direction by at least five percentage points.
- **E:** the preliminary dashboard reports a change of more than 10% in that direction.

The four response categories are D only, S only, both and neither. They exhaust event combinations, not possible explanations. For example, “neither” permits noise or smaller business/reporting changes. The definitions imply that D and S together entail E; the report exposes any shortfall from a 100% forecast for that combination as a specific comprehension/consistency observation. Other conditional likelihoods are not fixed by the task.

| Checkpoint | New information | Requested response |
| --- | --- | --- |
| Background and predictions | Anecdotal business change and an unconfirmed pipeline problem | Joint state distribution; four forecasts P(E given each state) |
| Dashboard arrives | E occurred; this is the previously described source | Joint distribution; choose demand audit, pipeline audit or stop |
| Research result | The chosen audit resolves only D or only S; stopping adds no information | Joint distribution |
| Final audit | Both events resolved conclusively within the task | Joint distribution |

Each case has 20 probability entries and one research choice: **32 checkpoints, 160 entries, eight choices** in a full collection. Joint entries sum to 100%; the four separate signal forecasts need not. Entries use whole percentages. Cases are authored contrasts, not random portfolio draws, so outcomes do not support calibration or reliability estimates.

The MCP current-trial tool returns only new documents. Its history tool restores accepted documents and answers. The browser emphasizes new evidence and keeps earlier evidence and answers under a collapsed history. Research choices and responses are immutable; identical retries return the original receipt. The evaluator reveals only the chosen audit until final resolution.

## Observable comparisons

Let h index the four joint states, π(h) be the initial joint report, L(h) the prospective signal forecast, and r₁, r₂, r₃ the later joint reports. These are elicited reports, not access to internal beliefs.

The own-report consistency reference after E is:

\[
b_1(h)=\frac{\pi(h)L(h)}{\sum_j\pi(j)L(j)}.
\]

After the chosen audit A, compare with a reference conditional on the **previous reported joint**:

\[
b_2(h)=\frac{r_1(h)\mathbf 1[h\text{ agrees with }A]}
{\sum_jr_1(j)\mathbf 1[j\text{ agrees with }A]}.
\]

For stop, b₂ = r₁. A zero denominator is explicitly undefined; probabilities are not silently clipped to create support. Such cases remain in the behavioral report. References assume stable event meanings and conditional expectations; eliciting the predictions may itself scaffold reasoning.

Discrepancy is total variation in percentage points, 50 Σₕ |r(h) − b(h)|. The report also gives demand/artifact marginals, their covariance, changes in the unaudited event, and final direct-resolution error. “Explaining away” is observable when resolving one event reduces support for the other under the respondent's declared joint expectations. It is conditional on those expectations, not an unconditional rule that either explanation must suppress the other.

Whole-percentage rounding can be amplified by a low-probability audit. A sensitivity calculation allows each input and output a nearest-percent rounding bin of ±0.005, clipped at 0 and 1. Conservative coordinate bounds relax the unrounded simplex constraint. Non-overlap cannot be explained by that rounding assumption alone; overlap **does not prove** that a single coherent unrounded joint distribution exists. This is not a statistical significance test.

The stated research objective is uncertainty reduction about the joint D/S state. Because either audit perfectly reveals one binary component, its expected information is H(D) or H(S), computed from r₁. Stopping yields zero. The report records information foregone and whether the chosen query is within 0.01 bits of the maximum, an explicit descriptive tolerance. This comparator does not optimize profit, decision utility or the unknown true generative process.

Matched contrasts compare initial joint probabilities, signal forecasts, post-signal probabilities and research choices. Later audit responses are compared only if the pair chose the same audit. With one realization per format, differences cannot be attributed uniquely to formatting rather than ordinary response variability. Two directions do not identify a negativity trait.

## Conditional report-generating model

The small model family conditions on elicited π and L rather than estimating hidden priors from initial reports. Its parameters describe possible mappings between these reports:

\[
u_1(h)\propto\pi(h)L(h)^w,
\qquad q_1(h)=\kappa u_1(h)+(1-\kappa)u_1(D)u_1(S).
\]

The product term uses the marginal probability corresponding to h. It removes dependence while preserving marginals. w controls signal weight; κ controls retention of dependence. Then q₂ conditions q₁ on the audit (or equals q₁ for stop), and q₃ is the final one-hot joint state. The reporting layer is:

\[
r_0^*=\pi,\qquad r_t^*=(1-\alpha)r_{t-1}^*+\alpha q_t,
\quad t=1,2,3.
\]

The grid is w ∈ {0, 0.5, 1, 1.5, 2} and κ, α ∈ {0, 0.25, 0.5, 0.75, 1}: 125 points. Equal checkpoint squared error is minimized on the joint simplex. This is **descriptive least squares**, not an independent likelihood over four probability entries. Per case there are 12 reported coordinates but only nine simplex degrees of freedom. Report every tied minimizer and its parameter range; no posterior intervals or model-selection significance are claimed.

The full family is compared with w = 1, κ = 1, α = 1 and the fixed (1, 1, 1) reference. Only cases with strictly positive initial joint entries and signal forecasts enter this fit, giving every candidate the same eligible cases and well-defined audit conditionals. Zero-input cases are explicitly listed as fit exclusions and retained in all behavioral results. This restriction can select a nonrepresentative subset. Values of 1 are allowed.

When α = 0, w and κ cannot affect the reports; the fit exposes all 25 tied settings. Other input sets can also be uninformative. A successful fit would not establish these three quantities as unique cognitive mechanisms. In particular, changing interpretations, joint report noise and other omitted processes can mimic the proposed mappings.

## Synthetic validation and version review

This adds `narrative-inference/0.1.0`, `narrative-evaluator/0.1.0`, `narrative-analysis/0.1.0`, and independent collection/trial/report v1 schemas. The main report contract and all earlier evaluator fingerprints are unchanged. Frozen collections bind their implementation and exact manifest bytes.

Recovery uses six declared grid profiles, varied strictly positive synthetic π/L inputs, both audit types, and 16 repetitions per profile. The logical both-state forecast is 1. Checkpoint noise is independent additive SD 0.008 noise, truncated at zero, renormalized and quantized to whole percentages. The new-input prediction comparison uses different synthetic inputs with the same task templates and no observation noise in the target. It is not an empirical held-out test.

Both seeds **20260924 and 20260925** pass the declared checks: all clean profiles uniquely recovered, parameter MAE ≤ 0.1, mean new-input latent prediction RMSE ≤ 1 percentage point, α = 0 nonidentifiability exposed, and an incompatible final-resolution pattern with best RMSE ≥ 8 points. On these runs all sampled grid estimates were exact, giving zero parameter MAE and zero new-input latent prediction RMSE. The incompatible-pattern best fits were **31.254 and 31.773 points**. These easy, coarse-grid synthetic conditions validate implementation and limited recoverability; they do not guarantee recovery with agent/human data, noisier inputs or off-grid mechanisms.

## Run locally

```sh
uv run python -m epistemics.narrative create \
  --directory output/private-narrative --participant output/participant.json
uv run python -m epistemics.narrative serve --directory output/private-narrative --port 8772
uv run python -m epistemics.narrative export --directory output/private-narrative
uv run python -m epistemics.narrative schema
uv run python -m epistemics.narrative validate-synthetic \
  --seed 20260924 --repetitions 16 --output output/narrative-recovery.json
uv run python -m epistemics.narrative simulate --directory output/narrative-synthetic
```

MCP runs as `python -m epistemics.narrative.mcp_server` with `EPISTEMICS_NARRATIVE` pointing to the private collection and `EPISTEMICS_ASSIGNMENT` to one assigned case. Only the evaluator sees the manifest. Export requires all eight cases to be finished. Private results and databases stay outside Git. Browser capability access is a local alpha boundary, not hosted tenant isolation. There is no narrative-module passport issuance adapter yet.

## Literature relationship

The central-versus-auxiliary interpretation follows the credit-assignment question in [Gershman's *How to never be wrong*](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf): surprising evidence can change support for a main claim, its linking assumptions, or both. This module is an original adaptation, not a replication. Its four offered combinations also make the boundary with theory search explicit: [Ullman, Goodman and Tenenbaum](https://www.tomerullman.org/papers/tlss-final.pdf) address search over explanations, which this task does not implement. Simulation and recovery follow the development discipline discussed by [Wilson and Collins](https://elifesciences.org/articles/49547); recovery under the generating family does not establish that family as an adequate account of a real respondent.
