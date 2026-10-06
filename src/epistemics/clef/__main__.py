"""Clef pilot commands (docs/clef-pilot-design.md). Live commands need CLOUDFLARE_ACCOUNT_ID and
CLOUDFLARE_API_TOKEN in the environment or in .env at the repository root.

uv run python -m epistemics.clef smoke --out output/clef-smoke-<date> [--model clef ...]
uv run python -m epistemics.clef plan --root output/clef-pilot-<date> [--model clef ...]
    [--design pilot|battery|far|desk|desk2|desk3|desk3-record|desk4]
uv run python -m epistemics.clef run --root output/clef-pilot-<date> [--limit N] [--workers N]
"""

import argparse
import sys

from epistemics.clef import pilot, requests
from epistemics.clef.client import ClefError, Client, load_env_file


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m epistemics.clef")
    sub = parser.add_subparsers(dest="command", required=True)
    smoke = sub.add_parser("smoke")
    smoke.add_argument("--out", required=True)
    smoke.add_argument("--model", action="append", choices=tuple(requests.MODELS))
    plan = sub.add_parser("plan")
    plan.add_argument("--root", required=True)
    plan.add_argument("--model", action="append", choices=tuple(requests.MODELS))
    plan.add_argument(
        "--design",
        choices=("pilot", "battery", "far", "desk", "desk2", "desk3", "desk3-record", "desk4"),
        default="pilot",
    )
    run = sub.add_parser("run")
    run.add_argument("--root", required=True)
    run.add_argument("--limit", type=int)
    run.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    models = tuple(args.model) if getattr(args, "model", None) else tuple(requests.MODELS)
    if args.command != "plan":
        load_env_file()
    try:
        if args.command == "plan":
            document = pilot.plan(args.root, models, args.design)
            print(f"{len(document['calls'])} calls planned: {document['counts']}")
        elif args.command == "smoke":
            pilot.smoke(args.out, Client.from_env(), models)
        else:
            remaining = pilot.run(args.root, Client.from_env(), args.limit, workers=args.workers)
            sys.exit(1 if remaining and args.limit is None else 0)
    except ClefError as error:
        sys.exit(f"clef: {error}")


if __name__ == "__main__":
    main()
