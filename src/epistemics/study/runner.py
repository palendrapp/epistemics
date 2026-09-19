"""Provider-neutral fresh-process respondent collection through real MCP stdio."""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.discovery.models import DiscoveryAnswer
from epistemics.service import now
from epistemics.study.design import digest, load_manifest
from epistemics.study.service import StudyService


async def call(client, name, args=None):
    result = await client.call_tool(name, args or {})
    if result.isError:
        raise ValueError(str(result.content))
    return result.structuredContent or json.loads(result.content[0].text)


def server_parameters(directory, assignment_id):
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "epistemics.study.mcp_server"],
        env={
            **os.environ,
            "EPISTEMICS_STUDY": str(Path(directory).resolve()),
            "EPISTEMICS_ASSIGNMENT": assignment_id,
        },
    )


async def interactive_client(directory, assignment_id):
    """Transport-only helper for a manually assigned fresh respondent; no answer logic."""
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
            request = json.loads(line)
            if request.get("close"):
                return
            try:
                value = await call(client, request["tool"], request.get("arguments", {}))
                print(json.dumps({"result": value}), flush=True)
            except (KeyError, ValueError) as error:
                print(json.dumps({"error": str(error)}), flush=True)


async def collect_episode(directory, assignment, command_spec, timeout=180):
    directory = Path(directory).resolve()
    service = StudyService(directory, assignment.assignment_id)
    with service.state() as state:
        if state["report"] is not None:
            return False
        # Resuming restores accepted public history; it never re-elicits accepted answers.
        history = [
            {"trial": service.records[i]["trial"], "answer": a["answer"]}
            for i, a in enumerate(state["answers"])
        ]
    command = command_spec["command"]
    if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
        raise ValueError("command must be a nonempty JSON argv list, not shell text")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONUNBUFFERED": "1"}
    for key in command_spec.get("pass_environment", []):
        if key.startswith("EPISTEMICS_"):
            raise ValueError("Evaluator environment cannot be passed to the respondent")
        if key in os.environ:
            env[key] = os.environ[key]
    attempts = directory / "attempts.jsonl"
    entry = {
        "assignment_id": assignment.assignment_id,
        "started_at": now(),
        "command_sha256": digest(json.dumps(command_spec, sort_keys=True).encode()),
        "restored_answers": len(history),
        "status": "running",
    }
    with attempts.open("a") as stream:
        stream.write(json.dumps(entry) + "\n")
    process = None
    try:
        with tempfile.TemporaryDirectory(prefix="epistemics-respondent-") as cwd:
            # This is context/process separation, not an OS security sandbox.
            with (directory / f"respondent-{assignment.assignment_id}.stderr").open("ab") as stderr:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=cwd,
                    env=env,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=stderr,
                    limit=1_000_000,
                )
                async with (
                    stdio_client(server_parameters(directory, assignment.assignment_id)) as (
                        read,
                        write,
                    ),
                    ClientSession(read, write) as client,
                ):
                    await client.initialize()

                    async def send(value):
                        process.stdin.write((json.dumps(value) + "\n").encode())
                        await process.stdin.drain()

                    await send(
                        {
                            "type": "start",
                            "protocol": await call(client, "describe_battery"),
                            "answer_schema": DiscoveryAnswer.model_json_schema(),
                            "history": history,
                        }
                    )
                    while not (current := await call(client, "get_trial"))["complete"]:
                        await send({"type": "trial", "trial": current["trial"]})
                        line = await asyncio.wait_for(process.stdout.readline(), timeout)
                        if not line:
                            raise RuntimeError(
                                "Respondent exited before answering the current trial"
                            )
                        response = json.loads(line)
                        answer = DiscoveryAnswer.model_validate(response["answer"])
                        receipt = await call(
                            client,
                            "submit_answer",
                            {
                                "trial_id": current["trial"]["trial_id"],
                                "answer": answer.model_dump(mode="json"),
                            },
                        )
                        await send({"type": "receipt", **receipt})
                    await send({"type": "complete", **await call(client, "finish_evaluation")})
                    process.stdin.close()
                    await asyncio.wait_for(process.wait(), 10)
                    if process.returncode != 0:
                        raise RuntimeError("Respondent exited unsuccessfully after completion")
        entry["status"] = "completed"
        return True
    except BaseException as error:
        entry["status"] = "failed"
        entry["error_type"] = type(error).__name__
        raise
    finally:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        entry["finished_at"] = now()
        with attempts.open("a") as stream:
            stream.write(json.dumps(entry) + "\n")


async def collect(directory, command_file, max_episodes=1, timeout=180):
    import fcntl

    directory = Path(directory)
    manifest, _ = load_manifest(directory)
    if manifest.response_origin != "agent":
        raise ValueError("The real respondent runner requires an agent-origin study")
    spec_bytes = Path(command_file).read_bytes()
    command = json.loads(spec_bytes)
    binding = directory / "respondent-command.sha256"
    with (directory / ".runner.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("Another collector is running this study") from error
        if binding.exists() and binding.read_text().strip() != digest(spec_bytes):
            raise ValueError("Respondent command changed within the study")
        binding.write_text(digest(spec_bytes) + "\n")
        completed = 0
        for assignment in manifest.assignments:
            if completed >= max_episodes:
                break
            completed += await collect_episode(directory, assignment, command, timeout)
        return completed
