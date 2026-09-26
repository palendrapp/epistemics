"""Bounded fresh-context acceptance and eight-context Stage A; operator-only."""

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
from epistemics.source_learning.service import export
from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_panel.runner import TOOLS
from epistemics.source_panel.runner import command as panel_command
from epistemics.source_verification.analysis import contrast, gate
from epistemics.source_verification.service import (
    VerificationService,
    create,
    fingerprint,
    load_evidence,
)

PROMPT = (
    "You are a fresh respondent completing an assigned-verification evaluation with 24 fictional "
    "companies and 36 checkpoints. Use only the assigned collection MCP tools. First call "
    "describe_battery and get_history. Then read get_trial and submit your own company probability "
    "and invest/decline decision, continuing until every checkpoint is complete. Follow the public "
    "protocol. The evaluator assigns verification; do not choose a check or submit a research query. "
    "Maintain one continuing context; earlier public evidence, accepted answers and resolutions "
    "may inform later answers. You may use get_history to restore public history. Accepted "
    "answers cannot be changed. Do not read files, browse, inspect evaluator code, use other tools, "
    "request future evidence or seek evaluator feedback. Do not disclose private chain-of-thought. "
    "After get_trial reports complete, call finish_evaluation. Finally give brief answers to the "
    "completion questions and describe confusing instructions or interface friction. Do not guess "
    "cognitive labels or evaluation scores."
)


def command(root, entry, config):
    args = panel_command(root, entry, config)
    return [
        s.replace(
            "epistemics.source_panel.mcp_server", "epistemics.source_verification.mcp_server"
        ).replace("EPISTEMICS_SOURCE_PANEL", "EPISTEMICS_SOURCE_VERIFICATION")
        for s in args[:-1]
    ] + [PROMPT]


def prepare(root, validation_paths, *, phase, acceptance=None):
    root = Path(root).resolve()
    if phase not in ("acceptance", "stage-a"):
        raise ValueError("Unknown phase")
    validations = []
    for path in validation_paths:
        raw = Path(path).read_bytes()
        result = json.loads(raw)
        if (
            not result["passed"]
            or result["implementation_sha256"] != fingerprint()
            or result["repetitions_per_family_per_policy"] < 32
        ):
            raise ValueError("Require passed full recovery of this exact implementation")
        validations.append({"sha256": digest(raw), "seed": result["seed"]})
    if len(validations) != 2 or len({v["seed"] for v in validations}) != 2:
        raise ValueError("Require two distinct validation seeds")
    forbidden = set()
    accepted = None
    if phase == "stage-a":
        if acceptance is None:
            raise ValueError("Review acceptance before Stage A")
        acceptance = Path(acceptance)
        prior = json.loads((acceptance / "plan.json").read_bytes())
        review_raw = (acceptance / "acceptance-review.json").read_bytes()
        review = json.loads(review_raw)
        if (
            prior["phase"] != "acceptance"
            or prior["implementation_sha256"] != fingerprint()
            or review["plan_sha256"] != digest((acceptance / "plan.json").read_bytes())
            or not review["passed"]
        ):
            raise ValueError("Require matching reviewed acceptance")
        for entry in prior["runs"]:
            report, evidence = load_evidence(acceptance / "collections" / entry["run_id"])
            if (
                evidence["binding"]["policy"] != entry["policy"]
                or report.manifest.design_seed != prior["world_seeds"][entry["world"]]
            ):
                raise ValueError("Acceptance binding mismatch")
            if (
                json.loads(
                    (acceptance / "collections" / entry["run_id"] / "execution.json").read_bytes()
                )["status"]
                != "completed"
            ):
                raise ValueError("Acceptance incomplete")
        forbidden.update(prior["world_seeds"].values())
        accepted = {
            "plan_sha256": digest((acceptance / "plan.json").read_bytes()),
            "review_sha256": digest(review_raw),
        }
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
            "from epistemics.source_verification.service import fingerprint; print(fingerprint())",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(snapshot)},
        text=True,
    ).strip()
    if actual != fingerprint():
        raise ValueError("Snapshot mismatch")
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
        for label, model in (
            [("astra", "gpt-6-astra")]
            if phase == "acceptance"
            else [("astra", "gpt-6-astra"), ("sol", "gpt-6-sol")]
        )
    }
    worlds = ["acceptance"] if phase == "acceptance" else ["a", "b"]
    seeds = {w: secrets.randbits(64) for w in worlds}
    if len(set(seeds.values())) != len(seeds) or set(seeds.values()) & forbidden:
        raise ValueError("Require distinct new worlds")
    runs = [
        {"run_id": f"{c}-{w}-{p}", "configuration": c, "world": w, "policy": p}
        for c in configs
        for w in worlds
        for p in ("none", "always")
    ]
    order_seed = secrets.randbits(64)
    random.Random(order_seed).shuffle(runs)
    plan = {
        "schema_version": "epistemics.source-verification-plan.v1",
        "phase": phase,
        "created_at": now(),
        "implementation_sha256": fingerprint(),
        "validations": validations,
        "acceptance": accepted,
        "configurations": configs,
        "world_seeds": seeds,
        "order_seed": order_seed,
        "runs": runs,
        "limits": {
            "max_attempts_per_run": 1,
            "per_run_seconds": 900,
            "total_seconds": 1800 if phase == "acceptance" else 3600,
            "max_known_processed_tokens": 8000000 if phase == "acceptance" else 25000000,
            "admission_reserve_tokens_per_run": 3000000,
            "concurrency": 2,
        },
        "analysis": {
            "primary": "Always minus none mean net realized payoff over twelve later companies, separately per config/world",
            "secondary": [
                "final Brier",
                "gross payoff",
                "verification cost",
                "false acceptance",
                "missed opportunity",
                "decision changes",
                "usage",
                "latency",
            ],
            "feasibility_gate": {"mean_net_gain_at_least": 0.01, "both_worlds_nonnegative": True},
            "uncertainty": "Four context/world contrasts; no independent-company bootstrap or population claim",
            "trajectory": "Full fresh policy contexts; policies declared upfront; comparison includes anticipation and carryover",
            "acceptance": "Engineering/comprehension only; excluded from Stage A estimates",
            "release": "Fictional controlled task; no general verification benefit, stable trait or passport-guided benefit",
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
            "subject_id": f"codex:{cfg['model']}:{phase}:{e['run_id']}",
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
            policy=e["policy"],
            seed=seeds[e["world"]],
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
        with tempfile.TemporaryDirectory(prefix="epistemics-verification-respondent-") as cwd:
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
            VerificationService(directory).evidence()
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
    runs = {}
    worlds = {}
    for e in plan["runs"]:
        directory = root / "collections" / e["run_id"]
        report, evidence = load_evidence(directory)
        execution = json.loads((directory / "execution.json").read_bytes())
        m = report.manifest
        cfg = plan["configurations"][e["configuration"]]
        if (
            execution["status"] != "completed"
            or evidence["binding"]["policy"] != e["policy"]
            or evidence["binding"]["implementation_sha256"] != plan["implementation_sha256"]
            or m.design_seed != plan["world_seeds"][e["world"]]
            or m.participant.configuration.configuration_sha256 != digest(encoded(cfg))
            or m.response_origin != "agent"
            or m.created_at.isoformat() < plan["created_at"]
        ):
            raise ValueError("Run does not match prospective plan")
        world = digest(
            encoded([m.model_dump(mode="json")[k] for k in ("sources", "archive", "companies")])
        )
        if e["world"] in worlds and worlds[e["world"]] != world:
            raise ValueError("World content mismatch")
        worlds[e["world"]] = world
        runs[e["run_id"]] = {
            "analysis": evidence["analysis"],
            "elapsed_seconds": execution["elapsed_seconds"],
            "usage": execution["usage"],
            "report_sha256": digest((directory / "report.json").read_bytes()),
            "evidence_sha256": digest((directory / "verification-evidence.json").read_bytes()),
            "submission_calls": sum(t["tool"] == "submit_answer" for t in execution["tools"]),
            "tool_errors": sum(
                t["result_is_error"] or t["status"] != "completed" or bool(t["error"])
                for t in execution["tools"]
            ),
        }
    if len(set(worlds.values())) != len(worlds):
        raise ValueError("Worlds must differ")
    comparisons = {
        c: {
            w: contrast(runs[f"{c}-{w}-none"]["analysis"], runs[f"{c}-{w}-always"]["analysis"])
            for w in plan["world_seeds"]
        }
        for c in plan["configurations"]
    }
    result = {
        "schema_version": "epistemics.source-verification-summary.v1",
        "plan_sha256": digest(raw),
        "phase": plan["phase"],
        "runs": runs,
        "contrasts": comparisons,
        "gates": {c: gate(list(v.values())) for c, v in comparisons.items()}
        if plan["phase"] == "stage-a"
        else None,
        "scope": plan["analysis"]["release"],
    }
    save(root / "summary.json", encoded(result))
    return result


async def run(root, plan):
    start = time.monotonic()
    executions = []
    failure = None
    try:
        for offset in range(0, len(plan["runs"]), 2):
            batch = plan["runs"][offset : offset + 2]
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
    p.add_argument("--phase", choices=["acceptance", "stage-a"], required=True)
    p.add_argument("--acceptance", type=Path)
    args = p.parse_args()
    root = args.directory.resolve()
    plan = prepare(root, args.validation, phase=args.phase, acceptance=args.acceptance)
    asyncio.run(run(root, plan))


if __name__ == "__main__":
    main()
