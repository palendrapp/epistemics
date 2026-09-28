# Relative-judgement module (0.4) — 28 September 2026

Build and validation record. The [relay baseline experiment](disposition-baseline-2026-09-28.md) found that strongly worded descriptions map to fixed priors, while ambiguous ones move with the other outlets in view. This module tests that directly by varying the comparison set:
- disposition-model/0.4.0;
- disposition-design/0.4.0;
- disposition-tasks/0.4.0.

It has not been run yet. The predictions below were written before any collection.

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
