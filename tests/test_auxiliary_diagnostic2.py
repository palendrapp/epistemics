import asyncio
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.diagnostic.service import fingerprint as original_fingerprint
from epistemics.diagnostic2.battery import archive_counts, archive_records, public_trial, schedule
from epistemics.diagnostic2.inference import PARAMETERS, fit, predictions
from epistemics.diagnostic2.models import Answer, Manifest, Report, Trial
from epistemics.diagnostic2.service import DiagnosticService, create, encoded, export, load
from epistemics.diagnostic2.simulation import GENERATORS, answers, recovery, simulate
from epistemics.diagnostic2.web import LocalServer

PARTICIPANT = {
    "kind": "agent",
    "subject_id": "synthetic:auxiliary2-test",
    "configuration": {
        "model": "synthetic",
        "model_version": "test",
        "configuration_sha256": "0" * 64,
    },
}


def test_matched_information_equivalence_and_future_boundary(tmp_path):
    m = create(tmp_path / "c", PARTICIPANT, seed=12, synthetic=True)
    assert m.assignments == schedule(12)
    assert len(m.assignments) == 16
    for a in m.assignments:
        decoded = Counter()
        for r in archive_records(a):
            growth = r["audited_revenue"] > 1.1 * r["prior_revenue"]
            auxiliary = (
                r["opening_backlog"] > 100
                if a.target == "backlog"
                else (r["audited_revenue"] - r["initial_bulletin_revenue"]) / r["audited_revenue"]
                >= 0.05
            )
            decoded[growth, auxiliary] += 1
        assert decoded == {
            (r["growth_above_10_percent"], r["auxiliary_event"]): r["companies"]
            for r in archive_counts(a)
        }
        others = [b for b in m.assignments if b.quartet_id == a.quartet_id]
        assert all(archive_records(a) == archive_records(b) for b in others)
        for i in range(3):
            trial = public_trial(a, i)
            assert trial.auxiliary_resolved is None
            if i == 0 or a.evidence == "signal":
                assert trial.growth_resolved is None
            else:
                assert trial.growth_resolved == a.growth_outcome
            assert (
                public_trial(a.model_copy(update={"auxiliary_outcome": not a.auxiliary_outcome}), i)
                == trial
            )
            if a.evidence == "signal":
                assert (
                    public_trial(a.model_copy(update={"growth_outcome": not a.growth_outcome}), i)
                    == trial
                )
            visible = trial.model_dump_json()
            for private in (
                '"quartet_id"',
                '"relationship"',
                '"signal_positive"',
                '"growth_outcome"',
                '"auxiliary_outcome"',
                '"archive_seed"',
            ):
                assert private not in visible
        assert public_trial(a, 3).growth_resolved == a.growth_outcome
        assert public_trial(a, 3).auxiliary_resolved == a.auxiliary_outcome
    broken = m.model_dump(mode="json")
    broken["assignments"][0]["archive_seed"] += 1
    with pytest.raises(ValueError, match="Matched cases"):
        Manifest.model_validate(broken)


def test_conditional_bridge_separates_uncertainty_from_propagation(tmp_path):
    report = simulate(tmp_path / "c", seed=13)
    # The reference moves less on uncertain evidence while exactly preserving
    # its own conditional mixture. A smaller raw change alone is not damping.
    for r in report.analysis["facts"]:
        assert abs(r["conditional_mixture_gap_pp"]) < 1e-8
        assert r["repeat_auxiliary_change_pp"] == r["repeat_growth_change_pp"] == 0
        assert (
            r["direct_auxiliary_resolution_error_pp"] == r["direct_growth_resolution_error_pp"] == 0
        )
        if r["relationship"] == "associated":
            delta = abs(r["auxiliary_after_evidence"] - 0.5)
            assert delta == pytest.approx(0.3 if r["evidence"] == "audit" else 0.15)
    assert all(
        r["records_minus_summary_conditional_spread_pp"] == 0
        for r in report.analysis["matched_presentation_contrasts"]
    )
    assert not report.analysis["model_parameters_are_passport_traits"]
    raw = (tmp_path / "c/report.json").read_bytes()
    export(tmp_path / "c")
    assert (tmp_path / "c/report.json").read_bytes() == raw
    data = report.model_dump(mode="json")
    data["cases"][report.manifest.assignments[0].assignment_id][0]["trial"]["documents"].append(
        "Tampered"
    )
    with pytest.raises(ValueError, match="frozen assignment"):
        Report.model_validate(data)


def test_separate_mechanisms_and_declared_synthetic_recovery():
    assignments = schedule(12)
    for parameters in GENERATORS.values():
        fitted = fit(np.round(predictions(assignments, parameters)[0], 2), assignments)["full"]
        assert [fitted["parameters"][p] for p in PARAMETERS] == list(parameters)
    propagation = predictions(assignments, (1, 1, 1, 0.5, 1))[0].reshape(16, 7)
    smoothing = predictions(assignments, (1, 1, 1, 1, 0.5))[0].reshape(16, 7)
    assert np.allclose(propagation[:, 3], smoothing[:, 3])
    assert not np.allclose(propagation[:, 5:], smoothing[:, 5:])
    for seed in (20260924, 20260925):
        result = recovery(seed, repetitions=16)
        assert result["passed"], result
        assert result["degenerate_propagation_flagged"]


def test_immutable_retries_restart_and_manifest_binding(tmp_path):
    m = create(tmp_path / "c", PARTICIPANT, seed=3, synthetic=True)
    a = m.assignments[0]
    service = DiagnosticService(tmp_path / "c", a.assignment_id)
    with pytest.raises(ValueError, match="sixteen cases"):
        export(tmp_path / "c")
    with pytest.raises(ValueError, match="every checkpoint"):
        service.finish()
    with pytest.raises(ValueError, match="current checkpoint"):
        service.submit(f"{a.assignment_id}:3", answers(a)[3])
    with pytest.raises(ValueError, match="conditional forecasts"):
        service.submit(f"{a.assignment_id}:0", answers(a)[1])
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
        service.submit(
            f"{a.assignment_id}:0", answers(a)[0].model_copy(update={"auxiliary_probability": 0.25})
        )
    assert DiagnosticService(tmp_path / "c", a.assignment_id).get_trial()["answered"] == 1
    with pytest.raises(ValueError, match="increments"):
        Answer(growth_probability=0.123, auxiliary_probability=0.5)
    with (tmp_path / "c/manifest.json").open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="bytes changed"):
        load(tmp_path / "c")


def test_actual_mcp_transport_for_records_and_uncertain_evidence(tmp_path):
    m = create(tmp_path / "c", PARTICIPANT, seed=3, synthetic=True)
    a = next(a for a in m.assignments if a.presentation == "records" and a.evidence == "signal")

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.diagnostic2.mcp_server"],
            env={
                **os.environ,
                "EPISTEMICS_DIAGNOSTIC2": str(tmp_path / "c"),
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
            assert state["case_number"] == i + 1 and state["case_count"] == 16
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
        assert export(tmp_path / "human").manifest.response_origin == "synthetic"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_schema_snapshots_and_original_evaluator_unchanged():
    for model, name in [(Manifest, "collection"), (Trial, "trial"), (Report, "report")]:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        assert Path(f"schemas/auxiliary-{name}.v2.json").read_bytes() == encoded(schema)
    assert (
        original_fingerprint() == "3e5584987011181d97894a2af47a0a15fc967a1e0f127b5551424075055b29e1"
    )
