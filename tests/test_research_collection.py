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

from epistemics.research_world.analysis import panel
from epistemics.research_world.collection import (
    CollectionService,
    Report,
    create,
    load_report,
    world_for,
)
from epistemics.research_world.design import TYPES, design
from epistemics.research_world.presentation import HINT
from epistemics.research_world.simulation import simulate
from epistemics.research_world.web import LocalServer
from epistemics.research_world.world import PAIRS
from epistemics.source_learning.simulation import PARTICIPANT
from epistemics.source_learning.storage import encoded

ITEMS = [
    {"pair_seed": 11, "family": "disclosure", "presentation": "selected", "check_price": 0.05},
    {"pair_seed": 12, "family": "shared_origin", "presentation": "relayed", "check_price": 0.02},
    {"pair_seed": 13, "family": "shared_origin", "presentation": "independent", "check_price": 0.1},
]
PRIVATE = (
    '"strong":',
    "pair_seed",
    "normative",
    "naive",
    "atom_id",
    "p_favorable",
    '"presentation":',
    "silent_control",
    "relayed",
)


def run_all(service, answers):
    trial, seen = service.get_trial()["trial"], []
    while trial is not None:
        seen.append(trial)
        answer = answers(trial)
        trial = service.submit(trial["trial_id"], answer)["next_trial"]
    return seen


def test_buying_adds_one_final_checkpoint_and_skipping_moves_on(tmp_path):
    create(
        tmp_path / "run",
        PARTICIPANT,
        arm="unprompted",
        items=ITEMS,
        check_offered=True,
        synthetic=True,
    )
    s = CollectionService(tmp_path / "run")
    with pytest.raises(ValueError, match="Read"):
        s.submit("case-01-assessment", {"probability": 0.5, "decision": "decline", "check": "skip"})

    def answers(trial):
        if trial["stage"] == "final":
            return {"probability": 0.6, "decision": "invest"}
        return {
            "probability": 0.5,
            "decision": "decline",
            "check": "buy" if trial["case_number"] == 2 else "skip",
        }

    seen = run_all(s, answers)
    assert [t["trial_id"] for t in seen] == [
        "case-01-assessment",
        "case-02-assessment",
        "case-02-final",
        "case-03-assessment",
    ]
    final = seen[2]
    assert final["documents"][-1]["doc_id"] == "C1" and final["check_cost_charged"] == 0.02
    assert "check_price" not in final
    for trial in seen:
        assert not any(key in json.dumps(trial) for key in PRIVATE)
    s.finish()
    report = load_report_after_export(tmp_path / "run")
    rows = {r["case"]: r for r in report.analysis["rows"]}
    assert rows[2]["check_bought"] and not rows[1]["check_bought"]
    assert rows[2]["expected_payoff"] <= rows[2]["optimal_expected_payoff"]


def load_report_after_export(directory):
    from epistemics.research_world.collection import export

    export(directory)
    return load_report(directory)


def test_answers_are_immutable_retries_idempotent_and_checks_validated(tmp_path):
    create(
        tmp_path / "run", PARTICIPANT, arm="hinted", items=ITEMS, check_offered=True, synthetic=True
    )
    s = CollectionService(tmp_path / "run")
    first = s.get_trial()["trial"]
    with pytest.raises(ValueError, match="check"):
        s.submit(first["trial_id"], {"probability": 0.5, "decision": "decline"})
    with pytest.raises(ValueError):
        s.submit(first["trial_id"], {"probability": 0.505, "decision": "decline", "check": "skip"})
    a = {"probability": 0.4, "decision": "decline", "check": "skip"}
    with ThreadPoolExecutor(4) as pool:
        receipts = list(pool.map(lambda _: s.submit(first["trial_id"], a), range(4)))
    assert all(r == receipts[0] for r in receipts) and receipts[0]["answered"] == 1
    with pytest.raises(ValueError, match="cannot be changed"):
        s.submit(first["trial_id"], {"probability": 0.9, "decision": "invest", "check": "buy"})
    assert s.get_trial()["trial"]["trial_id"] == "case-02-assessment"
    with pytest.raises(ValueError, match="Answer every case"):
        s.finish()


def test_arms_change_only_structure_statements(tmp_path):
    trials = {}
    unpriced = [{k: v for k, v in i.items() if k != "check_price"} for i in ITEMS]
    for arm in ("unprompted", "hinted", "explicit"):
        create(
            tmp_path / arm,
            PARTICIPANT,
            arm=arm,
            items=unpriced,
            check_offered=False,
            synthetic=True,
        )
        s = CollectionService(tmp_path / arm)
        trials[arm] = s.get_trial()["trial"]
        instructions = s.describe()["instructions"]
        assert (HINT in instructions) == (arm == "hinted")
        assert ("independent_survey" in s.describe()) is False
        assert "check_price" not in trials[arm]
    assert trials["explicit"]["structure_note"].startswith("The letter covers only KPIs")
    for arm in ("unprompted", "hinted"):
        assert "structure_note" not in trials[arm]
        assert trials[arm]["documents"] == trials["explicit"]["documents"]


def test_frozen_manifest_and_report_tampering_are_rejected(tmp_path):
    report = simulate(
        tmp_path / "run", ITEMS, arm="explicit", check_offered=True, chi=0.3, noise_sd=0.0, seed=1
    )
    assert load_report(tmp_path / "run") == report
    bad = json.loads(encoded(report))
    bad["observations"][0]["trial"]["documents"][0]["text"] = "Changed"
    with pytest.raises(ValueError):
        Report.model_validate(bad)
    late = json.loads(encoded(report))
    late["observations"][0]["locked_at"] = late["completed_at"]
    with pytest.raises(ValueError):
        Report.model_validate(late)
    manifest = tmp_path / "run" / "manifest.json"
    manifest.write_bytes(manifest.read_bytes().replace(b'"explicit"', b'"hinted"'))
    with pytest.raises(ValueError, match="manifest"):
        CollectionService(tmp_path / "run")


def test_design_separates_matched_presentations_and_matches_prices():
    contexts = design(5, 8, 4, 2, check_offered=True)
    assert len(contexts) == 4 and all(len(c["items"]) == 10 for c in contexts)
    placed = {}
    for c in contexts:
        manipulated = {
            i["family"] for i in c["items"] if i["presentation"] == PAIRS[i["family"]][1]
        }
        assert len(manipulated) == 1
        for i in c["items"]:
            assert i["presentation"] == TYPES[c["context_type"]].get(i["family"]) or (
                i["family"] == TYPES[c["context_type"]]["anchor"]
            )
            placed.setdefault((i["family"], i["pair_seed"]), []).append((c["context_type"], i))
    paired = [v for v in placed.values() if len(v) == 2]
    assert len(paired) == 16
    for (type_a, a), (type_b, b) in paired:
        assert type_a != type_b and a["check_price"] == b["check_price"]


def test_panel_recovers_neglect_across_separate_contexts(tmp_path):
    contexts = design(7, 12, 6, 1, check_offered=False)
    reports = [
        simulate(
            tmp_path / f"{i}",
            c["items"],
            arm="unprompted",
            check_offered=False,
            chi=0.7,
            noise_sd=0.0,
            seed=i,
        )
        for i, c in enumerate(contexts)
    ]
    estimates = panel(reports)
    for family in PAIRS:
        assert estimates[f"unprompted/{family}"]["chi"] == pytest.approx(0.7, abs=0.1)
        assert estimates[f"unprompted/{family}"]["pairs"] == 12
    with pytest.raises(ValueError):
        panel([reports[0], reports[0]])


def test_complete_stdio_mcp_collection(tmp_path):
    create(
        tmp_path / "run",
        PARTICIPANT,
        arm="explicit",
        items=ITEMS,
        check_offered=True,
        synthetic=True,
    )

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.research_world.mcp_server"],
            env={**os.environ, "EPISTEMICS_RESEARCH_WORLD": str(tmp_path / "run")},
        )
        async with stdio_client(params) as (reader, writer), ClientSession(reader, writer) as c:
            await c.initialize()
            assert len((await c.list_tools()).tools) == 5
            described = json.loads((await c.call_tool("describe_battery", {})).content[0].text)
            assert "independent_survey" in described
            t = json.loads((await c.call_tool("get_trial", {})).content[0].text)["trial"]
            while t is not None:
                answer = {"probability": 0.55, "decision": "invest"}
                if t["stage"] == "assessment":
                    answer["check"] = "buy"
                result = await c.call_tool(
                    "submit_answer", {"trial_id": t["trial_id"], "answer": answer}
                )
                assert not result.isError
                t = json.loads(result.content[0].text)["next_trial"]
            result = await c.call_tool("finish_evaluation", {})
            assert not result.isError

    asyncio.run(run())
    report = load_report_after_export(tmp_path / "run")
    assert len(report.observations) == 6


def test_complete_human_browser_http_and_auth(tmp_path):
    create(
        tmp_path / "run",
        {"kind": "human", "subject_id": "test:synthetic"},
        arm="unprompted",
        items=ITEMS,
        check_offered=True,
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
        while not (state := request("/api/state"))["current"]["complete"]:
            trial = state["current"]["trial"]
            answer = {"probability": 0.5, "decision": "decline"}
            if trial["stage"] == "assessment":
                answer["check"] = "skip"
            request("/api/answers", {"trial_id": trial["trial_id"], "answer": answer})
        request("/api/finish", {})
        assert world_for(server.service.manifest.items[0]).family == "disclosure"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_validation_and_plan_freeze_the_design_before_answers(tmp_path, monkeypatch):
    from epistemics.research_world import runner
    from epistemics.research_world.validation import validate

    monkeypatch.setattr(runner, "codex_version", lambda: "test-only")
    result = validate(3, audited_seeds=500, worlds_per_family=8)
    assert result["passed"] and len(result["estimates"]) == 6
    paths = []
    for seed in (1, 2):
        p = tmp_path / f"validation-{seed}.json"
        p.write_bytes(encoded({**result, "seed": seed}))
        paths.append(p)
    with pytest.raises(ValueError, match="two distinct"):
        runner.prepare(tmp_path / "one", paths[:1])
    root = tmp_path / "acceptance"
    plan = runner.prepare(root, paths, configurations=("astra",), arms=("unprompted", "explicit"))
    assert len(plan["runs"]) == 4
    assert {(r["arm"], r["context_type"]) for r in plan["runs"]} == {
        (a, t) for a in ("unprompted", "explicit") for t in ("A", "B")
    }
    for e in plan["runs"]:
        s = CollectionService(root / "collections" / e["run_id"])
        assert s.manifest.arm == e["arm"] and len(s.manifest.items) == 9
        argv = runner.command(root, e, plan["configurations"]["astra"])
        assert any("research_world.mcp_server" in a for a in argv)
        assert any("EPISTEMICS_RESEARCH_WORLD" in a for a in argv)
        assert not any("source_panel" in a for a in argv[:-1]) and argv[-1] == runner.PROMPT
        assert "hint" not in runner.PROMPT.lower() and "relay" not in runner.PROMPT.lower()
    with pytest.raises(ValueError, match="committed bytes"):
        asyncio.run(runner.run(root, dict(plan, order_seed=0)))
