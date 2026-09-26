"""Bound stdio adapter; no operator or prediction tools are exposed."""

import os

from mcp.server.fastmcp import FastMCP

from epistemics.source_verification.presentation import Answer
from epistemics.source_verification.service import VerificationService


def create_server(directory):
    service = VerificationService(directory)
    server = FastMCP(
        "Epistemics assigned verification 0.1", instructions=service.describe()["instructions"]
    )

    @server.tool()
    def describe_battery() -> dict:
        """Read the public protocol and answer contract. Keep one continuing context."""
        return service.describe()

    @server.tool()
    def get_trial() -> dict:
        """Read the current checkpoint; evaluator predictions are frozen before it is returned."""
        return service.get_trial()

    @server.tool()
    def get_history() -> dict:
        """Restore accepted public history, including already resolved companies."""
        return service.get_history()

    @server.tool()
    def submit_answer(trial_id: str, answer: Answer) -> dict:
        """Commit one answer. Identical retries return the original receipt."""
        return service.submit(trial_id, answer)

    @server.tool()
    def finish_evaluation() -> dict:
        """Finish after all checkpoints; no private results or future evidence are returned."""
        return service.finish()

    return server


if __name__ == "__main__":
    create_server(os.environ["EPISTEMICS_SOURCE_VERIFICATION"]).run(transport="stdio")
