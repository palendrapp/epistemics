# Development

Bootstrap with `mise install` and `mise run setup`. Run `mise run check` before sharing changes. The checks use Ruff, pytest, TypeScript, Biome and Node's test runner. No real model or wallet credentials are required.

Keep the evaluator independent of chain availability. New tasks need a generative specification, analytic/reference behavior, a recovery test that can detect a wrong implementation, and a statement of identifiability limits. Separate task performance, fit to reported probabilities, and claims about cognition.

The battery fingerprint includes its specification and the source bytes of `battery.py`, `analysis.py`, and `models.py`. Version the battery and evaluator when experiment behavior changes. Preserve the original environment for unfinished sessions; finishing a session under a changed fingerprint is rejected.

After modifying report models, run `uv run epistemics schema`. Keep Python and TypeScript schema interoperability tests passing. Reports and record payloads have different serialization rules: report commitments hash exact file bytes, while the string/null record payload has a specified canonical encoding.

Chain operations belong in `packages/solana`. Never conflate simulation, submission, confirmation and finality. Keep live-chain and funded-key tests opt-in; the default suite mocks RPC transport. A real devnet smoke run must verify the published record from its transaction signature after finalization.

Useful optional checks: `actionlint`, `gitleaks dir .`, and `osv-scanner scan source -r .`. Avoid checking generated environments/dependency trees into Git. The public repository is `palendrapp/epistemics`; no open-source license has been selected yet. See [development history](docs/development-history.md) for the provenance of the initial commit sequence.
