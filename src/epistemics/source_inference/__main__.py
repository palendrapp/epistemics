import argparse
import json
from pathlib import Path

from epistemics.source_inference.report import run


def main():
    parser = argparse.ArgumentParser(
        description="Offline source-inference design validation; no participant collection"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument("--repetitions", type=int, default=32)
    args = parser.parse_args()
    try:
        result = run(args.output, args.seed, args.repetitions)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "report": str(args.output / "report.md"),
                "response_origin": result["response_origin"],
                "gates": result["gates"],
            },
            indent=2,
        )
    )
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
