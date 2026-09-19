import asyncio
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from epistemics.predictive.client import call, server_parameters
from epistemics.predictive.collection import (
    CollectionService,
    collection_status,
    create_collection,
    export_collection,
)
from epistemics.predictive.collection_models import (
    CollectionExport,
    CollectionManifest,
    CollectionSpec,
)
from epistemics.predictive.design import create_manifest, digest, episode, write_manifest

ANSWER = {"probability": 0.61, "decision": "act"}


@pytest.fixture
def collection(tmp_path):
    manifest = create_manifest(seed=901)
    write_manifest(tmp_path / "design", manifest)
    assignment = manifest.assignments[0]
    twin = next(
        a
        for a in manifest.assignments
        if a.matched_group == assignment.matched_group and a != assignment
    )
    spec = CollectionSpec(
        participant={
            "kind": "agent",
            "subject_id": "offline-fixture",
            "configuration": {
                "model": "test-fixture",
                "model_version": "1",
                "configuration_sha256": "a" * 64,
            },
        },
        response_origin="synthetic",
        purpose="transport_smoke",
        assignment_ids=[assignment.assignment_id, twin.assignment_id],
        configuration_scope="Fixture configuration only",
        execution_notes="Offline fixture, not a model invocation",
        allowed_tools=["mcp"],
        assistance=[],
    )
    directory = tmp_path / "collection"
    create_collection(tmp_path / "design", directory, spec)
    return directory, [assignment, twin], spec


def finish(service):
    while not (current := service.get_trial())["complete"]:
        service.submit(current["checkpoint"]["checkpoint_id"], ANSWER)
    return service.finish()


def test_sequential_immutable_resume_and_exact_export(collection):
    directory, assignments, _ = collection
    service = CollectionService(directory, assignments[0].assignment_id)
    first = service.get_trial()
    assert first["history"] == []
    assert first["checkpoint"]["evidence"] == []
    with pytest.raises(ValueError, match="current checkpoint"):
        service.submit(service.checkpoints[2].checkpoint_id, ANSWER)
    with pytest.raises(ValueError, match="every checkpoint"):
        service.finish()
    receipt = service.submit(first["checkpoint"]["checkpoint_id"], ANSWER)
    resumed = CollectionService(directory, assignments[0].assignment_id)
    assert resumed.submit(first["checkpoint"]["checkpoint_id"], ANSWER) == receipt
    assert resumed.get_trial()["history"][0]["receipt"] == receipt
    with pytest.raises(ValueError, match="cannot be changed"):
        resumed.submit(first["checkpoint"]["checkpoint_id"], ANSWER | {"probability": 0.7})
    finished = finish(resumed)
    assert resumed.finish() == finished
    assert resumed.submit(first["checkpoint"]["checkpoint_id"], ANSWER) == receipt
    with pytest.raises(ValueError, match="Every planned"):
        export_collection(directory)
    status = collection_status(directory)
    assert status["assignments"][0]["finished"]
    assert status["assignments"][1]["answered"] == 0
    finish(CollectionService(directory, assignments[1].assignment_id))
    data = export_collection(directory)
    assert export_collection(directory) == data
    report = CollectionExport.model_validate_json(data)
    assert report.collection.response_origin == "synthetic"
    assert report.collection.purpose == "transport_smoke"
    assert len(report.episodes) == 2
    assert report.episodes[0].observations[0].answer.probability == 0.61
    with pytest.raises(ValueError, match="already exported"):
        resumed.begin_attempt()


def test_concurrent_submissions_are_transactional(collection):
    directory, assignments, _ = collection
    services = [CollectionService(directory, assignments[0].assignment_id) for _ in range(4)]
    checkpoint_id = services[0].checkpoints[0].checkpoint_id
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(lambda s: s.submit(checkpoint_id, ANSWER), services))
    assert receipts == [receipts[0]] * 4
    assert services[0].get_trial()["answered"] == 1

    def submit_competing(pair):
        service, probability = pair
        try:
            service.submit(
                service.checkpoints[1].checkpoint_id, ANSWER | {"probability": probability}
            )
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit_competing, zip(services, [0.2, 0.8], strict=False)))
    assert sorted(results) == [False, True]
    assert services[0].get_trial()["answered"] == 2


@pytest.mark.parametrize("probability", [True, "0.5", -1, 2, float("nan"), float("inf")])
def test_invalid_answers_do_not_advance(collection, probability):
    directory, assignments, _ = collection
    service = CollectionService(directory, assignments[0].assignment_id)
    with pytest.raises(ValueError):
        service.submit(service.checkpoints[0].checkpoint_id, ANSWER | {"probability": probability})
    assert service.get_trial()["answered"] == 0


def test_configuration_rebinding_is_rejected_even_after_restart(collection):
    directory, assignments, _ = collection
    service = CollectionService(directory, assignments[0].assignment_id)
    service.get_trial()
    path = directory / "collection.json"
    data = json.loads(path.read_bytes())
    data["participant"]["subject_id"] = "different-agent"
    raw = json.dumps(data).encode()
    path.write_bytes(raw)
    (directory / "collection.sha256").write_text(digest(raw))
    with pytest.raises(ValueError, match="binding changed"):
        service.describe()
    with pytest.raises(ValueError, match="Stored response binding"):
        CollectionService(directory, assignments[0].assignment_id).get_trial()


def test_design_and_code_drift_rejected(collection, monkeypatch):
    directory, assignments, _ = collection
    service = CollectionService(directory, assignments[0].assignment_id)
    monkeypatch.setattr("epistemics.predictive.design.implementation_sha256", lambda: "0" * 64)
    with pytest.raises(ValueError, match="fingerprint has changed"):
        service.describe()
    with pytest.raises(ValueError, match="fingerprint has changed"):
        collection_status(directory)


def test_scope_and_origin_cannot_silently_change(collection, tmp_path):
    directory, assignments, spec = collection
    with pytest.raises(ValueError, match="entire ordered"):
        create_collection(
            directory / "design",
            tmp_path / "bad",
            spec.model_copy(update={"purpose": "full_pilot"}),
        )
    with pytest.raises(ValueError, match="origin must match"):
        CollectionSpec.model_validate(spec.model_dump() | {"response_origin": "human"})
    with pytest.raises(ValueError, match="not planned"):
        CollectionService(directory, "0" * 20)
    with pytest.raises(FileExistsError):
        create_collection(directory / "design", directory, spec)


def test_attempts_preserve_interruption_and_resume(collection):
    directory, assignments, _ = collection
    service = CollectionService(directory, assignments[0].assignment_id)
    interrupted = service.begin_attempt()
    service.submit(service.checkpoints[0].checkpoint_id, ANSWER)
    resumed = service.begin_attempt()
    service.end_attempt(resumed)
    attempts = collection_status(directory)["attempts"]
    assert attempts[0]["attempt_id"] == interrupted
    assert attempts[0]["transport_status"] == "open"
    assert attempts[1]["restored_answers"] == 1
    assert attempts[1]["transport_status"] == "closed"


def test_collection_schema_snapshots():
    for model, filename in (
        (CollectionSpec, "predictive-collection-spec.v1.json"),
        (CollectionManifest, "predictive-collection.v1.json"),
        (CollectionExport, "predictive-responses.v1.json"),
    ):
        actual = json.loads((Path(__file__).parents[1] / "schemas" / filename).read_bytes())
        actual.pop("$schema")
        assert actual == model.model_json_schema()


def test_missing_database_is_not_reinitialized(collection):
    directory, assignments, _ = collection
    service = CollectionService(directory, assignments[0].assignment_id)
    (directory / "responses.sqlite3").unlink()
    import sqlite3

    with pytest.raises(sqlite3.OperationalError):
        service.get_trial()
    assert not (directory / "responses.sqlite3").exists()


def test_design_bytes_are_bound_independently_of_sidecar(collection):
    directory, assignments, _ = collection
    service = CollectionService(directory, assignments[0].assignment_id)
    path = directory / "design" / "manifest.json"
    raw = path.read_bytes() + b"\n"
    path.write_bytes(raw)
    (path.parent / "manifest.sha256").write_text(digest(raw))
    with pytest.raises(ValueError, match="design binding changed"):
        service.get_trial()


def test_cli_bridge_and_private_export_round_trip(collection, tmp_path):
    directory, assignments, spec = collection
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(spec.model_dump_json())
    target = tmp_path / "cli-collection"

    def cli(*args, input=None):
        return subprocess.run(
            [sys.executable, "-m", "epistemics.cli", "predictive", *map(str, args)],
            input=input,
            capture_output=True,
            text=True,
            timeout=30,
        )

    result = cli("bind", "--design", directory / "design", "--spec", spec_path, "--output", target)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["response_origin"] == "synthetic"
    for assignment in assignments:
        requests = ["not-json", json.dumps({"tool": "get_trial"})]
        for checkpoint in episode(assignment):
            requests.append(
                json.dumps(
                    {
                        "tool": "submit_answer",
                        "arguments": {"checkpoint_id": checkpoint.checkpoint_id, "answer": ANSWER},
                    }
                )
            )
            requests.append(json.dumps({"tool": "get_trial"}))
        requests.extend([json.dumps({"tool": "finish_evaluation"}), json.dumps({"close": True})])
        result = cli(
            "client",
            "--collection",
            target,
            "--assignment",
            assignment.assignment_id,
            input="\n".join(requests) + "\n",
        )
        assert result.returncode == 0, result.stderr
        messages = [json.loads(line) for line in result.stdout.splitlines()]
        assert "protocol" in messages[0]
        assert "error" in messages[1]
        assert messages[-1]["result"]["complete"]
    status = cli("status", "--collection", target)
    assert status.returncode == 0, status.stderr
    assert all(a["finished"] for a in json.loads(status.stdout)["assignments"])
    output = tmp_path / "responses.json"
    result = cli("export", "--collection", target, "--output", output)
    assert result.returncode == 0, result.stderr
    assert CollectionExport.model_validate_json(output.read_bytes()).collection == (
        CollectionManifest.model_validate_json((target / "collection.json").read_bytes())
    )
    assert cli("export", "--collection", target, "--output", output).returncode != 0
    assert output.read_bytes() == export_collection(target)


def test_complete_full_pilot_export_preserves_every_partition(collection, tmp_path):
    directory, _, spec = collection
    from epistemics.predictive.design import load_manifest

    manifest = load_manifest(directory / "design")
    spec = spec.model_copy(
        update={
            "purpose": "full_pilot",
            "assignment_ids": [a.assignment_id for a in manifest.assignments],
        }
    )
    target = tmp_path / "full-pilot"
    create_collection(directory / "design", target, spec)
    for assignment in manifest.assignments:
        finish(CollectionService(target, assignment.assignment_id))
    result = CollectionExport.model_validate_json(export_collection(target))
    assert len(result.episodes) == 72
    assert sum(len(e.observations) for e in result.episodes) == 360
    assert {e.assignment.split for e in result.episodes} == {"profile", "policy", "heldout"}
    assert result.collection.purpose == "full_pilot"
    assert result.collection.response_origin == "synthetic"


def test_real_mcp_sequential_boundary_and_restart(collection):
    directory, assignments, _ = collection

    def public_only(value):
        if isinstance(value, dict):
            assert not set(value) & {
                "seed",
                "split",
                "matched_group",
                "assignments",
                "participant",
                "reference_probability",
                "parameters",
                "design_sha256",
                "response_origin",
            }
            for item in value.values():
                public_only(item)
        elif isinstance(value, list):
            for item in value:
                public_only(item)

    async def run():
        assignment = assignments[0]
        params = server_parameters(directory, assignment.assignment_id)
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            tools = {t.name: t for t in (await client.list_tools()).tools}
            assert set(tools) == {
                "describe_battery",
                "get_trial",
                "submit_answer",
                "finish_evaluation",
            }
            assert set(tools["submit_answer"].inputSchema["properties"]) == {
                "checkpoint_id",
                "answer",
            }
            for name in ("get_trial", "describe_battery", "finish_evaluation"):
                assert tools[name].inputSchema.get("properties", {}) == {}
            public_only(await call(client, "describe_battery"))
            assert (await client.call_tool("finish_evaluation", {})).isError
            current = await call(client, "get_trial")
            public_only(current)
            assert current["checkpoint"] == episode(assignment)[0].model_dump(mode="json")
            assert (
                await client.call_tool(
                    "submit_answer",
                    {
                        "checkpoint_id": f"{assignment.assignment_id}:2",
                        "answer": ANSWER,
                    },
                )
            ).isError
            submission = {"checkpoint_id": current["checkpoint"]["checkpoint_id"], "answer": ANSWER}
            receipt = await call(client, "submit_answer", submission)
        # A new real server process resumes the same accepted history.
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            assert await call(client, "submit_answer", submission) == receipt
            current = await call(client, "get_trial")
            assert current["answered"] == 1
            assert current["history"][0]["receipt"] == receipt
            while not current["complete"]:
                public_only(current)
                checkpoint = current["checkpoint"]
                assert checkpoint == episode(assignment)[current["answered"]].model_dump(
                    mode="json"
                )
                response = await call(
                    client,
                    "submit_answer",
                    {
                        "checkpoint_id": checkpoint["checkpoint_id"],
                        "answer": ANSWER,
                    },
                )
                public_only(response)
                current = await call(client, "get_trial")
            completion = await call(client, "finish_evaluation")
            public_only(completion)
            assert completion == await call(client, "finish_evaluation")

    asyncio.run(run())
    attempts = collection_status(directory)["attempts"]
    assert len(attempts) == 2
    assert attempts[1]["restored_answers"] == 1
