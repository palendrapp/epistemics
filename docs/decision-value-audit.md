# Expected decision value and starting-report calibration audit

27 September 2026. Analysis version `source-value-audit/0.1.0`. This is an offline simulator audit of the existing `source-verification/0.2.0` task, following the [negative cost-aware comparison](cost-aware-results-2026-09-26.md). It changes no participant task, purchase rule, accepted answer, report schema or passport claim. No account-backed respondent collection is part of this audit.

## Questions and information boundaries

1. Does the existing task offer checks worth their price, even when the source process is known?
2. How much value does the specified observer achieve using only public histories?
3. Can distorted starting reports cause poor purchases or actions despite correct subsequent sample incorporation?
4. How often does a beneficial expected policy lose on only two independently generated worlds?

The **known-process oracle** receives the current company prior and source report, plus the source's actual measurement accuracy and selection rule. It receives neither current company truth nor the independent panel realization when predicting or selecting a check. It is an upper-information reference, not a fair description of what respondents knew.

The **public observer** is the existing `joint_process` observer: a uniform prior over 25 combinations of five measurement accuracies and five selection rules, updated using the displayed resolved archive and earlier company resolutions. It gets the current public report and prior. It does not know that the generator permutes exactly six particular processes across source identities. This is one specified public-information model, not an assertion that all rational public observers must agree or that its prior matches the generator.

The public-input type contains resolved history, a truth-free probe, threshold and price. The oracle function separately requires a source process. Realized scoring is a separate function. Changing the current hidden outcome or panel cannot change either prediction. Every previous outcome is revealed after its final decision under all three policies. Conditional on that outcome, independent panels add no source-process information. Thus this specified synthetic observer has the same source-learning history under all policies; no trajectory is assembled from real-agent answers.

## Exact expected-value model

Let \(H\in\{0,1\}\) indicate strong demand, \(x\) the published source count, \(\pi\) the company prior and \(\theta\) the true source process. The privileged reference probability is

\[
q=P(H=1\mid x,\pi,\theta)
=\frac{\pi P_\theta(x\mid H=1)}{\pi P_\theta(x\mid H=1)+(1-\pi)P_\theta(x\mid H=0)}.
\]

The source-count likelihood includes per-customer measurement errors followed by random, maximum or minimum panel selection, exactly as in the existing generator. The public observer integrates that likelihood against its posterior over source parameters.

Let \(r\) be the starting probability report, \(t\) the investment threshold and \(c\) the offered price. An independent count \(K\) has \(f_1(k)=\operatorname{Binom}(k;5,.7)\) and \(f_0(k)=\operatorname{Binom}(k;5,.3)\). The synthetic respondent incorporates a supplied sample as

\[
r_k=\frac{r f_1(k)}{r f_1(k)+(1-r)f_0(k)},\qquad
a_0(r)=\mathbf 1[r>t],\qquad a_k(r)=\mathbf 1[r_k>t].
\]

Decline on exact payoff ties. The existing selective rule buys if its **subjective** expected sample value exceeds price by more than \(10^{-12}\):

\[
\operatorname{EVSI}(r,t)=\sum_{k=0}^{5}\max\{0,r f_1(k)(1-t)-(1-r)f_0(k)t\}-\max\{0,r-t\}.
\]

Actual expected payoffs under the generator, before the check outcome exists, are

\[
N_r=(q-t)a_0(r),\qquad
G_r=\sum_{k=0}^{5}[q f_1(k)(1-t)-(1-q)f_0(k)t]a_k(r),
\]
\[
V_r=(1-b)N_r+b(G_r-c),
\]

where \(b\) is 0 for none, 1 for always, or the report-based purchase indicator for cost-aware. The primary contrast is \(V_r-N_r\), paired with that same reporter's own no-check action. This integrates both possible company states and every sample count, not just the generated realization.

The known-process optimum is \(V^*=\max(N_q,G_q-c)\). Decompose total expected regret without double-counting:

\[
R_{\mathrm{purchase}}=V^*-[(1-b)N_q+b(G_q-c)],
\]
\[
R_{\mathrm{action}}=[(1-b)N_q+b(G_q-c)]-V_r.
\]

Both are nonnegative up to numerical precision; they sum to \(V^*-V_r\). The first holds actions optimal given the reference information and attributes regret to purchase selection. The second holds the actual purchase fixed and attributes regret to subsequent or no-check actions. Neither is a fitted cognitive parameter.

Realized payoff uses the generator's actual \(H,K\), the same synthetic rule and the same prices, separately from these expectations. Repeating an identical sample cannot reduce its outcome luck. The audit instead draws independent worlds and examines nonoverlapping pairs.

## Synthetic reporters and calibration

Eight predeclared reporters:

| Reporter | Starting report |
| --- | --- |
| Oracle | \(q\) |
| Rounded oracle | \(q\) rounded to one percentage point |
| Public | Public-history joint observer probability |
| Rounded public | Public probability rounded to one percentage point |
| Underconfident control | \(\sigma(.6\operatorname{logit}q)\) |
| Overconfident control | \(\sigma(1.6\operatorname{logit}q)\) |
| Optimistic control | \(\sigma(\operatorname{logit}q+.8)\) |
| Pessimistic control | \(\sigma(\operatorname{logit}q-.8)\) |

All controls incorporate a supplied sample with the same Bayesian formula. They isolate starting-report distortion, not a slow-update mechanism. Rounded controls round the starting report only; final actions use the unrounded conditional posterior. This separates input quantization from final response-grid effects and does not simulate all real-agent reporting behavior.

Mean \((r-q)^2\) is expected excess Brier loss relative to privileged prediction. **It is not by itself a calibration measure**: a calibrated less-informed observer can differ from \(q\). Separately, ten fixed probability bins report mean forecast, expected frequency (mean \(q\)), and realized frequency (mean \(H\)). Expected and realized frequency-minus-report errors receive world-clustered Monte Carlo standard errors. The expected binned absolute gap validates that the controls exhibit their intended distortions. Binning can conceal within-bin error, and finite-sample empirical absolute gaps are biased upward. No calibration map is learned or applied to real respondents.

## Frozen cohort and interpretation rules

Two batches, seeds **20260927 and 20270927**, each **512 independent worlds**: 1,024 worlds and 12,288 later-company cases. Seeds identify pseudorandom streams, not collection dates. Each world retains 12 initial companies, 12 later companies and the full public archive. World and price seeds use separate SHA-256-derived channels. Prices remain balanced: four each at .01, .04 and .20 per world, with the unchanged incomplete crossing over company priors and payoff thresholds. No outcome-based world selection or stopping.

Compare all eight reporters under none, always and cost-aware. Report pooled and separate-batch world means, world standard deviations, normal 95% Monte Carlo intervals and realized-minus-expected residuals. These intervals describe numerical sampling of the specified simulator, not uncertainty about real agents or external workflows. Consecutive, nonoverlapping pairs within each batch estimate the frequency of a negative realized selective-minus-none contrast over two worlds. Policies and reporters share worlds; those comparisons are paired, not independent replications.

Show opportunity coverage by price and by the **rounded public observer's** predicted EVSI minus price: nonpositive, positive but below .01, and at least .01. Strata use information available before current outcomes or sample realizations; selection never uses favorable realized checks. Conditional stratum means are descriptive, not a new participant success gate.

Compare oracle and rounded-public expected mean gains with the earlier **.01 points/company** target. If even the oracle falls below it, an unchanged unconditional comparison is a poor next experiment for that target. If the public observer falls below it, improve or reassess the comparison before more collection. A favorable simulator screen would justify designing, not automatically launching, a bounded real-agent comparison. The estimated world count for a normal .005 half-width is a simulator precision illustration, not a power calculation for real agents.

## Validation and version review

The analysis lives in a new module; participant-facing experimental versions and all previous implementation fingerprints are unchanged. There are no new fitted parameters, so this increment does not claim parameter recovery. Existing recovery evidence remains version-bound. New diagnostic validation uses exact rational enumeration independent of the implementation, an independent Bernoulli/binomial Monte Carlo check, known calibrated/distorted controls, oracle optimality, nonnegative regret and decomposition identities, public-boundary and history-timing tests, price balance, separate deterministic seeds, immutable artifacts and rejected implementation drift.

The runner exclusively creates `plan.json`, then exact-byte-bound `cases.json`, `worlds.json` and `summary.json`. Identical retries are safe; conflicting bytes are refused. These evaluator-side artifacts remain in ignored `output/`. Freeze and publish the implementation/plan before the main audit. Execution uses no provider API, network, payment or on-chain action.

```sh
uv run python -m epistemics.source_value_audit plan output/value-audit-20260927
uv run python -m epistemics.source_value_audit run output/value-audit-20260927
```

See the separate dated plan for exact commitments and the completed result document once available.
