# Harder-cue dossier acceptance (0.2) — 27 September 2026

**Harder cues did not produce neglect.** In every arm, including unprompted, Astra and Sol inferred both structures:
- **Relays:** unattributed and partly rounded relays were counted once;
- **Omissions:** KPIs dropped from a letter were read as misses through a general background fact.

Their reports matched the normative posterior to the nearest point. The only material deviation was one arithmetic error by Sol on a control dossier, repeated identically in two separate contexts. All 12 contexts completed without tool errors. This is an engineering acceptance and a scoped behavioral observation, not a passport claim.

## Design

The frozen plan was identical in shape to the [0.1 acceptance](research-acceptance-2026-09-27.md):
- **Contexts:** Astra and Sol medium; unprompted, hinted and explicit arms; one type A and one type B context each. That makes 12 fresh contexts through the Codex CLI on the existing ChatGPT subscription.
- **Cases:** nine per context, with a priced survey on each, drawn from new worlds.
- **Implementation:** [research-world 0.2](research-world-design.md#11-harder-cues-research-world020-27-september), fingerprint `852e9cee…479388`, with two passed validations.

## Results

| Measurement | Astra | Sol |
| --- | --- | --- |
| Contexts completed / tool errors | 6/6 · 0 | 6/6 · 0 |
| Input tokens per context | 0.43–0.46 million | 0.38–0.42 million |
| Seconds per context | 62–81 | 67–95 |
| Decisions consistent with own report | 54/54 | 54/54 |
| Mean deviation from normative, relayed dossiers (naive gap 49.9 points) | 0.2 points | 0.2 points |
| Mean deviation from normative, selected letters (naive gap 17.4 points) | 0.3 points | 0.3 points |
| Survey bought / worth buying | 24 / 24 | 22 / 24 |
| Neglect weight, shared origin (every arm) | 0.00 | 0.00 |
| Neglect weight, disclosure | 0.00 (every arm) | 0.00 hinted; 0.22 unprompted and explicit, an artifact of the control error below |

Total known usage was 5,087,707 input tokens (4,657,280 cached) and 19,098 output tokens. Main wall time was 479 seconds. Longer dossiers cost about 20–30% more per context than 0.1.

**The one deviation.** Sol reported 31% for one full-letter control case, against a correct 47.9%: a 20% prior, three KPI beats and one miss. It gave exactly the same answer in its unprompted and explicit contexts, which were separate fresh contexts showing the same world. Astra reported 48%. The implied log-odds update, about 0.59 against 1.30, is consistent with an arithmetic slip rather than any reading of structure.
- **Effect on neglect estimates:** the error is on the control member of a disclosure pair, so it appears as a positive neglect estimate (0.22, standard error 0.21, four pairs) that says nothing about omission.
- **Effect on decisions:** the investment decision was unaffected, because both probabilities fall below the 0.7 threshold. But a survey worth +0.022 net was skipped, which accounts for both of Sol's missed purchases.

An error that repeats identically across fresh contexts is reproducible rather than random. It is one case, and cannot support a claim.

## What the respondents said

Respondents again named the structures unprompted, now as matters requiring care rather than stated facts:
- "The repeated reports of a single reseller survey required care to avoid counting the same evidence several times." (Sol, unprompted)
- "Missing KPIs required attention to the omission rule." (Astra, unprompted)

Reported friction:
- unrelated sector roundups adding reading load;
- the full dossier being repeated after a survey purchase.

## Interpretation

Two templated rounds now show both configurations reading dependence and selective disclosure correctly from dossier text. That holds both when stated (0.1) and when it must be inferred from matching figures, dates and a general background fact (0.2).

The remaining scaffold both rounds share is **numeric likelihoods plus general facts that make the correct answer exactly computable**. That is the regime the literature associates with Bayesian-looking behavior. As a reading-guide observation for these configurations, at this scope:

> Relayed coverage and KPI omissions in short research dossiers did not distort forecasts or verification purchases, even unprompted.

Scaling this collection would add precision to a null. Under the stopping rule it is not scaled.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation fingerprint | `852e9ceeeac7d9cd147d704b194bb789cf744be15a7588710da9aa6d41479388` |
| plan.json | `c3f978ccd05fefe72ab8e646f0931b1b15a54f146e3858583fb744b3757c2679` |
| summary.json | `63c43b5b070d00ae73796c042abba7b97a64532d33873e8ba07f192dddbee245` |
| execution.json | `88eb559855703dbe93109aaa6d6490be8f5e0815b70b34c5da0e8bb1974e41dc` |

Raw collections and transcripts remain private and outside Git. Model revisions are requested aliases, and execution is operator-asserted.
