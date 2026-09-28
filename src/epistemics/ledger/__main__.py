"""Ledger commands: build the ledger, or print the tables the docs report.

uv run python -m epistemics.ledger build [--output output/ledger.json]
uv run python -m epistemics.ledger runs <root>
uv run python -m epistemics.ledger retest <first root> <second root>
uv run python -m epistemics.ledger contrast <root>
"""

import argparse
import json
from pathlib import Path

from epistemics.ledger import dispositions
from epistemics.ledger.build import build


def fmt(value):
    if value is None:
        return "—"
    if isinstance(value, dict) and "mean" in value:
        low, high = value.get("interval_90", [None, None])
        return f"{value['mean']:.2f}" + (f" [{low:.2f}, {high:.2f}]" if low is not None else "")
    if isinstance(value, list):
        return ", ".join(f"{v:.2f}" for v in value)
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def runs_table(root):
    lines = ["| Run | Module | Variant | Headline |", "| --- | --- | --- | --- |"]
    for record in dispositions.extract(root):
        s = dispositions.summary(record)
        if not s.get("verified", True):
            lines.append(f"| {record['run_id']} | — | — | not verified: {s['error']} |")
            continue
        if s["module"] == "checks":
            headline = f"λ linear {fmt(s['certainty_value_linear'])}; exact decision value {s['exact_decision_value']}/24"
        elif s["module"] in ("corroboration", "disclosure"):
            headline = f"disposition {fmt(s['disposition'])}; γ {s['gamma']:.2f}; τ {s['report_sd']:.2f}; exact at 50% {s['exact_indifference']}/24"
            if "learning" in s:
                x = s["learning"]
                headline += f"; start {fmt(x['start'])}, κ {x['strength']:.1f}, P(learning) {x['learning_probability']:.2f}"
        else:
            headline = f"implied {fmt(s['implied'])}; stated {fmt(s['stated'])}"
        lines.append(f"| {record['run_id']} | {s['module']} | {s['variant']} | {headline} |")
    return "\n".join(lines)


def verified_pairs(root):
    records = dispositions.extract(root)
    return [(r, dispositions.summary(r)) for r in records if r.get("verified")]


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--registry", type=Path, default=Path("docs/experiments.json"))
    b.add_argument("--output", type=Path, default=Path("output/ledger.json"))
    r = sub.add_parser("runs")
    r.add_argument("root", type=Path)
    t = sub.add_parser("retest")
    t.add_argument("first", type=Path)
    t.add_argument("second", type=Path)
    c = sub.add_parser("contrast")
    c.add_argument("root", type=Path)
    v = sub.add_parser("variance")
    v.add_argument("roots", type=Path, nargs="+")
    v.add_argument("--configuration", required=True)
    v.add_argument("--module", default="corroboration-cues")
    v.add_argument("--variant", default="cues-a")
    v.add_argument("--levels", type=int, nargs="+", default=[1, 2, 3])
    v.add_argument("--order-policy", default="random", help="'any' to pool every order policy")
    val = sub.add_parser("variance-validate")
    val.add_argument("--output", type=Path, required=True)
    val.add_argument("--seed", type=int, default=20260928)
    val.add_argument("--repetitions", type=int, default=30)
    a = parser.parse_args()
    if a.command == "build":
        ledger = build(a.registry)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"output": str(a.output), **ledger["totals"]}, indent=2))
    elif a.command == "runs":
        print(runs_table(a.root))
    elif a.command == "retest":
        rows = dispositions.retest(verified_pairs(a.first), verified_pairs(a.second))
        print(
            "| Configuration | Module | Variant | First | Retest | Mean absolute difference | Rank agreement |"
        )
        print("| --- | --- | --- | --- | --- | --- | --- |")
        for x in rows:
            print(
                f"| {x['configuration']} | {x['module']} | {x['variant']} | {fmt(x['first'])} | {fmt(x['second'])} | {x['mean_absolute_difference']:.2f} | {fmt(x['rank_agreement'])} |"
            )
    elif a.command == "contrast":
        contrast = dispositions.range_contrast(verified_pairs(a.root))
        print(json.dumps(contrast, indent=2))
    elif a.command == "variance":
        from epistemics.ledger import variance

        y, s, used = [], [], []
        for root in a.roots:
            for record in dispositions.extract(root):
                if not (
                    record.get("verified")
                    and record["configuration"] == a.configuration
                    and record["module"] == a.module
                    and record["variant"] == a.variant
                    and (a.order_policy == "any" or record["order_policy"] == a.order_policy)
                ):
                    continue
                chosen = [record["slot_fits"][level]["implied"] for level in a.levels]
                y.append([c["mean"] for c in chosen])
                s.append(variance.standard_errors([c["interval_90"] for c in chosen]))
                used.append(record["run_id"])
        result = variance.estimate(y, s)
        print(json.dumps({"configuration": a.configuration, "runs": used, **result}, indent=2))
    else:
        from epistemics.ledger import variance

        result = variance.validate(a.seed, repetitions=a.repetitions)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        for cell in result["cells"]:
            print(json.dumps({k: round(v, 3) for k, v in cell.items()}))


if __name__ == "__main__":
    main()
