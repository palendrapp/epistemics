"""Operator-only pilot design and synthetic checks. No subject transport yet."""

import json
from pathlib import Path

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
        "predictive", help="Design and synthetically validate the provenance pilot"
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


def run(args):
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
