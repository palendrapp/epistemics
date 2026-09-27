import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from epistemics.disposition_tasks.collection import (
    CollectionService,
    Report,
    create,
    export,
    load_report,
)
from epistemics.disposition_tasks.presentation import Answer
from epistemics.disposition_tasks.render import items_for, render
from epistemics.disposition_tasks.simulation import simulate
from epistemics.disposition_tasks.validation import PRIVATE, audit, validate
from epistemics.source_learning.simulation import PARTICIPANT
from epistemics.source_learning.storage import encoded

ORDER = list(range(23, -1, -1))


def run_all(service, answer):
    trial, seen = service.get_trial()["trial"], []
    while trial is not None:
        seen.append(trial)
        trial = service.submit(trial["trial_id"], answer(trial))["next_trial"]
    return seen


def test_rendering_audit_and_key_wording():
    assert audit()["cases"] == 624
    conflict = render("corroboration", "markets", 4)
    assert "a relayed call simply repeats the original call" in conflict["case"]
    assert "90% of the time" in conflict["case"] and "it says demand is low" in conflict["case"]
    assert "uses different wording from" in conflict["case"]
    probe = render("corroboration", "ecology", 18)
    assert probe["question"].startswith("What is the probability that Station S59 forwarded")
    silence = render("disclosure", "markets", 3)
    assert "does not mention any of its 4 indicators" in silence["case"]
    assert "Dunmore Freight's demand" in silence["question"]
    check = render("checks", "markets", 6)
    assert "comes back positive with probability 60%" in check["case"]
    assert check["response"] == "points"
    for module in ("corroboration", "disclosure", "checks"):
        for cover in ("markets", "ecology"):
            text = json.dumps([render(module, cover, i) for i in range(24)]).lower()
            assert not any(word in text for word in PRIVATE)
    with pytest.raises(ValueError, match="Unknown cover"):
        render("checks", "weather", 0)


def test_answers_follow_the_requested_response():
    assert Answer.model_validate({"probability": 0.29}).probability == 0.29
    for bad in ({}, {"probability": 0.5, "points": 3}, {"probability": 0.505}, {"points": 101}):
        with pytest.raises(ValueError):
            Answer.model_validate(bad)
    with pytest.raises(ValueError):
        Answer.model_validate({"points": 12.5})
    for p in range(101):
        Answer.model_validate({"probability": round(p / 100, 2)})


def test_service_orders_cases_locks_and_keeps_answers_immutable(tmp_path):
    create(
        tmp_path / "run",
        PARTICIPANT,
        module="disclosure",
        cover="ecology",
        order=ORDER,
        synthetic=True,
    )
    s = CollectionService(tmp_path / "run")
    with pytest.raises(ValueError, match="Read"):
        s.submit("case-01", {"probability": 0.5})
    first = s.get_trial()["trial"]
    assert first["case"] == render("disclosure", "ecology", 23)["case"]
    with pytest.raises(ValueError, match="asks for probability"):
        s.submit(first["trial_id"], {"points": 10})
    with ThreadPoolExecutor(4) as pool:
        receipts = list(
            pool.map(lambda _: s.submit(first["trial_id"], {"probability": 0.4}), range(4))
        )
    assert all(r == receipts[0] for r in receipts) and receipts[0]["answered"] == 1
    with pytest.raises(ValueError, match="cannot be changed"):
        s.submit(first["trial_id"], {"probability": 0.41})
    with pytest.raises(ValueError, match="current checkpoint"):
        s.submit("case-03", {"probability": 0.4})
    with pytest.raises(ValueError, match="Answer every case"):
        s.finish()
    assert len(s.get_history()["history"]) == 1
    with pytest.raises(ValueError, match="permutation"):
        create(
            tmp_path / "bad",
            PARTICIPANT,
            module="checks",
            cover="markets",
            order=[0] * 24,
            synthetic=True,
        )


def test_simulated_respondent_is_recovered_and_tampering_rejected(tmp_path):
    truth = {"disposition": 0.3, "gamma": 1.0, "bias": 0.0, "report_sd": 0.1}
    report = simulate(
        tmp_path / "run",
        module="corroboration",
        cover="markets",
        order=ORDER,
        truth=truth,
        seed=2,
    )
    assert report.analysis["fit"]["parameters"]["disposition"]["mean"] == pytest.approx(
        0.3, abs=0.1
    )
    assert report.analysis["model_comparison"]["preferred"] == "dependence"
    assert [r["item"] for r in report.analysis["rows"]] == ORDER
    assert load_report(tmp_path / "run") == report
    bad = json.loads(encoded(report))
    bad["observations"][0]["trial"]["case"] = "Changed"
    with pytest.raises(ValueError):
        Report.model_validate(bad)
    late = json.loads(encoded(report))
    late["observations"][0]["locked_at"] = late["completed_at"]
    with pytest.raises(ValueError):
        Report.model_validate(late)
    manifest = tmp_path / "run" / "manifest.json"
    manifest.write_bytes(manifest.read_bytes().replace(b'"markets"', b'"ecology"'))
    with pytest.raises(ValueError, match="manifest"):
        CollectionService(tmp_path / "run")


def test_checks_module_separates_certainty_functions(tmp_path):
    truth = {"function": "entropy", "certainty_value": 120.0, "decision_weight": 1.0, "wtp_sd": 2.0}
    report = simulate(
        tmp_path / "run",
        module="checks",
        cover="ecology",
        order=ORDER,
        truth=truth,
        seed=4,
    )
    analysis = report.analysis
    assert analysis["certainty_function"]["preferred"] == "entropy"
    fitted = analysis["fits"]["entropy"]["parameters"]["certainty_value"]["mean"]
    assert fitted == pytest.approx(120, abs=15)
    assert analysis["mean_points"]["zero_decision_value"] > 5


def test_complete_stdio_mcp_collection(tmp_path):
    create(
        tmp_path / "run",
        PARTICIPANT,
        module="checks",
        cover="markets",
        order=ORDER,
        synthetic=True,
    )

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "epistemics.disposition_tasks.mcp_server"],
            env={**os.environ, "EPISTEMICS_DISPOSITION_TASKS": str(tmp_path / "run")},
        )
        async with stdio_client(params) as (reader, writer), ClientSession(reader, writer) as c:
            await c.initialize()
            assert len((await c.list_tools()).tools) == 5
            described = json.loads((await c.call_tool("describe_battery", {})).content[0].text)
            assert "true maximum" in described["instructions"] and described["cases"] == 24
            t = json.loads((await c.call_tool("get_trial", {})).content[0].text)["trial"]
            while t is not None:
                result = await c.call_tool(
                    "submit_answer", {"trial_id": t["trial_id"], "answer": {"points": 7}}
                )
                assert not result.isError
                t = json.loads(result.content[0].text)["next_trial"]
            result = await c.call_tool("finish_evaluation", {})
            assert not result.isError

    asyncio.run(run())
    export(tmp_path / "run")
    report = load_report(tmp_path / "run")
    assert len(report.observations) == 24
    assert all(r["response"] == 7 for r in report.analysis["rows"])


def test_validation_and_plan_freeze_orders_before_answers(tmp_path, monkeypatch):
    from epistemics.disposition_tasks import runner

    monkeypatch.setattr(runner, "codex_version", lambda: "test-only")
    result = validate(3)
    assert result["passed"] and len(result["contexts"]) == 28
    paths = []
    for seed in (1, 2):
        p = tmp_path / f"validation-{seed}.json"
        p.write_bytes(encoded({**result, "seed": seed}))
        paths.append(p)
    with pytest.raises(ValueError, match="two distinct"):
        runner.prepare(tmp_path / "one", paths[:1])
    bad = [
        {"configurations": ["astra"], "modules": ["checks"], "contexts": [["open", "markets", 1]]}
    ]
    with pytest.raises(ValueError, match="only the paired"):
        runner.prepare(tmp_path / "two", paths, groups=bad)
    groups = [
        {
            "configurations": ["astra"],
            "modules": ["checks", "disclosure"],
            "contexts": runner.CONTEXTS,
        },
        {
            "configurations": ["luna"],
            "modules": ["corroboration"],
            "contexts": [["learning-high", "markets", 1]],
        },
    ]
    root = tmp_path / "acceptance"
    plan = runner.prepare(root, paths, groups=groups)
    assert len(plan["runs"]) == 7 and set(plan["configurations"]) == {"astra", "luna"}
    assert {(r["module"], r["variant"], r["cover"], r["repeat"]) for r in plan["runs"]} == {
        (m, v, c, r) for m in ("checks", "disclosure") for v, c, r in runner.CONTEXTS
    } | {("corroboration", "learning-high", "markets", 1)}
    assert all((r["reveal_seed"] is None) == (r["variant"] == "paired") for r in plan["runs"])
    assert len(runner.check_groups(runner.PRESETS["round-2"])) == 32
    orders = [tuple(r["order"]) for r in plan["runs"]]
    assert len(set(orders)) == len(orders)
    for e in plan["runs"]:
        s = CollectionService(root / "collections" / e["run_id"])
        m = s.manifest
        assert (m.module, m.cover, m.variant, m.order) == (
            e["module"],
            e["cover"],
            e["variant"],
            e["order"],
        )
        argv = runner.command(root, e, plan["configurations"][e["configuration"]])
        assert any("disposition_tasks.mcp_server" in a for a in argv)
        assert any("EPISTEMICS_DISPOSITION_TASKS" in a for a in argv)
        assert not any("source_panel" in a for a in argv[:-1]) and argv[-1] == runner.PROMPT
    assert not any(
        w in runner.PROMPT.lower()
        for w in ("relay", "selective", "certainty", "withhold", "dependence", "silence")
    )
    with pytest.raises(ValueError, match="committed bytes"):
        asyncio.run(runner.run(root, dict(plan, order_seed=0)))


def test_agreement_compares_repeats_and_covers():
    from epistemics.disposition_tasks.runner import agreement

    def row(cover, repeat, mean):
        return {
            "variant": "paired",
            "cover": cover,
            "repeat": repeat,
            "estimate": {"parameter": "disposition", "mean": mean},
        }

    result = agreement(
        {
            ("astra", "corroboration"): [
                row("markets", 1, 0.3),
                row("markets", 2, 0.4),
                row("ecology", 1, 0.7),
            ]
        }
    )["astra/corroboration"]
    assert result["repeat_differences"] == [pytest.approx(0.1)]
    assert result["cross_cover_difference"] == pytest.approx(0.4)
    assert np.isclose(result["estimates"]["paired/ecology1"]["mean"], 0.7)


def test_variants_change_only_the_framing_sentences():
    paired = render("disclosure", "markets", 1, "paired")["case"]
    open_ = render("disclosure", "markets", 1, "open")["case"]
    suggestive = render("disclosure", "markets", 1, "suggestive")["case"]
    assert "could be either kind" in paired and "could be either kind" not in open_
    assert paired.replace(" Brightwater Cable could be either kind.", "") == open_
    assert "about to ask investors for new financing" in suggestive
    assert (
        suggestive.replace("\n\nBrightwater Cable is about to ask investors for new financing.", "")
        == open_
    )
    reassuring = render("corroboration", "ecology", 10, "reassuring")["case"]
    assert "may have sampled" not in reassuring and "different sampling method" in reassuring
    with pytest.raises(ValueError, match="variant"):
        render("checks", "markets", 0, "open")


def test_learning_variant_reveals_each_answered_case(tmp_path):
    with pytest.raises(ValueError, match="reveal seed"):
        create(
            tmp_path / "x",
            PARTICIPANT,
            module="corroboration",
            cover="markets",
            order=ORDER,
            variant="learning-high",
            synthetic=True,
        )
    truth = {"start": 0.5, "strength": 2.0, "gamma": 1.0, "bias": 0.0, "report_sd": 0.05}
    report = simulate(
        tmp_path / "run",
        module="corroboration",
        cover="markets",
        order=ORDER,
        truth=truth,
        seed=6,
        variant="learning-high",
        reveal_seed=11,
    )
    manifest = report.manifest
    kinds = items_for("corroboration")["kind"]
    assert all(
        (r is None) == (k == "single") for r, k in zip(manifest.revealed, kinds, strict=True)
    )
    assert "previous_case" not in report.observations[0].trial
    shown = [o.trial["previous_case"] for o in report.observations[1:]]
    assert all(s.startswith("Revealed after case") or "nothing to reveal" in s for s in shown)
    instructions = CollectionService(tmp_path / "run").describe()["instructions"]
    assert "same population" in instructions and "nothing carries over" not in instructions
    learning = report.analysis["learning"]
    assert learning["learning_probability"] > 0.9
    assert learning["parameters"]["start"]["mean"] == pytest.approx(0.5, abs=0.15)


def test_value_of_certainty_near_zero_selects_no_function(tmp_path):
    truth = {"function": "linear", "certainty_value": 0.0, "decision_weight": 1.0, "wtp_sd": 0.2}
    report = simulate(
        tmp_path / "run", module="checks", cover="markets", order=ORDER, truth=truth, seed=8
    )
    assert report.analysis["certainty_function"]["preferred"] == "undetermined"
    assert report.analysis["mean_points"]["zero_decision_value"] == 0
    assert report.analysis["mean_points"]["positive_decision_value"] == pytest.approx(59 / 6)
