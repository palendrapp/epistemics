"""Transport-only JSON-lines bridge to real MCP stdio; supplies no respondent logic."""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def server_parameters(directory, assignment_id):
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "epistemics.predictive.mcp_server"],
        env={
            **os.environ,
            "EPISTEMICS_COLLECTION": str(Path(directory).resolve()),
            "EPISTEMICS_ASSIGNMENT": assignment_id,
        },
    )


async def call(client, name, args=None):
    result = await client.call_tool(name, args or {})
    if result.isError:
        raise ValueError(str(result.content))
    return result.structuredContent or json.loads(result.content[0].text)


async def interactive_client(directory, assignment_id):
    async with (
        stdio_client(server_parameters(directory, assignment_id)) as (read, write),
        ClientSession(read, write) as client,
    ):
        await client.initialize()
        print(
            json.dumps(
                {
                    "protocol": await call(client, "describe_battery"),
                    "tools": [t.model_dump(mode="json") for t in (await client.list_tools()).tools],
                }
            ),
            flush=True,
        )
        while line := await asyncio.to_thread(sys.stdin.readline):
            try:
                request = json.loads(line)
                if request.get("close"):
                    return
                value = await call(client, request["tool"], request.get("arguments", {}))
                print(json.dumps({"result": value}), flush=True)
            except (KeyError, ValueError, TypeError, AttributeError) as error:
                print(json.dumps({"error": str(error)}), flush=True)
