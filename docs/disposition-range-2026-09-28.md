# Relative-judgement module (0.4) — 28 September 2026

Build and validation record. The [relay baseline experiment](disposition-baseline-2026-09-28.md) found that strongly worded descriptions map to fixed priors, while ambiguous ones move with the other outlets in view. This module tests that directly by varying the comparison set:
- disposition-model/0.4.0;
- disposition-design/0.4.0;
- disposition-tasks/0.4.0.

The predictions below were written before any collection.

**Result.** A fixed mapping. The mean contrast was −0.003 for Astra and +0.016 for Sol, within the preregistered ±0.05. Relative judgement is not supported. Ambiguous descriptions vary between contexts, most for Sol, independently of the comparison set.

## Design

**Targets.** Five descriptions are fixed in every context:
- two mildly reassuring: "sometimes runs its own surveys of retailers"; "has a few analysts who occasionally speak to suppliers";
- one irrelevant: "is based in a city on the coast";
- two mildly suggestive: "is a small newsletter with two analysts"; "usually publishes shortly after larger outlets".

These are the descriptions that drifted between 28% and 70% in earlier contexts.

**Comparison set.** Three outlets, all strongly reassuring or all strongly suggestive, depending on the variant:

| Variant | Comparison outlets |
| --- | --- |
| range-reassuring | employs twenty reporters who interview customers and suppliers before every call; has a research desk that visits the company's factories before every call; runs a monthly survey of two thousand retailers and publishes its method |
| range-suggestive | aggregator site with no reporters posting dozens of market calls a day; one-person blog posting within minutes of larger outlets; automated feed with no staff that rewrites other outlets' stories |

**Checkpoints (24):**
- **Each target:** a base-rate question, a relay probe and a forecast.
- **Each comparison outlet:** a base-rate question and a probe.
- **Three anchors,** without descriptions, pin sensitivity, bias and noise.

The comparison cases come first (the `comparison-first` order policy), so every target is judged with the range already established. Target cases render identically in both variants; only the comparison outlets differ. The model is the per-description fit of the cue modules, with eight slots.

## Predictions

**Measure.** For each configuration, the contrast is the mean implied target prior among reassuring outlets minus the mean among suggestive outlets. Each context type runs twice, and the contrast averages the two.

- **Relative judgement:** the targets look more relay-prone among outlets with reporters and research desks, and less so among aggregators and automated feeds. Predicts a contrast of at least +0.10, in both configurations.
- **Fixed mapping:** the targets are read the same way in either company. Predicts a contrast within ±0.05.
- **Irrelevant target:** reported separately. Astra's fixed 50% default predicts 50% in both variants. Sol's default depended on having something to compare against, so its irrelevant target may move.

The baseline experiment's repeat differences (0.00–0.07) set the noise floor for a single context.

## Validation

**Model recovery.** Both seeds passed every gate, including the new relative-judgement design. Implied priors for its eight slots were recovered at r = 0.982, error 0.040, coverage 0.93–0.94, in the agent-like noise band.

**Task pipeline.** Both seeds passed:
- **Audit:** 768 rendered cases.
- **Synthetic contexts:** 34 through the service, including a relative judge in each variant, recovered within 0.10.

**Change to the pipeline criterion.** At one seed, a learning context's start was estimated at 0.74 against a true 0.50. Its case order put three cases that are uninformative about relaying straight after the first informative case, so reveals accumulated before the start could show. The 90% interval ([0.45, 1.00]) correctly contained the truth. For single contexts, the learning-start check is now coverage by the 90% interval, widened by half a grid step, instead of a fixed tolerance on the mean. It passed on five seeds.

**Runner.** `comparison-first` joins the order policies. A new `range` preset runs Astra and Sol with each variant twice, 8 contexts, and the run summary reports the per-configuration contrast.

## Proposed run

8 fresh contexts (preset `range`), about 4.2 million input tokens, mostly cached, with an 8 million cap.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Model implementation fingerprint | `b277792e9d5d80768a4b7c3463ab73a101dad41d045bccf4db642a76bd2cb1ba` |
| Model recovery, seed 20260927 | `b16b96b4ba0b31aa732aef2119ffbaa9b6d5aaee6f911a62dc36507c77aaf884` |
| Model recovery, seed 20261027 | `0b43a57404a0bff0efc19e4755ac3da97fdbd4f397c0047055cf61160c22ac38` |
| Tasks implementation fingerprint | `7cbee7762191eb4f4c1afb1160ba0605eceb1f87a34062c417cff008ee85f140` |
| Task validation, seed 20260927 | `ceeb6a3cc0461b63f0dd45cacfbda26e8e89426ce26b02b989f00675051df714` |
| Task validation, seed 20261027 | `a0073f5dbc45201c506b85a50e54dee042a5dd7443e9059313e469818e38ba34` |

Validation outputs remain in the ignored `output/` directory.

## Results

**Collection.** All 8 contexts completed with the minimum 27 calls and no tool errors, in 98–308 seconds. They used 4,089,347 input tokens (3,853,440 cached), and the run summary completed. Tables regenerate with `uv run python -m epistemics.ledger runs output/disposition-range-20260928` and `… contrast …`.

Target priors, implied, averaged over the two contexts of each variant. Targets in order: surveys, a few analysts, coast (irrelevant), two-analyst newsletter, publishes after larger outlets.

| Configuration | Among reassuring outlets | Among suggestive outlets | Contrast per target | Mean contrast |
| --- | --- | --- | --- | --- |
| GPT-6 Astra | 0.45, 0.50, 0.50, 0.55, 0.67 | 0.49, 0.49, 0.49, 0.49, 0.72 | −0.04, +0.01, +0.01, +0.06, −0.05 | −0.003 |
| GPT-6 Sol | 0.36, 0.43, 0.29, 0.53, 0.64 | 0.28, 0.40, 0.40, 0.43, 0.64 | +0.08, +0.02, −0.11, +0.10, −0.01 | +0.016 |

The comparison outlets themselves were read at their extremes: 0.00–0.10 when reassuring, 0.70–0.95 when suggestive. Stated and implied priors again agreed.

**Against the predictions.** The fixed-mapping prediction holds for both configurations: mean contrasts of −0.003 and +0.016, within ±0.05. The relative-judgement prediction (at least +0.10 in both) is not supported. No single target shows a consistent contrast across both configurations.

**The variation is between contexts.** It does not track the comparison set. Sol's targets differ by up to 0.20 between the two contexts of the same variant: the coastal outlet was 0.50 in one suggestive context and 0.30 in the other, and the newsletter 0.36 and 0.50. Astra's targets stayed within 0.40–0.73, with the coastal outlet at 0.49–0.50 in all four contexts. Sol placed the uninformative coastal outlet near 30% in three of four contexts, consistent with its cold default (35–40%) in the baseline experiment.

## Interpretation

1. **Ambiguous descriptions are not judged relative to the comparison set.** A three-outlet comparison set at either extreme left the targets' priors unchanged on average. The relative-judgement account suggested by the baseline experiment is not supported by its confirmatory test.
2. **What moves the ambiguous descriptions is variation between contexts.** The comparison set does not drive it. It is largest for Sol, where the same sentence can be read 0.1–0.2 apart in two fresh contexts with the same design. This matches the relay retest. It is a reliability property of how a configuration interprets ambiguous evidence, not a context effect that a model term can predict.
3. **Consequences for the model and the reading guide.**
   - **The mapping:** a fixed description-to-prior mapping, with a per-configuration, per-description context-level variance.
   - **Default prior:** Astra's default for an uninformative source is a stable 50%. Sol's is lower, about 30–40%, and less stable.
   - **Reading-guide entry:** "Sol's priors from ambiguous source descriptions vary between sessions by up to 0.2; prefer explicit base rates."

## Next

- Estimate the context-level variance directly: several fresh contexts of the same design per configuration, fitted hierarchically.
- Weaker configurations on the description modules.
- Dossier transfer, starting with descriptions at the fixed extremes.

## Commitments (run)

| Artifact | SHA-256 |
| --- | --- |
| plan.json | `01bc1cde484602b9c5e2d90776cf8666064fe1e8e498c4d4b8ed064a70f5a295` |
| execution.json | `347376c495a98c351120bc6af4f6d16a1541a8e04be45ad889f8f3b933c2a444` |
| summary.json | `011776f2f918c269b8de76a87ca807810ca7230ee46f190915b4fc9dfa0f1fe5` |
