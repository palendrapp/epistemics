import copy
import json
import math
import stat
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from epistemics.predictive.analysis import (
    conditional_task_metrics,
    features,
    fit_profile,
    predict,
    reference_probability,
)
from epistemics.predictive.design import (
    STRUCTURES,
    budget,
    create_manifest,
    episode,
    load_manifest,
    public_checkpoint,
    write_manifest,
)
from epistemics.predictive.models import (
    DesignManifest,
    Parameters,
    PublicCheckpoint,
    Response,
    SyntheticValidation,
)
from epistemics.predictive.simulation import simulate, validation


@pytest.fixture
def manifest():
    return create_manifest(seed=2026)


def test_balanced_matched_design_has_structurally_disjoint_partitions(manifest):
    assert create_manifest(seed=2026) == manifest
    assert len(manifest.assignments) == 72
    assert budget(manifest)["checkpoints_per_configuration"] == 360
    groups = {}
    families = {}
    for assignment in manifest.assignments:
        groups.setdefault(assignment.matched_group, []).append(assignment)
        families.setdefault(assignment.split, set()).add(assignment.family)
    assert len(groups) == 36
    assert len(set.union(*families.values())) == 3
    for rows in groups.values():
        assert len(rows) == 2
        assert len({a.split for a in rows}) == 1
        assert len({a.seed for a in rows}) == 1
        twins = [episode(a) for a in rows]
        for left, right in zip(twins[0], twins[1], strict=True):
            assert left.company == right.company
            assert left.question == right.question
            assert left.prior_probability == right.prior_probability
            for a, b in zip(left.evidence, right.evidence, strict=True):
                # Only declared provenance differs; substantive claims and archives match.
                assert a.model_dump(exclude={"based_on", "provenance_note"}) == b.model_dump(
                    exclude={"based_on", "provenance_note"}
                )
    assert STRUCTURES["interleaved_chains"][-1][1] == 2


@pytest.mark.parametrize("mutation", ["split", "provenance", "seed", "id", "missing"])
def test_manifest_rejects_split_leakage_and_incomplete_factor_cells(manifest, mutation):
    value = manifest.model_dump()
    first = value["assignments"][0]
    if mutation == "split":
        first["split"] = "heldout" if first["split"] != "heldout" else "profile"
    elif mutation == "provenance":
        first["provenance"] = "copied" if first["provenance"] == "independent" else "independent"
    elif mutation == "seed":
        first["seed"] += 1
    elif mutation == "id":
        first["assignment_id"] = value["assignments"][1]["assignment_id"]
    else:
        value["assignments"].pop()
    with pytest.raises(ValueError):
        DesignManifest.model_validate(value)


def test_public_views_have_only_current_evidence_and_no_design_or_answer_keys(manifest):
    forbidden = {
        "seed",
        "split",
        "family",
        "matched_group",
        "direction",
        "strength",
        "truth",
        "reference",
        "likelihood",
        "assignments",
    }

    def keys(value):
        if isinstance(value, dict):
            return set(value) | set().union(*(keys(v) for v in value.values()))
        if isinstance(value, list):
            return set().union(*(keys(v) for v in value))
        return set()

    for assignment in manifest.assignments:
        full = episode(assignment)
        for index, view in enumerate(full):
            assert len(view.evidence) == index
            assert view.evidence == full[-1].evidence[:index]
            assert not forbidden & keys(view.model_dump())
        with pytest.raises(ValueError, match="index"):
            public_checkpoint(assignment, len(full))
    with pytest.raises(ValueError):
        Response(probability=float("nan"), decision="act")


def test_public_provenance_rejects_cycles_inconsistent_copies_and_future_documents(manifest):
    assignment = next(
        a for a in manifest.assignments if a.split == "heldout" and a.provenance == "copied"
    )
    raw = episode(assignment)[-1].model_dump()
    for patch in [
        {"based_on": "document-5"},
        {"based_on": "unknown"},
        {
            "assessment": "misses_target"
            if raw["evidence"][2]["assessment"] == "meets_target"
            else "meets_target"
        },
    ]:
        changed = copy.deepcopy(raw)
        changed["evidence"][2].update(patch)
        with pytest.raises(ValueError):
            PublicCheckpoint.model_validate(changed)
    raw["index"] -= 1
    with pytest.raises(ValueError, match="index|prefix"):
        PublicCheckpoint.model_validate(raw)


def test_transitive_copies_do_not_change_reference_and_features_use_public_data_only(
    manifest, monkeypatch
):
    assignment = next(
        a
        for a in manifest.assignments
        if a.split == "heldout"
        and a.provenance == "copied"
        and a.direction == 1
        and a.strength == "strong"
        and a.prior == 0.5
    )
    checkpoints = episode(assignment)
    import epistemics.predictive.design as design

    monkeypatch.setattr(design, "episode", lambda *_: pytest.fail("Private assignment lookup"))
    public = PublicCheckpoint.model_validate_json(checkpoints[-1].model_dump_json())
    independent = math.log(4) - math.log(13 / 7)
    copies = 2 * math.log(4) - math.log(13 / 7)
    assert features(public) == pytest.approx([1, 0, independent, copies])
    assert reference_probability(public) == pytest.approx(28 / 41)
    assert all(reference_probability(c) == pytest.approx(28 / 41) for c in checkpoints[2:])
    assert features(checkpoints[0]) == pytest.approx([1, 0, 0, 0])


def test_identification_and_fitting_partition_are_enforced(manifest):
    rows = simulate(manifest, Parameters(copy_weight=0.63))
    train = [r for r in rows if r.split == "profile"]
    fit = fit_profile(train, manifest.analysis_plan)
    assert fit["parameters"]["copy_weight"] == pytest.approx(0.63)
    assert fit["n_matched_groups"] == 12
    independent = [r for r in train if r.x[3] == 0]
    with pytest.raises(ValueError, match="rank"):
        fit_profile(independent, manifest.analysis_plan)
    for split in ("policy", "heldout"):
        with pytest.raises(ValueError, match="reserved"):
            fit_profile([*train, next(r for r in rows if r.split == split)], manifest.analysis_plan)
    # Changing final-test answers cannot feed back into a profile fit.
    changed = [replace(r, response=1 - r.response) if r.split == "heldout" else r for r in rows]
    assert fit_profile([r for r in changed if r.split == "profile"], manifest.analysis_plan) == fit


@pytest.mark.parametrize("seed", [19, 2026, 7182])
def test_noisy_recovery_structural_prediction_and_misspecification_control(seed):
    manifest = create_manifest(seed=seed)
    report = validation(manifest, seed=seed)
    assert report.passed, report.checks
    assert report.response_origin == "synthetic"
    assert len(report.recovery) == 4
    assert report.misspecification["detected"]
    assert (
        report.misspecification["heldout"]["probability_rmse"]
        > manifest.analysis_plan.heldout_probability_rmse_limit
    )
    assert all(r["noiseless_max_parameter_error"] < 1e-10 for r in report.recovery)
    assert all(r["fitted"]["interval_95"] is not None for r in report.recovery)


def test_behavior_prediction_and_conditional_task_quality_are_distinct(manifest):
    rows = simulate(manifest, Parameters(copy_weight=1))
    train = [r for r in rows if r.split == "profile"]
    test = [r for r in rows if r.split == "heldout"]
    fit = fit_profile(train, manifest.analysis_plan, bootstrap=False)
    assert predict(test, fit) == pytest.approx([r.response for r in test], abs=1e-12)
    assert conditional_task_metrics(test)["excess_brier"] > 0
    reference = simulate(manifest, Parameters())
    metrics = conditional_task_metrics(reference)
    assert metrics["excess_brier"] == pytest.approx(0, abs=1e-12)
    assert metrics["expected_decision_regret"] == pytest.approx(0, abs=1e-12)
    assert np.isfinite(metrics["expected_brier"])


def test_manifest_byte_immutability_private_permissions_and_version_binding(
    manifest, tmp_path, monkeypatch
):
    path = write_manifest(tmp_path / "design", manifest)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert load_manifest(path.parent) == manifest
    with pytest.raises(FileExistsError):
        write_manifest(path.parent, manifest)
    import epistemics.predictive.design as design

    with monkeypatch.context() as patch:
        patch.setattr(design, "implementation_sha256", lambda: "a" * 64)
        with pytest.raises(ValueError, match="fingerprint"):
            load_manifest(path.parent)
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="bytes changed"):
        load_manifest(path.parent)


def test_cli_design_preview_validation_and_no_overwrite(tmp_path):
    def run(*args):
        return subprocess.run(
            [sys.executable, "-m", "epistemics.cli", *map(str, args)],
            capture_output=True,
            text=True,
        )

    directory = tmp_path / "design"
    created = run("predictive", "create", "--output", directory, "--seed", "1909")
    assert created.returncode == 0, created.stderr
    assert json.loads(created.stdout)["budget"]["episodes_per_configuration"] == 72
    manifest = load_manifest(directory)
    preview = tmp_path / "preview.json"
    args = (
        "predictive",
        "preview",
        "--design",
        directory,
        "--assignment",
        manifest.assignments[0].assignment_id,
        "--index",
        "1",
        "--output",
        preview,
    )
    assert run(*args).returncode == 0
    assert len(json.loads(preview.read_bytes())["evidence"]) == 1
    assert run(*args).returncode != 0
    output = tmp_path / "validation.json"
    checked = run("predictive", "validate-synthetic", "--design", directory, "--output", output)
    assert checked.returncode == 0, checked.stderr
    assert SyntheticValidation.model_validate_json(output.read_bytes()).passed
    assert run("validate", output).returncode == 0


@pytest.mark.parametrize(
    "contract,filename",
    [
        (DesignManifest, "predictive-design.v1.json"),
        (PublicCheckpoint, "predictive-checkpoint.v1.json"),
        (SyntheticValidation, "predictive-validation.v1.json"),
    ],
)
def test_predictive_schemas_match_exported_contracts(contract, filename):
    expected = contract.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert json.loads((Path("schemas") / filename).read_bytes()) == expected
