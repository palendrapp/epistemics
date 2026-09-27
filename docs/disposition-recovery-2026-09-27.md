# Disposition model recovery: T2, T3 and T5 — 27 September 2026

**The first three modules of the [generative model](epistemic-generative-model.md) are identifiable under their specified observers.** This is step 1 of its development sequence: specification and synthetic recovery, with no respondent collection.

In the agent-like noise band, two independent seeds of 200 simulated respondents each recovered the three disposition parameters:
- **Dependence prior δ:** recovered well only with structure probes. From forecasts alone, recovery was marginal.
- **Suspicion of silence σ:** recovered from forecasts alone.
- **Value of certainty λ_c:** recovered from willingness to pay (WTP) for checks.

Model recovery against each heuristic rival was 97–100% accurate. Both seeds passed every declared gate.

These results come from synthetic respondents drawn from the fitted model families. They validate the measurement design, not any agent's or human's behavior.

## What was specified

The package `epistemics.dispositions` implements disposition-model/0.1.0 and disposition-design/0.1.0.

| Module | Observer (free parameter) | Heuristic rival | 24 checkpoints |
| --- | --- | --- | --- |
| T2 Ambiguous corroboration | Prior δ that a matching report relays the first; a relay copies its source exactly, so it cannot conflict with it | Fixed discount on the second report, blind to the wording cue and to conflict | 4 single reports, 4 conflicting pairs, 16 matching pairs across 7 wording-cue strengths |
| T3 Silence | Prior σ that the sender is selective (shares good items, withholds bad ones), against random omission at a stated rate | Each withheld item counts as a fixed fraction of a bad item | 16 forecasts with only good items shared; 8 controls, 4 of which share a bad item and so reveal a non-selective sender |
| T5 Value of certainty | WTP = ν × decision value + λ_c × expected certainty gain | Linear certainty \(\lvert 2p-1\rvert\) against negative entropy | 24 checks with stated posteriors: 6 decision-relevant, 18 with zero decision value, 9 of them with both outcomes on the same side of 50% |

Every module shares the rest of the observer:
- **Evidence sensitivity γ:** scales every stated likelihood ratio, including the wording cues.
- **Forecast bias b:** a shift toward high demand, which does not apply to probes.
- **Report noise τ:** in log-odds, with reports rounded to whole percentages.

T5 states the posterior after each check outcome, so its decision value is computable and λ_c is separated from misestimated value. WTP is in whole points, and any latent value below half a point is reported as zero.

The **probe designs** replace six redundant forecasts with structure probes, so every design stays at 24 checkpoints:
- **T2:** "how likely is it that the second outlet relayed the first?"
- **T3:** "how likely is it that this sender is selective?"

## Recovery design

Every fit uses a grid posterior under uniform priors (δ and σ in steps of 0.05; λ_c in steps of 4 points).

**Parameter recovery.** Each seed simulated 200 respondents per design, drawn from uniform generating ranges:

| Parameter | Generating range |
| --- | --- |
| δ, σ | 0–1 |
| γ | 0.6–1.4 |
| b | −0.4 to 0.4 |
| τ | 0.05–0.8 |
| λ_c, linear | −20 to 80 |
| λ_c, entropy | −40 to 160 |
| ν | 0.6–1.4 |
| WTP noise | 1.5–12 points |

Results are split into two bands:
- **Agent-like noise:** τ ≤ 0.5, about 12 points at 50%, or WTP noise ≤ 7 points. Earlier collections put Astra near τ = 0.1 and Sol near 0.3.
- **Human-like noise:** the remainder.

**Model recovery.** 100 datasets per model, scored only where the rivals' predictions differ:
- δ in 0.25–1 against a discount weight in 0–0.75;
- σ and the skepticism weight each in 0.25–1;
- λ_c in 30–80 (linear) or 60–160 (entropy).

**Boundary cells.** δ and σ at 0, 0.5 and 1, with the ideal observer (γ = 1, b = 0) at τ = 0.1 and 0.3, 25 repetitions each.

**Gates, declared before the runs:** in the agent band, disposition correlation ≥ 0.9, mean absolute error ≤ 0.1 (λ_c: ≤ 10% of its range), 90%-interval coverage ≥ 0.8, and model recovery ≥ 0.85.

The first gate set also had a coverage ceiling of 0.98. A 20-respondent dry run failed T5 only on that ceiling (coverage 1.0). Grid intervals span whole cells, so over-coverage is built in, and the ceiling was removed before either recorded run.

## Results

Ranges span the two seeds. Agent-like noise band, forecast designs unless stated.

| Module | Disposition r | Absolute error | 90% coverage | Error correlation with γ (T5: with ν) | Rival identified |
| --- | --- | --- | --- | --- | --- |
| T2, forecasts only | 0.92–0.93 | 0.070–0.077 | 0.87–0.93 | 0.85–0.86 | 97–100% |
| T2, with probes | 1.00 | 0.018–0.020 | 0.89 | 0.42–0.56 | — |
| T3, forecasts only | 0.98 | 0.040–0.042 | 0.93–0.95 | −0.43 to −0.32 | 98–100% |
| T3, with probes | 1.00 | 0.016–0.017 | 0.93–0.94 | −0.18 to 0.01 | — |
| T5, linear certainty | 0.98–0.99 | 3.0–4.0 points | 0.98–0.99 | −0.59 to −0.42 | 98–100% |
| T5, entropy certainty | 1.00 | 4.2–4.5 points | 0.96–0.98 | −0.42 to −0.41 | 100% |

In the human-like band, δ from forecasts alone fell to r = 0.79–0.82; with probes it stayed at 0.98–0.99. σ held at 0.93 from forecasts. λ_c held at 0.96–0.99.

**Boundary cells.** The ideal observer was recovered in every cell, with mean absolute error at most 0.03 at τ = 0.1 and 0.08 at τ = 0.3. The exception was δ = 1 at τ = 0.3, which shrank to 0.90–0.91: the posterior mean is pulled inward at a grid edge. Its coverage was 0.92.

## Findings

1. **T2 needs relay probes.** From forecasts alone, a respondent who overweights evidence looks like one who assumes reports are independent: the δ and γ errors correlate at 0.85. Six probes break the trade-off and bring absolute error from 0.07 to 0.02. They matter most at human-like noise. This answers decision 3 of the design: **include structure probes**. They are probability reports about how evidence was generated, not self-descriptions.
2. **Silence is identified from forecasts.** Revealing one bad item exonerates a sender's omissions for the Bayesian observer but not for the heuristic. That contrast separates the two nearly perfectly. Probes still tighten σ.
3. **The certainty functions are distinguishable, so fit both.** Linear certainty gives zero value to a check whose outcomes stay on one side of 50%; entropy values any informative check. With those items in the design, the generating function was identified in 97–100% of datasets where λ_c was material. This answers decision 2: **fit both functions per respondent** and read λ_c within the selected one; their scales differ.
4. **Asymmetric stakes are necessary.** At a 50% action threshold, linear certainty value is proportional to decision value, so λ_c would be indistinguishable from stakes sensitivity. The design uses thresholds of 30%, 50% and 70%.
5. **The weight on decision value is weakly identified** (r = 0.53–0.72), and its errors trade off against λ_c. λ_c itself stays well recovered because the zero-decision-value checks carry it. A respondent who misvalues decision-relevant checks is described by ν, but only coarsely.

## What this does not show

- **Correctly specified respondents.** Simulated respondents follow the fitted families; misspecification was tested only against the named rivals.
- **No real respondents.** Nothing here shows that any agent has stable δ, σ or λ_c, that they survive rewording, or that agents will commit to a probability when a base rate is missing.
- **No rendered tasks.** The modules are specified as numbers. Rendering them as checkpoint tasks, and checking comprehension, comes next.

## Next

1. **Render the modules.** T2 with probes, T3 and T5 become compact checkpoint tasks through the existing interface, with paraphrase variants for the reliability check.
2. **Agent acceptance with test–retest.** Astra and Sol at medium and low effort, plus Luna and Terra, in fresh repeated contexts. This needs account-backed runs and your approval.
3. **Build T4 (HGF) offline in parallel.** Coupling κ stays fixed.

The bounded estimation collection for weaker configurations is deferred behind this track.

## Commitments

Reproduce with `uv run python -m epistemics.dispositions --output <empty directory> --seed <seed>` (200 respondents, 100 model-recovery datasets per model, 25 boundary repetitions).

| Artifact | SHA-256 |
| --- | --- |
| Implementation fingerprint | `eeb2adaa1070688d3ec909b72e9d28939bddaa1cfd3ab8237c22b976321306e1` |
| Validation, seed 20260927 | `8a82fe0305b7c577e722300f2086ea3cc2662f53a8f6e43b9f47212c70758381` |
| Validation, seed 20261027 | `aef06a53e0bae1eceacddca2ccb3338558a184cfe7855f1408012eb363143cdf` |

Validation outputs remain in the ignored `output/` directory.
