import argparse
import json
from pathlib import Path

from epistemics.disposition_tasks.render import COVERS, MODULES, render
from epistemics.source_learning.storage import encoded, save


def show(module, cover):
    lines = [f"# {module} / {cover}", ""]
    for i in range(24):
        case = render(module, cover, i)
        lines += [f"## Item {i}", "", case["case"], "", f"**{case['question']}**", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Disposition checkpoint tasks (development only)")
    sub = parser.add_subparsers(dest="command", required=True)
    sample = sub.add_parser("sample")
    sample.add_argument("--module", choices=MODULES, required=True)
    sample.add_argument("--cover", choices=COVERS, default="markets")
    validate = sub.add_parser("validate")
    validate.add_argument("--seed", type=int, required=True)
    validate.add_argument("--output", type=Path, required=True)
    demo = sub.add_parser("demo")
    demo.add_argument("--directory", type=Path, required=True)
    demo.add_argument("--module", choices=MODULES, default="corroboration")
    demo.add_argument("--cover", choices=COVERS, default="markets")
    demo.add_argument("--seed", type=int, default=1)
    out = sub.add_parser("export")
    out.add_argument("--directory", type=Path, required=True)
    a = parser.parse_args()
    if a.command == "sample":
        print(show(a.module, a.cover))
    elif a.command == "validate":
        from epistemics.disposition_tasks.validation import validate as run_validation

        result = run_validation(a.seed)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        save(a.output, encoded(result))
        print(json.dumps({"passed": result["passed"], "audit": result["audit"]}))
        if not result["passed"]:
            raise SystemExit(1)
    elif a.command == "demo":
        import numpy as np

        from epistemics.disposition_tasks.simulation import simulate

        if a.module == "checks":
            truth = {
                "function": "entropy",
                "certainty_value": 60.0,
                "decision_weight": 1.0,
                "wtp_sd": 3.0,
            }
        else:
            truth = {"disposition": 0.4, "gamma": 1.0, "bias": 0.0, "report_sd": 0.2}
        order = np.random.default_rng(a.seed).permutation(24).tolist()
        report = simulate(
            a.directory, module=a.module, cover=a.cover, order=order, truth=truth, seed=a.seed
        )
        print(json.dumps({k: v for k, v in report.analysis.items() if k != "rows"}, indent=2))
    else:
        from epistemics.disposition_tasks.collection import export

        export(a.directory)


if __name__ == "__main__":
    main()
