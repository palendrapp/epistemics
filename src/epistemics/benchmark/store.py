"""Frozen benchmark manifests, stage gates and exact-byte analysis locks."""

import json
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

from epistemics.benchmark.models import BenchmarkManifest, BenchmarkSpec
from epistemics.predictive.collection import create_collection, load_collection, transaction
from epistemics.predictive.design import (
    budget,
    digest,
    encoded,
    load_manifest,
    write_manifest,
)
from epistemics.predictive.design import (
    implementation_sha256 as task_fingerprint,
)
from epistemics.service import now


def fingerprint():
    package = Path(__file__).parent
    return digest(
        task_fingerprint().encode()
        + b"".join(p.name.encode() + b"\0" + p.read_bytes() for p in sorted(package.glob("*.py")))
    )


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def create(design_directory, directory, spec, *, codex_version, response_origin="agent"):
    from epistemics.benchmark.runner import runner_configuration

    spec = BenchmarkSpec.model_validate(spec)
    design = load_manifest(design_directory)
    if spec.purpose == "prediction_pilot" and design.replicates < 2:
        raise ValueError("The prediction pilot requires at least two design repetitions")
    expected_attempts = len(spec.configurations) * (
        len(design.assignments) if spec.purpose == "prediction_pilot" else 2
    )
    if spec.budget.max_attempts < expected_attempts:
        raise ValueError("Attempt budget cannot cover every planned episode")
    root = Path(directory)
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    write_manifest(root / "design", design)
    design_hash = digest((root / "design" / "manifest.json").read_bytes())
    assignments = design.assignments
    if spec.purpose == "development_costing":
        group = next(a.matched_group for a in assignments if a.split == "heldout")
        assignments = [a for a in assignments if a.matched_group == group]
    hashes = {}
    for configuration in spec.configurations:
        config_hash = digest(json_bytes(runner_configuration(configuration, codex_version)))
        collection = root / "collections" / configuration.configuration_id
        create_collection(
            root / "design",
            collection,
            {
                "participant": {
                    "kind": "agent",
                    "subject_id": configuration.configuration_id,
                    "configuration": {
                        "model": configuration.model,
                        "model_version": configuration.model_revision,
                        "configuration_sha256": config_hash,
                    },
                },
                "response_origin": response_origin,
                "purpose": "full_pilot"
                if spec.purpose == "prediction_pilot"
                else "transport_smoke",
                "assignment_ids": [a.assignment_id for a in assignments],
                "configuration_scope": "Runner configuration, prompt, requested model/effort and CLI version; excludes hidden provider instructions and unverified model revision.",
                "execution_notes": "Fresh Codex process per episode, continuous context within it. Public MCP only requested; runtime records are operator observations, not independent attestation. Failed attempts are retained; no silent exclusions.",
                "allowed_tools": ["assigned MCP server"],
                "assistance": [],
            },
        )
        hashes[configuration.configuration_id] = digest(
            (collection / "collection.json").read_bytes()
        )
    manifest = BenchmarkManifest(
        **spec.model_dump(mode="json"),
        design_sha256=design_hash,
        implementation_sha256=fingerprint(),
        runner_sha256=digest((Path(__file__).parent / "runner.py").read_bytes()),
        codex_version=codex_version,
        collection_hashes=hashes,
        response_origin=response_origin,
        created_at=now(),
    )
    raw = encoded(manifest)
    (root / "benchmark.json").write_bytes(raw)
    (root / "benchmark.json").chmod(0o600)
    (root / "benchmark.sha256").write_text(digest(raw) + "\n")
    with closing(sqlite3.connect(root / "benchmark.sqlite3")) as db, db:
        db.execute("CREATE TABLE metadata (id TEXT PRIMARY KEY, payload BLOB NOT NULL)")
        db.execute("INSERT INTO metadata VALUES ('binding', ?)", (digest(raw),))
        db.execute("CREATE TABLE runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
    (root / "benchmark.sqlite3").chmod(0o600)
    return manifest


def load(directory):
    root = Path(directory)
    raw = (root / "benchmark.json").read_bytes()
    if digest(raw) != (root / "benchmark.sha256").read_text().strip():
        raise ValueError("Benchmark manifest bytes changed")
    manifest = BenchmarkManifest.model_validate_json(raw)
    if manifest.implementation_sha256 != fingerprint():
        raise ValueError("Benchmark source fingerprint changed; use the original implementation")
    design = load_manifest(root / "design")
    if digest((root / "design" / "manifest.json").read_bytes()) != manifest.design_sha256:
        raise ValueError("Benchmark design binding changed")
    for configuration in manifest.configurations:
        collection, _, collection_hash = load_collection(
            root / "collections" / configuration.configuration_id
        )
        if collection_hash != manifest.collection_hashes[configuration.configuration_id]:
            raise ValueError("Benchmark collection binding changed")
        if (
            collection.design_sha256 != manifest.design_sha256
            or collection.response_origin != manifest.response_origin
        ):
            raise ValueError("Collections must share the design and response origin")
    return manifest, design, digest(raw)


@contextmanager
def database(directory):
    manifest, design, manifest_hash = load(directory)
    uri = (Path(directory).resolve() / "benchmark.sqlite3").as_uri() + "?mode=rw"
    with closing(sqlite3.connect(uri, uri=True, timeout=30)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT payload FROM metadata WHERE id='binding'").fetchone() != (
            manifest_hash,
        ):
            raise ValueError("Stored benchmark binding changed")
        yield db, manifest, design


def episode_states(directory, configuration_id):
    path = Path(directory) / "collections" / configuration_id
    with transaction(path) as (db, _, _):
        return {i: json.loads(p) for i, p in db.execute("SELECT id,payload FROM episodes")}


def complete_split(directory, manifest, design, split):
    ids = [a.assignment_id for a in design.assignments if a.split == split]
    for configuration in manifest.configurations:
        states = episode_states(directory, configuration.configuration_id)
        if any(states.get(i, {}).get("completion") is None for i in ids):
            return False
    return True


def guard(directory, configuration_id, assignment_id):
    with database(directory) as (db, manifest, design):
        if configuration_id not in manifest.collection_hashes:
            raise ValueError("Unplanned configuration")
        assignment = next((a for a in design.assignments if a.assignment_id == assignment_id), None)
        if assignment is None:
            raise ValueError("Unplanned assignment")
        if manifest.purpose == "development_costing":
            return
        if (
            assignment.split != "profile"
            and not db.execute("SELECT 1 FROM metadata WHERE id='prediction_lock'").fetchone()
        ):
            raise ValueError("Profile fits and comparator predictions must be locked first")
        if assignment.split == "heldout" and not complete_split(
            directory, manifest, design, "policy"
        ):
            raise ValueError("Finish the policy partition before opening held-out cases")


def accounting(directory):
    with database(directory) as (db, manifest, design):
        runs = [json.loads(p) for (p,) in db.execute("SELECT payload FROM runs ORDER BY rowid")]
        totals = {
            key: sum((r.get("usage") or {}).get(key, 0) for r in runs)
            for key in ("input_tokens", "cached_input_tokens", "output_tokens")
        }
        totals["processed_tokens"] = totals["input_tokens"] + totals["output_tokens"]
        totals["elapsed_seconds"] = sum(r.get("elapsed_seconds", 0) for r in runs)
        totals["attempts"] = len(runs)
        totals["unresolved_attempts"] = sum(r["status"] != "completed" for r in runs)
        totals["unknown_usage_attempts"] = sum(r.get("usage") is None for r in runs)
        totals["billing"] = manifest.budget.billing
        totals["marginal_usd"] = None
        planned = budget(design)
        return {"totals": totals, "runs": runs, "full_design_per_configuration": planned}
