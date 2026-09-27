# Positive control on register versus validity (0.3) — 27 September 2026

**The battery separates real configurations.** Where the medium-effort GPT-6 configurations were exact, three of four weaker configurations deviated.
- **Luna:** GPT-5.6 Luna took two of four fabricated survey reports at face value when unprompted. Its own summary described "unreliable-looking survey reports with impossible totals or implausible margins of error."
- **Terra and Astra (low):** GPT-5.6 Terra and GPT-6 Astra at low effort each accepted the one fabricated report whose impossibility was a ±1-point margin of error.
- **Explicit arm:** a structure note naming the impossibility removed every face-value acceptance.
- **Sol (low):** GPT-6 Sol at low effort matched its medium-effort exactness.

With four fabricated cases per configuration and arm, these are **detection results, not precise estimates**.

## Design

The frozen plan used the unchanged 0.3 dossiers with a runner update that added named configurations (implementation fingerprint `5544aa9f…ece5cb`; two passed validations):
- **Configurations:** GPT-5.6 Luna and Terra at medium effort; GPT-6 Astra and Sol at low effort.
- **Arms:** unprompted and explicit only. The hinted arm is not needed to test detection.
- **Contexts:** one type A and one type B context each: 16 fresh contexts of nine cases through the Codex CLI on the existing ChatGPT subscription.

All four configurations answered a one-word availability check before the plan was frozen. Design randomization gave this plan only count-type and margin-type fabrications, so percentage and date impossibilities were not tested here.

## Results

**Collection:** all 16 contexts completed with no tool errors in 529 seconds, using 5,487,665 input tokens (4,912,000 cached) and 26,004 output tokens. Every final decision was consistent with the respondent's own probability.

**Fabricated reports** (validity manipulation; four per configuration and arm):

| Configuration | Unprompted: discounted / face value / other | Explicit: discounted / face value / other |
| --- | --- | --- |
| GPT-6 Astra, medium (0.3 acceptance) | 4 / 0 / 0 | 4 / 0 / 0 |
| GPT-6 Sol, medium (0.3 acceptance) | 4 / 0 / 0 | 4 / 0 / 0 |
| GPT-6 Sol, low | 4 / 0 / 0 | 4 / 0 / 0 |
| GPT-6 Astra, low | 3 / 1 (margin) / 0 | 4 / 0 / 0 |
| GPT-5.6 Terra, medium | 3 / 1 (margin) / 0 | 3 / 0 / 1 |
| GPT-5.6 Luna, medium | 1 / 2 (counts) / 1 (margin) | 4 / 0 / 0 |

"Discounted" means within 1.5 points of the normative posterior, and "face value" within 1.5 points of the naive one. The two acceptance rows combine one report of each impossibility type.

**Neglect estimates** (four pairs each, with wide uncertainty):
- **Validity:** Luna unprompted 1.07 (standard error 0.43), against 0.00 explicit; Terra 0.29 unprompted and 0.45 explicit; Astra-low 0.29 unprompted; Sol-low 0.00.
- **Register:** Terra −0.50 in both arms. This comes from one informal-email dossier Terra read identically wrong in both contexts: 24% against a normative 63% and a naive 80%. It is a reproducible misreading rather than register discounting. Luna's register estimates reflect errors on polished control dossiers, which it answered correctly in the explicit arm.

**Verification purchases.** Across its 36 cases, Luna bought 3 surveys where 8 were worth buying under the normative posterior, and skipped every survey in two contexts. Sol-low and Astra-low bought exactly the 8 worth buying. Terra bought 9, 7 of them worth buying.

## Interpretation

1. **The measurement can detect a real deviation.** The same dossiers that stronger configurations read exactly produced face-value acceptance of fabricated figures in a weaker configuration. The explicit arm then removed it. That is the separation the design needed, between noticing and computing: Luna can compute the correct answer once told, but does not reliably act on impossibilities it notices.
2. **Detection is not the same as discounting.** Luna's summary identified impossible totals while its forecasts used two of those reports. This matches the capability-versus-deployment gap reported by [Pradhan & Goley (2026)](https://arxiv.org/abs/2606.05403).
3. **Impossibility types differ in difficulty.** The margin-of-error fabrication was missed by two configurations that caught every count impossibility. A reading guide should report detection by type rather than one validity score.
4. **Stronger configurations appear safe at this scope, weaker ones need verification.** An illustrative reading-guide contrast, which needs a larger collection before it could be issued:
   - GPT-6 medium, unprompted: dossiers with fabricated survey figures were read correctly.
   - GPT-5.6 Luna: fabricated figures were sometimes taken at face value; verify conclusions resting on quantitative reports, or supply a validity check first.

## Next

A bounded estimation collection for the weaker configurations would make these claims issuable:
- **Size:** more independent worlds, with fabrication types balanced by design rather than drawn at random.
- **Arms:** unprompted and explicit.
- **Stopping rule:** stop if face-value acceptance does not replicate.

The cost is about 0.3–0.4 million input tokens per nine-case context.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation fingerprint | `5544aa9fa92bb9ec37a60920b9d50164f96d9eac5a12e115fafccc035aece5cb` |
| research-world3-validation-pc-20260927.json | `b9177aff7b199f990f0fbacba0ab7626fb66b3c3b33c77fa2c2a20a13b03c660` |
| research-world3-validation-pc-20261027.json | `517ce503404e477ba595e484579ffb163c2bd7273e331fce15292a8dd4fe48cf` |
| plan.json | `49747e04eaff8457c832ac9beeffb4ff9ea50ac599e35ea58de86fb1aaf01345` |
| summary.json | `8f301da255b03a0e9eca59208dffe60e74928defb395ff282de54ef6a623ef2a` |
| execution.json | `cbd9109d71bf0d77df37cdf1184f8488fc02176382cceff21d0a3150e63ab236` |

Raw collections and transcripts remain private and outside Git. Model revisions are requested aliases, and execution is operator-asserted.
