# Disposition task acceptance: T2, T3 and T5 — 27 September 2026

**Both configurations filled every missing base rate with 50% and then computed exactly.** Across 18 fresh contexts, GPT-6 Astra and Sol at medium effort answered as Bayesian observers with:
- **Dependence prior:** δ = 0.5.
- **Suspicion of silence:** σ = 0.5.
- **Evidence sensitivity:** γ = 1.
- **Value of certainty:** zero.

**Stability.** The answers were the same across fresh contexts and across both cover stories. Sol matched that observer on all 216 of its checkpoints; Astra on 207 of 216.

**What they said.** Eleven of the twelve T2 and T3 completion answers said the unstated prior had been set to equal chances. The twelfth named that prior as the main ambiguity without giving its value.

This is an engineering acceptance and a scoped behavioral observation, not a passport claim.

## Design

The frozen plan (implementation fingerprint `c128ddf5…f8517`, two passed task validations) ran the [disposition tasks](disposition-tasks.md) through the Codex CLI on the existing ChatGPT subscription:

| Setting | Value |
| --- | --- |
| Configurations | GPT-6 Astra and Sol, medium effort |
| Modules | T2 (with relay probes), T3 (with sender probes), T5 |
| Contexts per module | markets twice, ecology once, each in its own evaluator-chosen order |
| Runs | 18 fresh contexts of 24 checkpoints |
| Token cap | 20 million known processed tokens |

## Results

**Collection:**
- **Completion:** all 18 contexts completed with the minimum 27 tool calls each and no tool errors.
- **Time:** 87–163 seconds per context, 18 minutes in total.
- **Tokens:** 0.51–0.55 million input tokens per context. The total was 9,542,857 input tokens (8,974,208 cached) and 36,023 output tokens.

| Module | Fitted observer (every context) | Matches to that observer |
| --- | --- | --- |
| T2 corroboration | δ = 0.50, γ = 1.00, bias 0.00; 90% intervals on the grid point | Sol 72/72; Astra 65/72 (six forecasts one point off, one three points off) |
| T3 silence | σ = 0.50 (one Astra context 0.496), γ = 1.00, bias 0.00 | Sol 72/72; Astra 70/72 (one forecast one point off, one probe ten points off) |
| T5 value of certainty | Price equal to decision value, rounded down; 0 for all 18 zero-value checks | 72/72 for both configurations |

**Model comparison.** The Bayesian observer beat its heuristic rival in every T2 and T3 context, with model probability 1.00.

**Retest and cover differences:**
- **Sol:** zero for every module.
- **Astra:** zero for T2; 0.004 for T3, where one context gave 0.496; zero for T5.

Examples of what they wrote:
- "I treated relaying and checking independently as equally likely before considering the reports and wording." (Sol)
- "Where the relay probability was unstated, I assumed 50%." (Astra)
- "When contractor-type probabilities were unstated, I assumed an equal prior split, independent of fish-stock health." (Astra)
- "I valued checks by their expected improvement in decision payoff, using the greatest whole-point price I would pay." (Astra)

## Interpretation

1. **The answer to "which Bayesian?" for these configurations is the indifference Bayesian.** Given a binary unknown with no base rate, both apply the principle of insufficient reason. They do so explicitly, consistently and independently of wording and cover story, and then compute the posterior exactly, including treating a match as evidence of relaying. The dispositions are identified. They are a shared rule rather than a trait, so there is no between-configuration variance for an individual profile to capture here.
2. **Their value of certainty is zero.** Checks that cannot change the decision are worth nothing to them, and decision-relevant checks are worth exactly their expected improvement. Human evidence points the other way (people pay for non-instrumental information, as in [Eliaz & Schotter 2010](https://ideas.repec.org/a/eee/gamebe/v70y2010i2p304-324.html)), so this parameter should separate agents from people once humans are measured.
3. **A reading-guide candidate follows,** for these configurations and this task frame: when a base rate is missing they assume 50%, say so, and otherwise reason exactly. A consumer should supply base rates, because 50% may be badly wrong in a real domain; much syndicated news, for example, is relayed. Issuing this claim would need weaker configurations and a transfer check.
4. **The symmetric framing may invite indifference.** Each unknown was posed as a two-way possibility ("may have checked for itself or relayed", "could be either kind"). Sol remarked that this phrase "left that assumption unclear". Whether the 50% default survives framings that do not present a symmetric choice, and realistic material where world knowledge suggests a base rate, is the open question. It is also the question the transfer layer was designed to answer.

## Issues found

Each issue is recorded here and none is fixed yet; each change requires a version review and a recovery rerun.

- **T5 response model.** With whole-point prices, reporting the floor of one's value is optimal under the random-price rule, and both configurations did exactly that. The model assumed rounding to the nearest point. The half-point shortfall pushes fitted λ_c slightly negative (linear −2.5, interval −4 to 0). **Fix:** model the reported price as the floor of the latent value, or make every decision value a whole number of points.
- **Certainty-function selection at zero value.** The reported preference for entropy (0.89) is an artifact of that offset. At λ_c ≈ 0 the two functions make identical predictions, as the recovery study showed. **Fix:** report the function as undetermined when the λ_c interval includes zero.
- **Zero-value split in the report.** The mean-price split compared decision values with exact zero, so floating-point residues moved some zero-value checks into the decision-relevant group. The report's 4.8 points should read 0.0 and 9.5. **Fix:** use a tolerance.
- **Conflicting pairs with identical wording.** Astra flagged "same wording alongside opposite calls" as ambiguous. It resolved the case correctly, treating conflict as ruling out a relay. The item mixes an impossible combination into the cue design. **Fix:** drop identical-wording cues from conflicting pairs.

## Next

1. **Weaker configurations on the same tasks:** GPT-5.6 Luna and Terra, and the GPT-6 configurations at low effort. At about 0.5 million input tokens per context, this is cheap to run and shows whether anything varies below the frontier.
2. **Break the symmetry:**
   - a variant that states the possibilities without presenting them as a symmetric pair;
   - a variant with qualitative plausibility cues (a wire service against a single-reporter blog), to test whether agents replace 50% with world knowledge;
   - a learnable variant in which relays are revealed across cases, linking δ to the learning modules (T1, T4).
3. **Transfer to the dossiers without background facts,** where the formal result predicts 50% defaults and any deviation shows knowledge-based priors.
4. **The T5 fixes above,** before any further T5 collection.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation fingerprint | `c128ddf5fb32e9c0298135729aeda280e6cdb1fe40461ca57e425643b47f8517` |
| plan.json | `55fcc6c4dafdabef38f88cf74d2b397be02f519d52dcb37592ae67d577754f47` |
| summary.json | `4a39507644f15b21173cf32ad34f342751253c9171bce47ae3ae33a9d4ac109e` |
| execution.json | `1bc32ee7c0cb6f9799b092d89eaab476a40b18afd12a31cac58e5e14efe2a4b3` |

Raw collections and transcripts remain private and outside Git. Model revisions are requested aliases, and execution is operator-asserted.
