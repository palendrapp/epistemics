"""Bound stdio adapter; no operator or prediction tools are exposed."""

import os

from mcp.server.fastmcp import FastMCP

from epistemics.source_compact.presentation import Answer
from epistemics.source_compact.service import CompactService


def create_server(directory):
    service = CompactService(directory)
    server = FastMCP(
        "Epistemics cost-aware verification 0.3 (compact)",
        instructions=service.describe()["instructions"],
    )

    @server.tool()
    def describe_battery() -> dict:
        """Read the protocol, constants and field definitions once. Keep one continuing context."""
        return service.describe()

    @server.tool()
    def get_trial() -> dict:
        """Read the checkpoint awaiting an answer; needed only to begin or to recover."""
        return service.get_trial()

    @server.tool()
    def get_history() -> dict:
        """Restore earlier checkpoints, accepted answers and resolved companies."""
        return service.get_history()

    @server.tool()
    def submit_answer(trial_id: str, answer: Answer) -> dict:
        """Commit one answer. The receipt includes next_trial. Identical retries are safe."""
        return service.submit(trial_id, answer)

    @server.tool()
    def finish_evaluation() -> dict:
        """Finish after all checkpoints; no private results or future evidence are returned."""
        return service.finish()

    return server


if __name__ == "__main__":
    create_server(os.environ["EPISTEMICS_SOURCE_COMPACT"]).run(transport="stdio")
