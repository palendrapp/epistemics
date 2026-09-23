"""Operator commands and a real MCP transport; no model-provider requests."""

import asyncio
import json
import os
import sys
from pathlib import Path

from epistemics.investigation3.service import create, encoded, export, status, write_private


def add_commands(commands):
    parser = commands.add_parser(
        "investigation3", help="Discovery with an active research choice (development)"
    )
    sub = parser.add_subparsers(dest="investigation_command", required=True)
    design = sub.add_parser("create", help="Freeze a private development schedule and participant")
    design.add_argument("--directory", type=Path, required=True)
    design.add_argument("--participant", type=Path, required=True)
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
    check.add_argument("--seed", type=int, default=20260923)
    check.add_argument("--worlds", type=int, default=24)
    check.add_argument("--repetitions", type=int, default=4)
    web = sub.add_parser("serve", help="Serve a human collection or one bound case on loopback")
    web.add_argument("--directory", type=Path, required=True)
    web.add_argument("--assignment", help="Optional single case; default is the whole collection")
    web.add_argument("--port", type=int, default=8768)
    compare = sub.add_parser(
        "compare-initialization",
        help="Exploratory reanalysis of an exact-byte investigation source; not new validation",
    )
    compare.add_argument("--report", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
    demo = sub.add_parser("demo", help="Run and export a clearly labelled synthetic respondent")
    demo.add_argument("--directory", type=Path, required=True)
    demo.add_argument("--seed", type=int, default=19)


def run(args):
    command = args.investigation_command
    if command == "compare-initialization":
        from epistemics.investigation3 import ANALYSIS_VERSION
        from epistemics.investigation3.inference import INITIALIZATIONS, fit
        from epistemics.investigation3.service import digest, fingerprint
        from epistemics.passport.investigation import InvestigationCollection, derive, read_case

        raw = args.report.read_bytes()
        source = InvestigationCollection.model_validate_json(raw)
        if source != derive(source.cases):
            raise ValueError("Source collection differs from its original reports")
        reports = [read_case(case) for case in source.cases]
        result = {
            "schema_version": "epistemics.initialization-comparison.v1",
            "analysis_version": ANALYSIS_VERSION,
            "implementation_sha256": fingerprint(),
            "source_sha256": digest(raw),
            "source_protocol": source.context.protocol_version,
            "response_origin": source.context.response_origin,
            "scope": "Exploratory reanalysis of existing observations, not a new evaluation or held-out empirical validation. Original artifacts remain unchanged.",
            "fits": {
                m: fit([r.observations for r in reports], initialization=m) for m in INITIALIZATIONS
            },
        }
        write_private(args.output, encoded(result))
        print(json.dumps(result, indent=2))
    elif command == "create":
        manifest = create(
            args.directory,
            json.loads(args.participant.read_bytes()),
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
    elif command == "serve":
        from epistemics.investigation3.web import serve

        serve(args.directory, args.assignment, args.port)
    elif command == "status":
        print(json.dumps(status(args.directory), indent=2))
    elif command == "client":
        asyncio.run(interactive_client(args.directory, args.assignment))
    elif command == "export":
        print(json.dumps(export(args.directory), indent=2))
    elif command == "validate-synthetic":
        from epistemics.investigation3.service import fingerprint
        from epistemics.investigation3.simulation import validation

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
                        "parameter_mean_absolute_errors",
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
    from epistemics.investigation3.models import Trial as InvestigationTrial
    from epistemics.investigation3.service import InvestigationService
    from epistemics.investigation3.simulation import response

    manifest = create(
        directory,
        {
            "kind": "agent",
            "subject_id": "synthetic:joint-observer",
            "configuration": {
                "model": "analytic-observer",
                "model_version": "investigation/0.3.0",
                "configuration_sha256": "0" * 64,
            },
        },
        seed=seed,
        synthetic=True,
    )
    for assignment in manifest.assignments:
        service = InvestigationService(directory, assignment.assignment_id)
        while not (current := service.get_trial())["complete"]:
            trial = InvestigationTrial.model_validate(current["trial"])
            answer = response(trial)
            service.submit(trial.trial_id, answer)
        service.finish()


def server_parameters(directory, assignment):
    from mcp import StdioServerParameters

    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "epistemics.investigation3.mcp_server"],
        env={
            **os.environ,
            "EPISTEMICS_INVESTIGATION3": str(Path(directory).resolve()),
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
