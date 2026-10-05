# Passport adapter: a mitigation bound to the passport (design)

Written 5 October 2026. Status: design; nothing is built or collected yet. Literature: [reading list](reading-list.md), "Passport-bound mitigation".

## Goal

Show that **a configuration with its passport adapter does better than the configuration alone**. The adapter is a mitigation generated from that configuration's passport and attached to its identity. The test also checks that the binding matters:
- **The passport adds something:** the configuration's own adapter beats a one-size-fits-all mitigation, or matches it more cheaply.
- **The match matters:** its own adapter beats an adapter generated for a different configuration.

"Does better" is measured against correct answers that the cases determine, not against preferences.

## What the passport says is worth mitigating

A target needs a cost against a correct answer, a difference between configurations (or tailoring is pointless), and a measure.

| Target | Passport finding | Cost | Tailoring signal | Phase |
| --- | --- | --- | --- | --- |
| **Hidden structures in finance dossiers** | Unprompted, Astra and Sol treat an aggregator with no reporters as independent (implied copying 0.00–0.03) and read silence as barely bad news ([unprompted dossiers](disposition-unprompted-2026-09-28.md)). | Double-counted calls; over-optimistic reads of incomplete updates: tens of points against the correct posterior. | Structure checks give the lightest prompt that works, per configuration (below). | **1** |
| The stated–applied gap | Luna states base rates its forecasts do not use, in finance descriptions and abstract tasks; Terra in abstract tasks. | Incoherent forecasts. | Luna and Terra, not Astra and Sol. | 2 |
| Confident wording without a record | Terra and Luna are moved more than the others by confident forecasts ([confident wording](exploration-log.md)). | Overweighting unverified confidence. | Terra and Luna. | 2 |
| Session-to-session variation | Luna sometimes ignores analysts' calls entirely; Terra varies widely ([session variation](exploration-log.md)). | Unreliable single answers. | Terra and Luna. | 2 |
| Round readout | Astra and Luna round more ([single-judgment test](single-judgment-preregistration.md)). | Small: rounding to 5 points costs little. | — | Not a target |

**Structure-check recommendations for the finance dossiers.** Each entry is the lightest prompt that made the configuration reliably consider the structure (the `structure_checks` ledger model). Rung 1 is mentioning the structure, rung 2 is also asking how common it is, and rung 3 is also asking about it for each case. "Undetermined" means the check did not converge.

| | Sources repeating another source (relay) | Selective silence (disclosure) |
| --- | --- | --- |
| Astra | Rung 2 | Undetermined |
| Sol | Rung 3 | Rung 2 |
| Luna | Rung 3 | Rung 3 |
| Terra | Rung 3 | Undetermined |

No configuration considers either structure reliably unprompted. The abstract urn structures vary more (rungs 1–3, "needs the rate", "not reliable") and are available for later phases.

## Mitigation components

Each component comes from a passport reading and has a dose. Fischhoff (1982) and Larrick (2004) favour changing the task or its representation over general warnings, and every component below is a question, an elicitation or a tool rather than an exhortation.

| Component | What it does | Triggered by | Dose | Sources |
| --- | --- | --- | --- | --- |
| **C1. Structure check** | Names a structure the configuration misses unprompted. Rung 1 names it; rung 2 also asks how common it is before the forecast; rung 3 also asks, for each case, whether it applies there. | A structure-check reading below rung 0 | Its recommended rung; undetermined or "not reliable" gets the strongest rung, since recommending too little is the costly error | Enke & Zimmermann 2019 (salience reduces correlation neglect); our [salience result](disposition-salience-2026-09-28.md) (one sentence: aggregator 0–3% to 86–92% copied); Kahneman & Lovallo 1993 (outside view); Lord, Lepper & Preston 1984 (a targeted question, not a warning) |
| C2. State, then compute | Asks for the base rates first, then a calculation tool takes stated prior, rates and evidence and returns the posterior. | The stated–applied gap | On or off | Gao et al. 2023 (program-aided); our [probes](disposition-probed-2026-09-28.md) brought forecasts within 0.04 of stated rates; Gigerenzer & Hoffrage 1995 (frequency format for the tool's output) |
| C3. Record before wording | When a claim's confidence is expressed in words, asks what the source's record is, and treats confident wording as no stronger than plain without one. A record-lookup tool is used where records exist. | A confident-wording reading of "moved more" | On or off | Our confident-wording and call-reaction results (exact with records); Jin, Luca & Martin 2021 (insufficient skepticism without feedback) |
| C4. Aggregate | Answers each case k times independently and reports a trimmed mean. | High session-to-session variation | k | Halawi et al. 2024 (trimmed-mean aggregation) |

**Generic comparator.** Every component at full dose for every configuration (C1 at rung 3 for every structure, C2 to C4 on). This stands in for an off-the-shelf debiasing preamble, as in Echterhoff et al. 2024 and Lyu et al. 2025. A literature generic, such as a BiasBuster-style self-help prompt, can be added as a fifth arm.

**Out of scope.** Fine-tuning (Bayesian teaching; program-based posterior training) changes the model rather than attaching to it.

## The adapter

**Format:** `epistemics.passport-adapter.v1`, a JSON document.

```json
{
  "schema_version": "epistemics.passport-adapter.v1",
  "subject": {"configuration_id": "configuration:<digest of model and effort>",
              "configuration": {"model": "gpt-6-sol", "reasoning_effort": "medium"}},
  "passport": {"guide_version": "reading-guide/0.8.0", "ledger_sha256": "<…>",
               "readings": ["check-relay", "check-disclosure"]},
  "generator": {"version": "passport-adapter/0.1.0", "implementation_sha256": "<…>"},
  "components": [
    {"id": "C1", "structure": "relay", "rung": 3, "reading": "check-relay",
     "text": "Some sources repeat another source's report instead of checking …"},
    {"id": "C1", "structure": "disclosure", "rung": 2, "reading": "check-disclosure",
     "text": "Some companies stay silent when their numbers are bad …"}
  ],
  "instructions": "<the preamble the components compile to>",
  "tools": [],
  "adapter_sha256": "<digest of everything above>"
}
```

- **Generation.** The adapter is a deterministic function of the configuration's passport readings and the generator version, so the same passport always gives the same adapter. Each component names the reading that triggered it, and the adapter is reproducible from the ledger.
- **Identity binding.** The subject is the configuration identity used elsewhere in the passport (`configuration:` plus the digest of the configuration). Issuer, subject, configuration and execution identities stay distinct (AGENTS.md).
  - A run records the adapter's digest in its plan, so every session can be traced to the adapter it ran with.
  - Attaching an adapter to a different configuration is possible, and that is the mismatched arm, but the record shows it.
- **Delivery.** The `instructions` are appended to the session's instructions. Tools (C2, C3) are exposed through the collection's MCP server.
  - The texts are general guidance about structures, never about a case, and never mention the evaluation or its answers.
  - Phase 1 is instructions only, with no tools.

## Evaluation (phase 1)

**Held-out cases: dossier set B.** Set A was used to build the structure-check recommendations, so the evaluation needs new cases: new companies, outlets, documents and case skeletons, in the same "unprompted" format (nothing in the brief names a mechanism). Each set-B dossier makes the structure **determinate from its documents** without naming it:

| Case type | Relay example | Disclosure example | Correct reading |
| --- | --- | --- | --- |
| Present, evident | The second outlet's story begins "According to Harbor Ledger…", or its profile says it has no reporters and republishes others' calls | The company's investor FAQ says its quarterly update reports only the indicators that met their targets | Copied (c = 1); selective (s = 1) |
| Absent, evident | The second outlet's profile and story show its own survey, with figures that differ from the first outlet's | The update follows an auditor's fixed template listing all four indicators; one is marked "not yet available: systems migration" | Independent (c = 0); random omission (s = 0) |
| No structure in play | Independent outlets, no relaying cues | Full disclosure | As stated |

- **Correct answers.** Because the structure is determinate, the correct posterior is computable exactly from the case's stated prior, records and reference rates. The task code's observers (`dispositions.observers.corroboration` and `.disclosure`) already compute it, with the prior that a source relays or is selective set to the case's 1 or 0.
- **Balance.** Present and absent cases are balanced. The absent cases are where a heavy-handed mitigation overcorrects, discounting an independent source or a complete update.

**Scores.**
- **Primary:** the mean absolute error of the forecast against the correct posterior, in log-odds, over a session's dossier cases.
- **Secondary:**
  - error on present and absent cases separately (absent-case error measures overcorrection);
  - Brier score against outcomes simulated from the case design;
  - the extra input tokens the adapter costs.

**Arms** (between sessions; each session takes one arm):

| Arm | Instructions |
| --- | --- |
| A. Alone | The standard instructions |
| B. Generic | Standard, plus every C1 check at rung 3 |
| C. **Passport adapter** | Standard, plus this configuration's adapter |
| D. Mismatched | Standard, plus the adapter of a pre-specified other configuration (the one whose rungs differ most from its own) |

**Configurations:** Astra, Sol, Luna and Terra at medium effort, the configurations with dossier structure checks. The effort variants have none, so they could join only after their own checks.

**Hypotheses for the preregistration**, written after the pilot:
- **M1 (primary):** for each configuration, the adapter lowers the error against arm A. This is tested per configuration and Holm-adjusted over the four, because the product claim is "this model plus its adapter".
- **M2:**
  - The adapter is not worse than the generic arm by more than a pre-specified margin, and it costs fewer tokens.
  - It is better than the generic arm on the absent cases, where overcorrection shows.
- **M3:** the adapter beats the mismatched arm (identity binding).

## Plan

1. **Build set B** (tasks 0.44.0): `corroboration-unprompted` and `disclosure-unprompted` set-B variants with determinate cases; their correct posteriors; an audit that every case is determinate and balanced; and validation on both seeds.
2. **Adapter generator** (`epistemics.passport.adapter`): readings in, adapter JSON out, deterministic, with tests. The runner gains an `adapter` field per run: the plan stores the digest, and the instructions append the adapter text. That part of the runner is covered by the fingerprint.
3. **Pilot.** Four configurations × four arms × two modules, one session each: 32 sessions, about 15 million input tokens. It estimates the effects and session variation for the power simulation and checks that set B is not at ceiling for arm A (the cases are not so evident that nobody neglects them).
4. **Power and preregistration**, committed before the main collection.
5. **Main collection.** Size to be set by the power simulation. At a guess, three sessions per cell: 96 sessions, about 45 million input tokens.
6. **Phase 2:** C2 (calculation tool) for Luna and Terra, C3 (record before wording), and C4 (aggregation), on tasks where those failures cost accuracy, with the same four arms.

## Risks

- **Too evident.** If set B's evidence is so plain that every configuration uses it unprompted, arm A has nothing to fix. The pilot checks this, and the evidence can be made less direct (a profile line rather than an attribution) before the preregistration.
- **Overcorrection.** The generic arm may lower errors on present cases and raise them on absent ones. The design measures this, and it is the main argument for tailoring.
- **Dose transfer.** The recommended rungs were measured with prompts inside the case. The adapter delivers them as instructions, so the dose may not transfer one to one. The pilot shows whether it does.
- **Session modes.** Luna's zero-weight sessions and Terra's variability add noise. Arms are compared over several sessions, and C4 targets this directly in phase 2.
- **Readout against belief.** All scores are on reported probabilities against correct posteriors. No claim is made about internal beliefs.

## Decisions

1. **Phase 1 scope:** structure checks only (recommended), or C2 to C4 as well.
2. **A literature generic arm** (a BiasBuster-style self-help prompt), alongside the full-dose generic. Recommended only if budget allows.
3. **Budget:** pilot about 15 million input tokens; main collection about 45 million at three sessions per cell, to be confirmed by the power simulation.

## Built (5 October 2026)

Decisions (user, "build it with the recommended defaults"): phase 1 is structure checks only, there is no literature generic arm, and the budget is the pilot first.

**Adapter generator:** `epistemics.passport.adapter` (passport-adapter/0.1.0).
- Command: `uv run python -m epistemics.passport.adapter --out src/epistemics/disposition_tasks/adapters`.
- It reads the ledger's structure checks and writes one adapter per configuration plus the generic comparator. Each is a JSON document whose digest covers its contents.
- The frozen adapters were generated from the ledger at reading guide 0.8.0.

| Adapter | Relay | Disclosure | Basis | Digest |
| --- | --- | --- | --- | --- |
| Astra | Rung 2 | Rung 3 | Relay recommended; disclosure check undetermined, so full dose | `02371ee8…` |
| Sol | Rung 3 | Rung 2 | Both recommended | `ce15c8d1…` |
| Luna | Rung 3 | Rung 3 | Both recommended | `e46c006b…` |
| Terra | Rung 3 | Rung 3 | Relay recommended; disclosure undetermined | `9d7ae8e5…` |
| Generic | Rung 3 | Rung 3 | Full dose for all | `0a9d9e03…` |

**The adapters are frozen into the task package** (`disposition_tasks/adapters/*.json`). The tasks fingerprint now covers them, so a session's implementation digest binds the exact adapter it ran with.

**The arm is the session's variant** (`alone`, `generic`, `adapter-<configuration>`). The instructions are the standard dossier instructions, plus the adapter's guidance for every arm except `alone`.

**Held-out modules:** `relay-evident` and `disclosure-evident` (design 0.32.0, tasks 0.44.0; `dispositions.evident`, `disposition_tasks.evident_texts`). They are new modules rather than a set-B variant of the unprompted dossiers, because the structure has to be determinate case by case.
- **Cases.** 24 per module with new companies and outlets: eight where the structure is evidently present, eight evidently absent, and eight controls.
- **Relay evidence.**
  - Present: an "According to …" story, or a profile saying the outlet has no reporters and republishes others' calls.
  - Absent: the outlet's own retailer survey.
  - Controls: a single call, or conflicting calls.
- **Disclosure evidence.**
  - Present: an investor FAQ saying updates report only indicators that met target, or a record of withheld indicators later shown below target.
  - Absent: an auditor's fixed template, where gaps mean late data. Nothing below target is shared, so a selective company could have sent the update. The audit caught a first version where this was not true, which would have made those cases uninformative about overcorrection.
  - Controls: complete updates.
- **Correct forecasts.** The observers with the structure's prior at 1 or 0. Ignoring a present structure costs 1.7 log-odds on relay cases and 2.2 on disclosure. Treating an absent one as present costs 1.7 and 1.65.
- **Session analysis.** Error by case type, plus the fitted structure use (present cases) and false structure (absent cases). Validation recovers both.

**Pilot preset** `adapter-pilot`: Astra, Sol, Luna and Terra, each on both modules in four arms. That is 32 sessions:
- alone;
- generic;
- its own adapter;
- the mismatched adapter: Astra gets Sol's, Sol gets Astra's, Luna gets Astra's and Terra gets Sol's (the adapter whose doses differ most, ties to the lighter dose).

Analysis: `uv run python -m epistemics.ledger adapter-eval <roots> --output <file>`.

**A limitation of phase 1.** Luna's and Terra's adapters give both structures the full dose, so their instructions are identical to the generic comparator's. For them, M2 (adapter against generic) is null by construction. M3 then tests whether a lighter dose (Astra's or Sol's adapter) would have done as well, which is a test of the passport's recommendation. The tailoring contrasts are informative for Astra and Sol, whose doses differ (relay 2 and disclosure 3 against relay 3 and disclosure 2). Phase 2's components (calculation, record before wording, aggregation) are where Luna's and Terra's adapters would diverge from generic.

**Task validation 0.44** passed on both seeds (4,944 cases, 201 contexts; evident-structure recovery error 0.00–0.05). Fingerprint `bb256033b80e4bc9b95bced64ed8c4a1fce6433a718ce4451965b38571f732e3`.

| Seed | SHA-256 |
| --- | --- |
| 20260927 | `6a14c2eb…` |
| 20261027 | `9e20c01d…` |
