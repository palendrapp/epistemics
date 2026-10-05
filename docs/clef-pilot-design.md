# Clef pilot: Bayesian dispositions of a decision model (design)

Written 5 October 2026. Status: built with the recommended defaults (see [Built](#built-5-october-2026)); nothing collected yet.

## Why Clef

Clef is Cloudflare's open-weight decision model (Apache 2.0), released on 1 October 2026.
- **Sizes.** Clef has a 27B backbone; Clef-flash has 9B.
- **Training.** Both are post-trained from Qwen3.8.
- **Input.** A call takes a *state* (text or JSON, optionally images) and 1–64 typed questions:
  - `noul`: yes or no;
  - `choice`: named options;
  - `score`: an ordered rubric of up to 10 levels.
- **Output.** A prefill-only pass and a joint schema head score every allowed answer to every question. A softmax per question turns the scores into probabilities, and no text is generated.
- **Claims and reported weaknesses.**
  - Cloudflare says the training rewards "correct answers and well-calibrated probabilities", on synthetic data that shuffles field orders, prompts and schemas. No calibration figures are published.
  - Coverage of the launch lists, as stated weaknesses, weaker reasoning-benchmark results than the competitor Jev (BBH, GPQA) and answers near 0.5 for vague questions.

**Three properties matter for this paradigm:**
1. **Readout.** The probability is a softmax over the allowed answers, not a number the model writes. The verbal readout layer is absent: round numbers, session modes, and the wording a number is given. We have spent the last week separating that layer from judgement.
2. **Determinism and cost.**
   - No sampling and no session.
   - Reported median latency is about 0.2 s for Clef; Clef-flash answers in tens of milliseconds.
   - A Clef call on one of our cases is a few hundred input tokens. A Codex session on the hinted dossiers used a median of 0.56 million input tokens (adapter-hinted roots).
3. **Joint questions on one state.** A base rate, a per-case structure probe and a forecast can be asked about the same case in one call. Whether the forecast applies the stated base rate can then be checked within a single state, with no session history or question order to explain it away.

Clef is pitched as the step in an agent pipeline that acts on its answer directly: routing a ticket, blocking a request or escalating to a human. That makes its dispositions consequential, and a passport for a decision model is a product in its own right.

## Questions

| | Question | Materials (per model) | Measure |
| --- | --- | --- | --- |
| **Q1** | Does Clef's probability match the correct posterior when the documents settle the structure? | `relay-evident`, `disclosure-evident`: 48 cases | Absolute log-odds error against the exact posterior, by case type; fitted structure use and false structure (`dispositions.evident.session`) |
| **Q2** | Does Clef neglect structures that are only hinted, and does stating the mechanism change its answers? | `relay-hinted`, `disclosure-hinted`, variants `alone` and `reference`: 96 cases | Implied relay and selective-disclosure priors per description (the agents' slot fits); the distance between alone and reference answers, as in the adapter evaluation |
| **Q3** | Does Clef apply the base rates it states? | Across cases: `corroboration-cues`, `disclosure-cues`, variant `cues-a`, 48 cases. Within state: the 60 described forecast cases of Q2's alone arm and Q3 | Across cases: the passport's stated–applied gap. Within state: forecast and probe against the observer given Clef's own base rate from the same call |
| **Q4** (method) | Is the elicitation stable? | Subsets of the above | Repeat calls; one question alone against within a joint call; question order; paraphrase |

**Comparison.** Astra, Sol, Luna and Terra have already answered the same cases:
- **Evident:** the adapter pilot's `alone` arm.
- **Hinted:** the adapter-hinted `alone` and `reference` arms.
- **Cues:** `cues-a`, markets, in the finance-transfer collection.

The agents answered whole modules within sessions, under instructions; Clef answers each case statelessly. The comparison is of dispositions on identical cases, not of identical procedures.

## Elicitation (fixed before any call)

**State.** The state is the rendered case text the agents saw (`render(module, "markets", i, variant)["case"]`): the case brief and documents, or the description and mechanism for a rate case. The agents' general instructions are not included.

**Probability questions** ("What is the probability that P?") become `noul` questions with the instructions "Is it true that P?", using the clause verbatim. The answer is Clef's probability of true. This covers:
- forecasts ("…that Fenwick Dairy's demand is high");
- structure probes:
  - "…that B relayed A's call rather than checking for itself";
  - "…that the company is the kind that withholds every off-target indicator".

**Base-rate questions** ("Among outlets like B, what proportion relay…?") become `choice` questions over 21 options, 0%, 5%, …, 100% (keys `p00` to `p100`). The estimate is the probability-weighted mean. The modal option is reported alongside it.

**Within-state joint calls (Q3).** These run on each described forecast case: 20 relay-hinted pairs, 20 disclosure-hinted forecasts, 10 corroboration-cues pairs and 10 disclosure-cues forecasts. A joint call asks three questions on the case's state:
- the forecast;
- the structure probe for this case's source, built from the module's probe template;
- the base rate for sources like it, built from the module's rate template.

**Question order.** Base rate, then probe, then forecast. Each joint call is repeated once in reverse order (a Q4 check).

**Models.** `@cf/cloudflare/clef` and `@cf/cloudflare/clef-flash`, treated as two configurations.

**Method checks (Q4):**

| Check | Cases | Read |
| --- | --- | --- |
| Repeat identical calls | 24 (12 from each of Q1's modules), each called three times | Maximum absolute difference in probability. Below 0.001 counts as deterministic |
| Alone against joint | The 60 within-state cases: the forecast from Q2 or Q3's single call against the joint call's | Mean absolute log-odds difference. It decides whether joint answers can stand for single ones |
| Question order | The 60 joint calls in both orders | Mean absolute log-odds difference per question |
| Paraphrase | 24 forecast cases (Q1): "Is it true that X's demand is high?" against "Is X's demand high?" | Mean absolute log-odds difference |

**Volume per model:**
- 192 single-question calls (Q1 48, Q2 96, Q3 48);
- 120 joint calls (60 cases in two orders);
- 72 check calls (48 repeats, 24 paraphrases);
- 384 calls in all, so 768 for both models.

States average 600–850 characters. The whole pilot is therefore well under half a million input tokens: about $0.10 at the listed $0.24 per million.

## Analysis (`ledger/clef.py`)

Every quantity reuses the function that computed it for the agents, applied to Clef's probabilities.

**Q1.**
- Error against the exact posterior by case type (present, absent, control).
- Structure use and false structure (`dispositions.evident.session`).
- A reliability table: Clef's probability against the exact posterior in bins. These cases have exact answers, so calibration is read against the correct posterior, not against simulated outcomes.

**Q2.**
- Implied structure priors per description level, alone and with the mechanism stated.
- The mean absolute log-odds distance of alone answers from reference answers on described cases. This is the deviation measure of `adapter_eval.hinted_summary`; Clef is deterministic, so it has no session noise floor.
- Both are set beside each agent configuration's.

**Q3, across cases.** The passport's stated–applied gap: the mean over description levels 1–3 of |stated base rate − implied rate from forecasts| (`finance_transfer._gap`).

**Q3, within state.** Let r be Clef's base-rate answer in a joint call. Two gaps are computed:
- **Forecast gap:** |logit(forecast) − logit(observer forecast with structure prior r)|. The observer is `observers.corroboration` or `observers.disclosure`.
- **Probe gap:** |logit(probe) − logit(observer structure posterior with base rate r)|, using `observers.structure_posterior`.

Both use the case's stated prior, likelihoods and reports at face value. They are new measures: they ask whether one answer applies another answer given in the same call.

**Q4.** The stability table above. If the repeat check fails, every other result is reported with its repeat spread.

All outputs are elicited answers from a trained head. They are not read as direct access to the model's internal beliefs.

## Implementation

All of this lives outside the task package, so the tasks fingerprint and validation are untouched.

**`epistemics.clef.client`.** Workers AI REST: `POST https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/cloudflare/{model}`.
- Credentials come from the environment (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`). They are never logged, stored or written into a record.
- Timeouts, with bounded retries on transient errors.

**`epistemics.clef.requests`.** Deterministic builders from `render` and `items_for`, following the elicitation above. Each request body is hashed.

**`epistemics.clef.pilot`.**
- **Frozen plan.** A plan of every call (model, module, variant, case, kind, question order) is written with its request digests before any call: `output/clef-pilot-<date>/plan.json`.
- **Records.** Each call's request digest, raw response, latency and token usage go in `calls.jsonl`.
- **Resumable.** Calls already answered are skipped, so a rerun resumes; no record is overwritten.

**Ledger.**
- A registry entry, and `uv run python -m epistemics.ledger clef-pilot <root>`.
- Clef and Clef-flash enter the passport only after the pilot, and only if the method checks pass.

**Tests.** Offline and mocked, covering:
- request building from cases;
- the question transformations;
- parsing of the three answer types from recorded response shapes;
- the analysis on synthetic answers.

Live coverage is reported separately from the mocked tests.

**First live step.** A smoke test of one call per question type per model, to confirm the response field names before the plan is frozen. The documentation names them as follows:
- `noul`: the probability of true;
- `choice`: `choice`, `confidence` and `probabilities`;
- `score`: `score`, `confidence`, `legend` and `probabilities`.

The parser follows the shape actually returned.

## Access

- **Workers AI (recommended).** It needs a Cloudflare account with Workers AI and an API token with the Workers AI permission. You create the token and export the two variables in the shell that runs the pilot. I do not handle it.
- **Local weights: not feasible on this Mac.** The released inference code loads the model on CUDA, and was tested on a single H200. A rented GPU is the alternative if Workers AI is unsuitable. Downloading the weights (27B in BF16) would need your go-ahead.

## What each outcome means

**Near the exact posterior on Q1 and coherent on Q3.** Clef applies stated likelihoods and its own base rates without a reasoning trace, and its passport centres on structure handling (Q2).

**Neglect of hinted structures on Q2, as the agents show.** The neglect does not depend on verbal readout or session state. It would belong in a decision-model passport, with stating the mechanism as the remedy if the reference arm moves the answers.

**Far from the exact posterior on Q1.** This fits a model that cannot compute step by step, and fits the regime account of Chen et al. 2026: models look Bayesian with explicit likelihoods only when they can compute. It also fits the reported weakness on reasoning benchmarks. It is reported as a property of this decision model on these tasks.

**Answers near 0.5 on hinted cases.** This matches the reported behaviour on vague questions. It is read against the reference arm before it is called neglect.

**Unstable on Q4.** The pilot stops at method, and no disposition is reported until the instability is understood.

## Decisions

1. **Access:** Workers AI with your token (recommended), or a rented GPU.
2. **Models:** both Clef and Clef-flash (recommended), or Clef only.
3. **Adapter arm.** Passport-adapter guidance appended to the question instructions, in this pilot or after it. Recommended after: the pilot should first show whether Clef's instructions field moves its answers at all.

## Built (5 October 2026)

The recommended defaults are Workers AI, both models, and no adapter arm.

**Package `epistemics.clef`** (pilot version clef-pilot/0.1.0). It sits outside the task package, so no tasks version, fingerprint or validation changes.
- **`requests`** builds every request body from `render` and `items_for`.
  - 768 calls: 384 per model.
  - Per model: q1 48, q2 96, q3 48, joint 120, repeat 48, paraphrase 24.
  - The probe and base-rate wording of the joint calls is the cue modules' own; a test checks it against their rendered probe and rate items.
- **`client`**:
  - Workers AI REST over the standard library.
  - Credentials only from `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN`, and scrubbed from every error message.
  - Up to five attempts on transient HTTP errors.
- **`answers`** parses the probability of true for noul questions, and the 21 option probabilities for base rates (mean and mode). The documented field names are loose, so it accepts the plausible shapes and fails loudly otherwise. Raw responses are always kept, so a parser fix never needs a new call.
- **`pilot`**:
  - `plan` freezes `plan.json` (call metadata, request digests, a digest of each module's items) and `requests.jsonl` (the bodies), and never rewrites them.
  - `run` checks each frozen body against its digest, sends only unanswered calls, and appends records to `calls.jsonl` (failures to `errors.jsonl`). It stops after five consecutive failures.
  - `smoke` sends one call per question type per model.

**Commands** (the live ones need the two environment variables in your shell):

```
uv run python -m epistemics.clef smoke --out output/clef-smoke-<date>
uv run python -m epistemics.clef plan --root output/clef-pilot-<date>
uv run python -m epistemics.clef run --root output/clef-pilot-<date>
uv run python -m epistemics.ledger clef-pilot output/clef-pilot-<date> \
    --evident-roots output/adapter-pilot-20261005 \
    --hinted-roots output/adapter-hinted-20261005-* \
    --cues-roots output/finance-transfer-20261004 output/finance-transfer-20261004-b output/finance-transfer-20261004-c --output output/clef-pilot-<date>.json
```

**Analysis (`ledger/clef.py`).**
- **Agent comparison.** The agents' values come from their roots, using the same functions as before:
  - evident and hinted alone arms: `adapter_eval`;
  - cues-a gap: `finance_transfer._gap` per session.
- **Rotated baseline (within-state).** The same gaps are also computed with each case's base rate taken from another case of the module, averaged over every rotation. A forecast that applies its own stated base rate should sit well below this case-blind baseline.
- **Rounding for the cue fit.** The fit's report likelihood is censored at whole percentages, the agents' resolution, so Clef's answers enter it rounded to whole percentages. Every other measure uses them unrounded.
- **Hinted joint calls.** Their questions name the mechanism (the probe asks whether the outlet relayed the call). On hinted cases the joint call is therefore an asked condition, and alone against joint there measures the effect of naming, not method noise. The cue cases already describe the mechanism, so there it is a pure method check. The analysis reports the two separately.

**Tests (`tests/test_clef.py`, offline).**
- **Client:** a mocked opener, covering the retries and that credentials never reach an error message.
- **Pilot and analysis:** a synthetic responder, an exact Bayesian observer standing in for Clef. On it the analysis gives:
  - error near 0 on Q1, structure use 1, false structure 0;
  - implied priors equal to the responder's (0.20–0.80);
  - stated–applied gap near 0;
  - within-state gaps of 0, against rotated baselines of 0.4–1.2 log-odds;
  - deterministic repeats.
- **What this covers.** It is parameter recovery for the measures; it is not evidence about Clef. Live coverage begins with the smoke test.

**Next.**
1. You export the two variables.
2. Smoke test, one call per question type per model, to confirm the response shape.
3. Freeze the plan.
4. Run, about 768 calls.
5. Analysis.

## Sources

Read through an automated summarizer on 5 October 2026; numbers to be rechecked before reuse:
- [Clef on Hugging Face](https://huggingface.co/Cloudflare/clef): model card, architecture, the Decision Index median latency (209 ms), local inference requirements.
- [Workers AI model page](https://developers.cloudflare.com/workers-ai/models/clef/): request and response schema, context window, price.
- [Workers AI changelog, 1 October 2026](https://developers.cloudflare.com/changelog/post/2026-10-01-clef-workers-ai/): release and sizes. The backbone and Clef-flash's latency come from search summaries of this announcement.
- [flaviocopes.com](https://flaviocopes.com/clef/): mechanism, training data and calibration objective, and stated weaknesses (reasoning benchmarks against Jev, vague questions).
- [The Decoder](https://the-decoder.com/cloudflare-says-its-new-clef-model-means-humans-no-longer-need-to-be-in-the-loop-for-ai-agents/): the "no human in the loop" framing; no calibration figures.
- Papers: [reading list](reading-list.md), "Decision models (5 October)".
