"""Benchmark stage gate in front of the public sequential collector."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from epistemics.benchmark.store import guard
from epistemics.predictive.collection import CollectionService
from epistemics.predictive.models import Response


def create_server(directory, configuration_id, assignment_id):
    service = CollectionService(Path(directory) / "collections" / configuration_id, assignment_id)

    def check():
        guard(directory, configuration_id, assignment_id)

    @asynccontextmanager
    async def lifespan(server):
        check()
        attempt = service.begin_attempt()
        failed = True
        try:
            yield {}
            failed = False
        finally:
            service.end_attempt(attempt, failed=failed)

    server = FastMCP("Company assessment episode", lifespan=lifespan)

    @server.tool()
    def describe_battery() -> dict:
        """Read the public instructions and response contract."""
        check()
        return service.describe()

    @server.tool()
    def get_trial() -> dict:
        """Read the current checkpoint and accepted public history."""
        check()
        return service.get_trial()

    @server.tool()
    def submit_answer(checkpoint_id: str, answer: Response) -> dict:
        """Submit an immutable answer; identical retries return the original receipt."""
        check()
        return service.submit(checkpoint_id, answer)

    @server.tool()
    def finish_evaluation() -> dict:
        """Finish the episode without evaluator feedback."""
        check()
        return service.finish()

    return server


if __name__ == "__main__":
    create_server(
        os.environ["EPISTEMICS_BENCHMARK"],
        os.environ["EPISTEMICS_CONFIGURATION"],
        os.environ["EPISTEMICS_ASSIGNMENT"],
    ).run(transport="stdio")
