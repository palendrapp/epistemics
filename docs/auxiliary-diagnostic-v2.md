# Reading relationships and using uncertain evidence

`auxiliary-diagnostic/0.2.0` is a separate development module. It asks whether a respondent extracts the same relationship from summary counts and company records, how it interprets an imperfect growth signal, and whether its related judgment follows its own reported expectations. The [0.1 acceptance](auxiliary-acceptance-2026-09-23.md) found exact consistency under explicit controls; this revision adds extraction burden and evidence uncertainty without changing that completed evaluation or the active human session.

This is one step toward interpreting richer company evidence. Numerical records still have unambiguous event definitions. The task does not yet measure open-ended interpretation of headlines, alternative causal explanations or spontaneous hypothesis generation.

## Matched cases

There are **16 cases, 64 checkpoints and 160 probability reports**. Four underlying worlds cross two related targets (backlog and bulletin understatement) with associated or independent archives. Each world is presented in four independent agent contexts:

| Archive presentation | New evidence |
| --- | --- |
| Summary of event counts | Definitive growth audit |
| Company records | Definitive growth audit |
| Summary of event counts | Imperfect growth reading |
| Company records | Imperfect growth reading |

Both presentations describe the same complete archive of 20 companies. Counts can be reconstructed exactly from the records. Record identifiers are uninformative, and the task explicitly says numerical differences beyond the defined event categories have no additional predictive relevance. Records require extracting growth and backlog/understatement categories; they do not provide additional company evidence. Associated backlog probabilities are 0.8 versus 0.2 conditional on growth, associated understatement probabilities are 0.2 versus 0.8, and independent probabilities are 0.5 versus 0.5.

The source event now has an explicit denominator: `(audited revenue − initial bulletin revenue) / audited revenue ≥ 0.05`. Growth means audited revenue strictly more than 10% above prior revenue. Backlog means opening backlog strictly above 100 million credits. All amounts use millions of credits. The original 0.1 wording is preserved in that frozen version.

The four checkpoints are:

1. Report growth and related-event marginals, plus related-event probabilities conditional on each possible definitive growth audit result.
2. Read either a definitive growth audit or a high/low instrument reading with its complete validation history. Report both marginals.
3. Report again with explicitly no new information. The previous reading must not be counted twice.
4. A final definitive audit resolves **both** events. Report both marginals.

Resolving both events at the end avoids confusing direct response adjustment with legitimate reverse inference about growth after learning the related event. The signal's validation archive contains 40 other companies: 15 high and 5 low readings among the 20 high-growth companies, with the reverse counts for low growth. Its errors are declared independent of the related event conditional on growth, with the same error process for the current company. Exact population likelihoods are not supplied. This conditional-independence assumption is part of the diagnostic, not something the respondent must discover.

Quartets share archive, evidence direction and final outcomes. Directions and outcomes balance within each target, but direction is confounded with associated/independent status within that target. Association sign also remains confounded with target. This small design cannot support valence or negativity claims. The final growth outcome matches the signal direction in these authored cases; final outcomes must not be used to estimate instrument reliability. Cases are contrasts, not random portfolio draws. Seed, quartet labels and unrevealed outcomes stay evaluator-side. Human participation is continuous and may have carryover.

## Observations before fitted explanations

Let a respondent initially report `c+ = P(A | G)` and `c− = P(A | not G)`, and subsequently report growth probability `g`. Its own conditional mixture is:

\[
\widetilde a(g)=g c_+ +(1-g)c_-.
\]

The report compares its subsequent related-event probability with this mixture. This uses its own signal interpretation, rather than assuming it must report 0.75 or 0.25 after the reading. An agent can make a smaller related-event update because its growth forecast remains uncertain and still be perfectly consistent with its earlier conditionals.

Case facts include initial mixture consistency, both later mixture gaps, growth and related-event changes on the neutral repeat, direct resolution errors and the reported conditional spread. Eight matched presentation contrasts report records-minus-summary spreads and absolute mixture gaps. These are descriptive observations with denominators. Their interpretation assumes the conditionals retain their meaning, the conditional-independence instruction is understood and eliciting a conditional did not itself change the relationship being judged. A gap alone is not a bias diagnosis.

## Candidate report model

The authored model has five parameters: separate association scales `βsummary` and `βrecords`, signal weight `λ`, propagation fraction `ρ`, and **auxiliary-only** report adjustment `α`. For presentation `p`, let `d` be +0.3 for associated backlog, −0.3 for associated understatement and 0 for independent archives:

\[
c_+=0.5+\beta_p d,\qquad c_-=0.5-\beta_p d.
\]

For a definitive audit, `q` equals its resolved growth outcome. For a signal, let `s = +1` for high and `−1` for low:

\[
q=\operatorname{logistic}(\lambda s\log 3),\qquad
m=q c_+ +(1-q)c_-,\qquad
t=0.5+\rho(m-0.5).
\]

The log likelihood ratio `log 3` is the plug-in reference from the empirical instrument archive, with a fixed 0.5 initial growth probability. It is a modeling assumption, not a disclosed population likelihood or the only defensible inference under finite evidence. Both post-evidence and neutral-repeat growth reports have prediction `q`. Related-event report predictions are:

\[
r_1=0.5+\alpha(t-0.5),\quad
r_2=r_1+\alpha(t-r_1),\quad
r_3=r_2+\alpha(a-r_2),
\]

where `a` is the final related-event resolution. The model does not apply `α` to growth reports. Separate growth-report inertia, asymmetric responses, changing conditionals, lapses and correlations in response noise are outside this family.

Both association scales range from 0 to 1.5 by 0.25; `λ` ranges from 0 to 2 by 0.5; `ρ` and `α` range from 0 to 1 by 0.25. All 6,125 grid points are evaluated using the shared rounded logistic-normal report likelihood with fixed logit SD 0.25 and censored endpoints. Fits use seven observations per case: the two conditionals, both post-evidence reports, both repeat reports and the final related-event report—112 fitted observations overall. Initial marginals and final growth reports are checks. Maximum departures from the assumed 0.5 initial marginals remain visible.

Restricted comparisons share the association scale across presentations, force full propagation or force immediate auxiliary reporting. These families overlap; tied likelihoods do not identify an internal mechanism. The first auxiliary change identifies a product of propagation and report adjustment, with later checkpoints supplying additional constraints. Zero association or zero auxiliary adjustment leaves propagation unidentified. Outputs expose grid ties; they do not supply calibrated uncertainty intervals or validated passport traits.

This is an authored diagnostic informed by our [cognitive-modeling review](cognitive-modeling-review-2026-09-20.md) and the design/recovery workflow of [Wilson and Collins (2019)](https://elifesciences.org/articles/49547), not a replication of a published instrument.

## Recovery and acceptance boundary

The declared offline checks simulate six separated grid profiles: reference, records attenuation, signal attenuation, selective propagation, auxiliary smoothing and a combined profile. Sixteen repetitions per profile give 96 datasets per seed. Predeclared gates require parameter MAE ≤0.20 and average error in predicted means on a new template collection ≤5 probability points. Independently noisy future reports score frozen fits; changing case order and resolutions does not create a new domain. Restricted-family scores are recorded without claiming unique family recovery.

Both seeds, 20260924 and 20260925, pass. Across all parameters, the largest MAE is 0.0130 / 0.0104; mean new-collection prediction error is 0.151 / 0.105 points. Zero-association and zero-adjustment degeneracy are flagged. A deliberately out-of-family pattern reverses the growth forecast on the no-information repeat; its best fit remains poor at 10.26 points, exceeding the declared eight-point negative-control minimum. That minimum is a simulation check, not an empirical participant cutoff. These checks use the assumed noise family and separated grid parameters; they do not establish equal precision on real responses.

Implementation fingerprint: `231248e45c2433a5c22077043746cfe5b2f892f1880d5e2ad39a229dfe0dee95`. Protocol, evaluator and analysis versions are independently named `auxiliary-diagnostic/0.2.0`, `auxiliary-diagnostic-evaluator/0.2.0` and `auxiliary-diagnostic-analysis/0.2.0`. New collection/trial/report contracts use `epistemics.auxiliary-*.v2`; existing contracts, fingerprints and passport issuance remain unchanged. The module is not yet a passport dimension or provider-issuable report.

Implementation checks pass: 266 Python tests and 37 TypeScript tests, including equivalent information across archive formats, hidden future resolutions, immutable concurrent retries, resume, schemas, actual MCP transport and a complete synthetic browser collection through private HTTP. A separate synthetic records/signal case was inspected in the browser. The original evaluator fingerprint is unchanged.

The [fresh-agent acceptance](auxiliary2-acceptance-2026-09-24.md) is complete: all 16 cases and 160 reports in 11 minutes 46 seconds, without retries or failed submissions. Archive extraction, signal interpretation and conditional propagation matched the reference exactly; all model families tie at parameter values of 1.0. The added controls revealed no difficulty for this configuration. Repeated archives and irrelevant bulletin wording generated usability feedback. No task change was made during collection.

Actual human completion is still needed, particularly to assess the burden of extracting categories from records. Human and agent observations must remain separately labeled. Keep scientific derivation separate from issuer signatures and execution assertions. The next measurement priority is richer narrative/causal interpretation, rather than expanding arithmetic controls simply to seek variation.

## Local commands

```sh
uv run python -m epistemics.diagnostic2 create --directory output/diagnostic2 --participant participant.json
EPISTEMICS_DIAGNOSTIC2=output/diagnostic2 EPISTEMICS_ASSIGNMENT=CASE_ID \
  uv run python -m epistemics.diagnostic2.mcp_server
uv run python -m epistemics.diagnostic2 export --directory output/diagnostic2
uv run python -m epistemics.diagnostic2 validate-synthetic --seed 20260924 --output output/recovery2.json
uv run python -m epistemics.diagnostic2 simulate --directory output/diagnostic2-synthetic
uv run python -m epistemics.diagnostic2 schema
```

For a separate human collection, supply a human participant descriptor, then run `uv run python -m epistemics.diagnostic2 serve --directory output/diagnostic2-human --port 8771`. It uses whole percentages and the same transactional, immutable-answer service as MCP. Open only its private URL. The original port 8769 session belongs to the original diagnostic and is not migrated. Synthetic previews require explicit synthetic origin and never count as human participation.
