import argparse
import json
from pathlib import Path

from epistemics.dispositions.validation import run


def main():
    parser = argparse.ArgumentParser(
        description="Offline recovery study for the disposition model; no respondent collection"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260927)
    parser.add_argument("--respondents", type=int, default=200)
    parser.add_argument("--model-datasets", type=int, default=100)
    parser.add_argument("--boundary-repetitions", type=int, default=25)
    args = parser.parse_args()
    try:
        result = run(
            args.output, args.seed, args.respondents, args.model_datasets, args.boundary_repetitions
        )
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "validation": str(args.output / "validation.json"),
                "sha256": result["sha256"],
                "implementation_sha256": result["plan"]["implementation_sha256"],
                "gates": result["gates"],
            },
            indent=2,
        )
    )
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
