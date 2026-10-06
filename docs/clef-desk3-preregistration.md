# Preregistration: a passport mitigation that works without the model's own track record

Written and committed on 6 October 2026, before any data from this desk. The design, hypotheses, tests, decision rule and code (`epistemics.clef.desk3`, `ledger/clef_desk3.py`) are fixed by this commit.

## Background

**The first desk** ([clef-desk-demo.md](clef-desk-demo.md)) favoured the passport lane by construction.

**On the robustness desk:**
- speakers had unequal, unstated reliabilities;
- two of them echoed the previous speaker;
- remarks were mild or mixed;
- parameters were learned from 40 past meetings.

There, the passport mitigation was no better than a generic recalibration of the model's own beliefs. Recalibration needs a track record of this model's own forecasts against outcomes. A post-hoc check on the same 60 test meetings suggested that recalibration fails when that record is short, while the passport mitigation, which needs only facts about the speakers, does not. This test confirms or refutes that on fresh meetings.

**The passport behind the mitigation** (the [Clef battery](clef-battery-design.md)) found three things:
- Both Clef models decide before the evidence warrants (jumping to conclusions).
- They compress multiple signals (sample-size neglect).
- They read single signals reliably.

The mitigation follows from that: the model only classifies each remark, code adds the evidence with each speaker's record as weight, and code decides when to act at the optimal threshold.

## Design

**The world.** The same robustness world as desk2, on fresh seeds:
- ten fictional speakers with true reliabilities 0.55–0.85;
- two echoers who repeat the previous speaker's direction with probability 0.8;
- remarks strong (45%), mild (40%) or mixed (15%);
- six speakers per meeting;
- market prices of 35%, 50% or 65%, with the outcome drawn from the price;
- payoffs of ±$100k for a position, $5k for each speaker waited.

**Two kinds of history, kept separate:**
- **Domain record:** 40 past meetings form the speakers' scorecard ("Governor Hale 23 of 25"). It is fixed, shown to every lane (inside the model's prompts as well), and used by the passport lane for its weights. Every threshold uses the optimal policy for the committee's mean estimated record.
- **The model's own forecast record:** a pool of 100 past meetings on which the model's beliefs are collected. Generic recalibration is fitted on k of them: a logistic regression of the outcome on the model's belief log-odds and the price log-odds, with a small ridge.

**Scoring** is on 400 held-out test meetings, for both models (Clef and Clef-flash): 13,314 calls in all.

**Lanes:**

| Lane | What it uses | Decision |
| --- | --- | --- |
| **alone** | The model's act-or-wait choice | The model decides |
| **gated** | The model's belief | Optimal threshold |
| **recalibrated_k** | The model's belief, recalibrated on k own-forecast meetings. For k < 100, averaged over 20 random draws (seed 20261013); k = 5, 10, 20, 40, 100 | Optimal threshold |
| **passport** | The model's classification of each remark. Evidence (2·P(hawkish) − 1)·logit(estimated record) is added to the price log-odds | Optimal threshold |
| **oracle** | The exact posterior under the true reliabilities and echoes | Optimal threshold |

## Hypotheses (primary)

For each model:
- **H1.** The passport lane earns more per meeting than generic recalibration fitted on 10 meetings of the model's own forecast record.
- **H2.** The passport lane earns more per meeting than the model alone.

**Test.**
- **Statistic:** the mean of the per-meeting paired P&L differences (passport minus comparator) over the 400 test meetings. For H1 the comparator's P&L per meeting is averaged over its 20 draws.
- **p-value:** one-sided, from a sign-flip permutation test (100,000 permutations, seed 20261014).
- **Correction:** Holm across the four tests (two hypotheses × two models).
- **Decision rule:** a hypothesis passes for a model if its Holm-adjusted p < 0.05 and the mean difference is positive.

**Power** (estimated from desk2, a different design, so approximate):
- **H1:** differences of about 16 (Clef) and 27 (Clef-flash), with a per-meeting SD of about 62. With n = 400 the SE is about 3.1, and power is above 0.95 for both.
- **H2:** for Clef-flash about 39, so power is above 0.95. For Clef about 10 (desk2 interval −12 to 31), with an SD of about 100: power is about 0.4 at the Holm-adjusted level. A failure of H2 for Clef would be uninformative about a small effect.

## Secondary (descriptive, no tests)

- Recalibration at every k; the curve predicted to converge on the passport lane by k = 40–100.
- The gated lane.
- The oracle minus the passport lane.
- Positions taken with nothing heard.
- Speakers heard.
- Classification accuracy by remark strength.

## Prediction

- **H1 passes for both models.**
- **H2 passes for Clef-flash.** For Clef it is uncertain.
- **Recalibration catches up** with the passport lane by k = 40–100.

## Commands

```
uv run python -m epistemics.clef plan --root output/clef-desk3-20261006 --design desk3
uv run python -m epistemics.clef run --root output/clef-desk3-20261006 --workers 6
uv run python -m epistemics.ledger clef-desk3 output/clef-desk3-20261006 --output output/clef-desk3-20261006.json
```

## Deviations

None so far. Any deviation will be recorded here before the analysis is run.
