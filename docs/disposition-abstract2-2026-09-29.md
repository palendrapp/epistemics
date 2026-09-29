# Abstract transfer, corrected urn tasks — 29 September 2026

Preregistration, written and committed before collection.

The [first abstract transfer](disposition-abstract-2026-09-28.md) could not test the second layer. Its preregistered fit did not converge, because of two design flaws that the data exposed:
- **Selection:** the named mechanism ("reporters that hold back every blue ball") made any record containing a blue ball logically disqualifying. Once the mechanism was named and asked about, both configurations set those levels to 0, correctly.
- **Mismatch:** "readings are correct 90% of the time" was ambiguous about whether it included filing errors. The mapping fell from the named rung to the probed rung.

This run corrects both and repeats the test with the analysis unchanged.

## Corrections (disposition-tasks/0.11.0; variants `urn2-plain` and `urn2-named`)

1. **The structures are stated per round, as the observers assume.** For example: "In any round, a reporter may report every red ball it drew and hold back every blue one; in other rounds it leaves balls unreported at random."
   - **Why this fixes selection:** a record with a few blue balls is then compatible with a mostly selective reporter.
   - **Questions:** base-rate questions ask for the proportion of rounds, and probes ask about this round.
2. **The named sentence says what the stated accuracies cover.**
   - **Copying:** "a sensor's stated accuracy applies when it reads the urn itself".
   - **Mismatch:** "a sensor's stated accuracy applies to readings of the urn it is filed under".
3. **Unchanged:** plain texts (byte-identical to the first run's), item designs (design 0.8.0), models and records.

The new variant names keep this run's sessions apart from the first run's in every analysis (`--format urn2`).

**Not corrected, and why.** Two further issues from the first run are behaviour, not design, so this run does not change them. The analysis rules below account for them.
- **Copying's irrelevant level.** "Mounted on rack 4" got 0.04–0.30, not 0.50. That is the configurations' own default for a sensor copying, so it stays; but it makes inclusion at uninformative copying levels hard to identify.
- **Partial discounting of copying unprompted.** Five of six plain sessions gave the 198-of-200 sensor 0.12–0.33, neither 0 nor the named 0.95. The second layer's discrete inclusion cannot express partial discounting. This is a known risk for the copying structure.

**Validation.**
- **Model recovery (design 0.8.0):** applies unchanged.
- **Second-layer recovery:** at these session counts it applies unchanged, because designs and counts are identical: 30 of 30 converged; θ correlation 0.96, MAE 0.16.
- **Task validation 0.11:** passed on both seeds.
  - **Changed setting.** The description-module synthetic respondent now has report noise 0.05, not 0.15. This matches the validation's stated scope ("synthetic collections … at low report noise"), which is a pipeline check.
  - **Reason.** At 0.15 the forecast-only relay design misses single-context tolerances by sampling error alone. It did so once at 0.11: largest error 0.229 against the 0.20 guard, on seed 20260927.
  - **Result.** At 0.05, all 37 description contexts recover with largest level errors of 0.051 or less. Every other context is identical to 0.10.

**Collection** (preset `abstract2`): the same design as the first run.

| Setting | Value |
| --- | --- |
| Configurations | GPT-6 Astra and Sol, medium effort |
| Sessions per configuration and structure | 3 plain, 3 named, 3 named and asked, 2 named, asked and probed |
| Contexts | 66 |
| Tokens | about 35 million (the first run used 34.6 million); cap 38 million |

## Analysis

The primary analysis is the one preregistered for the first run, on this run's sessions:

```bash
uv run python -m epistemics.ledger inclusion-joint --format urn2
```

It uses a shared threshold, the fidelity mixture, the stated-rate channel at the ambiguous levels, and four chains of 40,000 iterations.

**Validity rule (new).**
- **Primary fit:** P1–P4 are assessed only if every parameter of the primary fit has R-hat of 1.05 or less. Otherwise they are reported as not assessable.
- **Per-structure fits:** a θ is assessed only if its fit meets the same rule and its 90% interval stays clear of the prior bounds (−1 and 4).

**Secondary analysis (new).** The same model fitted to each structure alone, with the same validity rule.

## Predictions

**The second layer transfers** (unchanged from the first run):
- **P1.** Each configuration's urn θ lies within 0.5 of its dossier θ (Astra 0.47, Sol 0.74).
- **P2.** For both configurations, inclusion for an uninformative level is at most 0.35 at rung 0 and at least 0.80 at rung 2.
- **P3.** Astra's urn φ is at least 0.85.
- **P4.** Structure-specific thresholds do not beat a shared threshold by more than two standard errors of the paired WAIC difference.
- **S1 (secondary).** For each structure whose fit is assessable, its θ lies within 0.5 of the configuration's dossier θ.

**The corrections work:**
- **C1. Selection no longer collapses.** The strongly suggestive selection level ("1 of 200 blue") has a mean implied prior of at least 0.50 at both rung 2 and rung 3, for both configurations. It was 0.00–0.57 in the first run.
- **C2. Mismatch is stable across rungs.** The strongly suggestive mismatch level's mean implied prior at rung 3 lies within 0.20 of its value at rung 1, for both configurations. In the first run it fell by 0.51–0.62.

## Commitments (preregistration)

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint (0.11.0) | `7d4ef613e1d98a0ec23a61f601dc0335c13bcfd4e8edcb79bae97512e831ef6e` |
| Model and design fingerprint (unchanged: model 0.5.0, design 0.8.0) | `05a5a4747b13049d3749469060289b8e7767386fb7d1fa297104fca3068afe45` |
| Task validation 0.11, seed 20260927 | `aeb808ec5993640cb8e4006ca0092d322b9ca3288304a29724809fbd9d9bab65` |
| Task validation 0.11, seed 20261027 | `b24ca1d4f1182334cc85ee99736efcde2b0e8adc302e0fee83869c9415cd78ad` |
| Second-layer recovery at the urn counts (applies unchanged) | `32e9d7905131422912b83452f2f960275b5eb8d53bbc15c604584fbf683935fc` |

## Results

**Collection.**
- **Completion:** all 66 contexts completed with no tool errors, in 72–262 seconds each, 64 minutes in all.
- **Tokens:** 34,671,515 input tokens in total (32,637,696 cached), or 0.49–0.55 million per context, inside the 38 million cap.

The tables regenerate with:

```bash
uv run python -m epistemics.ledger cues-summary output/disposition-abstract2-20260929
```

```bash
uv run python -m epistemics.ledger inclusion-joint --format urn2
```

```bash
uv run python -m epistemics.ledger inclusion-joint --format urn2 --family selection
```

The last command also runs with `--family copying` and `--family mismatch`. `--family` fits the preregistered specification (shared threshold, fidelity mixture) to the named structures only. It was added after collection to run the preregistered secondary analysis.

Mean implied priors per level, from strongly reassuring to strongly suggestive:

| Structure | Configuration | Plain (rung 0) | Named (1) | Named and asked (2) | Named, asked and probed (3) |
| --- | --- | --- | --- | --- | --- |
| Copying | Astra | 0.00, 0.16, 0.09, 0.44, 0.58 | 0.00, 0.08, 0.50, 0.43, 0.95 | 0.00, 0.10, 0.39, 0.44, 0.95 | 0.05, 0.09, 0.53, 0.46, 0.95 |
| Copying | Sol | 0.00, 0.05, 0.01, 0.14, 0.14 | 0.02, 0.09, 0.17, 0.48, 0.94 | 0.00, 0.10, 0.12, 0.44, 0.95 | 0.05, 0.08, 0.33, 0.46, 0.94 |
| Selection | Astra | 0.05, 0.21, 0.03, 0.71, 0.96 | 0.05, 0.27, 0.50, 0.70, 0.99 | 0.05, 0.30, 0.42, 0.69, 1.00 | 0.05, 0.30, 0.49, 0.70, 0.95 |
| Selection | Sol | 0.05, 0.21, 0.03, 0.71, 0.96 | 0.05, 0.26, 0.48, 0.68, 0.98 | 0.04, 0.32, 0.48, 0.70, 0.98 | 0.06, 0.31, 0.49, 0.69, 0.95 |
| Mismatch | Astra | 0.00, 0.00, 0.00, 0.00, 0.00 | 0.00, 0.00, 0.00, 0.00, 0.00 | 0.00, 0.00, 0.02, 0.02, 0.03 | 0.03, 0.07, 0.09, 0.13, 0.17 |
| Mismatch | Sol | 0.00, 0.00, 0.00, 0.00, 0.00 | 0.00, 0.50, 0.33, 0.90, 0.97 | 0.00, 0.35, 0.08, 0.63, 0.74 | 0.05, 0.28, 0.28, 0.51, 0.63 |

### The corrections

**C1 (selection no longer collapses): supported.** The "1 of 200 blue" reporter's mean implied prior is 1.00 at rung 2 and 0.95 at rung 3 for Astra, and 0.98 and 0.95 for Sol. In the first run it was 0.00–0.57. Named selection now has one mapping at every rung (about 0.05, 0.30, 0.50, 0.70, 0.95 to 1.00), with the irrelevant level at the 50% default.

**C2 (mismatch stable across rungs): not supported.**
- **Sol:** 0.97 at rung 1 and 0.63 at rung 3, a fall of 0.34 (limit 0.20). All three named sessions gave the "shared by 50 urns and moving" sensor 0.95 or more. Asked and probed sessions split: three high (0.95–0.97) and two low (0.30 and 0.32).
- **Astra:** 0.00 at rung 1 and 0.17 at rung 3, within 0.20, but only because Astra did not apply misfiling at any rung. In the first run it gave the same sensor 0.88 when named.

**Why the mismatch correction failed.** The corrected sentence was "a sensor's stated accuracy applies to readings of the urn it is filed under". It can be read in two ways:
- **Intended:** accuracy applies when the reading really comes from the urn it is filed under.
- **Astra's reading:** accuracy applies to the readings filed under the urn, misfiled ones included, so misfiling is already priced in.

Astra's completion answers (descriptive only) raised this in 6 of its 8 named sessions: "I did not invent a separate misfiling rate"; the misfiling language was "ambiguous alongside that accuracy statement". Its stated misfiling rates agreed with its forecasts: 0.05–0.20 for the 50-urn sensor when asked. So this is a consistent reading of the wording, not a stated–applied gap. None of Sol's completion answers described the accuracy statement as ambiguous. Five of them noted that no misfiling rate was given, so the answers required judgment.

### The preregistered analysis

**P1–P4 are not assessable.** The primary fit (shared threshold, fidelity mixture) had R-hat 1.96 for Astra and 1.15 for Sol, both above the 1.05 validity rule.

The other variants, for completeness (exploratory):

| Variant | Astra R-hat | Astra θ | Sol R-hat | Sol θ |
| --- | --- | --- | --- | --- |
| Shared, considered | 1.03 | 0.61 [0.45, 0.82] | 1.02 | −0.06 [−0.34, 0.22] |
| Shared, applied | 3.52 | — | 1.02 | −0.08 [−0.35, 0.19] |
| Shared, mixture (primary) | 1.96 | — | 1.15 | — |
| Structure-specific, considered | 1.32 | — | 1.04 | selection −0.26, copying −0.27, mismatch 0.75 |
| Structure-specific, applied | 1.15 | — | 1.23 | — |
| Structure-specific, mixture | 1.15 | — | 2.39 | — |

In the one comparison where both fits converged (Sol, considered), structure-specific thresholds had lower WAIC than a shared threshold by 20.7 (SE 5.9). Astra's comparisons (26 ± 8 and 32 ± 7 in the same direction) involve an unconverged fit.

### The secondary analysis: one structure at a time

Every per-structure fit converged (R-hat 1.003–1.007).

| Structure | Configuration | θ [90%] | Inclusion by rung, 0 → 3 | φ | S1: distance from dossier θ |
| --- | --- | --- | --- | --- | --- |
| Selection | Astra | −0.25 [−0.52, 0.00] | 0.75, 1.00, 1.00, 1.00 | 0.46 | 0.72, fails |
| Selection | Sol | −0.26 [−0.52, −0.03] | 0.76, 1.00, 1.00, 1.00 | 0.84 | 1.00, fails |
| Copying | Astra | −0.77 [−0.98, −0.41] | 0.94, 0.99, 1.00, 1.00 | 0.19 | 1.24, fails |
| Copying | Sol | 0.07 [−0.70, 0.65] | 0.42, 0.96, 1.00, 1.00 | 0.47 | 0.67, fails |
| Mismatch | Astra | 2.42 [1.78, 3.33] | 0.01, 0.06, 0.32, 0.77 | 0.41 | 1.95, fails |
| Mismatch | Sol | 0.86 [0.41, 1.33] | 0.06, 0.62, 0.97, 0.99 | 0.85 | 0.12, holds |

**S1 holds for one of six fits (Sol, mismatch).** Dossier thresholds were 0.47 (Astra) and 0.74 (Sol).

Astra's copying interval reaches −0.98, 0.02 inside the prior's lower bound. The preregistration did not define "clear of the bound". Under a literal reading the fit is assessable; S1 fails either way.

### Other observations (descriptive)

1. **Plain selection is a calculation.** All 12 plain selection sessions across both runs, from both configurations and in different case orders, gave the same 24 answers to within 0.01. This is why the plain mappings are identical. A record such as "1 of 200 blue" is used as data for an explicit inference, and no session-to-session variation remains.
2. **Unprompted mismatch neglect replicates.** All six plain sessions put every level at 0.00, as in the first run: 12 of 12 across the two runs.
3. **Unprompted copying is partial and varies by session.** The 198-of-200 sensor, plain:

   | | This run | First run |
   | --- | --- | --- |
   | Astra | 0.33, 0.43, 0.97 | 0.12, 0.23, 0.24 |
   | Sol | 0.11, 0.12, 0.19 | 0.00, 0.29, 0.33 |

   The plain texts are identical across the runs.
4. **This time the copying stated–applied gap is Astra's.** Astra's stated copying rates exceeded its applied priors in all five asked and probed sessions: mean gap +0.06 to +0.13, largest +0.13 to +0.25. The gap is mainly at the reassuring levels: in the asked sessions, for the 128-of-200 sensor, it stated 0.15–0.25 but applied 0.00. Sol had a gap in two of five sessions (+0.12 and +0.16). In the first run it was Sol, in two of three asked sessions, with Astra within 0.06. The named copying sentence differs between the runs.
5. **φ is unreliable next to 0.** Astra's mismatch φ (0.41) comes from stated rates of 0.02–0.05 at the ambiguous levels against applied priors of 0.00. That is a small absolute gap but a large one on the log-odds scale. Its copying φ (0.19) reflects real gaps of 0.15–0.25.

## Interpretation

1. **The noticing threshold is not a configuration trait in this format.**
   - The primary joint fit failed to converge again. One structure at a time, every fit converged, and the thresholds differ by structure.
   - **Selection** is considered in most sessions without being named (θ about −0.25 for both configurations).
   - **Mismatch** needs naming (Sol, θ 0.86) or was hardly taken up under this wording (Astra).
   - **Across formats,** only Sol's mismatch threshold lies within 0.5 of its dossier threshold.
   - **Where both fits converged (Sol),** structure-specific thresholds fit better by 3.5 standard errors.
2. **θ measures a structure, a cue format and a reading together.**
   - Selection's records show the structure on their face ("1 of 200 blue"). Mismatch's records (how many urns a sensor serves) do not. Copying's match counts fall between.
   - The thresholds therefore order how self-evident each cue is, as well as how attentive each configuration is. Any threshold claim has to name its structure and format.
3. **One correction worked and one did not.** Stating the structures per round fixed selection. The clarified accuracy sentence for mismatch was read as covering misfiling by Astra. Sol applied misfiling when named, but judged it rare in two of five asked or probed sessions.
4. **For the reading guide:** keep noticing claims per structure, as the "Told that…" readings already are. Do not report a configuration-level noticing threshold. The dossier second-layer estimates stay labelled dossier-specific.

## Next

- **A hierarchical second layer.** Thresholds per structure and format (dossier relay, dossier disclosure, copying, selection, mismatch), partially pooled toward a configuration mean and fitted jointly to the existing dossier and urn sessions.
  - **Quantity of interest:** the spread between structures, which measures how far noticing generalises.
  - **Requirements:** recovery validation before any estimate is reported. No new collection is needed for a first fit.
- **Done (tasks 0.12, [structure checks](structure-checks.md)): a third mismatch wording.** For example: "When a reading does come from the urn it is filed under, it is correct 90% of the time; a reading from a different urn says nothing about this one."

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `26f027516c716ae3c201adf0c4ffa4db4f93f4395a8be641128a1c913e036f32` |
| execution.json | `48626b9d883978867c99f4eecdc218839d6fceb43104aa8e1fc3d87487ba77e5` |
| summary.json | `bd514bee3544590ea40a405eab428431e3497732a631ccf0b339fd5710e54c23` |
| Preregistered fit | `514b71f280484d931f08d5b91674085abd9d07518a2456186bca04731d39d9ee` |
| Per-structure fit, selection | `5883331142eb2bae1baad41ee03fe1b023f9d803d088c0ea6ad1b5e3fb1d7a16` |
| Per-structure fit, copying | `b08b50b122d795771b8a151fe6b23ab15588dfc1e4979c27edb3cdb15d8c4ca7` |
| Per-structure fit, mismatch | `8be613889cb0c306692d49471e598765d0e19f058d10c7e82906667ff8062f8d` |
