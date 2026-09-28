# Disposition round 2: weaker configurations, framings and learned base rates — 27–28 September 2026

**The 50% default belongs to ignorance, not to the wording.** In the [0.2 tasks](disposition-v0.2-2026-09-27.md), GPT-6 Astra and Sol at medium effort showed three things:
- **Framing:** removing the explicit two-way sentence changed nothing; they still set every missing base rate to 50%.
- **Descriptions:** a one-sentence qualitative description moved their priors a long way, in the described direction. How they did so gave the first disposition difference between frontier configurations.
- **Revealed cases:** when earlier cases were revealed, both learned the base rate like a Laplace learner, starting at 0.5 with a prior worth about two observations.

**Weaker configurations.** GPT-5.6 Luna and Terra, and GPT-6 Astra and Sol at low effort, shared the same 50% default and the same zero value of certainty. They differed only in precision. No configuration placed any value on certainty.

These are single contexts per cell: descriptive observations, not passport claims.

## Collection

The frozen `round-2` plan (tasks fingerprint `f781dc25…26a0`) had 32 fresh contexts. Two stalled when the laptop slept with its lid closed: the per-run timeout uses a clock that pauses during sleep. After three hours, those two processes were stopped, with 1 and 0 answers, and the runner failed them as its protocol requires. That stopped admission with 14 contexts complete and 16 unattempted.

The remaining 18 then ran as a second frozen plan on the same implementation, with fresh case orders and reveal seeds, and all completed. Together the two plans cover every planned cell once:
- **Tools:** every context used the minimum 27 calls, and none had a tool error.
- **Tokens:** 17.3 million known input tokens in total (16.1 million cached).

## Results

**Weaker configurations** (paired variant, markets):

| Configuration | δ (T2) | σ (T3) | Value of certainty (T5) | Report noise τ (T2, T3) |
| --- | --- | --- | --- | --- |
| GPT-5.6 Luna | 0.40 [0.35, 0.45] | 0.50 [0.45, 0.55] | 0: price = decision value on 24/24 | 0.31, 0.50 |
| GPT-5.6 Terra | 0.50 | 0.41 [0.35, 0.45] | 0: 24/24 | 0.05, 0.42 |
| GPT-6 Astra, low | 0.50 | 0.50 | 0: 24/24 | 0.05, 0.05 |
| GPT-6 Sol, low | 0.50 | 0.50 | 0: 24/24 | 0.05, 0.05 |

Luna and both low-effort configurations said they assumed equal chances; Terra described "a neutral best-judgment assumption". Luna's and Terra's departures come from a few large errors, not from a different prior:
- **Luna, T3:** reported 30% where the 50%-prior answer is 83%.
- **Luna, T2:** reported 30% on a single-report case whose correct answer is 50%.
- **Terra, T3:** reported 78% where 41% follows.

The GPT-6 configurations at low effort were as exact as at medium effort.

**Frontier framings** (GPT-6, medium effort, markets). Each cell is the fitted δ or σ; where it differed, it is shown for each descriptor:

| | Astra T2 | Sol T2 | Astra T3 | Sol T3 |
| --- | --- | --- | --- | --- |
| paired (0.1 acceptance) | 0.50 | 0.50 | 0.50 | 0.50 |
| open | 0.50 (24/24 exact) | 0.50 (24/24) | 0.50 (24/24) | 0.50 (23/24) |
| suggestive | 0.70–0.80 | 0.80 | 0.75 | 0.60–0.65 |
| reassuring | 0.10 | 0.17–0.20 | 0.50: descriptions given "no numerical effect" | auditor 0.05; annual full data 0.26; cooperative 0.25 |

**Learning variants.** Every context was classified as learning, with posterior probability 1.00:

| | T2, 80% world | T2, 20% world | T3, 80% world | T3, 20% world |
| --- | --- | --- | --- | --- |
| Astra: start, κ | 0.52, 2 | 0.50, 2 | 0.50, 2 | 0.50, 2 |
| Sol: start, κ | 0.50, 2 | 0.25, 4 | 0.50, 2 | 0.52, 8 |

Revealed rates were 0.70–0.71 in the 80% worlds and 0.15–0.38 in the 20% worlds. In one context, Sol's first answer, given before any reveal, already implied a prior of about 0.25. Astra in all four contexts, and Sol in both disclosure contexts, described starting from an even estimate and updating from the reveals. Sol's relay contexts described "a judgmental starting estimate".

## Interpretation

1. **The default is indifference under ignorance, and the phrasing did not cause it.** Removing the explicit two-way sentence left every answer unchanged.
2. **The priors are hierarchical and learnable.** Given revealed cases from a shared population, both configurations behaved as Laplace learners (start 0.5, κ ≈ 2) in six of eight contexts. That is the uniform-hyperprior Bayesian: the natural formal description of the 50% default is "unknown base rate, uniform prior, update from experience".
3. **Qualitative knowledge sets priors, and this is where the configurations differ.**
   - **Relays:** both moved δ strongly (to 0.7–0.8, or 0.1–0.2).
   - **Suggestive disclosure:** Astra applied one value per framing, σ = 0.75.
   - **Reassuring disclosure:** Astra declined to use the descriptions at all. Sol used them, and graded them: an outside auditor lowered σ to 0.05, the other two descriptions to about 0.25.

   The disposition that varies among frontier configurations is therefore not the default prior. It is how qualitative evidence about a source becomes a prior. That is the right target for the next module.
4. **Value of certainty is zero for every configuration tested.** All six priced checks at exactly their decision value. The parameter does not separate these agents; it should separate agents from people.
5. **Below the frontier, the difference is precision.** Luna and Terra share the priors and valuations but make occasional large errors. This matches the earlier finding that noise is the most robust configuration-level parameter.

There is no normative answer for how much "a two-person newsletter" should raise the relay prior. The descriptor results describe how agents map descriptions to priors; they do not say which mapping is right.

## Implications

**For the model.** The fixed-prior δ and σ are well defined but context-dependent. The stable, configuration-level quantities are:
- the hyperprior and learning rate: here uniform, κ ≈ 2;
- the mapping from qualitative cues to priors, which differs by configuration;
- report precision.

**For the reading guide.** Candidate entries, scoped to this task frame:
- **All tested configurations:** when a base rate is missing they assume 50% and update quickly from observed cases. Supply base rates or track records where possible.
- **GPT-6 Sol:** discounts sources for reassuring institutional detail, such as an outside auditor. Astra ignores such detail in disclosure settings.
- **GPT-5.6 Luna and Terra:** same priors, lower precision; verify quantitative conclusions.

## Next

1. **Measure the cue-to-prior mapping directly.**
   - **Graded descriptors:** a range running from strongly reassuring to strongly suggestive.
   - **Direct probe:** an elicited probe of the implied base rate ("what fraction of outlets like this relay?").
   - **Real base rates:** where possible, cues whose real-world base rates are known, so the mapping can be scored for calibration.
2. **Retest the descriptor effects** in fresh contexts, since each cell here is a single context.
3. **Transfer:** dossiers without background facts, where the prediction is now specific. Agents should default to 50%, move on source descriptions, and learn across dossiers when outcomes are revealed.
4. **Human reference:** compare σ with receivers in the [Jin, Luca & Martin](https://www.aeaweb.org/articles?id=10.1257/mic.20180217) disclosure game (data downloaded), where people are insufficiently sceptical.
5. **Runner fix:** make the per-run timeout use wall-clock time, so that a sleeping machine fails runs promptly.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint | `f781dc25ba84cd2ed3650bc8017877b29617c0322dceb7e5df3b8ed6935d26a0` |
| Round 2 plan.json | `eeeb638037b2e8559513b62e732314b7ba8171361b7e69c5e5177af4b8ab41bd` |
| Round 2 execution.json (failed after 14; see above) | `7c1683eb03e7dbeda9a8f6682e5b374ad089cb926932b1f12f2a07cf104b7680` |
| Remainder plan.json | `88b0e1b34e40caee044ad4b93b42dddb584c5917d3db822adbfea8eb42438950` |
| Remainder execution.json | `a17300a45b527effc6dfde2acf5883a9f0cbbf26bba84262046af36fa1f965e8` |
| Remainder summary.json | `023cd4f8bddfa460474d1338cc6a15950f7c5ced861a57deee7f7fc448782468` |

Raw collections and transcripts remain private and outside Git. Model revisions are requested aliases, and execution is operator-asserted.
