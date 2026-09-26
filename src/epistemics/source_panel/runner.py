"""Bounded account-backed panel. Operator-only; never expose this module through MCP."""

import argparse
import asyncio
import json
import os
import random
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from epistemics.benchmark.runner import DISABLED_FEATURES, codex_version, read_usage
from epistemics.investigation_pilot.runner import EXTRA_DISABLED
from epistemics.service import now
from epistemics.source_learning.models import Report
from epistemics.source_learning.service import create, export
from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_panel.analysis import summarize
from epistemics.source_panel.profiles import fit_profile
from epistemics.source_panel.service import PanelService, bind, fingerprint

TOOLS = ["describe_battery", "get_history", "get_trial", "submit_answer", "finish_evaluation"]
PROMPT = (
    "You are a fresh respondent completing a source-learning evaluation with 24 fictional "
    "companies and 36 checkpoints. Use only the assigned collection MCP tools. First call "
    "describe_battery and get_history. Then read get_trial, submit your own probability, "
    "decision and any research choice or source judgment requested at that checkpoint, and "
    "continue until all checkpoints are complete. Follow the public protocol. Maintain one "
    "continuing context; earlier public evidence, your accepted answers and company resolutions "
    "may inform later answers. You may use get_history to restore public history. Accepted "
    "answers cannot be changed. Do not read files, browse, inspect evaluator code, use other "
    "tools, request future evidence or seek evaluator feedback. Do not disclose private "
    "chain-of-thought. After get_trial reports complete, call finish_evaluation. Finally give "
    "brief answers to any completion questions and describe confusing instructions or interface friction. "
    "Do not guess cognitive labels or evaluation scores."
)


def prepare(root, validation_paths):
    root = Path(root).resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    validations = []
    for path in validation_paths:
        raw = Path(path).read_bytes()
        result = json.loads(raw)
        if not result["passed"] or result["implementation_sha256"] != fingerprint():
            raise ValueError("Require passed validation of this exact implementation")
        validations.append({"sha256": digest(raw), "seed": result["seed"]})
    if len(validations) != 2 or len({r["seed"] for r in validations}) != 2:
        raise ValueError("Require two distinct validation seeds")
    repo = Path(__file__).resolve().parents[3]
    snapshot = root / "implementation/src"
    snapshot.mkdir(mode=0o700, parents=True)
    for source in (repo / "src").rglob("*"):
        if source.is_file() and (source.suffix == ".py" or "assets" in source.parts):
            target = snapshot / source.relative_to(repo / "src")
            target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            save(target, source.read_bytes())
    for name in ("pyproject.toml", "uv.lock"):
        save(root / "implementation" / name, (repo / name).read_bytes())
    snapshot_fp = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "from epistemics.source_panel.service import fingerprint; print(fingerprint())",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(snapshot)},
        text=True,
    ).strip()
    if snapshot_fp != fingerprint():
        raise ValueError("Snapshot fingerprint mismatch")
    configs = {
        label: {
            "model": model,
            "reasoning_effort": "medium",
            "model_revision": "unverified_requested_alias",
            "temperature": None,
            "codex_version": codex_version(),
            "prompt": PROMPT,
            "tools": TOOLS,
            "disabled_features": list(DISABLED_FEATURES) + EXTRA_DISABLED,
            "enabled_features": ["skip_host_skill_discovery", "code_mode_host"],
            "ignore_user_config": True,
            "ephemeral": True,
            "project_doc_max_bytes": 0,
            "sandbox": "read-only",
            "web_search": "disabled",
            "approval_policy": "never",
            "context": "fresh_per_collection_continuous_within",
            "tool_approval": "five_public_tools_only",
            "execution_verification": "operator_asserted",
            "authentication": "existing_chatgpt_login",
            "implementation_sha256": fingerprint(),
        }
        for label, model in (("astra", "gpt-6-astra"), ("sol", "gpt-6-sol"))
    }
    seeds = {w: secrets.randbits(64) for w in ("a", "b", "transfer")}
    if len(set(seeds.values())) != 3:
        raise ValueError("World seeds must differ")
    runs = []
    for config in configs:
        for world in ("a", "b"):
            for repeat in (1, 2):
                runs.append(
                    {
                        "run_id": f"{config}-{world}-sparse-{repeat}",
                        "configuration": config,
                        "phase": "baseline",
                        "world": world,
                        "repeat": repeat,
                        "condition": "sparse",
                        "presentation": "structured",
                    }
                )
            runs.append(
                {
                    "run_id": f"{config}-{world}-dense-1",
                    "configuration": config,
                    "phase": "dense",
                    "world": world,
                    "repeat": 1,
                    "condition": "dense",
                    "presentation": "structured",
                }
            )
        for presentation in ("structured", "packet"):
            runs.append(
                {
                    "run_id": f"{config}-transfer-{presentation}",
                    "configuration": config,
                    "phase": "transfer",
                    "world": "transfer",
                    "repeat": 1,
                    "condition": "sparse",
                    "presentation": presentation,
                }
            )
    order_seed = secrets.randbits(64)
    random.Random(order_seed).shuffle(runs)
    # All phases/order are fixed before responses; baseline must precede external-profile freeze.
    runs.sort(key=lambda r: (r["phase"] != "baseline", r["phase"] == "transfer"))
    plan = {
        "schema_version": "epistemics.source-panel-plan.v1",
        "created_at": now(),
        "implementation_sha256": fingerprint(),
        "validations": validations,
        "configurations": configs,
        "world_seeds": seeds,
        "order_seed": order_seed,
        "runs": runs,
        "limits": {
            "max_attempts_per_run": 1,
            "per_run_seconds": 900,
            "total_seconds": 5400,
            "max_known_processed_tokens": 40000000,
            "admission_reserve_tokens_per_run": 3000000,
            "concurrency": 2,
        },
        "analysis": {
            "repeatability": "RMS differences of first twelve unaudited reports within each config/world; between-config differences use repeat means",
            "dense": "First twelve reports compared with same-config/world sparse repeat mean; one dense context each; bundled prompting/burden effect, no population CI",
            "profile_fit": "Only first twelve reports of each of eight baseline collections; four per config, all eight for shared; no dense or transfer responses",
            "transfer_primary": "First twelve unaudited forecasts in one new world, matched structured/packet fresh contexts per configuration; configuration/shared/fixed joint/flat/discount and mean/prior comparators locked before each answer",
            "transfer_secondary": "All 36 predictions conditional on actual research path; no joint choice likelihood or causal effect attributed to presentation alone",
            "adequacy": "256 conditional simulations per family, 99th percentile RMSE screen on twelve unaudited transfer reports; fixed analysis seed 20260926, not a composite test",
            "uncertainty": "Show every world/configuration contrast and repeat variation; two development worlds and one transfer world are insufficient for population confidence intervals",
            "release": "Feasibility/development comparison, no stable phenotype or support/policy benefit; retain shared/simple account absent demonstrated individual gain",
        },
        "failures": "Stop admission on failed run or exhausted budget; preserve all partial attempts; no automatic substitution/retry or case exclusion",
        "billing": "Provider processed/cached/output tokens recorded; token ceiling checked at run boundaries with admission reserve, not a hard streaming token cap; marginal dollar cost unknown",
        "commitment": "Operator-created precollection commitment, not independent timestamp or model attestation",
    }
    save(root / "plan.json", encoded(plan))
    save(root / "plan.sha256", (digest(encoded(plan)) + "\n").encode())
    for entry in runs:
        config = configs[entry["configuration"]]
        participant = {
            "kind": "agent",
            "subject_id": f"codex:{config['model']}:{entry['run_id']}",
            "configuration": {
                "model": config["model"],
                "model_version": config["model_revision"],
                "configuration_sha256": digest(encoded(config)),
                "temperature": None,
            },
        }
        create(
            root / "collections" / entry["run_id"],
            participant,
            seed=seeds[entry["world"]],
            condition=entry["condition"],
        )
    return plan


def command(root, entry, config):
    settings = {
        "model_reasoning_effort": config["reasoning_effort"],
        "approval_policy": "never",
        "web_search": "disabled",
        "forced_login_method": "chatgpt",
        "hide_agent_reasoning": True,
        "project_doc_max_bytes": 0,
        "mcp_servers.collection.command": sys.executable,
        "mcp_servers.collection.args": ["-m", "epistemics.source_panel.mcp_server"],
        "mcp_servers.collection.env.EPISTEMICS_SOURCE_PANEL": str(
            root / "collections" / entry["run_id"]
        ),
        "mcp_servers.collection.env.PYTHONPATH": str(root / "implementation/src"),
        "mcp_servers.collection.required": True,
        "mcp_servers.collection.enabled_tools": TOOLS,
    }
    for tool in TOOLS:
        settings[f"mcp_servers.collection.tools.{tool}.approval_mode"] = "approve"
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
    ]
    for feature in config["enabled_features"]:
        argv.extend(["--enable", feature])
    for feature in config["disabled_features"]:
        argv.extend(["--disable", feature])
    for key, value in settings.items():
        argv.extend(["-c", f"{key}={json.dumps(value)}"])
    return [*argv, PROMPT]


async def collect(root, entry, config, timeout):
    directory = root / "collections" / entry["run_id"]
    execution = {
        "run_id": entry["run_id"],
        "status": "running",
        "started_at": now(),
        "usage": None,
        "tools": [],
        "messages": [],
        "diagnostics": [],
    }
    save(directory / "execution-start.json", encoded(execution))
    save(directory / "command.json", encoded(command(root, entry, config)))
    started, process = time.monotonic(), None
    print(json.dumps({"run_id": entry["run_id"], "status": "started"}), flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix="epistemics-panel-respondent-") as cwd:
            save(directory / "stderr.log", b"")
            with (directory / "stderr.log").open("ab") as stderr:
                process = await asyncio.create_subprocess_exec(
                    *command(root, entry, config),
                    cwd=cwd,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=stderr,
                    limit=4000000,
                    start_new_session=True,
                )
                async with asyncio.timeout(timeout):
                    while line := await process.stdout.readline():
                        event = json.loads(line)
                        if event.get("type") == "thread.started":
                            execution["thread_id"] = event.get("thread_id")
                        if event.get("type") in {"error", "turn.failed"}:
                            execution["diagnostics"].append(str(event)[:4000])
                        if event.get("type") == "turn.completed":
                            usage = read_usage(event.get("usage"))
                            old = execution["usage"] or dict.fromkeys(usage, 0)
                            execution["usage"] = {k: old[k] + usage[k] for k in usage}
                        if event.get("type") != "item.completed":
                            continue
                        item = event.get("item", {})
                        kind = item.get("type")
                        if kind == "mcp_tool_call":
                            call = {k: item.get(k) for k in ("server", "tool", "status", "error")}
                            call["elapsed_seconds"] = time.monotonic() - started
                            call["result_is_error"] = (item.get("result") or {}).get(
                                "isError", False
                            )
                            execution["tools"].append(call)
                            if call["server"] != "collection" or call["tool"] not in TOOLS:
                                raise ValueError("Unexpected tool outside public interface")
                            if call["tool"] == "submit_answer":
                                n = sum(t["tool"] == "submit_answer" for t in execution["tools"])
                                if n % 6 == 0:
                                    print(
                                        json.dumps({"run_id": entry["run_id"], "submissions": n}),
                                        flush=True,
                                    )
                        elif kind == "agent_message":
                            execution["messages"].append(item.get("text", "")[:12000])
                        elif kind == "error":
                            execution["diagnostics"].append(str(item)[:4000])
                        elif kind not in {"reasoning", "plan", None}:
                            raise ValueError(f"Unexpected action {kind}")
                    await process.wait()
            if process.returncode or execution["usage"] is None:
                raise ValueError(f"Process exit {process.returncode} or missing usage")
            PanelService(directory).evidence()
            export(directory)
            execution["status"] = "completed"
    except BaseException as error:
        execution["status"] = "failed"
        execution["error"] = f"{type(error).__name__}: {error}"
        if process is not None and process.returncode is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                await asyncio.wait_for(process.wait(), 5)
            except TimeoutError:
                os.killpg(process.pid, signal.SIGKILL)
                await process.wait()
    finally:
        execution["finished_at"] = now()
        execution["elapsed_seconds"] = time.monotonic() - started
        save(directory / "execution.json", encoded(execution))
        print(
            json.dumps({k: execution[k] for k in ("run_id", "status", "elapsed_seconds", "usage")}),
            flush=True,
        )
    return execution


def freeze(root, plan):
    entries = [e for e in plan["runs"] if e["phase"] == "baseline"]
    reports = {
        e["run_id"]: Report.model_validate_json(
            (root / "collections" / e["run_id"] / "report.json").read_bytes()
        )
        for e in entries
    }
    result = {
        "frozen_at": now(),
        "plan_sha256": digest(encoded(plan)),
        "configuration": {
            c: fit_profile([reports[e["run_id"]] for e in entries if e["configuration"] == c])
            for c in plan["configurations"]
        },
        "shared": fit_profile(list(reports.values())),
        "training_reports_sha256": {
            rid: digest((root / "collections" / rid / "report.json").read_bytes())
            for rid in reports
        },
    }
    save(root / "frozen-profiles.json", encoded(result))
    return result


async def run(root, plan):
    start = time.monotonic()
    executions, failure, profiles = [], None, None
    try:
        for phase in ("baseline", "dense", "transfer"):
            entries = [e for e in plan["runs"] if e["phase"] == phase]
            for offset in range(0, len(entries), 2):
                batch = entries[offset : offset + 2]
                remaining = plan["limits"]["total_seconds"] - (time.monotonic() - start)
                known = sum(
                    e["usage"]["input_tokens"] + e["usage"]["output_tokens"]
                    for e in executions
                    if e["usage"] is not None
                )
                if (
                    remaining <= 0
                    or known + len(batch) * plan["limits"]["admission_reserve_tokens_per_run"]
                    > plan["limits"]["max_known_processed_tokens"]
                ):
                    raise ValueError("Panel admission budget exhausted")
                for entry in batch:
                    bound = (
                        None
                        if phase != "transfer"
                        else {
                            "configuration": profiles["configuration"][entry["configuration"]],
                            "shared": profiles["shared"],
                        }
                    )
                    bind(
                        root / "collections" / entry["run_id"],
                        presentation=entry["presentation"],
                        profiles=bound,
                        frozen_at=profiles["frozen_at"] if bound is not None else None,
                    )
                results = await asyncio.gather(
                    *(
                        collect(
                            root,
                            e,
                            plan["configurations"][e["configuration"]],
                            min(remaining, plan["limits"]["per_run_seconds"]),
                        )
                        for e in batch
                    )
                )
                executions.extend(results)
                if any(e["status"] != "completed" for e in results):
                    raise ValueError("A run failed; no further admission")
            if phase == "baseline":
                profiles = freeze(root, plan)
        summarize(root)
    except BaseException as error:
        failure = f"{type(error).__name__}: {error}"
    result = {
        "status": "failed" if failure else "completed",
        "error": failure,
        "finished_at": now(),
        "elapsed_seconds": time.monotonic() - start,
        "executions": executions,
        "unattempted_runs": len(plan["runs"]) - len(executions),
        "known_usage": {
            k: sum(e["usage"][k] for e in executions if e["usage"] is not None)
            for k in ("input_tokens", "cached_input_tokens", "output_tokens")
        },
        "unknown_usage_attempts": sum(e["usage"] is None for e in executions),
    }
    save(root / "execution.json", encoded(result))
    print(json.dumps({k: v for k, v in result.items() if k != "executions"}), flush=True)
    if failure:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--validation", action="append", type=Path, required=True)
    args = parser.parse_args()
    root = args.directory.resolve()
    plan = prepare(root, args.validation)
    asyncio.run(run(root, plan))


if __name__ == "__main__":
    main()
