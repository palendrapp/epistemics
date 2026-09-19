"""Operator-owned schedule, precommitted splits, and public-only episode materials."""

import hashlib
import json
import random
import secrets
from itertools import product
from pathlib import Path
from uuid import uuid4

from epistemics.discovery.battery import generate_battery
from epistemics.service import now
from epistemics.study.models import Assignment, StudyManifest, StudyTrial


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def implementation_sha256():
    root = Path(__file__).resolve().parent.parent
    h = hashlib.sha256()
    for folder in (root / "study", root / "discovery"):
        for path in sorted(folder.glob("*.py")):
            h.update(str(path.relative_to(root)).encode() + b"\0" + path.read_bytes())
    for path in (root / "models.py", root / "company/models.py"):
        h.update(str(path.relative_to(root)).encode() + b"\0" + path.read_bytes())
    return h.hexdigest()


def episode(assignment: Assignment):
    original = generate_battery(assignment.seed, variant=assignment.variant)
    initial = json.loads(json.dumps(original[0]))
    for source in initial["trial"]["sources"]:
        source["archive"] = []
    initial["trial"]["background"] += (
        " Source track records arrive at the next checkpoint. At this checkpoint assess the "
        "sources using only their descriptions; an empty archive is not a record of failures."
    )
    records = [initial, *original]
    for index, record in enumerate(records):
        record["trial"]["index"] = index
        record["trial"]["trial_id"] = f"study{index:02d}"
        record["trial"] = StudyTrial.model_validate(record["trial"]).model_dump(mode="json")
    return records


def create_manifest(
    agent, *, worlds=12, replicates=2, seed=None, response_origin="agent", plan=None
):
    if not 4 <= worlds <= 128 or not 1 <= replicates <= 10:
        raise ValueError("Use 4..128 worlds and 1..10 replicates")
    rng = random.Random(secrets.randbits(64) if seed is None else seed)
    # Whole world groups are split before any responses are collected.
    world_seeds = rng.sample(range(2**40), worlds)
    n_train = max(2, worlds * 2 // 3)
    assignments = []
    for i, world_seed in enumerate(world_seeds):
        for framing, history, response, replicate in product(
            ("skeptical", "optimistic"), ("short", "long"), ("growth", "failure"), range(replicates)
        ):
            assignments.append(
                Assignment(
                    assignment_id=str(uuid4()),
                    world_id=f"world-{i:03d}",
                    seed=world_seed,
                    split="train" if i < n_train else "heldout",
                    replicate=replicate,
                    variant={
                        "framing": framing,
                        "history": history,
                        "response": response,
                        "lineage": "shared" if i % 2 else "independent",
                    },
                )
            )
    rng.shuffle(assignments)
    return StudyManifest(
        study_id=str(uuid4()),
        created_at=now(),
        implementation_sha256=implementation_sha256(),
        agent=agent,
        assignments=assignments,
        response_origin=response_origin,
        **({"analysis_plan": plan} if plan is not None else {}),
    )


def write_manifest(directory, manifest):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "manifest.json"
    # Never replace a prior design or reassign already observed data.
    data = (manifest.model_dump_json(indent=2) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(data)
    path.chmod(0o600)
    (directory / "manifest.sha256").write_text(digest(data) + "\n")
    return path


def load_manifest(directory, *, check_implementation=True):
    directory = Path(directory)
    data = (directory / "manifest.json").read_bytes()
    if digest(data) != (directory / "manifest.sha256").read_text().strip():
        raise ValueError("Manifest bytes changed after study creation")
    manifest = StudyManifest.model_validate_json(data)
    if check_implementation and manifest.implementation_sha256 != implementation_sha256():
        raise ValueError("Use the study's original implementation; its fingerprint has changed")
    return manifest, digest(data)
