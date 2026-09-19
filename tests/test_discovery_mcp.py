import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.discovery.models import DiscoveryReport, DiscoveryTrial
from epistemics.discovery.simulation import answer_trial


def test_complete_discovery_session_through_mcp(tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.mcp_server"],
            env={**os.environ, "EPISTEMICS_DB": str(tmp_path / "discovery.sqlite3")},
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()

            async def call(name, args):
                r = await client.call_tool(name, args)
                assert not r.isError, r
                return r.structuredContent or json.loads(r.content[0].text)

            described = await call("describe_battery", {"battery": "discovery"})
            assert described["total_trials"] == 10
            assert "source_parameters" not in json.dumps(described)
            started = await call(
                "start_evaluation",
                {
                    "battery": "discovery",
                    "agent": {
                        "agent_id": "test:discovery-mcp",
                        "model": "synthetic-public-observer",
                        "model_version": "0.3.0",
                        "configuration_sha256": "0" * 64,
                    },
                },
            )
            session = {"session_id": started["session_id"]}
            assert (await client.call_tool("finish_evaluation", session)).isError
            for _ in range(10):
                current = await call("get_trial", session)
                assert not current["complete"]
                t = DiscoveryTrial.model_validate(current["trial"])
                request = {
                    **session,
                    "trial_id": t.trial_id,
                    "answer": answer_trial(t).model_dump(),
                }
                receipt = await call("submit_answer", request)
                assert receipt == await call("submit_answer", request)
                assert "outcome" not in receipt
            assert (await call("get_trial", session))["complete"]
            report = DiscoveryReport.model_validate(await call("finish_evaluation", session))
            assert report.observer_models["joint_learning"].growth_report_rmse < 1e-12
            assert report.metrics["decision_report_agreement"] == 1

    asyncio.run(run())
