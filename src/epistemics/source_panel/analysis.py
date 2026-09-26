"""Descriptive matched comparisons; no independent-trial population inference."""

import json
from pathlib import Path

import numpy as np

from epistemics.source_inference.measurement import GAINS, sample_reports
from epistemics.source_inference.observers import FAMILIES
from epistemics.source_learning.inference import forecast
from epistemics.source_learning.service import export
from epistemics.source_learning.storage import digest, encoded, save
from epistemics.source_panel.service import PanelService


def rmse(observed, expected):
    return float(100 * np.sqrt(np.mean((np.asarray(observed) - np.asarray(expected)) ** 2)))


def first_reports(report):
    return np.array([o.answer.probability for o in report.observations[:12]])


def adequacy(raws, answers, profile, *, seed=20260926, draws=256):
    rng = np.random.default_rng(seed)
    blocks = [str(i) for i in range(len(raws))]
    result = {}
    for family in FAMILIES:
        logits = np.array([r[family]["logit"] for r in raws])
        mean = np.array([forecast(r, profile)["family_means"][family] for r in raws])
        samples = [
            rmse(
                sample_reports(
                    logits, rng.choice(GAINS, p=profile["gain_probabilities"][family]), blocks, rng
                ),
                mean,
            )
            for _ in range(draws)
        ]
        error, boundary = rmse(answers, mean), float(np.quantile(samples, 0.99))
        result[family] = {
            "rmse_pp": error,
            "conditional_99_percent_boundary_pp": boundary,
            "outside_boundary": error > boundary,
        }
    return result


def summarize(root):
    root = Path(root)
    plan_raw = (root / "plan.json").read_bytes()
    if digest(plan_raw) != (root / "plan.sha256").read_text().strip():
        raise ValueError("Panel plan changed")
    plan = json.loads(plan_raw)
    reports, evidence = {}, {}
    for entry in plan["runs"]:
        directory = root / "collections" / entry["run_id"]
        report = export(directory)
        if (
            report.manifest.design_seed != plan["world_seeds"][entry["world"]]
            or report.manifest.condition != entry["condition"]
        ):
            raise ValueError("Report does not match planned assignment")
        reports[entry["run_id"]] = report
        evidence[entry["run_id"]] = PanelService(directory).evidence()
        if evidence[entry["run_id"]]["binding"]["presentation"] != entry["presentation"]:
            raise ValueError("Unexpected presentation")
    frozen = json.loads((root / "frozen-profiles.json").read_bytes())
    for rid, expected in frozen["training_reports_sha256"].items():
        if digest((root / "collections" / rid / "report.json").read_bytes()) != expected:
            raise ValueError("Training evidence changed after profile freeze")
    for entry in plan["runs"]:
        if entry["phase"] == "transfer":
            binding = evidence[entry["run_id"]]["binding"]
            expected = {
                "configuration": frozen["configuration"][entry["configuration"]],
                "shared": frozen["shared"],
            }
            if (
                binding["profiles"] != expected
                or binding["profile_frozen_at"] != frozen["frozen_at"]
            ):
                raise ValueError("Transfer binding differs from frozen training profiles")
    configurations = list(plan["configurations"])

    def select(**criteria):
        return [r for r in plan["runs"] if all(r[k] == v for k, v in criteria.items())]

    repeats, between, dense = [], [], []
    for world in ("a", "b"):
        means = {}
        for config in configurations:
            entries = select(phase="baseline", configuration=config, world=world)
            values = [first_reports(reports[e["run_id"]]) for e in entries]
            if len(values) != 2:
                raise ValueError("Expected two sparse repeats")
            means[config] = np.mean(values, axis=0)
            repeats.append(
                {"configuration": config, "world": world, "initial_report_rmse_pp": rmse(*values)}
            )
            (dense_entry,) = select(phase="dense", configuration=config, world=world)
            d = first_reports(reports[dense_entry["run_id"]])
            dense.append(
                {
                    "configuration": config,
                    "world": world,
                    "dense_vs_sparse_mean_rmse_pp": rmse(d, means[config]),
                    "mean_signed_change_pp": float(100 * np.mean(d - means[config])),
                    "sparse_repeat_rmse_pp": rmse(*values),
                    "scope": "Matched first twelve unaudited reports; one dense context versus mean of two sparse contexts",
                }
            )
        between.append(
            {
                "world": world,
                "configuration_mean_rmse_pp": rmse(*(means[c] for c in configurations)),
            }
        )

    transfer, format_contrasts = [], []
    for config in configurations:
        by_format = {}
        for entry in select(phase="transfer", configuration=config):
            rid = entry["run_id"]
            report, transport = reports[rid], evidence[rid]
            p = first_reports(report)
            locks = transport["locks"]
            errors = {
                name: rmse(p, [r["prediction"][name] for r in locks[:12]])
                for name in locks[0]["prediction"]
            }
            all_errors = {
                name: rmse(
                    [o.answer.probability for o in report.observations],
                    [r["prediction"][name] for r in locks],
                )
                for name in locks[0]["prediction"]
            }
            transfer.append(
                {
                    "configuration": config,
                    "presentation": entry["presentation"],
                    "world": entry["world"],
                    "primary_first_twelve_rmse_pp": errors,
                    "secondary_all_36_conditional_path_rmse_pp": all_errors,
                    "configuration_family_adequacy_first_twelve": adequacy(
                        [r["raw"] for r in report.prediction_locks[:12]],
                        p,
                        transport["binding"]["profiles"]["configuration"],
                    ),
                    "predictions_locked_before_answers": True,
                }
            )
            by_format[entry["presentation"]] = p
        format_contrasts.append(
            {
                "configuration": config,
                "first_twelve_format_rmse_pp": rmse(by_format["structured"], by_format["packet"]),
            }
        )

    per_run = []
    for entry in plan["runs"]:
        report = reports[entry["run_id"]]
        per_run.append(
            {
                **entry,
                "analysis": report.analysis,
                "calibration_family": report.fit_lock["fit"]["decision"],
                "report_sha256": digest(
                    (root / "collections" / entry["run_id"] / "report.json").read_bytes()
                ),
                "transport_evidence_sha256": digest(encoded(evidence[entry["run_id"]])),
            }
        )
    result = {
        "schema_version": "epistemics.source-panel-summary.v1",
        "plan_sha256": digest(plan_raw),
        "runs": per_run,
        "within_configuration_repeatability": repeats,
        "between_configuration_initial_reports": between,
        "dense_elicitation": dense,
        "transfer": transfer,
        "format_contrasts": format_contrasts,
        "limitations": [
            "Two configurations, two development worlds, one held-out transfer world; no population interval or stable trait claim.",
            "The first twelve unaudited reports have matched evidence; later research choices can change public paths.",
            "Dense presentation changes prompting and reporting burden together; sparse repeat variation contextualizes rather than identifies treatment uncertainty.",
            "Transfer changes factual presentation only; numeric business rates and bounded source structure remain disclosed.",
            "Local source-learning fits in transfer artifacts are diagnostics only; the panel's configuration/shared profiles are frozen from baseline calibration before transfer begins.",
            "Report prediction, resolved-outcome performance, research policy and buyer decision benefit are different claims; no support or buyer policy was tested.",
            "Conditional simulation envelopes assume the specified noise model and are not calibrated composite tests.",
        ],
    }
    save(root / "summary.json", encoded(result))
    return result
