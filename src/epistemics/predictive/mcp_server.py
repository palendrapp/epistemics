"""Public MCP: one preassigned episode, no operator controls or feedback endpoints."""

import os
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from epistemics.predictive.collection import CollectionService
from epistemics.predictive.models import Response


def create_server(directory, assignment_id):
    service = CollectionService(directory, assignment_id)

    @asynccontextmanager
    async def lifespan(server):
        attempt_id = service.begin_attempt()
        failed = True
        try:
            yield {}
            failed = False
        finally:
            service.end_attempt(attempt_id, failed=failed)

    server = FastMCP("Epistemics company episode", lifespan=lifespan)

    @server.tool()
    def describe_battery() -> dict:
        """Read the public instructions and response contract."""
        return service.describe()

    @server.tool()
    def get_trial() -> dict:
        """Read the current checkpoint and previously accepted public history."""
        return service.get_trial()

    @server.tool()
    def submit_answer(checkpoint_id: str, answer: Response) -> dict:
        """Accept one immutable answer. Identical retries return the original receipt."""
        return service.submit(checkpoint_id, answer)

    @server.tool()
    def finish_evaluation() -> dict:
        """Finish after all answers; the receipt contains no evaluator feedback."""
        return service.finish()

    return server


def main():
    create_server(os.environ["EPISTEMICS_COLLECTION"], os.environ["EPISTEMICS_ASSIGNMENT"]).run(
        transport="stdio"
    )


if __name__ == "__main__":
    main()
