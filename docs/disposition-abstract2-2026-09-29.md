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
