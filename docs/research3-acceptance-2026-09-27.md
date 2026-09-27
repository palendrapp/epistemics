# Register-versus-validity acceptance (0.3) — 27 September 2026

**Neither failure appeared.** In every arm, including unprompted, Astra and Sol:
- **Fabricated reports:** gave no weight to polished survey reports whose own figures were impossible;
- **Informal emails:** gave full weight to valid reports written up as hurried emails.

Reports matched the normative posterior within half a point, where a naive reading would have moved them 13.8 points (validity) or 18.4 points (register). Every paired estimate is zero. All 12 contexts completed. This is an engineering acceptance and a scoped behavioral observation, not a passport claim.

## Design

The frozen plan was identical in shape to the [0.1](research-acceptance-2026-09-27.md) and [0.2](research2-acceptance-2026-09-27.md) acceptances:
- **Contexts:** Astra and Sol medium, three arms, one type A and one type B context each: 12 fresh contexts through the Codex CLI on the existing ChatGPT subscription.
- **Cases:** nine per context.
- **Implementation:** [research-world 0.3](research-world-design.md#12-register-versus-validity-research-world030-27-september), fingerprint `1144012e…827296`, with two passed validations.

## Results

| Measurement | Astra | Sol |
| --- | --- | --- |
| Contexts completed | 6/6 | 6/6 |
| Rejected tool calls | 0 | 1 malformed submission, resubmitted correctly |
| Input tokens per context | 0.40–0.44 million | 0.37–0.40 million |
| Seconds per context | 63–83 | 69–77 |
| Decisions consistent with own report | 54/54 | 54/54 |
| Mean deviation from normative, fabricated-report dossiers | 0.4 points | 0.4 points |
| Mean deviation from normative, informal-email dossiers | 0.1 points | 0.1 points |
| Survey bought / worth buying | 19 / 18 | 18 / 18 |
| Neglect weight, validity and register (every arm) | 0.00 | 0.00 |

Total known usage was 4,750,821 input tokens (4,345,344 cached) and 18,248 output tokens. Main wall time was 446 seconds. Astra bought one survey whose normative net value was negative.

## What the respondents said

Unprompted, respondents identified every impossibility type:
- "Unreliable reports included reversed fieldwork dates, counts exceeding the sample size, inconsistent percentages, and an implausibly small margin of error." (Astra)
- "Some reports looked unreliable because their dates ran backward, their counts and percentages disagreed, or their stated margin of error was implausible." (Sol)

Both correctly treated percentages totalling 99% or 101% as rounding, and informal emails as "covered by the same stated reliability as formal reports." Friction was limited to unrelated briefs and the dossier being repeated at survey checkpoints.

## Interpretation across three rounds

| Round | Structure | Result (both configurations, every arm) |
| --- | --- | --- |
| 0.1 | Relays and selective disclosure, stated in the text | Exact Bayes |
| 0.2 | The same structures, inferred from matching figures, dates and a general fact | Exact Bayes, apart from one repeated arithmetic slip |
| 0.3 | Fabricated-but-polished and valid-but-informal reports in synthesis | Exact Bayes |

Within this task frame, the two medium-effort GPT-6 configurations reason correctly about provenance, omission, fabrication and register:
- explicit numeric likelihoods;
- stated general facts that define the correct answer;
- short dossiers delivered whole;
- a single forecast per case.

The failures reported in the literature were mostly observed in open-weight or earlier models, or in settings without these scaffolds.

**What this does not yet establish.** No real agent has shown a deviation on this battery. The synthetic validations show that the estimator would recover one. They do not show that a real configuration capable of the error would make it on these dossiers. Before investing in harder regimes, a **positive control** would test whether the battery separates configurations at all. The candidates are configurations expected to reason less carefully:
- `gpt-5.6-luna` and `gpt-5.6-terra`, which were available in the earlier prediction benchmark and less accurate there;
- the GPT-6 configurations at low reasoning effort.

If a weaker configuration shows neglect here, the battery discriminates. It would then support a reading-guide product that tells orchestrators which cheaper configurations can safely handle this evidence. If not, the next levers are removing the calculation scaffold or making the respondent direct its own research.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Implementation fingerprint | `1144012ec64deb39597e6e2973c1e9207747f8d3bd396d1d932ee0a5de827296` |
| plan.json | `9db845d6ff3a56d23678200d44dfbd5d8ad58a8f01a1baef9c32a5e078b60399` |
| summary.json | `68de3b747f4d98142f008b4ee42988af752a57d5856f3ccd45713d8c079be71c` |
| execution.json | `d2482e29c9df8d3afa58eea306d4e30298849baac6f91bce382709db614d4f22` |

Raw collections and transcripts remain private and outside Git. Model revisions are requested aliases, and execution is operator-asserted.
