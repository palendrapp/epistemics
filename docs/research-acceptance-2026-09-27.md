# Research-dossier acceptance — 27 September 2026

**The collection works, and both configurations read both structures correctly in every arm.**
- **Collection:** all 12 contexts completed with no tool errors, at 0.31–0.37 million input tokens per nine-case context.
- **Accuracy:** Astra and Sol reported the normative posterior to the nearest percentage point on every case. That covers selectively disclosed and relayed dossiers, including the unprompted arm.
- **Purchases:** they bought the independent survey exactly when its normative expected value exceeded its price.
- **Neglect:** every paired estimate is zero.

At this level of explicitness the dossiers do not separate the configurations or the arms. This is an engineering acceptance and a scoped behavioral observation, not a passport claim.

## Design

The [frozen plan](research-world-design.md#10-collection-interface-27-september) ran on the implementation fingerprint `b4531ca5…ec446d` with two passed validations:
- **Contexts:** Astra and Sol medium; unprompted, hinted and explicit arms; one type A and one type B context each. That makes 12 fresh contexts, run through the Codex CLI on the existing ChatGPT subscription.
- **Cases:** each context had four disclosure and four shared-origin worlds plus one anchor, nine cases in all, with a priced independent survey on every case.
- **Pairing:** matched presentations of each world appeared in separate contexts.
- **Execution:** no context was retried, and no outcome feedback was given during collection.

## Results

| Measurement | Astra | Sol |
| --- | --- | --- |
| Contexts completed / tool errors | 6/6 · 0 | 6/6 · 0 |
| Input tokens per context | 0.33–0.37 million | 0.31–0.37 million |
| Seconds per context | 65–75 | 63–93 |
| Decisions consistent with own report | 54/54 | 54/54 |
| Mean absolute deviation from normative posterior | 0.1–0.3 points in every presentation | 0.1–0.3 points in every presentation |
| Survey bought / survey worth buying (normative net value > 0) | 21 / 21 | 21 / 21 |
| Neglect weight, every arm and family (4 pairs each) | 0.00 | 0.00 |
| Mean action regret | 0 | 0 |

The deviations from the normative posterior are rounding to whole percentages. After a purchased survey, both configurations updated by exact Bayes from their own report, e.g. 0.81 to 0.94 on a positive survey.
- **Selected letters:** reports equalled the full-letter reports on the same world, although a naive reading would have been 30.6 points higher on average.
- **Relayed coverage:** reports equalled single-report coverage, although triple counting would have moved them 23.1 points on average.

Total known usage was 4,122,348 input tokens (3,776,640 cached) and 20,180 output tokens, with no unknown-usage attempts. Main wall time was 484 seconds.

## What the respondents said

Every completion answer about outcome timing and survey charging was correct. Without being asked, respondents named the structures:
- "Some news briefs repeated the same underlying reseller survey, so they were not independent evidence." (Sol, unprompted)
- "The shareholder letters reported only KPIs that met guidance, so their omissions mattered." (Sol, hinted)

Friction and ambiguity to fix in the next version:
- **Company-name collisions within a context:** two cases used the same fictional company name. The design should enforce unique names.
- **KPI independence unstated:** the normative model assumes KPIs are conditionally independent given demand, but the reference rates do not say so.
- **Inconsistent verbs:** "beats guidance" in the reference rates against "met or exceeded" in the analyst note.
- **Negative-survey wording:** "a majority increasing versus not" reads awkwardly beside a negative result.
- **Progress counter:** `answered` counts checkpoints rather than companies.

## Interpretation

This matches the [literature review](literature-review-2026-09-27.md)'s calculator regime, now reached through prose. Each dossier gave:
- **Explicit reference rates** for every evidence type;
- **The disclosure rule stated outright** in an analyst note;
- **Explicit attribution in every relay** ("surveyed by *firm* … the firm said in a note");
- **Four short documents**, only two of them relevant.

Recovering the structure required reading, not inference. The prose did not make the structure hard to notice.

Under the [pilot's stopping rule](decision-value-pilot.md#2b-naturalistic-disclosure-and-shared-origin-pilot), this collection is not scaled. Both findings are recorded at this scope. The next step is a decision between two routes:
- **Harder versions of the same two families:** more of the structure left for the reader to infer.
- **The next family:** register versus validity, or reliability learned through prestige cues.

**Measurement note.** Report noise here was far below the 2–8 points assumed in the precision study, about 0.3 points. When a deviation exists, a few independent worlds will detect it, and each context costs about a third of a compact-verification context. Any larger collection can be cheaper per world than planned.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation fingerprint | `b4531ca555d77d0e18b6d4dcf8b2269848a5daaf18f9871b97f0b47744ec446d` |
| plan.json | `75e23f33a7b39797dd6586a461ece25cb655a2dc4b70561a5117fa5d5a07afc6` |
| summary.json | `efe56c3d03f925c318a77fa0a5cc56471612eaf591939740f678295fe94c0a7a` |
| execution.json | `2c3eeaeeded583f541bf5e1f6f2869cf07644f1645a548b1ffaa11ba17f3c750` |

Raw collections and transcripts remain private and outside Git. Model revisions are requested aliases, and execution is operator-asserted.
