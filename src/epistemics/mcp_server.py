"""Local stdio MCP. Run the evaluator under a separate trust boundary for real studies."""

import os
from typing import Literal

from mcp.server.fastmcp import FastMCP

from epistemics.battery import BATTERY_SHA256, SPEC
from epistemics.company import battery as company_battery
from epistemics.company.models import CompanyAnswer
from epistemics.discovery import battery as discovery_battery
from epistemics.discovery.models import DiscoveryAnswer
from epistemics.models import AgentDescriptor, Answer
from epistemics.service import EvaluationService


def create_server(database: str | None = None) -> FastMCP:
    service = EvaluationService(
        database or os.getenv("EPISTEMICS_DB", ".epistemics/evaluations.sqlite3")
    )
    server = FastMCP(
        "Epistemics",
        instructions=(
            "Choose battery='belief' (original numeric tasks), 'company' (disclosed-model dossiers), "
            "or 'discovery' (source archives and company documents without disclosed likelihoods) "
            "in describe_battery and start_evaluation, then repeat get_trial and submit_answer. "
            "Report numeric probabilities honestly; finish_evaluation is available only after all trials. "
            "The session_id is a local bearer capability; keep it private."
        ),
    )

    @server.tool()
    def describe_battery(battery: Literal["belief", "company", "discovery"] = "belief") -> dict:
        """Describe the public protocol and assumptions, without seeds or answer keys."""
        if battery == "discovery":
            return {
                "specification": discovery_battery.SPEC,
                "battery_sha256": discovery_battery.battery_sha256(),
                "total_trials": 10,
            }
        if battery == "company":
            return {
                "specification": company_battery.SPEC,
                "battery_sha256": company_battery.battery_sha256(),
                "total_trials": 54,
            }
        return {"specification": SPEC, "battery_sha256": BATTERY_SHA256, "total_trials": 88}

    @server.tool()
    def start_evaluation(
        agent: AgentDescriptor, battery: Literal["belief", "company", "discovery"] = "belief"
    ) -> dict:
        """Start the selected battery. Record the actual model and configuration fingerprint."""
        return service.start(agent, battery=battery)

    @server.tool()
    def get_trial(session_id: str) -> dict:
        """Fetch the current trial; retries return the same trial until an answer is accepted."""
        return service.get_trial(session_id)

    @server.tool()
    def submit_answer(
        session_id: str, trial_id: str, answer: Answer | CompanyAnswer | DiscoveryAnswer
    ) -> dict:
        """Submit one immutable probability report. Exact retries are idempotent."""
        return service.submit(session_id, trial_id, answer)

    @server.tool()
    def finish_evaluation(session_id: str) -> dict:
        """After completion, obtain parameter fits and the full auditable transcript including seed."""
        return service.finish(session_id).model_dump(mode="json")

    return server


def main() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
