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
