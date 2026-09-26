# Cost-aware verification, source-verification/0.2.0

This increment tests whether a simple selective check can improve net decision outcomes before attempting passport-based selection. The [earlier blanket-check comparison](verification-stage-a-results-2026-09-26.md) improved Brier but lost net fictional payoff in all four matched contrasts. Its exploratory price groups motivated this follow-up; they do not validate this policy.

The implementation lives in `epistemics.source_selective`. The existing source-learning, delivery, panel and verification 0.1 implementations and their evidence remain unchanged. Both the browser and MCP share the new service. No report-v1 contract, registry, payment or identity semantics change.

## Fixed decision rule

Let `p` be the accepted provisional probability of strong demand, `t` the investment threshold and `c` the offered sample price. Investing earns `1-t` when demand is strong and `-t` otherwise; declining earns zero. Let

\[
f_h(k) = {5\choose k}q_h^k(1-q_h)^{5-k},\quad q_1=0.7,\ q_0=0.3.
\]

The current optimal expected payoff under the reported probability is `max(0,p-t)`. The sample's expected value is

\[
V(p,t)=\sum_{k=0}^{5}\max\{0,\ p f_1(k)(1-t)-(1-p)f_0(k)t\}-\max\{0,p-t\}.
\]

The rule buys exactly when `V(p,t)-c > 1e-12`; ties receive no check. This is the expected value of sample information for this task's payoff, calculated by integrating over every possible result. It does not require the evaluator's current company truth, independent sample, source-process estimate or fitted respondent parameters. The agent's provisional action does not affect the assignment.

For example, at `p=t=0.30`, the five-customer sample has expected value 0.1415064 points under these assumptions. It earns a check at prices 0.01 and 0.04, but not 0.20. At `p=0.99,t=0.30`, its value is zero: none of its possible results changes the payoff-maximizing action.

This is a **myopic benchmark**. It assumes the reported probability is an appropriate decision input, correct Bayesian use of the supplied sample, and a payoff-maximizing final action. It ignores learning value for future companies and possible benefits from reconsideration alone. It does not claim that reports expose internal beliefs, that source inference is correct, or that the respondent actually follows the benchmark. The real whole-trajectory comparison tests whether this rule helps despite those limitations. The declared rule may influence anticipation and reporting; those effects are included, not identified separately.

## Price assignment

A separate private price seed assigns the same twelve offered prices to every policy/configuration/repeat of a world. The price algorithm reads only company IDs, priors and decision thresholds. It does not read demand, source evidence, independent samples, or accepted answers.

Each world offers four samples at each of 0.01, 0.04 and 0.20 points. Every prior (0.20, 0.50, 0.80) receives every price, with one price duplicated. The duplicated price is randomly permuted across priors, and assignment within each prior/threshold stratum is randomized. Each decision threshold (0.30, 0.70) receives two samples at each price. This is a balanced incomplete crossing: twelve companies cannot completely cross three priors, two thresholds and three prices. Chance associations with realized evidence/outcomes can remain. Price is no longer determined by prior as it was in 0.1.

## Evidence and immutability

Before responses, `verification-binding.json` commits the rule, price seed, offers, exact public description, base-manifest hash and new implementation hash. Each public checkpoint is hash-locked before its answer. At a provisional checkpoint the conditional cost is explicitly pending; at the final checkpoint the actual check/no-check branch and charged price are shown.

The derived query is committed atomically with the accepted provisional answer in the canonical ledger. A concurrent retry cannot change the accepted probability or its derived action. Independent evidence appears only at the following checkpoint. Company demand is revealed only after the final answer. Verification reconstructs each derived action from the accepted probability and bound terms and checks presentation, hashes, chronology, resolutions and arithmetic.

The underlying canonical source-learning report retains **legacy prices** to preserve its original validated contract and calculation history. Its old payoff, research-value and research-choice analyses are inapplicable here. Use `verification-evidence.json` and `verification-report.md` with the canonical report for this version's outcomes. The assigned-verification passport guard continues to reject this evidence as voluntary research preferences. Raw evidence is private and excluded from Git. There is no new deployable machine policy or passport claim in this increment.

## Comparison and release boundary

Three policies: no check, always check and cost-aware. Collect complete trajectories in fresh contexts; do not splice selective rows out of always-check outcomes. Each trajectory has twelve initial company forecasts, followed by twelve provisional/final pairs, for 36 checkpoints. The primary outcome concerns only the later twelve companies.

The bounded comparison uses two requested configurations (Astra/Sol, medium), two newly generated worlds, three policies and two fresh context repeats: **24 contexts / 864 checkpoints**. The two worlds are shared across configurations; repeats measure response variability on the same cases and do not increase the number of independent worlds. Four randomized world/repeat blocks each contain every policy for both configurations. Rotations and reversals prevent all always-check runs preceding all no-check runs. Two configurations run concurrently per batch. Provider drift remains possible and aliases do not attest exact model revisions.

For each configuration/world, average the two repeats within each policy before computing contrasts. Weight the two worlds equally. The fixed development gate requires:

- Cost-aware minus none: average net gain at least 0.01 fictional points per later company, with nonnegative repeat-mean gains in both worlds.
- Cost-aware minus always: average net gain at least zero, with nonnegative repeat-mean gains in both worlds.

Report every repeat, the signs of repeat contrasts, within-policy probability differences, net-payoff differences and check-assignment disagreements. Gross payoff, Brier, error categories, decisions, check expenditure, usage and time are secondary. No independent-company bootstrap, population confidence interval or stable cognitive interpretation is licensed by this small comparison.

Before the comparison: two synthetic recovery seeds, each 32 datasets per observer family/policy (576 total), followed by a separate three-context agent acceptance, one per policy. Recovery validates synthetic family/gain inference along the new assigned paths; it does not validate behavioral assumptions or verification benefit. Acceptance checks completion, correct understanding of assignment/outcome timing/sample fallibility/cost, public information boundaries and friction. It is excluded from outcome estimates and admitted on comprehension/engineering, not favorable payoff. Human usability remains untested by agent acceptance.

Bounds are frozen before responses: one attempt per context, 900 seconds per attempt, two concurrent; acceptance 1,800 seconds and 12 million known processed tokens; comparison 7,200 seconds and 40 million. Admission reserves three million tokens per incoming context. This is an admission boundary, not a hard streaming cap. Stop new admission after a failed attempt or exhausted bound; keep partials and usage, with no automatic replacement. Correctable rejected tool submissions within an ongoing context remain recorded separately from accepted answers. Existing-account billing in money is unknown.

A passing development gate warrants a bounded transfer test with more new worlds and realistic reviewer dependence/errors and costs. It does not warrant jumping to personalized allocation. A failed gate warrants retaining the null/negative result and inspecting whether the simple policy, available evidence or decision task creates usable value before expanding the passport model.

## Operator commands

```sh
uv run python -m epistemics.source_selective validate-synthetic --output output/selective-validation-a.json --seed 20260927
uv run python -m epistemics.source_selective validate-synthetic --output output/selective-validation-b.json --seed 20261027
uv run python -m epistemics.source_selective simulate --directory output/selective-demo --seed 57 --policy cost_aware
uv run python -m epistemics.source_selective serve --directory output/selective-demo --port 8779
```

For real collection use the operator-only `epistemics.source_selective.runner`: `prepare(...)` saves the plan/code snapshot and creates bound empty collections; `run(...)` executes that exact plan. Save the public plan commitment before launching comparison respondents. The MCP exposes only describe, history, current checkpoint, answer and finish. The human browser uses the same rule, costs, immutable answers and private loopback authentication.
