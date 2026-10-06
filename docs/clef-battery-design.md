# Clef cognitive battery: decision parameters on urns, tested on a central-bank desk (design)

Written 6 October 2026, before any battery data. Status: run on 6 October 2026; see [Results](#results-6-october-2026). Exploratory. The aim is a fast check of whether parameters of the kind computational psychiatry fits transfer from abstract tasks to a recognisably financial one, and whether they can be used to correct the model. The [Clef pilot](clef-pilot-design.md) gives the background on Clef. The pilot's plain cases already gave a teaser of the Grether weights:
- **Clef:** prior weight 1.04, evidence weight 1.02.
- **Clef-flash:** prior weight 0.52, evidence weight 0.81, bias −0.62.

## Tasks

Each task is posed twice: on urns (the abstract version) and on a central-bank desk (the finance version). The officials are fictional and the language generic.

| Task | Urn version | Desk version | Parameters |
| --- | --- | --- | --- |
| **Bookbag** (Phillips & Edwards 1966; Grether 1980) | Two urns (60:40 or 70:30), a prior of 10–90%, then 1, 3 or 5 draws with replacement. 120 items | The market-implied chance of a rate rise, and 1, 3 or 5 policymakers' signals, each matching the decision 60% or 70% of the time, independently. 120 items | Fitted in log-odds as z = α·prior + β·evidence + bias:<br>• α, the prior weight (below 1 is base-rate neglect);<br>• β, the evidence weight (below 1 is conservatism, above 1 overreaction);<br>• bias;<br>• δ, extra evidence weight when the sample agrees with the prior's leaning (confirmation);<br>• β by sample size (neglect of sample size) |
| **Beads** (Huq, Garety & Hemsley 1988) | Jars of 85:15 or 60:40 beads, even prior. After each prefix of eight five-draw sequences, a choice: decide jar A, decide jar B, or draw again. A correct decision wins 100, a wrong one loses 100, and each extra draw costs 5. 58 states | Even odds of a rise or a hold, and speakers signalling one at a time. A choice: take a position on a rise, take one on a hold, or wait for the next speaker. $100k for a correct position, $100k lost for a wrong one, $5k per further speaker. 58 states | P(decide now) = σ(κ(\|posterior log-odds\| − θ)). θ is the evidence threshold, against the optimal one; optimal stopping decides once one side leads by two. Also expected draws before deciding, and the slope of the stated belief on the posterior |
| **Tone** | A ball with a 30, 50 or 70% prior of red. An observer says "I think it's probably red" (hedged), "It's red" (plain) or "It's definitely red. Confirmed." (confident), with no record or with a 70% record. 36 items | A committee member's remark worded the same three ways ("…definitely raise rates… That is settled"), with no record or a 70% record. 36 items | The shift from the prior towards the reported side, per wording. The tone index is confident minus hedged with no record; it is ideally 0 with a record |

**Phrasings.** Every item is written in three phrasings, and the analysis averages over them: log-odds for probabilities, probabilities for choices. The pilot found Clef shifts by 0.3 log-odds under a paraphrase.

**Belief question.** Each beads state also gets a belief question (the probability of jar A, or of a rise), on the first phrasing only.

**Calls.** Questions are asked one per call: `noul` for probabilities and `choice` for the beads decision. That is 1,400 calls per model, 2,800 for Clef and Clef-flash.

## Transfer and mitigation

**Transfer, within each model.**
- Fit the parameters on the urns.
- Predict the desk answers from those urn parameters.
- Compare that prediction with three baselines:
  - an ideal Bayesian;
  - the other model's urn parameters (a mismatched passport);
  - the desk's own fit (an in-sample ceiling, not a test).
- **Reading.** A parameter transfers if the urn fit predicts the desk well below Bayes and below the mismatched parameters, and close to the ceiling. The urn and desk values are also set side by side.

**Mitigation: Grether inversion.** On the desk the market prior is known, so a desk answer z can be inverted through the model's urn-fitted map:
1. Recover the evidence weight it gave: (z − α·prior − bias)/β.
2. Re-apply that evidence at weight 1.

Error against the Bayesian answer is compared raw, inverted with the model's own urn parameters, and inverted with the other model's. This mitigation is bound to the model's identity by construction.

## Analysis details (`ledger/clef_battery.py`)

- **Clipping.** Probabilities are clipped at 0.05% and 99.95%; Clef reports four decimals.
- **Bookbag fitting range.** Weights are fitted on the 108 items whose Bayesian answer lies within ±4 log-odds. This selects on the design, not on the answers, so it does not bias the slopes. Beyond that range answers saturate.
- **Intervals.** 90% bootstrap intervals over items.
- **The simple fit and the full fit.** The simple Grether fit (α, β, bias) absorbs any confirmation asymmetry. The full fit with δ is reported alongside it.
- **Beads.** θ and κ are fitted by least squares per ratio.

**Parameter recovery** (`tests/test_clef_battery.py`). The synthetic responders are offline. They have known α, β, δ, bias, θ, κ and tone shifts, identical in both domains, and run through the whole path: frozen plan, parallel run, analysis.
- **Recovered values:** α, β and δ within 0.05, θ within 0.15, tone index within 0.1, and a tone index of 0 with a record.
- **Transfer and inversion** both pick out the model's own parameters over the other model's.

## Prediction (exploratory)

- **Bookbag.** Clef near Bayes (α, β ≈ 1). Clef-flash showing base-rate neglect and conservatism with a negative bias, as in the pilot's plain cases.
- **Transfer.** If these are general parameters of each model, each model's urn fit predicts its desk answers better than Bayes and better than the other model's parameters, and inversion with its own parameters lowers its desk error.
- **Beads and tone.** No prediction.

## Commands

```
uv run python -m epistemics.clef plan --root output/clef-battery-<date> --design battery
uv run python -m epistemics.clef run --root output/clef-battery-<date> --workers 4
uv run python -m epistemics.ledger clef-battery output/clef-battery-<date> --output output/clef-battery-<date>.json
```

## Results (6 October 2026)

**The run.**
- The root is `output/clef-battery-20261006`: 2,800 of 2,800 calls, with no errors, retries or parse failures.
- Four workers, about 8 minutes, 640K Workers AI input tokens (about $0.15).

**Regenerating the tables.**

```
uv run python -m epistemics.ledger clef-battery output/clef-battery-20261006 --output output/clef-battery-20261006.json
```

Every number below comes from that file. Values are in log-odds unless stated; brackets are 90% bootstrap intervals over items.

### Bookbag: Clef-flash's base-rate neglect transfers to the desk

| | α (prior weight) | β (evidence weight) | Bias | δ (confirmation) | R² |
| --- | --- | --- | --- | --- | --- |
| Clef, urn | 0.83 [0.74, 0.91] | 1.41 [1.30, 1.56] | −0.34 | 0.19 [−0.07, 0.42] | 0.85 |
| Clef, desk | 0.70 [0.62, 0.78] | 1.09 [1.02, 1.19] | +0.23 | 0.09 [−0.08, 0.25] | 0.86 |
| Clef-flash, urn | 0.40 [0.30, 0.50] | 1.21 [1.11, 1.36] | −0.19 | 0.26 [0.01, 0.50] | 0.76 |
| Clef-flash, desk | 0.28 [0.20, 0.37] | 1.10 [1.02, 1.23] | −0.24 | 0.28 [0.08, 0.47] | 0.81 |

**Error predicting the desk answers** (RMSE in log-odds):

| | From its own urn fit | Ideal Bayes | Other model's urn fit | Desk's own fit (ceiling) |
| --- | --- | --- | --- | --- |
| Clef-flash | 0.84 | 1.41 | 1.18 | 0.81 |
| Clef | 1.05 | 0.91 | 1.00 | 0.72 |

- **Clef-flash's profile holds in both domains:** strong base-rate neglect, evidence weighted slightly above Bayes, a confirmation asymmetry and a pessimistic bias. Its urn parameters predict its desk answers almost as well as the desk's own fit, and far better than Bayes or Clef's parameters.
- **Clef shows milder base-rate neglect in both domains.** Its evidence weight and bias change between domains, and its urn fit predicts the desk no better than Bayes.

**Inversion** (mean error against Bayes on the desk):

| | Raw | Inverted with its own urn parameters | Inverted with the other model's |
| --- | --- | --- | --- |
| Clef-flash | 1.17 | 0.57 | 0.69 |
| Clef | 0.74 | 0.60 | 0.67 |

Clef-flash's own map halves its desk error and beats the mismatched map.

**Sample-size neglect, in both models and both domains.** β by number of draws (1, 3, 5):

| | Urn | Desk |
| --- | --- | --- |
| Clef | 2.33, 1.57, 1.29 | 1.90, 1.22, 0.99 |
| Clef-flash | 2.82, 1.36, 1.07 | 1.91, 1.27, 0.99 |

A single signal is weighted about two to three times its Bayesian worth, and five signals about at their worth. In desk terms, one policymaker's signal moves these models nearly as far as several.

### Beads: both models jump to conclusions, on urns and on the desk

**The optimal policy** for these payoffs decides once one side leads by two. That is a threshold of 3.47 log-odds at 85:15 and 0.81 at 60:40, and 3.25 expected draws along the test sequences.

**What the models do:**

| | Threshold θ (85:15, 60:40) | Expected draws (85:15, 60:40) | Decides before any draw |
| --- | --- | --- | --- |
| Clef, urn | 0.70, 0.00 | 0.93, 1.18 | 18%, 25% |
| Clef, desk | 1.55, 0.35 | 1.70, 1.85 | 13%, 16% |
| Clef-flash, urn | 1.15, 0.20 | 0.91, 0.98 | 32%, 34% |
| Clef-flash, desk | 0.05, 0.10 | 1.28, 1.58 | 15%, 16% |

**When they decide, they pick the favoured side** 83–92% of the time.

**Predicting desk decisions** (mean absolute error in P(decide)):
- From the urn fit 0.12–0.17, against 0.32–0.38 for the optimal policy (in-sample ceiling 0.09–0.13).
- The other model's urn fit does as well (0.11–0.14).

**Reading.** Jumping to conclusions transfers in direction, but it is shared by both models, not specific to either.

**Beliefs and decisions dissociate.** Their stated beliefs on the same states track the posterior (slopes 0.98–1.13). So they decide early while reporting appropriately uncertain beliefs.

### Tone: no consistent wording trait

**Clef.**
- **No record.** A report shifts its answer 1.3 (hedged), 2.8 (plain) and 3.0 (confident) on urns, and 1.8, 2.6 and 2.6 on the desk. The tone index is 1.69 on urns and 0.87 on the desk.
- **With a 70% record** (Bayesian shift 0.85), it still shifts 1.2–1.7 on urns and 1.6–2.6 on the desk. On the desk the record changes almost nothing (record weight 1.9–3.1×).
- **Prediction.** Its urn shifts predict its desk answers no better than a wording-blind version (1.01 against 1.04).

**Clef-flash** reverses: the tone index is −0.55 on urns and +0.71 on the desk.

**Reading.** Both models give a bare report far more weight than a 70% source deserves. Neither has a wording trait that carries across domains.

### Phrasing

Averaged over items, the spread across the three phrasings is 0.25–0.66 log-odds for probabilities and 0.06–0.11 for P(decide). Averaging over three phrasings is necessary.

### Reading (exploratory, product claims to confirm)

These are two models on one mirrored desk. The desk uses the same numbers as the urns in a different story, so this is near transfer. A naturalistic test, Fed-style text without stated hit rates, comes next.

1. **Clef-flash's base-rate neglect is a transferable, model-specific parameter, and the mitigation it supports works.** Inverting its answers through its own urn-fitted map halves its desk error and beats the mismatched map. This is the clearest computational-psychiatry-style result so far: a fitted parameter, a transfer test, and a correction bound to the model.
2. **Sample-size neglect is a shared, transferable regularity.** One signal is over-weighted two to three times, an aggregate is weighted about right. Desk mitigation: pool signals before asking.
3. **Jumping to conclusions is also shared and transferable.** Both models decide on about one piece of evidence where the payoffs warrant about three, while their stated beliefs remain appropriately uncertain. The mitigation follows directly: decide from the stated belief with an external threshold.
4. **Tone does not separate these models.** Both over-weight bare reports.

## Far transfer (design, written 6 October 2026 before its data)

The near desk mirrored the urn task's numbers. The far desk uses natural-language remarks from fictional committee members, with the market price stated but no hit rates and no counts. There is no exact Bayesian answer, so each test uses a property that any Bayesian answer must have.

**Remarks** (65 items). The market-implied probability of a rate rise takes five levels (20–80%). Thirteen sets of remarks run from none to five, each remark pointing to a rise or a hold, with the same remarks at every price. Three phrasings each.
- **Price weight α.** The slope of the answer on the price's log-odds, with a fixed effect per set of remarks. A Bayesian moves one-for-one with the price (α = 1). The primary estimate uses the sets with a net of at most one remark, which keeps answers away from saturation; all sets are a check.
- **Inversion.** Apply the urn-fitted map to the far answers and refit α, which should then be 1. Repeat with the other model's map.
- **Sample size.** The evidence from 3 and from 5 agreeing remarks, relative to 1, after removing the price with α. For independent speakers Bayes gives 3 and 5. The urn fit predicts 3β₃/β₁ and 5β₅/β₁.

**Waiting** (21 states). Even odds, remarks heard so far, and the choice: take a position now or wait (the beads payoffs). Measured: P(take a position) with nothing heard, and by net count, against the near desk.

**Calls.** 258 per model. Analysis: `ledger/clef_far.py`. Recovery test: `tests/test_clef_far.py`. The synthetic responder recovers α within 0.03 and the sample-size ratios within 0.05. Inversion with the model's own map restores α to 1; the mismatched map does not.

**Prediction (exploratory):**
- **Clef-flash's price weight** stays well below 1, near its urn value (0.40). If so, inversion with its own urn map brings it near 1, and Clef's map leaves it short.
- **Clef's price weight** is nearer 1.
- **Sample-size ratios** fall below Bayes for both models, towards the urn predictions.
- **Both models** sometimes take a position with nothing heard.

```
uv run python -m epistemics.clef plan --root output/clef-far-<date> --design far
uv run python -m epistemics.clef run --root output/clef-far-<date> --workers 4
uv run python -m epistemics.ledger clef-far output/clef-far-<date> --battery output/clef-battery-20261006 --output output/clef-far-<date>.json
```

## Far-transfer results (6 October 2026)

**The run.** The root is `output/clef-far-20261006`: 516 of 516 calls, no errors, 141K input tokens, about a minute.

**Regenerating the tables.**

```
uv run python -m epistemics.ledger clef-far output/clef-far-20261006 --battery output/clef-battery-20261006 --output output/clef-far-20261006.json
```

### Price weight: the prediction failed

The price weight is the slope on the price's log-odds, with a fixed effect per set of remarks. A Bayesian answer has a slope of 1.

| | Urn α | Far α (sets with net ≤ 1) | Far α (with at least one remark) | Far α (no remarks) | Far α (all sets) |
| --- | --- | --- | --- | --- | --- |
| Clef | 0.83 | 1.42 [1.22, 1.64] | 1.31 [1.12, 1.51] | 2.10 | 0.99 |
| Clef-flash | 0.40 | 1.39 [1.20, 1.60] | 1.32 [1.11, 1.53] | 1.84 | 0.88 |

**What they do instead.** With natural remarks, both models amplify the market's lean rather than neglecting it.
- **With no remarks,** a 20% price becomes a 5–8% answer, 35% becomes 7–16%, and 80% becomes 89–92%.
- **With remarks,** the slope is still about 1.3.
- **The two models no longer differ,** so Clef-flash's base-rate neglect does not carry to this desk. It is specific to explicit-probability problems.
- **Inversion makes it worse.** Through Clef-flash's own urn map the far slope goes from 1.39 to 1.82; through Clef's map it stays at 1.40.

### Sample size: the urn fit predicts the far desk

| | Evidence of 3 agreeing remarks against 1 | 5 against 1 | Bayes | Urn fit predicted |
| --- | --- | --- | --- | --- |
| Clef | 2.14 | 2.27 | 3, 5 | 2.02, 2.78 |
| Clef-flash | 1.65 | 1.87 | 3, 5 | 1.45, 1.90 |

**Evidence is compressed.** Five agreeing remarks are worth about twice one remark, not five times. Clef-flash's ratios match the urn prediction closely, and Clef's 3:1 ratio does too. The answers with five agreeing remarks average 3.3–3.5 log-odds, well inside the clip.

### Waiting: jumping to conclusions carries over

| | Position with nothing heard | Net 0 (after remarks) | Net 1 | Net 2 | Near desk: nothing heard, net 1 |
| --- | --- | --- | --- | --- | --- |
| Clef | 13% | 18% | 40% | 93% | 15%, 55% |
| Clef-flash | 11% | 26% | 47% | 70% | 15%, 67% |

Both models still sometimes take a position with nothing heard, and nearly half decide on a lead of one remark.

### Reading (exploratory)

Of the three near-transfer results:

| Result | Far transfer |
| --- | --- |
| Sample-size neglect, shared | Survives, and quantitatively for Clef-flash: the urn fit predicts the far ratios |
| Jumping to conclusions, shared | Survives |
| Clef-flash's base-rate neglect, model-specific | Does not survive |

**What replaces it.** With natural remarks, both models over-weight the market price (about 1.3–1.4) and sharpen it when there is no news. The inversion that halved Clef-flash's near-desk error would make its far answers worse. A parameter-based correction therefore needs the parameter to be measured in the domain where it is applied, or a battery whose urn tasks carry the same features: natural language and no stated probabilities.

**For the demo, the transferable traits are sample-size neglect and jumping to conclusions.** Both have direct mitigations:
- **Sample-size neglect:** pool speakers before asking, or correct by the urn-fitted compression curve.
- **Jumping to conclusions:** ask for the belief, then act at the optimal threshold.

Neither is model-specific between Clef and Clef-flash.

