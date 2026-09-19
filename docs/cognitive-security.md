# Cognitive security and targeted support

## Purpose



The product loop is **evaluate → model → select support → test → record what helps**. An interpretable profile is useful both for deciding how to work with someone and for choosing how to support them.

The [local draft passport](passport-v1.md) now includes an untested evidence-ledger candidate under one explicit interpretation rule. The intervention runner, learned selection policy, human evaluation interface and intervention-effect estimator remain proposed.

## From behavior to an intervention hypothesis

A descriptive model can suggest interventions; its fit alone does not establish their effects. Separate the observed pattern, plausible mechanism, proposed support and measured response to that support. Multiple mechanisms can explain the same behavior, and the same intervention may help across multiple mechanisms.

For example, “updates too slowly” needs a reference. In a disclosed task, compare responses with the stated evidence model. In discovery tasks, use predictive outcomes, stated decision objectives and comparisons across plausible models. Account for source reliability, dependency, environmental change and resource costs. Faster updating is not an improvement by itself.

Candidate supports below are hypotheses to test, not established remedies for the current agents or for humans:

| Observed pattern under specified conditions | Mechanism to distinguish | Candidate support | Success and tradeoff checks |
| --- | --- | --- | --- |
| Too little response to strong independent evidence | Evidence is overlooked or integration is difficult, versus justified source distrust | An evidence ledger separating prior, new observations, source reliability and dependencies; an explicit reassessment step | Better held-out forecasts or decisions, while preserving restraint for weak evidence |
| Repeated coverage increases confidence without new information | Copies are treated as independent corroboration | Group documents by origin and surface a provenance map | Reduced response to duplicate coverage while retaining response to independent corroboration |
| Source prestige dominates a contradictory track record | Label-based source impressions persist despite demonstrated accuracy | Present comparable track records alongside source labels | Improved evidence use across both prestigious and unfamiliar sources |
| Bad news has disproportionate influence in matched cases | Valence weighting, wording effects or a different inferred causal model | A structured comparison of favorable and unfavorable evidence with equalized diagnosticity | Better performance across evidence directions, without concealing real downside information |
| Expressed certainty exceeds demonstrated accuracy | Poor uncertainty reporting or overconfident inference | Calibration feedback and a reference-class comparison | Better proper scores or interval coverage/sharpness on new cases; report cost and completion changes |

## What to estimate

Let `D` be observed responses, `c` the task/configuration context, `a` a candidate intervention and `theta` the fitted behavioral parameters. The baseline model estimates `p(theta | D, c)`. An intervention model would additionally estimate `p(response | evidence, c, theta, do(a))` from intervention data. Baseline parameter recovery does not supply that causal relationship.

For a declared task loss `L`, define the intervention benefit:

`B(a, c) = E[L(response, outcome) | do(a = none), c] - E[L(response, outcome) | do(a), c]`.

Positive benefit means lower expected loss under the tested conditions. Measure assistance cost separately or combine it using a declared conversion to the same utility units. A later selector can use `expected benefit - cost`, parameter uncertainty and compatibility with the current context; doing nothing must remain an available option.

Forecast tasks can use proper scoring rules. Decision tasks need explicit payoffs or decision-maker-endorsed objectives. Agreement with an evaluator's favored conclusion is not the success metric. In less controlled settings, assumptions and uncertainty about outcomes must remain visible.

## A bounded intervention check

1. Fit the baseline on one set of cases. Choose a candidate and success criteria before inspecting its evaluation cases.
2. Compare no assistance, generic assistance and the profile-selected support on fresh, matched cases. This tests whether tailoring adds value beyond offering any extra structure or attention.
3. Balance evidence direction and include cases where changing less is appropriate. Test both ordinary evidence and defined misleading-information conditions, such as copied corroboration or unreliable source claims.
4. For agents, use fresh contexts and record every prompt/tool change. For humans, account for learning, fatigue and order effects; training with carryover cannot be tested by assuming a clean reset.
5. Report performance effects, uncertainty, cost, failures and regressions. Keep held-out cases separate from intervention selection. An improvement under one condition is evidence for that condition, not universal efficacy or proof of a unique mechanism.

A practical first slice is an evidence-ledger intervention for an agent exhibiting weak integration of independent evidence. Compare it with baseline and generic review on fresh scenarios, including weak, strong and duplicated evidence. First establish whether the support helps that configuration. Stronger personalization claims need comparisons with untailored or other supports and further profiles.

## What the passport records

Add a proposed support section alongside the baseline profile:

- **Candidate:** targeted behavior, hypothesized mechanism, intervention version and expected benefit; explicitly untested.
- **Tested response:** comparison conditions, observed effect, uncertainty, task coverage, cost and any deterioration.
- **Deployment scope:** compatible configurations and contexts, whether the support was active during evaluation, and retest conditions.

An assisted agent is a distinct evaluated configuration. A score obtained with an evidence tool or review prompt must not silently replace its unassisted score. For humans, distinguish performance with assistance, learning retained after assistance is removed, and ordinary repeated-task improvement.

## Control and disclosure

Select support against explicit objectives chosen by the decision maker or authorized operator. Make its operation inspectable, adjustable and reversible. Preserve relevant evidence and access to alternatives. This gives cognitive security a concrete product criterion: better evidence use and resilience while retaining control of the decision.

Detailed vulnerability profiles and intervention histories should have controlled access. For humans, participation and identity-linked sharing require consent, with private use available. A public passport can carry an authorized summary; detailed records and any personal identifiers remain off-chain under an explicit access policy. Do not automatically anchor a human profile or a publicly identifying digest: revoking off-chain access does not erase a ledger commitment.

The agent passport's existing independent-issuer semantics do not automatically define a human identity system. Solana provenance can authenticate a published intervention result; it does not establish that the intervention works or authorize access to private behavioral data.

## Research inspiration

Lieder, Chen, Krueger and Griffiths (2019), [Cognitive prostheses for goal achievement](https://www.nature.com/articles/s41562-019-0672-9), developed decision support by restructuring sequential choices around longer-term goals. This provides a precedent for building assistance around a computational account of a decision problem. It does not validate our proposed supports, individualized selection, or transfer to agents.

Lieder and colleagues, [A cognitive tutor for helping people overcome present bias](https://cocosci.princeton.edu/papers/liedera.pdf), tested planning feedback and transfer in controlled human tasks. It motivates measuring response to support and retention separately. Our passport and proposed interventions are original designs, not replications of either instrument.
