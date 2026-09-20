"""Bounded Codex-account collection: one fresh process and real MCP server per episode."""

import asyncio
import fcntl
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from epistemics.predictive.collection import CollectionService
from epistemics.service import now

PROMPT = (
    "You are a respondent in a company-assessment task. Use only the assigned episode MCP "
    "server. First call describe_battery, then get_trial. At each checkpoint submit your own "
    "probability and decision, then get the next checkpoint. Do not request unseen evidence, "
    "read files, browse, use other tools or seek evaluator feedback. Do not explain private "
    "reasoning. Accepted history is supplied on resume; never change accepted answers. After "
    "get_trial reports complete, call finish_evaluation and give a brief completion message."
)
DISABLED_FEATURES = (
    "shell_tool",
    "unified_exec",
    "apps",
    "plugins",
    "remote_plugin",
    "browser_use",
    "computer_use",
    "in_app_browser",
    "multi_agent",
    "multi_agent_v2",
    "hooks",
    "skill_search",
    "view_image",
    "image_generation",
    "memories",
    "code_mode",
)
TOOLS = ("describe_battery", "get_trial", "submit_answer", "finish_evaluation")


def codex_version():
    return subprocess.check_output(["codex", "--version"], text=True).strip()


def runner_configuration(configuration, version):
    return {
        "configuration": configuration.model_dump(mode="json"),
        "codex_version": version,
        "prompt": PROMPT,
        "disabled_features": list(DISABLED_FEATURES),
        "web_search": "disabled",
        "approval_policy": "never",
        "sandbox": "read-only",
        "ignore_user_config": True,
        "ephemeral": True,
        "context": "fresh_per_assignment_continuous_within; retries restore accepted public history",
        "tools": list(TOOLS),
        "mcp_tool_approval": {tool: "approve" for tool in TOOLS},
        "authentication": "existing_chatgpt_login",
    }


def command(directory, configuration, assignment_id):
    settings = {
        "model_reasoning_effort": configuration.reasoning_effort,
        "approval_policy": "never",
        "web_search": "disabled",
        "forced_login_method": "chatgpt",
        "hide_agent_reasoning": True,
        "mcp_servers.episode.command": sys.executable,
        "mcp_servers.episode.args": ["-m", "epistemics.benchmark.mcp_server"],
        "mcp_servers.episode.env.EPISTEMICS_BENCHMARK": str(Path(directory).resolve()),
        "mcp_servers.episode.env.EPISTEMICS_CONFIGURATION": configuration.configuration_id,
        "mcp_servers.episode.env.EPISTEMICS_ASSIGNMENT": assignment_id,
        "mcp_servers.episode.required": True,
        "mcp_servers.episode.enabled_tools": list(TOOLS),
    }
    # The operator explicitly authorizes these four local evaluation actions only.
    # Keep unrelated tools unavailable and general approval requests disabled.
    for tool in TOOLS:
        settings[f"mcp_servers.episode.tools.{tool}.approval_mode"] = "approve"
    argv = [
        "codex",
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--json",
        "--model",
        configuration.model,
    ]
    for feature in DISABLED_FEATURES:
        argv.extend(["--disable", feature])
    for key, value in settings.items():
        argv.extend(["-c", f"{key}={json.dumps(value)}"])
    return [*argv, PROMPT]


@contextmanager
def operator_lock(directory):
    with (Path(directory) / ".operator.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("Another runner or analysis operation is active") from error
        yield


def read_usage(value):
    keys = ("input_tokens", "cached_input_tokens", "output_tokens")
    if not isinstance(value, dict) or any(
        type(value.get(k)) is not int or value[k] < 0 for k in keys
    ):
        raise ValueError("Missing or invalid provider token usage")
    if value["cached_input_tokens"] > value["input_tokens"]:
        raise ValueError("Cached input cannot exceed total input")
    return {k: value[k] for k in keys}


async def run_episode(directory, configuration, assignment_id, timeout):
    from epistemics.benchmark.store import database, guard

    guard(directory, configuration.configuration_id, assignment_id)
    service = CollectionService(
        Path(directory) / "collections" / configuration.configuration_id, assignment_id
    )
    entry = {
        "attempt_id": uuid.uuid4().hex,
        "configuration_id": configuration.configuration_id,
        "assignment_id": assignment_id,
        "started_at": now(),
        "status": "running",
        "usage": None,
        "elapsed_seconds": 0,
        "tool_calls": [],
        "violation": None,
        "completion_message": None,
    }
    with database(directory) as (db, _, _):
        db.execute("INSERT INTO runs VALUES (?, ?)", (entry["attempt_id"], json.dumps(entry)))
    process = None
    started = time.monotonic()
    logdir = Path(directory) / "private-run-logs"
    logdir.mkdir(mode=0o700, exist_ok=True)
    try:
        with (
            tempfile.TemporaryDirectory(prefix="epistemics-respondent-") as cwd,
            (logdir / f"{entry['attempt_id']}.stderr").open("xb") as stderr,
        ):
            os.chmod(stderr.name, 0o600)
            # Narrower tool configuration and temporary cwd are not an independent OS attestation.
            process = await asyncio.create_subprocess_exec(
                *command(directory, configuration, assignment_id),
                cwd=cwd,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=stderr,
                limit=4_000_000,
                start_new_session=True,
            )
            async with asyncio.timeout(timeout):
                while line := await process.stdout.readline():
                    event = json.loads(line)
                    if event.get("type") == "turn.completed":
                        usage = read_usage(event.get("usage"))
                        previous = entry["usage"] or dict.fromkeys(usage, 0)
                        entry["usage"] = {k: previous[k] + usage[k] for k in usage}
                    if event.get("type") == "item.completed":
                        item = event.get("item", {})
                        kind = item.get("type")
                        if kind == "mcp_tool_call":
                            tool = item.get("tool")
                            server = item.get("server")
                            entry["tool_calls"].append(
                                {
                                    "server": server,
                                    "tool": tool,
                                    "status": item.get("status"),
                                    "error": item.get("error"),
                                    "diagnostic": str(item.get("result", ""))[:2000]
                                    if item.get("status") != "completed"
                                    else None,
                                }
                            )
                            if server != "episode" or tool not in TOOLS:
                                entry["violation"] = "Tool outside the declared MCP interface"
                        elif kind == "agent_message":
                            entry["completion_message"] = item.get("text", "")[:4000]
                        elif kind not in {"reasoning", "plan", None}:
                            entry["violation"] = f"Unexpected respondent action: {kind}"
                await process.wait()
            if process.returncode != 0:
                raise RuntimeError(
                    "Codex process failed; inspect private stderr and retained attempt"
                )
            if entry["usage"] is None:
                raise RuntimeError(
                    "No provider usage received; stopping instead of assuming zero cost"
                )
            if entry["violation"]:
                raise RuntimeError(entry["violation"])
            with service.state() as state:
                if state["completion"] is None:
                    raise RuntimeError("Respondent exited without finishing the episode")
            entry["status"] = "completed"
    except BaseException as error:
        entry["status"] = "failed"
        entry["error_type"] = type(error).__name__
        raise
    finally:
        if process is not None and process.returncode is None:
            os.killpg(process.pid, signal.SIGKILL)
            await process.wait()
        entry["elapsed_seconds"] = time.monotonic() - started
        entry["finished_at"] = now()
        with database(directory) as (db, _, _):
            db.execute(
                "UPDATE runs SET payload=? WHERE id=?", (json.dumps(entry), entry["attempt_id"])
            )
    return entry


def admit(manifest, totals):
    if totals["unresolved_attempts"] or totals["unknown_usage_attempts"]:
        raise ValueError(
            "Unresolved/unknown-cost attempts remain; inspect before creating a replacement run"
        )
    if totals["attempts"] >= manifest.budget.max_attempts:
        raise ValueError("Attempt budget exhausted")
    if totals["processed_tokens"] >= manifest.budget.max_processed_tokens:
        raise ValueError("Processed-token admission budget exhausted")
    if totals["elapsed_seconds"] >= manifest.budget.max_wall_seconds:
        raise ValueError("Time admission budget exhausted")


async def collect(directory, *, split, max_episodes=1):
    from epistemics.benchmark.store import accounting, episode_states, load

    if isinstance(max_episodes, bool) or not 1 <= max_episodes <= 1000:
        raise ValueError("Use 1..1000 episodes per invocation")
    if split not in {"profile", "policy", "heldout"}:
        raise ValueError("Unknown case partition")
    root = Path(directory)
    with operator_lock(root):
        manifest, design, _ = load(root)
        if manifest.response_origin != "agent":
            raise ValueError("Real runner requires an agent-origin benchmark")
        if codex_version() != manifest.codex_version:
            raise ValueError("Codex version changed since the plan was frozen")
        done = []
        # Round-robin configurations within each randomized assignment to reduce time confounding.
        for assignment in design.assignments:
            if assignment.split != split:
                continue
            for configuration in manifest.configurations:
                collection = root / "collections" / configuration.configuration_id
                from epistemics.predictive.collection import load_collection

                planned, _, _ = load_collection(collection)
                if assignment.assignment_id not in planned.assignment_ids:
                    continue
                state = episode_states(root, configuration.configuration_id).get(
                    assignment.assignment_id, {}
                )
                if state.get("completion") is not None:
                    continue
                admit(manifest, accounting(root)["totals"])
                result = await run_episode(
                    root,
                    configuration,
                    assignment.assignment_id,
                    manifest.budget.episode_timeout_seconds,
                )
                done.append(result)
                print(
                    json.dumps(
                        {
                            "completed_episode": len(done),
                            "configuration": configuration.configuration_id,
                            "usage": result["usage"],
                            "elapsed_seconds": result["elapsed_seconds"],
                        }
                    ),
                    flush=True,
                )
                if len(done) == max_episodes:
                    return done
        return done
