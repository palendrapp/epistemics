import asyncio
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.diagnostic.service import fingerprint as original_fingerprint
from epistemics.diagnostic2.service import fingerprint as second_fingerprint
from epistemics.narrative.battery import background_facts, public_trial, schedule
from epistemics.narrative.inference import analyze, condition, fit, normalize, predictions
from epistemics.narrative.models import Answer, Joint, Manifest, Observation, Report, Trial
from epistemics.narrative.service import NarrativeService, create, encoded, export, load
from epistemics.narrative.simulation import answers, recovery, simulate, synthetic_inputs
from epistemics.narrative.web import LocalServer
from epistemics.service import now

PARTICIPANT = {
    "kind": "agent",
    "subject_id": "synthetic:narrative-test",
    "configuration": {
        "model": "synthetic",
        "model_version": "test",
        "configuration_sha256": "0" * 64,
    },
}


def test_matched_sentences_and_selective_disclosure():
    assignments = schedule(42)
    assert assignments == schedule(42)
    for a in assignments:
        pair = next(b for b in assignments if b.pair_id == a.pair_id and b != a)
        assert background_facts(a) == background_facts(pair)
        assert " ".join(public_trial(a, 0).new_documents) == " ".join(
            public_trial(pair, 0).new_documents
        )
        flipped = a.model_copy(
            update={
                "demand_outcome": not a.demand_outcome,
                "artifact_outcome": not a.artifact_outcome,
            }
        )
        for i in (0, 1):
            assert public_trial(a, i) == public_trial(flipped, i)
        assert public_trial(a, 2, "stop") == public_trial(flipped, 2, "stop")
        for query, hidden in (
            ("demand_audit", "artifact_outcome"),
            ("pipeline_audit", "demand_outcome"),
        ):
            trial = public_trial(a, 2, query)
            assert trial == public_trial(
                a.model_copy(update={hidden: not getattr(a, hidden)}), 2, query
            )
            assert len(trial.new_documents) == 1
        assert public_trial(a, 3, "stop").demand_resolved == a.demand_outcome
        for private in ('"pair_id"', '"presentation"', '"demand_outcome"', '"artifact_outcome"'):
            assert private not in public_trial(a, 0).model_dump_json()
        with pytest.raises(ValueError, match="choice required"):
            public_trial(a, 2)


def test_contracts_and_exact_trial_reconstruction(tmp_path):
    report = simulate(tmp_path / "c", 14)
    for fact in report.analysis["facts"]:
        assert fact["signal_consistency_gap_tv_pp"] <= 1.5
        assert fact["signal_rounding_sensitivity"]["all_report_bins_overlap"]
        assert fact["audit_rounding_sensitivity"]["all_report_bins_overlap"]
        assert fact["final_resolution_error_tv_pp"] == 0
    assert not report.analysis["model_parameters_are_passport_traits"]
    raw = (tmp_path / "c/report.json").read_bytes()
    export(tmp_path / "c")
    assert (tmp_path / "c/report.json").read_bytes() == raw
    data = report.model_dump(mode="json")
    key = next(iter(data["cases"]))
    data["cases"][key][1]["answer"]["query"] = "stop"
    with pytest.raises(ValueError, match="frozen assignment and research choice"):
        Report.model_validate(data)
    m = report.manifest.model_dump()
    m["assignments"][0]["artifact_outcome"] = not m["assignments"][0]["artifact_outcome"]
    with pytest.raises(ValueError, match="Matched pairs"):
        Manifest.model_validate(m)
    with pytest.raises(ValueError, match="sum to"):
        Joint(demand_only=0.5, artifact_only=0.5, both=0.5, neither=0.5)
    with pytest.raises(ValueError, match="increments"):
        Joint(demand_only=0.251, artifact_only=0.249, both=0.25, neither=0.25)


def test_immutable_branch_choice_concurrent_retry_and_binding(tmp_path):
    m = create(tmp_path / "c", PARTICIPANT, seed=3, synthetic=True)
    a = m.assignments[0]
    service = NarrativeService(tmp_path / "c", a.assignment_id)
    reports = answers(synthetic_inputs([a], 10)[0])
    with pytest.raises(ValueError, match="eight cases"):
        export(tmp_path / "c")
    with pytest.raises(ValueError, match="every checkpoint"):
        service.finish()
    with pytest.raises(ValueError, match="current checkpoint"):
        service.submit(f"{a.assignment_id}:3", reports[3])
    with pytest.raises(ValueError, match="signal forecasts"):
        service.submit(f"{a.assignment_id}:0", reports[3])
    service.submit(f"{a.assignment_id}:0", reports[0])
    with ThreadPoolExecutor(4) as pool:
        receipts = list(
            pool.map(
                lambda _: NarrativeService(tmp_path / "c", a.assignment_id).submit(
                    f"{a.assignment_id}:1", reports[1]
                ),
                range(4),
            )
        )
    assert receipts == [receipts[0]] * 4
    with pytest.raises(ValueError, match="cannot be changed"):
        service.submit(f"{a.assignment_id}:1", reports[1].model_copy(update={"query": "stop"}))
    restored = NarrativeService(tmp_path / "c", a.assignment_id)
    assert restored.get_trial()["trial"]["selected_query"] == reports[1].query
    assert len(restored.get_history()["history"]) == 2
    with (tmp_path / "c/manifest.json").open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="bytes changed"):
        load(tmp_path / "c")


def test_undefined_references_and_fit_exclusions_are_explicit():
    a = schedule(2)[0].model_copy(update={"demand_outcome": False})
    initial = Answer(
        joint={"demand_only": 1, "artifact_only": 0, "both": 0, "neither": 0},
        signal_if_state={"demand_only": 0, "artifact_only": 0.5, "both": 1, "neither": 0.5},
    )
    report = initial.model_copy(update={"signal_if_state": None, "query": "demand_audit"})
    rows = [
        Observation(
            trial=public_trial(a, i, "demand_audit" if i >= 2 else None),
            answer=answer,
            answered_at=now(),
        )
        for i, answer in enumerate(
            [
                initial,
                report,
                report.model_copy(update={"query": None}),
                report.model_copy(update={"query": None}),
            ]
        )
    ]
    result = analyze(
        {a.assignment_id: rows},
        [
            a.model_copy(update={"presentation": "narrative"}),
            a.model_copy(update={"presentation": "facts"}),
        ],
    )
    assert all(
        f["signal_reference_undefined"] and f["audit_reference_undefined"] for f in result["facts"]
    )
    assert all(
        f["signal_consistency_gap_tv_pp"] is None and f["audit_consistency_gap_tv_pp"] is None
        for f in result["facts"]
    )
    assert result["conditional_report_model"]["status"] == "no_eligible_cases"
    assert len(result["fit_exclusions"]) == 2
    assert normalize([0, 0, 0, 0]) is None
    assert condition([1, 0, 0, 0], "demand_audit", a) is None


def test_explaining_away_and_degenerate_parameter_reporting():
    a = schedule(3)[0].model_copy(update={"demand_outcome": True})
    entry = (np.array([0.25] * 4), np.array([0.8, 0.8, 0.9, 0.1]), "demand_audit", a)
    reference = predictions(*entry, (1, 1, 1))
    # A confirmed real demand change reduces artifact probability under the declared model.
    assert reference[1, [1, 2]].sum() < reference[0, [1, 2]].sum()
    independent = predictions(*entry, (1, 0, 1))
    assert independent[1, [1, 2]].sum() == pytest.approx(independent[0, [1, 2]].sum())
    fit_result = fit([entry], [predictions(*entry, (1, 1, 0))])["families"]["full"]
    assert fit_result["tied_grid_points"] == 25
    assert fit_result["parameter_ranges"]["signal_weight"] == [0, 2]
    for seed in (20260924, 20260925):
        result = recovery(seed, repetitions=16)
        assert result["passed"], result


def test_schema_snapshots_and_previous_evaluators_unchanged():
    for model, name in [(Manifest, "collection"), (Trial, "trial"), (Report, "report")]:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        assert Path(f"schemas/narrative-{name}.v1.json").read_bytes() == encoded(schema)
    assert (
        original_fingerprint() == "3e5584987011181d97894a2af47a0a15fc967a1e0f127b5551424075055b29e1"
    )
    assert (
        second_fingerprint() == "231248e45c2433a5c22077043746cfe5b2f892f1880d5e2ad39a229dfe0dee95"
    )


def test_actual_mcp_transport_with_research_choice(tmp_path):
    m = create(tmp_path / "c", PARTICIPANT, seed=3, synthetic=True)
    a = m.assignments[0]

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.narrative.mcp_server"],
            env={
                **os.environ,
                "EPISTEMICS_NARRATIVE": str(tmp_path / "c"),
                "EPISTEMICS_ASSIGNMENT": a.assignment_id,
            },
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            assert len((await client.list_tools()).tools) == 5
            assert (await client.call_tool("finish_evaluation", {})).isError
            for answer in answers(synthetic_inputs([a], 20)[0]):
                current = json.loads((await client.call_tool("get_trial", {})).content[0].text)
                data = {"trial_id": current["trial"]["trial_id"], "answer": answer.model_dump()}
                result = await client.call_tool("submit_answer", data)
                assert not result.isError
                assert result.content == (await client.call_tool("submit_answer", data)).content
            assert not (await client.call_tool("finish_evaluation", {})).isError

    asyncio.run(run())


def test_browser_whole_collection_and_authorization(tmp_path):
    m = create(
        tmp_path / "human", {"kind": "human", "subject_id": "private:test"}, seed=3, synthetic=True
    )
    server = LocalServer(tmp_path / "human")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def request(path, body=None, **headers):
        req = urllib.request.Request(
            base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Authorization": "Bearer " + server.access,
                "Content-Type": "application/json",
                "X-Epistemics-Request": "1",
                **headers,
            },
        )
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    try:
        assert request("/api/state", Authorization="")[0] == 403
        assert request("/api/state", Origin="https://attacker.invalid")[0] == 403
        assert request("/manifest.json")[0] == 404
        assert request("/")[0] == 200
        assert request("/api/begin", {"instructions_accepted": False})[0] == 400
        assert request("/api/begin", {"instructions_accepted": True})[0] == 200
        assert request("/api/finish", {"assignment_id": m.assignments[1].assignment_id})[0] == 400
        for i, a in enumerate(m.assignments):
            state = json.loads(request("/api/state")[1])
            assert state["case_number"] == i + 1 and state["case_count"] == 8
            for j, answer in enumerate(answers(synthetic_inputs([a], 20)[0])):
                body = {
                    "assignment_id": a.assignment_id,
                    "trial_id": f"{a.assignment_id}:{j}",
                    "answer": answer.model_dump(),
                }
                assert request("/api/answers", body)[0] == 200
                assert request("/api/answers", body)[0] == 200
            body = {"assignment_id": a.assignment_id}
            assert request("/api/finish", body)[0] == 200
            assert request("/api/finish", body)[0] == 200
        assert json.loads(request("/api/state")[1])["complete"]
        assert export(tmp_path / "human").manifest.response_origin == "synthetic"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
