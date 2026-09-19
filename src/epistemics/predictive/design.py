"""Balanced, partitioned provenance graphs with public prefix views only."""

import hashlib
import json
import random
import secrets
from itertools import product
from pathlib import Path

from epistemics.predictive.models import (
    PRIORS,
    SPLIT_FAMILIES,
    Assignment,
    DesignManifest,
    EvidenceCard,
    PublicCheckpoint,
    TrackRecord,
)

# Each entry is (direction relative to the matched claim, copy parent or None).
STRUCTURES = {
    "paired_reports": ((1, None), (1, 0), (-1, None)),
    "repeated_chain": ((1, None), (1, 0), (-1, None), (1, 1)),
    "interleaved_chains": ((-1, None), (1, None), (1, 1), (-1, 0), (1, 2)),
}
DOMAINS = {
    "paired_reports": (
        "component supplier",
        "meet its next-quarter shipment target",
        "customer orders",
    ),
    "repeated_chain": (
        "subscription service",
        "meet its annual renewal target",
        "customer renewals",
    ),
    "interleaved_chains": (
        "distribution business",
        "meet its next-quarter delivery target",
        "contract deliveries",
    ),
}
INSTRUCTIONS = (
    "Assess the company's target using only the information shown so far. The starting "
    "probability is the base rate for comparable companies. Publisher histories refer to "
    "resolved original assessments; inspect each document's provenance. Give your current "
    "probability (0..1) and choose act or defer under the stated hypothetical payoffs. "
    "No explanation of private reasoning is required. Each company episode is separate."
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(model):
    return (model.model_dump_json(indent=2) + "\n").encode()


def implementation_sha256():
    package = Path(__file__).resolve().parent.parent
    files = [
        *Path(__file__).parent.glob("*.py"),
        package / "models.py",
        package / "participants.py",
    ]
    return digest(
        b"".join(
            str(p.relative_to(package)).encode() + b"\0" + p.read_bytes() for p in sorted(files)
        )
    )


def create_manifest(*, seed=None, replicates=1):
    if isinstance(replicates, bool) or not isinstance(replicates, int) or not 1 <= replicates <= 8:
        raise ValueError("Use 1..8 replicates")
    rng = random.Random(secrets.randbits(128) if seed is None else seed)
    assignments, used_seeds = [], set()
    for split, prior, strength, direction, replicate in product(
        SPLIT_FAMILIES, PRIORS, ("weak", "strong"), (-1, 1), range(replicates)
    ):
        world_seed = rng.randrange(2**52)
        while world_seed in used_seeds:
            world_seed = rng.randrange(2**52)
        used_seeds.add(world_seed)
        group = digest(f"group:{world_seed}".encode())[:20]
        for provenance in ("independent", "copied"):
            assignments.append(
                Assignment(
                    assignment_id=digest(f"assignment:{world_seed}:{provenance}".encode())[:20],
                    matched_group=group,
                    split=split,
                    family=SPLIT_FAMILIES[split],
                    seed=world_seed,
                    prior=prior,
                    strength=strength,
                    direction=direction,
                    replicate=replicate,
                    provenance=provenance,
                )
            )
    rng.shuffle(assignments)
    return DesignManifest(
        implementation_sha256=implementation_sha256(),
        replicates=replicates,
        assignments=assignments,
    )


def public_checkpoint(assignment: Assignment, index: int) -> PublicCheckpoint:
    structure = STRUCTURES[assignment.family]
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index <= len(structure):
        raise ValueError("Checkpoint index is outside this episode")
    rng = random.Random(assignment.seed)
    company = f"{rng.choice(['Alder', 'Cedar', 'Juniper', 'Rowan'])} {rng.choice(['Works', 'Group', 'Systems', 'Partners'])}"
    _, target, observation = DOMAINS[assignment.family]
    cards = []
    for i, (relative_direction, parent) in enumerate(structure[:index]):
        positive = assignment.direction * relative_direction == 1
        assessment = "meets_target" if positive else "misses_target"
        strong = (assignment.strength == "strong") == (relative_direction == 1)
        copy = parent is not None and assignment.provenance == "copied"
        cards.append(
            EvidenceCard(
                document_id=f"document-{i + 1}",
                publisher=f"Desk {chr(65 + i)}",
                assessment=assessment,
                text=f"Our assessment of {observation} indicates that {company} will {'meet' if positive else 'miss'} its target.",
                based_on=f"document-{parent + 1}" if copy else None,
                provenance_note=(
                    "Relays the cited document's assessment; no additional sample was collected."
                    if copy
                    else "Original assessment from a separately collected, non-overlapping sample."
                ),
                original_assessment_history=TrackRecord(correct=15 if strong else 12),
            )
        )
    return PublicCheckpoint(
        checkpoint_id=f"{assignment.assignment_id}:{index}",
        index=index,
        company=company,
        question=f"Will {company} {target}?",
        prior_probability=assignment.prior,
        instructions=INSTRUCTIONS,
        evidence=cards,
    )


def episode(assignment):
    return [public_checkpoint(assignment, i) for i in range(len(STRUCTURES[assignment.family]) + 1)]


def budget(manifest):
    result = {}
    for split in SPLIT_FAMILIES:
        rows = [a for a in manifest.assignments if a.split == split]
        result[f"{split}_episodes"] = len(rows)
        result[f"{split}_checkpoints"] = sum(len(STRUCTURES[a.family]) + 1 for a in rows)
    result["episodes_per_configuration"] = len(manifest.assignments)
    result["checkpoints_per_configuration"] = sum(
        result[f"{s}_checkpoints"] for s in SPLIT_FAMILIES
    )
    return result


def write_manifest(directory, manifest):
    # A fresh operator-owned directory prevents accidental reuse or overwrite.
    directory = Path(directory)
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    data = encoded(manifest)
    path = directory / "manifest.json"
    with path.open("xb") as stream:
        stream.write(data)
    path.chmod(0o600)
    (directory / "manifest.sha256").write_text(digest(data) + "\n")
    return path


def load_manifest(directory):
    directory = Path(directory)
    data = (directory / "manifest.json").read_bytes()
    if digest(data) != (directory / "manifest.sha256").read_text().strip():
        raise ValueError("Manifest bytes changed after design creation")
    manifest = DesignManifest.model_validate(json.loads(data))
    if manifest.implementation_sha256 != implementation_sha256():
        raise ValueError("Use the original implementation; its fingerprint has changed")
    return manifest
