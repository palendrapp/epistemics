import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.company.models import CompanyReport, CompanyTrial
from epistemics.company.simulation import answer_trial


def test_company_battery_over_real_mcp_stdio(tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.mcp_server"],
            env={**os.environ, "EPISTEMICS_DB": str(tmp_path / "mcp.sqlite3")},
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()

            async def call(name, arguments):
                result = await client.call_tool(name, arguments)
                assert not result.isError, result
                return result.structuredContent or json.loads(result.content[0].text)

            spec = await call("describe_battery", {"battery": "company"})
            assert spec["total_trials"] == 54
            started = await call(
                "start_evaluation",
                {
                    "battery": "company",
                    "agent": {
                        "agent_id": "test:company-mcp",
                        "model": "synthetic-public-client",
                        "model_version": "0.2.0",
                        "configuration_sha256": "0" * 64,
                    },
                },
            )
            session = {"session_id": started["session_id"]}
            assert "seed" not in started
            premature = await client.call_tool("finish_evaluation", session)
            assert premature.isError
            for _ in range(54):
                current = await call("get_trial", session)
                assert not current["complete"]
                trial = CompanyTrial.model_validate(current["trial"])
                request = {
                    **session,
                    "trial_id": trial.trial_id,
                    "answer": answer_trial(trial).model_dump(),
                }
                receipt = await call("submit_answer", request)
                assert receipt == await call("submit_answer", request)
                assert "outcome" not in receipt
            assert (await call("get_trial", session))["complete"]
            report = CompanyReport.model_validate(await call("finish_evaluation", session))
            assert len(report.observations) == 54
            assert all(m.reference_rmse < 1e-12 for m in report.metrics.values())
            assert report.model_fits["weighted_evidence"].identified

    asyncio.run(run())
