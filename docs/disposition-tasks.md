# Disposition tasks: T2, T3 and T5 as checkpoints

Build record, 27 September 2026. This is step 2 of the [generative model](epistemic-generative-model.md#8-development-sequence). The package `epistemics.disposition_tasks` (disposition-tasks/0.1.0) renders the [recovery-validated designs](disposition-recovery-2026-09-27.md) as fictional text cases and collects them through the existing compact MCP pattern. No agent has answered them yet.

## What a respondent sees

Each fresh context answers one module's 24 cases, one call per checkpoint:
- **T2 and T3:** 18 forecasts and 6 structure probes, each answered with a probability in whole percentages.
- **T5:** 24 checks, each answered with a maximum price in whole points.

Every case states:
- the prior and the source reliabilities;
- how relays or random omissions work;
- the wording cue's rates;
- the payoffs and the posteriors after each check result.

What is never stated is the quantity being measured: how common relays are, how many senders are selective, and what certainty is worth.

**The protocol.** It says that not every quantity is stated and that respondents should use their own judgment and still answer. That wording is identical for every respondent. The T5 protocol describes a random-price mechanism, which makes stating your true maximum the best strategy. No outcomes, prices or check results are revealed. Module, parameter and model names never appear in public output, and the validation audits for them.

**Two cover stories** share identical structure and numbers:
- **Markets:** company demand, news outlets, company indicator updates and a market check.
- **Ecology:** a lake's fish stock, monitoring stations, a survey contractor's markers and a laboratory test.

Names are fixed by item. A repeat with the same cover therefore shows identical text in a new evaluator-chosen order, while the other cover changes every surface detail.

Example cases (markets). The full sets print with `uv run python -m epistemics.disposition_tasks sample --module <corroboration|disclosure|checks> --cover <markets|ecology>`.

> **T2.** Fernhill Robotics' quarterly demand is either high or low. Before any reports, the probability that demand is high is 50%. Lantern Review reports that demand is low. Lantern Review's demand calls are correct 65% of the time. Fairhaven Dispatch also reports on Fernhill Robotics: it says demand is high. When Fairhaven Dispatch checks for itself, its calls are correct 80% of the time. Some outlets relay another outlet's call instead of checking for themselves; a relayed call simply repeats the original call. Fairhaven Dispatch may have checked for itself or relayed Lantern Review's call. Relayed stories reuse the original story's wording 80% of the time; stories by outlets that checked for themselves match another outlet's wording 20% of the time. Fairhaven Dispatch's story uses different wording from Lantern Review's.
> *What is the probability that Fernhill Robotics' demand is high?*

> **T3.** Oakhurst Glass' quarterly demand is either high or low. Before its update, the probability that demand is high is 50%. Oakhurst Glass tracks 4 operating indicators. When demand is high, each indicator independently lands on target with probability 75%; when demand is low, with probability 25%. Some companies share every on-target indicator and withhold every off-target one. Others leave indicators out of their updates at random: each indicator is left out with probability 50%, whether or not it was on target. Oakhurst Glass could be either kind. Oakhurst Glass' update reports 2 indicators on target and 1 off target, and does not mention the other 1.
> *What is the probability that Oakhurst Glass' demand is high?*

> **T5.** You are deciding whether to invest in Cobalt Foods. Investing gains 30 points if its demand is high and loses 70 points if demand is low; not investing scores 0 points. Take the probability that demand is high to be 54%. A market check is available. It comes back positive with probability 50%. If it is positive, the probability that demand is high becomes 68%; if it is negative, it becomes 40%. If you buy the check, you decide after seeing its result; otherwise you decide now.
> *What is the most you would pay for this check, in whole points?*

These three are diagnostic items:
- **T2:** a conflicting pair, so a relay is impossible and the prior on relaying should not matter.
- **T3:** one off-target indicator was shared, so the sender cannot be selective and the omission should not matter.
- **T5:** no check result can change the decision, so any price above zero reflects value placed on certainty.

## Changes made while rendering

- **T5 items adjusted.** Stating the chance of a positive result exposed 14 T5 items whose implied chance was not a whole percentage. Those items were adjusted by one to five points, each kept its group, and the recovery study was rerun with both seeds passing (recorded in the [recovery study](disposition-recovery-2026-09-27.md)).
- **Rival models on forecasts only.** The rivals make no predictions for structure probes, so per-context model comparison uses the 18 forecasts, while the disposition estimate uses all 24 checkpoints.

## Collection and analysis

The service follows the [0.3 dossier collection](research-world-design.md#12-register-versus-validity-research-world030-27-september):
- **Frozen manifest:** it binds the implementation fingerprint, which covers both the tasks and the model packages, the case order, and the bytes of every rendered case.
- **Locks before answers:** each checkpoint is locked before its answer.
- **Answers:** immutable, with idempotent retries and transactional state.
- **Adapter:** a five-tool stdio MCP adapter.
- **Report:** a reconstructed, re-verifiable report.

Each context's analysis gives:
- **T2 and T3:** the disposition, γ, bias and report noise, with 90% intervals, and the model comparison against the heuristic rival.
- **T5:** fits under both certainty functions, the selected function, and mean prices for decision-relevant and zero-decision-value checks.

No browser interface was built, because human collection is paused.

## Validation

The pipeline validation is bound to the fingerprint. It audits all 144 rendered cases, for displayed probabilities, distinct subjects and absence of private labels. It then drives 18 synthetic contexts through the service: every module and cover with three known respondents each. Both seeds passed:
- **T2 and T3:** dispositions were recovered within 0.01.
- **T5:** values of certainty were recovered within 8 points of 0, 50 and 100.

At a value of certainty of zero, the choice between certainty functions is arbitrary, as expected.

The runner's plan preparation was dry-run against these validations: it produced 18 frozen runs and made no model calls. The test suite covers:
- rendering;
- answer types;
- ordering, locks and immutability;
- tamper rejection;
- a full stdio MCP collection;
- synthetic recovery through the service;
- plan freezing.

## Proposed agent acceptance

Run on 27 September; see the [acceptance record](disposition-acceptance-2026-09-27.md). It uses the existing ChatGPT subscription through the Codex CLI.

| Setting | Proposal |
| --- | --- |
| Configurations | GPT-6 Astra and Sol, medium effort |
| Modules | T2, T3, T5 |
| Contexts per module | markets twice (retest), ecology once (cover dependence) |
| Runs | 18 fresh contexts of 24 checkpoints |
| Token cap | 20 million known processed tokens (the default of 10 million would stop admission early) |

Per context, expect roughly 0.5–1 million input tokens, mostly cached, by analogy with the compact acceptance's one million for 36 checkpoints. Weaker configurations follow if the tasks work.

**Engineering criteria:** every context completes with no tool errors, every answer has the requested type, and completion answers show the protocol was understood.

**Scientific readouts,** all descriptive at this size:
- whether respondents commit to probabilities when the base rate is missing;
- per-context δ, σ and λ_c with intervals;
- same-cover retest differences against the intervals;
- the cross-cover difference;
- which certainty function is selected.

Nothing here supports a trait claim on its own.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation fingerprint (tasks and model packages) | `c128ddf5fb32e9c0298135729aeda280e6cdb1fe40461ca57e425643b47f8517` |
| Task validation, seed 20260927 | `d5818201674d10af3ab5a76fcbf11f226fd2e46c346f891dea065931dce24d3e` |
| Task validation, seed 20261027 | `cf20eff6a8b711da46c39cea9e0038d21a728de82f373a7fe3e74a9ef9e32870` |

Validation files remain in the ignored `output/` directory.
