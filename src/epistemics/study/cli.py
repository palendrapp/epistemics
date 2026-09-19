"""Create, collect, validate and fit matched discovery studies."""

import argparse
import asyncio
import json
from pathlib import Path

from epistemics.models import AgentDescriptor
from epistemics.study.design import create_manifest, load_manifest, write_manifest


def main():
    parser = argparse.ArgumentParser(description="Matched discovery study pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", help="Freeze a private schedule and analysis plan")
    create.add_argument("--agent", type=Path, required=True, help="AgentDescriptor JSON")
    create.add_argument("--directory", type=Path, required=True)
    create.add_argument("--worlds", type=int, default=12)
    create.add_argument("--replicates", type=int, default=2)
    create.add_argument("--seed", type=int)
    status = sub.add_parser("status", help="Operator-only collection status")
    status.add_argument("directory", type=Path)
    client = sub.add_parser("client", help="Interactive JSONL transport to one assigned MCP")
    client.add_argument("directory", type=Path)
    client.add_argument("assignment_id")
    run = sub.add_parser("run", help="Fresh respondent process per episode, through real MCP")
    run.add_argument("directory", type=Path)
    run.add_argument(
        "--respondent", type=Path, required=True, help="JSON command/pass_environment spec"
    )
    run.add_argument("--max-episodes", type=int, default=1)
    run.add_argument("--timeout", type=float, default=180)
    export = sub.add_parser(
        "export", help="Export exact-byte reports once every assignment finishes"
    )
    export.add_argument("directory", type=Path)
    fit = sub.add_parser(
        "fit", help="Train-only parameter inference and frozen held-out prediction"
    )
    fit.add_argument("directory", type=Path)
    demo = sub.add_parser("simulate", help="Populate an explicitly SYNTHETIC study offline")
    demo.add_argument("directory", type=Path)
    demo.add_argument("--worlds", type=int, default=4)
    demo.add_argument("--replicates", type=int, default=1)
    recovery = sub.add_parser("recovery", help="Synthetic recovery and misspecification checks")
    recovery.add_argument("directory", type=Path)
    recovery.add_argument("--worlds", type=int, default=12)
    recovery.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    if args.command == "create":
        agent = AgentDescriptor.model_validate_json(args.agent.read_bytes())
        manifest = create_manifest(
            agent, worlds=args.worlds, replicates=args.replicates, seed=args.seed
        )
        print(write_manifest(args.directory, manifest))
        print(f"Planned {len(manifest.assignments)} fresh episodes, 11 checkpoints each.")
    elif args.command == "status":
        import sqlite3

        manifest, _ = load_manifest(args.directory)
        database = args.directory / "responses.sqlite3"
        rows = {}
        if database.exists():
            with sqlite3.connect(database) as db:
                rows = {
                    sid: json.loads(payload)
                    for sid, payload in db.execute("SELECT id,payload FROM episodes")
                }
        print(
            json.dumps(
                {
                    "study_id": manifest.study_id,
                    "planned": len(manifest.assignments),
                    "completed": sum(r["report"] is not None for r in rows.values()),
                    "pending": [
                        {
                            "assignment_id": a.assignment_id,
                            "accepted_answers": len(
                                rows.get(a.assignment_id, {}).get("answers", [])
                            ),
                        }
                        for a in manifest.assignments
                        if rows.get(a.assignment_id, {}).get("report") is None
                    ],
                },
                indent=2,
            )
        )
    elif args.command == "client":
        from epistemics.study.runner import interactive_client

        asyncio.run(interactive_client(args.directory, args.assignment_id))
    elif args.command == "run":
        from epistemics.study.runner import collect

        if args.max_episodes < 1 or args.timeout <= 0:
            parser.error("max-episodes and timeout must be positive")
        print(
            asyncio.run(collect(args.directory, args.respondent, args.max_episodes, args.timeout))
        )
    elif args.command == "export":
        from epistemics.study.service import export_reports

        print(f"Exported {len(export_reports(args.directory))} immutable episode reports")
    elif args.command == "fit":
        from epistemics.study.fit import fit_directory

        profile = fit_directory(args.directory)
        print(
            json.dumps(
                {
                    "profile": str(args.directory / "profile.json"),
                    "parameters": {k: v.model_dump() for k, v in profile.parameters.items()},
                    "heldout_standardized_rmse": profile.diagnostics["heldout_standardized_rmse"],
                },
                indent=2,
            )
        )
    elif args.command == "simulate":
        from epistemics.study.simulation import simulate_study

        simulate_study(args.directory, worlds=args.worlds, replicates=args.replicates)
        print("Synthetic responses exported. Run fit to analyze them.")
    elif args.command == "recovery":
        from epistemics.study.simulation import recovery_study

        if not 1 <= args.repetitions <= 100:
            parser.error("repetitions must be in 1..100")
        result = recovery_study(args.directory, worlds=args.worlds, repetitions=args.repetitions)
        print(json.dumps({k: v for k, v in result.items() if k != "runs"}, indent=2))
        if not result["passed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
