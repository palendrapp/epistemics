import asyncio
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.diagnostic.battery import public_trial, schedule
from epistemics.diagnostic.inference import fit, predictions
from epistemics.diagnostic.models import Answer, Report
from epistemics.diagnostic.service import DiagnosticService, create, export, load
from epistemics.diagnostic.simulation import recovery
from epistemics.diagnostic.web import LocalServer

PARTICIPANT = {
    "kind": "agent",
    "subject_id": "synthetic:auxiliary-test",
    "configuration": {
        "model": "synthetic",
        "model_version": "test",
        "configuration_sha256": "0" * 64,
    },
}


def answers(a, parameters=(1, 1, 1)):
    p = np.round(predictions([a], parameters)[0], 2)
    return [
        Answer(
            growth_probability=0.5 if i == 0 else int(a.growth_outcome),
            auxiliary_probability=0.5 if i == 0 else p[i + 1],
            auxiliary_if_growth=p[0] if i == 0 else None,
            auxiliary_if_no_growth=p[1] if i == 0 else None,
        )
        for i in range(4)
    ]


def test_matched_design_information_boundary_and_transfer(tmp_path):
    manifest = create(tmp_path / "collection", PARTICIPANT, seed=12, synthetic=True)
    assert manifest.design_seed == 12
    assert len(manifest.assignments) == 8
    for a in manifest.assignments:
        b = next(b for b in manifest.assignments if b.pair_id == a.pair_id and b != a)
        assert a.growth_outcome == b.growth_outcome and a.auxiliary_outcome == b.auxiliary_outcome
        initial = public_trial(a, 0)
        assert sum(r["companies"] for r in initial.archive) == 40
        assert initial.growth_resolved is None and initial.auxiliary_resolved is None
        assert public_trial(a, 2).auxiliary_resolved is None
        assert any("no new document" in text for text in public_trial(a, 2).documents)
        assert not any("no new document" in text for text in public_trial(a, 3).documents)
        service = DiagnosticService(tmp_path / "collection", a.assignment_id)
        for i, answer in enumerate(answers(a)):
            current = service.get_trial()
            visible = json.dumps(current)
            for private in (
                '"pair_id"',
                '"relationship"',
                '"growth_outcome"',
                '"auxiliary_outcome"',
                '"assignments"',
                '"seed"',
            ):
                assert private not in visible
            receipt = service.submit(current["trial"]["trial_id"], answer)
            assert receipt == service.submit(current["trial"]["trial_id"], answer)
            assert len(service.get_history()["history"]) == i + 1
        assert service.finish() == service.finish()
    report = export(tmp_path / "collection")
    raw = (tmp_path / "collection/report.json").read_bytes()
    export(tmp_path / "collection")
    assert (tmp_path / "collection/report.json").read_bytes() == raw
    for row in report.analysis["facts"]:
        assert abs(row["conditional_transfer_gap_pp"]) < 1e-10
        assert row["direct_resolution_error_pp"] == 0
    assert report.analysis["model_parameters_are_passport_traits"] is False
    altered = report.model_dump(mode="json")
    first_id = manifest.assignments[0].assignment_id
    altered["cases"][first_id][0]["trial"]["documents"].append("Injected later information")
    with pytest.raises(ValueError, match="frozen assignment"):
        Report.model_validate(altered)


def test_immutable_concurrent_answers_resume_and_frozen_manifest(tmp_path):
    m = create(tmp_path / "c", PARTICIPANT, seed=3, synthetic=True)
    a = m.assignments[0]
    s = DiagnosticService(tmp_path / "c", a.assignment_id)
    with pytest.raises(ValueError, match="every checkpoint"):
        s.finish()
    with pytest.raises(ValueError, match="eight cases"):
        export(tmp_path / "c")
    with pytest.raises(ValueError, match="current checkpoint"):
        s.submit(f"{a.assignment_id}:3", answers(a)[3])
    with pytest.raises(ValueError, match="conditional forecasts"):
        s.submit(f"{a.assignment_id}:0", answers(a)[1])
    with ThreadPoolExecutor(4) as pool:
        receipts = list(
            pool.map(
                lambda _: DiagnosticService(tmp_path / "c", a.assignment_id).submit(
                    f"{a.assignment_id}:0", answers(a)[0]
                ),
                range(4),
            )
        )
    assert receipts == [receipts[0]] * 4
    with pytest.raises(ValueError, match="cannot be changed"):
        s.submit(
            f"{a.assignment_id}:0", answers(a)[0].model_copy(update={"auxiliary_probability": 0.25})
        )
    assert DiagnosticService(tmp_path / "c", a.assignment_id).get_trial()["answered"] == 1
    with pytest.raises(ValueError, match="increments"):
        Answer(growth_probability=0.123, auxiliary_probability=0.5)
    with (tmp_path / "c/manifest.json").open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="bytes changed"):
        load(tmp_path / "c")


def test_recovery_and_identifiability_boundaries():
    for seed in (20260923, 20260924):
        result = recovery(seed, repetitions=32)
        assert result["passed"], result
        assert result["zero_association_propagation_unidentified"]
    assignments = schedule(100)
    # After the first evidence step alone, slower expression and partial propagation
    # have the same product. Repetition and direct resolution break that ambiguity.
    x = predictions(assignments, (1, 0.5, 1))[0].reshape(8, 5)
    y = predictions(assignments, (1, 1, 0.5))[0].reshape(8, 5)
    assert np.allclose(x[:, 2], y[:, 2])
    assert not np.allclose(x[:, 3:], y[:, 3:])
    for p in ((1, 0.5, 1), (1, 1, 0.5), (1.25, 0.5, 0.75)):
        result = fit(np.round(predictions(assignments, p)[0], 2), assignments)["full"]
        assert list(result["parameters"].values()) == list(p)
    no_movement = fit(predictions(assignments, (1, 0.5, 0))[0], assignments)["full"]
    assert not no_movement["propagation_identifiable_in_selected_model"]


def test_real_mcp_transport(tmp_path):
    m = create(tmp_path / "c", PARTICIPANT, seed=3, synthetic=True)
    a = m.assignments[0]

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.diagnostic.mcp_server"],
            env={
                **os.environ,
                "EPISTEMICS_DIAGNOSTIC": str(tmp_path / "c"),
                "EPISTEMICS_ASSIGNMENT": a.assignment_id,
            },
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            assert len((await client.list_tools()).tools) == 5
            assert (await client.call_tool("finish_evaluation", {})).isError
            for answer in answers(a):
                current = json.loads((await client.call_tool("get_trial", {})).content[0].text)
                data = {"trial_id": current["trial"]["trial_id"], "answer": answer.model_dump()}
                response = await client.call_tool("submit_answer", data)
                assert not response.isError
                assert response.content == (await client.call_tool("submit_answer", data)).content
            assert not (await client.call_tool("finish_evaluation", {})).isError

    asyncio.run(run())


def test_browser_shared_state_authorization_and_whole_collection(tmp_path):
    m = create(tmp_path / "human", {"kind": "human", "subject_id": "private:test"}, seed=3)
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
            assert state["case_number"] == i + 1
            for j, answer in enumerate(answers(a)):
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
        assert export(tmp_path / "human").manifest.response_origin == "human"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
