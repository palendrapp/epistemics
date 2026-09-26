import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.service import now
from epistemics.source_learning.battery import public_trial
from epistemics.source_learning.inference import raw_predictions
from epistemics.source_learning.models import Answer
from epistemics.source_learning.service import create, export
from epistemics.source_learning.simulation import PARTICIPANT, synthetic_answer
from epistemics.source_learning.storage import encoded
from epistemics.source_learning.storage import fingerprint as base_fingerprint
from epistemics.source_panel.presentation import packet
from epistemics.source_panel.profiles import fit_profile, predictions
from epistemics.source_panel.runner import prepare
from epistemics.source_panel.service import PanelService, bind, fingerprint
from epistemics.source_panel.simulation import calibration, recovery


def profiles():
    rng = np.random.default_rng(92)
    training = [calibration(56 + i // 2, str(i), "joint_process", 0.93, rng) for i in range(4)]
    fit = fit_profile(training)
    return {"configuration": fit, "shared": fit}


def setup(directory, presentation="structured", condition="sparse", frozen=None):
    manifest = create(directory, PARTICIPANT, seed=35, condition=condition, synthetic=True)
    bind(directory, presentation=presentation, profiles=frozen, frozen_at=now() if frozen else None)
    return manifest, PanelService(directory)


def answer_for(service, answers):
    i = len(answers)
    raw = raw_predictions(service.base.manifest, i, answers)
    query = ("customer_panel", "selection_audit", "measurement_audit", "stop")[(i // 2) % 4]
    return synthetic_answer(service.base.manifest, i, raw, "joint_process", 1.0, 0, query)


@pytest.mark.parametrize("condition", ["sparse", "dense"])
def test_packet_preserves_public_facts_without_private_input(tmp_path, condition):
    manifest, service = setup(tmp_path / "run", "packet", condition)
    public = public_trial(manifest, 0, [])
    trial = service.get_trial()["trial"]
    assert trial == packet(public)
    text = trial["research_packet"]
    assert all(document in text for document in public.documents)
    for i, record in enumerate(public.archive, 1):
        assert f"Record {i}: {record.source_id} reported {record.count}" in text
        assert f"demand later proved {'strong' if record.resolved_strong else 'weak'}" in text
    assert ("Also report" in text) == (condition == "dense")
    serialized = json.dumps(
        {"describe": service.describe(), "trial": trial, "history": service.get_history()}
    )
    for private in (
        "design_seed",
        "true_panels",
        "measured_panels",
        "configuration_profile",
        "gain_probabilities",
        "panel-binding",
    ):
        assert private not in serialized
    assert "known_selection" not in trial
    assert "archive" not in trial


def test_paired_presentations_have_identical_answers_predictions_and_branch_facts(tmp_path):
    original_fp = base_fingerprint()
    frozen = profiles()
    a, structured = setup(tmp_path / "structured", frozen=frozen)
    b, prose = setup(tmp_path / "packet", "packet", frozen=frozen)
    assert a.archive == b.archive and a.companies == b.companies
    answers = []
    for i in range(36):
        pa, pb = structured.get_trial(), prose.get_trial()
        assert pb["trial"] == packet(public_trial(a, i, answers))
        answer = answer_for(structured, answers)
        for service, trial in ((structured, pa["trial"]), (prose, pb["trial"])):
            service.submit(trial["trial_id"], answer)
        answers.append(answer)
    structured.finish()
    result = prose.finish()
    assert len(result["completion_questions"]) == 3
    assert all("research_packet" in r["trial"] for r in prose.get_history()["history"])
    ea, eb = structured.evidence(), prose.evidence()
    assert [r["prediction"] for r in ea["locks"]] == [r["prediction"] for r in eb["locks"]]
    assert ea["binding"]["profiles"] == eb["binding"]["profiles"] == frozen
    for service in (structured, prose):
        export(service.directory)
        original = (service.directory / "panel-evidence.json").read_bytes()
        service.evidence()
        assert (service.directory / "panel-evidence.json").read_bytes() == original
    assert base_fingerprint() == original_fp


def test_requires_presentation_lock_and_preserves_concurrent_retry(tmp_path):
    _, service = setup(tmp_path / "run", "packet", frozen=profiles())
    answer = Answer(probability=0.5, decision="decline")
    with pytest.raises(ValueError, match="Read the current"):
        service.submit("source-01", answer)
    service.get_trial()
    with ThreadPoolExecutor(4) as pool:
        receipts = list(pool.map(lambda _: service.submit("source-01", answer), range(4)))
    assert all(r == receipts[0] for r in receipts)
    resumed = PanelService(service.directory)
    assert resumed.submit("source-01", answer) == receipts[0]
    with pytest.raises(ValueError, match="cannot be changed"):
        resumed.submit("source-01", Answer(probability=0.51, decision="decline"))
    with pytest.raises(ValueError, match="Bind before"):
        bind(service.directory)
    path = service.directory / "panel-binding.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="binding changed"):
        resumed.get_trial()


def test_profiles_ignore_heldout_answers_and_preserve_training_identity():
    rng = np.random.default_rng(3)
    report = calibration(74, "r1", "flat_accuracy", 1, rng)
    before = fit_profile([report])
    report.observations.extend(report.observations[:12])
    report.prediction_locks.extend([{"raw": {}}] * 12)
    assert fit_profile([report]) == before
    with pytest.raises(ValueError, match="twice"):
        fit_profile([report, report])
    assert before["training_reports"] == 12
    raw = report.prediction_locks[0]["raw"]
    assert set(predictions(raw, {"configuration": before, "shared": before}, 0.5)) == {
        "configuration_profile",
        "shared_profile",
        "fixed_joint",
        "fixed_flat",
        "fixed_discount",
        "configuration_mean",
        "shared_mean",
        "stated_prior",
    }


def test_uninformative_observations_do_not_force_family_identity():
    report = calibration(81, "null", "joint_process", 1, np.random.default_rng(4))
    for observation, lock in zip(report.observations, report.prediction_locks, strict=True):
        observation.answer = Answer(probability=0.5, decision="decline")
        for row in lock["raw"].values():
            row["logit"] = 0.0
    assert fit_profile([report])["decision"] == "ambiguous"


def test_pooled_calibration_recovers_models_on_new_worlds():
    result = recovery(8801, repetitions=2)
    assert result["passed"], result


def test_plan_partitions_and_matched_worlds_precede_answers(tmp_path, monkeypatch):
    from epistemics.source_panel import runner

    monkeypatch.setattr(runner, "codex_version", lambda: "synthetic-test-version")
    paths = []
    for seed in (1, 2):
        path = tmp_path / f"validation-{seed}.json"
        path.write_bytes(
            encoded({"passed": True, "seed": seed, "implementation_sha256": fingerprint()})
        )
        paths.append(path)
    plan = prepare(tmp_path / "panel", paths)
    assert len(plan["runs"]) == 16
    assert [r["phase"] for r in plan["runs"]] == ["baseline"] * 8 + ["dense"] * 4 + ["transfer"] * 4
    assert len(set(plan["world_seeds"].values())) == 3
    assert plan["limits"]["concurrency"] == 2
    assert not list((tmp_path / "panel/collections").glob("*/report.json"))


def test_actual_mcp_transports_complete_synthetic_packet(tmp_path):
    _, service = setup(tmp_path / "run", "packet", frozen=profiles())

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.source_panel.mcp_server"],
            env={
                **os.environ,
                "EPISTEMICS_SOURCE_PANEL": str(service.directory),
                "PYTHONPATH": str(Path("src").resolve()),
            },
        )
        async with (
            stdio_client(params) as (reader, writer),
            ClientSession(reader, writer) as session,
        ):
            await session.initialize()
            assert {t.name for t in (await session.list_tools()).tools} == {
                "describe_battery",
                "get_history",
                "get_trial",
                "submit_answer",
                "finish_evaluation",
            }
            description = await session.call_tool("describe_battery", {})
            assert not description.isError
            answers = []
            for _ in range(36):
                response = await session.call_tool("get_trial", {})
                assert not response.isError, response
                trial = json.loads(response.content[0].text)["trial"]
                assert "research_packet" in trial
                answer = answer_for(service, answers)
                receipt = await session.call_tool(
                    "submit_answer",
                    {"trial_id": trial["trial_id"], "answer": answer.model_dump(mode="json")},
                )
                assert not receipt.isError
                answers.append(answer)
            assert not (await session.call_tool("finish_evaluation", {})).isError

    asyncio.run(run())
    assert len(service.evidence()["locks"]) == 36


def test_whole_synthetic_panel_freezes_before_transfer_and_summarizes(tmp_path):
    from epistemics.source_learning.storage import digest, save
    from epistemics.source_panel.analysis import summarize
    from epistemics.source_panel.runner import freeze

    root = tmp_path / "panel"
    root.mkdir()
    entries = []
    for config in ("a", "b"):
        for world in ("a", "b"):
            for repeat in (1, 2):
                entries.append(
                    {
                        "run_id": f"{config}-{world}-{repeat}",
                        "configuration": config,
                        "world": world,
                        "phase": "baseline",
                        "condition": "sparse",
                        "presentation": "structured",
                    }
                )
            entries.append(
                {
                    "run_id": f"{config}-{world}-dense",
                    "configuration": config,
                    "world": world,
                    "phase": "dense",
                    "condition": "dense",
                    "presentation": "structured",
                }
            )
        for style in ("structured", "packet"):
            entries.append(
                {
                    "run_id": f"{config}-transfer-{style}",
                    "configuration": config,
                    "world": "transfer",
                    "phase": "transfer",
                    "condition": "sparse",
                    "presentation": style,
                }
            )
    entries.sort(key=lambda r: (r["phase"] != "baseline", r["phase"] == "transfer"))
    plan = {
        "runs": entries,
        "configurations": {"a": {}, "b": {}},
        "world_seeds": {"a": 21, "b": 22, "transfer": 23},
    }
    save(root / "plan.json", encoded(plan))
    save(root / "plan.sha256", (digest(encoded(plan)) + "\n").encode())
    frozen = None
    for ordinal, entry in enumerate(entries):
        if ordinal == 8:
            frozen = freeze(root, plan)
        directory = root / "collections" / entry["run_id"]
        m = create(
            directory,
            PARTICIPANT,
            seed=plan["world_seeds"][entry["world"]],
            condition=entry["condition"],
            synthetic=True,
        )
        bound = (
            None
            if entry["phase"] != "transfer"
            else {
                "configuration": frozen["configuration"][entry["configuration"]],
                "shared": frozen["shared"],
            }
        )
        bind(
            directory,
            presentation=entry["presentation"],
            profiles=bound,
            frozen_at=frozen["frozen_at"] if bound else None,
        )
        service = PanelService(directory)
        answers = []
        for i in range(36):
            trial = service.get_trial()["trial"]
            raw = raw_predictions(m, i, answers)
            answer = synthetic_answer(
                m,
                i,
                raw,
                "joint_process" if entry["configuration"] == "a" else "flat_accuracy",
                0.93,
                0,
                "stop",
            )
            service.submit(trial["trial_id"], answer)
            answers.append(answer)
        service.finish()
        export(directory)
    summary = summarize(root)
    assert len(summary["runs"]) == 16 and len(summary["transfer"]) == 4
    assert all(
        row["initial_report_rmse_pp"] == 0 for row in summary["within_configuration_repeatability"]
    )
    assert all(row["first_twelve_format_rmse_pp"] == 0 for row in summary["format_contrasts"])
    assert all(
        row["primary_first_twelve_rmse_pp"]["configuration_profile"] < 2
        for row in summary["transfer"]
    )
    original = (root / "summary.json").read_bytes()
    summarize(root)
    assert (root / "summary.json").read_bytes() == original
