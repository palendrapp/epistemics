import asyncio
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.benchmark.analysis import analyze, lock_predictions, paired_comparison
from epistemics.benchmark.cli import cost_projection
from epistemics.benchmark.models import (
    Acceptance,
    BenchmarkManifest,
    BenchmarkReport,
    BenchmarkSpec,
)
from epistemics.benchmark.runner import admit, command, read_usage
from epistemics.benchmark.store import accounting, create, database, guard, load
from epistemics.predictive.collection import CollectionService
from epistemics.predictive.design import create_manifest, digest, episode, write_manifest
from epistemics.predictive.models import Parameters
from epistemics.predictive.simulation import simulate, validation


def setup(tmp_path, *, purpose="prediction_pilot", origin="synthetic"):
    design = create_manifest(seed=222, replicates=2)
    write_manifest(tmp_path / "design", design)
    spec = BenchmarkSpec(
        purpose=purpose,
        configurations=[
            {"configuration_id": "alpha", "model": "fixture-alpha", "reasoning_effort": "low"},
            {"configuration_id": "beta", "model": "fixture-beta", "reasoning_effort": "medium"},
        ],
        budget={"max_attempts": 300, "max_processed_tokens": 1000000, "max_wall_seconds": 30000},
        acceptance={"bootstrap_draws": 100},
        cost_basis="Offline synthetic fixture, no inference cost",
    )
    root = tmp_path / "benchmark"
    manifest = create(
        tmp_path / "design", root, spec, codex_version="fixture-cli", response_origin=origin
    )
    return root, manifest, design


def fill(root, manifest, design, split, *, same=False):
    for i, configuration in enumerate(manifest.configurations):
        generated = simulate(design, Parameters(copy_weight=0 if same else i))
        values = {(r.assignment_id, r.index): r for r in generated}
        for assignment in design.assignments:
            if assignment.split != split:
                continue
            service = CollectionService(
                root / "collections" / configuration.configuration_id, assignment.assignment_id
            )
            for checkpoint in episode(assignment):
                row = values[(assignment.assignment_id, checkpoint.index)]
                service.submit(
                    checkpoint.checkpoint_id,
                    {"probability": row.response, "decision": row.decision},
                )
            service.finish()


def test_freeze_stage_gates_predictions_and_complete_report(tmp_path):
    root, manifest, design = setup(tmp_path)
    heldout = next(a for a in design.assignments if a.split == "heldout")
    with pytest.raises(ValueError, match="locked first"):
        guard(root, "alpha", heldout.assignment_id)
    with pytest.raises(ValueError, match="profile cases first"):
        lock_predictions(root)
    fill(root, manifest, design, "profile")
    raw = lock_predictions(root)
    assert lock_predictions(root) == raw
    locked = json.loads(raw)
    assert locked["configurations"]["alpha"]["individual_fit"]["parameters"][
        "copy_weight"
    ] == pytest.approx(0, abs=1e-12)
    assert locked["configurations"]["beta"]["individual_fit"]["parameters"][
        "copy_weight"
    ] == pytest.approx(1)
    with pytest.raises(ValueError, match="policy partition"):
        guard(root, "alpha", heldout.assignment_id)
    fill(root, manifest, design, "policy")
    guard(root, "alpha", heldout.assignment_id)
    with pytest.raises(ValueError, match="Every planned"):
        analyze(root)
    fill(root, manifest, design, "heldout")
    report_bytes = analyze(root)
    report = BenchmarkReport.model_validate_json(report_bytes)
    assert analyze(root) == report_bytes
    assert report.response_origin == "synthetic"
    assert report.lock_sha256 == digest(raw)
    assert report.cohort["matched_groups"] == 24
    assert report.cohort["macro_rmse"]["individual"] < 1e-12
    assert report.result == "criteria_met"
    assert all(len(v["post_evidence_prediction"]) == 6 for v in report.configurations.values())
    assert report.accounting["totals"]["marginal_usd"] is None
    assert validation(design).passed


def test_no_personalization_signal_yields_null_result():
    design = create_manifest(seed=123, replicates=2)
    values = [r for r in simulate(design, Parameters()) if r.split == "heldout"]
    datasets = {"a": values, "b": values}
    predictions = {
        cid: {
            name: np.array([r.response for r in values])
            for name in (
                "individual",
                "pooled",
                "reference_calibration",
                "one_gain_all_reports",
                "persistence",
                "raw_source_sensitivity",
            )
        }
        for cid in datasets
    }
    result = paired_comparison(datasets, predictions, Acceptance(bootstrap_draws=100))
    assert not result["criteria_met"]
    assert result["comparisons"]["pooled"]["rmse_improvement"] == 0
    assert result["comparisons"]["pooled"]["interval_95"] == [0, 0]


def test_opening_future_cases_invalidates_freeze(tmp_path):
    root, manifest, design = setup(tmp_path)
    fill(root, manifest, design, "profile")
    assignment = next(a for a in design.assignments if a.split == "heldout")
    # Deliberate operator bypass of the guarded MCP endpoint must be detected before locking.
    CollectionService(root / "collections" / "alpha", assignment.assignment_id).get_trial()
    with pytest.raises(ValueError, match="already been opened"):
        lock_predictions(root)


def test_manifest_rebinding_and_source_drift_fail(tmp_path, monkeypatch):
    root, _, _ = setup(tmp_path)
    path = root / "benchmark.json"
    value = json.loads(path.read_bytes())
    value["budget"]["max_processed_tokens"] += 1
    path.write_text(json.dumps(value))
    (root / "benchmark.sha256").write_text(digest(path.read_bytes()))
    with pytest.raises(ValueError, match="Stored benchmark binding"):
        with database(root):
            pass
    monkeypatch.setattr("epistemics.benchmark.store.fingerprint", lambda: "0" * 64)
    with pytest.raises(ValueError, match="source fingerprint changed"):
        load(root)


def test_development_cannot_be_promoted_and_costs_are_not_dollars(tmp_path):
    root, manifest, design = setup(tmp_path, purpose="development_costing")
    with pytest.raises(ValueError, match="cannot be promoted"):
        lock_predictions(root)
    with pytest.raises(ValueError, match="cannot produce"):
        analyze(root)
    with pytest.raises(ValueError, match="predeclared pair"):
        cost_projection(root, 2)
    for configuration in manifest.configurations:
        for i in range(2):
            with database(root) as (db, _, _):
                db.execute(
                    "INSERT INTO runs VALUES (?, ?)",
                    (
                        f"{configuration.configuration_id}{i}",
                        json.dumps(
                            {
                                "configuration_id": configuration.configuration_id,
                                "status": "completed",
                                "usage": {
                                    "input_tokens": 1000,
                                    "cached_input_tokens": 200,
                                    "output_tokens": 100,
                                },
                                "elapsed_seconds": 10,
                            }
                        ),
                    ),
                )
    estimate = cost_projection(root, 2)
    assert estimate["marginal_usd"] is None
    assert estimate["configurations"]["alpha"]["projected_processed_tokens"] == 144 * 1100
    assert estimate["configurations"]["alpha"]["suggested_token_admission_budget"] == 144 * 2200
    assert accounting(root)["totals"]["processed_tokens"] == 4400


@pytest.mark.parametrize(
    "field",
    [
        "attempts",
        "processed_tokens",
        "elapsed_seconds",
        "unknown_usage_attempts",
        "unresolved_attempts",
    ],
)
def test_resource_limits_stop_before_another_episode(tmp_path, field):
    _, manifest, _ = setup(tmp_path)
    totals = dict.fromkeys(
        [
            "attempts",
            "processed_tokens",
            "elapsed_seconds",
            "unknown_usage_attempts",
            "unresolved_attempts",
        ],
        0,
    )
    totals[field] = 1000001
    with pytest.raises(ValueError):
        admit(manifest, totals)


def test_provider_usage_and_command_configuration(tmp_path):
    root, manifest, design = setup(tmp_path)
    assert read_usage(
        {
            "input_tokens": 100,
            "cached_input_tokens": 80,
            "output_tokens": 20,
            "reasoning_output_tokens": 10,
        }
    ) == {"input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 20}
    for bad in (
        None,
        {},
        {"input_tokens": True, "cached_input_tokens": 0, "output_tokens": 1},
        {"input_tokens": 1, "cached_input_tokens": 2, "output_tokens": 0},
    ):
        with pytest.raises(ValueError):
            read_usage(bad)
    argv = command(root, manifest.configurations[0], design.assignments[0].assignment_id)
    assert "--ephemeral" in argv and "--ignore-user-config" in argv
    assert "read-only" in argv and "--dangerously-bypass-approvals-and-sandbox" not in argv
    assert 'web_search="disabled"' in argv
    assert "shell_tool" in argv
    assert any("epistemics.benchmark.mcp_server" in a for a in argv)
    assert len([a for a in argv if a.endswith('.approval_mode="approve"')]) == 4
    assert not any("default_tools_approval_mode" in a for a in argv)


def test_benchmark_mcp_only_exposes_current_public_episode(tmp_path):
    root, _, design = setup(tmp_path)
    assignment = next(a for a in design.assignments if a.split == "profile")

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.benchmark.mcp_server"],
            env={
                "EPISTEMICS_BENCHMARK": str(root),
                "EPISTEMICS_CONFIGURATION": "alpha",
                "EPISTEMICS_ASSIGNMENT": assignment.assignment_id,
            },
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            assert {t.name for t in (await client.list_tools()).tools} == {
                "describe_battery",
                "get_trial",
                "submit_answer",
                "finish_evaluation",
            }
            result = await client.call_tool("get_trial", {})
            assert not result.isError
            data = json.loads(result.content[0].text)
            assert data["checkpoint"]["index"] == 0
            assert data["checkpoint"]["evidence"] == []
            for text in ("matched_group", "design_sha256", "reasoning_effort", "budget", "split"):
                assert text not in result.content[0].text

    asyncio.run(run())


def test_schema_snapshots():
    for model, name in (
        (BenchmarkSpec, "prediction-benchmark-spec.v1"),
        (BenchmarkManifest, "prediction-benchmark.v1"),
        (BenchmarkReport, "prediction-benchmark-report.v1"),
    ):
        stored = json.loads((Path(__file__).parents[1] / "schemas" / f"{name}.json").read_bytes())
        stored.pop("$schema")
        assert model.model_json_schema() == stored


def test_actual_process_events_and_mcp_collection_accounted_offline(tmp_path, monkeypatch):
    import os

    from epistemics.benchmark.runner import run_episode

    root, manifest, design = setup(tmp_path, purpose="development_costing")
    assignment = next(a for a in design.assignments if a.split == "heldout")
    # A synthetic process exercises real MCP transport and the runner's JSON-event parser.
    fake = tmp_path / "respondent.py"
    fake.write_text("""import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def run():
    p=StdioServerParameters(command=sys.executable,args=["-m","epistemics.benchmark.mcp_server"],env={"EPISTEMICS_BENCHMARK":sys.argv[1],"EPISTEMICS_CONFIGURATION":sys.argv[2],"EPISTEMICS_ASSIGNMENT":sys.argv[3]})
    async with stdio_client(p) as (r,w), ClientSession(r,w) as c:
        await c.initialize()
        async def call(name,args={}):
            result=await c.call_tool(name,args)
            if result.isError: raise RuntimeError(str(result.content))
            print(json.dumps({"type":"item.completed","item":{"type":"mcp_tool_call","server":"episode","tool":name}}),flush=True)
            return json.loads(result.content[0].text)
        while not (trial:=await call("get_trial"))["complete"]:
            await call("submit_answer",{"checkpoint_id":trial["checkpoint"]["checkpoint_id"],"answer":{"probability":0.6,"decision":"act"}})
        await call("finish_evaluation")
    print(json.dumps({"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":50,"output_tokens":20}}),flush=True)
asyncio.run(run())
""")
    monkeypatch.setattr(
        "epistemics.benchmark.runner.command",
        lambda d, c, a: [sys.executable, str(fake), str(d), c.configuration_id, a],
    )
    result = asyncio.run(
        run_episode(root, manifest.configurations[0], assignment.assignment_id, 30)
    )
    assert result["status"] == "completed"
    assert len(result["tool_calls"]) == 14
    assert accounting(root)["totals"]["processed_tokens"] == 120
    assert not result["violation"]
    assert os.stat(next((root / "private-run-logs").glob("*.stderr"))).st_mode & 0o777 == 0o600


def test_failed_process_preserves_unknown_cost_and_blocks_next_call(tmp_path, monkeypatch):
    from epistemics.benchmark.runner import run_episode

    root, manifest, design = setup(tmp_path, purpose="development_costing")
    assignment = next(a for a in design.assignments if a.split == "heldout")
    monkeypatch.setattr(
        "epistemics.benchmark.runner.command",
        lambda d, c, a: [sys.executable, "-c", "raise SystemExit(1)"],
    )
    with pytest.raises(RuntimeError, match="process failed"):
        asyncio.run(run_episode(root, manifest.configurations[0], assignment.assignment_id, 30))
    totals = accounting(root)["totals"]
    assert totals["attempts"] == 1
    assert totals["unknown_usage_attempts"] == 1
    with pytest.raises(ValueError, match="unknown-cost"):
        admit(manifest, totals)
