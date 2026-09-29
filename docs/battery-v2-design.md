# Abstract battery v2: a design for showing general traits

Design, 29 September 2026. Since built, preregistered and run: see [the preregistration and results](battery-v2-preregistration.md). The decisions below were taken as recommended (a 78 million token budget, noticing secondary, 24-case sessions).

## Aim

Show whether a configuration's traits carry over to tasks on which they were not measured. The tasks are abstract, and each isolates one latent variable at a time. This follows the direction set on 29 September: general traits first, on abstract tasks. The [trait reanalysis](traits-2026-09-29.md) sets the targets and sizes.

## The test (to be preregistered)

**Unit.** For each target trait, a cell mean per configuration and task: 6 configurations × 6 tasks.

**Primary test: leave one task out.**
- **Prediction:** a configuration's deviation from the other configurations on a held-out task is predicted from its mean deviation on the other five.
- **Pass:** the transfer gain (1 − MSE of the prediction / MSE of predicting no deviation) is above 0, and a within-task permutation test gives p < 0.05. The permutation shuffles which configuration is which within each task, which destroys consistency but keeps task effects.
- **Multiple tests:** Holm correction across the primary traits.

**Secondary tests.**
- **Leave one formal core out (far transfer):** hold out both surface versions of a core (see Tasks), so the prediction comes only from different structures.
- **Near against far:** the gain when the held-out task's twin surface is in the training set, against when it is not.
- **Consistency ρ:** from the generalizability study (configuration, task, configuration × task, session).

**Validity.**
- **Cells:** a cell counts only if its sessions completed and verified.
- **Noticing cells:** also need their per-structure fit to converge (R-hat 1.05 or less).
- **Enough cells:** a trait is tested only if at least 5 configurations and 5 tasks remain.

## Targets

| Trait | Role | Why |
| --- | --- | --- |
| Precision (log report noise) | Primary | Trait-like in the reanalysis (ρ 0.91, gain 0.59). Still needs showing on a balanced design and among closer configurations. |
| Stated–applied fidelity | Primary | A candidate between model families (ρ 0.75, gain 0.40), confounded so far with task coverage. |
| Noticing threshold (prompting needed) | Secondary | Astra needs less prompting than Sol in 3 of 4 structures, but it is underpowered at the recommended size (below). |
| Cue sensitivity | Measured, not tested | It did not transfer in the reanalysis. It comes free with the same sessions. |
| Default for an unstated rate; evidence weight | Measured as constants | No variation between configurations so far (about 50%; γ ≈ 1). |

## Configurations

All six take every task: Astra, Sol (GPT-6, medium effort), Astra-low, Sol-low (low effort), Luna, Terra (GPT-5.6). The configurations are the "subjects". Traits can only be shown where they differ, and the frontier pair alone is at ceiling or identical on several candidates.

## Tasks: three formal cores, two surfaces each

Each formal core has one observer model and one item design. The two surfaces share them exactly and differ only in the story, so a pair of surfaces tests near transfer and different cores test far transfer.

| Formal core | Observer | Surface A (exists) | Surface B (new texts only) |
| --- | --- | --- | --- |
| Dependence: a report may repeat another instead of observing | dependence | Sensors that may copy another sensor's logged reading (urn2) | Observers who may repeat what another observer told them instead of looking |
| Selective withholding: what is missing may be missing for a reason | disclosure | A reporter that may hold back every blue ball it drew (urn2) | Sensors that may transmit only when they read red and stay silent otherwise |
| Uninformative evidence: a reading may not bear on this urn | mismatch | Readings that may come from a different urn than the one they are filed under (urn3 wording) | Readings that may date from before the urn was emptied and refilled |

Each task keeps the salience ladder and the five graded records, from strongly reassuring to strongly suggestive.

**Ceilings.** Selective reporting was noticed almost at once by the frontier pair, so it cannot separate them. It may still separate the weaker configurations, so it stays. Stage 1 below shows each configuration's thresholds on the existing tasks before the new surfaces are collected. A surface B that turns out to be at ceiling for every configuration can then be reworded before Stage 2.

## Per-cell protocol

The minimal ladder, plus a second plain session: 5 sessions per configuration and task, in the current 24-case format.

| Rung | Sessions | Measures |
| --- | --- | --- |
| 0, plain | 2 | precision; noticing |
| 1, named | 1 | precision; noticing |
| 2, named and asked for rates | 1 | precision; noticing; fidelity; default; cue sensitivity |
| 3, named, asked and probed | 1 | the same |

Noticing per cell comes from the per-structure second-layer fit (`structure_check`), with a θ uncertainty of about ±0.5 rungs.

## Size and power

Six configurations, the primary test above (`uv run python -m epistemics.ledger traits-power --output output/traits-power-20260929.json`). The variance components are the reanalysis estimates. With no trait, the test passes 5.75% of the time.

| Tasks | Sessions per cell | Precision | Precision, if configurations differ only as much as Astra and Sol | Fidelity | Noticing (σ config 0.37 / 0.5) |
| --- | --- | --- | --- | --- | --- |
| 3 | 5 | 0.92 | 0.63 | 0.61 | 0.23 / 0.41 |
| 4 | 5 | 0.97 | 0.79 | 0.78 | 0.39 / 0.57 |
| **6** | **5** | **0.99** | **0.92** | **0.91** | **0.62 / 0.79** |
| 6 | 2 (rate-asking sessions only) | 0.95 | 0.78 | 0.91 | not measured |
| 6 | 11 (full ladder) | 0.99 | 0.92 | 0.91 | 0.80 / 0.93 |

**Six tasks are needed.** With three or four, only precision is safe. Noticing reaches about 0.8 only with the full ladder, which would more than double the cost. Hence its secondary role.

## Cost

Every configuration uses about 0.5 million input tokens per session (medians 0.49–0.53 million).

| Plan | New sessions | Tokens |
| --- | --- | --- |
| **Recommended: 6 × 6 at 5 sessions per cell**, reusing Astra's and Sol's existing sessions on the three existing tasks (same texts) | 150 | about 78 million |
| &nbsp;&nbsp;Stage 1: the three existing tasks for Astra-low, Sol-low, Luna and Terra | 60 | about 31 million |
| &nbsp;&nbsp;Stage 2: the three new surfaces for all six configurations | 90 | about 47 million |
| Cheaper: 6 × 6 with only the 2 rate-asking sessions per cell (precision and fidelity; no noticing) | 60 after reuse | about 31 million |
| Noticing at full power: the full ladder (11 sessions) in every cell, reusing what exists | about 340 | about 175 million |

**Staging.**
- **Stage 1** gives a balanced 6 × 3 crossing on the existing tasks. The precision test is already adequately powered there (0.86–0.92).
- **Stage 1 also shows** where the weaker configurations sit on the noticing ladder before the new surfaces are finalised.
- **Stage 2** completes the 6 × 6 design for the preregistered test.

## What has to be built

1. **Report-noise grid below 0.05** (0.01, 0.02, 0.03). Many frontier sessions sit at the current floor. Reports are whole percentages, so values below about 0.02 are only partly identified, and recovery will show how far down the grid is informative. This is disposition model 0.6.0, with recovery validation on two seeds.
2. **Surface B renderers for the three cores** (battery 0.14.0). New texts only: the same designs, observers and records' grading. They need the rendering audit, the wording checks (a structure is stated only in its named sentence) and task validation on two seeds.
3. **Analysis.**
   - The `traits` command reads v2 tasks as core × surface and adds the leave-one-core-out test and the Holm correction.
   - Noticing cells come from the per-structure fits, which record the core and surface.
   - Recovery: synthetic configurations with known traits, through the real designs and fits, at this design's size. The preregistration adopts that, not the surrogate power alone.
4. **Runner presets** `traits-stage1` and `traits-stage2` (the runner's admission reserve is 0.8 million tokens per run in a batch, so caps must include it).
5. **Preregistration,** committed before Stage 2. Stage 1 is described as a calibration stage: it informs only the surface-B wording and the ceiling checks, not the test.

## Decisions for you

1. **Budget:**
   - the recommended 78 million tokens (31 million now, 47 million after the build);
   - the cheaper 31 million without noticing;
   - or something between.
2. **Noticing:** accept it as a secondary test at about 0.6–0.8 power, or plan for the full ladder later.
3. **Session length:** stay with the 24-case format (validated, and allows reuse). A 12-case format might roughly halve tokens per session, but it needs new designs and validation, and it gives up the reuse. I would stay with 24.
