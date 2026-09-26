import asyncio
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.source_inference.report import fingerprint as lab_fingerprint
from epistemics.source_inference.world import RANDOM
from epistemics.source_learning.battery import generate, knowledge, location, public_trial
from epistemics.source_learning.inference import raw_predictions
from epistemics.source_learning.models import Answer, Manifest, Report, Trial
from epistemics.source_learning.service import SourceLearningService, create, export, load
from epistemics.source_learning.simulation import (
    PARTICIPANT,
    memory_manifest,
    recovery,
    simulate,
    synthetic_answer,
)
from epistemics.source_learning.storage import digest, encoded
from epistemics.source_learning.web import LocalServer


def next_answer(service, query=None, p=None):
    trial = service.get_trial()["trial"]
    with service.state() as state:
        earlier = [Answer.model_validate(r["answer"]) for r in state["answers"]]
    index = len(earlier)
    c, _ = location(index)
    raw = raw_predictions(service.manifest, index, earlier)
    answer = synthetic_answer(
        service.manifest,
        index,
        raw,
        "joint_process",
        1,
        0,
        query or ("customer_panel", "selection_audit", "measurement_audit", "stop")[c % 4],
    )
    if p is not None:
        answer = answer.model_copy(update={"probability": p})
    return trial, answer


def advance(service, count):
    for _ in range(count):
        trial, answer = next_answer(service)
        service.submit(trial["trial_id"], answer)


def test_coherent_generating_processes_and_neutral_label_permutation():
    s, a, c = generate(41)
    assert (s, a, c) == generate(41)
    assert s != generate(42)[0]
    m = memory_manifest(41)
    assert len(m.archive) == 72
    assert len(m.companies) == 24
    for company in c:
        assert company.record.source == next(
            x for x in s if x.source_id == company.record.public.source_id
        )
        assert company.record.public.resolved_strong == company.independent_panel.resolved_strong
    data = m.model_dump()
    data["companies"][0]["record"]["source"]["measurement_accuracy"] = 0.75
    with pytest.raises(ValueError, match="consistent"):
        Manifest.model_validate(data)
    data = m.model_dump()
    data["companies"][0]["independent_panel"]["resolved_strong"] = not c[
        0
    ].record.public.resolved_strong
    with pytest.raises(ValueError, match="same company"):
        Manifest.model_validate(data)


def test_private_truth_and_unselected_research_cannot_change_public_trial():
    m = memory_manifest(6)
    modified = m.model_copy(deep=True)
    for company in modified.companies:
        company.record = company.record.model_copy(
            update={
                "public": company.record.public.model_copy(
                    update={"resolved_strong": not company.record.public.resolved_strong}
                )
            }
        )
        company.independent_panel = company.independent_panel.model_copy(
            update={"count": 5 - company.independent_panel.count}
        )
    assert public_trial(m, 0, []) == public_trial(modified, 0, [])
    assert raw_predictions(m, 0, []) == raw_predictions(modified, 0, [])
    answers = [Answer(probability=0.5, decision="decline") for _ in range(12)]
    answers.append(Answer(probability=0.5, decision="decline", query="stop"))
    # Only modify the unresolved target; earlier resolved outcomes must still be available.
    modified = m.model_copy(deep=True)
    modified.companies[12].independent_panel = modified.companies[12].independent_panel.model_copy(
        update={"count": (m.companies[12].independent_panel.count + 1) % 6}
    )
    assert public_trial(m, 13, answers) == public_trial(modified, 13, answers)
    assert raw_predictions(m, 13, answers) == raw_predictions(modified, 13, answers)
    serialized = public_trial(m, 0, []).model_dump_json()
    for key in (
        '"design_seed"',
        '"true_panels"',
        '"measured_panels"',
        '"independent_panel"',
        '"phase"',
    ):
        assert key not in serialized


def test_actual_audits_persist_and_resolution_waits_for_final_answer(tmp_path):
    m = create(tmp_path / "run", PARTICIPANT, seed=23, condition="sparse", synthetic=True)
    service = SourceLearningService(tmp_path / "run")
    advance(service, 12)
    trial, answer = next_answer(service, query="selection_audit")
    target = m.companies[12]
    assert trial["known_selection"] is None
    service.submit(trial["trial_id"], answer)
    revision = service.get_trial()["trial"]
    assert revision["known_selection"] == target.record.source.rule.model_dump(mode="json")
    assert service.get_history()["history"][-1]["resolved_strong"] is None
    _, answer = next_answer(service)
    service.submit(revision["trial_id"], answer)
    assert (
        service.get_history()["history"][-1]["resolved_strong"]
        == target.record.public.resolved_strong
    )
    with service.state() as state:
        answers = [Answer.model_validate(r["answer"]) for r in state["answers"]]
    history, selection, _ = knowledge(m, 14, answers)
    assert selection[target.record.source.source_id] == target.record.source.rule
    assert history[-1] == target.record.public
    later = next(
        i
        for i in range(14, 36)
        if public_trial(
            m, i, answers + [Answer(probability=0.5, decision="decline", query="stop")] * 36
        ).source_id
        == target.record.source.source_id
    )
    while len(service.get_history()["history"]) < later:
        advance(service, 1)
    assert service.get_trial()["trial"]["known_selection"] == revision["known_selection"]


def test_disclosed_random_process_makes_joint_and_flat_equivalent():
    m = memory_manifest(24)
    target = next(i for i in range(12, 24) if m.companies[i].record.source.rule == RANDOM)
    index = 12 + 2 * (target - 12)
    answers = []
    for i in range(index + 1):
        _, stage = location(i)
        answers.append(
            Answer(
                probability=0.5,
                decision="decline",
                query="selection_audit" if stage == "research" else None,
            )
        )
    predictions = raw_predictions(m, index + 1, answers)
    assert predictions["joint_process"]["probability"] == pytest.approx(
        predictions["flat_accuracy"]["probability"]
    )


def test_sparse_dense_match_inputs_but_require_different_answers(tmp_path):
    a = create(tmp_path / "a", PARTICIPANT, seed=12, condition="sparse", synthetic=True)
    b = create(tmp_path / "b", PARTICIPANT, seed=12, condition="dense", synthetic=True)
    assert a.companies == b.companies and a.archive == b.archive
    ta, tb = public_trial(a, 0, []), public_trial(b, 0, [])
    assert ta.model_copy(update={"request_diagnostics": True}) == tb
    assert raw_predictions(a, 0, []) == raw_predictions(b, 0, [])
    answer = Answer(probability=0.5, decision="decline")
    answer.validate_trial(ta)
    with pytest.raises(ValueError, match="diagnostic"):
        answer.validate_trial(tb)
    for value in (float("nan"), 1.01, 0.501, True):
        with pytest.raises(ValueError):
            Answer(probability=value, decision="decline")
    with pytest.raises(ValueError):
        Answer(probability=0.5, decision="decline", hidden_truth=True)


def test_lock_before_answer_concurrent_retry_and_resume(tmp_path):
    create(tmp_path / "run", PARTICIPANT, seed=3, condition="sparse", synthetic=True)
    service = SourceLearningService(tmp_path / "run")
    with pytest.raises(ValueError, match="Read the current"):
        service.submit("source-01", Answer(probability=0.5, decision="decline"))
    trial, answer = next_answer(service)
    with ThreadPoolExecutor(4) as pool:
        results = list(
            pool.map(
                lambda _: SourceLearningService(tmp_path / "run").submit(trial["trial_id"], answer),
                range(4),
            )
        )
    assert results == [results[0]] * 4
    with pytest.raises(ValueError, match="cannot be changed"):
        service.submit(
            trial["trial_id"],
            answer.model_copy(
                update={"decision": "invest" if answer.decision == "decline" else "decline"}
            ),
        )
    restored = SourceLearningService(tmp_path / "run")
    assert restored.get_trial()["answered"] == 1
    with pytest.raises(ValueError, match="current checkpoint"):
        restored.submit("source-36", answer)
    with pytest.raises(ValueError, match="every checkpoint"):
        restored.finish()
    with (tmp_path / "run/manifest.json").open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="bytes changed"):
        load(tmp_path / "run")


def test_frozen_fit_ignores_later_reports_and_dense_diagnostics(tmp_path):
    for name in ("a", "b"):
        create(tmp_path / name, PARTICIPANT, seed=4, condition="dense", synthetic=True)
    a, b = [SourceLearningService(tmp_path / name) for name in ("a", "b")]
    for _ in range(12):
        ta, aa = next_answer(a)
        tb, ab = next_answer(b)
        ab = ab.model_copy(
            update={"measurement_accuracy": 0.5, "random_selection_probability": 1.0}
        )
        a.submit(ta["trial_id"], aa)
        b.submit(tb["trial_id"], ab)
    with a.state() as sa, b.state() as sb:
        assert sa["fit_lock"]["fit"] == sb["fit_lock"]["fit"]
        original = encoded(sa["fit_lock"])
    for service, probability in ((a, 0.01), (b, 0.99)):
        trial, answer = next_answer(service, query="customer_panel", p=probability)
        service.submit(trial["trial_id"], answer)
        service.get_trial()
    with a.state() as sa, b.state() as sb:
        assert encoded(sa["fit_lock"]) == original
        assert sa["locks"][13]["raw"] == sb["locks"][13]["raw"]
        assert sa["locks"][13]["forecast"] == sb["locks"][13]["forecast"]


@pytest.mark.parametrize("condition", ["sparse", "dense"])
def test_complete_synthetic_report_reconstruction_and_exact_bytes(tmp_path, condition):
    report = simulate(tmp_path / "run", 25, condition)
    a = report.analysis
    assert a["decision_consistency"] == {"consistent": 36, "denominator": 36}
    assert a["research_counts"] == {
        q: 3 for q in ("customer_panel", "selection_audit", "measurement_audit", "stop")
    }
    assert len(a["research_policy_comparisons"]) == 12
    assert len(a["final_outcome_scores"]) == 24
    assert not a["all_candidates_inadequate"]
    assert not a["model_parameters_are_passport_traits"]
    raw = (tmp_path / "run/report.json").read_bytes()
    assert digest(raw) == (tmp_path / "run/report.sha256").read_text().strip()
    export(tmp_path / "run")
    assert raw == (tmp_path / "run/report.json").read_bytes()
    data = report.model_dump(mode="json")
    data["observations"][13]["trial"]["selected_query"] = "stop"
    with pytest.raises(ValueError, match="frozen design"):
        Report.model_validate(data)
    data = report.model_dump(mode="json")
    data["prediction_locks"][0]["locked_at"] = report.completed_at.isoformat()
    with pytest.raises(ValueError, match="Prediction bytes"):
        Report.model_validate(data)


def test_coherent_design_recovery_and_previous_lab_unchanged():
    for seed in (20260925, 20261025):
        result = recovery(seed, repetitions=16)
        assert result["passed"], result
    assert lab_fingerprint() == "46da0ced2322c89971c833e0e657517ff166de86cb6ba1b51674ecbc6f0a535d"


def test_reversed_response_process_can_fail_all_models(tmp_path):
    create(tmp_path / "run", PARTICIPANT, seed=25, condition="sparse", synthetic=True)
    service = SourceLearningService(tmp_path / "run")
    for i in range(36):
        trial, answer = next_answer(service)
        if i >= 12:
            answer = answer.model_copy(update={"probability": round(1 - answer.probability, 2)})
        service.submit(trial["trial_id"], answer)
    service.finish()
    report = export(tmp_path / "run")
    assert report.analysis["all_candidates_inadequate"]


def test_schema_snapshots():
    for model, name in ((Manifest, "collection"), (Trial, "trial"), (Report, "report")):
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        assert Path(f"schemas/source-learning-{name}.v1.json").read_bytes() == encoded(schema)


def test_actual_mcp_transport_whole_collection(tmp_path):
    create(tmp_path / "run", PARTICIPANT, seed=7, condition="dense", synthetic=True)

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.source_learning.mcp_server"],
            env={**os.environ, "EPISTEMICS_SOURCE_LEARNING": str(tmp_path / "run")},
        )
        local = SourceLearningService(tmp_path / "run")
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            assert {t.name for t in (await client.list_tools()).tools} == {
                "describe_battery",
                "get_trial",
                "get_history",
                "submit_answer",
                "finish_evaluation",
            }
            assert (await client.call_tool("finish_evaluation", {})).isError
            for _ in range(36):
                result = await client.call_tool("get_trial", {})
                current = json.loads(result.content[0].text)
                assert "raw" not in result.content[0].text
                _, answer = next_answer(local)
                data = {"trial_id": current["trial"]["trial_id"], "answer": answer.model_dump()}
                receipt = await client.call_tool("submit_answer", data)
                assert not receipt.isError
                assert receipt.content == (await client.call_tool("submit_answer", data)).content
            assert not (await client.call_tool("finish_evaluation", {})).isError
            history = json.loads((await client.call_tool("get_history", {})).content[0].text)[
                "history"
            ]
            assert len(history) == 36 and history[-1]["resolved_strong"] is not None

    asyncio.run(run())
    assert export(tmp_path / "run").manifest.response_origin == "synthetic"


def test_browser_authorization_shared_protocol_and_completion(tmp_path):
    create(
        tmp_path / "run",
        {"kind": "human", "subject_id": "private:synthetic-test"},
        seed=7,
        condition="sparse",
        synthetic=True,
    )
    server = LocalServer(tmp_path / "run")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def request(path, body=None, token=None, origin=None):
        headers = {
            "Authorization": "Bearer " + (server.access if token is None else token),
            "Content-Type": "application/json",
            "X-Epistemics-Request": "1",
        }
        if origin:
            headers["Origin"] = origin
        req = urllib.request.Request(
            base + path, data=None if body is None else json.dumps(body).encode(), headers=headers
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.load(response)

    try:
        with pytest.raises(urllib.error.HTTPError) as error:
            request("/api/state", token="wrong")
        assert error.value.code == 403
        with pytest.raises(urllib.error.HTTPError):
            request("/api/begin", {"instructions_accepted": True}, origin="https://example.com")
        assert request("/api/state")["current"] is None
        with pytest.raises(urllib.error.HTTPError):
            request("/api/answers", {"trial_id": "source-01", "answer": {}})
        request("/api/begin", {"instructions_accepted": True})
        for _ in range(36):
            state = request("/api/state")
            trial, answer = next_answer(server.service)
            assert state["current"]["trial"] == trial
            data = {"trial_id": trial["trial_id"], "answer": answer.model_dump()}
            assert request("/api/answers", data) == request("/api/answers", data)
        assert request("/api/state")["current"]["complete"]
        assert not request("/api/state")["current"]["finished"]
        assert request("/api/finish", {}) == request("/api/finish", {})
        assert request("/api/state")["current"]["finished"]
        with pytest.raises(urllib.error.HTTPError) as error:
            request("/manifest.json")
        assert error.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
