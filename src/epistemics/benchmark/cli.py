"""Operator commands; no benchmark control is exposed through respondent MCP."""

import asyncio
import json
from pathlib import Path

from epistemics.benchmark.analysis import analyze, lock_predictions
from epistemics.benchmark.models import BenchmarkSpec, RecoveryPolicy
from epistemics.benchmark.recovery import amend
from epistemics.benchmark.runner import codex_version, collect
from epistemics.benchmark.store import accounting, create, json_bytes, load
from epistemics.predictive.design import budget, create_manifest


def cost_projection(directory, replicates):
    manifest, _, _ = load(directory)
    if manifest.purpose != "development_costing":
        raise ValueError("Cost projection requires a separate development-costing run")
    resources = accounting(directory)
    if resources["totals"]["unresolved_attempts"] or resources["totals"]["unknown_usage_attempts"]:
        raise ValueError("Cannot cost a plan with unresolved/unknown-usage attempts")
    planned = budget(create_manifest(seed=0, replicates=replicates))
    projections = {}
    for configuration in manifest.configurations:
        cid = configuration.configuration_id
        values = [r for r in resources["runs"] if r["configuration_id"] == cid]
        if len(values) < 2:
            raise ValueError("Complete the predeclared pair for every configuration before costing")
        tokens = [r["usage"]["input_tokens"] + r["usage"]["output_tokens"] for r in values]
        elapsed = [r["elapsed_seconds"] for r in values]
        n = planned["episodes_per_configuration"]
        projections[cid] = {
            "observed_episodes": len(values),
            "planned_episodes": n,
            "mean_processed_tokens_per_episode": sum(tokens) / len(tokens),
            "projected_processed_tokens": n * sum(tokens) / len(tokens),
            "projected_serial_seconds": n * sum(elapsed) / len(elapsed),
            "suggested_token_admission_budget": n * max(tokens) * 2,
            "suggested_time_admission_budget_seconds": int(n * max(elapsed) * 2 + 1),
        }
    return {
        "schema_version": "epistemics.benchmark-cost-estimate.v1",
        "configurations": projections,
        "budget_per_configuration": planned,
        "marginal_usd": None,
        "billing": manifest.budget.billing,
        "interpretation": "Extrapolation from two longest-graph episodes per configuration, not a provider quote or confidence bound. Admission ceilings use twice the observed maximum per episode; one episode may overshoot. Token counts do not convert directly to account quota percentages.",
    }


def add_commands(commands):
    parser = commands.add_parser("benchmark", help="Freeze and run multi-configuration predictions")
    sub = parser.add_subparsers(dest="benchmark_command", required=True)
    setup = sub.add_parser("create")
    setup.add_argument("--design", type=Path, required=True)
    setup.add_argument("--spec", type=Path, required=True)
    setup.add_argument("--output", type=Path, required=True)
    recovery = sub.add_parser("amend-recovery")
    recovery.add_argument("--benchmark", type=Path, required=True)
    recovery.add_argument("--policy", type=Path, required=True)
    recovery.add_argument("--output", type=Path, required=True)
    recovery.add_argument("--reason", required=True)
    recovery.add_argument("--review-process-exit", action="append", default=[])
    for name in ("run", "status", "lock", "analyze", "cost"):
        command = sub.add_parser(name)
        command.add_argument("--benchmark", type=Path, required=True)
        if name == "run":
            command.add_argument("--split", choices=["profile", "policy", "heldout"], required=True)
            command.add_argument("--max-episodes", type=int, default=1)
        if name in {"lock", "analyze", "cost"}:
            command.add_argument("--output", type=Path, required=True)
        if name == "cost":
            command.add_argument("--replicates", type=int, default=2)


def run(args):
    name = args.benchmark_command
    if name == "amend-recovery":
        policy = RecoveryPolicy.model_validate_json(args.policy.read_bytes())
        value = amend(
            args.benchmark,
            args.output,
            policy,
            reviewed_process_exits=args.review_process_exit,
            reason=args.reason,
        )
        print(
            json.dumps(
                {
                    "benchmark": str(args.output),
                    "version": value.benchmark_version,
                    "protocol_status": "amended",
                }
            )
        )
    elif name == "create":
        spec = BenchmarkSpec.model_validate_json(args.spec.read_bytes())
        value = create(args.design, args.output, spec, codex_version=codex_version())
        print(
            json.dumps(
                {
                    "benchmark": str(args.output),
                    "purpose": value.purpose,
                    "configurations": len(value.configurations),
                }
            )
        )
    elif name == "run":
        asyncio.run(collect(args.benchmark, split=args.split, max_episodes=args.max_episodes))
    elif name == "status":
        manifest, design, _ = load(args.benchmark)
        from epistemics.predictive.collection import collection_status

        print(
            json.dumps(
                {
                    "purpose": manifest.purpose,
                    "design_budget": budget(design),
                    "accounting": accounting(args.benchmark),
                    "collections": {
                        c.configuration_id: collection_status(
                            args.benchmark / "collections" / c.configuration_id
                        )
                        for c in manifest.configurations
                    },
                },
                indent=2,
            )
        )
    else:
        if args.output.exists():
            raise FileExistsError(args.output)
        data = (
            lock_predictions(args.benchmark)
            if name == "lock"
            else analyze(args.benchmark)
            if name == "analyze"
            else json_bytes(cost_projection(args.benchmark, args.replicates))
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(data)
        args.output.chmod(0o600)
        print(json.dumps({"output": str(args.output)}))
