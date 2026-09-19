"""Operator design/collection commands and a public MCP transport bridge."""

import asyncio
import json
from pathlib import Path

from epistemics.predictive.collection import (
    collection_status,
    create_collection,
    export_collection,
)
from epistemics.predictive.design import (
    budget,
    create_manifest,
    encoded,
    load_manifest,
    public_checkpoint,
    write_manifest,
)
from epistemics.predictive.simulation import validation


def add_commands(commands):
    parser = commands.add_parser(
        "predictive", help="Design, validate and collect the provenance pilot"
    )
    subcommands = parser.add_subparsers(dest="predictive_command", required=True)
    create = subcommands.add_parser("create", help="Freeze an operator-owned matched design")
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--seed", type=int)
    create.add_argument("--replicates", type=int, default=1)
    check = subcommands.add_parser(
        "validate-synthetic", help="Offline parameter recovery and held-out prediction"
    )
    check.add_argument("--design", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    check.add_argument("--seed", type=int, default=1909)
    preview = subcommands.add_parser(
        "preview", help="Operator preview of one public checkpoint; not a session API"
    )
    preview.add_argument("--design", type=Path, required=True)
    preview.add_argument("--assignment", required=True)
    preview.add_argument("--index", type=int, default=0)
    preview.add_argument("--output", type=Path, required=True)
    bind = subcommands.add_parser("bind", help="Freeze a participant and planned assignments")
    bind.add_argument("--design", type=Path, required=True)
    bind.add_argument("--spec", type=Path, required=True)
    bind.add_argument("--output", type=Path, required=True)
    for name, help_text in (
        ("status", "Operator progress, including incomplete assignments and attempts"),
        ("client", "Public JSON-lines bridge to an assigned real MCP process"),
        ("export", "Freeze a private response snapshot after all planned episodes finish"),
    ):
        command = subcommands.add_parser(name, help=help_text)
        command.add_argument("--collection", type=Path, required=True)
        if name == "client":
            command.add_argument("--assignment", required=True)
        if name == "export":
            command.add_argument("--output", type=Path, required=True)


def run(args):
    if args.predictive_command == "client":
        from epistemics.predictive.client import interactive_client

        asyncio.run(interactive_client(args.collection, args.assignment))
        return
    if args.predictive_command == "status":
        print(json.dumps(collection_status(args.collection), indent=2))
        return
    if args.predictive_command == "bind":
        manifest = create_collection(args.design, args.output, json.loads(args.spec.read_bytes()))
        print(
            json.dumps(
                {
                    "collection": str(args.output),
                    "purpose": manifest.purpose,
                    "response_origin": manifest.response_origin,
                    "planned_episodes": len(manifest.assignment_ids),
                },
                indent=2,
            )
        )
        return
    if args.predictive_command == "export":
        data = export_collection(args.collection)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(data)
        args.output.chmod(0o600)
        print(json.dumps({"output": str(args.output), "bytes": len(data)}))
        return
    if args.predictive_command == "create":
        manifest = create_manifest(seed=args.seed, replicates=args.replicates)
        path = write_manifest(args.output, manifest)
        print(
            json.dumps(
                {"manifest": str(path), "scope": manifest.use, "budget": budget(manifest)}, indent=2
            )
        )
        return
    manifest = load_manifest(args.design)
    if args.predictive_command == "preview":
        assignment = next(
            (a for a in manifest.assignments if a.assignment_id == args.assignment), None
        )
        if assignment is None:
            raise ValueError("Unknown assignment")
        result = public_checkpoint(assignment, args.index)
    else:
        if args.seed < 0:
            raise ValueError("Validation seed must be nonnegative")
        result = validation(manifest, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(encoded(result))
    args.output.chmod(0o600)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "schema_version": result.schema_version,
                **(
                    {
                        "passed": result.passed,
                        "response_origin": "synthetic",
                        "checks": result.checks,
                    }
                    if args.predictive_command == "validate-synthetic"
                    else {}
                ),
            },
            indent=2,
        )
    )
    if args.predictive_command == "validate-synthetic" and not result.passed:
        raise SystemExit(1)
