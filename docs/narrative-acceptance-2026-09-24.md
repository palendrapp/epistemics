# Narrative inference: fresh-agent acceptance, 24 September 2026

Eight fresh Astra contexts completed **32 checkpoints, 160 probability entries and eight research choices in 6 minutes 32 seconds**. The task supplied qualitative business/reporting stories, not numerical likelihoods. The respondent's later updates closely followed its own prospective forecasts and joint probabilities. The useful additional evidence is the declared interpretation that drove those updates, rather than a newly discovered updating deficit.

This is one configuration's development acceptance, with offered event combinations and explicit prospective questions. It does not validate a general phenotype, identify an internal cognitive mechanism or test an intervention.

## Scope and execution

- Battery `narrative-inference/0.1.0`, evaluator `narrative-evaluator/0.1.0`, analysis `narrative-analysis/0.1.0`; [design and mathematics](narrative-inference.md).
- Requested `gpt-6-astra`, medium reasoning, temperature unspecified; exact provider model revision unverified. Codex CLI `0.155.1`, existing account authentication.
- Eight distinct process/context IDs; fresh temporary working directory per case, continuous history within a case. User configuration, project documents, memories, shell, browsing and unrelated tools disabled; five assigned MCP tools enabled. Execution remains operator-asserted, not independently attested.
- Plan, configuration, evaluator snapshot and assignments committed to private hashes before the first answer. One attempt per case, 300-second per-attempt ceiling, 900-second total ceiling, concurrency one. No adaptive stopping or case replacement.
- Started **12:09:55.021716 UTC**, finished **12:16:27.465590 UTC**; elapsed **392.464 seconds**.
- All eight cases finished. No retries, rejected answers, failed attempts, unattempted cases or unknown-usage attempts. All eight cases were eligible for the prespecified conditional fit; none excluded.
- **96 MCP calls:** eight descriptions, eight histories, 40 current-trial reads, 32 submissions and eight finishes. No calls outside the assigned protocol.

CLI diagnostics included the known under-development skill-discovery warning. Each process also logged four startup state-database lookup fallback warnings. They caused no observed failed case, but the operator's checks are not proof of provider-side isolation.

## Interpretation before evidence

Across all eight cases, the respondent forecast the dashboard signal with these ranges:

| Assumed combination | Forecast P(signal) |
| --- | --- |
| Real demand change, no reporting artifact | 90–95% |
| Reporting artifact, no real demand change | 60–65% |
| Both | 99–100% |
| Neither | 10–15% |

Thus it treated a real demand change as more predictive of the signal than a reporting artifact alone. Initial marginal probabilities ranged from **45–60% for demand** and **40–50% for the artifact**. These are declared expectations under these stories, not known population priors or validated likelihood estimates. The task has no empirical base rate against which to label these values biased.

Five cases assigned 99%, rather than 100%, to the signal when both defined events occurred. The definitions logically entail the signal in that combination. This is a specific one-point shortfall in five of eight forecasts; it does not establish a general aversion to certainty or an underlying mechanism. All final definitive audits received exact endpoint reports.

## Updating and research

| Comparison | Mean discrepancy | Largest discrepancy | Cases |
| --- | --- | --- | --- |
| After signal versus initial joint × declared likelihoods | 0.607 TV percentage points | 0.843 | 8 |
| After selected audit versus conditioning the preceding joint report | 0.121 TV percentage points | 0.273 | 8 |
| Final report versus resolved joint state | 0 | 0 | 8 |

TV is half the sum of absolute differences across the four state probabilities. All signal and audit comparisons passed the conservative coordinatewise rounding-overlap check. Overlap is compatible with nearest-percent rounding; it does not prove exact joint coherence. No conditional reference was undefined.

The respondent selected the **pipeline audit in 8/8 cases**. It maximized expected joint-state information under each preceding report, with zero foregone bits. However, the constant policy “always inspect the pipeline” predicts these same choices: this run does **not distinguish information-sensitive research from a fixed source-checking preference**. Demand-audit and stop branches have implementation/synthetic coverage but no real-agent coverage here.

The audit changed the unaudited demand probability in the direction implied by the declared joint model. Confirming a reporting artifact reduced demand probability by 9–11 points; ruling it out increased demand probability by 12–16 points. For example, one distributor-rise case went from **76% to 65% demand probability** when the artifact was confirmed; one subscription-fall case went from **68% to 84%** when it was ruled out. These are task-conditional examples of explanatory competition, not evidence that business change and reporting error are mutually exclusive.

## Matched presentations

Each pair shared every background sentence, dashboard signal and final resolution. The table gives unsigned distances, not a directional framing effect.

| Matched case | Initial joint TV gap | Mean absolute signal-forecast gap | Post-signal joint TV gap | Post-audit joint TV gap |
| --- | --- | --- | --- | --- |
| Distributor, fall | 5 | 4 | 3 | 2 |
| Distributor, rise | 0 | 1.25 | 2 | 3 |
| Subscriptions, rise | 5 | 0 | 6 | 3 |
| Subscriptions, fall | 5 | 1.25 | 6 | 3 |

All values are percentage points. All pairs chose the same audit, so their post-audit evidence is comparable. Initial interpretations varied modestly even with identical sentences. With one fresh response per format, **format effects and ordinary run-to-run variation are confounded**. There is no repeated-same-format comparison or established negativity effect in this run.

## Conditional model fit

All five prespecified families reached the same point: **signal weight w = 1, dependence retention κ = 1, report adjustment α = 1**, with **0.337 percentage-point coordinate RMSE** over 96 later-report coordinates (72 simplex degrees of freedom). The full grid has one minimizing point; the restricted families include that point and therefore tie. No more flexible family improved the fit over the respondent-declared reference.

This is an in-sample conditional report fit using the elicited initial distribution and forecasts as inputs. It shows no need for damped updating, discarded dependence or report lag in these cases. It neither uniquely identifies an internal Bayesian mechanism nor supplies held-out predictive validation. The earlier richer investigation's inadequate fit remains unresolved.

## Usability and cost

Every context mentioned the same minor friction: prose used one-based checkpoint numbering while tool indices started at zero. All selected the correct stage and completed successfully. Use named checkpoints in the next protocol revision; preserve this frozen run. No context mentioned repeated evidence burden, although absence of a complaint does not establish a usability benefit. The synthetic browser preview separately confirmed new-evidence presentation, prior-history access and selected-audit handling. The existing private human session was untouched; actual human acceptance remains pending.

| Provider usage | Tokens |
| --- | ---: |
| Input, including cached input | 1,216,396 |
| Cached input, included above | 1,065,216 |
| Non-cached input | 151,180 |
| Output | 5,057 |
| Total processed input + output | 1,221,453 |

Marginal dollar cost is unknown under the existing account arrangement. No payment, blockchain transaction, passport publication or identity registration occurred.

## Checks and next boundary

The offline suite passed **274 Python tests and 37 TypeScript tests**; Ruff checks and formatting passed. Both declared 96-dataset synthetic recovery runs passed, including nonidentifiability and out-of-family checks. Local browser/MCP transports were tested; Solana RPC coverage in the suite remains mocked. The first TypeScript test attempt was blocked by sandbox loopback restrictions and passed when rerun with local-listener permission.

The operator audit verified exact plan/configuration/manifest/report hashes, frozen implementation identity, distinct context IDs, complete immutable responses, permitted tools, complete usage and reproducible analysis. Raw responses, prompts, execution logs and evaluator truth remain private.

The next useful measurement step is a **small same-wording repeat comparison** to separate variability from presentation differences, plus a design revision that can make either audit informative. Keep initial interpretation, consistency and research policy separate in the eventual readable/machine-readable passport. Actual human usability, owned-identity issuance and a bounded paid job remain product requirements. No larger collection or intervention claim follows automatically from this acceptance.

## Exact artifact commitments

| Artifact | SHA-256 |
| --- | --- |
| Frozen implementation | `89a971dc11790af2e7137ed4ce4ccc42546e4cbc9f97401e83faf147c2ff3fd7` |
| Precollection plan | `4249622b93195b312e4d93d3baebc626e9af8a816ba447721be85d5823725313` |
| Configuration | `ee36a488afda20e464c63223f80c00b86e87f5c5d9ecd8821f63f32760473a7f` |
| Collection manifest | `82cc2922d9eaa7f649549f93d57d4c029c6036fc0d06e60dad83e8911c4ea7db` |
| Completed report | `7bdbae35326f0daf4e168aae9a41a9c548891438f7520db9cb1b6d0635f9ef0e` |
| Execution record | `aad2a5c8afd371bdbff4992b217427147e234ae20e28735428a40d560e80c21a` |

These bind exact private bytes. They are operator-created commitments, not independent timestamps, model attestations or public access grants.
