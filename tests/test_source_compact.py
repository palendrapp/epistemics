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
from epistemics.source_compact import VERSION
from epistemics.source_compact.presentation import expand
from epistemics.source_compact.service import (
    CompactService,
    create,
    fingerprint,
    load_evidence,
    verify_evidence,
)
from epistemics.source_compact.simulation import simulate, transport
from epistemics.source_compact.web import LocalServer
from epistemics.source_learning.battery import location, public_trial
from epistemics.source_learning.models import Answer as LedgerAnswer
from epistemics.source_learning.simulation import PARTICIPANT
from epistemics.source_learning.storage import digest, encoded
from epistemics.source_selective.policy import POLICIES, choose, price_for
from epistemics.source_selective.presentation import present as present_v2
from epistemics.source_selective.service import fingerprint as selective_fingerprint

SECRETS = (
    "design_seed",
    "price_seed",
    "true_panels",
    "measured_panels",
    "implementation_sha256",
    "prediction_locks",
    "independent_panel",
)


def answer_for(i):
    p = round(0.2 + 0.6 * ((i * 7) % 10) / 10, 2)
    return {"probability": p, "decision": "invest" if p > 0.5 else "decline"}


@pytest.mark.parametrize("policy", POLICIES)
@pytest.mark.parametrize("seed", [3, 45])
def test_every_checkpoint_expands_exactly_to_v0_2_and_is_smaller(tmp_path, policy, seed):
    d = tmp_path / "run"
    create(d, PARTICIPANT, seed=seed, price_seed=seed + 9, policy=policy, synthetic=True)
    s = CompactService(d)
    described = s.describe()
    assert described["battery_version"] == VERSION and described["delivery"] == "compact"
    assert "do not choose" in described["instructions"]
    assert set(described["answer_schema"]["properties"]) == {"probability", "decision"}
    trial = s.get_trial()["trial"]
    compact_bytes = full_bytes = 0
    for i in range(36):
        with s.base.state() as state:
            earlier = [LedgerAnswer.model_validate(r["answer"]) for r in state["answers"]]
        full = present_v2(public_trial(s.manifest, i, earlier), s.binding)
        assert expand(trial, policy) == full
        assert len(trial["source_history"].split()) == len(full["archive"])
        serialized = json.dumps({"trial": trial, "description": described})
        assert not any(secret in serialized for secret in SECRETS)
        compact_bytes += len(encoded(trial))
        full_bytes += len(encoded(full))
        receipt = s.submit(trial["trial_id"], answer_for(i))
        assert (receipt["resolved_company"] is None) == (location(i)[1] == "research")
        trial = receipt["next_trial"]
    assert trial is None and receipt["all_checkpoints_answered"]
    assert compact_bytes < 0.2 * full_bytes


def test_submit_returns_locked_next_checkpoint_and_retries_are_idempotent(tmp_path):
    create(tmp_path / "run", PARTICIPANT, seed=3, policy="cost_aware", synthetic=True)
    s = CompactService(tmp_path / "run")
    with pytest.raises(ValueError, match="Read"):
        s.submit("source-01", {"probability": 0.5, "decision": "decline"})
    first = s.get_trial()["trial"]
    a = {"probability": 0.5, "decision": "decline"}
    with ThreadPoolExecutor(4) as pool:
        receipts = list(pool.map(lambda _: s.submit("source-01", a), range(4)))
    assert receipts == [receipts[0]] * 4
    assert receipts[0]["next_trial"] == s.get_trial()["trial"]
    assert receipts[0]["next_trial"]["trial_id"] == "source-02" != first["trial_id"]
    with pytest.raises(ValueError, match="cannot be changed"):
        s.submit("source-01", {"probability": 0.6, "decision": "invest"})
    second = s.submit("source-02", a)
    retried = s.submit("source-01", a)
    assert {k: v for k, v in retried.items() if k != "next_trial"} == {
        k: v for k, v in receipts[0].items() if k != "next_trial"
    }
    assert retried["next_trial"] == second["next_trial"]
    with s.base.state() as state:
        locks = state["verification_locks"]
    assert [lock["public_trial"]["trial_id"] for lock in locks] == [
        "source-01",
        "source-02",
        "source-03",
    ]


@pytest.mark.parametrize("policy", POLICIES)
def test_assigned_checks_costs_evidence_and_tampering(tmp_path, policy):
    d = tmp_path / policy
    create(d, PARTICIPANT, seed=45, price_seed=17, policy=policy, synthetic=True)
    s = CompactService(d)
    trial = s.get_trial()["trial"]
    charged = []
    for i in range(36):
        stage = location(i)[1]
        if stage == "research":
            assert trial["stage"] == "provisional"
            price = price_for(s.binding, trial["company_id"])
            assert trial["check"]["available_check_cost"] == price
            assert trial["check"]["charged_cost"] == (
                None if policy == "cost_aware" else price if policy == "always" else 0
            )
            checked = choose(policy, 0.5, trial["decision_threshold"], price) == "customer_panel"
            charged.append(price if checked else 0)
        if stage == "revision":
            assert trial["check"]["check_supplied"] == (charged[-1] > 0 or policy == "always")
            assert ("independent_sample" in trial) == trial["check"]["check_supplied"]
            assert trial["check"]["charged_cost"] == charged[-1]
        trial = s.submit(trial["trial_id"], {"probability": 0.5, "decision": "decline"})[
            "next_trial"
        ]
    s.finish()
    e = s.evidence()
    r, _ = load_evidence(d)
    assert e["analysis"]["total_check_cost"] == pytest.approx(sum(charged))
    assert s.evidence() == e
    history = s.get_history()["history"]
    assert len(history) == 36 and all(
        set(row["answer"]) == {"probability", "decision"} for row in history
    )
    assert all("archive" not in row["trial"] for row in history)
    with pytest.raises(ValueError, match="Assigned verification"):
        bundle([d])
    for field in ("assignment", "chronology", "analysis", "public", "schema"):
        bad = json.loads(encoded(e))
        if field == "assignment":
            bad["binding"]["offers"][0]["available_check_cost"] += 1
            bad["binding_sha256"] = digest(encoded(bad["binding"]))
        elif field == "chronology":
            bad["locks"][13]["locked_at"] = r.manifest.created_at.isoformat()
        elif field == "analysis":
            bad["analysis"]["mean_net_payoff"] += 1
        elif field == "public":
            bad["locks"][0]["public_trial"]["source_history"] = "5S"
        else:
            bad["schema_version"] = "epistemics.source-selective-evidence.v1"
        with pytest.raises(ValueError):
            verify_evidence(r, bad)


def test_fingerprint_is_distinct_and_synthetic_transport_is_smaller():
    assert fingerprint() != selective_fingerprint()
    results = transport(11)
    assert set(results) == set(POLICIES)
    for r in results.values():
        assert r["checkpoints"] == 36 and r["byte_ratio"] < 0.2
        assert r["respondent_tool_calls"] < r["v0_2_minimum_tool_calls"]


def test_complete_stdio_mcp_uses_one_call_per_checkpoint(tmp_path):
    create(tmp_path / "run", PARTICIPANT, seed=61, policy="cost_aware", synthetic=True)

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.source_compact.mcp_server"],
            env={**os.environ, "EPISTEMICS_SOURCE_COMPACT": str(tmp_path / "run")},
        )
        async with stdio_client(params) as (reader, writer), ClientSession(reader, writer) as c:
            await c.initialize()
            assert len((await c.list_tools()).tools) == 5
            described = json.loads((await c.call_tool("describe_battery", {})).content[0].text)
            assert described["delivery"] == "compact"
            t = json.loads((await c.call_tool("get_trial", {})).content[0].text)["trial"]
            for i in range(36):
                result = await c.call_tool(
                    "submit_answer", {"trial_id": t["trial_id"], "answer": answer_for(i)}
                )
                assert not result.isError
                receipt = json.loads(result.content[0].text)
                assert (receipt["resolved_company"] is None) == (location(i)[1] == "research")
                t = receipt["next_trial"]
            assert t is None and receipt["all_checkpoints_answered"]
            result = await c.call_tool("finish_evaluation", {})
            assert not result.isError
            assert len(json.loads(result.content[0].text)["completion_questions"]) == 5

    asyncio.run(run())
    CompactService(tmp_path / "run").evidence()


def test_complete_human_browser_http_and_auth(tmp_path):
    create(
        tmp_path / "run",
        {"kind": "human", "subject_id": "test:synthetic"},
        seed=3,
        policy="cost_aware",
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
            assert state["protocol"]["field_definitions"]["source_history"]
            trial = state["current"]["trial"]
            receipt = request(
                "/api/answers", {"trial_id": trial["trial_id"], "answer": answer_for(i)}
            )
            assert (receipt["resolved_company"] is None) == (location(i)[1] == "research")
        request("/api/finish", {})
        server.service.evidence()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_acceptance_plan_requires_compact_validation(tmp_path, monkeypatch):
    from epistemics.source_compact import runner

    monkeypatch.setattr(runner, "codex_version", lambda: "test-only")
    validations = []
    for seed in (1, 2):
        p = tmp_path / f"validation-{seed}.json"
        p.write_bytes(
            encoded(
                {
                    "schema_version": "epistemics.source-compact-recovery.v1",
                    "passed": True,
                    "implementation_sha256": fingerprint(),
                    "repetitions_per_family_per_policy": 32,
                    "datasets": 288,
                    "delivery": {p: {} for p in POLICIES},
                    "seed": seed,
                }
            )
        )
        validations.append(p)
    with pytest.raises(ValueError, match="two distinct"):
        runner.prepare(tmp_path / "one", validations[:1])
    root = tmp_path / "acceptance"
    plan = runner.prepare(root, validations)
    assert len(plan["runs"]) == 6
    assert {(r["configuration"], r["policy"]) for r in plan["runs"]} == {
        (c, p) for c in ("astra", "sol") for p in POLICIES
    }
    assert (root / "plan.sha256").read_text().strip() == digest((root / "plan.json").read_bytes())
    for e in plan["runs"]:
        s = CompactService(root / "collections" / e["run_id"])
        assert s.manifest.design_seed == plan["world_seeds"]["acceptance"]
        argv = runner.command(root, e, plan["configurations"][e["configuration"]])
        assert any("source_compact.mcp_server" in arg for arg in argv)
        assert any("EPISTEMICS_SOURCE_COMPACT" in arg for arg in argv)
        assert not any("source_panel" in arg for arg in argv[:-1])
        assert argv[-1] == runner.PROMPT
    # Offline fixture only: mocked completion is not agent acceptance evidence.
    for e in plan["runs"]:
        directory = root / "collections" / e["run_id"]
        simulate_fixture = CompactService(directory)
        trial = simulate_fixture.get_trial()["trial"]
        while trial is not None:
            trial = simulate_fixture.submit(
                trial["trial_id"], {"probability": 0.5, "decision": "decline"}
            )["next_trial"]
        simulate_fixture.finish()
        simulate_fixture.evidence()
        (directory / "execution.json").write_bytes(
            encoded(
                {
                    "status": "completed",
                    "elapsed_seconds": 0,
                    "turns": 0,
                    "usage": {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0},
                    "tools": [],
                    "test_fixture": True,
                }
            )
        )
    summary = runner.summarize(root)
    assert len(summary["runs"]) == 6 and summary["known_usage"]["input_tokens"] == 0
    with pytest.raises(ValueError, match="committed bytes"):
        asyncio.run(runner.run(root, dict(plan, order_seed=0)))


def test_simulated_collection_verifies(tmp_path):
    evidence = simulate(tmp_path / "run", 7, "cost_aware")
    report, loaded = load_evidence(tmp_path / "run")
    assert loaded == json.loads(encoded(evidence))
    assert report.manifest.response_origin == "synthetic"
