# Abstract-to-finance transfer: preregistered test (design)

Written 4 October 2026. This is the design. The preregistration is written from it, with the decisions below settled, and committed before any data are collected.

## Why

The product needs traits that carry across settings. A post hoc check on data already collected ([exploration log](exploration-log.md), 4 October; `uv run python -m epistemics.ledger finance-transfer`) asked whether a configuration's place on a trait in abstract (urn) tasks predicts its place in finance tasks. Finance here means market newsletters and company disclosure, central-bank statements and an economist's forecasts.

| Trait | Exploration result |
| --- | --- |
| Round readout | Carries. The same order of four configurations in abstract and finance tasks (ρ 1.00), and on each finance task separately. ρ 0.76, p 0.018 across eight configurations (general vignettes against central-bank statements). |
| Stated–applied gap | Carries in who has one: Luna, then Terra; Astra and Sol near zero. ρ 0.80, four configurations. |
| Sensitivity to verbal confidence | Only at the ends: Astra low and Terra high in both; Luna moves from the middle to the top. ρ 0.40. |

The data were already seen and the hypotheses came from them, so none of this is a claim. Three weaknesses drive the design:
- **Few configurations:** four for the primary checks.
- **Model family:** most of what carried separates GPT-5.6 from GPT-6, with only two GPT-5.6 configurations.
- **Mixed sources:** abstract and finance values came from different collections, run days apart.

## What the test claims, if it passes

**H1.** A configuration's round readout in abstract urn tasks predicts its round readout in finance tasks.
- Round readout is the share of answers reported at multiples of 0.05.
- This is a readout style, not a belief parameter.
- The claim is about these tasks, not finance in general.

## Configurations

Twelve configurations, six per model family:

| | Low effort | Medium | High |
| --- | --- | --- | --- |
| GPT-6 Astra | Astra-low | Astra | Astra-high |
| GPT-6 Sol | Sol-low | Sol | Sol-high |
| GPT-5.6 Luna | **Luna-low** | Luna | **Luna-high** |
| GPT-5.6 Terra | **Terra-low** | Terra | **Terra-high** |

- **New configurations.** The four in bold are new. They would be added to the configuration table (`research_world3.runner.CONFIGURATIONS`) as `gpt-5.6-luna` and `gpt-5.6-terra` at low and high effort.
- **Smoke test.** One session of an existing module per new configuration confirms the provider accepts the effort level, before anything is frozen.
- **Fallback.** If an effort level is refused, the test runs on the configurations available, at least eight. The critical ρ and power follow from the number (see Power).
- **Why twelve.** Six configurations per family allow a test within each model family (H2). Without them, a pass on H1 could be nothing more than GPT-5.6 against GPT-6.

## Tasks

Existing modules only, so no task code changes beyond a preset. Each abstract task has a finance twin of the same structure; one finance task has no abstract twin, so the finance side also includes a different structure.

| Domain | Module | Story | Twin | Sessions | Measures |
| --- | --- | --- | --- | --- | --- |
| Abstract | `wording-urn-a` to `-d` | An analyst's call on an urn, in four wordings | the policy forms | 4 | readout, confidence |
| Abstract | `copying-urn-asked` (`urn2-named`) | Sensors that may copy a logged reading; base rates asked | corroboration cues | 2 | readout, gap |
| Abstract | `selection-urn-asked` (`urn2-named`) | A reporter that may hold back blue draws; base rates asked | disclosure cues | 2 | readout, gap |
| Finance | `wording-policy-a` to `-d` | An economist's forecast of a central bank's decision | the urn forms | 4 | readout, confidence |
| Finance | `corroboration-cues` (`cues-a`) | Newsletters and aggregators that may repeat others' market calls | copying | 2 | readout, gap |
| Finance | `disclosure-cues` (`cues-a`) | Companies that may withhold bad indicators | selection | 2 | readout, gap |
| Finance | `announced-a`, `-b` | A central bank's statement with one changed sentence | none | 2 | readout |

- **Per configuration:** 8 abstract and 10 finance sessions.
- **In total:** 216 sessions at twelve configurations, 144 at eight.
- **Fresh sessions only.** The sessions that suggested the hypotheses are not reused.
- **Order.** Every case is separate and in random order: no sequences and no follow-ups, which change Astra's readout. The runner shuffles the order of sessions across the collection, so the two domains are interleaved in time.

**Budget.** At about 0.47 million input tokens per session, about 90% of them cached:
- twelve configurations: about 100 million input tokens;
- eight configurations: about 68 million.

Battery v2 used 77 million.

## Measures

Fixed before collection, as in the exploration (`ledger.finance_transfer`):
- **Round readout:**
  - Per session: the share of probability answers at multiples of 0.05, among answers between 0.06 and 0.94 that differ from a stated prior where the case states one.
  - Sessions with fewer than five such answers are dropped.
  - A configuration's value in a domain is the mean over its sessions there.
- **Stated–applied gap:**
  - Per rate-asking session: the mean over levels 1–3 of |mean stated base rate − applied base rate|, where applied is the implied rate the forecasts fit.
  - A configuration's value in a domain is the mean of its two structures, each the mean of its sessions.
- **Sensitivity to verbal confidence:** the mean weight of a "definitely… confirmed" claim minus an "I think…" claim, in log-odds from the stated prior, over the four wording forms in each domain.

## Hypotheses and tests

All tests use Spearman's ρ between configurations' abstract and finance values, one-sided, with an exact or permutation p. The critical ρ is 0.503 at twelve configurations, 0.643 at eight and 0.829 at six.

| | Hypothesis | Configurations | Role |
| --- | --- | --- | --- |
| H1 | Round readout transfers | all | **Primary**; pass at p < 0.05 |
| H2a | Round readout transfers within GPT-6 | Astra and Sol, three efforts each | Secondary |
| H2b | Round readout transfers within GPT-5.6 | Luna and Terra, three efforts each | Secondary |
| H3 | The stated–applied gap transfers | all | Secondary |
| H4 | Sensitivity to verbal confidence transfers | all | Secondary |

The four secondary tests are Holm-adjusted together.

**Also reported:**
- **Per-configuration readings** for the passport: for each configuration and trait, whether it sits on the same side of the median in both domains.
- **Near against far transfer:** round readout on the twin tasks only, and on the announced statements alone.
- **Session-to-session SDs.**

**What the outcomes mean:**
- **H1 passes:** round readout is the first trait in the repository to pass a preregistered test of transfer from abstract tasks to finance tasks. The passport's readout reading can say so, conditional on these tasks.
- **H2a also passes:** it carries within one model, not only between families. That would be the stronger product claim.
- **H1 fails with ρ above 0:** transfer is not established. The exploration result is then reported as not replicated at this power.

## Power

From `uv run python -m epistemics.ledger finance-transfer-power --output output/finance-transfer-power-20261004.json`.

**Model:**
- configuration values with a between-configuration SD of 0.17 in each domain (the eight-configuration sweep), correlated ρ across domains;
- each session's share off by N(0, 0.20), the pooled within-configuration session SD of the existing urn, policy and announced sessions;
- a configuration's value is the mean of its sessions in a domain.

**H1:**

| Configurations | Sessions per domain | Full transfer (ρ 1) | As explored (ρ 0.76) | ρ 0.5 | No transfer |
| --- | --- | --- | --- | --- | --- |
| 12 | 10 | 0.98 | 0.73 | 0.38 | 0.06 |
| 12 | 8 | 0.97 | 0.70 | 0.34 | 0.05 |
| 12 | 4 | 0.85 | 0.59 | 0.29 | 0.05 |
| 8 | 8 | 0.82 | 0.49 | 0.24 | 0.05 |
| 8 | 4 | 0.63 | 0.37 | 0.19 | 0.05 |

**Sensitivity.** With a between-configuration SD of 0.24, as the four configurations measured suggest, power at twelve configurations and eight sessions is 1.00, 0.78 and 0.41 for the three transfer levels.

**H3 (gap), from a one-off simulation** not yet in the saved file; it is added to the power command at build (GPT-6 gaps 0.02 ± 0.015, GPT-5.6 0.10 ± 0.05; session SDs 0.02 and 0.08; four sessions per domain):
- power 0.73 if full;
- 0.48 if as explored;
- false positives 0.06.

At eight configurations, with two of them GPT-5.6, power is 0.50 and 0.26. The gap is concentrated in GPT-5.6, so its test depends on the four new configurations.

**Reading.** With twelve configurations the primary test is well powered if transfer is close to full, and moderately (0.70) if it is as strong as the exploration suggested. With eight it is underpowered (0.49). That is the case for the four new configurations.

## Validity and exclusions

- A session counts if it completed and verified.
- A failed session is re-collected once in a top-up.
- A configuration enters a test if it has at least 6 of 8 abstract and 8 of 10 finance sessions.
- H1 runs if at least 10 configurations enter. Below that, it runs on those available with the matching critical ρ, and its power is reported.

The task validation for the frozen version (preset only) runs on both seeds before collection, as for every version.

## Build

1. **Configurations.** Add the four GPT-5.6 effort variants to the configuration table, then smoke-test each.
2. **Preset.** Add `finance-transfer` with the groups above: tasks 0.42.0 for the preset, with validation on both seeds.
3. **Analysis.** Extend `ledger.finance_transfer` with the preregistered analysis on the new root: the session-level measures above, and H1–H4 with Holm. Add a test, and fix the code with the preregistration.
4. **Preregistration.** Write `docs/finance-transfer-preregistration.md` from this design and commit it before collection.
5. **Collect.** 216 sessions.

## Decisions

1. **Configurations:** twelve, with the four GPT-5.6 effort variants (recommended), or the existing eight (power 0.49 as explored).
2. **Budget:** about 100 million input tokens at twelve configurations, or about 68 million at eight.
3. **Gap tasks on the finance side:**
   - the cue modules, as in the exploration (recommended, so the hypothesis tested is the one found);
   - or the rate-asking dossiers (`corroboration-asked`, `disclosure-asked`), which match the urn sessions' format more closely: the mechanism is named, then the base rate is asked.
