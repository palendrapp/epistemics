"""Clef pilot commands (docs/clef-pilot-design.md). Live commands need CLOUDFLARE_ACCOUNT_ID and
CLOUDFLARE_API_TOKEN in the environment.

uv run python -m epistemics.clef smoke --out output/clef-smoke-<date> [--model clef ...]
uv run python -m epistemics.clef plan --root output/clef-pilot-<date> [--model clef ...]
uv run python -m epistemics.clef run --root output/clef-pilot-<date> [--limit N]
"""

import argparse
import sys

from epistemics.clef import pilot, requests
from epistemics.clef.client import ClefError, Client


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m epistemics.clef")
    sub = parser.add_subparsers(dest="command", required=True)
    smoke = sub.add_parser("smoke")
    smoke.add_argument("--out", required=True)
    smoke.add_argument("--model", action="append", choices=tuple(requests.MODELS))
    plan = sub.add_parser("plan")
    plan.add_argument("--root", required=True)
    plan.add_argument("--model", action="append", choices=tuple(requests.MODELS))
    run = sub.add_parser("run")
    run.add_argument("--root", required=True)
    run.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    models = tuple(args.model) if getattr(args, "model", None) else tuple(requests.MODELS)
    try:
        if args.command == "plan":
            document = pilot.plan(args.root, models)
            print(f"{len(document['calls'])} calls planned: {document['counts']}")
        elif args.command == "smoke":
            pilot.smoke(args.out, Client.from_env(), models)
        else:
            remaining = pilot.run(args.root, Client.from_env(), args.limit)
            sys.exit(1 if remaining and args.limit is None else 0)
    except ClefError as error:
        sys.exit(f"clef: {error}")


if __name__ == "__main__":
    main()
