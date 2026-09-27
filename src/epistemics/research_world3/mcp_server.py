"""Bound stdio adapter; no operator, ledger or analysis tools are exposed."""

import os

from mcp.server.fastmcp import FastMCP

from epistemics.research_world3.collection import CollectionService
from epistemics.research_world3.presentation import Answer


def create_server(directory):
    service = CollectionService(directory)
    server = FastMCP(
        "Epistemics research dossiers 0.1", instructions=service.describe()["instructions"]
    )

    @server.tool()
    def describe_battery() -> dict:
        """Read the protocol once. Keep one continuing context."""
        return service.describe()

    @server.tool()
    def get_trial() -> dict:
        """Read the checkpoint awaiting an answer; needed only to begin or to recover."""
        return service.get_trial()

    @server.tool()
    def get_history() -> dict:
        """Restore earlier checkpoints and your accepted answers."""
        return service.get_history()

    @server.tool()
    def submit_answer(trial_id: str, answer: Answer) -> dict:
        """Commit one answer. The receipt includes next_trial. Identical retries are safe."""
        return service.submit(trial_id, answer)

    @server.tool()
    def finish_evaluation() -> dict:
        """Finish after every case; no outcomes or private results are returned."""
        return service.finish()

    return server


if __name__ == "__main__":
    create_server(os.environ["EPISTEMICS_RESEARCH_WORLD3"]).run(transport="stdio")
