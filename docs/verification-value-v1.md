# Verification value: bounded next comparison

Design version 0.1, 26 September 2026. This document preserves the original proposal. Stage A is now implemented and has a [frozen precollection plan](verification-stage-a-plan-2026-09-26.md), following [synthetic and engineering validation](source-verification-validation-2026-09-26.md) and reviewed acceptance. The [completed Stage A results](verification-stage-a-results-2026-09-26.md) failed the frozen net-benefit criterion for both configurations. Stage B remains deferred; the next development question is a simple cost-aware policy with offered prices separated from company priors. Its first question is whether purchasing a specific independent evidence check improves decisions after its cost. It does not require a uniquely identified cognitive mechanism. The [source-panel results](source-panel-results-2026-09-26.md) inform the design but are not confirmation data for this new claim.

## The decision and available check

A buyer receives a configured agent's company assessment and decides whether to require a fresh independent customer sample before the final invest/decline decision. The controlled check measures five random customers accurately. Individual expansion still has probability 0.7 under strong demand and 0.3 under weak demand, so even perfect measurement is fallible about company demand. This is an information purchase, not evidence about the reliability of a real human reviewer or commercial verification service.

Use the clarified [0.2 instructions](source-delivery-v2.md). Keep source archives, company priors, investment thresholds and check prices visible. Keep evaluator truth and unpurchased checks hidden. Version the assigned-verification task separately because an evaluator-assigned check replaces the participant's free research choice. Source audits are excluded from this first comparison, avoiding unpriced future benefits from learning a recurring source property.

## Stage A: does the check help?

Proposed allocation: two declared configurations × two **new** source worlds × two assigned policies = **eight complete contexts**. Every context starts fresh; it continues through its companies. Match the worlds across policies and configurations, but collect each complete policy trajectory separately. A check may affect later behavior even when the resolved archive eventually contains the same company outcomes; do not splice unobserved answers from another trajectory.

Policies:

1. **No additional check:** proceed to the final checkpoint with no new evidence and no check cost.
2. **Always check:** supply the independent five-customer sample and charge its declared cost before the final answer.

Use twelve early unaudited forecasts and twelve later companies with assigned verification/final decisions, retaining the existing generator's prior/threshold/price coverage. The research stage becomes a provisional forecast/action; the assigned policy determines the check, without offering a false participant choice. Outcomes appear only after the final answer. Freeze exact wording, assignment order, seeds, configurations and resource bounds before responding.

Primary measurement is the paired difference in **net realized fictional payoff per later company**, including check costs, shown separately for every configuration/world. Secondary measurements are final Brier, decision changes, erroneous acceptance/rejection, check count, input/output usage and latency. The baseline and verification arms must use the same payoff definition and final-decision timing. There are four context/world contrasts; do not bootstrap companies as independent participants.

For a feasibility go/no-go rule, propose at least 0.01 additional fictional points per later company averaged across the two worlds for a configuration, with nonnegative payoff differences in both worlds. This is an explicit development threshold, not a buyer's dollar willingness to pay or a certification criterion. Freeze it before launch; a negative result stays visible. If the threshold is not met, inspect coverage, cost and specific failures before spending on personalization. Passing would justify a bounded follow-up, not a claim of general verification benefit.

## Stage B: does the passport help select checks?

Only after a useful check is demonstrated, compare four policies on **further new worlds**:

- No verification.
- Always verify.
- A simple policy using the current forecast's distance from the investment threshold and the check price, with thresholds fixed on development evidence.
- The same decision inputs augmented with pre-existing passport evidence, such as measured repeat variation and its coverage.

Use the same available verifier and constraints. The sparse repeat difference can inform a declared heuristic; it is not a calibrated standard error for an individual future judgment. Choose the heuristic, uncertainty handling, missing-evidence fallback and decision thresholds before confirmation. Do not choose the policy that wins on the same cases used to report its benefit. Do not use the failed Sol family label as a validated predictor.

Collect each policy's whole trajectory in a fresh context. Report actual verification expenditure as well as same-budget comparisons. A passport-guided policy must improve on the simple policy after evaluation/re-evaluation cost, not merely on doing nothing. Amortize assessment cost over an explicitly declared number of uses. General support benefit and profile-guided allocation are separate claims and may have different outcomes.

## Buyer translation and release

Until a buyer defines loss weights, report false acceptance, missed opportunities, verification cost and latency separately. The fictional payoff supplies a controlled feasibility target; it is not financial advice or investment-return evidence. If a later pilot uses an actual reviewer, measure reviewer errors, dependence on shared sources and service latency rather than treating review as truth.

The [assigned-check collector](source-verification.md), prospective policy locks, synthetic branch/recovery validation and small acceptance are implemented; the frozen Stage A plan records their commitments. Reuse immutable answers, exact evidence binding and the passport adapter. Stop admission after a failed attempt; preserve partial work and accounting. A proposed Stage A ceiling is two concurrent sessions, 900 seconds per attempt, one attempt each, 3,600 seconds total and a 25-million-known-token admission boundary with a three-million-token reserve per incoming run. Account billing cost remains unknown. These limits must be committed with the actual run plan, and can be revised transparently before launch.

No buyer has been contacted and no real verification or payment service has been purchased. Design-partner preparation, owned-identity enrollment and human usability remain parallel tasks. A positive point estimate from this small experiment does not authorize a stable trait, automated authority increase or production policy.
