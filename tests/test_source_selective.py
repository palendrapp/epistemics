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
from epistemics.source_learning.battery import location
from epistemics.source_learning.simulation import PARTICIPANT, memory_manifest
from epistemics.source_learning.storage import digest, encoded
from epistemics.source_selective.analysis import contrast, gate, repeatability, repeated_contrast
from epistemics.source_selective.policy import POLICIES, choose, expected_value, offers, price_for
from epistemics.source_selective.presentation import Answer
from epistemics.source_selective.service import (
    VerificationService,
    create,
    fingerprint,
    load_evidence,
    verify_evidence,
)
from epistemics.source_selective.simulation import simulate
from epistemics.source_selective.web import LocalServer


@pytest.mark.parametrize("policy", POLICIES)
def test_assigned_paths_immutable_choices_and_exact_costs(tmp_path, policy):
    d = tmp_path / policy
    create(d, PARTICIPANT, seed=45, price_seed=17, policy=policy, synthetic=True)
    s = VerificationService(d)
    assert set(s.describe()["answer_schema"]["properties"]) == {"probability", "decision"}
    assert "do not choose" in s.describe()["instructions"]
    with pytest.raises(ValueError, match="Read"):
        s.submit("source-01", {"probability": 0.5, "decision": "decline"})
    first = None
    charged = []
    checked = False
    for i in range(36):
        t = s.get_trial()["trial"]
        serialized = json.dumps(
            {"trial": t, "history": s.get_history(), "description": s.describe()}
        )
        for secret in (
            "design_seed",
            "price_seed",
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
                None
                if policy == "cost_aware"
                else price_for(s.binding, t["company_id"])
                if policy == "always"
                else 0
            )
            checked = (
                choose(policy, 0.5, t["decision_threshold"], price_for(s.binding, t["company_id"]))
                == "customer_panel"
            )
            charged.append(price_for(s.binding, t["company_id"]) if checked else 0)
            with pytest.raises(ValueError):
                s.submit(
                    t["trial_id"], {"probability": 0.5, "decision": "decline", "query": "stop"}
                )
        if stage == "revision":
            assert ("The independent check accurately" in " ".join(t["documents"])) == checked
            assert t["assigned_verification"]["charged_cost"] == charged[-1]
            assert ("no new evidence has arrived" in t["stage_instruction"]) == (not checked)
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
    expected_cost = sum(charged)
    assert e["analysis"]["total_check_cost"] == pytest.approx(expected_cost)
    assert e["analysis"]["mean_net_payoff"] == pytest.approx(-expected_cost / 12)
    assert e["analysis"]["check_count"] == sum(c > 0 for c in charged)
    if policy == "cost_aware":
        assert 0 < e["analysis"]["check_count"] < 12
    assert s.evidence() == e
    assert all(
        set(row["answer"]) == {"probability", "decision"} for row in s.get_history()["history"]
    )
    with pytest.raises(ValueError, match="Assigned verification"):
        bundle([d])
    for field in ("assignment", "chronology", "analysis", "public", "resolution"):
        bad = json.loads(encoded(e))
        if field == "assignment":
            bad["binding"]["offers"][0]["available_check_cost"] += 1
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

    def comparison(a, b):
        return {
            w: {
                k: {"repeat_mean": {"net_payoff_gain": v}}
                for k, v in (("cost_aware_vs_none", a[i]), ("cost_aware_vs_always", b[i]))
            }
            for i, w in enumerate(("a", "b"))
        }

    assert gate(comparison([0.02, 0], [0, 0]))["passed"]
    assert not gate(comparison([0.10, -0.001], [0, 0]))["passed"]
    assert not gate(comparison([0.02, 0.02], [0.1, -0.01]))["passed"]
    assert not gate(comparison([0, 0], [0.1, 0.1]))["passed"]
    assert repeatability([n["analysis"]] * 2)["final_probability_mae_pp"] == 0
    repeated = repeated_contrast([n["analysis"]] * 2, [a["analysis"]] * 2)
    assert repeated["repeat_mean"] == c
    with pytest.raises(ValueError):
        gate({"a": c})
    a["analysis"]["rows"][0]["check_price"] += 1
    with pytest.raises(ValueError, match="matched"):
        contrast(n["analysis"], a["analysis"])


@pytest.mark.parametrize("policy", POLICIES)
def test_complete_assigned_stdio_mcp(tmp_path, policy):
    create(tmp_path / "run", PARTICIPANT, seed=61, policy=policy, synthetic=True)

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.source_selective.mcp_server"],
            env={**os.environ, "EPISTEMICS_SOURCE_SELECTIVE": str(tmp_path / "run")},
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
            trial = state["current"]["trial"]
            assert state["protocol"]["assigned_policy"] == "cost_aware"
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
    from epistemics.source_selective import runner

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
                    "datasets": 288,
                    "policies": {p: {"passed": True} for p in POLICIES},
                    "seed": seed,
                }
            )
        )
        validations.append(p)
    root = tmp_path / "acceptance"
    plan = runner.prepare(root, validations, phase="acceptance")
    assert len(plan["runs"]) == 3 and {r["policy"] for r in plan["runs"]} == set(POLICIES)
    assert (root / "plan.sha256").read_text().strip() == digest((root / "plan.json").read_bytes())
    for e in plan["runs"]:
        s = VerificationService(root / "collections" / e["run_id"])
        assert s.get_history()["history"] == []
        assert len(s.binding["offers"]) == 12
        argv = runner.command(root, e, plan["configurations"][e["configuration"]])
        assert any("source_selective.mcp_server" in arg for arg in argv)
        assert argv[-1] == runner.PROMPT
    with pytest.raises(ValueError, match="Review acceptance"):
        runner.prepare(tmp_path / "comparison", validations, phase="comparison")

    # Exercise the complete 24-cell summary on explicitly mocked respondent execution.
    # These offline fixtures are not real agent acceptance or model execution evidence.
    def complete_fixture(collection):
        service = VerificationService(collection)
        for _ in range(36):
            trial = service.get_trial()["trial"]
            service.submit(trial["trial_id"], {"probability": 0.5, "decision": "decline"})
        service.finish()
        service.evidence()
        (collection / "execution.json").write_bytes(
            encoded(
                {
                    "status": "completed",
                    "elapsed_seconds": 0,
                    "usage": {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0},
                    "tools": [],
                    "test_fixture": True,
                }
            )
        )

    for entry in plan["runs"]:
        complete_fixture(root / "collections" / entry["run_id"])
    (root / "acceptance-review.json").write_bytes(
        encoded(
            {
                "plan_sha256": digest((root / "plan.json").read_bytes()),
                "passed": True,
                "test_fixture": True,
            }
        )
    )
    comparison = tmp_path / "comparison"
    main_plan = runner.prepare(comparison, validations, phase="comparison", acceptance=root)
    assert set(main_plan["world_seeds"].values()).isdisjoint(plan["world_seeds"].values())
    for entry in main_plan["runs"]:
        complete_fixture(comparison / "collections" / entry["run_id"])
    summary = runner.summarize(comparison)
    assert len(summary["runs"]) == 24
    for config in ("astra", "sol"):
        assert not summary["gates"][config]["passed"]  # all decline, checks only lose cost
        for world in ("a", "b"):
            assert set(summary["repeatability"][config][world]) == set(POLICIES)
            assert (
                summary["repeatability"][config][world]["cost_aware"]["final_probability_mae_pp"]
                == 0
            )
    changed = dict(main_plan, order_seed=0)
    with pytest.raises(ValueError, match="committed bytes"):
        asyncio.run(runner.run(comparison, changed))


def test_failed_attempt_stops_admission_and_retains_usage(tmp_path, monkeypatch):
    from epistemics.source_selective import runner

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
    plan["implementation_sha256"] = fingerprint()
    (tmp_path / "plan.json").write_bytes(encoded(plan))
    (tmp_path / "plan.sha256").write_text(digest(encoded(plan)))
    with pytest.raises(SystemExit):
        asyncio.run(runner.run(tmp_path, plan))
    record = json.loads((tmp_path / "execution.json").read_bytes())
    assert (
        len(calls) == 2
        and record["unattempted_runs"] == 6
        and record["unknown_usage_attempts"] == 2
    )


def test_expected_value_matches_enumerated_customer_sequences():
    import itertools

    for p in (0, 0.01, 0.3, 0.5, 0.7, 0.99, 1):
        for threshold in (0.3, 0.7):
            value = 0.0
            for outcome in itertools.product((0, 1), repeat=5):
                k = sum(outcome)
                a, b = 0.7**k * 0.3 ** (5 - k), 0.3**k * 0.7 ** (5 - k)
                marginal = p * a + (1 - p) * b
                posterior = p * a / marginal
                value += marginal * max(0, posterior - threshold)
            ev = expected_value(p, threshold)
            assert ev == pytest.approx(value - max(0, p - threshold), abs=1e-14)
            assert 0 <= ev <= min(p * (1 - threshold), (1 - p) * threshold) + 1e-14
            assert choose("cost_aware", p, threshold, ev) == "stop"
            if ev > 1e-6:
                assert choose("cost_aware", p, threshold, ev - 1e-6) == "customer_panel"
    for x in (float("nan"), float("inf"), -0.01, 1.01):
        with pytest.raises(ValueError):
            expected_value(x, 0.3)


def test_price_design_crosses_priors_balances_thresholds_and_ignores_private_world():
    from collections import Counter

    m = memory_manifest(44)
    for seed in range(30):
        assigned = offers(m, seed)
        prices = {o["company_id"]: o["available_check_cost"] for o in assigned}
        assert Counter(prices.values()) == {0.01: 4, 0.04: 4, 0.2: 4}
        for prior in (0.2, 0.5, 0.8):
            assert {prices[c.company_id] for c in m.companies[12:] if c.prior_strong == prior} == {
                0.01,
                0.04,
                0.2,
            }
        for threshold in (0.3, 0.7):
            assert Counter(
                prices[c.company_id] for c in m.companies[12:] if c.threshold == threshold
            ) == {0.01: 2, 0.04: 2, 0.2: 2}
        assert assigned == offers(memory_manifest(999), seed)
    assert offers(m, 1) != offers(m, 2)


def test_order_balances_each_block_and_repeats_every_cell():
    from collections import Counter

    from epistemics.source_selective.runner import balanced_runs

    for seed in range(20):
        runs = balanced_runs(["astra", "sol"], ["a", "b"], seed)
        assert len(runs) == len({r["run_id"] for r in runs}) == 24
        assert set(
            Counter((r["configuration"], r["world"], r["policy"]) for r in runs).values()
        ) == {2}
        for i in range(0, 24, 6):
            block = runs[i : i + 6]
            assert len({(r["world"], r["repeat"]) for r in block}) == 1
            for config in ("astra", "sol"):
                assert {r["policy"] for r in block if r["configuration"] == config} == set(POLICIES)
        assert runs == balanced_runs(["astra", "sol"], ["a", "b"], seed)


def test_atomic_conditional_action_conflicting_concurrent_submissions(tmp_path):
    create(
        tmp_path / "run", PARTICIPANT, seed=3, price_seed=10, policy="cost_aware", synthetic=True
    )
    s = VerificationService(tmp_path / "run")
    for _ in range(12):
        trial = s.get_trial()["trial"]
        s.submit(trial["trial_id"], {"probability": 0.5, "decision": "decline"})
    # Reach an inexpensive provisional checkpoint to test opposite policy branches.
    while s.get_trial()["trial"]["assigned_verification"]["available_check_cost"] == 0.2:
        for _ in range(2):
            t = s.get_trial()["trial"]
            s.submit(t["trial_id"], {"probability": 0.0, "decision": "decline"})
    trial = s.get_trial()["trial"]
    threshold = trial["decision_threshold"]

    def submit(p):
        try:
            return s.submit(trial["trial_id"], {"probability": p, "decision": "decline"})
        except ValueError:
            return None

    with ThreadPoolExecutor(2) as pool:
        receipts = list(pool.map(submit, (0.0, threshold)))
    assert sum(r is not None for r in receipts) == 1
    with s.base.state() as state:
        accepted = state["answers"][-1]["answer"]
        assert accepted["query"] == ("stop" if accepted["probability"] == 0 else "customer_panel")
    final = s.get_trial()["trial"]
    assert final["assigned_verification"]["check_supplied"] == (
        accepted["query"] == "customer_panel"
    )
    assert "probability" in Answer.model_json_schema()["properties"]
    assert Answer.model_json_schema()["properties"]["probability"]["multipleOf"] == 0.01
