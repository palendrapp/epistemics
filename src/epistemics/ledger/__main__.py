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
uv run python -m epistemics.ledger inclusion-hier [--family relay ...] [--output <file>]
uv run python -m epistemics.ledger inclusion-hier-validate --output <file>
uv run python -m epistemics.ledger inclusion-hier-power --output <file> [--spot-structures 10]
uv run python -m epistemics.ledger traits --output <file> [--configuration astra ...]
uv run python -m epistemics.ledger traits-power --output <file>
uv run python -m epistemics.ledger battery-v2 --output <file>
uv run python -m epistemics.ledger battery-v2-recovery --output <file>
uv run python -m epistemics.ledger capacity-pilot <roots...> --output <file>
uv run python -m epistemics.ledger capacity-recovery --output <file>
uv run python -m epistemics.ledger capacity-load-recovery --module <m> --output <file>
uv run python -m epistemics.ledger capacity-pooled <roots...> --output <file>
uv run python -m epistemics.ledger social-recovery --output <file>
uv run python -m epistemics.ledger social-pilot <roots...> --output <file>
uv run python -m epistemics.ledger confidence-power --output <file>
uv run python -m epistemics.ledger confidence-transfer <roots...> --output <file>
uv run python -m epistemics.ledger position --output <file>
uv run python -m epistemics.ledger battery-v3-recovery --output <file>
uv run python -m epistemics.ledger battery-v3-power --output <file>
uv run python -m epistemics.ledger battery-v3 <roots...> --output <file>
uv run python -m epistemics.ledger battery-v31-recovery --output <file>
uv run python -m epistemics.ledger battery-v31-power --output <file>
uv run python -m epistemics.ledger battery-v31 <roots...> --output <file>
uv run python -m epistemics.ledger battery-v32-recovery --output <file>
uv run python -m epistemics.ledger battery-v32-power --output <file>
uv run python -m epistemics.ledger battery-v32 <roots...> --output <file>
uv run python -m epistemics.ledger cohere-validation --output <file>
uv run python -m epistemics.ledger cohere-a <roots...> --output <file>
uv run python -m epistemics.ledger cohere-b <roots...> --output <file>
uv run python -m epistemics.ledger statements-validation --output <file>
uv run python -m epistemics.ledger sweep --output <file>
uv run python -m epistemics.ledger roundness --output <file>
uv run python -m epistemics.ledger deliberation-validation --output <file>
uv run python -m epistemics.ledger deliberation-pilot <roots...> --output <file>
uv run python -m epistemics.ledger deliberation-followup <roots...> --output <file>
uv run python -m epistemics.ledger deliberation-frames <roots...> [--baseline <roots...>] --output <file>
uv run python -m epistemics.ledger deliberation-quality <roots...> --output <file>
uv run python -m epistemics.ledger followups <roots...> --output <file>
uv run python -m epistemics.ledger announced-count <roots...> --output <file>
uv run python -m epistemics.ledger correlated-changes <roots...> --output <file>
uv run python -m epistemics.ledger primacy --statements <roots...> --correlated <roots...> --output <file>
uv run python -m epistemics.ledger statements-probe <roots...> --output <file>
uv run python -m epistemics.ledger statements-a <roots...> --output <file>
uv run python -m epistemics.ledger statements-explore <roots...> --output <file>
uv run python -m epistemics.ledger statements-b <roots...> --output <file>
uv run python -m epistemics.ledger screen-validation --output <file>
uv run python -m epistemics.ledger screen-a <roots...> --output <file>
uv run python -m epistemics.ledger screen-b <roots...> --output <file>
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
    ij.add_argument("--format", choices=("dossier", "urn", "urn2"), default="dossier")
    ij.add_argument(
        "--family",
        action="append",
        default=None,
        help="Fit only these structures (the per-structure analysis); mixture model only",
    )
    ijv = sub.add_parser("inclusion-joint-validate")
    ijv.add_argument("--output", type=Path, required=True)
    ijv.add_argument("--datasets", type=int, default=30)
    ijv.add_argument("--models", type=int, default=12)
    ijv.add_argument("--format", choices=("dossier", "urn"), default="dossier")
    ih = sub.add_parser("inclusion-hier")
    ih.add_argument("--ledger", type=Path, default=Path("output/ledger.json"))
    ih.add_argument("--configuration", action="append", default=None)
    ih.add_argument(
        "--family",
        action="append",
        default=None,
        help="Structures to pool (default: relay, disclosure, copying, selection, mismatch)",
    )
    ih.add_argument("--output", type=Path, default=None)
    ihv = sub.add_parser("inclusion-hier-validate")
    ihv.add_argument("--output", type=Path, required=True)
    ihv.add_argument("--datasets", type=int, default=30)
    ihv.add_argument("--workers", type=int, default=8)
    tr = sub.add_parser("traits")
    tr.add_argument("--ledger", type=Path, default=Path("output/ledger.json"))
    tr.add_argument("--output", type=Path, required=True)
    tr.add_argument("--configuration", action="append", default=None)
    bv = sub.add_parser("battery-v2")
    bv.add_argument("--ledger", type=Path, default=Path("output/ledger.json"))
    bv.add_argument("--output", type=Path, required=True)
    bvr = sub.add_parser("battery-v2-recovery")
    bvr.add_argument("--output", type=Path, required=True)
    bvr.add_argument("--datasets", type=int, default=24)
    cp = sub.add_parser("capacity-pilot")
    cp.add_argument("roots", type=Path, nargs="+")
    cp.add_argument("--output", type=Path, required=True)
    cr = sub.add_parser("capacity-recovery")
    cr.add_argument("--output", type=Path, required=True)
    cr.add_argument("--respondents", type=int, default=100)
    cr.add_argument("--load-respondents", type=int, default=100)
    for name in ("battery-v3-recovery", "battery-v3-power"):
        sub.add_parser(name).add_argument("--output", type=Path, required=True)
    b3 = sub.add_parser("battery-v3")
    b3.add_argument("roots", type=Path, nargs="+")
    b3.add_argument("--output", type=Path, required=True)
    sub.add_parser("screen-validation").add_argument("--output", type=Path, required=True)
    sub.add_parser("cohere-validation").add_argument("--output", type=Path, required=True)
    sub.add_parser("statements-validation").add_argument("--output", type=Path, required=True)
    sub.add_parser("sweep").add_argument("--output", type=Path, required=True)
    sub.add_parser("roundness").add_argument("--output", type=Path, required=True)
    pr = sub.add_parser("primacy")
    pr.add_argument("--statements", type=Path, nargs="+", required=True)
    pr.add_argument("--correlated", type=Path, nargs="+", required=True)
    pr.add_argument("--calls", type=Path, nargs="*", default=[])
    pr.add_argument("--output", type=Path, required=True)
    for name in ("announced-count", "correlated-changes"):
        ac = sub.add_parser(name)
        ac.add_argument("roots", type=Path, nargs="+")
        ac.add_argument("--output", type=Path, required=True)
        if name == "correlated-changes":
            ac.add_argument("--key", choices=("correlated", "calls"), default="correlated")
    sub.add_parser("deliberation-validation").add_argument("--output", type=Path, required=True)
    for name in (
        "deliberation-pilot",
        "deliberation-followup",
        "deliberation-frames",
        "deliberation-quality",
        "followups",
    ):
        dp = sub.add_parser(name)
        dp.add_argument("roots", type=Path, nargs="+")
        dp.add_argument("--output", type=Path, required=True)
        if name == "deliberation-frames":
            dp.add_argument("--baseline", type=Path, nargs="*", default=[])
    for name in ("statements-probe", "statements-a", "statements-b", "statements-explore"):
        sp = sub.add_parser(name)
        sp.add_argument("roots", type=Path, nargs="+")
        sp.add_argument("--output", type=Path, required=True)
    for name in ("cohere-a", "cohere-b"):
        ca = sub.add_parser(name)
        ca.add_argument("roots", type=Path, nargs="+")
        ca.add_argument("--output", type=Path, required=True)
    for name in ("screen-a", "screen-b"):
        sa = sub.add_parser(name)
        sa.add_argument("roots", type=Path, nargs="+")
        sa.add_argument("--output", type=Path, required=True)
    for version in ("v31", "v32"):
        for name in (f"battery-{version}-recovery", f"battery-{version}-power"):
            sub.add_parser(name).add_argument("--output", type=Path, required=True)
        b31 = sub.add_parser(f"battery-{version}")
        b31.add_argument("roots", type=Path, nargs="+")
        b31.add_argument("--output", type=Path, required=True)
    pos = sub.add_parser("position")
    pos.add_argument("--output", type=Path, required=True)
    cfp = sub.add_parser("confidence-power")
    cfp.add_argument("--output", type=Path, required=True)
    cft = sub.add_parser("confidence-transfer")
    cft.add_argument("roots", type=Path, nargs="+")
    cft.add_argument("--output", type=Path, required=True)
    sp = sub.add_parser("social-pilot")
    sp.add_argument("roots", type=Path, nargs="+")
    sp.add_argument("--output", type=Path, required=True)
    sr = sub.add_parser("social-recovery")
    sr.add_argument("--output", type=Path, required=True)
    sr.add_argument("--respondents", type=int, default=100)
    sr.add_argument("--task", action="append", default=None)
    cpl = sub.add_parser("capacity-pooled")
    cpl.add_argument("roots", type=Path, nargs="+")
    cpl.add_argument("--output", type=Path, required=True)
    clr = sub.add_parser("capacity-load-recovery")
    clr.add_argument("--module", action="append", required=True)
    clr.add_argument("--respondents", type=int, default=100)
    clr.add_argument("--output", type=Path, required=True)
    tp = sub.add_parser("traits-power")
    tp.add_argument("--output", type=Path, required=True)
    ihp = sub.add_parser("inclusion-hier-power")
    ihp.add_argument("--output", type=Path, required=True)
    ihp.add_argument(
        "--recovery", type=Path, default=Path("output/inclusion-hier-recovery-20260929.json")
    )
    ihp.add_argument("--repetitions", type=int, default=400)
    ihp.add_argument("--spot-structures", type=int, default=None)
    ihp.add_argument("--spot-spread", type=float, default=0.1)
    ihp.add_argument("--spot-datasets", type=int, default=8)
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
            rows, ids = inclusion.ledger_sessions(models, config, with_ids=True, fmt=a.format)
            if not rows:
                continue
            if a.family:
                rows = {f: r for f, r in rows.items() if f in a.family}
                iterations, burn = joint.CHAINS[a.format]["fit"]
                fit_ = joint.sample(rows, "shared", "mixture", 4, iterations, burn)
                fit_["waic"].pop("elpd_pointwise", None)
                fit_["session_fidelity"] = {
                    fam: dict(zip(ids[fam], ps, strict=True))
                    for fam, ps in fit_["session_fidelity"].items()
                }
                result[config] = {"fits": {"shared/mixture": fit_}, "families": sorted(rows)}
                continue
            iterations, burn = joint.CHAINS[a.format]["fit"]
            fits = {
                f"{variant}/{stated}": joint.sample(rows, variant, stated, 4, iterations, burn)
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
                rows, "shared", "mixture", 4, iterations, burn, stated_levels=(0, 1, 2, 3, 4)
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

        run = joint.validate(datasets=a.datasets, models=a.models, fmt=a.format)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n")
        summary = {
            k: run[k]
            for k in ("metrics", "converged_only", "converged_datasets", "stated_model_recovery")
        }
        print(json.dumps(summary, indent=2))
    elif a.command == "inclusion-hier":
        from epistemics.ledger import inclusion
        from epistemics.ledger import inclusion_hier as hier

        models = json.loads(a.ledger.read_text())["models"]
        chosen = a.family or list(hier.FORMAT)
        result = {}
        for config in a.configuration or ["astra", "sol"]:
            rows = {}
            for fmt_ in ("dossier", "urn2"):
                rows.update(inclusion.ledger_sessions(models, config, fmt=fmt_))
            rows = {f: rows[f] for f in chosen if f in rows}
            result[config] = hier.sample(rows, workers=4)
        text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(text)
        print(text)
    elif a.command == "inclusion-hier-validate":
        from epistemics.ledger import inclusion_hier as hier

        run = hier.validate(datasets=a.datasets, workers=a.workers)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        summary = {
            k: run[k]
            for k in (
                "metrics",
                "spread_readings_by_true_spread",
                "wrong_direction_readings",
                "converged_datasets",
            )
        }
        print(json.dumps(summary, indent=2))
    elif a.command == "traits":
        import hashlib

        from epistemics.ledger import traits

        raw = a.ledger.read_bytes()
        models = json.loads(raw)["models"]
        if a.configuration:
            models = {
                **models,
                "sessions": [
                    s for s in models["sessions"] if s["configuration"] in a.configuration
                ],
            }
        checks = models.get("structure_checks")
        if checks and a.configuration:
            checks = {
                **checks,
                "checks": {c: v for c, v in checks["checks"].items() if c in a.configuration},
            }
        run = {
            **traits.analyse(models, checks),
            "ledger_sha256": hashlib.sha256(raw).hexdigest(),
            "configurations_filter": a.configuration,
        }
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(traits.table(run))
    elif a.command == "battery-v2":
        import hashlib

        from epistemics.ledger import battery_v2

        raw = a.ledger.read_bytes()
        models = json.loads(raw)["models"]
        run = {
            **battery_v2.analyse(models, models.get("structure_checks")),
            "ledger_sha256": hashlib.sha256(raw).hexdigest(),
        }
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        for trait, r in run["traits"].items():
            print(trait, r["role"], r["configurations"], r["tasks"], json.dumps(r.get("tests")))
    elif a.command == "battery-v2-recovery":
        from epistemics.ledger import battery_v2

        run = battery_v2.recovery(datasets=a.datasets)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps(run["pass_rates"], indent=2))
    elif a.command == "capacity-pilot":
        from epistemics.ledger import capacity

        run = capacity.pilot(a.roots)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(capacity.tables(run))
    elif a.command == "capacity-recovery":
        from epistemics.ledger import capacity

        run = capacity.recovery(a.respondents, a.load_respondents)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({k: run[k] for k in ("uptake", "load", "sessions_needed")}, indent=2))
    elif a.command in (
        "deliberation-validation",
        "deliberation-pilot",
        "deliberation-followup",
        "deliberation-frames",
        "deliberation-quality",
        "followups",
    ):
        from epistemics.ledger import deliberation as deliberation_ledger

        if a.command == "deliberation-validation":
            run = deliberation_ledger.validation()
            summary = {k: run[k] for k in ("rho", "a", "confusion", "a_on_own", "passed")}
        elif a.command == "followups":
            run = deliberation_ledger.followups(a.roots)
            summary = run["configurations"]
        elif a.command == "deliberation-quality":
            run = deliberation_ledger.quality(a.roots)
            summary = {"configurations": len(run["configurations"])}
        elif a.command == "deliberation-frames":
            run = deliberation_ledger.frames(a.roots, a.baseline)
            summary = run["families"]
        elif a.command == "deliberation-followup":
            run = deliberation_ledger.followup(a.roots)
            summary = {"configurations": len(run["configurations"])}
        else:
            run = deliberation_ledger.pilot(a.roots)
            summary = {
                k: run[k]
                for k in ("P1_grain", "P2_plateaus", "P3_anchoring", "P4_effort", "P5_seconds")
            }
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps(summary, indent=2))
    elif a.command == "primacy":
        from epistemics.ledger import primacy

        run = primacy.summary(a.statements, a.correlated, a.calls)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({"configurations": len(run["configurations"])}))
    elif a.command == "correlated-changes":
        from epistemics.ledger import correlated as correlated_ledger

        run = correlated_ledger.summary(a.roots, a.key)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(
            json.dumps(
                {c: {k: v[k] for k in ("a", "b")} for c, v in run["configurations"].items() if v},
                indent=2,
            )
        )
    elif a.command == "announced-count":
        from epistemics.ledger import announced as announced_ledger

        run = announced_ledger.summary(a.roots)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({c: v["restored"] for c, v in run["configurations"].items()}, indent=2))
    elif a.command == "roundness":
        from epistemics.ledger import roundness

        run = roundness.analyse()
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({k: run[k] for k in ("sessions", "sessions_with_current_design")}))
    elif a.command == "sweep":
        from epistemics.ledger import sweep

        run = sweep.sweep()
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({k: run[k] for k in ("answers", "runs")}, indent=2))
        for sig, v in run["stability"].items():
            print(sig, v["collections"], v["pairs"], v["mean_rho"])
    elif a.command.startswith("statements-"):
        from epistemics.ledger import statements as statements_ledger

        if a.command == "statements-validation":
            run = statements_ledger.validation()
            summary = {"passed": run["passed"], "law_rates": run["law_rates"]}
        elif a.command == "statements-probe":
            run = statements_ledger.probe(a.roots)
            summary = {"flagged": run["flagged"]}
        elif a.command == "statements-explore":
            run = statements_ledger.explore(a.roots)
            summary = {k: run[k] for k in ("step_by_announced", "first_step_by_announced")}
        elif a.command == "statements-a":
            run = statements_ledger.stage_a(a.roots)
            summary = {
                "incomplete": run["incomplete"],
                "H1": {k: v["departing"] for k, v in run["H1_readings_differ"]["slots"].items()},
                "H2": {law: run["H2_order_or_path"][law]["departing"] for law in ("order", "path")},
                "H3": run["H3_content"]["departing"],
            }
        else:
            run = statements_ledger.stage_b(a.roots)
            summary = {"passed": run["passed"]}
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps(summary, indent=2))
    elif a.command in ("cohere-validation", "cohere-a", "cohere-b"):
        from epistemics.ledger import cohere_sets

        if a.command == "cohere-validation":
            run = cohere_sets.validation()
            summary = {"families": run["families"], "passed": run["passed"]}
        elif a.command == "cohere-a":
            run = cohere_sets.stage_a(a.roots)
            summary = {
                f: {
                    k: v[k]
                    for k in ("H1_incoherent", "H2_open_above_computable", "H4_gpt56_above_gpt6")
                }
                for f, v in run["families"].items()
            }
        else:
            run = cohere_sets.stage_b(a.roots)
            summary = {"passed": run["passed"]}
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps(summary, indent=2))
    elif a.command in ("screen-validation", "screen-a", "screen-b"):
        from epistemics.ledger import screen as screen_ledger

        if a.command == "screen-validation":
            run = {
                "recovery": screen_ledger.recovery(),
                "calibration": screen_ledger.calibration(),
                "profile_recovery": screen_ledger.profile_recovery(configs=200),
            }
            run["passed"] = all(
                run[k]["passed"] for k in ("recovery", "calibration", "profile_recovery")
            )
            summary = {
                "recovery_passed": run["recovery"]["passed"],
                "calibration": run["calibration"]["result"],
                "profile_recovery_passed": run["profile_recovery"]["passed"],
                "passed": run["passed"],
            }
        elif a.command == "screen-a":
            run = screen_ledger.stage_a(a.roots)
            summary = {
                f: {n: c["passed"] for n, c in v["contrasts"].items()}
                for f, v in run["families"].items()
            }
        else:
            run = screen_ledger.stage_b(a.roots)
            summary = {"passed": run["passed"]}
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps(summary, indent=2))
    elif a.command.startswith(("battery-v31", "battery-v32")):
        from epistemics.ledger import battery_v31

        scheme = a.command.split("-")[1]
        if a.command.endswith("-recovery"):
            run = battery_v31.recovery(scheme=scheme)
        elif a.command.endswith("-power"):
            run = battery_v31.power(scheme=scheme)
        else:
            run = battery_v31.analyse(a.roots, scheme=scheme)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(
            json.dumps(
                run.get("parameters") or run.get("result") or run.get("generality"), indent=2
            )
        )
    elif a.command in ("battery-v3-recovery", "battery-v3-power", "battery-v3"):
        from epistemics.ledger import battery_v3

        if a.command == "battery-v3-recovery":
            run = battery_v3.recovery(configs=100)
        elif a.command == "battery-v3-power":
            run = battery_v3.power()
        else:
            run = battery_v3.analyse(a.roots)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(
            json.dumps(
                run.get("parameters") or run.get("result") or run.get("generality"), indent=2
            )
        )
    elif a.command == "position":
        from epistemics.ledger import position

        run = position.analyse()
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps(run["overall"], indent=2))
    elif a.command in ("confidence-power", "confidence-transfer"):
        from epistemics.ledger import confidence

        run = confidence.power() if a.command == "confidence-power" else confidence.analyse(a.roots)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps(run.get("result") or run["primary"], indent=2))
    elif a.command == "social-pilot":
        from epistemics.ledger import social

        run = social.pilot(a.roots)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(social.pilot_table(run))
    elif a.command == "social-recovery":
        from epistemics.ledger import social

        run = social.recovery(a.respondents, tasks=a.task)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(social.table(run))
    elif a.command == "capacity-pooled":
        from epistemics.ledger import capacity

        run = capacity.pooled_load(a.roots)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(capacity.pooled_table(run))
    elif a.command == "capacity-load-recovery":
        from epistemics.ledger import capacity

        run = {
            "schema_version": "epistemics.capacity-load-recovery.v1",
            "load_gates": capacity.LOAD_GATES,
            "load": capacity.load_recovery(a.respondents, modules=tuple(a.module)),
        }
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps(run["load"], indent=2))
    elif a.command == "traits-power":
        from epistemics.ledger import traits

        run = traits.power_table()
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        for r in run["rows"]:
            print(r)
    elif a.command == "inclusion-hier-power":
        import hashlib

        from epistemics.ledger import inclusion_hier as hier

        recovery_bytes = a.recovery.read_bytes()
        run = {
            "schema_version": "epistemics.inclusion-hier-power.v1",
            "surrogate_se": list(hier.SURROGATE_SE),
            "recovery": {
                "file": a.recovery.name,
                "sha256": hashlib.sha256(recovery_bytes).hexdigest(),
            },
            "surrogate_check": hier.surrogate_check(json.loads(recovery_bytes)),
            "power": hier.power(repetitions=a.repetitions),
            "spot_check": hier.spot_check(a.spot_structures, a.spot_spread, a.spot_datasets)
            if a.spot_structures
            else None,
            "scope": (
                "Surrogate: normal per-structure threshold estimates with posterior SDs uniform "
                "on the stated range, pooled on a grid with the hierarchical model's priors and "
                "decision rule; checked against the full model's recovery at five structures and, "
                "when requested, by full-model fits at a larger number of structures."
            ),
        }
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({k: run[k] for k in ("surrogate_check", "spot_check")}, indent=2))
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
                if s["module"].endswith(
                    ("-cues", "-dossier", "-unprompted", "-asked", "-probed", "-urn")
                ):
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
