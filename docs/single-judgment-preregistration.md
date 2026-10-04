# Single-judgment transfer: preregistration

Written 4 October 2026, before any data for this test were collected. Motivation: the [abstract-to-finance test](finance-transfer-preregistration.md#results-4-october-2026) and the post hoc follow-up in the [exploration log](exploration-log.md) (4 October, idea 36).

## Background

The preregistered abstract-to-finance test passed only as a difference between model families: GPT-5.6 rounds its probabilities more than GPT-6, in both domains. Within each family there was no transfer. Its abstract measure mixed two things:
- base-rate questions, which every configuration answers fine-grained;
- urn calls, on which Astra and Sol are level and which GPT-5.6 often gives no weight.

Post hoc, open single judgments in abstract vignettes (the open-inference screens) and in finance (an economist's forecasts, central-bank statements) separated Astra from Sol at every effort in both domains (within GPT-6 ρ 0.77, p 0.051). Those data came from collections days apart, with the tasks chosen after the sweep. This test repeats the comparison on fresh data, specified in advance.

## Hypotheses

Round readout is the share of answers given at multiples of 0.05. As before, it describes how precisely a configuration reports probabilities in these tasks, not what it believes.

**Co-primary.**
- **H1.** Within GPT-6, Astra rounds its open single judgments more than Sol, in the abstract vignettes and in the finance judgments.
- **H2.** Within GPT-5.6, Luna rounds its open single judgments more than Terra, in both domains.

A hypothesis passes if its difference is positive in both domains, its intersection-union p is below the Holm threshold, and the Holm-adjusted p is below 0.05. The intersection-union p is the larger of the two domains' one-sided p values. H1 and H2 are Holm-adjusted together.

**Secondary.**
- **S1.** Configuration-level transfer within families: the mean of the two within-family Spearman ρs (six configurations each) between abstract and finance readout. The p is exact under independent permutation within each family.
- **S2.** Spearman over all twelve configurations, with a permutation p.

Both are reported without correction and with their power stated (low for S1).

## Data

**Preset** `single-judgment-transfer`, tasks 0.43.0 (design 0.31.0, model 0.21.0). Every session is fresh, and no earlier session is used.

**Configurations:** the twelve of the abstract-to-finance test: Astra, Sol, Luna and Terra, each at low, medium and high effort.

**Sessions per configuration: 5 abstract, 12 finance; 204 in total.**

| Domain | Modules | Variant | Sessions |
| --- | --- | --- | --- |
| Abstract | `screen-gen-a`, `screen-num-a`, `screen-choice-a`, `screen-lists-a`, `screen-trend-a`: open-inference vignettes (number processes, durations, inspections, pumps, tanks) | `screen` | 1 each |
| Finance | `wording-policy-a` to `-d`: an economist's forecast of a central bank's decision | `wording` | 2 each (repeats 1 and 2) |
| Finance | `announced-a` to `-d`: a central bank's statement with one change | `announced` | 1 each |

Cases are separate and in random order. The runner shuffles sessions across the collection.

**Roots.** The runner limits a root to two hours, so the 204 planned runs are collected in four roots of 51 run one after the other: `output/single-judgment-20261004-1` to `-4`. Each holds every fourth run of the preset's list in order, under the same frozen implementation. Long collections are kept awake with `caffeinate`.

**Validity.**
- A session counts if it completed and verified. Failed sessions are re-collected once in a top-up root.
- Missing round-readout values (fewer than five qualifying answers) are not replaced.

## Measures

The code is `ledger.single_judgment`, committed with this document.

- **Round readout per session.**
  - The share of answers at a multiple of 0.05, among answers between 0.06 and 0.94 inclusive.
  - Abstract: the screen vignettes' open cases only. Anchors, fixed and computable cases are excluded (`ledger.sweep.case_class`).
  - Finance: answers that differ from the case's stated prior.
  - A session with fewer than 5 such answers has no value.
- **Configuration value** (S1, S2): the mean of its sessions' values in a domain.

## Tests

- **Variant contrast** (H1, H2), per domain.
  - The statistic is the mean over the three effort levels of (mean session readout of the first-named variant − that of the second). At each effort level the sessions of the two configurations are compared.
  - The one-sided p comes from 20,000 permutations of variant labels among each effort level's sessions (seed 20261008).
- **S1:** the exact null of the mean of two independent six-configuration Spearman ρs.
- **S2:** 20,000 random orderings.

```bash
uv run python -m epistemics.ledger single-judgment-preregistered output/single-judgment-20261004-1 output/single-judgment-20261004-2 output/single-judgment-20261004-3 output/single-judgment-20261004-4 --output output/single-judgment-preregistered-<date>.json
```

## Power

From `uv run python -m epistemics.ledger single-judgment-power --output output/single-judgment-power-20261004.json`.

**Model:**
- a true Astra − Sol difference in each domain;
- configuration SD 0.05 within a variant;
- session SD 0.21 (the pooled within-configuration SD of the finance single-judgment sessions in `output/finance-transfer-20261004*`).

Power is the chance that both domains pass. It is given at α 0.025, the Holm threshold when this hypothesis has the smaller p, and at 0.05.

| Difference (abstract, finance) | 5 + 8 sessions | 5 + 12 sessions (this design) |
| --- | --- | --- |
| 0.36, 0.17 (the post hoc estimate) | 0.72 / 0.81 | 0.83 / 0.90 |
| 0.25, 0.12 (about 70% of it) | 0.41 / 0.53 | 0.50 / 0.65 |
| None | 0.00 / 0.01 | 0.00 / 0.01 |

The post hoc estimate is likely inflated, having been picked from many comparisons. If the true difference is about 70% of it, power is 0.50–0.65. The finance contrast is the binding one.

H2's post hoc difference is larger: Luna 0.93–1.00 against Terra 0.53–0.61 in finance, and screens 0.94 against 0.72 at medium effort.

## What the outcomes mean

- **H1 passes:** within GPT-6, Astra's rounder readout carries from abstract vignettes to finance judgments. That would be a variant-level trait with transfer, inside one model family. The passport could say so for Astra and Sol, conditional on single open judgments.
- **H2 passes:** the same for Luna against Terra within GPT-5.6.
- **A hypothesis fails:** that variant-level transfer is not established at this power. If the difference has the right sign in both domains, that is reported.
- **S1:** configuration-level transfer, including effort, is secondary. A failure there is expected at its power and is not evidence against H1 or H2.

## Frozen implementation

**Tasks fingerprint:** `e6df10095005470df558edaa711ce528344fbe9e61fef849c75e99c91817aa32` (disposition-tasks/0.43.0).

**Task validation 0.43** passed on both seeds (4,656 cases, 199 contexts):

| Seed | File | SHA-256 |
| --- | --- | --- |
| 20260927 | `output/disposition-validation-0.43-20260927.json` | `8b3932dddadaa91d4bb37acb70b89703d0b23d0a47c9c4867968350f1ad15073` |
| 20261027 | `output/disposition-validation-0.43-20261027.json` | `91bac83ac9e031886ed5216a3b8b9df3b7c554302da6c5e151e53c39cd053daa` |

This document and the analysis code (`src/epistemics/ledger/single_judgment.py`, with `tests/test_single_judgment.py`) are committed together, before collection. Deviations, if any, are reported with the results.
