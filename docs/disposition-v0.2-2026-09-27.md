# Disposition model and tasks 0.2: fixes, framings and learned base rates — 27 September 2026

Build and validation record. It follows the [acceptance](disposition-acceptance-2026-09-27.md) in which GPT-6 Astra and Sol set every missing base rate to 50%. Version 0.2 fixes the four problems that acceptance exposed and adds task variants that test where the 50% default comes from:
- disposition-model/0.2.0;
- disposition-design/0.2.0;
- disposition-tasks/0.2.0.

No respondent has answered 0.2 yet.

## Fixes

| Problem | Change |
| --- | --- |
| Rational whole-point prices round decision values down (7.5 becomes 7), which the model read as negative value of certainty | Every decision value is now a whole number of points, so the optimal floor and the nearest whole point agree for a respondent who values checks only for their decision value. Two checks moved from 7.5 and 12.5 points to 8 and 13; each kept its group. |
| Exact respondents looked information-averse | Every negative latent price is reported as zero, so a respondent who pays exactly nothing for checks that cannot change the decision fits a slightly negative value when the smallest noise level is 1 point. Noise levels of 0.25 and 0.5 points were added, and an exact respondent now fits λ_c = 0.0, interval [0, 0]. |
| A certainty function was "selected" at zero value | A function is now selected only when λ_c is credibly positive (the lower end of its 90% interval above zero). At zero the functions coincide; below zero they differ only through the six decision-relevant checks. |
| The report's split of mean prices by decision value used exact zero | A tolerance is used. |
| Conflicting pairs could claim identical wording | Conflicting pairs now use only different-wording or no cues. |

## New variants (T2 and T3)

| Variant | What changes | What it tests |
| --- | --- | --- |
| paired | The 0.1 wording: the unknown is posed as a two-way possibility ("may have checked for itself or relayed", "could be either kind") | Baseline |
| open | That sentence is removed; nothing else changes | Whether the explicit two-way choice produces the 50% default |
| suggestive | Open, plus one qualitative sentence making a relay or selective sender more plausible (for example "a two-person newsletter with no research staff", "about to ask investors for new financing") | Whether world knowledge moves the default |
| reassuring | Open, plus a sentence making it less plausible (for example "runs its own monthly survey of retailers", "prepared by an outside auditor using a fixed template") | Same, in the other direction |
| learning-high, learning-low | Open. Cases share one population, and each checkpoint reveals how the previous case was produced (relay or not, selective or not), drawn at a world rate of 80% or 20% given that case's evidence | Whether the base rate is treated as learnable, from what starting value, and how fast |

**How the variants sit together.**
- **Numbers:** unchanged in every variant, so each difference is a framing effect.
- **Descriptors:** three per direction, module and cover, cycled across cases.
- **Learning reveals:** because each revealed structure is drawn from its posterior given the case's evidence, the reveals are coherent for a Bayesian who knew the world rate.

**The learning model.** The disposition at each case is the posterior mean of a Beta prior, with mean *start* and strength *κ* in pseudo-observations, after the reveals shown so far. κ = 1024 stands for no learning, and "learning" means κ ≤ 32. An indifference learner that treats the rate as unknown and updates like Laplace has start 0.5 and κ = 2. Learning is detected by the posterior probability of κ ≤ 32, with equal prior weight on learning and on no learning. Two corrections were made before the recorded runs, after a small dry run:
- **Balanced prior:** the uniform grid prior gave learning 7:1 prior odds, because seven of the eight κ values count as learning, so the weights were balanced.
- **Scoring region:** detection is scored only where the start differs from the world rate by at least 0.25. Otherwise learning leaves no trace; the agents' 0.5 start against rates of 0.2 and 0.8 lies inside the scored region.

## Validation

**Model recovery.** Both seeds passed every gate. Agent-like noise band, ranges across seeds:

| Parameter | Result |
| --- | --- |
| δ with probes / σ with probes | r = 1.00, error 0.02 (unchanged) |
| Rival identified | 97–100% |
| λ_c | r = 0.98–0.99 |
| Certainty function (material values) | 100% |
| Learning detected (κ ≤ 16) | 87–97% |
| No learning detected (κ = 1024) | 93–100% |
| Starting value (κ ≥ 8) | r = 0.98–0.99, error 0.035–0.038, coverage 0.91–0.94 |
| log₂ κ | r = 0.83–0.87 |

**Task pipeline.** The validation passed on both seeds:
- **Audit:** 624 rendered cases across every module, cover and variant. It checks the displayed probabilities and the absence of private labels, and that the two-way sentence appears exactly in the paired variant.
- **Synthetic contexts:** 28 through the service. Every paired context was recovered in both covers, and every other variant in the markets cover. In both learning variants a learner starting at 0.5 was detected as learning, with its start recovered, and saw 23 reveals.

The validation's learner uses κ = 8. At κ = 2 the start shapes only the first few cases, and the recovery study scores starts only from κ = 8.

## Planned round

This is the frozen `round-2` preset, 32 fresh contexts:

| Group | Configurations | Modules | Contexts |
| --- | --- | --- | --- |
| Weaker configurations | GPT-5.6 Luna and Terra (medium); GPT-6 Astra and Sol (low) | T2, T3, T5 | paired, markets, once each |
| Frontier framings | GPT-6 Astra and Sol (medium) | T2, T3 | open, suggestive, reassuring, learning-high, learning-low (markets) |

At about 0.53 million input tokens per context, that is roughly 17 million input tokens, mostly cached, under a 25 million cap.

**What would count as a finding:**
- **Weaker configurations:** do they depart from the indifference observer in δ, σ, γ or noise, and do they place any value on certainty?
- **Frontier, framing:** does removing the two-way sentence move δ or σ away from 0.5?
- **Frontier, plausibility:** do the plausibility sentences move δ and σ in their stated directions?
- **Frontier, learning:** do the learning variants show learning from a 0.5 start, and at what κ?

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Model implementation fingerprint | `2383c3636ddc504d0d5a61e3616d1fdd9382dc1c3dd5989516a3fd1339021317` |
| Model recovery, seed 20260927 | `7790e539614d92327bf7b63c6c40e2b2a3e4ca123e62a3ee58ae9a76d30e0e06` |
| Model recovery, seed 20261027 | `d127a703f429131547ffdb584b6e5884f0f38ac09fed298b3a1e3470ca70ca2d` |
| Tasks implementation fingerprint | `f781dc25ba84cd2ed3650bc8017877b29617c0322dceb7e5df3b8ed6935d26a0` |
| Task validation, seed 20260927 | `2620fad1826747d46bab763a2bcd3386119b44b499db800b1879b648753f9eff` |
| Task validation, seed 20261027 | `f598a0a5f3188765f0390a2c100322caf9e80c4186117fda6efc07ccfe0491ee` |

Validation outputs remain in the ignored `output/` directory.
