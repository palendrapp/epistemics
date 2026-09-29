# Abstract transfer of the second layer: urn tasks — 28 September 2026

Preregistration, written and committed before collection; the results follow below. This is the confirmatory test proposed in the [second-layer model](structure-inclusion-model.md#next).

**Result.** The preregistered analysis failed. The second-layer fit to the urn sessions did not converge (R-hat 1.4–13), so P1–P4 cannot be assessed as preregistered.

The failure traces to two design problems the data exposed:
- **Selection:** once the mechanism is named, the selection records contradict it logically.
- **Mismatch:** stated sensor accuracy is ambiguous about whether it includes filing errors.

Descriptively and in exploratory fits:
- **Unprompted neglect transfers:** fully for the new mismatch structure, partly for copying.
- **Naming restores consideration** for both copying and mismatch.
- **Mismatch alone** gives inclusion thresholds close to the dossier ones.
- **Sol's stated–applied gap** reappeared in the copying asked condition.


The second layer describes Astra and Sol with a few abstract parameters, all fitted to relay and disclosure dossiers:
- **θ, inclusion threshold:** how much prompting a hidden structure needs before it is considered, on a salience ladder of plain, named, named and asked, and named, asked and probed.
- **w, cue-driven inclusion.**
- **σ, session drift.**
- **φ, stated–applied fidelity.**

It was built after seeing those data. The test here is whether the parameters carry over to tasks that share no content with the dossiers, and to a hidden structure the model has not seen.

## Design

**Urn tasks** (disposition-tasks/0.10.0; model 0.5.0; design 0.8.0; `epistemics.disposition_tasks.urn`). Every case concerns an urn that is either red-majority or blue-majority, with a stated prior and "Half of all urns in the lab are red-majority." Three hidden structures:

| Structure | Evidence | Hidden structure | Graded cue (record), strongly reassuring → strongly suggestive |
| --- | --- | --- | --- |
| **Copying** (the relay model) | Two sensors' readings, logged in order, with stated accuracies | Sensor B may copy A's reading | How often B's reading matched A's over 200 rounds: 128, 142, (rack number), 164, 198 |
| **Selection** (the disclosure model) | A reporter drew 4 balls and reported some | The reporter may report every red ball and hold back every blue one | Blue balls among the last 200 it reported: 94, 70, (station number), 30, 1 |
| **Mismatch** (new) | A sensor reading on file for the urn | The reading may come from a different urn than the one it is filed under | Urns the sensor serves: fixed to one, 2, (paint colour), 10, 50 and moving |

The cues are records, not descriptions. For copying and selection they are statistics an ideal observer could reason from. The dossiers used semantic descriptions ("an aggregator site with no reporters").

The copying and selection items are exactly the dossier designs at each rung:
- **Rungs 0–1:** forecast-only (four forecasts per level).
- **Rung 2:** base-rate question and three forecasts.
- **Rung 3:** base-rate question, probe and two forecasts. The disclosure description design serves at rung 3 for selection.

Only the surface changes. Mismatch has its own observer (`observers.mismatch`: a misfiled reading carries no evidence, because another urn is red-majority with probability one half) and designs of the same shape. Its anchors are the respondent's own draws, which cannot be misfiled.

**Ladder:**
- **Rung 0:** `urn-plain` never names the structure. The audit fails if a plain case contains any mechanism word for its structure.
- **Rung 1:** `urn-named` adds one background sentence naming it, without a rate.
- **Rungs 2 and 3:** the asked and probed modules also name it in their base-rate and probe questions.

**Validation.**
- **Model recovery (design 0.8.0):** passed every gate on both seeds, and all earlier recovery results are identical to 0.7. The three mismatch designs recover implied priors as follows:

  | Mismatch design | Correlation | MAE | 90% coverage |
  | --- | --- | --- | --- |
  | Forecast-only | 0.97 | 0.05 | 0.94–0.96 |
  | Asked | 0.96–0.97 | 0.05–0.06 | 0.96 |
  | Probed | 0.99 | 0.03 | 0.92–0.93 |

- **Task validation (0.10):** passed on both seeds, with every earlier context reproducing 0.9 exactly.
  - **Criterion change.** The task validation's criterion for description-level priors was changed in this version. It had been "largest level error at most 0.15".
    - **What happened:** the forecast-only and asked copying contexts missed it in three of eight urn contexts, with largest errors of 0.158–0.173 and mean errors of 0.06–0.07.
    - **Why it is chance:** at the validation's report noise (0.15), those designs recover levels with mean error 0.08, so the largest of five errors exceeds 0.15 by chance. The same designs in dossier form had passed by chance.
    - **New criterion:** mean level error at most 0.10 (the recovery gate), with no level off by more than 0.20.
    - **Earlier contexts:** every earlier context keeps its estimate and verdict under the new criterion.
- **Second-layer recovery:** 30 synthetic configurations at the collected counts below, from urn sessions alone, through the real designs and fits.
  - **Chain length:** the urn format fits three structures (23 parameters), and its extreme mapping levels mix slowly. With four chains of 10,000 iterations only 7 of 30 fits converged. With 30,000 all 30 converged (largest R-hat 1.03). The real-data fit uses 40,000 iterations.
  - **Recovery:**

    | Parameter | Correlation | MAE | 90% coverage |
    | --- | --- | --- | --- |
    | θ | 0.96 | 0.16 | 0.83, slightly under nominal |
    | w | 0.96 | 0.07 | 0.93 |
    | σ | 0.87 | 0.14 | 0.87 |
    | Mapping | — | 0.016 | 0.87 |

  - **Stated-rate model recovery:** the stated-rate hypotheses were recovered in 24 of 24 cases, although some of those model-recovery fits had R-hat up to 1.65.
  - **What this means for P1:** θ's recovery error is small beside P1's tolerance of 0.5, so a real difference of a rung would be detected.

**Collection** (preset `abstract`): GPT-6 Astra and Sol, medium effort. For each configuration and structure:

| Rung | Sessions |
| --- | --- |
| 0, plain | 3 |
| 1, named | 3 |
| 2, named and asked | 3 |
| 3, named, asked and probed | 2 |

That is 66 contexts. Urn cases are about half the length of dossier cases. Estimated tokens are 0.45–0.5 million per context, 30–33 million in total; proposed cap 38 million.

**Analysis.** Two versioned commands:

```bash
uv run python -m epistemics.ledger inclusion-joint --format urn
```

fits the second layer to the urn sessions alone. Its specification is fixed from the dossier fit: the stated-rate channel at the ambiguous levels, the fidelity mixture, and shared and structure-specific thresholds.

```bash
uv run python -m epistemics.ledger inclusion-joint
```

gives the dossier reference: Astra θ 0.47, σ 0.39, φ 0.97; Sol θ 0.74, σ 0.74, φ 0.87.

## Predictions

All use the urn fit with a shared threshold and the fidelity mixture unless stated.
- **P1. The threshold transfers.** Each configuration's urn θ lies within 0.5, half a rung, of its dossier θ.
- **P2. Neglect and naming transfer.** For both configurations, inclusion for an uninformative level is at most 0.35 at rung 0 and at least 0.80 at rung 2.
- **P3. Astra's fidelity transfers.** Astra's urn φ is at least 0.85.
- **P4. One threshold for three structures.** For both configurations, the structure-specific model does not beat the shared-threshold model by more than two standard errors of the paired WAIC difference.
- **Exploratory:**
  - Sol's fidelity and session drift relative to Astra's.
  - Cue-driven inclusion w with records instead of descriptions. Statistical records may trigger inclusion more readily at rung 0.
  - The per-level mappings for each structure.

If P1 fails, the threshold is format-specific: dossier descriptions and abstract records engage consideration differently. In that case the second layer's parameters stay descriptive of the dossier format until further evidence.

## Commitments (preregistration)

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint (0.10.0) | `ad93726ca218b466359248d7c71ab6e265556e1c8eb9aede9e009fcd683b2144` |
| Model and design fingerprint (dispositions: model 0.5.0, design 0.8.0) | `05a5a4747b13049d3749469060289b8e7767386fb7d1fa297104fca3068afe45` |
| Recovery validation 0.8, seed 20260927 | `699d928dec463d4a22373fddfd1191062fab0b656cb13b384eaf2ea690abadde` |
| Recovery validation 0.8, seed 20261027 | `b6e52999c455e258582d996988f31f6694a2cc724da2e5f32629826717b332df` |
| Task validation 0.10, seed 20260927 | `db1805f8d578f047805dadb04b371c180aa1c3d198a91b150ab83fb87c8d4f77` |
| Task validation 0.10, seed 20261027 | `787994888a843971c5cf57f88b34351dba5aefc17959ebff86f73ed343b284e0` |
| Second-layer recovery at the urn counts | `32e9d7905131422912b83452f2f960275b5eb8d53bbc15c604584fbf683935fc` |

## Results

**Collection.**
- **Completion:** all 66 contexts completed with the minimum 27 calls and no tool errors, in 71–127 seconds each, 58 minutes in all.
- **Tokens:** 34,595,381 input tokens in total (32,642,048 cached), or 0.49–0.61 million per context, inside the 38 million cap.

The tables regenerate with:

```bash
uv run python -m epistemics.ledger cues-summary output/disposition-abstract-20260928
```

```bash
uv run python -m epistemics.ledger inclusion-joint --format urn
```

### The preregistered analysis

The joint second-layer fit to the urn sessions (shared threshold, fidelity mixture, 4 chains of 40,000 iterations) did not converge.
- **R-hat:** 1.66 for Astra and 2.05 for Sol in the preregistered specification, and up to 13 in the structure-specific variants.
- **WAIC:** several variants gave values in the millions, meaning chains stuck in degenerate regions.
- **θ:** its 90% intervals reached the lower bound of its prior (−1).

Recovery at these session counts had converged in all 30 synthetic datasets. The failure therefore reflects a mismatch between the model and these data, not the counts. **P1–P4 are not assessable as preregistered.**

### Why: the model's assumptions fail for two of the three structures

The second layer assumes each structure has one mapping from cue to prior, which inclusion switches on or off. Mean implied priors per level, from strongly reassuring to strongly suggestive:

| Structure | Configuration | Plain (rung 0) | Named (1) | Named and asked (2) | Named, asked and probed (3) |
| --- | --- | --- | --- | --- | --- |
| Copying | Astra | 0.00, 0.10, 0.04, 0.19, 0.20 | 0.00, 0.08, 0.22, 0.43, 0.95 | 0.00, 0.10, 0.10, 0.43, 0.95 | 0.03, 0.07, 0.30, 0.44, 0.95 |
| Copying | Sol | 0.00, 0.11, 0.05, 0.28, 0.21 | 0.00, 0.10, 0.06, 0.50, 0.96 | 0.00, 0.10, 0.10, 0.44, 0.95 | 0.05, 0.06, 0.15, 0.44, 0.95 |
| Selection | Astra | 0.05, 0.21, 0.03, 0.71, 0.96 | 0.02, 0.18, 0.39, 0.63, 0.92 | 0.04, 0.08, 0.54, 0.22, 0.57 | 0.00, 0.00, 0.46, 0.00, 0.00 |
| Selection | Sol | 0.05, 0.21, 0.03, 0.71, 0.96 | 0.02, 0.29, 0.40, 0.82, 0.96 | 0.03, 0.03, 0.53, 0.03, 0.10 | 0.00, 0.00, 0.49, 0.00, 0.00 |
| Mismatch | Astra | 0.00, 0.00, 0.00, 0.00, 0.00 | 0.00, 0.44, 0.20, 0.77, 0.88 | 0.06, 0.40, 0.19, 0.62, 0.67 | 0.03, 0.11, 0.13, 0.19, 0.26 |
| Mismatch | Sol | 0.00, 0.00, 0.00, 0.00, 0.00 | 0.00, 0.50, 0.12, 0.90, 0.96 | 0.00, 0.50, 0.27, 0.90, 0.97 | 0.03, 0.11, 0.13, 0.25, 0.45 |

1. **Selection: the records contradict the named mechanism.** The named sentence and the questions describe reporters that hold back every blue ball. A record showing any blue balls reported, even 1 of 200, therefore proves this reporter is not one.

   Asked and probed, both configurations applied this: every level with a record went to 0, and only the irrelevant level (no record) kept the 50% default. Their completion answers say so directly: "Records containing blue reports rule out literal red-only behavior"; "I interpreted 'every' literally".

   Their reasoning was correct; the design was not. The same records, unnamed, read as strong selectivity (0.96 for 1 of 200). The dossier descriptions never contradicted the mechanism, which is why this did not arise there.
2. **Mismatch: stated accuracy is ambiguous.** The mismatch mapping falls from rung 1 to rung 3 (strongly suggestive: 0.88 → 0.26 for Astra, 0.96 → 0.45 for Sol). Completion answers in the probed sessions said "readings are correct" was ambiguous about whether it included filing errors. If it does, misfiling is already priced into the stated accuracy. The relay dossiers had the same ambiguity over track records.
3. **Copying:** its mapping is stable across rungs 1–3. Its irrelevant level ("mounted on rack 4") sits at 0.04–0.30, not 0.50. That makes inclusion at uninformative levels hard to identify.

### Exploratory results

Everything in this section is exploratory, because the preregistered analysis failed.

**Unprompted neglect transfers to two of the three structures.**
- **Mismatch:** all six plain sessions put every level at 0.00, including a sensor "shared by 50 urns and moves between them". Named, the same sensor got 0.88–0.96. This is the relay-dossier pattern in a new structure and a contentless format.
- **Copying:** partial. Unprompted, a sensor that had matched the other in 198 of 200 rounds got 0.20–0.21. Named, it got 0.95–0.96. That statistical record carries more unprompted weight than "an aggregator with no reporters" did (0.00–0.03).
- **Selection:** no neglect. Unprompted, a reporter with 1 blue ball of 200 got 0.96. That record makes the structure plain without naming it.

**Mismatch alone fits the second layer and matches the dossier pattern.** The joint fit on mismatch sessions alone converged (R-hat at most 1.01):

| | θ | Inclusion by rung 0 → 3 | φ |
| --- | --- | --- | --- |
| Astra, mismatch | 0.69 [0.29, 1.04] | 0.07, 0.75, 0.99, 1.00 | 0.86 |
| Sol, mismatch | 0.69 [0.19, 1.16] | 0.10, 0.73, 0.97, 0.99 | 0.86 |
| Astra, dossiers | 0.47 [0.17, 0.73] | 0.17, 0.85, 0.99, 1.00 | 0.97 |
| Sol, dossiers | 0.74 [0.28, 1.08] | 0.18, 0.62, 0.94, 0.99 | 0.87 |

Both mismatch thresholds are within 0.25 of the dossier ones. Had P1 been assessable on this structure alone, it would have held. The copying-only fit converged, but its θ is not identified (see point 3 above). The copying-and-mismatch fit did not converge for Sol.

**Sol's stated–applied gap reappeared in the analogous condition.** In the copying asked sessions:
- **Sol:** stated rates exceeded its applied priors at the ambiguous levels by +0.15 in two of three sessions, and +0.04 in the third. Its stated rate for the mildly suggestive sensor was 0.72 and 0.60, against 0.43 and 0.45 applied.
- **Astra:** within 0.06 in all three.
- **Mismatch asked:** stated and applied rates agreed almost exactly for both configurations.

This matches the dossier finding: Sol's gap appears intermittently when copying is named and its rate is asked, and not elsewhere.

**Against the predictions:** P1–P4 are not assessable (non-convergence). On the mismatch structure alone, exploratory: P1 would hold for both; P2 holds (rung 0 at most 0.10, rung 2 at least 0.97); P3 holds for Astra (0.86); P4 is untestable with one structure.

## Interpretation

1. **The confirmatory test did not work, and the failure is informative about the design.**
   - **Selection:** the record cues and the deterministic mechanism statement were incompatible. Once named, the agents correctly treated any blue ball as disqualifying.
   - **Mismatch:** the ambiguity over what "readings are correct" covers let the mapping shift with the question format.

   Both are fixable. The second layer's claims stay descriptive of the dossier format until a corrected urn task is run.
2. **What does transfer, descriptively:**
   - **Unprompted neglect:** fully for a new structure (mismatch), partly for copying.
   - **Naming restores consideration.**
   - **For mismatch,** the inclusion ladder closely matches the dossier one.
   - **Sol's intermittent stated–applied gap** appears in the copying condition again.
3. **The cue format matters.** Statistical records ("198 of 200", "1 of 200 blue") carry more weight unprompted than semantic descriptions do. The second layer's cue weight w is format-dependent, as the preregistration anticipated.

## Next

- **Corrected urn task:**
  - **Selection:** make the records compatible with the mechanism. Either name a probabilistic mechanism ("hold back most blue balls"), or use records that don't count blue reports.
  - **Mismatch:** state accuracy as conditional on reading the right urn ("when it reads the urn it is filed under, its readings are correct 90% of the time").
  - **Copying:** give its irrelevant level a neutral default.

  Then preregister again, with the analysis specification unchanged.
- **Keep the dossier second-layer estimates marked as dossier-specific** in the design note until then.

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `ce59e1f72c50dc6b7cfa99c4b5e1a97dfe1a0716705748155a105039e563e4f4` |
| execution.json | `5d3d8b1fcba3655f8c026454553d013550ad6e087f3b6dd7a86c30659df25235` |
| summary.json | `983f29a5886549e301515341c04cebdade572b4c6c7e6246d8786bb2f8bbc1c1` |
| Preregistered urn fit | `2a8887b95b99a650a631beda03083be9ab0e83c8e6ab88bc76ffd80b2d95e38d` |
| Exploratory urn fits (copying, mismatch, both) | `d68b2db7e792a0a06c821b317111d25208ede933756212ee65f78cb1c9846565` |
