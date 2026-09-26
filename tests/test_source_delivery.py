import asyncio
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.source_delivery.presentation import DIAGNOSTICS, RESEARCH, present
from epistemics.source_delivery.service import DeliveryService, create, verify_evidence
from epistemics.source_delivery.web import LocalServer
from epistemics.source_learning.battery import location, public_trial
from epistemics.source_learning.inference import raw_predictions
from epistemics.source_learning.models import Answer
from epistemics.source_learning.service import export
from epistemics.source_learning.simulation import PARTICIPANT, synthetic_answer
from epistemics.source_learning.storage import encoded
from epistemics.source_learning.storage import fingerprint as base_fingerprint
from epistemics.source_panel.service import fingerprint as panel_fingerprint


def answer(service, answers, query=None):
    i = len(answers)
    c, _ = location(i)
    return synthetic_answer(
        service.manifest,
        i,
        raw_predictions(service.manifest, i, answers),
        "joint_process",
        1,
        0,
        query or ("customer_panel", "selection_audit", "measurement_audit", "stop")[c % 4],
    )


@pytest.mark.parametrize("presentation", ["structured", "packet"])
@pytest.mark.parametrize("condition", ["sparse", "dense"])
def test_public_clarity_resolution_boundaries_and_all_branches(tmp_path, presentation, condition):
    m = create(
        tmp_path / "run",
        PARTICIPANT,
        seed=45,
        condition=condition,
        presentation=presentation,
        synthetic=True,
    )
    s = DeliveryService(tmp_path / "run")
    assert s.describe()["research_options"] == RESEARCH
    assert s.describe()["diagnostic_definitions"] == DIAGNOSTICS
    serialized = json.dumps(
        {"description": s.describe(), "current": s.get_trial(), "history": s.get_history()}
    )
    for secret in (
        "design_seed",
        "true_panels",
        "measured_panels",
        "implementation_sha256",
        "prediction_locks",
    ):
        assert secret not in serialized
    answers = []
    for i in range(36):
        t = s.get_trial()["trial"]
        assert t == present(public_trial(m, i, answers), presentation)
        a = answer(s, answers)
        receipt = s.submit(t["trial_id"], a)
        c, stage = location(i)
        if stage == "research":
            assert receipt["resolved_company"] is None
            assert set(t["research_options"]) == set(RESEARCH)
        else:
            assert (
                receipt["resolved_company"]["resolved_strong"]
                == m.companies[c].record.public.resolved_strong
            )
        assert s.submit(t["trial_id"], a) == receipt
        answers.append(a)
    s.finish()
    e = s.evidence()
    assert verify_evidence(export(s.directory), e) == s.binding
    original = (s.directory / "delivery-evidence.json").read_bytes()
    assert encoded(s.evidence()) == original
    altered = json.loads(original)
    altered["resolutions"][12] = {"resolved_strong": True}
    with pytest.raises(ValueError, match="feedback"):
        verify_evidence(export(s.directory), altered)
    altered = json.loads(original)
    altered["locks"][0]["locked_at"] = "2099-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="chronology"):
        verify_evidence(export(s.directory), altered)


def test_concurrent_immutable_retry_and_old_fingerprints(tmp_path):
    assert base_fingerprint() == "d222e34b05736bf934ba04adaf63ad8a4350213e351f92a249d3898855656ade"
    assert panel_fingerprint() == "8ecfeca196c023826fe0c461ca4a4e54c1d68094269d8d9548921f46ad41676d"
    create(tmp_path / "run", PARTICIPANT, seed=3, synthetic=True, condition="sparse")
    s = DeliveryService(tmp_path / "run")
    a = Answer(probability=0.5, decision="decline")
    with pytest.raises(ValueError, match="Read"):
        s.submit("source-01", a)
    s.get_trial()
    with ThreadPoolExecutor(4) as pool:
        receipts = list(pool.map(lambda _: s.submit("source-01", a), range(4)))
    assert receipts == [receipts[0]] * 4
    with pytest.raises(ValueError, match="cannot be changed"):
        s.submit("source-01", Answer(probability=0.6, decision="invest"))
    assert DeliveryService(s.directory).submit("source-01", a) == receipts[0]


def test_actual_mcp_clarified_collection(tmp_path):
    create(tmp_path / "run", PARTICIPANT, seed=61, synthetic=True, condition="sparse")
    s = DeliveryService(tmp_path / "run")

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.source_delivery.mcp_server"],
            env={**os.environ, "EPISTEMICS_SOURCE_DELIVERY": str(s.directory)},
        )
        async with (
            stdio_client(params) as (reader, writer),
            ClientSession(reader, writer) as client,
        ):
            await client.initialize()
            description = json.loads(
                (await client.call_tool("describe_battery", {})).content[0].text
            )
            assert description == s.describe()
            answers = []
            for _ in range(36):
                t = json.loads((await client.call_tool("get_trial", {})).content[0].text)["trial"]
                a = answer(s, answers)
                r = await client.call_tool(
                    "submit_answer", {"trial_id": t["trial_id"], "answer": a.model_dump()}
                )
                assert not r.isError
                answers.append(a)
            result = await client.call_tool("finish_evaluation", {})
            assert not result.isError
            assert len(json.loads(result.content[0].text)["completion_questions"]) == 4

    asyncio.run(run())
    s.evidence()


def test_browser_shares_protocol_authorization_and_final_feedback(tmp_path):
    create(
        tmp_path / "run",
        {"kind": "human", "subject_id": "private:synthetic"},
        seed=3,
        synthetic=True,
        condition="sparse",
    )
    server = LocalServer(tmp_path / "run")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(path, body=None, token=None):
        req = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}" + path,
            data=encoded(body) if body is not None else None,
            headers={
                "Authorization": "Bearer " + (server.access if token is None else token),
                "Content-Type": "application/json",
                "X-Epistemics-Request": "1",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.load(response)

    try:
        with pytest.raises(urllib.error.HTTPError):
            request("/api/state", token="wrong")
        state = request("/api/state")
        assert state["protocol"] == server.service.describe() and state["current"] is None
        request("/api/begin", {"instructions_accepted": True})
        answers = []
        for _ in range(36):
            t = request("/api/state")["current"]["trial"]
            a = answer(server.service, answers)
            receipt = request("/api/answers", {"trial_id": t["trial_id"], "answer": a.model_dump()})
            assert (receipt["resolved_company"] is None) == (t["stage"] == "research")
            answers.append(a)
        request("/api/finish", {})
        server.service.evidence()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
