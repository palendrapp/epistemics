import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from epistemics.discovery.inference import forecast
from epistemics.study.design import create_manifest, digest, episode, load_manifest, write_manifest
from epistemics.study.fit import fit_reports, load_reports, prepare
from epistemics.study.inference import covariance, observed_vector, predict
from epistemics.study.models import EpisodeReport, StudyManifest, StudyProfile, StudyTrial
from epistemics.study.runner import call, collect_episode, server_parameters
from epistemics.study.service import StudyService, export_reports
from epistemics.study.simulation import answers_from_vector, make_reports, synthetic_agent


def manifest(**kwargs):
    return create_manifest(
        synthetic_agent(), worlds=4, replicates=1, seed=78, response_origin="synthetic", **kwargs
    )


def constant_answer(trial):
    return {
        "target_probability": 0.5,
        "growth_quantiles_pct": {"p10": 4, "p50": 12, "p90": 20},
        "decision": "invest",
        "evidence_ids": [],
        "source_accuracy": {s: 0.5 for s in trial["source_probe_ids"]},
        "conditional_growth_probability": 0.5 if trial["conditional_probe"] else None,
        "extracted_values": {k: 0.0 for k in trial["extraction_keys"]},
    }


def test_matched_design_initial_source_probe_and_grouped_split():
    m = manifest()
    assert len(m.assignments) == 32
    for world in {a.world_id for a in m.assignments}:
        rows = [a for a in m.assignments if a.world_id == world]
        assert len(rows) == 8 and len({a.split for a in rows}) == 1
        assert len({a.seed for a in rows}) == 1
        records = [episode(a) for a in rows]
        assert all(not s["archive"] for r in records for s in r[0]["trial"]["sources"])
        assert all(len(r[1]["trial"]["sources"][0]["archive"]) in (2, 8) for r in records)
        assert all(
            r[0]["truth"]["realized_growth_pct"] == records[0][0]["truth"]["realized_growth_pct"]
            for r in records
        )
        assert all(r[-1]["trial"]["index"] == 10 for r in records)
    altered = m.model_dump()
    altered["assignments"][0]["split"] = "heldout" if m.assignments[0].split == "train" else "train"
    with pytest.raises(ValueError, match="one partition"):
        StudyManifest.model_validate(altered)


def test_factorized_observer_matches_enumerated_joint_and_uses_public_data_only(monkeypatch):
    records = episode(manifest().assignments[0])
    import epistemics.study.design as design

    monkeypatch.setattr(
        design, "episode", lambda *_: (_ for _ in ()).throw(AssertionError("private read"))
    )
    for step in (1, 3, 5, 7, 8, 10):
        t = StudyTrial.model_validate(records[step]["trial"])
        for alpha in (0, 1):
            # The old battery has no pre-archive checkpoint; only its index differs.
            expected = forecast(t.model_copy(update={"index": step - 1}), source_frame=alpha)
            actual = predict(t, [[alpha, 1, 0, 0]])
            assert actual["growth"][0] == pytest.approx(expected.growth_probability, abs=1e-12)
            assert actual["conditional"][0] == pytest.approx(
                expected.conditional_growth_probability, abs=1e-12
            )
            assert actual["quantiles"][0] == pytest.approx(
                list(expected.growth_quantiles_pct.model_dump().values()), abs=1e-7
            )
            for sid in actual["sources"]:
                assert actual["sources"][sid][0] == pytest.approx(
                    expected.source_accuracy[sid], abs=1e-12
                )
    # A deterministic model adds no independent information.
    assert predict(StudyTrial.model_validate(records[4]["trial"]), [[0, 1, 0, 0]])[
        "growth"
    ] == pytest.approx(
        predict(StudyTrial.model_validate(records[5]["trial"]), [[0, 1, 0, 0]])["growth"]
    )


def test_archive_weight_and_profile_prior_have_distinct_signatures():
    records = episode(manifest().assignments[0])
    first = StudyTrial.model_validate(records[0]["trial"])
    later = StudyTrial.model_validate(records[7]["trial"])
    before = StudyTrial.model_validate(records[6]["trial"])
    assert predict(first, [[1, 0, 0, 0]])["sources"]["beacon"] == pytest.approx(
        predict(first, [[1, 2, 0, 0]])["sources"]["beacon"]
    )
    assert predict(first, [[-1, 1, 0, 0]])["sources"]["beacon"] != pytest.approx(
        predict(first, [[1, 1, 0, 0]])["sources"]["beacon"]
    )
    assert predict(before, [[0, 0, 0, 0]])["growth"] == pytest.approx(
        predict(later, [[0, 0, 0, 0]])["growth"]
    )
    assert (
        abs(
            predict(before, [[0, 1, 0, 0]])["growth"][0]
            - predict(later, [[0, 1, 0, 0]])["growth"][0]
        )
        > 1e-9
    )


def test_manifest_immutability_and_implementation_binding(tmp_path, monkeypatch):
    m = manifest()
    write_manifest(tmp_path, m)
    assert load_manifest(tmp_path)[0] == m
    with pytest.raises(FileExistsError):
        write_manifest(tmp_path, m)
    import epistemics.study.design as design

    monkeypatch.setattr(design, "implementation_sha256", lambda: "f" * 64)
    with pytest.raises(ValueError, match="fingerprint"):
        load_manifest(tmp_path)
    (tmp_path / "manifest.json").write_text(m.model_dump_json())
    with pytest.raises(ValueError, match="bytes changed"):
        load_manifest(tmp_path)


def test_service_retries_order_private_visibility_and_export_barrier(tmp_path):
    m = manifest()
    write_manifest(tmp_path, m)
    service = StudyService(tmp_path, m.assignments[0].assignment_id)
    first = service.get_trial()
    assert not {"seed", "split", "truth", "source_parameters", "private_case"} & set(first)
    assert "seed" not in json.dumps(service.describe())
    with pytest.raises(ValueError, match="Complete every"):
        service.finish()
    trial = first["trial"]
    answer = constant_answer(trial)
    with pytest.raises(ValueError, match="current trial"):
        service.submit("study10", answer)
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(lambda _: service.submit(trial["trial_id"], answer), range(4)))
    assert all(x == receipts[0] for x in receipts)
    with pytest.raises(ValueError, match="cannot be changed"):
        service.submit(trial["trial_id"], {**answer, "target_probability": 0.7})
    while not (current := service.get_trial())["complete"]:
        t = current["trial"]
        service.submit(t["trial_id"], constant_answer(t))
    assert (
        service.finish()
        == service.finish()
        == {"complete": True, "answered": 11, "report_stored": True}
    )
    with pytest.raises(ValueError, match="All planned"):
        export_reports(tmp_path)


@pytest.fixture(scope="module")
def fitted_data():
    m = manifest()
    reports = make_reports(m, params=(1, 0.5, -1, 0), beta=0.4, noise=False)
    grid, prepared = prepare(reports, m.analysis_plan)
    return m, reports, grid, prepared


def test_joint_parameter_recovery_and_heldout_exclusion(fitted_data):
    m, reports, grid, prepared = fitted_data
    profile = fit_reports(m, "0" * 64, reports, {}, bootstrap=5, prepared_data=(grid, prepared))
    for key, expected in zip(profile.parameters, [1, 0.5, -1, 0, 0.4], strict=True):
        tolerance = 0.15 if key == "relationship_prior" else 0.03
        assert profile.parameters[key].estimate == pytest.approx(expected, abs=tolerance)
        lo, hi = profile.parameters[key].interval_95
        assert lo <= expected <= hi
    assert profile.diagnostics["predictive_adequacy_passed"]
    altered = []
    for p in prepared:
        p = dict(p)
        if p["report"].assignment.split == "heldout":
            p["observed"] = p["observed"] + 4
            residual = p["observed"] - p["pred"]
            inv = np.linalg.inv(
                covariance([o.trial for o in p["report"].observations], m.analysis_plan)
            )
            p["a"] = np.sum((residual @ inv) * residual, axis=1)
            p["b"] = (residual @ inv) @ p["w"]
        altered.append(p)
    again = fit_reports(m, "0" * 64, reports, {}, bootstrap=5, prepared_data=(grid, altered))
    for key in profile.parameters:
        assert profile.parameters[key].estimate == again.parameters[key].estimate
        assert profile.parameters[key].interval_95 == again.parameters[key].interval_95
    for name in profile.model_comparisons:
        assert (
            profile.model_comparisons[name]["training_log_evidence"]
            == again.model_comparisons[name]["training_log_evidence"]
        )
    assert (
        again.diagnostics["heldout_standardized_rmse"]
        > profile.diagnostics["heldout_standardized_rmse"]
    )
    assert all(p.status == "unidentified" for p in again.parameters.values())


def test_report_export_integrity_and_mixed_configuration_rejection(tmp_path, fitted_data):
    m, reports, _, _ = fitted_data
    write_manifest(tmp_path, m)
    for report in reports:
        service = StudyService(tmp_path, report.assignment.assignment_id)
        for o in report.observations:
            service.submit(o.trial.trial_id, o.answer)
        service.finish()
    hashes = export_reports(tmp_path)
    assert hashes == export_reports(tmp_path)
    assert len(load_reports(tmp_path)[2]) == 32
    filename = next(iter(hashes))
    path = tmp_path / "reports" / filename
    data = json.loads(path.read_text())
    data["agent"]["model"] = "different"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="bytes"):
        load_reports(tmp_path)
    hashes[filename] = digest(path.read_bytes())
    (tmp_path / "report-hashes.json").write_text(json.dumps(hashes))
    with pytest.raises(ValueError, match="configuration"):
        load_reports(tmp_path)


def test_endpoint_reports_and_correlated_covariance(fitted_data):
    m, reports, _, _ = fitted_data
    report = reports[0].model_copy(deep=True)
    report.observations[0].answer.target_probability = 0
    report.observations[1].answer.target_probability = 1
    vector = observed_vector(report.observations, m.analysis_plan)
    assert np.isfinite(vector).all()
    cov = covariance([o.trial for o in report.observations], m.analysis_plan)
    assert np.linalg.eigvalsh(cov).min() > 0
    assert cov[0, 1] > 0 and cov[0, -1] > 0
    answers = answers_from_vector([o.trial for o in report.observations], vector)
    assert len(answers) == 11


def test_actual_mcp_bound_assignment_no_evaluator_controls(tmp_path):
    m = manifest()
    write_manifest(tmp_path, m)

    async def run():
        params = server_parameters(tmp_path, m.assignments[0].assignment_id)
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == {
                "describe_battery",
                "get_trial",
                "submit_answer",
                "finish_evaluation",
            }
            assert all("seed" not in t.inputSchema.get("properties", {}) for t in tools.tools)
            assert (await client.call_tool("finish_evaluation", {})).isError
            for _ in range(11):
                t = (await call(client, "get_trial"))["trial"]
                args = {"trial_id": t["trial_id"], "answer": constant_answer(t)}
                receipt = await call(client, "submit_answer", args)
                assert receipt == await call(client, "submit_answer", args)
            assert await call(client, "finish_evaluation") == {
                "complete": True,
                "answered": 11,
                "report_stored": True,
            }

    asyncio.run(run())


def test_runner_fresh_process_public_history_resume_and_attempt_log(tmp_path):
    m = manifest()
    write_manifest(tmp_path, m)
    script = tmp_path / "respondent.py"
    script.write_text("""import json,sys,os
assert "EPISTEMICS_STUDY" not in os.environ
for line in sys.stdin:
    message=json.loads(line)
    if message["type"]=="start":
        assert "seed" not in message and "assignment" not in message
        print("pid="+str(os.getpid())+" history="+str(len(message["history"])),file=sys.stderr)
    if message["type"]=="trial":
        t=message["trial"]
        answer={"target_probability":0.5,"growth_quantiles_pct":{"p10":4,"p50":12,"p90":20},"decision":"invest","evidence_ids":[],"source_accuracy":{s:0.5 for s in t["source_probe_ids"]},"conditional_growth_probability":0.5 if t["conditional_probe"] else None,"extracted_values":{k:0.0 for k in t["extraction_keys"]}}
        print(json.dumps({"answer":answer}),flush=True)
""")
    first = StudyService(tmp_path, m.assignments[0].assignment_id)
    t = first.get_trial()["trial"]
    first.submit(t["trial_id"], constant_answer(t))

    async def run():
        for a in m.assignments[:2]:
            assert await collect_episode(tmp_path, a, {"command": [sys.executable, str(script)]})
        assert not await collect_episode(
            tmp_path, m.assignments[0], {"command": [sys.executable, str(script)]}
        )

    asyncio.run(run())
    logs = [
        (tmp_path / f"respondent-{a.assignment_id}.stderr").read_text() for a in m.assignments[:2]
    ]
    assert "history=1" in logs[0] and "history=0" in logs[1]
    assert logs[0].split()[0] != logs[1].split()[0]
    attempts = [json.loads(x) for x in (tmp_path / "attempts.jsonl").read_text().splitlines()]
    assert [a["status"] for a in attempts] == ["running", "completed", "running", "completed"]


def test_study_schemas_match():
    for contract, filename in [
        (StudyManifest, "study.v1.json"),
        (EpisodeReport, "study-episode.v1.json"),
        (StudyProfile, "study-profile.v1.json"),
    ]:
        expected = contract.model_json_schema()
        expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        assert json.loads((Path("schemas") / filename).read_text()) == expected


def test_continuous_refinement_recovers_between_grid_parameters(fitted_data):
    m, _, grid, prepared = fitted_data
    true = [0.6, 0.8, -0.6, 0.2, 0.25]
    reports = make_reports(m, params=true[:4], beta=true[4], noise=False)
    changed = []
    for original, report in zip(prepared, reports, strict=True):
        observed = observed_vector(report.observations, m.analysis_plan)
        residual = observed - original["pred"]
        inv = np.linalg.inv(covariance([o.trial for o in report.observations], m.analysis_plan))
        changed.append(
            {
                **original,
                "report": report,
                "observed": observed,
                "a": np.sum((residual @ inv) * residual, axis=1),
                "b": (residual @ inv) @ original["w"],
            }
        )
    result = fit_reports(m, "0" * 64, reports, {}, bootstrap=10, prepared_data=(grid, changed))
    assert result.diagnostics["continuous_refinement_converged"]
    for key, expected in zip(result.parameters, true, strict=True):
        parameter = result.parameters[key]
        # Two training worlds leave the business prior weak enough for visible prior shrinkage.
        tolerance = 0.1 if key == "relationship_prior" else 0.03
        assert parameter.estimate == pytest.approx(expected, abs=tolerance)
        assert parameter.interval_95[0] <= expected <= parameter.interval_95[1]
        assert parameter.interval_95[1] > parameter.interval_95[0]
        assert parameter.grid_resolution is None


def test_recovery_artifact_is_serializable_and_retains_every_attempt(tmp_path):
    from epistemics.study.simulation import recovery_study

    result = recovery_study(tmp_path, worlds=4, repetitions=1)
    saved = json.loads((tmp_path / "recovery.json").read_text())
    assert saved == json.loads(json.dumps(result, allow_nan=False))
    assert len(saved["runs"]) == 8
    assert len((tmp_path / "recovery-runs.jsonl").read_text().splitlines()) == 8
    assert (tmp_path / "recovery.sha256").read_text().strip() == digest(
        (tmp_path / "recovery.json").read_bytes()
    )
    assert saved["gates"]["misspecification_detected"]
    assert saved["gates"]["off_grid_recovery_error"]
