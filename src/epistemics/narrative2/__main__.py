import argparse
import json
from pathlib import Path

from epistemics.narrative2.models import Manifest, Report, Trial
from epistemics.narrative2.service import create, encoded, export, save


def main():
    parser = argparse.ArgumentParser(description="Development narrative-inference diagnostic")
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("create")
    new.add_argument("--directory", type=Path, required=True)
    new.add_argument("--participant", type=Path, required=True)
    new.add_argument("--seed", type=int)
    new.add_argument("--synthetic", action="store_true")
    run = commands.add_parser("serve")
    run.add_argument("--directory", type=Path, required=True)
    run.add_argument("--port", type=int, default=8773)
    out = commands.add_parser("export")
    out.add_argument("--directory", type=Path, required=True)
    validation = commands.add_parser("validate-synthetic")
    validation.add_argument("--seed", type=int, default=20260924)
    validation.add_argument("--repetitions", type=int, default=16)
    validation.add_argument("--output", type=Path, required=True)
    schemas = commands.add_parser("schema")
    schemas.add_argument("--directory", type=Path, default=Path("schemas"))
    preview = commands.add_parser("simulate")
    preview.add_argument("--directory", type=Path, required=True)
    preview.add_argument("--seed", type=int, default=20260924)
    args = parser.parse_args()
    try:
        if args.command == "create":
            m = create(
                args.directory,
                json.loads(args.participant.read_bytes()),
                seed=args.seed,
                synthetic=args.synthetic,
            )
            print(json.dumps({"study_id": m.study_id, "cases": len(m.assignments)}))
        elif args.command == "export":
            report = export(args.directory)
            print(
                json.dumps(
                    {"report": str(args.directory / "report.json"), "cases": len(report.cases)}
                )
            )
        elif args.command == "serve":
            from epistemics.narrative2.web import serve

            serve(args.directory, args.port)
        elif args.command == "simulate":
            from epistemics.narrative2.simulation import simulate

            report = simulate(args.directory, args.seed)
            print(
                json.dumps(
                    {
                        "response_origin": report.manifest.response_origin,
                        "cases": len(report.cases),
                        "report": str(args.directory / "report.json"),
                    }
                )
            )
        elif args.command == "schema":
            args.directory.mkdir(parents=True, exist_ok=True)
            for model, name in [
                (Manifest, "narrative-collection.v2"),
                (Trial, "narrative-trial.v2"),
                (Report, "narrative-report.v2"),
            ]:
                schema = model.model_json_schema()
                schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
                (args.directory / f"{name}.json").write_bytes(encoded(schema))
        else:
            from epistemics.narrative2.simulation import recovery

            result = recovery(args.seed, args.repetitions)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            save(args.output, encoded(result))
            print(
                json.dumps(
                    {k: v for k, v in result.items() if k != "restricted_family_comparisons"},
                    indent=2,
                )
            )
            if not result["passed"]:
                raise SystemExit(1)
    except (ValueError, OSError) as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()
