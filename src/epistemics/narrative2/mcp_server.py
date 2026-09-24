import os

from mcp.server.fastmcp import FastMCP

from epistemics.narrative2.models import Answer
from epistemics.narrative2.service import NarrativeService


def create_server(directory, assignment_id):
    service = NarrativeService(directory, assignment_id)
    server = FastMCP(
        "Epistemics narrative inference 0.2", instructions=service.describe()["instructions"]
    )

    @server.tool()
    def describe_battery() -> dict:
        """Read the public protocol and answer contract."""
        return service.describe()

    @server.tool()
    def get_trial() -> dict:
        """Read only the current checkpoint."""
        return service.get_trial()

    @server.tool()
    def get_history() -> dict:
        """Restore this case's accepted public history."""
        return service.get_history()

    @server.tool()
    def submit_answer(trial_id: str, answer: Answer) -> dict:
        """Submit one immutable report; identical retries return the same receipt."""
        return service.submit(trial_id, answer)

    @server.tool()
    def finish_evaluation() -> dict:
        """Finish the case without revealing evaluator analysis or future cases."""
        return service.finish()

    return server


if __name__ == "__main__":
    create_server(os.environ["EPISTEMICS_NARRATIVE2"], os.environ["EPISTEMICS_ASSIGNMENT"]).run(
        transport="stdio"
    )
