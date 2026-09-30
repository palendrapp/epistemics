# Confidence persuasion transfer test: preregistration

Written 30 September 2026, before any data on surfaces B, C or D were collected. Design: [confidence-transfer-design.md](confidence-transfer-design.md).

## Hypothesis

Reliance on a source's expressed confidence, when nothing says how reliable the source is, is a general disposition of a configuration, not a reaction to one surface.

The trait is *w*<sub>conf</sub>: the log-odds per step of expressed confidence in the T1-open model. It is fitted per session by `social.fit_advice_open`, on the same 24 cases (`social.advice_design`) on every surface.

## Data

**Surfaces.** Tasks 0.22.0:

| | Module | Variant | Surface |
| --- | --- | --- | --- |
| A | `advice-peer` | `peer-open` | an analyst's spoken call |
| B | `advice-relay` | `peer-open` | an analyst who did not read the urn passes on another's call in its own words |
| C | `advice-sensor` | `peer-open` | a sensor's display with a confidence indicator |
| D | `advice-agent` | `peer-open` | an automated agent's structured message with a confidence field |

**Configurations:** Astra-low, Astra, Astra-high, Sol-low, Sol, Sol-high, Luna and Terra.

**One session per cell.**
- **Surface A** uses sessions already collected: `output/multi-agent-open-20260930` for Astra, Sol, Luna and Terra, and `output/multi-agent-stability-20260930` for the four effort variants. Astra's and Sol's second sessions in the stability collection are not used.
- **Surfaces B, C and D:** one new collection of 24 sessions.

**Validity.** A cell counts if its session completed and verified. If a session fails, it is re-collected once in a top-up; if that fails too, the cell is missing. The test runs if at least 7 configurations have all four surfaces.

## Primary test

**Leave one surface out.**
- A configuration's deviation from the other configurations on a held-out surface is predicted from its mean deviation on the other three.
- The gain is 1 − (squared prediction error) / (squared deviation).
- The within-surface permutation *p* uses 2,000 permutations with seed 20261016 (`ledger.confidence.test`).

**Pass:** gain > 0 and *p* < 0.05. There is one primary test, so no correction.

```bash
uv run python -m epistemics.ledger confidence-transfer output/multi-agent-open-20260930 output/multi-agent-stability-20260930 <new collection> --output output/confidence-transfer-<date>.json
```

The roots are given in this order, so for Astra and Sol surface A takes the first session collected.

## Secondary tests (reported, not gating)

1. **Model direction:** Sol above Astra at each effort (low, medium, high) on each surface. That is 12 comparisons, reported as wins out of 12.
2. **Uninformed emphasis (surface B):** per configuration, whether the 90% interval of *w*<sub>conf</sub> on B lies above 0. The ideal is 0, because the relayer has no information of its own.
3. **Social against non-social:** per configuration, the mean of A and B minus the mean of C and D.

## Power

`ledger confidence-power`, 400 simulated data sets per scenario. The configuration values are the task-A estimates so far, and the within-configuration spread is 0.08 for GPT-6 and 0.15 for GPT-5.6.

| Scenario | Pass rate | Median gain |
| --- | --- | --- |
| General: every surface reflects the trait | 1.00 | 0.88 |
| Social only: A and B share it; C and D carry an unrelated effect of the same spread | 0.25 | −0.17 |
| None: every surface carries an unrelated effect | 0.045 | −0.36 |

SHA-256 of the power output: `e1a3c9412f952888f7d8a5efc535b5f0e473af6d0bfa6b89a08a465c1df0e35e`.

## Interpretation, fixed in advance

- **Pass:** a general reliance on expressed confidence, which separates the configurations. It becomes a passport entry, worded task-conditionally: "moved by a source's confidence when its record is unknown, across the surfaces tested".
- **Fail, with secondary 3 large** (A and B above C and D for the configurations that rely on confidence): a disposition about analysts' confidence, not confidence in general.
- **Fail otherwise:** reported per surface, and no general trait is claimed.
- **Secondary 2** is reported whatever the primary outcome. A configuration moved by uninformed emphasis is moved by confidence that cannot carry information.

## Implementation

- **Tasks 0.22.0,** fingerprint `19dbd647335574be6545a2383faae05340c5731d4e30b32bce9a99cfdf21b0f7`. It was validated on both seeds (2,472 cases, 108 contexts), including respondents with known *w*<sub>0</sub> and *w*<sub>conf</sub> on each new surface.
- **Validation SHA-256s:** seed 20260927 `02e23640c9a3926a012bcfea9890fbd9619b5c5176fc34e49314e0638020d195`; seed 20261027 `3abfe4e63897ecfa72605db7a5bbb831b2f29f86dc4f377ba7751f31bb576a1e`.
- **The new collection** runs from this implementation and these validations.

## Deviations (written during collection, before the top-up)

**The failure.** The first collection (`output/confidence-transfer-20260930`) stopped after 6 of 24 runs.
- Sol's sensor session failed after 15 tool calls with a provider error ("Selected model is at capacity"): an infrastructure failure, not a respondent one.
- The runner admits nothing after a failure, so 18 runs were not attempted.
- Five sessions completed and are kept.

**The top-up.** As the validity rule above provides, the failed session is re-collected once, in a top-up (`output/confidence-transfer-20260930-2`). The top-up has the same implementation and validations, and contains exactly the failed run and the 18 unattempted ones. The failed attempt's partial answers are not used.

**The analysis command** takes both new roots after the task-A roots:

```bash
uv run python -m epistemics.ledger confidence-transfer output/multi-agent-open-20260930 output/multi-agent-stability-20260930 output/confidence-transfer-20260930 output/confidence-transfer-20260930-2 --output output/confidence-transfer-20260930.json
```

## Results (30 September)

**Collection.** All 24 cells were collected: 5 in the first collection and 19 in the top-up, where the re-collected Sol sensor session completed. That is 12.1 million recorded input tokens. The primary test ran on all 8 configurations × 4 surfaces.

**Correction to the analysis code, not the analysis.** The first run of the preregistered command returned empty cells for B, C and D. The summary it calls kept only modules ending in `-peer`, which silently dropped the new surfaces. It now keeps the battery's list of peer modules. No other change was made, and the output below is from the preregistered command.

***w*<sub>conf</sub> by configuration and surface** (log-odds per step of expressed confidence):

| | A. Analyst's phrase | B. Uninformed relayer's phrase | C. Sensor flag | D. Agent's confidence field |
| --- | --- | --- | --- | --- |
| Astra-low | 0.00 | 0.00 | 0.90 | 0.50 |
| Astra | 0.00 | 0.00 | 0.90 | 0.69 |
| Astra-high | 0.00 | 0.00 | 0.69 | 0.69 |
| Sol-low | 0.29 | 0.00 | 1.00 | 0.60 |
| Sol | 0.50 | 0.00 | 0.80 | 0.50 |
| Sol-high | 0.50 | 0.00 | 0.69 | 0.60 |
| Luna | 0.06 | 0.00 | 0.95 | 0.49 |
| Terra | 0.88 | 0.00 | 0.00 (ignores the sensor: *w*<sub>0</sub> 0) | 0.54 |

**Primary: not supported.** The leave-one-surface-out gain is −0.69 (permutation *p* = 0.98, sign agreement 0.41). A configuration's reliance on expressed confidence on three surfaces does not predict it on the fourth.

**Secondary.**
1. **Sol above Astra.** The preregistered code reports 8 of 12. Exactly:
   - Sol is higher in 5: all three efforts on A, one on C, one on D.
   - Astra is higher in 3: C medium, D medium, D high.
   - 4 are ties: all three on B, and C high. The code's count broke the ties on floating-point noise at zero.
   - The Sol–Astra difference is confined to surface A.
2. **Uninformed emphasis (B).** No configuration's interval lies above 0. Every *w*<sub>conf</sub> is 0.00, while each still gives the relayed call itself its usual weight (*w*<sub>0</sub> 0.6–1.1; Luna 0).
3. **Social minus non-social.** Negative for seven of eight configurations (−0.39 to −0.79): confidence from sensors and agents counts more than confidence from analysts. The exception is Terra (+0.17), which ignores the sensor.

**Interpretation, as fixed in advance.** "Fail otherwise: reported per surface, and no general trait is claimed." Confidence persuasion is not a general trait of these configurations. What the four surfaces show:
- **Structured confidence is read as information by everyone.** A sensor's HIGH or an agent's `confidence: high` moves every configuration by 0.5–1.0 log-odds per step (Terra's sensor aside). Nothing says what the levels are worth, so this is a default, not an error.
- **Emphasis from a source with no information moves no one.** The confident-coordinator mechanism, in the form tested here (a relayer who is said to know nothing more), does not operate in any configuration. This is the clearest result for the incident question.
- **Verbal hedging and emphasis from an informed analyst is where Sol and Astra differ.** Sol reads "I think…" and "definitely… confirmed" as information about accuracy; Astra treats them as style. This replicated across effort and retest, but it is specific to spoken phrasing. It belongs in the passport as a surface-specific behaviour ("weighs an analyst's verbal confidence"), not as a trait.

| Artifact | SHA-256 |
| --- | --- |
| Analysis (`confidence-transfer`) | `9ea6cfbba4dc9853dcaa3432731cc068ffcc3b250c7c0eae690faedc85db3bc4` |
| Per-surface fits | `e526cc5bd66ffd7853b4fa3c10cc5414d8ac9b366924f7cf75774987f8811a78` |
| plan.json (first collection) | `5c99ba58b4ef54b7020ff548a1ed7d1cec5a62c823fd90aa15cbfd2c64038e5b` |
| execution.json (first collection) | `0294d70e8bfe4b25f445bebdc6966af899db38a94e4bb3aca075d5c1171bc102` |
| plan.json (top-up) | `3f232c3524fb259a48b008820bc1381a42403e60f0c4d49f4030281e05d59047` |
| execution.json (top-up) | `5512de99c47e52b62dec2255053b2f63d342d801ea69c7eca8b197316045a374` |
