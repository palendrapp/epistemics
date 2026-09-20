import asyncio
import json
import sqlite3
import sys

import pytest
from test_benchmark import fill, setup

from epistemics.benchmark.analysis import analyze, lock_predictions
from epistemics.benchmark.models import BenchmarkReport, RecoveryPolicy
from epistemics.benchmark.recovery import amend, chains
from epistemics.benchmark.runner import admit, collect
from epistemics.benchmark.store import accounting, database, episode_states, load
from epistemics.predictive.analysis import reference_probability
from epistemics.predictive.collection import CollectionService
from epistemics.predictive.design import digest, episode
from epistemics.predictive.models import Parameters
from epistemics.predictive.simulation import simulate


def interrupted(tmp_path, *, origin="agent", reference=False):
    root, manifest, design = setup(tmp_path, origin=origin)
    assignment = next(a for a in design.assignments if a.split == "profile")
    service = CollectionService(root / "collections" / "alpha", assignment.assignment_id)
    for cp in episode(assignment)[:3]:
        p = reference_probability(cp) if reference else 0.6
        service.submit(
            cp.checkpoint_id, {"probability": p, "decision": "act" if p > 0.5 else "defer"}
        )
    failed = {
        "attempt_id": "historical-failure",
        "configuration_id": "alpha",
        "assignment_id": assignment.assignment_id,
        "status": "failed",
        "usage": None,
        "elapsed_seconds": 10,
        "violation": None,
        "tool_calls": [],
    }
    with database(root) as (db, _, _):
        db.execute("INSERT INTO runs VALUES (?, ?)", (failed["attempt_id"], json.dumps(failed)))
    return root, manifest, design, assignment


def amendment(root, destination, **kwargs):
    return amend(
        root,
        destination,
        RecoveryPolicy(unknown_usage_reserve_tokens=1000, retry_delay_seconds=0),
        reviewed_process_exits=["historical-failure"],
        reason="Observed unsuccessful process exit; cause and usage remain unknown.",
        **kwargs,
    )


def test_amendment_preserves_predecessor_and_immutable_history(tmp_path, monkeypatch):
    old, _, _, assignment = interrupted(tmp_path)
    original_manifest = (old / "benchmark.json").read_bytes()
    original_db = (old / "collections" / "alpha" / "responses.sqlite3").read_bytes()
    before = episode_states(old, "alpha")[assignment.assignment_id]
    monkeypatch.setattr("epistemics.benchmark.store.fingerprint", lambda: "1" * 64)
    with pytest.raises(ValueError, match="source fingerprint"):
        load(old)
    new = tmp_path / "recovery"
    manifest = amendment(old, new)
    assert manifest.benchmark_version == "provenance-benchmark/0.2.0"
    assert manifest.amendment.predecessor_sha256 == digest(original_manifest)
    assert manifest.budget.max_attempts == 309
    assert manifest.budget.max_processed_tokens == 1000000
    assert (old / "benchmark.json").read_bytes() == original_manifest
    assert (old / "collections" / "alpha" / "responses.sqlite3").read_bytes() == original_db
    service = CollectionService(new / "collections" / "alpha", assignment.assignment_id)
    trial = service.get_trial()
    assert trial["answered"] == 3 and trial["checkpoint"]["index"] == 3
    assert len(trial["history"]) == 3
    cp = episode(assignment)[0]
    assert (
        service.submit(cp.checkpoint_id, before["answers"][0]["answer"])
        == before["answers"][0]["receipt"]
    )
    with pytest.raises(ValueError, match="cannot be changed"):
        service.submit(cp.checkpoint_id, {"probability": 0.4, "decision": "defer"})
    assert episode_states(new, "alpha")[assignment.assignment_id] == before
    assert accounting(new)["runs"][0] == accounting_legacy(old)[0]
    (new / "predecessor" / "benchmark.json").write_bytes(original_manifest + b" ")
    with pytest.raises(ValueError, match="snapshot changed"):
        load(new)


def accounting_legacy(root):
    with sqlite3.connect(root / "benchmark.sqlite3") as db:
        return [json.loads(p) for (p,) in db.execute("SELECT payload FROM runs ORDER BY rowid")]


@pytest.mark.parametrize(
    "obstacle", ["later", "lock", "running", "violation", "tool_error", "classified"]
)
def test_amendment_rejects_unsafe_or_post_lock_changes(tmp_path, obstacle):
    root, _, design, _ = interrupted(tmp_path)
    if obstacle == "later":
        a = next(a for a in design.assignments if a.split == "policy")
        CollectionService(root / "collections" / "alpha", a.assignment_id).get_trial()
    else:
        with database(root) as (db, _, _):
            if obstacle == "lock":
                db.execute("INSERT INTO metadata VALUES ('prediction_lock', '{}')")
            else:
                r = json.loads(db.execute("SELECT payload FROM runs").fetchone()[0])
                if obstacle == "running":
                    r["status"] = "running"
                elif obstacle == "violation":
                    r["violation"] = "Unapproved tool"
                elif obstacle == "tool_error":
                    r["tool_calls"] = [{"status": "failed"}]
                else:
                    r["failure_category"] = "incomplete_episode"
                db.execute("UPDATE runs SET payload=?", (json.dumps(r),))
    with pytest.raises(ValueError):
        amendment(root, tmp_path / "recovery")
    assert not (tmp_path / "recovery").exists()


def test_resumed_process_finishes_same_episode_without_rewriting_answers(tmp_path, monkeypatch):
    old, _, design, assignment = interrupted(tmp_path)
    root = tmp_path / "recovery"
    manifest = amendment(old, root)
    before = episode_states(root, "alpha")[assignment.assignment_id]["answers"]
    fake = tmp_path / "respondent.py"
    fake.write_text("""import asyncio,json,sys
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
 p=StdioServerParameters(command=sys.executable,args=["-m","epistemics.benchmark.mcp_server"],env={"EPISTEMICS_BENCHMARK":sys.argv[1],"EPISTEMICS_CONFIGURATION":sys.argv[2],"EPISTEMICS_ASSIGNMENT":sys.argv[3]})
 async with stdio_client(p) as (r,w),ClientSession(r,w) as c:
  await c.initialize()
  async def call(name,args={}):
   result=await c.call_tool(name,args)
   assert not result.isError,result.content
   return json.loads(result.content[0].text)
  trial=await call("get_trial")
  assert trial["answered"]==3 and len(trial["history"])==3
  cp=trial["checkpoint"]
  await call("submit_answer",{"checkpoint_id":cp["checkpoint_id"],"answer":{"probability":0.7,"decision":"act"}})
  await call("finish_evaluation")
 print(json.dumps({"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":50,"output_tokens":20}}),flush=True)
asyncio.run(main())
""")
    monkeypatch.setattr("epistemics.benchmark.runner.codex_version", lambda: "fixture-cli")
    monkeypatch.setattr(
        "epistemics.benchmark.runner.command",
        lambda d, c, a: [sys.executable, str(fake), str(d), c.configuration_id, a],
    )
    completed = asyncio.run(collect(root, split="profile", max_episodes=1))
    assert len(completed) == 1
    assert completed[0]["retry_of"] == "historical-failure"
    assert completed[0]["accepted_answers_at_start"] == 3
    assert completed[0]["context_mode"] == "resumed_public_history"
    state = episode_states(root, "alpha")[assignment.assignment_id]
    assert state["answers"][:3] == before
    assert len(state["answers"]) == 4 and state["completion"] is not None
    resources = accounting(root)
    assert resources["totals"]["processed_tokens"] == 120
    assert resources["totals"]["admission_token_charge"] == 1120
    assert not resources["totals"]["accounting_complete"]
    assert resources["totals"]["unresolved_attempts"] == 0
    assert resources["totals"]["unknown_usage_attempts"] == 1
    assert resources["recovery"]["retry_attempts"] == 1
    assert resources["runs"][0]["status"] == "failed"
    with pytest.raises(ValueError, match="profile cases first"):
        lock_predictions(root)
    beta = manifest.configurations[1].configuration_id
    assert (
        admit(
            manifest,
            resources["totals"],
            resources=resources,
            configuration_id=beta,
            assignment_id=assignment.assignment_id,
        )
        is None
    )


@pytest.mark.parametrize(
    "limit",
    ["per_episode", "total", "unknown", "tokens", "time", "attempts", "other_case", "semantic"],
)
def test_recovery_admission_limits(tmp_path, limit):
    old, _, _, assignment = interrupted(tmp_path)
    root = tmp_path / "recovery"
    manifest = amendment(old, root)
    resources = accounting(root)
    if limit == "per_episode":
        row = dict(
            resources["runs"][0],
            attempt_id="failed-retry",
            retry_of="historical-failure",
            failure_category="process_exit",
        )
        resources["runs"].append(row)
    elif limit == "total":
        resources["recovery"]["retry_attempts"] = manifest.recovery.max_retries_total
    elif limit == "unknown":
        resources["totals"]["unknown_usage_attempts"] = 3
    elif limit == "tokens":
        resources["totals"]["admission_token_charge"] = manifest.budget.max_processed_tokens
    elif limit == "time":
        resources["totals"]["elapsed_seconds"] = manifest.budget.max_wall_seconds
    elif limit == "attempts":
        resources["totals"]["attempts"] = manifest.budget.max_attempts
    elif limit == "semantic":
        resources["runs"][0]["failure_category"] = "incomplete_episode"
    with pytest.raises(ValueError):
        admit(
            manifest,
            resources["totals"],
            resources=resources,
            configuration_id="beta" if limit == "other_case" else "alpha",
            assignment_id=assignment.assignment_id,
        )


def test_retry_parent_cannot_cross_episodes():
    failed = {
        "attempt_id": "a",
        "configuration_id": "alpha",
        "assignment_id": "one",
        "status": "failed",
    }
    retry = dict(failed, attempt_id="b", assignment_id="two", retry_of="a")
    with pytest.raises(ValueError, match="parent is missing"):
        chains([failed, retry])


def test_execution_gate_precedes_export_freeze(tmp_path):
    root, manifest, design = setup(tmp_path, origin="agent")
    fill(root, manifest, design, "profile")
    with pytest.raises(ValueError, match="completed execution"):
        lock_predictions(root)
    for split in ("policy", "heldout"):
        fill(root, manifest, design, split)
    # Deliberately inject a placeholder lock to reach the final execution gate;
    # no agent execution exists, so no collection should become unresumable.
    with database(root) as (db, _, _):
        db.execute("INSERT INTO metadata VALUES ('prediction_lock', '{}')")
    with pytest.raises(ValueError, match="completed execution"):
        analyze(root)
    for c in manifest.configurations:
        with sqlite3.connect(root / "collections" / c.configuration_id / "responses.sqlite3") as db:
            assert db.execute("SELECT count(*) FROM exports").fetchone()[0] == 0


@pytest.mark.parametrize("mode", ["once", "twice", "violation"])
def test_collection_automatically_recovers_only_bounded_runtime_exits(tmp_path, monkeypatch, mode):
    old, _, _ = setup(tmp_path, origin="agent")
    root = tmp_path / "recovery"
    amend(
        old,
        root,
        RecoveryPolicy(unknown_usage_reserve_tokens=1000, retry_delay_seconds=0),
        reviewed_process_exits=[],
        reason="Freeze the offline recovery fixture before collection.",
    )
    fake = tmp_path / "respondent.py"
    fake.write_text("""import json,sys
from pathlib import Path
from epistemics.predictive.collection import CollectionService
s=CollectionService(Path(sys.argv[1])/"collections"/sys.argv[2],sys.argv[3])
t=s.get_trial()
first=t["answered"]==0
if first:
 s.submit(t["checkpoint"]["checkpoint_id"],{"probability":0.6,"decision":"act"})
if sys.argv[4]=="violation":
 print(json.dumps({"type":"item.completed","item":{"type":"command_execution"}}),flush=True)
if first or sys.argv[4]=="twice":
 raise SystemExit(7)
while not (t:=s.get_trial())["complete"]:
 s.submit(t["checkpoint"]["checkpoint_id"],{"probability":0.6,"decision":"act"})
s.finish()
print(json.dumps({"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":50,"output_tokens":20}}),flush=True)
""")
    monkeypatch.setattr("epistemics.benchmark.runner.codex_version", lambda: "fixture-cli")
    monkeypatch.setattr(
        "epistemics.benchmark.runner.command",
        lambda d, c, a: [sys.executable, str(fake), str(d), c.configuration_id, a, mode],
    )
    if mode == "once":
        assert len(asyncio.run(collect(root, split="profile", max_episodes=1))) == 1
    else:
        with pytest.raises(ValueError, match="recovery"):
            asyncio.run(collect(root, split="profile", max_episodes=1))
    r = accounting(root)
    assert len(r["runs"]) == (1 if mode == "violation" else 2)
    assert r["runs"][0]["status"] == "failed"
    assert r["totals"]["unknown_usage_attempts"] == (2 if mode == "twice" else 1)
    if mode == "once":
        assert r["runs"][1]["status"] == "completed"
        assert r["runs"][1]["accepted_answers_at_start"] == 1
        assert r["runs"][1]["retry_of"] == r["runs"][0]["attempt_id"]
    if mode == "violation":
        assert r["runs"][0]["failure_category"] == "task_violation"


def test_amended_report_includes_recovery_and_unknown_accounting(tmp_path):
    old, _, design, assignment = interrupted(tmp_path, origin="synthetic", reference=True)
    root = tmp_path / "recovery"
    manifest = amendment(old, root)
    # Complete the pre-existing case without changing its accepted prefix.
    service = CollectionService(root / "collections" / "alpha", assignment.assignment_id)
    cp = episode(assignment)[3]
    p = reference_probability(cp)
    service.submit(cp.checkpoint_id, {"probability": p, "decision": "act" if p > 0.5 else "defer"})
    service.finish()
    with database(root) as (db, _, _):
        db.execute(
            "INSERT INTO runs VALUES ('retry', ?)",
            (
                json.dumps(
                    {
                        "attempt_id": "retry",
                        "configuration_id": "alpha",
                        "assignment_id": assignment.assignment_id,
                        "retry_of": "historical-failure",
                        "status": "completed",
                        "elapsed_seconds": 1,
                        "usage": {
                            "input_tokens": 100,
                            "cached_input_tokens": 50,
                            "output_tokens": 20,
                        },
                    }
                ),
            ),
        )
    # Chunked collection must recover the same known effective weights as an
    # uninterrupted synthetic collection, without rewriting its accepted prefix.
    for i, c in enumerate(manifest.configurations):
        generated = {
            (r.assignment_id, r.index): r for r in simulate(design, Parameters(copy_weight=i))
        }
        for a in design.assignments:
            if a.split != "profile" or (
                c.configuration_id == "alpha" and a.assignment_id == assignment.assignment_id
            ):
                continue
            s = CollectionService(root / "collections" / c.configuration_id, a.assignment_id)
            for cp in episode(a):
                row = generated[(a.assignment_id, cp.index)]
                s.submit(cp.checkpoint_id, {"probability": row.response, "decision": row.decision})
            s.finish()
    lock = json.loads(lock_predictions(root))
    assert lock["protocol_status"] == "amended"
    assert not lock["accounting_complete_at_lock"]
    for i, c in enumerate(manifest.configurations):
        fitted = lock["configurations"][c.configuration_id]["individual_fit"]["parameters"]
        assert fitted == pytest.approx(
            {"intercept": 0, "prior_weight": 1, "evidence_weight": 1, "copy_weight": i}, abs=1e-12
        )
    fill(root, manifest, design, "policy")
    fill(root, manifest, design, "heldout")
    report = BenchmarkReport.model_validate_json(analyze(root))
    assert report.protocol_status == "amended"
    assert report.execution_scope == "includes_retried_episodes"
    assert report.accounting_complete is False
    assert report.accounting["totals"]["usage_scope"] == "known_lower_bound"
    assert report.result == "criteria_met"
    value = report.model_dump(mode="json")
    value["accounting_complete"] = True
    with pytest.raises(ValueError, match="disclosures"):
        BenchmarkReport.model_validate(value)
