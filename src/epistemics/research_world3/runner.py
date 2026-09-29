"""Bounded fresh-context collection of research dossiers; operator-only.

The plan freezes configurations, arms, the balanced context design, prices and limits
before any response. Neglect estimates pair matched presentations across separate contexts
within one configuration and arm.
"""

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
from epistemics.research_world3.analysis import panel
from epistemics.research_world3.collection import create, export, fingerprint, load_report
from epistemics.research_world3.design import design
from epistemics.research_world3.presentation import ARMS
from epistemics.service import now
from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_panel.runner import TOOLS
from epistemics.source_panel.runner import command as panel_command

PROMPT = (
    "You are a fresh respondent completing a research-dossier evaluation of fictional companies. "
    "Use only the assigned collection MCP tools. First call describe_battery once. Then call "
    "get_trial once. For each case, read the case brief and every document, then submit your own "
    "probability that end-customer demand is strong, your invest/decline decision and any other "
    "answer the checkpoint requests. Each submit_answer receipt contains next_trial, the "
    "checkpoint now awaiting your answer, so continue from it without calling get_trial again "
    "unless you need to recover. Follow the public protocol. Maintain one continuing context. "
    "Accepted answers cannot be changed. Do not read files, browse, inspect evaluator code, use "
    "other tools or seek evaluator feedback. Do not disclose private chain-of-thought. When a "
    "receipt reports all_cases_answered, call finish_evaluation. Finally give brief answers to "
    "the completion questions and describe confusing instructions or interface friction. Do not "
    "guess cognitive labels or evaluation scores."
)
# Label -> (requested model alias, reasoning effort). Weaker entries serve as positive controls.
CONFIGURATIONS = {
    "astra": ("gpt-6-astra", "medium"),
    "sol": ("gpt-6-sol", "medium"),
    "astra-low": ("gpt-6-astra", "low"),
    "sol-low": ("gpt-6-sol", "low"),
    "astra-high": ("gpt-6-astra", "high"),
    "sol-high": ("gpt-6-sol", "high"),
    "luna": ("gpt-5.6-luna", "medium"),
    "terra": ("gpt-5.6-terra", "medium"),
}


def command(root, entry, config):
    args = panel_command(root, entry, config)
    return [
        s.replace(
            "epistemics.source_panel.mcp_server", "epistemics.research_world3.mcp_server"
        ).replace("EPISTEMICS_SOURCE_PANEL", "EPISTEMICS_RESEARCH_WORLD3")
        for s in args[:-1]
    ] + [PROMPT]


def prepare(
    root,
    validation_paths,
    *,
    phase="acceptance",
    configurations=("astra", "sol"),
    arms=ARMS,
    worlds_per_family=4,
    per_family_per_context=4,
    anchors_per_context=1,
    check_offered=True,
    max_tokens=10000000,
):
    root = Path(root).resolve()
    if not configurations or set(configurations) - set(CONFIGURATIONS):
        raise ValueError("Unknown configuration")
    if not arms or set(arms) - set(ARMS):
        raise ValueError("Unknown arm")
    validations = []
    for path in validation_paths:
        raw = Path(path).read_bytes()
        result = json.loads(raw)
        if (
            result["schema_version"] != "epistemics.research-world-validation.v3"
            or not result["passed"]
            or result["implementation_sha256"] != fingerprint()
            or result["audited_pairs"] < 1000
        ):
            raise ValueError("Require passed full validation of this exact implementation")
        validations.append({"sha256": digest(raw), "seed": result["seed"]})
    if len(validations) != 2 or len({v["seed"] for v in validations}) != 2:
        raise ValueError("Require two distinct validation seeds")
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parents[3]
    snapshot = root / "implementation/src"
    snapshot.mkdir(mode=0o700, parents=True)
    for source in (repo / "src").rglob("*"):
        if source.is_file() and (source.suffix == ".py" or "assets" in source.parts):
            target = snapshot / source.relative_to(repo / "src")
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            save(target, source.read_bytes())
    for name in ("pyproject.toml", "uv.lock"):
        save(root / "implementation" / name, (repo / name).read_bytes())
    actual = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "from epistemics.research_world3.collection import fingerprint; print(fingerprint())",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(snapshot)},
        text=True,
    ).strip()
    if actual != fingerprint():
        raise ValueError("Snapshot mismatch")
    configs = {
        label: {
            "model": CONFIGURATIONS[label][0],
            "reasoning_effort": CONFIGURATIONS[label][1],
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
        for label in configurations
    }
    design_seed, order_seed = secrets.randbits(63), secrets.randbits(63)
    contexts = design(
        design_seed, worlds_per_family, per_family_per_context, anchors_per_context, check_offered
    )
    runs = [
        {
            "run_id": f"{config}-{arm}-{c['context_type']}{c['block']}",
            "configuration": config,
            "arm": arm,
            "context_type": c["context_type"],
            "block": c["block"],
            "items": c["items"],
        }
        for config in configs
        for arm in arms
        for c in contexts
    ]
    random.Random(order_seed).shuffle(runs)
    plan = {
        "schema_version": "epistemics.research-world-plan.v3",
        "phase": phase,
        "created_at": now(),
        "implementation_sha256": fingerprint(),
        "validations": validations,
        "configurations": configs,
        "arms": list(arms),
        "design": {
            "seed": design_seed,
            "worlds_per_family": worlds_per_family,
            "per_family_per_context": per_family_per_context,
            "anchors_per_context": anchors_per_context,
            "check_offered": check_offered,
        },
        "order_seed": order_seed,
        "runs": runs,
        "limits": {
            "max_attempts_per_run": 1,
            "per_run_seconds": 900,
            "total_seconds": 7200,
            "max_known_processed_tokens": max_tokens,
            "admission_reserve_tokens_per_run": 1000000,
            "concurrency": 2,
        },
        "analysis": {
            "primary": "Neglect weights per configuration, arm and family from matched presentations in separate contexts",
            "secondary": [
                "mean logit error by presentation",
                "decision consistency",
                "survey purchases against normative net value",
                "ex ante expected payoff and action regret",
                "usage and latency",
            ],
            "release": "Development collection; no passport claim, stable trait or verification benefit follows from it alone",
        },
        "failures": "Stop admission on any failed attempt or budget exhaustion; preserve partials; no automatic retry",
        "billing": "Existing account; known processed/cached/output tokens; marginal dollars unknown; token admission boundary is not a streaming cap",
        "commitment": "Operator-created before collection; no independent timestamp or model attestation",
    }
    save(root / "plan.json", encoded(plan))
    save(root / "plan.sha256", (digest(encoded(plan)) + "\n").encode())
    for e in runs:
        cfg = configs[e["configuration"]]
        participant = {
            "kind": "agent",
            "subject_id": f"codex:{cfg['model']}:research-{phase}:{e['run_id']}",
            "configuration": {
                "model": cfg["model"],
                "model_version": cfg["model_revision"],
                "configuration_sha256": digest(encoded(cfg)),
                "temperature": None,
            },
        }
        create(
            root / "collections" / e["run_id"],
            participant,
            arm=e["arm"],
            items=e["items"],
            check_offered=check_offered,
        )
    return plan


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
        with tempfile.TemporaryDirectory(prefix="epistemics-research-respondent-") as cwd:
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
                            if (
                                call["result_is_error"]
                                or call["error"]
                                or call["status"] != "completed"
                            ):
                                call["public_error_result"] = str(item.get("result"))[:4000]
                            execution["tools"].append(call)
                            if call["server"] != "collection" or call["tool"] not in TOOLS:
                                raise ValueError("Unexpected tool outside public interface")
                        elif kind == "agent_message":
                            execution["messages"].append(item.get("text", "")[:12000])
                        elif kind == "error":
                            execution["diagnostics"].append(str(item)[:4000])
                        elif kind not in {"reasoning", "plan", None}:
                            raise ValueError(f"Unexpected action {kind}")
                    await process.wait()
            if process.returncode or execution["usage"] is None:
                raise ValueError(f"Process exit {process.returncode} or missing usage")
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


def summarize(root):
    root = Path(root)
    raw = (root / "plan.json").read_bytes()
    plan = json.loads(raw)
    if (
        digest(raw) != (root / "plan.sha256").read_text().strip()
        or plan["implementation_sha256"] != fingerprint()
    ):
        raise ValueError("Plan or implementation changed")
    runs, reports = {}, {}
    for e in plan["runs"]:
        directory = root / "collections" / e["run_id"]
        report = load_report(directory)
        execution = json.loads((directory / "execution.json").read_bytes())
        m = report.manifest
        cfg = plan["configurations"][e["configuration"]]
        if (
            execution["status"] != "completed"
            or m.arm != e["arm"]
            or [i.model_dump(exclude={"case"}) for i in m.items] != e["items"]
            or m.participant.configuration.configuration_sha256 != digest(encoded(cfg))
            or m.response_origin != "agent"
            or m.created_at.isoformat() < plan["created_at"]
        ):
            raise ValueError("Run does not match prospective plan")
        reports.setdefault(e["configuration"], []).append(report)
        calls = [t["tool"] for t in execution["tools"]]
        runs[e["run_id"]] = {
            "analysis": {k: v for k, v in report.analysis.items() if k != "rows"},
            "elapsed_seconds": execution["elapsed_seconds"],
            "usage": execution["usage"],
            "tool_calls": {name: calls.count(name) for name in TOOLS},
            "tool_errors": sum(
                t["result_is_error"] or t["status"] != "completed" or bool(t["error"])
                for t in execution["tools"]
            ),
            "report_sha256": digest((directory / "report.json").read_bytes()),
        }
    result = {
        "schema_version": "epistemics.research-world-summary.v3",
        "plan_sha256": digest(raw),
        "phase": plan["phase"],
        "runs": runs,
        "neglect": {config: panel(group) for config, group in reports.items()},
        "known_usage": {
            k: sum(r["usage"][k] for r in runs.values())
            for k in ("input_tokens", "cached_input_tokens", "output_tokens")
        },
        "scope": plan["analysis"]["release"],
    }
    save(root / "summary.json", encoded(result))
    return result


async def run(root, plan):
    raw = (root / "plan.json").read_bytes()
    if digest(raw) != (root / "plan.sha256").read_text().strip() or json.loads(raw) != plan:
        raise ValueError("Execution plan differs from committed bytes")
    if plan["implementation_sha256"] != fingerprint():
        raise ValueError("Frozen implementation changed before admission")
    start = time.monotonic()
    executions = []
    failure = None
    try:
        step = plan["limits"]["concurrency"]
        for offset in range(0, len(plan["runs"]), step):
            batch = plan["runs"][offset : offset + step]
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
                raise ValueError("Admission budget exhausted")
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
                raise ValueError("Failed attempt; no further admission")
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--validation", action="append", type=Path, required=True)
    p.add_argument("--phase", default="acceptance")
    p.add_argument("--configuration", action="append", choices=sorted(CONFIGURATIONS))
    p.add_argument("--arm", action="append", choices=ARMS)
    p.add_argument("--worlds-per-family", type=int, default=4)
    p.add_argument("--per-family-per-context", type=int, default=4)
    p.add_argument("--anchors-per-context", type=int, default=1)
    p.add_argument("--no-check", action="store_true")
    p.add_argument("--max-tokens", type=int, default=10000000)
    a = p.parse_args()
    root = a.directory.resolve()
    plan = prepare(
        root,
        a.validation,
        phase=a.phase,
        configurations=tuple(a.configuration or ("astra", "sol")),
        arms=tuple(a.arm or ARMS),
        worlds_per_family=a.worlds_per_family,
        per_family_per_context=a.per_family_per_context,
        anchors_per_context=a.anchors_per_context,
        check_offered=not a.no_check,
        max_tokens=a.max_tokens,
    )
    asyncio.run(run(root, plan))


if __name__ == "__main__":
    main()
