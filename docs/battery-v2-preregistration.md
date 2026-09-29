# Abstract battery v2: preregistration

Written and committed before Stage 1. Design and rationale: [battery-v2-design.md](battery-v2-design.md); background: [trait reanalysis](traits-2026-09-29.md).

## Hypotheses

A configuration's position relative to other configurations carries over to abstract tasks on which it was not measured.

| | Trait | Role |
| --- | --- | --- |
| H1 | Precision: log report noise τ | Primary |
| H2 | Stated–applied fidelity: mean gap between stated and applied base rates at the ambiguous levels | Secondary (it failed its recovery gate; see Power and recovery) |
| H3 | Noticing threshold: prompting needed before the structure is considered (per-structure second layer) | Secondary |
| H4 | Far transfer: H1–H3 with both surfaces of the held-out task's core left out | Secondary |
| — | Near against far: the gain from the twin surface alone, against the gain from different cores | Descriptive |

## Design

**Configurations** (all six in every task): Astra, Sol (GPT-6, medium effort), Astra-low, Sol-low (low effort), Luna, Terra (GPT-5.6).

**Tasks** (three formal cores × two surfaces; battery disposition-tasks/0.14.0):

| Core | Surface A | Surface B |
| --- | --- | --- |
| Dependence | copying (urn2) | echo: observers who may repeat what another observer told them (urn2) |
| Withholding | selection (urn2) | hub: a hub that may forward every red reading and drop every blue one (urn2) |
| Uninformative evidence | mismatch (urn2-plain; urn3-named) | stale: readings that may date from before the urn was emptied and refilled (urn2) |

Each surface B uses its twin's item designs and observer exactly. Only the story, the records' wording and the questions differ.

**Protocol per configuration and task.** Five sessions: two plain, one named, one named and asked for rates, one named, asked and probed. Each session has 24 cases.

**Existing sessions.** Astra's and Sol's sessions on copying, selection and mismatch in these variants already exist and are used. For copying and selection, that is the urn2 run's 3, 3, 3 and 2 sessions per rung. For mismatch, it is 3 plain sessions and 1 per named rung. A cell's value is the mean of all its verified sessions in the battery's variants.

**Stages.**
- **Stage 1** (preset `traits-stage1`): Astra-low, Sol-low, Luna and Terra on copying, selection and mismatch. 60 contexts, token cap 34 million.
- **Stage 2** (preset `traits-stage2`): all six configurations on echo, hub and stale. 90 contexts, token cap 50 million.
- **Expected use:** about 79 million input tokens (0.53 million per context). The caps include the runner's admission reserve (0.8 million per run in a batch).

**Stage 1 as calibration.** Stage 1 may change one thing before Stage 2. If a surface-B story's twin sits at ceiling or floor for every configuration, meaning the noticing threshold is below 0 or above 3 for all of them, that story's graded records may be reworded. Any such change needs task validation and is recorded here before Stage 2. Nothing in the analysis may change.

## Analysis (frozen in code)

```bash
uv run python -m epistemics.ledger build
```

```bash
uv run python -m epistemics.structure_check check --validation output/structure-check-validation-20260929.json --output output/structure-checks-<date>.json
```

```bash
uv run python -m epistemics.ledger build
```

```bash
uv run python -m epistemics.ledger battery-v2 --output output/battery-v2-<date>.json
```

The second build picks up the structure checks.

**Cells.** One value per configuration × task (`epistemics.ledger.battery_v2`).
- **Precision:** the mean over sessions of log τ (disposition model 0.6.0, report-noise grid down to 0.01).
- **Fidelity:** the mean over the named, asked and probed sessions of |stated − implied| at levels 1–3.
- **Noticing:** θ from the per-structure second-layer fit (`structure_check`, 4 chains of 40,000 iterations). A cell counts only if the fit converged (R-hat 1.05 or less).

**Primary test.** For each trait, each configuration's deviation from the mean of the other configurations in a task is predicted by its mean deviation in the other five tasks.
- **Transfer gain** = 1 − Σ(deviation − prediction)² / Σ deviation².
- **Null:** within each task, which configuration is which is shuffled (5,000 shuffles, seed 20261001).
- **p:** the share of shuffles whose gain is at least the observed one, with the usual +1 correction.
- **H1 holds** if the gain is above 0 and p is below 0.05. It is the only primary test, so the Holm step leaves p unchanged.

**Secondary tests.**
- **H2 and H3:** the same test on fidelity and on noticing, unadjusted, each reported with its power and recovery (below).
- **H4:** leave one core out, meaning the prediction comes only from the other two cores. Its own shuffle p, unadjusted.
- **Near against far:** reported descriptively.
- **Consistency ρ:** from the generalizability study, for precision and fidelity.

**Validity.**
- **Minimum size:** a trait is tested only if at least 5 configurations and 5 tasks have cells. Missing cells are skipped, not imputed.
- **Contexts:** a context that failed or did not verify is not replaced within the stage.

## Power and recovery

**Surrogate power** (`traits-power`; six configurations, six tasks, five sessions per cell; variance components from the reanalysis):

| Trait | Power |
| --- | --- |
| Precision | 0.99 (0.92 if configurations differ only as much as Astra and Sol) |
| Fidelity | 0.91 |
| Noticing | 0.62–0.79 |

With no trait, the test passes 5.75% of the time.

**Recovery through the real designs and fits** (`battery-v2-recovery`, 24 synthetic studies per scenario, Holm over H1 and H2). Pass rates:

| Scenario | Precision | Fidelity |
| --- | --- | --- |
| No trait | 0% | 0% |
| Traits as estimated (σ config 0.82 for log τ; half-normal 0.06 for the gap) | 100% | 58% |
| Frontier-like (0.49; 0.03) | 88% | 33% |

**Recovery gates,** set before the recovery ran:
- **No trait:** at most 10% false passes for each primary trait.
- **Traits as estimated:** at least 80% passes.

**Gate result.**
- **Precision passes** both gates.
- **Fidelity fails the second:** 58% against 80%. Through the real fits, a gap measured from two rate-asking sessions per cell is too noisy at the effect size the reanalysis suggests.
- **Consequence:** fidelity was planned as primary, and was moved to secondary on this result, before any Stage 1 data existed. Precision is the single primary test.
- **Why not add sessions:** measuring fidelity adequately would need more rate-asking sessions per cell than the 78 million token budget allows.
- **Noticing is not simulated through the pipeline:** its evidence is the second-layer recovery at the urn counts (θ correlation 0.96, 30 of 30 converged) and the surrogate power above.

## Commitments

| Artifact | SHA-256 |
| --- | --- |
| Tasks implementation fingerprint (0.14.0) | `91883da31889999b508db6e924c829bd90e147247c9f7cceedb3696212ba7f1e` |
| Model validation 0.6.0, seed 20260927 | `9c81d435eb802aa61d86a56676f55e22e0a5f77cec4e8354f7b4fffb93a89e29` |
| Model validation 0.6.0, seed 20261027 | `340da35485c89baf0608ca27347dd1a4e7a8d0c86a17e8b3d6c6db88c5533b10` |
| Task validation 0.14, seed 20260927 | `730682b596422b44c5b945c8a26fe22ac0302ac1e93b8f1c69417335ee2422a1` |
| Task validation 0.14, seed 20261027 | `5d75ce5202bc494991c984fbe32dfabd94c8575c1ef20dddeeb45d61baa2df87` |
| Transfer-test power | `54020bc1bc1d21eb4ebe5236810e1ad5822508e694ad80bb8384d98aa50da4f1` |
| Transfer-test recovery | `5077c141835a19962f210f17ecbd7c3c027a8662db6f9cc693aa4b3cf015d76b` |

## Stage 1 and the calibration check (recorded before Stage 2)

**Collection.** All 60 contexts completed and verified, with no errors: 30.3 million input tokens (28.0 million cached), 61 minutes.
- **A ledger fix was needed:** it first ignored this collection, because its directory name did not start with `disposition-` or `structure-check-`. It now also reads `traits-stage` directories.
- **An invalid check output was discarded:** a structure-check output computed before the fix, without Stage 1's sessions, was deleted before use.

**Calibration rule.** Is any surface-B twin at ceiling (θ below 0) or floor (θ above 3) for every configuration? Per-structure second-layer fits, all six configurations (`output/structure-checks-20260929-5.json`):

| Task | θ by configuration (Astra, Sol, Astra-low, Sol-low, Luna, Terra) | At a bound for all? |
| --- | --- | --- |
| Copying | −0.76, 0.05, 0.07, −0.21, 0.52 (not converged), 0.54 | No |
| Selection | −0.25, −0.26, −0.25, −0.26, 1.08, 1.19 | No |
| Mismatch | 1.03, 1.17, 0.99, 1.06, 0.10, 1.19 | No |

**Result: no surface-B story is reworded.** Stage 2 runs on the validated texts (fingerprint `91883da3…`). No transfer test was run on Stage 1 data.

| Artifact | SHA-256 |
| --- | --- |
| Stage 1 plan.json | `7bf3e80cb1eb382853d532981bc2dc4e6b61652c2954b51f2e47b32454eb34b6` |
| Stage 1 execution.json | `dd1c72506b1f51371affe5599f961e64e9a864e6c6399ffd6769b530ebcf560b` |
| Stage 1 summary.json | `bafb61df9e04f220d944182dbc3ff1b07523ba57d19071fa576f7181687259b6` |
| Structure checks, six configurations | `0a4625130808a3e25d7e133ece3bdee07198f69ece67c3ba1e1332be95787e44` |
