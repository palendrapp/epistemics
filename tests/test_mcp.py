import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.baselines import answer_trial
from epistemics.models import Report, Trial


def test_full_battery_over_real_stdio(tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.mcp_server"],
            env={**os.environ, "EPISTEMICS_DB": str(tmp_path / "mcp.sqlite3")},
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == {
                "describe_battery",
                "start_evaluation",
                "get_trial",
                "submit_answer",
                "finish_evaluation",
            }

            async def call(name, args):
                result = await client.call_tool(name, args)
                assert not result.isError, result
                return json.loads(result.content[0].text)

            started = await call(
                "start_evaluation",
                {
                    "agent": {
                        "agent_id": "test:mcp",
                        "model": "reference",
                        "model_version": "v1",
                        "configuration_sha256": "0" * 64,
                    }
                },
            )
            session = {"session_id": started["session_id"]}
            invalid = await client.call_tool(
                "submit_answer", {**session, "trial_id": "t000", "answer": {"probability": 2}}
            )
            assert invalid.isError
            for _ in range(88):
                current = await call("get_trial", session)
                trial = Trial.model_validate(current["trial"])
                await call(
                    "submit_answer",
                    {
                        **session,
                        "trial_id": trial.trial_id,
                        "answer": answer_trial(trial).model_dump(),
                    },
                )
            assert (await call("get_trial", session))["complete"]
            report = Report.model_validate(await call("finish_evaluation", session))
            assert len(report.observations) == 88
            assert report.parameters["prior_weight"].estimate > 0.99

    asyncio.run(run())
