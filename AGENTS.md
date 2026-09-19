# Repository guidance

- Bootstrap with `uv sync --locked` and `pnpm install --frozen-lockfile`.
- Run `mise run check`, or its Ruff/pytest/`pnpm check` component commands.
- Keep scientific claims task-conditional. Cite primary papers and distinguish inspiration from replication.
- Do not interpret elicited probabilities as direct access to an agent's internal beliefs.
- Preserve evaluator-side seeds/truth during active sessions, immutable answers and idempotent retries.
- Changes to experimental behavior require battery/evaluator version review and parameter-recovery validation.
- Regenerate `schemas/report.v1.json` with `uv run epistemics schema` after changing the Pydantic report contract.
- Report hashes bind exact file bytes. Record signatures bind the specified versioned canonical payload and signature domain.
- Keep issuer identity, subject identity, configuration identity and execution verification distinct.
- Default tests are offline. Explicitly distinguish mocked RPC coverage from validator or live-network validation.
- Do not add credentials, evaluation databases, reports with private prompts, or generated dependency directories to Git.
