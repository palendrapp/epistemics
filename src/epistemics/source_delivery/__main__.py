import argparse
import json
from pathlib import Path

from epistemics.source_delivery.service import DeliveryService, create, fingerprint
from epistemics.source_learning.storage import digest, encoded, save


def main():
    parser = argparse.ArgumentParser(
        description="Clarified private source-learning interface, version 0.2"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("create")
    new.add_argument("--directory", type=Path, required=True)
    new.add_argument("--participant", type=Path, required=True)
    new.add_argument("--seed", type=int)
    new.add_argument("--condition", choices=("sparse", "dense"), default="sparse")
    new.add_argument("--presentation", choices=("structured", "packet"), default="structured")
    new.add_argument("--synthetic", action="store_true")
    web = commands.add_parser("serve")
    web.add_argument("--directory", type=Path, required=True)
    web.add_argument("--port", type=int, default=8777)
    out = commands.add_parser("export")
    out.add_argument("--directory", type=Path, required=True)
    sim = commands.add_parser("simulate")
    sim.add_argument("--directory", type=Path, required=True)
    sim.add_argument("--seed", type=int, default=20260926)
    sim.add_argument("--condition", choices=("sparse", "dense"), default="sparse")
    sim.add_argument("--presentation", choices=("structured", "packet"), default="structured")
    val = commands.add_parser("validate-synthetic")
    val.add_argument("--output", type=Path, required=True)
    val.add_argument("--seed", type=int, required=True)
    val.add_argument("--repetitions", type=int, default=32)
    args = parser.parse_args()
    if args.command == "create":
        m = create(
            args.directory,
            json.loads(args.participant.read_bytes()),
            seed=args.seed,
            condition=args.condition,
            presentation=args.presentation,
            synthetic=args.synthetic,
        )
        print(json.dumps({"study_id": m.study_id, "version": "source-learning/0.2.0"}))
    elif args.command == "serve":
        from epistemics.source_delivery.web import serve

        serve(args.directory, args.port)
    elif args.command == "export":
        DeliveryService(args.directory).evidence()
        print(args.directory / "delivery-evidence.json")
    elif args.command == "simulate":
        from epistemics.source_delivery.simulation import simulate

        simulate(args.directory, args.seed, args.condition, args.presentation)
        print(args.directory / "report.json")
    else:
        from epistemics.source_delivery.simulation import recovery

        plan = {
            "seed": args.seed,
            "repetitions": args.repetitions,
            "implementation_sha256": fingerprint(),
            "gates": "unchanged source-learning recovery gates; no semantic effect simulated",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        save(args.output.with_suffix(".plan.json"), encoded(plan))
        result = recovery(args.seed, args.repetitions)
        result["plan_sha256"] = digest(encoded(plan))
        save(args.output, encoded(result))
        print(json.dumps({"passed": result["passed"], "datasets": result["datasets"]}))
        if not result["passed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
