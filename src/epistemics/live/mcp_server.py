"""Core stdio MCP adapter, using the same service as the human interface."""

import json
import os

from mcp.server.fastmcp import FastMCP

from epistemics.discovery.models import DiscoveryAnswer
from epistemics.live.service import LiveService
from epistemics.models import Answer
from epistemics.participants import AgentParticipant, EvaluationConditions


def create_server(database=None, *, synthetic=False):
    service = LiveService(database or os.getenv("EPISTEMICS_LIVE_DB", ".epistemics/live.sqlite3"))
    server = FastMCP(
        "Epistemics Passport Core",
        instructions=(
            "Read describe_battery, including the shared instructions and practice example. "
            "Start with actual participant/configuration metadata, a random request_id, and instructions_accepted=true. "
            "Complete the 34 checkpoints in one continuous session. Discovery comes before calibration. "
            "Use payload instructions and the appropriate answer schema; probabilities are in [0,1]. "
            "Accepted answers are immutable. get_trial includes your accepted answer history for resume. "
            "Keep session_id private. finish_evaluation reveals outcomes and the draft passport only after all answers."
        ),
    )

    @server.tool()
    def describe_battery() -> dict:
        """Read the exact shared core protocol, instructions and unscored practice example."""
        return service.describe()

    @server.tool()
    def start_evaluation(
        participant: AgentParticipant,
        request_id: str,
        instructions_accepted: bool,
        conditions: EvaluationConditions | None = None,
    ) -> dict:
        """Start idempotently. No public seed, outcome, variant or scoring controls are available."""
        conditions = conditions or EvaluationConditions()
        conditions.interface = "mcp"
        return service.start(
            participant,
            request_id=request_id,
            conditions=conditions,
            instructions_accepted=instructions_accepted,
            response_origin="synthetic" if synthetic else "agent",
        )

    @server.tool()
    def get_trial(session_id: str) -> dict:
        """Read current public materials, progress and your accepted answers; never future trials."""
        return service.get_trial(session_id)

    @server.tool()
    def submit_answer(session_id: str, trial_id: str, answer: Answer | DiscoveryAnswer) -> dict:
        """Submit the current answer. Identical retries return the original receipt."""
        return service.submit(session_id, trial_id, answer.model_dump())

    @server.tool()
    def finish_evaluation(session_id: str) -> dict:
        """After all 34 answers, return the report and draft passport; export endpoints preserve exact bytes."""
        raw = service.report_bytes(session_id)
        return {
            "report": json.loads(raw),
            "report_json": raw.decode(),
            "passport": json.loads(service.passport_bytes(session_id)),
        }

    return server


def main():
    synthetic = os.getenv("EPISTEMICS_SYNTHETIC_RESPONSES") == "1"
    create_server(synthetic=synthetic).run(transport="stdio")


if __name__ == "__main__":
    main()
