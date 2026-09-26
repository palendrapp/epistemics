# Assigned source verification, version 0.1

This implements Stage A of the [verification-value design](verification-value-v1.md): compare complete fresh-context trajectories under no additional check and always buying a fallible independent customer sample. It measures a specific information purchase before testing whether passport evidence improves check allocation.

## Task and version boundary

`source-verification/0.1.0` uses the unchanged source-world generator, original inference engine and clarified sample definition. It keeps 24 companies and 36 checkpoints: twelve unaudited final forecasts, followed by twelve provisional/final pairs. The first twelve companies are not included in the primary payoff comparison.

Each collection has one policy, declared publicly at the beginning and bound privately before the first answer. For later companies:

- `none`: no extra evidence and zero check cost; a final answer is still required.
- `always`: accurately record five independent random customers, then request the final answer and charge the stated check cost, even if the participant declines to invest.

Accurate recording is fallible about company demand: each customer expands with probability 0.7 under strong demand and 0.3 under weak demand. The participant continues to infer the recurring source processes from public archives and resolved cases. Source audits are unavailable in this experiment.

The public answer has only `probability` and `decision`. The respondent never submits a research choice. The provisional answer is immutable, company demand stays hidden until the final answer, and identical retries return identical feedback. Policies are declared upfront, so an arm contrast includes anticipation and later context effects, not merely a sample's immediate effect. Each policy receives its own complete fresh context; answers are never spliced across runs.

Both interfaces share the same service and public definitions. The human browser remains private and supports the same protocol; synthetic transport checks are not evidence of actual human usability. Long retained histories remain a known reading burden.

## Evidence and interpretation

The private binding records the policy, all twelve assigned actions and prices, exact description, canonical manifest hash, implementation hash and creation time. Every rendered checkpoint is locked before its answer. Export reconstructs the assignment, public presentation, immutable responses, chronology, final feedback and payoff arithmetic.

The original `source-learning-report.v1` is reused only as a private calculation ledger. Its query fields contain **evaluator-injected actions**, and its legacy research-choice wording must not be interpreted as participant preferences. The new `verification-evidence.json` binds the exact canonical report bytes and provides assigned-policy analysis; `verification-report.md` is the readable entry point. Keep report and evidence together. The passport directory bundler refuses verification-bound collections rather than issuing voluntary research metrics. No new intervention claim or metric is added to the passport consumer in this increment.

For each of twelve later companies, analysis records:

- Gross realized payoff: `invest × (resolved_strong − threshold)`.
- Check expenditure and net payoff, including costs when declining.
- Final Brier, provisional-to-final decision changes, and final decision/report agreement.
- False acceptance (investing when demand resolves weak) and missed opportunity (declining when demand resolves strong).

Those error categories are realized outcomes, not proof that a probabilistic decision was irrational. Net payoff is in fictional points, not investment return or buyer dollars. Model diagnostics remain separate from outcome quality.

The primary contrast is always-check minus no-check mean net payoff per later company, reported separately by configuration and world. The predeclared feasibility gate requires a mean gain of at least 0.01 across the two worlds for a configuration and nonnegative gain in both worlds. There are four context/world contrasts, not 96 independent participants. A favorable point estimate is not a general policy validation.

## Validation and bounded execution

Synthetic recovery runs the three original observer families under **both assigned paths**, using off-grid reporting gains and company-correlated noise. Each declared seed has 32 repetitions per family per policy: 192 datasets. The original gates apply separately to each policy: primary-pair accuracy at least 90%, joint gain MAE at most 0.15 and joint later latent RMSE at most five points. The simulator does not establish a language effect or real verification benefit.

Before Stage A, a separate acceptance plan launches one fresh context per policy in one common world. An operator reviews completion and four comprehension answers: who assigned the check, when demand was revealed, sample fallibility, and costs when declining. Acceptance responses are excluded from Stage A analysis.

The Stage A runner then requires that reviewed acceptance and two passed recovery seeds for its exact implementation. It freezes a new plan, snapshots the code and creates **two configurations × two new worlds × two policies = eight contexts**. Configuration aliases remain requested aliases with unverified provider revisions. Ordering is randomized and recorded before collection. Matching uses exact world content, not just company labels.

Bounds: two concurrent sessions, one attempt each, 900 seconds per attempt, 3,600 seconds total, and a 25-million-known-token admission boundary with a three-million-token reserve per admitted run. This is an admission boundary, not a hard streaming token cap. Stop further admission on a failed attempt or exhausted budget; retain all partial work and accounting. Acceptance has a separate 1,800-second and eight-million-known-token bound. Marginal account dollar cost remains unknown.

## Commands

```sh
uv run python -m epistemics.source_verification create \
  --directory output/assigned-check \
  --participant path/to/private-participant.json --policy always
uv run python -m epistemics.source_verification serve \
  --directory output/assigned-check --port 8778
```

MCP: command `uv`, arguments `run python -m epistemics.source_verification.mcp_server`, environment `EPISTEMICS_SOURCE_VERIFICATION` pointing to the collection. Only the five public tools are exposed. Agents should first read `describe_battery` and `get_history`, then alternate `get_trial` and `submit_answer` before `finish_evaluation`.

```sh
uv run python -m epistemics.source_verification validate-synthetic \
  --output output/verification-validation-a.json --seed 20260926 --repetitions 32
uv run python -m epistemics.source_verification validate-synthetic \
  --output output/verification-validation-b.json --seed 20261026 --repetitions 32
uv run python -m epistemics.source_verification.runner output/verification-acceptance \
  --phase acceptance \
  --validation output/verification-validation-a.json \
  --validation output/verification-validation-b.json
```

After completion, record an operator `acceptance-review.json` in that private root, including `plan_sha256`, `passed` and the reviewed comprehension evidence. A mere completed collection is not a comprehension review. Then, if acceptance passes:

```sh
uv run python -m epistemics.source_verification.runner output/verification-stage-a \
  --phase stage-a --acceptance output/verification-acceptance \
  --validation output/verification-validation-a.json \
  --validation output/verification-validation-b.json
```

Every root is new; the runner does not overwrite or automatically retry an attempt. Private plans, seeds, source bundles and execution logs stay outside Git. The comparison adds no registry write, paid endpoint, external reviewer or payment. A later passport-guided policy still needs its own frozen heuristic and new confirmation worlds.

The separately versioned [0.2 cost-aware follow-up](cost-aware-results-2026-09-26.md) is also complete. This document and the 0.1 implementation retain their original contract.
