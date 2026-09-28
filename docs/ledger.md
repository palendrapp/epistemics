# Experiment ledger

Every number in a results doc should be reproducible from frozen artifacts by a versioned command. The ledger (`epistemics.ledger`, ledger/0.1.0) does that and feeds a private dashboard.

## Parts

- **Registry:** [`docs/experiments.json`](experiments.json), maintained by hand. It records each experiment's question, preregistered prediction, outcome, status, document and collection roots, plus the project's decision log and next steps. It holds no computed numbers.
- **Facts:** the plan, execution and per-run files of every root under `output/`. These give status, contexts completed, tool errors, token use and SHA-256 commitments.
- **Verified estimates:** for disposition collections. Each root's reports are re-verified and read in a subprocess using that root's own implementation snapshot, `output/<root>/implementation/src`, which checks exact bytes, reconstruction and recomputed analysis. Version-specific designs are therefore interpreted by the code that collected them. Tables are computed from those records with current, tested code: tie-aware ranks, retest differences, relative-judgement contrasts and per-description fits.
- **Passport so far:** per-configuration parameters pooled over verified contexts:
  - default priors;
  - value of certainty, and the share of checks priced at decision value;
  - evidence sensitivity and report noise;
  - learning;
  - description mappings, retest differences and the relative-judgement contrast.

## Commands

```bash
uv run python -m epistemics.ledger build
```

writes `output/ledger.json` (private, not in Git). The table commands print the tables used in the docs:

```bash
uv run python -m epistemics.ledger runs output/disposition-range-20260928
```

```bash
uv run python -m epistemics.ledger retest output/disposition-cues-20260928 output/disposition-cues-retest-20260928
```

```bash
uv run python -m epistemics.ledger contrast output/disposition-range-20260928
```

## Dashboard

The page is [`src/epistemics/ledger/assets/dashboard.html`](../src/epistemics/ledger/assets/dashboard.html). It reads `ledger.json` published alongside it and is hosted as a private claude.ai artifact: https://claude.ai/artifact/EsX4sqwbZ5eTKXFSo3Wbx8.

After each run:
1. Update the registry entry (outcome, status, next).
2. Rebuild the ledger.
3. Republish the page together with the new `ledger.json`.

The page never contains transcripts or prompts, only the summary figures that the docs already report.

## Tables regenerated so far

- Description-to-prior retest ([record](disposition-cues-acceptance-2026-09-28.md#retest)): matches the published table exactly.
- Relative-judgement contrast ([record](disposition-range-2026-09-28.md#results)): the first results table produced by the ledger rather than a scratch script.

Earlier tables were produced by scratch scripts. The ledger reproduces their inputs from the verified reports, and any discrepancy found when a doc is next revised will be recorded in that doc.
