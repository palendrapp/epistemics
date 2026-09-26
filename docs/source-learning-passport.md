# Source-learning evidence in the passport

`passport.v4` adds readable HTML/Markdown and machine JSON for completed source-learning sessions. It supports original structured/prose panel evidence and the clarified 0.2 delivery. It preserves all original report bytes and does not reinterpret old answers as responses to new instructions.

## Derivation and grouping

The private `source-evidence.v1` bundle embeds exact report and transport strings with byte hashes. Python reconstructs generated worlds, public trials, prediction locks, the calibration fit, later predictions, outcome analysis and delivery records. It then derives the summary instead of trusting imported facts. Changing a fact, report, presentation, chronology or claimed origin breaks verification.

A bundle may contain one to 64 sessions with the same declared configuration, response origin, condition, presentation and protocol. Duplicate sessions, mixed sparse/dense conditions, mixed structured/packet formats and distinct human participants are rejected. Repeat variation uses only the first twelve unaudited forecasts, with matched source worlds and all available session pairs. Overlapping pairs and shared worlds are dependent; no population reliability coefficient or confidence interval is claimed.

The passport preserves original session subject IDs. If all IDs match, it retains that subject. If agent IDs differ but the complete declared configuration matches, the result is explicitly a **configuration cohort**, with a derived configuration label and all source IDs retained. This grouping does not create an evaluated-controller association or establish that a deployed service ran the evaluation. The attestation tool refuses to issue cohort evidence as a single agent identity. A future enrolled repeated collection can use one consistently bound subject from the outset.

Old reports without recorded transport can still produce a readable summary, but delivery is explicitly `unverified`. A collection that has a transport binding must export its evidence before bundling; the directory adapter refuses to silently omit it. Imported raw bytes alone cannot prove that an omitted transport record ever existed, so an unverified presentation receives no qualified consumer metrics.

## Observations and their limits

The source profile carries:

- Decision/report agreement, with the number of decisions.
- Final-outcome Brier and fictional payoff per company evaluation.
- Matched-repeat forecast RMS differences, with pair, world and forecast counts; **missing** when no matched repeat exists.
- Customer-panel, selection-audit, measurement-audit and stop frequencies, with research coverage.
- Separate within-session model diagnostics, preserving model inadequacy rather than converting the preferred candidate or reporting gain into a trait.

The six existing dimension headings remain. General evidence weights, broad causal reasoning and updating speed remain insufficiently covered. Final Brier is an outcome score, not a population calibration estimate. Research frequency is not research optimality. Repeat variation and predictability are separate from decision quality. The adapter does not claim external profile transfer from within-session fits, and no intervention recommendation is inferred.

## Machine policy and signatures

The catalog adds 17 versioned `source.*.v1` metrics: eight observations and nine coverage counts. No family identity, gain or adequacy result becomes a consumer trait. The initial machine policy mapping qualifies **single-subject, sparse, structured** source evidence only. Dense, packet, unknown-delivery and cohort scopes remain inspectable but require further policy work; they must not silently satisfy a differently scoped requirement. Policies already pin the exact protocol hash, protocol version and interpretation version.

A single run omits the repeatability measurement. A policy requiring that measurement returns review, rather than treating absence as zero variation. Synthetic evidence remains ineligible; predictive-validation and execution-verification requirements still require review. An explicit provisional policy is not evidence that its thresholds improve outcomes.

The existing `passport-attestation.v1` signature domain and canonical payload are unchanged. For supported single-subject agent passports, the TypeScript signer checks schemas, exact source/report/transport byte hashes, subject/configuration/protocol bindings and chronology. It **does not re-execute Python's scientific derivation**; issuers must run `passport verify` before signing. The consumer separately verifies issuer trust, registry association, lifecycle status and policy. A signature does not prove which model ran.

Human passports remain private and cannot use agent issuance. Source bundles contain evaluator worlds and answers; authorized audit access is separate from the readable/machine summary. This increment adds no public hosting, registry write, payment endpoint or production verification policy.

## Build from existing sessions

```sh
uv run epistemics passport bundle-source \
  --directory output/first-completed-session \
  --directory output/second-completed-session \
  --output output/source-profile/source.json
uv run epistemics passport create \
  --report output/source-profile/source.json --output output/source-profile/passport
uv run epistemics passport verify output/source-profile/passport/passport.json \
  --report output/source-profile/source.json
pnpm consumer metrics
```

Omit the second directory for a single session. The bundle and passport both refuse to overwrite different existing results. Read [the clarified collection](source-delivery-v2.md), [the completed panel](source-panel-results-2026-09-26.md), and the [verification comparison design](verification-value-v1.md) for the current evidence and next experiment.
