"""Public-only MCP interface; bound profiles and operator tools remain private."""

import os

from mcp.server.fastmcp import FastMCP

from epistemics.source_learning.models import Answer
from epistemics.source_panel.service import PanelService


def create_server(directory):
    service = PanelService(directory)
    server = FastMCP("Epistemics source panel 0.1", instructions=service.describe()["instructions"])

    @server.tool()
    def describe_battery() -> dict:
        """Read the public instructions and response contract."""
        return service.describe()

    @server.tool()
    def get_trial() -> dict:
        """Read the current company checkpoint."""
        return service.get_trial()

    @server.tool()
    def get_history() -> dict:
        """Restore already accepted public evidence, answers and resolutions."""
        return service.get_history()

    @server.tool()
    def submit_answer(trial_id: str, answer: Answer) -> dict:
        """Commit the current answer. Identical retries return the original receipt."""
        return service.submit(trial_id, answer)

    @server.tool()
    def finish_evaluation() -> dict:
        """Finish only after all checkpoints; returns no evaluator model feedback."""
        return service.finish()

    return server


if __name__ == "__main__":
    create_server(os.environ["EPISTEMICS_SOURCE_PANEL"]).run(transport="stdio")
