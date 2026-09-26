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

from epistemics.passport.source_learning import bundle
from epistemics.source_delivery.service import fingerprint as delivery_fingerprint
from epistemics.source_learning.battery import costs, location
from epistemics.source_learning.simulation import PARTICIPANT
from epistemics.source_learning.storage import digest, encoded
from epistemics.source_verification.analysis import contrast, gate
from epistemics.source_verification.presentation import Answer
from epistemics.source_verification.service import (
    VerificationService,
    create,
    fingerprint,
    load_evidence,
    verify_evidence,
)
from epistemics.source_verification.simulation import simulate
from epistemics.source_verification.web import LocalServer


@pytest.mark.parametrize("policy", ["none", "always"])
def test_assigned_paths_immutable_choices_and_exact_costs(tmp_path, policy):
    d = tmp_path / policy
    create(d, PARTICIPANT, seed=45, policy=policy, synthetic=True)
    s = VerificationService(d)
    assert set(s.describe()["answer_schema"]["properties"]) == {"probability", "decision"}
    assert "do not choose" in s.describe()["instructions"]
    with pytest.raises(ValueError, match="Read"):
        s.submit("source-01", {"probability": 0.5, "decision": "decline"})
    first = None
    for i in range(36):
        t = s.get_trial()["trial"]
        serialized = json.dumps(
            {"trial": t, "history": s.get_history(), "description": s.describe()}
        )
        for secret in (
            "design_seed",
            "true_panels",
            "measured_panels",
            "implementation_sha256",
            "prediction_locks",
            "independent_panel",
        ):
            assert secret not in serialized
        c, stage = location(i)
        if stage == "research":
            assert t["stage"] == "provisional" and not t["research_costs"]
            assert t["assigned_verification"]["charged_cost"] == (
                costs(s.manifest.companies[c])["customer_panel"] if policy == "always" else 0
            )
            with pytest.raises(ValueError):
                s.submit(
                    t["trial_id"], {"probability": 0.5, "decision": "decline", "query": "stop"}
                )
        if stage == "revision":
            assert ("The independent check accurately" in " ".join(t["documents"])) == (
                policy == "always"
            )
        a = {"probability": 0.5, "decision": "decline"}
        receipt = s.submit(t["trial_id"], a)
        assert (receipt["resolved_company"] is None) == (stage == "research")
        if receipt["resolved_company"]:
            assert receipt["resolved_company"]["company_id"] == s.manifest.companies[c].company_id
        assert s.submit(t["trial_id"], a) == receipt
        first = first or receipt
    assert s.submit("source-01", {"probability": 0.5, "decision": "decline"}) == first
    s.finish()
    e = s.evidence()
    r, _ = load_evidence(d)
    assert e["analysis"]["mean_gross_payoff"] == 0
    expected_cost = (
        sum(costs(c)["customer_panel"] for c in r.manifest.companies[12:])
        if policy == "always"
        else 0
    )
    assert e["analysis"]["total_check_cost"] == pytest.approx(expected_cost)
    assert e["analysis"]["mean_net_payoff"] == pytest.approx(-expected_cost / 12)
    assert e["analysis"]["check_count"] == (12 if policy == "always" else 0)
    assert s.evidence() == e
    assert all(
        set(row["answer"]) == {"probability", "decision"} for row in s.get_history()["history"]
    )
    with pytest.raises(ValueError, match="Assigned verification"):
        bundle([d])
    for field in ("assignment", "chronology", "analysis", "public", "resolution"):
        bad = json.loads(encoded(e))
        if field == "assignment":
            bad["binding"]["assignments"][0]["charged_cost"] += 1
            bad["binding_sha256"] = digest(encoded(bad["binding"]))
        elif field == "chronology":
            bad["locks"][13]["locked_at"] = r.manifest.created_at.isoformat()
        elif field == "analysis":
            bad["analysis"]["mean_net_payoff"] += 1
        elif field == "public":
            bad["locks"][0]["public_trial"]["documents"][0] = "Changed"
        else:
            bad["resolutions"][12] = {"resolved_strong": True}
        with pytest.raises(ValueError):
            verify_evidence(r, bad)


def test_concurrent_retries_and_delivery_fingerprint(tmp_path):
    assert (
        delivery_fingerprint() == "b45e472082a50b3bda49cfae04147e3622f5df5ea64274d5b6710391825d2bb0"
    )
    create(tmp_path / "run", PARTICIPANT, seed=3, policy="always", synthetic=True)
    s = VerificationService(tmp_path / "run")
    s.get_trial()
    a = {"probability": 0.5, "decision": "decline"}
    with ThreadPoolExecutor(4) as pool:
        receipts = list(pool.map(lambda _: s.submit("source-01", a), range(4)))
    assert receipts == [receipts[0]] * 4
    with pytest.raises(ValueError, match="cannot be changed"):
        s.submit("source-01", {"probability": 0.6, "decision": "invest"})
    assert s.get_trial()["answered"] == 1
    with pytest.raises(ValueError):
        Answer(probability=0.501, decision="invest")


def test_matched_payoff_contrast_and_prospective_gate(tmp_path):
    for p in ("none", "always"):
        simulate(tmp_path / p, 37, p)
    r, n = load_evidence(tmp_path / "none")
    r2, a = load_evidence(tmp_path / "always")
    assert r.manifest.companies == r2.manifest.companies
    c = contrast(n["analysis"], a["analysis"])
    assert c["net_payoff_gain"] == pytest.approx(
        c["gross_payoff_gain"] - c["additional_check_cost_per_company"]
    )
    assert gate([{"net_payoff_gain": 0.02}, {"net_payoff_gain": 0}])["passed"]
    assert not gate([{"net_payoff_gain": 0.10}, {"net_payoff_gain": -0.001}])["passed"]
    assert not gate([{"net_payoff_gain": 0}, {"net_payoff_gain": 0}])["passed"]
    with pytest.raises(ValueError):
        gate([c])
    a["analysis"]["rows"][0]["check_price"] += 1
    with pytest.raises(ValueError, match="matched"):
        contrast(n["analysis"], a["analysis"])


@pytest.mark.parametrize("policy", ["none", "always"])
def test_complete_assigned_stdio_mcp(tmp_path, policy):
    create(tmp_path / "run", PARTICIPANT, seed=61, policy=policy, synthetic=True)

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.source_verification.mcp_server"],
            env={**os.environ, "EPISTEMICS_SOURCE_VERIFICATION": str(tmp_path / "run")},
        )
        async with stdio_client(params) as (reader, writer), ClientSession(reader, writer) as c:
            await c.initialize()
            assert len((await c.list_tools()).tools) == 5
            for i in range(36):
                t = json.loads((await c.call_tool("get_trial", {})).content[0].text)["trial"]
                result = await c.call_tool(
                    "submit_answer",
                    {
                        "trial_id": t["trial_id"],
                        "answer": {"probability": 0.5, "decision": "decline"},
                    },
                )
                assert not result.isError
                assert (json.loads(result.content[0].text)["resolved_company"] is None) == (
                    location(i)[1] == "research"
                )
            result = await c.call_tool("finish_evaluation", {})
            assert not result.isError
            assert len(json.loads(result.content[0].text)["completion_questions"]) == 4

    asyncio.run(run())
    VerificationService(tmp_path / "run").evidence()


def test_complete_human_browser_http_and_auth(tmp_path):
    create(
        tmp_path / "run",
        {"kind": "human", "subject_id": "test:synthetic"},
        seed=3,
        policy="always",
        synthetic=True,
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
        request("/api/begin", {"instructions_accepted": True})
        for i in range(36):
            state = request("/api/state")
            trial = state["current"]["trial"]
            assert state["protocol"]["assigned_policy"] == "always"
            receipt = request(
                "/api/answers",
                {
                    "trial_id": trial["trial_id"],
                    "answer": {"probability": 0.5, "decision": "decline"},
                },
            )
            assert (receipt["resolved_company"] is None) == (location(i)[1] == "research")
        request("/api/finish", {})
        server.service.evidence()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_plan_freezes_validation_configuration_and_policy_before_answers(tmp_path, monkeypatch):
    from epistemics.source_verification import runner

    monkeypatch.setattr(runner, "codex_version", lambda: "test-only")
    validations = []
    for seed in (1, 2):
        p = tmp_path / f"validation-{seed}.json"
        p.write_bytes(
            encoded(
                {
                    "passed": True,
                    "implementation_sha256": fingerprint(),
                    "repetitions_per_family_per_policy": 32,
                    "seed": seed,
                }
            )
        )
        validations.append(p)
    root = tmp_path / "acceptance"
    plan = runner.prepare(root, validations, phase="acceptance")
    assert len(plan["runs"]) == 2 and {r["policy"] for r in plan["runs"]} == {"none", "always"}
    assert (root / "plan.sha256").read_text().strip() == digest((root / "plan.json").read_bytes())
    for e in plan["runs"]:
        s = VerificationService(root / "collections" / e["run_id"])
        assert s.get_history()["history"] == []
        assert len(s.binding["assignments"]) == 12
        argv = runner.command(root, e, plan["configurations"][e["configuration"]])
        assert any("source_verification.mcp_server" in arg for arg in argv)
        assert argv[-1] == runner.PROMPT
    with pytest.raises(ValueError, match="Review acceptance"):
        runner.prepare(tmp_path / "stage-a", validations, phase="stage-a")


def test_failed_attempt_stops_admission_and_retains_usage(tmp_path, monkeypatch):
    from epistemics.source_verification import runner

    calls = []

    async def collect(root, entry, config, timeout):
        calls.append(entry["run_id"])
        return {"status": "failed", "usage": None}

    monkeypatch.setattr(runner, "collect", collect)
    plan = {
        "runs": [{"run_id": str(i), "configuration": "test"} for i in range(8)],
        "configurations": {"test": {}},
        "limits": {
            "total_seconds": 3600,
            "max_known_processed_tokens": 25000000,
            "admission_reserve_tokens_per_run": 3000000,
            "per_run_seconds": 900,
        },
    }
    with pytest.raises(SystemExit):
        asyncio.run(runner.run(tmp_path, plan))
    record = json.loads((tmp_path / "execution.json").read_bytes())
    assert (
        len(calls) == 2
        and record["unattempted_runs"] == 6
        and record["unknown_usage_attempts"] == 2
    )
