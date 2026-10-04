# Abstract-to-finance transfer: preregistration

Written 4 October 2026, before any data for this test were collected. Design: [finance-transfer-design.md](finance-transfer-design.md). Exploration that motivated it: [exploration log](exploration-log.md), 4 October.

## Hypothesis

**H1 (primary).** A configuration's round readout in abstract urn tasks predicts its round readout in finance tasks.
- Round readout is the share of its probability answers given at multiples of 0.05.
- This is a claim about how precisely a configuration reports numbers, in these tasks. It is not a claim about beliefs or about finance in general.

## Data

**Collection.** Preset `finance-transfer`, tasks 0.42.0 (design 0.31.0, model 0.21.0). One root, with every session fresh. No session that suggested the hypotheses is used.

**Configurations (12).**

| Family | Configurations |
| --- | --- |
| GPT-6 | Astra-low, Astra, Astra-high; Sol-low, Sol, Sol-high |
| GPT-5.6 | Luna-low, Luna, Luna-high; Terra-low, Terra, Terra-high |

The four GPT-5.6 effort variants were added for this test. A one-session smoke test of each (`output/smoke-gpt56-effort-20261004`) completed and verified, and the commands carried the effort setting with no warnings. Those sessions are not used.

**Sessions per configuration: 8 abstract, 10 finance.**

| Domain | Module | Variant | Sessions | Finance twin / abstract twin |
| --- | --- | --- | --- | --- |
| Abstract | `wording-urn-a` to `-d` | `wording` | 1 each | `wording-policy-a` to `-d` |
| Abstract | `copying-urn-asked` | `urn2-named` | 2 | `corroboration-cues` |
| Abstract | `selection-urn-asked` | `urn2-named` | 2 | `disclosure-cues` |
| Finance | `wording-policy-a` to `-d` | `wording` | 1 each | `wording-urn-a` to `-d` |
| Finance | `corroboration-cues` | `cues-a` | 2 | `copying-urn-asked` |
| Finance | `disclosure-cues` | `cues-a` | 2 | `selection-urn-asked` |
| Finance | `announced-a`, `-b` | `announced` | 1 each | none (a different structure) |

In total there are 216 sessions. Cases are separate and in random order within a session, and the runner shuffles sessions across the collection.

**Validity.**
- A session counts if it completed and verified.
- Sessions that fail are re-collected once, in a top-up root, with the same preset and implementation. The analysis reads both roots.
- A configuration enters the tests if it has at least 6 of its 8 abstract and 8 of its 10 finance sessions.

## Measures

The code is `ledger.finance_transfer.sessions` and `ledger.finance_transfer.preregistered`, committed with this document.

- **Round readout.**
  - Per session: the share of probability answers at a multiple of 0.05, among answers between 0.06 and 0.94 inclusive that differ from the case's stated prior.
  - The stated prior is the prior of the outcome the question asks about: the stated market or urn prior in the wording and statement cases, and the stated prior in the urn and description forecast cases.
  - Questions about a source's behaviour (the rate and probe questions: how often a source copies or withholds) state no prior for what they ask, so none of their answers is excluded on this ground.
  - A session with fewer than 5 such answers has no value.
  - A configuration's value in a domain is the mean over its sessions there.
- **Stated–applied gap** (secondary).
  - Per rate-asking session (the urn rate-asking and description modules): the mean over levels 1–3 of |mean stated base rate − applied base rate|. The applied rate is the fitted implied rate.
  - A configuration's value in a domain is the mean of its two structures, each the mean of its sessions. It needs both structures.
- **Sensitivity to verbal confidence** (secondary). The mean weight of a "definitely… confirmed" claim minus that of an "I think…" claim, in log-odds from the stated prior, over all wording cases in the domain.

## Tests

Each test is Spearman's ρ between configurations' abstract and finance values, with a one-sided permutation p:
- exact over every ordering for up to 9 configurations;
- otherwise 200,000 random orderings, seed 20261006.

| | Hypothesis | Configurations | Pass |
| --- | --- | --- | --- |
| **H1** | Round readout transfers | all included | ρ > 0 and p < 0.05 |
| H2a | Round readout transfers within GPT-6 | the GPT-6 configurations included | Holm-adjusted p < 0.05 |
| H2b | Round readout transfers within GPT-5.6 | the GPT-5.6 configurations included | Holm-adjusted p < 0.05 |
| H3 | The stated–applied gap transfers | all included | Holm-adjusted p < 0.05 |
| H4 | Sensitivity to verbal confidence transfers | all included | Holm-adjusted p < 0.05 |

- **Primary.** H1 is the single primary test, with no correction. The critical ρ is 0.503 at 12 configurations, 0.643 at 8 and 0.829 at 6.
- **Fallback.** H1 is designed for at least 10 configurations. With fewer included, it runs on those included at the matching critical ρ, and the result is flagged `below_minimum`.
- **Secondary.** H2a, H2b, H3 and H4 are Holm-adjusted together.

**Reported, not tested:**
- **Far transfer:** abstract round readout against the announced-count statements alone.
- **Per-configuration readings:** for each trait, whether each configuration is on the same side of the median in both domains.
- **Session-to-session SDs** of round readout.

```bash
uv run python -m epistemics.ledger finance-transfer-preregistered <root> --output output/finance-transfer-preregistered-<date>.json
```

## Power

From `uv run python -m epistemics.ledger finance-transfer-power --output output/finance-transfer-power-20261004.json`.

**H1.** The model:
- configuration values with a between-configuration SD of 0.17 per domain;
- a session SD of 0.20 (the pooled within-configuration SD of the existing urn, policy and announced sessions);
- 8 sessions per domain.

| | Full transfer | As explored (ρ 0.76) | ρ 0.5 | None |
| --- | --- | --- | --- | --- |
| 12 configurations | 0.97 | 0.70 | 0.34 | 0.05 |
| 8 configurations | 0.82 | 0.49 | 0.24 | 0.05 |

At 10 sessions per domain and twelve configurations: 0.98, 0.73, 0.38. With a between-configuration SD of 0.24: 1.00, 0.78, 0.41.

**H3.** The model: GPT-6 gaps 0.02 (session SD 0.02), GPT-5.6 gaps 0.10 (session SD 0.08), four rate-asking sessions per domain.
- Twelve configurations: power 0.73 if full, 0.47 as explored, 0.05 if none.
- If only the two medium-effort GPT-5.6 configurations entered: 0.51 and 0.27.

## What the outcomes mean

- **H1 passes:** round readout transfers from abstract to finance tasks in a preregistered test. This would be the first such trait in the repository. The passport's readout reading may then say so, conditional on these tasks.
- **H2a passes as well:** the transfer holds within one model family, not only between GPT-5.6 and GPT-6.
- **H1 fails:** transfer is not established at this power. The exploration result (ρ 1.00 on four configurations, 0.76 on eight) is then reported as not replicated.
- **H3 and H4** are secondary whatever H1's outcome. A failure there is not evidence against the exploration's coarser reading ("who has a gap").

## Frozen implementation

**Tasks fingerprint:** `2e8351bf3806c44922879079c100792c2b30920205614d9b3f425f5f54718c2a` (disposition-tasks/0.42.0).

**Task validation 0.42** passed on both seeds (4,656 cases, 199 contexts):

| Seed | File | SHA-256 |
| --- | --- | --- |
| 20260927 | `output/disposition-validation-0.42-20260927.json` | `6aa42fae563d9eddba7a699d7a6bd4ef028e26236aa1112fde54e26a087a6cca` |
| 20261027 | `output/disposition-validation-0.42-20261027.json` | `b2639bb226593a4c87242c8b7f248a1be6619922ae7e802c4b49a66a67786bec` |

This document and the analysis code (`src/epistemics/ledger/finance_transfer.py`, with `tests/test_finance_transfer.py`) are committed together, before the collection starts. The results cite that commit.

Deviations, if any, are reported with the results.
