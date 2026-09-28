# Description-to-prior acceptance — 28 September 2026

**For relaying, GPT-6 Astra and Sol share nearly the same mapping from descriptions to priors; for selective disclosure they diverge.** Across all eight contexts:
- **Stated equals implied:** each configuration's stated base rates matched the priors implied by its forecasts and probes: rank correlation 1 wherever the mapping varied, largest gap 0.11.
- **Irrelevant details ignored:** the irrelevant description always sat at the context's baseline. In the first run that baseline was 50%; the retest below shows it can move.

**Relaying.** Both configurations moved the prior from 5–10% for an outlet with reporters who visit suppliers to 83–95% for an aggregator or one-person blog, with close agreement.

**Selective disclosure.**
- **Sol** used the descriptions in both paraphrase sets.
- **Astra** used them in set A but ignored every description in set B, keeping 50% throughout. It said it "kept the same assumption across backgrounds".

**Retest.** A retest in fresh contexts reproduced this exactly: Astra again ignored every set-B description. Its use of company background for disclosure is therefore stable but depends on the particular description, not random. The disclosure mappings of both configurations retested within 0.00–0.04 on average. The relay mappings kept their extremes, but their middle shifted with the context's baseline.

These are single contexts per cell; the patterns are descriptive.

## Collection

The frozen `cues` plan (tasks fingerprint `3c52a370…6ea5`, two passed validations) ran 8 fresh contexts through the Codex CLI on the existing ChatGPT subscription, with `caffeinate` on mains power:
- GPT-6 Astra and Sol at medium effort;
- relay cues and disclosure cues;
- description sets A and B, markets.

**Outcome:**
- **Collection:** every context completed with the minimum 27 calls and no tool errors, in 101–169 seconds.
- **Tokens:** 4,201,437 input tokens (3,918,976 cached) and 16,125 output tokens.

**Two bugs.** After all eight reports were exported, the runner's summary step failed (`KeyError: 'disposition'`): its headline function did not know the cue modules. The reports themselves re-verify. A second bug gave the ordering statistic spurious values for tied or flat mappings. Both are fixed in disposition-tasks/0.3.1, with tests and two passed validations. The statistics below were recomputed with tie-aware ranks, and the stored per-report analyses keep the original values.

## Results

Implied prior at each description level. The stated base rate is shown only where it differed.

**Relaying**:

| Level | Set A description | Astra A | Sol A | Set B description | Astra B | Sol B |
| --- | --- | --- | --- | --- | --- | --- |
| Strongly reassuring | twenty reporters interview customers and suppliers | 0.05 | 0.05 | research desk visits factories before every call | 0.10 | 0.05 (stated 0.02) |
| Mildly reassuring | sometimes runs its own surveys of retailers | 0.60 | 0.50 | a few analysts occasionally speak to suppliers | 0.40 | 0.66 |
| Irrelevant | based in a city on the coast | 0.50 | 0.50 | blue-and-white layout | 0.50 | 0.52 |
| Mildly suggestive | small newsletter with two analysts | 0.60 | 0.60 | usually publishes shortly after larger outlets | 0.70 | 0.70 |
| Strongly suggestive | aggregator with no reporters, dozens of calls a day | 0.90 | 0.95 | one-person blog, posts minutes after larger outlets | 0.85 | 0.83 |

**Selective disclosure**:

| Level | Set A description | Astra A | Sol A | Set B description | Astra B | Sol B |
| --- | --- | --- | --- | --- | --- | --- |
| Strongly reassuring | checked by an independent auditor | 0.25 | 0.20 | customer cooperative publishing all data later | 0.50 | 0.20 |
| Mildly reassuring | reputation for plain, complete reporting | 0.15 | 0.10 | same outside accountants for twenty years | 0.50 | 0.50 |
| Irrelevant | new headquarters building | 0.49 | 0.50 | sponsors a local football team | 0.50 | 0.50 |
| Mildly suggestive | hoping to raise financing | 0.58 (stated 0.65) | 0.70 | share price fell three quarters in a row | 0.50 | 0.54 (stated 0.65) |
| Strongly suggestive | executive bonus depends on the indicators | 0.74 | 0.71 (stated 0.80) | in talks to be sold; price depends on indicators | 0.50 | 0.70 |

**Summary statistics:**

| | Relay A | Relay B | Disclosure A | Disclosure B |
| --- | --- | --- | --- | --- |
| Astra–Sol rank agreement | 0.92 | 0.90 | 1.00 | undefined (Astra flat) |
| Astra–Sol mean absolute difference | 0.03 | 0.07 | 0.05 | 0.11 |
| Designed-order ρ, Astra / Sol | 0.82 / 0.97 | 1.00 / 0.90 | 0.90 / 0.90 | undefined / 0.97 |
| Range of implied priors, Astra / Sol | 0.85 / 0.90 | 0.75 / 0.78 | 0.59 / 0.61 | 0.00 / 0.50 |

**Model fit.** Evidence sensitivity was 0.97–1.07 and bias 0–0.10. Report noise τ was 0.05–0.16, except Sol's relay set B (τ = 0.43).

## Interpretation

1. **Priors from descriptions are coherent.** Wherever a configuration used a description, its forecasts and probes implied the same prior it stated when asked for the base rate. The exceptions are three suggestive disclosure items, where the implied prior fell 7–11 points short of the stated one. The mapping is therefore a property of the respondent that it can report, not an artefact of how forecasts are combined.
2. **Irrelevant details were never over-read.** Coastal location, layout, a new headquarters and a football sponsorship all left the prior at the context's baseline: 50% in the first run, and about 30% in the relay set-A retest, where the baseline itself moved.
3. **For relaying, the two configurations share one mapping,** spanning roughly 5% to 95%. They disagree only on a hedged sentence, "sometimes runs its own surveys": Astra read it as more likely to relay (60%), Sol as uninformative.
4. **For disclosure, Sol uses every description set; Astra is selective.** Sol used company background in both sets. Astra used it in set A and ignored it throughout set B, and did so again on retest. Across round 2 and this acceptance, Astra ignored disclosure-relevant background in two of the four contexts that offered it (round 2's reassuring descriptions, and set B here) and used it in the other two. Which kinds of background a configuration applies, and how reliably, is a candidate reading-guide property.
5. **The designed ordering was partly wrong, and the two configurations agreed about how.** Both judged "a reputation for plain, complete reporting" more reassuring than "checked by an independent auditor". Where the designed order and the agents disagree, agreement between configurations, and later with people, is the better reference than the designer's intuition.

## Retest

The same eight cells ran again in fresh contexts with new case orders, as repeat 2 on disposition-tasks/0.3.1 (fingerprint `0c9941ed…dc02`):
- **Collection:** all 8 completed with the minimum 27 calls and no tool errors, in 98–405 seconds.
- **Tokens:** 4,227,484 input tokens (4,014,592 cached).
- **Summary step:** ran correctly after the fix.
- **Comparison:** the first run's reports were re-verified with their own frozen implementation snapshot before comparison.

| Cell | First run | Retest | Mean absolute difference | Rank agreement |
| --- | --- | --- | --- | --- |
| Astra, relay A | 0.05, 0.60, 0.50, 0.60, 0.90 | 0.05, 0.40, 0.30, 0.30, 0.95 | 0.15 | 0.92 |
| Sol, relay A | 0.05, 0.50, 0.50, 0.60, 0.95 | 0.05, 0.29, 0.32, 0.42, 0.82 | 0.14 | 0.97 |
| Astra, relay B | 0.10, 0.40, 0.50, 0.70, 0.85 | 0.05, 0.35, 0.50, 0.60, 0.65 | 0.08 | 1.00 |
| Sol, relay B | 0.05, 0.66, 0.52, 0.70, 0.83 | 0.05, 0.50, 0.50, 0.65, 0.80 | 0.05 | 0.97 |
| Astra, disclosure A | 0.25, 0.15, 0.49, 0.58, 0.74 | 0.20, 0.25, 0.50, 0.60, 0.75 | 0.04 | 0.90 |
| Sol, disclosure A | 0.20, 0.10, 0.50, 0.70, 0.71 | 0.10, 0.10, 0.50, 0.70, 0.80 | 0.04 | 0.97 |
| Astra, disclosure B | 0.50 at every level | 0.50 at every level | 0.00 | undefined (flat) |
| Sol, disclosure B | 0.20, 0.50, 0.50, 0.54, 0.70 | 0.25, 0.50, 0.50, 0.60, 0.70 | 0.02 | 1.00 |

Levels run from strongly reassuring to strongly suggestive, with the irrelevant level in the middle. Stated and implied priors again agreed (largest gap 0.07).

**The relay baseline moves between contexts; the extremes do not.** In the relay set-A retest, both configurations used a baseline of about 30% for an ordinary outlet from their first answers onward. A "small newsletter with two analysts" was implied at about 30%, where the first run gave 60%. The mild and irrelevant levels moved with it:
- Sol stated 30% for an outlet "based in a city on the coast";
- Astra's irrelevant level equalled its mildly suggestive level.

The strongly reassuring level stayed at 5% and the strongly suggestive level at 80–95%. The baseline is therefore a context-level default that can sit at indifference (50%) or at a belief that most outlets check for themselves (about 30%). Descriptions are applied relative to it, and irrelevant ones never moved away from it. Set B kept its 50% baseline in both runs. Which cue sets the baseline in a given context is not identified here: both runs of a cell used the same descriptions, in different orders.

**Retest reliability.**
- **Disclosure mappings:** reliable, with mean differences of 0.00–0.04. That includes Astra's reproducible ignoring of set B, which is therefore a stable, description-specific behaviour, not noise. Astra ignored the same kinds of background in round 2: customer ownership, later full publication of data.
- **Relay mappings:** less reliable in the middle (0.05–0.15), for the baseline reason above.

## Implications

**For the model.** The description-to-prior mapping is measurable, coherent and largely shared for relaying. Its between-configuration variance lies in how consistently incentive and governance information is applied. A reliability measure across paraphrase sets and repeats is more informative here than the mapping's average.

**For the reading guide.** Two candidate entries, each needing a retest:
- **Both configurations:** turn descriptions of a source's reporting capacity into strong relay priors (5–95%), and ignore irrelevant details.
- **Sol:** applies governance and incentive information to disclosure consistently. Astra's use of it varies between contexts; supply that assessment explicitly.

## Next

1. **Baseline.** Identify what sets the relay baseline: an explicit "ordinary outlet" description, and the effect of the first few cases.
2. **Weaker configurations and human references.** Run the same descriptions for GPT-5.6 Luna and Terra. The ordering disagreements also make a human rating of the descriptions worthwhile once human collection resumes.
3. **Transfer.** Dossiers without background facts, with source descriptions drawn from these levels, so the formal mapping predicts naturalistic behaviour.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint (collection) | `3c52a37088c4c2b1740837f8f4631ea49c7d0d9b81a4952b07e4b5d9e9015ea5` |
| plan.json | `9372f025e1c79a1bc78809747b3343a17a633dd9a91b0306a0091953d460b172` |
| execution.json (summary step failed; see above) | `96c4d3b36311fe2c6d08c3401bf4ddb14755a052893d57f87a834f438c22de18` |
| Tasks 0.3.1 fingerprint (bug fixes) | `0c9941ed4053311db432d5cc45506075490b9fa0551ee7a391189a80aeb3dc02` |
| Task validation 0.3.1, seed 20260927 | `64f5c3b07bd16b2c9cbfdf0c799ee094721cbd2ca7ac2096c647c124695667c5` |
| Task validation 0.3.1, seed 20261027 | `8835c84ee42cfc3fcb16b1ce76667cc5c0bba800a861ac70f13fc4558a111ee5` |
| Retest plan.json | `168deb0daa5963b4a0a1e0270671724ae24213f983e8b5bce713ad515b13c7da` |
| Retest execution.json | `51dfff08ef7d31ef9e6391cc28b46a6c77212e7415cc593288aa1677504c2efd` |
| Retest summary.json | `74a7f9134e167fc741ce3eb5d41e8840568d7a445109b0129b8465a79ec2f28e` |

Raw collections and transcripts remain private and outside Git. Model revisions are requested aliases, and execution is operator-asserted.
