"""Operator commands and a real MCP transport; no model-provider requests."""

import asyncio
import json
import os
import sys
from pathlib import Path

from epistemics.investigation.service import create, encoded, export, status, write_private


def add_commands(commands):
    parser = commands.add_parser(
        "investigation", help="Discovery with an active research choice (development)"
    )
    sub = parser.add_subparsers(dest="investigation_command", required=True)
    design = sub.add_parser("create", help="Freeze a private development schedule and participant")
    design.add_argument("--directory", type=Path, required=True)
    design.add_argument("--participant", type=Path, required=True)
    design.add_argument("--episodes", type=int, default=6)
    design.add_argument("--mode", choices=["discovery", "calibration"], default="discovery")
    design.add_argument("--seed", type=int)
    for name in ("status", "export", "client"):
        command = sub.add_parser(name)
        command.add_argument("--directory", type=Path, required=True)
        if name == "client":
            command.add_argument("--assignment", required=True)
    check = sub.add_parser(
        "validate-synthetic", help="Model discrimination and parameter recovery; no agents"
    )
    check.add_argument("--output", type=Path, required=True)
    check.add_argument("--seed", type=int, default=20260920)
    check.add_argument("--worlds", type=int, default=24)
    check.add_argument("--repetitions", type=int, default=20)
    demo = sub.add_parser("demo", help="Run and export a clearly labelled synthetic respondent")
    demo.add_argument("--directory", type=Path, required=True)
    demo.add_argument("--seed", type=int, default=19)


def run(args):
    command = args.investigation_command
    if command == "create":
        manifest = create(
            args.directory,
            json.loads(args.participant.read_bytes()),
            episodes=args.episodes,
            mode=args.mode,
            seed=args.seed,
        )
        print(
            json.dumps(
                {
                    "directory": str(args.directory),
                    "episodes": len(manifest.assignments),
                    "checkpoints_per_episode": 4,
                    "purpose": manifest.purpose,
                }
            )
        )
    elif command == "status":
        print(json.dumps(status(args.directory), indent=2))
    elif command == "client":
        asyncio.run(interactive_client(args.directory, args.assignment))
    elif command == "export":
        print(json.dumps(export(args.directory), indent=2))
    elif command == "validate-synthetic":
        from epistemics.investigation.service import fingerprint
        from epistemics.investigation.simulation import validation

        result = validation(seed=args.seed, worlds=args.worlds, repetitions=args.repetitions)
        result["implementation_sha256"] = fingerprint()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_private(args.output, encoded(result))
        print(
            json.dumps(
                {
                    k: result[k]
                    for k in (
                        "passed",
                        "response_origin",
                        "checks",
                        "recovery_rates",
                        "archive_weight_mean_absolute_error",
                    )
                },
                indent=2,
            )
        )
        if not result["passed"]:
            raise SystemExit(1)
    else:
        demo(args.directory, args.seed)
        print(json.dumps(export(args.directory), indent=2))


def demo(directory, seed):
    from epistemics.investigation.inference import best_query, forecasts
    from epistemics.investigation.models import InvestigationAnswer, InvestigationTrial
    from epistemics.investigation.service import InvestigationService

    manifest = create(
        directory,
        {
            "kind": "agent",
            "subject_id": "synthetic:joint-observer",
            "configuration": {
                "model": "analytic-observer",
                "model_version": "investigation/0.1.0",
                "configuration_sha256": "0" * 64,
            },
        },
        episodes=6,
        seed=seed,
        synthetic=True,
    )
    for assignment in manifest.assignments:
        service = InvestigationService(directory, assignment.assignment_id)
        while not (current := service.get_trial())["complete"]:
            trial = InvestigationTrial.model_validate(current["trial"])
            p, audit, backlog = [round(float(v), 2) for v in forecasts(trial)]
            answer = InvestigationAnswer(
                growth_probability=p,
                audit_understatement_probability=audit,
                backlog_high_probability=backlog,
                decision="invest" if (trial.gain + trial.loss) * p > trial.loss else "hold",
                query=best_query(trial) if trial.index == 1 else None,
            )
            service.submit(trial.trial_id, answer)
        service.finish()


def server_parameters(directory, assignment):
    from mcp import StdioServerParameters

    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "epistemics.investigation.mcp_server"],
        env={
            **os.environ,
            "EPISTEMICS_INVESTIGATION": str(Path(directory).resolve()),
            "EPISTEMICS_ASSIGNMENT": assignment,
        },
    )


async def interactive_client(directory, assignment):
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client

    async with (
        stdio_client(server_parameters(directory, assignment)) as (read, write),
        ClientSession(read, write) as client,
    ):
        await client.initialize()

        async def call(name, arguments=None):
            result = await client.call_tool(name, arguments or {})
            if result.isError:
                raise ValueError(str(result.content))
            return result.structuredContent or json.loads(result.content[0].text)

        print(
            json.dumps(
                {
                    "protocol": await call("describe_battery"),
                    "history": await call("get_history"),
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
                print(
                    json.dumps(
                        {"result": await call(request["tool"], request.get("arguments", {}))}
                    ),
                    flush=True,
                )
            except (KeyError, ValueError, TypeError, AttributeError) as error:
                print(json.dumps({"error": str(error)}), flush=True)
