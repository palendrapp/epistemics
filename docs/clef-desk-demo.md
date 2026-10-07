# The central-bank desk: mitigations scored against outcomes, and the live demo

Written 6 October 2026, before the desk data; results below. This follows from the [Clef battery](clef-battery-design.md). Two traits transferred from urns to natural-language central-bank remarks, shared by Clef and Clef-flash:
- **Sample-size neglect:** five agreeing remarks are worth about twice one.
- **Jumping to conclusions:** positions taken with nothing heard, or after a lead of one.

The far desk had no exact answer, so it could not show that a mitigation helps. This desk adds outcomes.

## The simulated desk (`epistemics.clef.desk`)

**Episodes.** There are 60, seeded.
- The market price for a rate rise is 35%, 50% or 65%.
- The outcome is drawn from the price, so the price is calibrated (28 rises in 60).
- Up to six fictional committee members speak.
- Each remark points to the outcome with probability 0.7, and the case states this as their record.
- Remarks come from eight hawkish and eight dovish sentences.

**Payoffs.** As in the beads task: a correct position earns $100k, a wrong one loses $100k, and each speaker waited for costs $5k. With a 0.7 record, optimal stopping waits for a lead of two remarks.

**Questions,** with one phrasing, as the live demo uses:
- After each prefix of remarks (0–6 heard), the act-or-wait choice and, separately, the belief in a rise.
- Each distinct remark is also classified on its own: "Is this remark signalling a rate rise?"
- That is 979 calls per model.

## Lanes

The lanes are simulated from the answers, so the same answers feed every lane.

| Lane | Decision | Mitigates |
| --- | --- | --- |
| **alone** | The model's own act-or-wait choice | — |
| **gated** | The model's stated belief, acted on at the optimal threshold | Jumping to conclusions |
| **passport** | The model only classifies each remark. The evidence is added in code at the stated record, (2·P(hawkish) − 1)·logit(0.7) per remark, and acted on at the optimal threshold | Jumping to conclusions and sample-size neglect: the model does what it does well (classify one remark) and code does what it does badly (add up and wait) |
| **bayes** | The exact posterior at the optimal threshold | Reference |

**Scores.**
- **P&L per episode**, with 90% bootstrap intervals over episodes; differences between lanes are paired.
- **Behaviour:** positions taken with nothing heard, speakers heard, and correct positions.
- **Belief quality:** log loss of the belief at the decision, and distance from the exact posterior.
- **Also:** classification accuracy, and how the model's beliefs scale with the exact evidence.

**Recovery** (`tests/test_clef_desk.py`). A synthetic model that jumps to conclusions, compresses evidence and classifies correctly. Its passport lane matches the Bayes lane, and only its alone lane takes positions with nothing heard.

## Prediction (exploratory)

**Alone** takes some positions with nothing heard, and on a lead of one remark. **Gated** and **passport** take none with nothing heard.

**Ordering by P&L:** passport > gated > alone, with passport near the Bayes lane if classification is accurate.

**Beliefs** scale less than the exact evidence as remarks accumulate.

## Commands

```
uv run python -m epistemics.clef plan --root output/clef-desk-<date> --design desk
uv run python -m epistemics.clef run --root output/clef-desk-<date> --workers 4
uv run python -m epistemics.ledger clef-desk output/clef-desk-<date> --output output/clef-desk-<date>.json
```

## Results (6 October 2026)

**The run.**
- The root is `output/clef-desk-20261006`: 1,958 of 1,958 calls.
- Two calls failed on a provider overload (HTTP 529) and succeeded on resume; 529 is now retried.
- 60 episodes, 28 of them rises.

**Regenerating the tables.**

```
uv run python -m epistemics.ledger clef-desk output/clef-desk-20261006 --output output/clef-desk-20261006.json
```

**P&L per episode** ($k, 90% bootstrap intervals over episodes):

| Lane | Clef | Clef-flash | Positions with nothing heard (Clef, flash) | Speakers heard | Correct | Log loss | Distance from the exact posterior (log-odds) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| alone | 21.6 [0.8, 41.8] | 20.2 [0.2, 40.5] | 33%, 0% | 1.0, 1.3 | 63%, 63% | 0.95, 0.81 | 1.60, 0.85 |
| gated | 31.5 [11.2, 51.5] | 27.8 [7.7, 48.1] | 67%, 0% | 0.4, 1.8 | 67%, 68% | 0.94, 0.78 | 1.88, 0.79 |
| passport | **44.4 [27.4, 60.3]** | **44.0 [26.9, 60.2]** | 0%, 0% | 3.8, 3.9 | 82%, 82% | 0.48, 0.47 | 0.08, 0.25 |
| bayes | 38.2 [21.0, 55.2] | 38.2 [20.2, 56.0] | 0% | 3.7 | 78% | 0.52 | 0 |

**Paired differences** ($k per episode):

| | Clef | Clef-flash |
| --- | --- | --- |
| passport − alone | +22.8 [1.1, 44.2] | +23.8 [2.8, 44.1] |
| gated − alone | +9.9 [−9.5, 27.7] | +7.6 [−7.6, 22.9] |
| passport − gated | +12.9 [−8.0, 33.5] | +16.2 [−1.8, 34.6] |

The passport lane comes out slightly above the Bayes lane. That is within noise, from the classifications' slightly soft evidence on 60 episodes.

**What the model gets right and wrong:**
- **Classification is perfect.** All 139 distinct remarks are classified correctly. The mean P(hawkish) is 0.97 and 0.92 for hawkish remarks, and 0.01 and 0.02 for dovish ones.
- **Beliefs show the battery's sample-size neglect.**

  | | Net 1 | Net 2 | Net 3 | Net 4 |
  | --- | --- | --- | --- | --- |
  | Clef | 1.98 | 3.10 | 3.75 | 3.96 |
  | Clef-flash | 1.42 | 2.14 | 2.53 | 2.75 |
  | Bayes | 0.85 | 1.69 | 2.54 | 3.39 |

  One remark moves them two to two and a half times its worth; four move them about their worth or less.
- **The price is distorted before anyone speaks.** Clef's belief with nothing heard is 3%, 16% and 88% at prices of 35%, 50% and 65% (the far desk's price amplification). It takes a position on a rise at 65% with nothing heard. Clef-flash's are 41%, 69% and 81%, tilted towards a rise.

**Reading** (exploratory, 60 episodes):
- **The mitigation designed from the passport roughly doubles P&L and reaches the Bayes lane, for both models.** The model classifies each remark, which it does perfectly; code adds the evidence at the stated record and waits for the optimal threshold, which the model does badly.
- **Gating the model's own beliefs helps less.** Its beliefs carry the same distortions: amplified prices and an over-weighted first remark. Acting on them at the right threshold still acts on the wrong number.
- **For the passport:** trust these models' classifications of single signals; do not trust their aggregation of several, or their choice of when to act.

## Live demo (`epistemics.clef.demo`)

```
uv run python -m epistemics.clef.demo            # live and replay, http://127.0.0.1:8765
uv run python -m epistemics.clef.demo --replay   # replay only, no credentials needed
```

**How it works.** A standard-library server bound to 127.0.0.1 serves one page and streams each act as server-sent events.
- **Live mode** calls Workers AI, six requests at a time. Credentials come from the environment or `.env` and never reach the page.
- **Replay mode** reads the recorded roots. Clef is deterministic, so live and replay give the same numbers. A live run of act 1 reproduced the recorded values to every digit (Clef-flash: five draws worth 1.2972… times one; decides with nothing drawn 31.6%).
- `tests/test_clef_demo.py` checks that replay reproduces the ledger in every act.

**The acts.** Model (Clef or Clef-flash), mode and speed are chosen at the top of the page.
1. **Passport: abstract tasks.** Unanimous bookbag samples at every prior and hit rate (the ledger's `unanimous` estimator), and six beads states. The passport card fills in:
   - five draws worth X times one (Bayes 5);
   - one draw weighted Y times its worth;
   - decides with no evidence;
   - decides on a lead of one.
2. **Transfer: the central-bank desk.** Unanimous remark sets at every price. The ratio of several speakers to one is drawn against Bayes and against the urns' ratio. Also shown: the share of positions taken with nothing heard.
3. **Mitigation: trading it.** The 60 desk meetings, traded by the three lanes and the Bayes reference. Each remark gets a classification badge, and the cumulative P&L chart and per-meeting scores update as the run goes.

**Numbers on screen** (identical to the ledger):

| | Five draws vs one (urns) | Five speakers vs one (desk) | P&L per meeting: alone, gated, passport (Bayes 38.2) |
| --- | --- | --- | --- |
| Clef-flash | 1.30 | 1.87 | 20.2, 27.8, 44.0 |
| Clef | 1.97 | 2.27 | 21.6, 31.5, 44.4 |

**Timing live:** act 1 takes about a minute and act 2 about half a minute. Act 3 makes three calls per step: about 3–4 minutes for 60 meetings, so use replay or Fast for the full set on stage.

**Framing for the audience.**
- Everything is task-conditional and exploratory: one simulated desk, 60 meetings, a stated 70% record, fictional officials.
- Answers are elicited outputs of a trained head, not beliefs.
- The traits shown are shared by both Clef models. This is a passport for a class of decision models, not a contrast between them.

## Robustness test (design, written 6 October 2026 before its data)

**The question.** The first desk favoured the passport lane by construction:
- the world was generated by exactly the model its code assumes (independent speakers, each right 70%);
- the remarks were unambiguous;
- the threshold used the true parameters.

That desk showed that the model aggregates and times badly even when given everything it needs. It did not show that the mitigation works when its assumptions are wrong or its parameters must be learned.

**The robustness desk** (`epistemics.clef.desk2`):
- **Speakers differ.** Ten speakers have true reliabilities from 0.55 to 0.85. These are never stated.
- **Two speakers echo.** Two speakers repeat the previous speaker's direction 80% of the time, whatever the truth. Nobody is told, and the passport lane still adds remarks as independent.
- **Remarks vary.** They are strong (45%), mild (40%) or mixed (15%, e.g. "finely balanced… I'd tilt towards holding").
- **Everything is learned from a scorecard.** Every lane sees the same scorecard from 40 past meetings ("Governor Hale 23 of 25"). The passport lane's weight per speaker is that record, Laplace-smoothed. All thresholds use the optimal policy for the committee's mean estimated record.
- **Scoring** is on 60 held-out meetings.

**Lanes:**
- **alone:** the model's own choice.
- **gated:** its belief at the threshold.
- **recalibrated:** the generic fix, with no passport. The model's beliefs on the 40 past meetings are regressed on the outcomes (logistic, on its belief and the price), and the fitted map is applied to its test beliefs.
- **passport:** classify each remark, weight it by the speaker's estimated record, add, threshold.
- **passport_flat:** the same with one pooled weight.
- **oracle:** the exact posterior under the true reliabilities and echoes; an upper bound.

**Calls.** 1,343 per model: 280 past-meeting beliefs, 840 test choices and beliefs, and 223 classifications.

**Plumbing test** (`tests/test_clef_desk2.py`). A synthetic model with exact beliefs: its gated lane equals the oracle lane.

**Prediction (exploratory):**
- **Passport beats alone**, as on the first desk.
- **Passport against recalibrated is the real question.** If the model's failures are mostly miscalibration, recalibration closes most of the gap. If they are failures of aggregation and timing, which a fixed map of its belief cannot undo, the passport lane stays ahead.
- **Echoes cost the passport lane something** on meetings that contain them, because it double-counts.
- **Mixed remarks** are classified less confidently.

```
uv run python -m epistemics.clef plan --root output/clef-desk2-<date> --design desk2
uv run python -m epistemics.clef run --root output/clef-desk2-<date> --workers 4
uv run python -m epistemics.ledger clef-desk2 output/clef-desk2-<date> --output output/clef-desk2-<date>.json
```

## Robustness test results (6 October 2026)

**The run.** The root is `output/clef-desk2-20261006`: 2,686 of 2,686 calls, no errors, 1.1M input tokens (about $0.26). There are 60 held-out meetings, 29 of them rises. The committee's mean estimated record is 0.70.

**Regenerating the tables.**

```
uv run python -m epistemics.ledger clef-desk2 output/clef-desk2-20261006 --output output/clef-desk2-20261006.json
```

**P&L per meeting** ($k, 90% bootstrap intervals):

| Lane | Clef | Clef-flash | Positions with nothing heard (Clef, flash) |
| --- | --- | --- | --- |
| alone | 38.8 [21.1, 56.8] | 14.3 [−5.8, 34.8] | 33%, 67% |
| gated | 44.8 [26.3, 62.0] | 50.5 [33.3, 65.7] | 33%, 33% |
| recalibrated (generic) | 48.9 [32.7, 64.2] | 55.3 [40.6, 68.7] | 0%, 0% |
| passport | 48.8 [31.4, 63.3] | 52.9 [36.7, 67.0] | 0%, 0% |
| passport, one pooled weight | 51.2 [34.3, 65.4] | 38.0 [20.2, 55.3] | 0%, 0% |
| oracle | 64.0 [50.2, 76.8] | 64.0 [50.6, 76.4] | 0% |

**Paired differences** ($k per meeting):

| | Clef | Clef-flash |
| --- | --- | --- |
| passport − alone | +9.9 [−12.5, 30.5] | +38.6 [14.7, 63.2] |
| passport − recalibrated | −0.2 [−10.7, 10.4] | −2.4 [−14.5, 10.1] |
| recalibrated − alone | +10.1 [−11.5, 30.9] | +41.0 [18.1, 64.3] |
| oracle − passport | +15.2 [2.0, 29.6] | +11.1 [0.1, 24.1] |

**Where the gain comes from** (successive steps):

| Step | Clef | Clef-flash |
| --- | --- | --- |
| alone → gated (take the act-or-wait decision away from the model) | +6.0 | +36.2 |
| gated → recalibrated (calibrate its belief) | +4.1 | +4.8 |
| recalibrated → passport (classify and add instead) | −0.2 | −2.4 |
| passport → oracle | +15.2 | +11.1 |

**Classification.** Strong remarks are classified perfectly, and mixed ones 96–100% correctly. Mild hawkish remarks are often read as ambiguous: mean P(hawkish) is 0.64 and 0.51, with accuracy of 86% and 78% for mild remarks overall.

**Echoes.** No visible cost to the passport lane on meetings with echoes (49 against 49, and 56 against 49).

**Reading (exploratory; 60 meetings, wide intervals):**
1. **The specific claim from the first desk does not survive.** That claim was that classify-then-add beats the model's own aggregation. Here a generic recalibration of the model's own beliefs on 40 past meetings does as well as the passport lane for both models. The first desk's advantage for the passport lane came largely from a world built to match its assumptions.
2. **What survives is jumping to conclusions,** the trait the abstract beads task found. Taking the act-or-wait decision away from Clef-flash is worth +36k per meeting on its own: alone it takes a position with nothing heard in two meetings of three. For Clef the gain is smaller and uncertain.
3. **The mitigation for that trait is simple and generic.** Act on a calibrated probability at a proper threshold. The passport identifies the need (which model, which failure); it does not, on this evidence, supply a better fix than recalibration.
4. **About 11–15k per meeting remains below the oracle.** That gap comes from learned rather than true reliabilities, echoes and ambiguous classification.

**Consequence for the demo.** Act 3 (the first desk) shows that the model fails when handed everything it needs; it does not show a mitigation that beats a generic one. If Act 3 stays, its claim should be "taking the decision away from the model recovers the money", with the recalibrated lane shown beside the passport lane.

## Live demo, Act 3 rebuilt on the confirmation desk (7 October 2026)

Act 3 now trades the meetings of the second preregistered confirmation ([clef-desk4-preregistration.md](clef-desk4-preregistration.md)), not the first desk. The first desk's world matched the passport lane's assumptions and was retired from the demo.

**Step 1: calibration.**
- The model reads the desk's 186 labelled past remarks.
- The panel shows typical mild hawkish remarks that the raw reader gets wrong and calibration fixes (for Clef-flash, 47% → 100%, 22% → 87%, 17% → 70%), with one mixed and one strong.
- It then states the accuracy over all labelled remarks (mild 81% → 99%, mixed 100% → 89%, strong 100%).

**Step 2: the standard fix is fitted.** That is 20 recalibrations, each on ten of the model's own past forecasts.

**Trading.** The first 60, 200 or all 1,000 held-out meetings, in five lanes:
- **alone:** the model chooses when to act. A position taken before anyone speaks is flagged "(no one spoke)".
- **gated:** its belief at the optimal threshold.
- **recalibrated:** the share of the 20 fits that have decided, with P&L averaged over the fits.
- **passport:** calibrated reading, evidence added with each speaker's record, threshold. Each remark shows its calibrated and raw reading and the speaker's record.
- **oracle.**

The page also shows the preregistered 1,000-meeting result for the chosen model.

**Fidelity.**
- **Replay against the ledger.** Replaying all 1,000 meetings reproduces the preregistered lane means exactly for both models (`tests/test_clef_demo.py`). The lane logic and the ledger share `calibration_map`, `calibrate`, `recal_subsets` and `recal_weights`; the ledger output was byte-identical after the refactor.
- **Live against replay.** A live run of three meetings, with its setup (calibration and recalibration, about 800 calls, 85 seconds), produced an event stream identical to replay.

**On stage.**
- Use replay.
- 60 meetings at 1× takes about 80 seconds; all 1,000 at Max about 2 minutes.
- In the first 60 meetings for Clef-flash, the gated lane is slightly ahead of the passport lane. Over all 1,000 they tie (+0.8), and both are far ahead of the model alone and the standard fix. Say so: the confirmed claims are passport > alone and passport > the standard fix with little history.

