import asyncio
import json

from mcp import ClientSession
from mcp.client.stdio import stdio_client
from test_investigation import PARTICIPANT, response

from epistemics.investigation.cli import server_parameters
from epistemics.investigation.models import InvestigationTrial
from epistemics.investigation.service import create


def test_investigation_through_real_stdio_mcp(tmp_path):
    directory = tmp_path / "collection"
    manifest = create(directory, PARTICIPANT, episodes=1, seed=11, synthetic=True)

    async def run():
        async with (
            stdio_client(server_parameters(directory, manifest.assignments[0].assignment_id)) as (
                read,
                write,
            ),
            ClientSession(read, write) as client,
        ):
            await client.initialize()
            tools = {t.name: t for t in (await client.list_tools()).tools}
            assert set(tools) == {
                "describe_battery",
                "get_trial",
                "get_history",
                "submit_answer",
                "finish_evaluation",
            }
            assert set(tools["submit_answer"].inputSchema["properties"]) == {"trial_id", "answer"}

            async def call(name, args=None):
                result = await client.call_tool(name, args or {})
                assert not result.isError, result
                return json.loads(result.content[0].text)

            assert (await call("describe_battery"))["mode"] == "discovery"
            assert (await client.call_tool("finish_evaluation", {})).isError
            for i in range(4):
                trial = InvestigationTrial.model_validate((await call("get_trial"))["trial"])
                assert trial.index == i
                request = {
                    "trial_id": trial.trial_id,
                    "answer": response(trial, "segment_check").model_dump(),
                }
                receipt = await call("submit_answer", request)
                assert receipt == await call("submit_answer", request)
            assert len((await call("get_history"))["history"]) == 4
            receipt = await call("finish_evaluation")
            assert receipt == await call("finish_evaluation")
            assert set(receipt) == {"complete", "answered", "report_stored"}

    asyncio.run(run())
