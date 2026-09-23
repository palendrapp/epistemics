"""Bounded 36-episode prospective pilot using fresh Codex processes and a frozen evaluator."""

import asyncio
import json
import os
import random
import secrets
import shutil
import signal
import sys
import tempfile
import time
from pathlib import Path

from epistemics.benchmark.runner import DISABLED_FEATURES, codex_version, read_usage
from epistemics.investigation3.service import (
    InvestigationService,
    create,
    digest,
    encoded,
    export,
    fingerprint,
    write_private,
)
from epistemics.investigation_pilot.prediction import commit, freeze_models, pilot_fingerprint
from epistemics.service import now

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
REPO = Path(__file__).resolve().parents[3]
COLLECTION = None
PHASE = None

TOOLS = ["describe_battery", "get_history", "get_trial", "submit_answer", "finish_evaluation"]
PROMPT = (
    "You are a fresh respondent in a company-investigation task. Use only the assigned episode "
    "MCP tools. First call describe_battery and get_history. Then read get_trial, submit your "
    "own probabilities and decision for the current checkpoint, and continue through all four "
    "checkpoints. Follow the public protocol about the research choice, including requested "
    "research expectations. Accepted answers cannot "
    "be changed; restore accepted public history if it exists and continue from the current trial. "
    "Do not read files, browse, inspect evaluator code, use other tools or request future trials "
    "or evaluator feedback. An optional explanation may be a brief decision summary; do not "
    "disclose private chain-of-thought. After get_trial reports complete, call finish_evaluation. "
    "Finally give a brief completion message and describe any confusing instructions or interface "
    "friction. Do not guess what cognitive labels the evaluator might assign."
)
EXTRA_DISABLED = [
    "browser_use_external",
    "browser_use_full_cdp_access",
    "goals",
    "sleep_tool",
    "tool_suggest",
    "workspace_dependencies",
    "unbounded_connection_retries",
]


def prepare():
    ROOT.mkdir(parents=True, mode=0o700, exist_ok=False)
    snapshot = ROOT / "implementation" / "src"
    snapshot.mkdir(parents=True, mode=0o700)
    for source in (REPO / "src").rglob("*"):
        if not source.is_file() or not (source.suffix == ".py" or "assets" in source.parts):
            continue
        target = snapshot / source.relative_to(REPO / "src")
        target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o600)
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(REPO / name, ROOT / "implementation" / name)
        (ROOT / "implementation" / name).chmod(0o600)
    import subprocess

    env = {**os.environ, "PYTHONPATH": str(snapshot)}
    frozen = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "from epistemics.investigation3.service import fingerprint; print(fingerprint())",
        ],
        env=env,
        cwd=ROOT,
        text=True,
    ).strip()
    if frozen != fingerprint():
        raise ValueError("Snapshot fingerprint mismatch")
    configuration = {
        "model": "gpt-6-astra",
        "reasoning_effort": "medium",
        "model_revision": "unverified_requested_alias",
        "temperature": None,
        "codex_version": codex_version(),
        "prompt": PROMPT,
        "disabled_features": list(DISABLED_FEATURES) + EXTRA_DISABLED,
        "enabled_features": ["skip_host_skill_discovery", "code_mode_host"],
        "tools": TOOLS,
        "mcp_tool_approval": {tool: "approve" for tool in TOOLS},
        "approval_policy": "never",
        "web_search": "disabled",
        "sandbox": "read-only",
        "ignore_user_config": True,
        "ephemeral": True,
        "project_doc_max_bytes": 0,
        "context": "fresh_process_per_episode_continuous_within",
        "implementation_sha256": fingerprint(),
        "episodes": 36,
        "concurrency": 1,
        "collection_budget_seconds": 2700,
        "timeout_seconds_per_attempt": 600,
        "max_attempts_per_episode": 1,
        "authentication": "existing_chatgpt_login",
        "purpose": "prospective_repeatability_and_new_cases",
        "billing": "Provider token usage recorded; marginal dollar cost unknown.",
        "pilot_sha256": pilot_fingerprint(),
    }
    raw = encoded(configuration)
    write_private(ROOT / "configuration.json", raw)
    participant = {
        "kind": "agent",
        "subject_id": "codex:gpt-6-astra:investigation3-pilot-20260923",
        "configuration": {
            "model": "gpt-6-astra",
            "model_version": "unverified_requested_alias",
            "configuration_sha256": digest(raw),
            "temperature": None,
        },
    }
    write_private(ROOT / "participant.json", encoded(participant))
    dev_seed, new_seed = secrets.randbits(64), secrets.randbits(64)
    manifests = {
        phase: create(ROOT / phase, participant, seed=seed)
        for phase, seed in (("development", dev_seed), ("repeat", dev_seed), ("new", new_seed))
    }
    order = {phase: [a.assignment_id for a in m.assignments] for phase, m in manifests.items()}
    random.Random(dev_seed + 1).shuffle(order["repeat"])
    plan = {
        "created_at": now(),
        "configuration_sha256": digest(raw),
        "implementation_sha256": fingerprint(),
        "pilot_sha256": pilot_fingerprint(),
        "manifests": {
            phase: digest((ROOT / phase / "manifest.json").read_bytes()) for phase in manifests
        },
        "order": order,
        "phases": ["development", "repeat", "new"],
        "planned_episodes": 36,
        "budget_seconds": 2700,
        "max_attempts_per_episode": 1,
        "analysis": {
            "fit": "Three initialization alternatives fitted on development only; grid maximum likelihood parameters locked before repeat/new",
            "comparators": [
                "fitted_working_prior",
                "fitted_hard_report",
                "fitted_noisy_report",
                "fixed_joint",
                "fixed_cut",
                "persistence",
            ],
            "forecast_lock": "After first accepted answer, before any later answer; all five query branches; predictions conditional on later public stimuli and pre-sampled result",
            "metrics": [
                "RMSE of predictive mean",
                "joint episode log score divided by report count",
                "same-case early-report RMSE",
                "research-choice repeat agreement",
            ],
            "diagnostics": "1000 draws per episode/model/branch from frozen rounded-report predictive distribution; central 95% RMSE and log-score reference ranges; exploratory cluster bootstrap 2000 resamples of whole worlds",
            "release": "Descriptive pilot; no pass threshold, model selection, individualized superiority or automatic validated trait. Report all cases, losses and exceptions. No intervention test.",
        },
        "interpretation": "Operator-created precollection commitment, not independent preregistration or execution attestation.",
    }
    commit(ROOT / "run-manifest.json", plan)
    return configuration, manifests, order


def command(config, assignment_id):
    settings = {
        "model_reasoning_effort": config["reasoning_effort"],
        "approval_policy": "never",
        "web_search": "disabled",
        "forced_login_method": "chatgpt",
        "hide_agent_reasoning": True,
        "project_doc_max_bytes": 0,
        "mcp_servers.episode.command": sys.executable,
        "mcp_servers.episode.args": ["-m", "epistemics.investigation_pilot.mcp_server"],
        "mcp_servers.episode.env.EPISTEMICS_PILOT": str(ROOT),
        "mcp_servers.episode.env.EPISTEMICS_PHASE": PHASE,
        "mcp_servers.episode.env.EPISTEMICS_ASSIGNMENT": assignment_id,
        "mcp_servers.episode.env.PYTHONPATH": str(ROOT / "implementation/src"),
        "mcp_servers.episode.required": True,
        "mcp_servers.episode.enabled_tools": TOOLS,
    }
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
        config["model"],
        "--enable",
        "skip_host_skill_discovery",
        "--enable",
        "code_mode_host",
    ]
    for feature in config["disabled_features"]:
        argv.extend(["--disable", feature])
    for key, value in settings.items():
        argv.extend(["-c", f"{key}={json.dumps(value)}"])
    return [*argv, PROMPT]


async def run_episode(config, assignment, ordinal):
    entry = {
        "ordinal": ordinal,
        "phase": PHASE,
        "assignment_id": assignment.assignment_id,
        "started_at": now(),
        "status": "running",
        "usage": None,
        "tools": [],
        "messages": [],
        "diagnostics": [],
        "thread_id": None,
        "accepted_answers_at_start": 0,
        "attempt": 1,
    }
    write_private(ROOT / f"episode-{ordinal}-start.json", encoded(entry))
    started = time.monotonic()
    process = None
    try:
        with tempfile.TemporaryDirectory(prefix="epistemics-investigation-respondent-") as cwd:
            stderr_path = ROOT / f"episode-{ordinal}.stderr"
            write_private(stderr_path, b"")
            with stderr_path.open("ab") as stderr:
                process = await asyncio.create_subprocess_exec(
                    *command(config, assignment.assignment_id),
                    cwd=cwd,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=stderr,
                    limit=4_000_000,
                    start_new_session=True,
                )
                async with asyncio.timeout(config["timeout_seconds_per_attempt"]):
                    while line := await process.stdout.readline():
                        event = json.loads(line)
                        if event.get("type") == "thread.started":
                            entry["thread_id"] = event.get("thread_id")
                        if event.get("type") in {"error", "turn.failed"}:
                            entry["diagnostics"].append(str(event)[:2000])
                        if event.get("type") == "turn.completed":
                            usage = read_usage(event.get("usage"))
                            old = entry["usage"] or dict.fromkeys(usage, 0)
                            entry["usage"] = {k: old[k] + usage[k] for k in usage}
                        if event.get("type") == "item.completed":
                            item = event.get("item", {})
                            kind = item.get("type")
                            if kind == "error":
                                entry["diagnostics"].append(str(item)[:4000])
                            elif kind == "mcp_tool_call":
                                tool = {
                                    k: item.get(k) for k in ("server", "tool", "status", "error")
                                }
                                tool["elapsed_seconds"] = time.monotonic() - started
                                if item.get("status") != "completed" or (
                                    isinstance(item.get("result"), dict)
                                    and item["result"].get("isError")
                                ):
                                    tool["diagnostic"] = str(item.get("result", ""))[:3000]
                                entry["tools"].append(tool)
                                # Private action metadata is retained without reasoning content.
                                if item.get("server") != "episode" or item.get("tool") not in TOOLS:
                                    raise RuntimeError("Unexpected tool outside assigned protocol")
                            elif kind == "agent_message":
                                entry["messages"].append(item.get("text", "")[:6000])
                            elif kind not in {"reasoning", "plan", None}:
                                raise RuntimeError(f"Unexpected respondent action: {kind}")
                    await process.wait()
                if process.returncode:
                    raise RuntimeError(f"Respondent process exit {process.returncode}")
        service = InvestigationService(COLLECTION, assignment.assignment_id)
        with service.state() as state:
            entry["accepted_answers_at_end"] = len(state["answers"])
            if len(state["answers"]) != 4 or state["completed_at"] is None:
                raise RuntimeError("Episode did not finish all four accepted answers")
        if entry["usage"] is None:
            raise RuntimeError("No provider usage received; cost is unknown")
        entry["status"] = "completed"
    except BaseException as error:
        entry["status"] = "failed"
        entry["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        if process is not None and process.returncode is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                await asyncio.wait_for(process.wait(), 5)
            except TimeoutError:
                os.killpg(process.pid, signal.SIGKILL)
                await process.wait()
        with InvestigationService(COLLECTION, assignment.assignment_id).state() as state:
            entry["accepted_answers_at_end"] = len(state["answers"])
        entry["process_returncode"] = process.returncode if process else None
        entry["finished_at"] = now()
        entry["elapsed_seconds"] = time.monotonic() - started
        write_private(ROOT / f"episode-{ordinal}-execution.json", encoded(entry))
        print(
            json.dumps({k: entry[k] for k in ("ordinal", "status", "usage", "elapsed_seconds")}),
            flush=True,
        )
    return entry


async def main():
    global COLLECTION, PHASE
    if ROOT is None:
        raise SystemExit(
            "Usage: python -m epistemics.investigation_pilot.runner NEW_PRIVATE_DIRECTORY"
        )
    config, manifests, order = prepare()
    started, started_at = time.monotonic(), now()
    entries = []
    run_status = "running"
    try:
        for phase in ("development", "repeat", "new"):
            PHASE, COLLECTION = phase, ROOT / phase
            if phase == "repeat":
                print(json.dumps({"models_locked": freeze_models(ROOT)}), flush=True)
            for aid in order[phase]:
                remaining = config["collection_budget_seconds"] - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError("Declared total collection budget exhausted")
                runtime_config = {**config, "timeout_seconds_per_attempt": min(600, remaining)}
                assignment = next(a for a in manifests[phase].assignments if a.assignment_id == aid)
                entries.append(await run_episode(runtime_config, assignment, len(entries) + 1))
            export(COLLECTION)
            print(json.dumps({"phase_complete": phase}), flush=True)
        run_status = "completed"
    except BaseException:
        run_status = "incomplete"
        raise
    finally:
        # Include failed attempts and unknown usage; do not silently exclude them.
        attempts = [
            json.loads(p.read_bytes()) for p in sorted(ROOT.glob("episode-*-execution.json"))
        ]
        keys = ("input_tokens", "cached_input_tokens", "output_tokens")
        total = {k: sum(e["usage"][k] for e in attempts if e["usage"] is not None) for k in keys}
        write_private(
            ROOT / "execution.json",
            encoded(
                {
                    "status": run_status,
                    "started_at": started_at,
                    "finished_at": now(),
                    "elapsed_seconds": time.monotonic() - started,
                    "episodes": attempts,
                    "known_usage": total,
                    "unknown_usage_attempts": sum(e["usage"] is None for e in attempts),
                    "unattempted_episodes": 36 - len(attempts),
                }
            ),
        )
    from epistemics.investigation_pilot.analysis import analyze

    result = analyze(ROOT)
    print(
        json.dumps(
            {
                "complete": True,
                "episodes": 36,
                "usage": total,
                "elapsed_seconds": time.monotonic() - started,
                "repeatability": result["repeatability"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
