import argparse
import json
from pathlib import Path

from epistemics.source_learning.models import Manifest, Report, Trial
from epistemics.source_learning.service import create, export
from epistemics.source_learning.storage import encoded, fingerprint, save


def main():
    parser = argparse.ArgumentParser(description="Private development source-learning collection")
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("create")
    new.add_argument("--directory", type=Path, required=True)
    new.add_argument("--participant", type=Path, required=True)
    new.add_argument("--seed", type=int)
    new.add_argument("--condition", choices=("sparse", "dense"))
    new.add_argument("--synthetic", action="store_true")
    web = commands.add_parser("serve")
    web.add_argument("--directory", type=Path, required=True)
    web.add_argument("--port", type=int, default=8775)
    out = commands.add_parser("export")
    out.add_argument("--directory", type=Path, required=True)
    preview = commands.add_parser("simulate")
    preview.add_argument("--directory", type=Path, required=True)
    preview.add_argument("--seed", type=int, default=20260925)
    preview.add_argument("--condition", choices=("sparse", "dense"), default="sparse")
    validation = commands.add_parser("validate-synthetic")
    validation.add_argument("--output", type=Path, required=True)
    validation.add_argument("--seed", type=int, default=20260925)
    validation.add_argument("--repetitions", type=int, default=32)
    schemas = commands.add_parser("schema")
    schemas.add_argument("--directory", type=Path, default=Path("schemas"))
    args = parser.parse_args()
    try:
        if args.command == "create":
            manifest = create(
                args.directory,
                json.loads(args.participant.read_bytes()),
                seed=args.seed,
                condition=args.condition,
                synthetic=args.synthetic,
            )
            print(
                json.dumps(
                    {
                        "study_id": manifest.study_id,
                        "condition": manifest.condition,
                        "checkpoints": 36,
                    }
                )
            )
        elif args.command == "serve":
            from epistemics.source_learning.web import serve

            serve(args.directory, args.port)
        elif args.command in ("simulate", "export"):
            if args.command == "simulate":
                from epistemics.source_learning.simulation import simulate

                report = simulate(args.directory, args.seed, args.condition)
            else:
                report = export(args.directory)
            print(
                json.dumps(
                    {
                        "report": str(args.directory / "report.md"),
                        "origin": report.manifest.response_origin,
                        "analysis": report.analysis,
                    },
                    indent=2,
                )
            )
        elif args.command == "validate-synthetic":
            from epistemics.source_learning.simulation import GATES, recovery

            args.output.parent.mkdir(parents=True, exist_ok=True)
            plan = {
                "seed": args.seed,
                "repetitions": args.repetitions,
                "gates": GATES,
                "implementation_sha256": fingerprint(),
            }
            save(args.output.with_suffix(".plan.json"), encoded(plan))
            result = recovery(args.seed, args.repetitions)
            result["implementation_sha256"] = plan["implementation_sha256"]
            save(args.output, encoded(result))
            print(json.dumps(result, indent=2))
            if not result["passed"]:
                raise SystemExit(1)
        else:
            args.directory.mkdir(parents=True, exist_ok=True)
            for model, name in ((Manifest, "collection"), (Trial, "trial"), (Report, "report")):
                schema = model.model_json_schema()
                schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
                save(args.directory / f"source-learning-{name}.v1.json", encoded(schema))
    except ValueError as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    main()
