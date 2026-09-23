import asyncio
import json

from mcp import ClientSession
from mcp.client.stdio import stdio_client
from test_investigation3 import PARTICIPANT

from epistemics.investigation3.cli import server_parameters
from epistemics.investigation3.models import Trial
from epistemics.investigation3.service import create
from epistemics.investigation3.simulation import response


def test_v3_real_mcp_transport_and_prospective_expectations(tmp_path):
    directory = tmp_path / "collection"
    manifest = create(directory, PARTICIPANT, seed=219, synthetic=True)
    assignment = next(a for a in manifest.assignments if a.family == "research")

    async def run():
        async with (
            stdio_client(server_parameters(directory, assignment.assignment_id)) as (read, write),
            ClientSession(read, write) as client,
        ):
            await client.initialize()
            assert {t.name for t in (await client.list_tools()).tools} == {
                "describe_battery",
                "get_trial",
                "get_history",
                "submit_answer",
                "finish_evaluation",
            }
            assert (await client.call_tool("finish_evaluation", {})).isError

            async def call(name, args=None):
                r = await client.call_tool(name, args or {})
                assert not r.isError, r
                return json.loads(r.content[0].text)

            for i in range(4):
                t = Trial.model_validate((await call("get_trial"))["trial"])
                assert t.index == i
                data = {"trial_id": t.trial_id, "answer": response(t).model_dump()}
                receipt = await call("submit_answer", data)
                assert receipt == await call("submit_answer", data)
            assert (await call("finish_evaluation"))["report_stored"]
            assert len((await call("get_history"))["history"]) == 4

    asyncio.run(run())
