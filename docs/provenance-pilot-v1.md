# Provenance pilot 0.1: specification and synthetic validation

Implemented design and synthetic-validation slice of the [predictive-usefulness pilot](predictive-usefulness-pilot.md): a frozen matched-case generator, public checkpoint contract, behavioral fit and offline synthetic checks. Protocol `provenance-pilot/0.1.0` and analysis `provenance-analysis/0.1.0` are separate from the shared core and earlier discovery studies. This is an original experimental design, not a replication or a validated general cognitive phenotype.

## Task and factors

A participant assesses whether a fictional company will meet a specified operating target. It first reports a probability and hypothetical action from a base rate, then updates after each document. Each document contains a directional assessment, a source track record and provenance: either a separately collected, non-overlapping sample or a relay of an earlier document with no new sample. No likelihood ratios, inferred source accuracies or evaluator reference probabilities appear in the public checkpoint.

The full factorial design crosses:

- Base rates: 0.2, 0.5 and 0.8.
- Leading evidence direction: favorable and unfavorable.
- Leading source history: 12/18 or 15/18 resolved original assessments correct. Opposing evidence uses the other track record.
- Provenance: independent reports or copied reports, with substantive text, publisher labels, track records, order and company held constant within a matched pair.

This makes provenance the manipulated difference between twins. All independent roots have their own samples; copied documents can cite another copy, requiring transitive provenance tracking. The public materials make dependencies explicit. This release does not test concealed copying, inferred plagiarism, retractions, source prestige, broad hypothesis generation or information search.

| Partition | Structure in copied condition | Episodes | Checkpoints |
| --- | --- | --- | --- |
| Profile fitting | Original, its copy, opposing original | 24 | 96 |
| Policy development | Original, its copy, opposing original, copy of the earlier copy | 24 | 120 |
| Held-out evaluation | Opposing original, leading original, copy of leading, copy of opposing, copy of leading copy | 24 | 144 |
| Total per configuration, one replicate | 36 matched groups, both twins together | 72 | 360 |

There is one prior-only checkpoint per episode. The independent twin retains the same claims and order but every document comes from a separate sample. Supplier, subscription and distribution cover stories accompany the three structures. Held-out transfer therefore includes a new dependency graph and cover story, **within the same binary-source model**; it does not establish transfer to a new causal mechanism or an entire industry.

The manifest fixes assignments and partitions before fitting. Every matched pair and world seed belongs to exactly one partition. Replicates repeat the full factor design; `--replicates N` multiplies the stated budget by N. Episode order is randomized. A future collector must provide a fresh context per assignment and continuous history within it, so twins are never shown in the same context.

## Conditional model

For an original source j with s_j correct assessments out of n_j, the evaluator reference assumes independent source accuracies with a symmetric Beta(1,1) prior. Its predictive accuracy for one new original assessment is:

`q_j = (s_j + 1) / (n_j + 2)`.

With assessment direction `d_j ∈ {-1,+1}`, its log likelihood ratio is:

`ℓ_j = d_j log(q_j / (1 - q_j))`.

This assumes symmetric errors conditional on the target and independent original signals given the target/source accuracies. Each original source contributes one new signal. A relay is deterministic conditional on its parent, so its content is not another independent observation under this reference. The experiment supplies track records and provenance, leaving the participant to infer their relevance; the reference's probabilistic assumptions are evaluator-side and remain contestable in interpreting real responses.

At checkpoint t, let U_t sum ℓ over distinct original signals and C_t sum ℓ over copied exposures, following each citation back to its original. With starting probability p_0, fit reported probability p_t using:

`logit(p_t) = b + w_p logit(p_0) + w_e U_t + w_c C_t + ε_t`.

| Parameter | Conditional interpretation | Reference |
| --- | --- | --- |
| b | Offset in reported log odds | 0 |
| w_p | Effective base-rate weight | 1 |
| w_e | Effective independent-evidence weight | 1 |
| w_c | Extra weight per copied exposure | 0 |

These are effective reporting weights conditional on the source model. A different interpretation of source histories, prior model or response scale can change them. They do not uniquely identify internal belief updates or an intrinsic bias. The reference probability is `sigmoid(logit(p_0) + U_t)`.

The fitter uses least squares on clipped reported log odds; endpoint probabilities are clipped at 10^-6 and counted. It rejects a rank-deficient design rather than reporting an unidentified copy weight. Bootstrap intervals resample whole matched groups, keeping twins and all their checkpoints together. Their population coverage has not been established.

## Validation and comparators

Four synthetic policies generate reference behavior, full counting of copies, weak response to independent evidence, and combined prior/evidence/copy/offset changes. Noiseless recovery must have maximum coefficient error at most 10^-8. Noisy simulations add checkpoint logit noise with SD 0.12 and a shared matched-group offset with SD 0.06; maximum coefficient error must be at most 0.12. These are engineering tolerances for known synthetic generators, not human/agent classification thresholds.

Only profile-partition responses may fit parameters. Policy-partition cases are reserved and unused in the current analysis. Held-out probability RMSE must remain at most 0.06 for each in-model synthetic policy. Compare individualized predictions with:

- A pooled fit using profile cases from all four synthetic policies, without individual weights.
- An individually fitted intercept/prior/one-gain model treating all reports as evidence, without a separate copy term.
- Persistence: the preceding observed response within the current episode, or the supplied prior at the initial checkpoint. This baseline uses past held-out responses; no future response is used.

The individualized model must beat each baseline on mean probability RMSE across the four synthetic policies. It need not beat every simpler model for every policy. Probability prediction, decision agreement and conditional task quality are reported separately.

A nonlinear negative control adds a copy effect only after two copied documents. It agrees with the reference on the fitting graphs, yet changes behavior on later structures. The held-out adequacy check must flag it. Passing this check demonstrates sensitivity to this particular failure of generalization, not all possible model misspecification.

Actions use hypothetical payoffs +1 if the target is met, -1 if missed and 0 for deferring; the synthetic decision rule acts only when reported probability exceeds 0.5. Terminal Brier scores and decision regret are expectations under the evaluator reference. No realized outcome oracle or real-world forecast outcome is collected in this slice. Accurate prediction of a synthetic agent's response can coexist with poor conditional task performance.

## Run offline

```sh
uv run epistemics predictive create --seed 1909 --output output/provenance-design
uv run epistemics predictive validate-synthetic --design output/provenance-design --seed 1909 --output output/provenance-validation.json
uv run epistemics validate output/provenance-validation.json

# Use an assignment ID from the operator-owned manifest.
uv run epistemics predictive preview --design output/provenance-design --assignment ASSIGNMENT_ID --index 1 --output output/provenance-preview.json
```

Omit the design seed for a fresh random schedule. The design directory must be new; artifact writes refuse to overwrite. Its manifest is mode 0600 in a mode 0700 directory and has an exact-byte digest plus an implementation fingerprint. Modifying bytes or using a different implementation rejects the design. This detects accidental drift; it is not an independently signed manifest. The command reports the complete episode/checkpoint budget; real-agent inference cost remains unmeasured.

`preview` is an operator tool. Its output contains only the requested evidence prefix and no seed, partition or reference answer, but the operator can request any checkpoint. It is **not a collection API or a security boundary**. Do not give respondents access to the design directory or evaluator commands. The separate [sequential collector](provenance-collection.md) now enforces order, hides future content, persists immutable answers and supports idempotent retries through MCP.

The JSON schemas are `predictive-design.v1`, `predictive-checkpoint.v1` and `predictive-validation.v1`. `uv run epistemics schema` exports them alongside unchanged existing contracts. The validation output is permanently labeled synthetic and is not a passport or accepted signing input. Reproduce it using the original manifest, code fingerprint and validation seed; no provider call, transaction or payment occurs.

## Example synthetic run

With design seed 1909, validation seed 1909 and one replicate, all 18 engineering checks pass. Mean held-out probability RMSE across the four synthetic policies is:

| Predictor | RMSE, probability points out of 100 |
| --- | --- |
| Individualized fit | 2.50 |
| Pooled fit | 7.27 |
| One-gain model treating all reports as evidence | 4.59 |
| Previous-response persistence | 13.00 |

The maximum noisy parameter-recovery error is 0.055. The nonlinear negative control produces 8.58 points of held-out RMSE, exceeding the 6-point synthetic adequacy limit despite fitting the simpler profile cases. These are reproducible checks on specified response generators. They provide no result about an actual agent, intervention efficacy or the predictive value of a real passport.

## Version review and next boundary

This release adds experimental behavior in a separate protocol. It does not modify shared core 0.1, report.v1–v4, passport.v1–v2, existing sessions or signature domains. Synthetic tests cover matched contrasts, public/private separation, graph semantics, split restrictions, recovery across three design/noise seeds, bootstrap grouping, structural holdout, the negative control, immutable manifests, schema drift and CLI behavior. Synthetic checks do not establish real-agent predictive validity, human predictive validity, intervention effects or registry integration. The [collection increment](provenance-collection.md) is versioned separately.

The sequential collector and operator-asserted execution/configuration metadata are implemented. Next size a real-run budget and freeze the empirical prediction/support criteria before final-test collection. Develop the evidence-ledger comparison on policy cases, with no assistance, generic review and untailored support as comparators. Current synthetic recovery neither validates those interventions nor supplies a personalization result.
