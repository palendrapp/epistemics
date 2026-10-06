# Preregistration: the calibrated passport mitigation against the model alone (second confirmation)

Written and committed on 6 October 2026, before any data from this desk. The design, hypotheses, tests, decision rule and code (`epistemics.clef.desk4`, `ledger/clef_desk4.py`) are fixed by this commit.

## Why a second confirmation

The [first confirmation](clef-desk3-preregistration.md) gave two results:
- **Its H1 passed for both models:** the passport mitigation beat generic recalibration fitted on 10 meetings of the model's own forecasts.
- **Its H2 failed for both:** the mitigation did not beat the model alone (−0.3 for Clef; +10.3 for Clef-flash, Holm p 0.098).

**After seeing that** (post hoc, on the same meetings), we found that most of the loss was misclassified mild remarks. Calibrating the model's remark classifier on the desk's labelled past remarks lifted the mitigation to +6.0 (Clef) and +21.8 (Clef-flash) over the model alone. Those labelled remarks are domain facts, not the model's forecasts.

**This test.** It confirms or refutes that on 1,000 fresh meetings. It is a second attempt after a failed hypothesis, and both confirmations are reported together.

## Design

**The world.** The same robustness world as desk2 and desk3, on new seeds:
- ten fictional speakers with true reliabilities 0.55–0.85, never stated;
- two echoers who repeat the previous speaker's direction with probability 0.8;
- remarks strong (45%), mild (40%) or mixed (15%);
- six speakers per meeting;
- market prices of 35%, 50% or 65%, with the outcome drawn from the price;
- payoffs of ±$100k for a position, $5k for each speaker waited.

**Data:**
- **Record:** 40 past meetings.
  - They give the speakers' scorecard, shown to every lane (inside the model's prompts as well) and used by the passport lane for its weights.
  - They also give the 186 distinct labelled remarks on which the passport lane calibrates the model's classifier: a logistic regression from the classifier's log-odds to the known direction.
- **Pool:** 100 past meetings of the model's own beliefs, for generic recalibration on k of them (logistic on its belief log-odds and the price log-odds).
- **Test:** 1,000 held-out meetings (480 rises).

**Thresholds.** Every lane except the model alone uses the optimal policy for the committee's mean estimated record.

**Models and size.** Clef and Clef-flash; 30,492 calls in all.

**The mitigation (calibrated passport lane):**
1. The model answers "Is this remark signalling a rate rise at the next meeting?" for each remark.
2. That probability goes through the calibration map.
3. The evidence (2·P − 1)·logit(estimated record) is added to the price log-odds.
4. Code acts at the optimal threshold.

## Hypotheses (primary)

For each model:
- **H1.** The calibrated passport lane earns more per meeting than the model alone (the model's own act-or-wait choices).
- **H2.** The calibrated passport lane earns more per meeting than generic recalibration on 10 meetings of the model's own forecasts (averaged over 20 random draws from the pool, seed 20261023).

**Test.**
- **Statistic:** the mean of the per-meeting paired P&L differences over the 1,000 test meetings.
- **p-value:** one-sided, from a sign-flip permutation test (100,000 permutations, seed 20261024).
- **Correction:** Holm across the four tests.
- **Decision rule:** a hypothesis passes for a model if its Holm-adjusted p < 0.05 and the mean difference is positive.

**Power** (from the post-hoc estimates, which a fix chosen after seeing the data probably inflates):
- **Clef, H1:** effect about +6, per-meeting SD about 94. At n = 1,000 the SE is about 3.0, giving power of about 0.65 at α = 0.05 and 0.42 at α = 0.0125. Holm is step-down, so if the other three tests pass, Clef's H1 is tested at 0.05. A smaller true effect means lower power. A failure would not rule out a small effect.
- **Clef-flash, H1:** effect about +22, SD about 108: power about 1.0.
- **H2 for both:** it replicates the first confirmation's H1, with power about 1.0.

## Secondary (descriptive, no tests)

- The uncalibrated passport lane, and calibrated minus uncalibrated.
- Recalibration at k = 5, 10, 20, 40, 100.
- The gated lane.
- The oracle gap.
- Positions taken with nothing heard, and speakers heard.
- Classification accuracy by strength, raw and calibrated.
- The calibration map.

## Prediction

- **H1 passes for Clef-flash.** For Clef it is uncertain (about +6 if real).
- **H2 passes for both.**
- **Calibration helps both models' passport lanes.**

## Commands

```
uv run python -m epistemics.clef plan --root output/clef-desk4-20261006 --design desk4
uv run python -m epistemics.clef run --root output/clef-desk4-20261006 --workers 6
uv run python -m epistemics.ledger clef-desk4 output/clef-desk4-20261006 --output output/clef-desk4-20261006.json
```

## Deviations

**None to the primary analysis.** After it ran, one descriptive secondary was added to the ledger output: the passport lane minus the gated lane (no test).

## Results (6 October 2026)

**The run.** The root is `output/clef-desk4-20261006`: 30,492 of 30,492 calls, no errors, 13.5M Workers AI input tokens (about $3.25). The 1,000 test meetings include 480 rises. The committee's mean estimated record is 0.76.

**Regenerating the tables.**

```
uv run python -m epistemics.ledger clef-desk4 output/clef-desk4-20261006 --output output/clef-desk4-20261006.json
```

### Primary: all four hypotheses pass

| | Mean paired difference ($k per meeting) | SE | One-sided p | Holm p | Result |
| --- | --- | --- | --- | --- | --- |
| Clef, H1: calibrated passport − alone | +9.4 | 2.8 | 0.0004 | 0.0004 | **passes** |
| Clef-flash, H1 | +24.6 | 3.7 | < 0.0001 | < 0.0001 | **passes** |
| Clef, H2: calibrated passport − recalibrated on 10 | +20.9 | 2.2 | < 0.0001 | < 0.0001 | **passes** |
| Clef-flash, H2 | +18.2 | 2.3 | < 0.0001 | < 0.0001 | **passes** |

### Secondary (descriptive)

**P&L per meeting** ($k):

| Lane | Clef | Clef-flash |
| --- | --- | --- |
| alone | 35.0 | 17.7 |
| gated | 43.6 | 41.5 |
| recalibrated, k = 5, 10, 20, 40, 100 | 22.8, 23.4, 35.5, 38.0, 42.5 | 18.8, 24.1, 33.9, 35.5, 39.6 |
| passport, uncalibrated | 39.2 | 33.3 |
| **passport, calibrated** | **44.3** | **42.3** |
| oracle | 53.7 | 53.7 |

**Calibration.** It adds +5.1 (SE 2.2) and +9.0 (SE 2.5) over the uncalibrated passport lane. The classifier's accuracy on mild remarks rises from 82% to 98% (Clef) and from 74% to 99% (Clef-flash). On mixed remarks it falls from 93% to 87% and from 100% to 89%. The map was fitted on 186 labelled remarks.

**Gaps:**
- The oracle exceeds the calibrated passport lane by 9.3 (SE 2.2) and 11.4 (SE 2.3).
- Recalibration needs about 100 of the model's own forecast meetings to come within 2–3 of the passport lane.

**Positions with nothing heard:** 33% (Clef) and 67% (Clef-flash) alone; 0% in every other lane.

**The generic gated lane** (the model's own belief, acted on at the optimal threshold) matches the passport lane on this desk: passport minus gated is +0.7 (SE 2.2) and +0.8 (SE 2.3). On the first confirmation desk the same lane earned 34.1 and 24.0, because there the model's belief with nothing heard (amplifying the price) crossed the threshold in two meetings of three or more. Across the two desks:

| Lane | First desk (Clef, flash) | This desk (Clef, flash) |
| --- | --- | --- |
| gated | 34.1, 24.0 | 43.6, 41.5 |
| calibrated passport | 45.8, 44.6 (exploratory) | 44.3, 42.3 (confirmed) |

### Reading (task-conditional)

1. **Confirmed on 1,000 fresh meetings, for both Clef models: the passport mitigation beats the model alone.** It classifies single remarks with a classifier calibrated on labelled past remarks, adds the evidence in code with each speaker's record as weight, and acts at the optimal threshold. The gain is +9.4k per meeting for Clef and +24.6k for Clef-flash. It is also confirmed, for the second time, to beat generic recalibration when only ten meetings of the model's own forecasts exist.
2. **Read with the first confirmation.** That test's H2 failed. The calibration step was chosen after it failed, on that desk's data, and this test confirms it on fresh meetings. Both results stand together.
3. **The mitigation needs no record of the model's own forecasts,** only domain facts: who said what before, and how often each speaker was right.
4. **A simpler generic fix, acting on the model's own belief at a threshold, can match it.** That holds only when the model's belief distortions happen not to cross the threshold, which they did on one desk and not the other. The passport lane does not rely on the model's beliefs at all.
5. **Scope:** one simulated desk family, fictional officials, two Clef models, P&L under stated payoffs. These are elicited outputs of a trained head, not beliefs.

