import asyncio
import hashlib
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from test_live import AGENT, response

from epistemics.live.models import CoreReport
from epistemics.passport.build import verify_derivation
from epistemics.passport.models import read_passport


def test_shared_core_over_real_stdio(tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.live.mcp_server"],
            env={
                **os.environ,
                "EPISTEMICS_LIVE_DB": str(tmp_path / "mcp.db"),
                "EPISTEMICS_SYNTHETIC_RESPONSES": "1",
            },
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            tools = {t.name: t for t in (await client.list_tools()).tools}
            assert set(tools) == {
                "describe_battery",
                "start_evaluation",
                "get_trial",
                "submit_answer",
                "finish_evaluation",
            }
            start_properties = tools["start_evaluation"].inputSchema["properties"]
            assert set(start_properties) == {
                "participant",
                "request_id",
                "instructions_accepted",
                "conditions",
            }

            async def call(name, args=None):
                result = await client.call_tool(name, args or {})
                assert not result.isError, result
                return json.loads(result.content[0].text)

            protocol = await call("describe_battery")
            assert protocol["total_trials"] == 34
            request = {
                "participant": AGENT,
                "request_id": "mcp-core-start-id-001",
                "instructions_accepted": True,
                "conditions": {"tools": [], "assistance": []},
            }
            receipt = await call("start_evaluation", request)
            assert await call("start_evaluation", request) == receipt
            session = {"session_id": receipt["session_id"]}
            assert (await client.call_tool("finish_evaluation", session)).isError
            for index in range(34):
                current = await call("get_trial", session)
                assert current["answered"] == index
                assert current["context"]["conditions"]["interface"] == "mcp"
                assert (
                    current["context"]["conditions"]["instructions_sha256"]
                    == protocol["instructions_sha256"]
                )
                trial = current["trial"]
                submission = session | {"trial_id": trial["trial_id"], "answer": response(trial)}
                result = await call("submit_answer", submission)
                assert await call("submit_answer", submission) == result
            finished = await call("finish_evaluation", session)
            raw = finished["report_json"].encode()
            report = CoreReport.model_validate_json(raw)
            assert report.model_dump(mode="json") == finished["report"]
            assert report.context.response_origin == "synthetic"
            assert report.context.participant.kind == "agent"
            passport = read_passport(json.dumps(finished["passport"]).encode())
            assert passport.source.sha256 == hashlib.sha256(raw).hexdigest()
            verify_derivation(passport, raw)
            assert await call("finish_evaluation", session) == finished

    asyncio.run(run())
