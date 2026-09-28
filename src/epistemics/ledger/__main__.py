"""Ledger commands: build the ledger, or print the tables the docs report.

uv run python -m epistemics.ledger build [--output output/ledger.json]
uv run python -m epistemics.ledger runs <root>
uv run python -m epistemics.ledger retest <first root> <second root>
uv run python -m epistemics.ledger contrast <root>
uv run python -m epistemics.ledger transfer <roots...>
uv run python -m epistemics.ledger noticing <roots...>
uv run python -m epistemics.ledger inclusion [--configuration astra --configuration sol]
uv run python -m epistemics.ledger inclusion-validate --output <file>
uv run python -m epistemics.ledger inclusion-joint [--configuration astra --configuration sol]
uv run python -m epistemics.ledger inclusion-joint-validate --output <file>
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
    b.add_argument("--guide", type=Path, default=Path("output/guide.json"))
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
    tr = sub.add_parser("transfer")
    tr.add_argument("roots", type=Path, nargs="+")
    no = sub.add_parser("noticing")
    no.add_argument("roots", type=Path, nargs="+")
    inc = sub.add_parser("inclusion")
    inc.add_argument("--ledger", type=Path, default=Path("output/ledger.json"))
    inc.add_argument("--configuration", action="append", default=None)
    ij = sub.add_parser("inclusion-joint")
    ij.add_argument("--ledger", type=Path, default=Path("output/ledger.json"))
    ij.add_argument("--configuration", action="append", default=None)
    ijv = sub.add_parser("inclusion-joint-validate")
    ijv.add_argument("--output", type=Path, required=True)
    ijv.add_argument("--datasets", type=int, default=30)
    ijv.add_argument("--models", type=int, default=12)
    fv = sub.add_parser("fidelity-validate")
    fv.add_argument("--output", type=Path, required=True)
    fv.add_argument("--datasets", type=int, default=20)
    iv = sub.add_parser("inclusion-validate")
    iv.add_argument("--output", type=Path, required=True)
    iv.add_argument("--datasets", type=int, default=40)
    cs = sub.add_parser("cues-summary")
    cs.add_argument("roots", type=Path, nargs="+")
    val = sub.add_parser("variance-validate")
    val.add_argument("--output", type=Path, required=True)
    val.add_argument("--seed", type=int, default=20260928)
    val.add_argument("--repetitions", type=int, default=30)
    a = parser.parse_args()
    if a.command == "build":
        ledger = build(a.registry)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(ledger, indent=2, sort_keys=True, allow_nan=False) + "\n")
        a.guide.write_text(json.dumps(ledger["guide"], indent=2, allow_nan=False) + "\n")
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
    elif a.command == "transfer":
        from epistemics.ledger import transfer

        records = [r for root in a.roots for r in dispositions.extract(root)]
        print(json.dumps(transfer.analyse(records), indent=2))
    elif a.command == "noticing":
        from epistemics.ledger import transfer

        records = [r for root in a.roots for r in dispositions.extract(root)]
        print(json.dumps(transfer.noticing(records), indent=2))
    elif a.command == "inclusion":
        from epistemics.ledger import inclusion

        models = json.loads(a.ledger.read_text())["models"]
        result = {}
        for config in a.configuration or ["astra", "sol"]:
            rows = inclusion.ledger_sessions(models, config)
            result[config] = {v: inclusion.fit(rows, v) for v in inclusion.VARIANTS}
        print(json.dumps(result, indent=2))
    elif a.command == "inclusion-joint":
        from epistemics.ledger import inclusion
        from epistemics.ledger import inclusion_joint as joint

        models = json.loads(a.ledger.read_text())["models"]
        result = {}
        for config in a.configuration or ["astra", "sol"]:
            rows, ids = inclusion.ledger_sessions(models, config, with_ids=True)
            fits = {
                f"{variant}/{stated}": joint.sample(rows, variant, stated, 4, 20000, 8000)
                for variant in ("shared", "theta_by_family")
                for stated in ("considered", "applied", "mixture")
            }
            comparisons = {
                "applied minus considered (shared)": joint.compare(
                    fits["shared/applied"], fits["shared/considered"]
                ),
                "applied minus considered (theta by family)": joint.compare(
                    fits["theta_by_family/applied"], fits["theta_by_family/considered"]
                ),
                "theta by family minus shared (considered)": joint.compare(
                    fits["theta_by_family/considered"], fits["shared/considered"]
                ),
                "theta by family minus shared (applied)": joint.compare(
                    fits["theta_by_family/applied"], fits["shared/applied"]
                ),
                "mixture minus considered (shared)": joint.compare(
                    fits["shared/mixture"], fits["shared/considered"]
                ),
                "mixture minus applied (shared)": joint.compare(
                    fits["shared/mixture"], fits["shared/applied"]
                ),
            }
            # Robustness: the stated channel at all five levels.
            fits["shared/mixture (all levels)"] = joint.sample(
                rows, "shared", "mixture", 4, 20000, 8000, stated_levels=(0, 1, 2, 3, 4)
            )
            fits["shared/mixture (all levels)"]["waic"].pop("elpd_pointwise")
            fits["shared/mixture (all levels)"].pop("session_fidelity")
            fidelity = fits["shared/mixture"]["session_fidelity"]
            fits["shared/mixture"]["session_fidelity"] = {
                fam: {
                    sid: p for sid, p in zip(ids[fam], probabilities, strict=True) if p is not None
                }
                for fam, probabilities in fidelity.items()
            }
            for fit_ in fits.values():
                fit_["waic"].pop("elpd_pointwise", None)
            result[config] = {"fits": fits, "comparisons": comparisons}
        print(json.dumps(result, indent=2))
    elif a.command == "inclusion-joint-validate":
        from epistemics.ledger import inclusion_joint as joint

        run = joint.validate(datasets=a.datasets, models=a.models)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n")
        summary = {
            k: run[k]
            for k in ("metrics", "converged_only", "converged_datasets", "stated_model_recovery")
        }
        print(json.dumps(summary, indent=2))
    elif a.command == "fidelity-validate":
        from epistemics.ledger import inclusion_joint as joint

        run = joint.validate_fidelity(datasets=a.datasets)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"phi": run["phi"], "rhat_max": max(run["rhat_by_dataset"])}, indent=2))
    elif a.command == "inclusion-validate":
        from epistemics.ledger import inclusion

        runs = {
            f"{variant}-{seed}": inclusion.validate(seed, a.datasets, variant)
            for variant, seeds in (
                ("shared", (20260928, 20261028)),
                ("theta_by_family", (20260928,)),
            )
            for seed in seeds
        }
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(runs, indent=2, sort_keys=True) + "\n")
        for key, run in runs.items():
            print(
                key,
                json.dumps(
                    {k: {m: round(v, 3) for m, v in x.items()} for k, x in run["metrics"].items()}
                ),
            )
    elif a.command == "cues-summary":
        import numpy as np

        groups = {}
        for root in a.roots:
            for record, s in verified_pairs(root):
                if s["module"].endswith(("-cues", "-dossier", "-unprompted", "-asked", "-probed")):
                    groups.setdefault(
                        (record["configuration"], s["module"], s["variant"]), []
                    ).append(s)
        print(
            "| Configuration | Module | Set | Sessions | Mean mapping | Suggestive − reassuring | "
            "Median τ | Sessions coherent within 0.10 | Irrelevant level |"
        )
        print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for (config, module, variant), rows in sorted(groups.items()):
            implied = np.array([r["implied"] for r in rows])
            mean = implied.mean(axis=0)
            gaps = [r["stated_minus_implied_max"] for r in rows]
            coherent = "—" if None in gaps else f"{sum(g <= 0.10 for g in gaps)}/{len(rows)}"
            print(
                f"| {config} | {module} | {variant} | {len(rows)} | {fmt(list(mean))} | "
                f"{mean[-1] - mean[0]:.2f} | {np.median([r['report_sd'] for r in rows]):.2f} | "
                f"{coherent} | {fmt(list(implied[:, 2]))} |"
            )
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
