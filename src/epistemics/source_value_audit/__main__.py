"""Create a frozen offline plan, then execute it without any provider calls."""

import argparse
from pathlib import Path

from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_value_audit.experiment import make_plan, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("directory", type=Path)
    plan.add_argument("--batch-seeds", type=int, nargs="+", default=[20260927, 20270927])
    plan.add_argument("--worlds-per-batch", type=int, default=512)
    execute = commands.add_parser("run")
    execute.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "plan":
        raw = encoded(make_plan(args.batch_seeds, args.worlds_per_batch))
        args.directory.mkdir(parents=True, exist_ok=True)
        save(args.directory / "plan.json", raw)
        print(f"Frozen plan: {digest(raw)}", flush=True)
    else:
        result = run(args.directory, progress=lambda n: print(f"Completed {n} worlds", flush=True))
        print(
            f"Completed {result['world_count']} worlds / {result['case_count']} cases", flush=True
        )
        print(f"Summary: {digest(encoded(result))}", flush=True)


if __name__ == "__main__":
    main()
