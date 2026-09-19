import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from epistemics.baselines import answer_trial
from epistemics.company.models import CompanyReport
from epistemics.discovery.models import DiscoveryReport
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
    from epistemics.passport.cli import add_commands as add_passport_commands
    from epistemics.predictive.cli import add_commands as add_predictive_commands

    add_passport_commands(commands)
    add_predictive_commands(commands)
    serve = commands.add_parser("serve", help="Run the shared core evaluation in a local browser")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--database", type=Path, default=Path(".epistemics/live.sqlite3"))
    serve.add_argument(
        "--synthetic-demo", action="store_true", help="Label all collected responses synthetic"
    )
    run = commands.add_parser("demo", help="Run a synthetic reference agent, offline")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--prior-weight", type=float, default=1)
    run.add_argument("--evidence-weight", type=float, default=1)
    run.add_argument("--output", type=Path, default=Path("output/demo-report.json"))
    company = commands.add_parser(
        "company-demo", help="Run a synthetic company respondent, offline"
    )
    company.add_argument("--seed", type=int, default=42)
    company.add_argument("--positive-weight", type=float, default=1)
    company.add_argument("--negative-weight", type=float, default=1)
    company.add_argument("--duplicate-weight", type=float, default=0)
    company.add_argument("--auxiliary-shift", type=float, default=0)
    company.add_argument("--output", type=Path, default=Path("output/company-report.json"))
    recovery = commands.add_parser(
        "company-recovery", help="Run a multi-seed synthetic recovery study"
    )
    recovery.add_argument("--seeds", type=int, default=20)
    recovery.add_argument("--output", type=Path, default=Path("output/company-recovery.json"))
    preview = commands.add_parser(
        "company-preview", help="Export an evaluator-side preview of a sample episode"
    )
    preview.add_argument("--seed", type=int, default=42)
    preview.add_argument("--output", type=Path, default=Path("output/company-preview.md"))
    discovery = commands.add_parser(
        "discovery-demo", help="Run a synthetic discovery observer offline"
    )
    discovery.add_argument("--seed", type=int, default=7)
    discovery.add_argument(
        "--model",
        choices=["joint_learning", "fixed_sources", "fixed_weak_link", "fixed_strong_link"],
        default="joint_learning",
    )
    discovery.add_argument("--source-frame", type=float, default=0)
    discovery.add_argument("--output-frame", type=float, default=0)
    discovery.add_argument("--output", type=Path, default=Path("output/discovery/report.json"))
    discovery_preview = commands.add_parser(
        "discovery-preview", help="Export the authored discovery materials"
    )
    discovery_preview.add_argument("--seed", type=int, default=7)
    discovery_preview.add_argument(
        "--output", type=Path, default=Path("output/discovery/episode.md")
    )
    discovery_recovery = commands.add_parser(
        "discovery-recovery", help="Multi-run source/output recovery and model discrimination"
    )
    discovery_recovery.add_argument("--seeds", type=int, default=8)
    discovery_recovery.add_argument("--blocks", type=int, default=3)
    discovery_recovery.add_argument(
        "--output", type=Path, default=Path("output/discovery/recovery.json")
    )
    schema = commands.add_parser("schema", help="Export the Python report contract as JSON Schema")
    schema.add_argument("--output", type=Path, default=Path("schemas/report.v1.json"))
    check = commands.add_parser("validate", help="Validate a report's structure (not provenance)")
    check.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.command == "predictive":
        from epistemics.predictive.cli import run as run_predictive

        try:
            run_predictive(args)
        except (OSError, ValueError) as error:
            parser.error(str(error))
        return
    if args.command == "serve":
        from epistemics.live.web import serve as serve_core

        if not 0 <= args.port <= 65535:
            parser.error("Port must be between 0 and 65535")
        serve_core(args.port, args.database, synthetic=args.synthetic_demo)
        return
    if args.command == "passport":
        from epistemics.passport.cli import run as run_passport

        try:
            run_passport(args)
        except (OSError, ValueError) as error:
            parser.error(str(error))
        return
    if args.command == "validate":
        from epistemics.live.models import CoreReport
        from epistemics.participants import ParticipantDescriptor, SessionContext
        from epistemics.passport.models import CorePassport, Passport
        from epistemics.predictive.models import (
            DesignManifest,
            PublicCheckpoint,
            SyntheticValidation,
        )
        from epistemics.study.models import EpisodeReport, StudyManifest, StudyProfile

        data = json.loads(args.path.read_bytes())
        contract = {
            "epistemics.report.v2": CompanyReport,
            "epistemics.report.v3": DiscoveryReport,
            "epistemics.report.v4": CoreReport,
            "epistemics.study.v1": StudyManifest,
            "epistemics.study-episode.v1": EpisodeReport,
            "epistemics.study-profile.v1": StudyProfile,
            "epistemics.participant.v1": ParticipantDescriptor,
            "epistemics.session-context.v1": SessionContext,
            "epistemics.passport.v1": Passport,
            "epistemics.passport.v2": CorePassport,
            "epistemics.predictive-design.v1": DesignManifest,
            "epistemics.predictive-checkpoint.v1": PublicCheckpoint,
            "epistemics.predictive-validation.v1": SyntheticValidation,
        }.get(data.get("schema_version"), Report)
        report = contract.model_validate(data)
        if isinstance(report, ParticipantDescriptor):
            report = report.root
        identifier = getattr(
            report, "session_id", getattr(report, "study_id", getattr(report, "passport_id", ""))
        )
        print(f"Valid {report.schema_version}: {identifier}")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.command == "schema":
        from epistemics.live.models import CoreReport, CoreTrial
        from epistemics.participants import ParticipantDescriptor, SessionContext
        from epistemics.passport.models import CorePassport, Passport
        from epistemics.predictive.models import (
            DesignManifest,
            PublicCheckpoint,
            SyntheticValidation,
        )
        from epistemics.study.models import EpisodeReport, StudyManifest, StudyProfile

        for contract, path in [
            (Report, args.output),
            (CompanyReport, args.output.with_name("report.v2.json")),
            (DiscoveryReport, args.output.with_name("report.v3.json")),
            (CoreReport, args.output.with_name("report.v4.json")),
            (CoreTrial, args.output.with_name("core-trial.v1.json")),
            (StudyManifest, args.output.with_name("study.v1.json")),
            (EpisodeReport, args.output.with_name("study-episode.v1.json")),
            (StudyProfile, args.output.with_name("study-profile.v1.json")),
            (ParticipantDescriptor, args.output.with_name("participant.v1.json")),
            (SessionContext, args.output.with_name("session-context.v1.json")),
            (Passport, args.output.with_name("passport.v1.json")),
            (CorePassport, args.output.with_name("passport.v2.json")),
            (DesignManifest, args.output.with_name("predictive-design.v1.json")),
            (PublicCheckpoint, args.output.with_name("predictive-checkpoint.v1.json")),
            (SyntheticValidation, args.output.with_name("predictive-validation.v1.json")),
        ]:
            data = contract.model_json_schema()
            data["$schema"] = "https://json-schema.org/draft/2020-12/schema"
            path.write_text(json.dumps(data, indent=2) + "\n")
        return
    if args.command == "discovery-preview":
        from epistemics.discovery.simulation import preview as discovery_preview

        args.output.write_text(discovery_preview(args.seed))
        print(args.output)
        return
    if args.command == "discovery-recovery":
        from epistemics.discovery.simulation import recovery_study as discovery_recovery

        data = discovery_recovery(args.seeds, args.blocks)
        args.output.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
        print(json.dumps({k: v for k, v in data.items() if k != "runs"}, indent=2))
        if not data["passed"]:
            raise SystemExit(1)
        return
    if args.command == "discovery-demo":
        from epistemics.discovery.simulation import demo as discovery_demo

        report = discovery_demo(
            args.seed,
            model=args.model,
            source_frame=args.source_frame,
            output_frame=args.output_frame,
        )
        args.output.write_text(report.model_dump_json(indent=2) + "\n")
        print(
            json.dumps(
                {
                    "report": str(args.output),
                    "metrics": report.metrics,
                    "observer_rmse": {
                        k: v.growth_report_rmse for k, v in report.observer_models.items()
                    },
                },
                indent=2,
            )
        )
        return
    if args.command == "company-preview":
        from epistemics.company.simulation import preview

        args.output.write_text(preview(args.seed))
        print(args.output)
        return
    if args.command == "company-recovery":
        from epistemics.company.simulation import recovery_study

        data = recovery_study(args.seeds)
        args.output.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "passed": data["passed_recovery_gates"],
                    "summary": data["summary"],
                },
                indent=2,
            )
        )
        if not data["passed_recovery_gates"]:
            raise SystemExit(1)
        return
    if args.command == "company-demo":
        from epistemics.company.simulation import demo as company_demo

        report = company_demo(
            args.seed,
            positive=args.positive_weight,
            negative=args.negative_weight,
            duplicate=args.duplicate_weight,
            auxiliary_shift=args.auxiliary_shift,
        )
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
