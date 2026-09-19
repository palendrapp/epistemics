"""MCP server bound by its operator to one immutable study assignment."""

import os

from mcp.server.fastmcp import FastMCP

from epistemics.discovery.models import DiscoveryAnswer
from epistemics.study.service import StudyService


def create_server(directory, assignment_id):
    service = StudyService(directory, assignment_id)
    server = FastMCP("Epistemics discovery study", instructions=service.describe()["instructions"])

    @server.tool()
    def describe_battery() -> dict:
        """Read the public study episode protocol."""
        return service.describe()

    @server.tool()
    def get_trial() -> dict:
        """Read only the current trial; no evaluator controls are exposed."""
        return service.get_trial()

    @server.tool()
    def submit_answer(trial_id: str, answer: DiscoveryAnswer) -> dict:
        """Submit an immutable answer; exact retries return the original receipt."""
        return service.submit(trial_id, answer)

    @server.tool()
    def finish_evaluation() -> dict:
        """Store the finished episode. Outcomes remain withheld during the study."""
        return service.finish()

    return server


def main():
    create_server(os.environ["EPISTEMICS_STUDY"], os.environ["EPISTEMICS_ASSIGNMENT"]).run(
        transport="stdio"
    )


if __name__ == "__main__":
    main()
