import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from epistemics.baselines import answer_trial
from epistemics.models import AgentDescriptor, Report, Trial
from epistemics.service import EvaluationService


def demo(seed: int = 42, prior_weight: float = 1, evidence_weight: float = 1) -> Report:
    configuration = json.dumps({"prior_weight": prior_weight, "evidence_weight": evidence_weight})
    agent = AgentDescriptor(
        agent_id="demo:reference",
        model="analytic-reference",
        model_version="0.1.0",
        configuration_sha256=hashlib.sha256(configuration.encode()).hexdigest(),
        context_policy="reset_per_trial",
        temperature=0,
    )
    with tempfile.TemporaryDirectory() as directory:
        service = EvaluationService(Path(directory) / "demo.sqlite3")
        session_id = service.start(agent, seed=seed)["session_id"]
        while not (current := service.get_trial(session_id))["complete"]:
            trial = Trial.model_validate(current["trial"])
            answer = answer_trial(trial, prior_weight=prior_weight, evidence_weight=evidence_weight)
            service.submit(session_id, trial.trial_id, answer)
        return service.finish(session_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Epistemics local evaluator")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("demo", help="Run a synthetic reference agent, offline")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--prior-weight", type=float, default=1)
    run.add_argument("--evidence-weight", type=float, default=1)
    run.add_argument("--output", type=Path, default=Path("output/demo-report.json"))
    schema = commands.add_parser("schema", help="Export the Python report contract as JSON Schema")
    schema.add_argument("--output", type=Path, default=Path("schemas/report.v1.json"))
    check = commands.add_parser("validate", help="Validate a report's structure (not provenance)")
    check.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        data = json.loads(args.path.read_bytes())
        contract = {"epistemics.report.v1": Report}.get(data.get("schema_version"), Report)
        report = contract.model_validate(data)
        print("Valid report structure")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.command == "schema":
        for contract, path in [(Report, args.output)]:
            data = contract.model_json_schema()
            data["$schema"] = "https://json-schema.org/draft/2020-12/schema"
            path.write_text(json.dumps(data, indent=2) + "\n")
        return
    report = demo(args.seed, args.prior_weight, args.evidence_weight)
    args.output.write_text(report.model_dump_json(indent=2) + "\n")
    print(
        json.dumps(
            {
                "report": str(args.output),
                "trials": len(report.observations),
                "parameters": {k: v.estimate for k, v in report.parameters.items()},
                "model_fits": {k: v.model_dump() for k, v in report.model_fits.items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
