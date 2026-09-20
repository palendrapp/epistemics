"""Public MCP bound to one operator-selected development assignment."""

import os

from mcp.server.fastmcp import FastMCP

from epistemics.investigation.models import InvestigationAnswer
from epistemics.investigation.service import InvestigationService


def create_server(directory, assignment_id):
    service = InvestigationService(directory, assignment_id)
    server = FastMCP(
        "Epistemics company investigation", instructions=service.describe()["instructions"]
    )

    @server.tool()
    def describe_battery() -> dict:
        """Read the public protocol and answer contract."""
        return service.describe()

    @server.tool()
    def get_trial() -> dict:
        """Read only the current checkpoint and the evidence available there."""
        return service.get_trial()

    @server.tool()
    def get_history() -> dict:
        """Restore this assignment's accepted public history after an interruption."""
        return service.get_history()

    @server.tool()
    def submit_answer(trial_id: str, answer: InvestigationAnswer) -> dict:
        """Submit an immutable answer and, at checkpoint 1, one research choice."""
        return service.submit(trial_id, answer)

    @server.tool()
    def finish_evaluation() -> dict:
        """Finish the assignment; private outcomes and analysis are withheld."""
        return service.finish()

    return server


def main():
    create_server(os.environ["EPISTEMICS_INVESTIGATION"], os.environ["EPISTEMICS_ASSIGNMENT"]).run(
        transport="stdio"
    )


if __name__ == "__main__":
    main()
