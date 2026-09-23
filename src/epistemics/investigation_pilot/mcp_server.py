"""Case-bound transport with evaluator-side forecast commitments, hidden from respondents."""

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from epistemics.investigation3.models import Answer
from epistemics.investigation3.service import InvestigationService
from epistemics.investigation_pilot.prediction import ensure_prediction


def create_server(root, phase, assignment):
    root = Path(root)
    if phase not in ("development", "repeat", "new"):
        raise ValueError("Unknown pilot phase")
    service = InvestigationService(root / phase, assignment)
    server = FastMCP(
        "Epistemics investigation 0.3", instructions=service.describe()["instructions"]
    )

    @server.tool()
    def describe_battery() -> dict:
        """Read the public protocol and answer contract."""
        return service.describe()

    @server.tool()
    def get_history() -> dict:
        """Restore this assignment's accepted public history after an interruption."""
        return service.get_history()

    @server.tool()
    def get_trial() -> dict:
        """Read only the current checkpoint and evidence available there."""
        ensure_prediction(root, phase, service)
        return service.get_trial()

    @server.tool()
    def submit_answer(trial_id: str, answer: Answer) -> dict:
        """Submit an immutable answer and, at Evidence and research, one research choice."""
        ensure_prediction(root, phase, service)
        receipt = service.submit(trial_id, answer)
        ensure_prediction(root, phase, service)
        return receipt

    @server.tool()
    def finish_evaluation() -> dict:
        """Finish the assignment; private outcomes and analysis are withheld."""
        return service.finish()

    return server


if __name__ == "__main__":
    create_server(
        os.environ["EPISTEMICS_PILOT"],
        os.environ["EPISTEMICS_PHASE"],
        os.environ["EPISTEMICS_ASSIGNMENT"],
    ).run(transport="stdio")
