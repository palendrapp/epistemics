import argparse
import json
from pathlib import Path

from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_verification.service import VerificationService, create, fingerprint


def main():
    parser = argparse.ArgumentParser(description="Assigned source verification")
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("create")
    new.add_argument("--participant", type=Path, required=True)
    for name in ("create", "simulate"):
        p = new if name == "create" else sub.add_parser(name)
        p.add_argument("--directory", type=Path, required=True)
        p.add_argument("--policy", choices=["none", "always"], required=True)
        p.add_argument("--seed", type=int, required=name == "simulate")
    new.add_argument("--synthetic", action="store_true")
    serve = sub.add_parser("serve")
    serve.add_argument("--directory", type=Path, required=True)
    serve.add_argument("--port", type=int, default=8778)
    out = sub.add_parser("export")
    out.add_argument("--directory", type=Path, required=True)
    validate = sub.add_parser("validate-synthetic")
    validate.add_argument("--output", type=Path, required=True)
    validate.add_argument("--seed", type=int, required=True)
    validate.add_argument("--repetitions", type=int, default=32)
    a = parser.parse_args()
    if a.command == "create":
        create(
            a.directory,
            json.loads(a.participant.read_bytes()),
            policy=a.policy,
            seed=a.seed,
            synthetic=a.synthetic,
        )
    elif a.command == "simulate":
        from epistemics.source_verification.simulation import simulate

        simulate(a.directory, a.seed, a.policy)
    elif a.command == "serve":
        from epistemics.source_verification.web import serve

        serve(a.directory, a.port)
    elif a.command == "export":
        VerificationService(a.directory).evidence()
    else:
        from epistemics.source_verification.simulation import recovery

        a.output.parent.mkdir(parents=True, exist_ok=True)
        plan = {
            "seed": a.seed,
            "repetitions": a.repetitions,
            "implementation_sha256": fingerprint(),
            "gates": "original source-learning recovery gates, separately for both assigned policies",
        }
        save(a.output.with_suffix(".plan.json"), encoded(plan))
        result = recovery(a.seed, a.repetitions)
        result["plan_sha256"] = digest(encoded(plan))
        save(a.output, encoded(result))
        print(json.dumps({"passed": result["passed"], "datasets": result["datasets"]}))
        if not result["passed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
