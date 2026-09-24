# Related judgments: a bounded diagnostic

Implemented 23 September 2026 as a separate development module, `auxiliary-diagnostic/0.1.0`, with evaluator and analysis versions `auxiliary-diagnostic-evaluator/0.1.0` and `auxiliary-diagnostic-analysis/0.1.0`. Existing investigation 0.1–0.3 implementations, fingerprints and reports remain unchanged. This module is not yet a released passport dimension.

The separate [0.2 diagnostic](auxiliary-diagnostic-v2.md) adds matched archive presentations and uncertain evidence. Its implementation leaves this version and existing human collections unchanged.

The [completed investigation pilot](investigation3-results-2026-09-23.md) showed larger changes in company forecasts than in source or backlog judgments. That pattern has several explanations. A respondent might expect little relationship between those events, expect a relationship but propagate little evidence through it, or adjust its reported numbers gradually. This diagnostic elicits observations that can separate those explanations under a small declared model family. It does not identify a unique internal cognitive mechanism.

## Eight cases, four checkpoints

Cross two auxiliary targets (backlog and an understatement in a source's initial revenue bulletin), two archive structures (associated and independent), and two growth audit results (above 10% and not above 10%). Within each of the four pairs, both audit outcomes are held fixed; only archive association and the case identifier differ. Each archive contains all 40 comparable companies with balanced event marginals. Associated backlog counts imply positive association, while associated source-understatement counts imply negative association. These signs are confounded with target and are **not** a negativity or framing contrast.

1. **Background and expectations:** report growth and auxiliary probabilities, plus the auxiliary probability conditional on each possible growth audit result. Exact population likelihoods and causal mechanisms are not disclosed.
2. **Growth resolved:** a definitive audit establishes the growth event. Report both probabilities again.
3. **Same information:** explicitly no new document, business period or hint. Report both probabilities again.
4. **Auxiliary resolved:** a separate definitive audit establishes the auxiliary event. Report both probabilities again.

The full collection has 32 checkpoints and 80 probability reports. The archive is empirical evidence; it is not a disclosed population likelihood. The conditioning and direct-resolution stages are deliberately strong diagnostic controls. This is a constrained supplement to the richer discovery investigation, not a replacement for active research, uncertain sources or causal hypothesis generation. Neither an observed association nor a conditional probability determines a causal graph.

Cases and resolutions are authored balanced contrasts, not random draws from a portfolio population. The final auxiliary outcome is hidden until the final checkpoint. Both conditions within a pair share it. A private seed randomizes order and the balanced resolutions; neither seed nor assignment conditions is exposed to participants. Fresh agent cases should have independent contexts. Humans participate continuously, with carryover explicitly recorded.

## Interpretable observations before model fitting

The report preserves a row for each case with:

- Conditional spread: reported auxiliary probability given growth minus that given no growth.
- Initial mixture gap: initial auxiliary probability minus the mixture implied by the two conditionals and reported growth probability.
- Conditional transfer gap: the auxiliary report after the growth audit minus the corresponding earlier conditional forecast.
- Change on the neutral repeat, direct auxiliary-resolution error, and growth-resolution errors.

These quantities describe reports and their consistency. A transfer gap is conditional on understanding the questions and the audit, and on the earlier conditional retaining its meaning. It does not automatically diagnose a bias. Eliciting conditionals can itself encourage consistency; repeated questions may prompt additional computation. The module does not measure spontaneous discovery behavior without those prompts.

## Explicit candidate models

Let `d` be the archive's signed conditional deviation from 0.5: +0.3 for associated backlog, −0.3 for associated source understatement and 0 for independent archives. Let `x` be the resolved growth event and `a` the resolved auxiliary event. The three development parameters are association scale β, propagation fraction ρ and report adjustment α:

\[
c_+=0.5+\beta d,\qquad c_-=0.5-\beta d,\qquad
m=0.5+\rho(c_x-0.5).
\]

\[
r_1=0.5+\alpha(m-0.5),\quad
r_2=r_1+\alpha(m-r_1),\quad
r_3=r_2+\alpha(a-r_2).
\]

Here `r1`, `r2` and `r3` predict auxiliary reports after the growth audit, neutral repeat and direct auxiliary resolution. The latent report trajectory is deterministic under each parameter set; observation noise does not feed back into its state. β ranges from 0 to 1.5 by 0.25, and ρ and α from 0 to 1 by 0.25. Report likelihoods use 0.01 rounding bins under a logistic-normal observation model with fixed logit SD 0.25 and censored endpoints. The likelihood implementation is shared with the earlier investigation.

Four model families are reported: the full model, association-only (ρ=α=1), selective propagation (α=1), and report smoothing (ρ=1). All five modeled observations per case—the two initial conditionals and three later auxiliary reports—enter the joint fit. Initial marginal and resolved-growth reports are model checks, not fitted observations. The fixed initial auxiliary probability of 0.5 is an assumption; the report shows the maximum observed departure from it. We do not silently condition on a noisy initial report as if it were a persistent internal prior.

The first indirect update identifies only the product αρ given β. A second elicitation and direct resolution provide additional constraints. When β=0 or α=0, ρ is structurally unidentifiable; the output flags this and counts equally scoring grid points. This is not a calibrated uncertainty interval. The nested association-only family may tie the larger families; a tie is not successful unique model recovery.

The equations are an authored diagnostic adaptation. The design/recovery workflow follows [Wilson and Collins (2019)](https://elifesciences.org/articles/49547); the broader rationale is in our [primary-literature review](cognitive-modeling-review-2026-09-20.md). This is not a replication of a published instrument or a validated phenotype.

## Validation and release boundary

The offline recovery command generates association-only, selective-propagation, smoothing and combined profiles. Fits use one eight-case collection; restricted-family comparisons use independently noisy reports on another balanced collection without refitting. Those collections share archive templates, so this is simulation recovery, not new-domain generalization. Declared gates are parameter MAE ≤0.20 and distinct-family recovery ≥75%. Nested association-only ties are reported separately and excluded from that distinct-family gate. Zero-association degeneracy is explicitly checked.

Default validation uses 32 repetitions per generating profile, or 128 generated datasets per seed. Recovery does not establish robustness to unknown noise, heterogeneous response strategies, lapses, different direct-audit treatment or baseline misspecification. The [fresh-agent acceptance](auxiliary-acceptance-2026-09-23.md) is complete: eight separate contexts supplied all 80 reports in 5 minutes 33 seconds, with zero conditional-transfer gaps, neutral-repeat changes or direct-resolution errors. All four families tie at β=ρ=α=1. This demonstrates consistency on the explicit controls, not unique model recovery or an explanation of the richer investigation's residuals. Actual human acceptance remains pending. All `model_parameters_are_passport_traits` and `empirical_predictive_validation` flags remain false.

Both implementation checks (seeds 20260923 and 20260924) pass. Association-scale MAE is 0.0039 / 0.0000, propagation-fraction MAE is 0.0254 / 0.0352, and report-rate MAE is 0 / 0. Distinct selective-propagation versus smoothing profiles are recovered in all 64 comparisons per seed. Association-only ties remain visible. These are intentionally separated synthetic profiles on the declared grid, not evidence of comparable precision for real participants. Recovery artifacts bind implementation fingerprint `3e5584987011181d97894a2af47a0a15fc967a1e0f127b5551424075055b29e1`.

The repository checks pass (259 Python tests and 37 TypeScript tests). Diagnostic tests cover two-seed recovery, degenerate parameters, the first-update ambiguity, manifest/trial integrity, concurrent duplicate submissions, resume, actual MCP transport and the whole browser collection through private HTTP. A synthetic browser case was also inspected interactively. Actual human acceptance remains pending.

## Run locally

```sh
uv run python -m epistemics.diagnostic create --directory output/diagnostic --participant participant.json
EPISTEMICS_DIAGNOSTIC=output/diagnostic EPISTEMICS_ASSIGNMENT=CASE_ID \
  uv run python -m epistemics.diagnostic.mcp_server
uv run python -m epistemics.diagnostic export --directory output/diagnostic
uv run python -m epistemics.diagnostic validate-synthetic --seed 20260923 --output output/diagnostic-recovery.json
uv run python -m epistemics.diagnostic schema
```

For human participation, create a separate collection with a human descriptor, then run `uv run python -m epistemics.diagnostic serve --directory output/diagnostic-human --port 8769`. Open its private URL. The browser uses whole percentages and the same immutable answer service as MCP. Collection and export remain private. Synthetic previews must be created with `--synthetic` and never counted as human acceptance. MCP exposes five case-bound tools; no export, seed, future-resolution or collection-inspection tool is available.
