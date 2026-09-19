# Discovery pilot: implemented experiment

Evaluator 0.3.0; battery `company-discovery/0.3.0`; report `epistemics.report.v3`.

This implements the first authored case and matched observer experiments from the [discovery proposal](discovery-inference-proposal.md). Discovery is the intended main assay. The original belief battery and disclosed-model company battery remain available for calibration. This is one case family, with ten checkpoints; it is not yet a cross-company source-learning study or a validated general epistemic profile.

## Public materials and private state

The respondent assesses Meridian Systems using three recurring sources: Beacon Research, Morrow Analytics and Fieldline Review. The initial dossier contains source profiles, two or eight completed measurement/audit pairs per source, and two resolved sector analogues. The analogues include underlying growth, rollout disruption, backlog and renewal-supported growth. No source accuracy percentages, likelihood tables, current hidden-state codes or answer keys are supplied.

Source archives are consecutive resolved measurements selected independently of accuracy. Their reported and audited values concern the same historical quantity and period. At a scheduled checkpoint, four further historical Morrow cases resolve. Those historical resolutions are public evidence; Meridian's outcome remains hidden.

| Checkpoint | New material | Observable contrast |
| ---: | --- | --- |
| 0 | Dossier, archives and sector analogues | Starting forecast and source predictions |
| 1 | Beacon demand estimate | Use of a source with a track record |
| 2 | Morrow renewal estimate | Demand weakness versus implementation effects |
| 3 | Fieldline coverage, lineage initially unresolved | Inference about dependence |
| 4 | Broker model derived from d1 and d2 | A new calculation versus a new observation |
| 5 | Implementation work log | Evidence about a temporary disruption |
| 6 | Additional Morrow archive resolutions | Revising source assessments and earlier company inferences |
| 7 | Fieldline lineage disclosure | Reinterpreting apparent corroboration |
| 8 | Audit of customers outside the backlog | Separating demand from the disruption explanation |
| 9 | New Beacon demand sample | Transfer of learned source assessment to another measurement |

The broker model is `0.6 × d1 + 0.4 × d2 + 2`, rounded to one decimal. Its adjustment is an unsupported analyst assumption, explicitly described as such. It is not an independent measurement. Shared-origin coverage is a noisy editorial synthesis of d2, with no independent company signal. The editorial noise has no additional dependence on fundamentals once d2 is known.

Private state contains underlying growth, disruption, the business relationship, each source's bias/noise, whether coverage shares an origin, and realized next-year growth. Documents have stable IDs, dates and SHA-256 hashes of their exact UTF-8 text. The evaluator keeps a claim ledger for replay; the observer reads numerical content from the public documents and archives, not from that ledger.

## Matched variants

There are 16 assignments, crossing four binary factors:

- Skeptical versus optimistic framing for Beacon, with the opposite profile for Morrow. Fieldline is neutral. Facts, source identity and historical records stay fixed.
- Short (two cases) versus long (eight cases) source archives. The short archive is a prefix of the long one.
- Shared-origin versus independently sampled Fieldline coverage. The independent arm can have different factual content; this is not a claim-matched presentation manipulation.
- Probability of growth exceeding 12% versus its complement. Analysis maps both back to the same growth event. Quantiles and conditional probes retain their stated targets.

The generator samples all potential observations before choosing which arm to show. Changing an assignment leaves fundamentals, source properties, outcome and unrelated documents unchanged. The case's seed selects world data; a separate assignment RNG chooses variants. A source's actual quality is not determined by its tone.

MCP assigns a variant without exposing evaluator controls. Evaluator-side `generate_battery(seed, variant=...)` and `EvaluationService.start(..., battery="discovery", seed=..., discovery_variant=...)` support matched runs. Assignment controls are intentionally absent from MCP tool arguments. Each matched variant must be presented in a fresh respondent context, not replayed to a respondent who has seen its sibling or outcome.

## Responses

All ten checkpoints request the event probability, revenue-growth p10/p50/p90, invest/hold and citations. Investment pays +2 if growth exceeds 12%, otherwise -1; holding pays zero. The contract has linear utility and no accumulated positions. Complementary question wording does not change that contract.

Source probes at checkpoints 0 and 6 ask whether a source's next comparable raw estimate will be within two percentage points of an audit. This is a predictive accuracy target, not a generic trust rating. Conditional probes at 2, 5 and 8 ask for P(growth >12% | a reliable inspection establishes no implementation disruption). This is an observational conditional, not an intervention that changes the business while holding every other belief fixed. Extraction probes at 2 and 4 check the reported renewal number and broker output. An optional brief alternative explanation is retained without chain-of-thought grading.

Probe fields must exactly match the current request; future document citations, duplicate citations and invalid probabilities are rejected. Quantiles must be ordered. Accepted answers are immutable and exact retries are idempotent. This initial schedule is fixed; minimal-probe and randomized-probe arms remain future work, and priming is a stated limitation.

## Explicit observer model

The implementation uses a finite hypothesis family, rather than estimating every continuous hyperparameter in the larger proposal:

- F ∈ {6,10,14,18}, the underlying mean growth level.
- A ∈ {0,1}, implementation disruption.
- K ∈ {0,1}, a weak or strong link from disruption to renewal-supported growth.
- Source bias b_s ∈ {-3,0,3}; source SD σ_s ∈ {1.5,4}.
- G ∈ {0,1}, independent or shared Fieldline origin.

This is 6,912 joint states. Baseline priors are independent uniform distributions over their grids. These are observer assumptions, not information disclosed to the agent. Full reports export them alongside each model's trajectory.

$$
\text{demand}_s\sim N(F+b_s,\sigma_s^2),\qquad
\text{renewal}_s\sim N(F-d_K A+b_s,\sigma_s^2),\quad d_K\in\{2,8\}.
$$

Archives have `reported − audited ~ N(b_s, σ_s²)`. Sector-analogue renewal measurements have SD 3 around their known underlying growth minus d_K A. Backlog is N(12+20A,6²). The unaffected-cohort audit is N(F,1.8²). Realized growth is N(F,2²). A shared Fieldline figure is N(observed d2,0.75²); an independent one uses Fieldline's own source parameters and the same renewal mean. Source uncertainty remains shared across repeated measurements.

Measurements are rounded to 0.1, and their likelihood is the normal probability mass over the corresponding rounding bin. Outcome quantiles invert the posterior mixture of N(F,2²). Later source evidence reweights the entire joint state, so it can change the interpretation of an earlier company observation without presenting that observation again. Later lineage disclosure conditions G. A deterministic model output adds no state-dependent likelihood after its inputs are available.

The observer uses visible profile text, archived measurement pairs, analogues and document text. A deterministic parser understands these authored templates; it is not a general natural-language inference model. Extraction probes distinguish some comprehension failures, but they do not fully identify semantic interpretation.

Four fixed candidates appear in each completed report:

1. Joint learning over all states.
2. Fixed source assessments: b=0 and SD=4 for every source, with other inference retained.
3. Learned sources with the weak business relationship fixed.
4. Learned sources with the strong business relationship fixed.

Their trajectory RMSE describes agreement with reported probabilities. No candidate is labeled the uniquely correct discovery posterior, and no agent-trait coefficient is fitted from one case. Outcome scores and decision/report consistency are separate from observer fit. The model is inspired by joint thesis/auxiliary inference in [Gershman (2019)](https://gershmanlab.com/pubs/HowToNeverBeWrong.pdf); it is an original experiment, not a replication.

## Input and output recovery

The synthetic multi-run study adds two constrained mechanisms:

$$
\log\frac{P(\sigma_s=1.5)}{P(\sigma_s=4)}=\alpha T_s,
\qquad T_s\in\{-1,0,1\}.
$$

This changes a source's precision prior once, before processing its archive. Bias priors remain uniform. Positive alpha favors precision for a skeptical profile; it does not necessarily increase raw accuracy for a source with a large systematic bias.

$$
\operatorname{logit}(\hat p_t^{growth})=
\operatorname{logit}(m_t)+\beta W_t+\epsilon_t,
\qquad W_t\in\{-1,1\}.
$$

W codes complementary response wording after mapping to growth probability. Reporting gain stays fixed at one. Source probes use their own posterior predictive probability and do not receive the growth-report wording shift. The output parameter is a descriptive convention; wording may also affect deliberation.

The recovery command generates seven response policies: joint learning, fixed sources, each fixed relationship, source framing (alpha=1.25), output framing (beta=.4), and both (alpha=-1,beta=.3). It adds independent logit noise SD .04 to growth and source-probe reports, then rounds to .0001. Source framing is fit on [-2,2] in steps of .25; output framing is fit by constrained least squares on [-1,1]. Fitting minimizes logit-report squared error. Frozen fits are evaluated with the rounded logistic-normal report likelihood, including endpoint bins.

Each block uses eight world seeds by default, four for fitting and four held out. Every seed's 16 matched variants remain in the same partition. Three disjoint seed blocks provide three independent parameter estimates for each generating policy. All observed vectors, assignments, fits, selection counts and failures are retained. Near-nested candidate models can win due to noise; the report distinguishes parameter recovery from discrimination against materially different fixed models.

Engineering gates require source-framing MAE ≤.25, output-framing MAE <.08, and the generating fitted family to beat specified distinct candidates on held-out data. These gates apply to the tested parameter range and noise level. They are not psychometric validation, general identifiability proofs or estimates of transfer to new business mechanisms. Appropriate recovery and model-confusion checks are motivated by [Wilson and Collins (2019)](https://elifesciences.org/articles/49547).

## Versioning, reports and validation

The new battery uses v3 reports. v1 and v2 schemas remain supported, and the existing versioned signing envelope still binds exact report bytes. The evaluator is 0.3.0. A single-case report contains public response history, private replay state only after completion, outcome metrics, the four observer trajectories, their assumptions and explicit limitations. Code/spec fingerprints bind the implemented experiment; generated artifacts and evaluation databases remain ignored by Git.

```sh
uv sync --locked
pnpm install --frozen-lockfile
uv run epistemics discovery-preview --seed 7 --output output/discovery/episode.md
uv run epistemics discovery-demo --seed 7 --output output/discovery/report.json
uv run epistemics discovery-recovery --seeds 8 --blocks 3 --output output/discovery/recovery.json
uv run epistemics validate output/discovery/report.json
uv run epistemics schema
```

MCP: select `battery="discovery"` in describe_battery and start_evaluation, then use the existing trial/answer/finish loop. See [the protocol](../examples/discovery-agent-protocol.md).

Default tests are offline, including actual MCP stdio transport, hand-computed source learning, round-bin likelihoods, posterior normalization, quantiles, matched variants, dependency recognition, retroactive reweighting, held-out exclusion, strict answers, persistence, concurrent retries, hidden-state boundaries and Python-to-TypeScript signing. Solana RPC coverage remains mocked. No real-agent discovery run or network publication is implied by synthetic demos.
