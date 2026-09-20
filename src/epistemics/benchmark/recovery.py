"""Bounded, visible recovery; original attempts and accepted answers remain intact."""

import json
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from epistemics.benchmark.models import Amendment, BenchmarkManifest, RecoveryPolicy
from epistemics.predictive.design import digest, encoded
from epistemics.service import now


def chains(runs):
    result = {}
    for i, run in enumerate(runs):
        key = (run["configuration_id"], run.get("assignment_id", f"unscoped-{i}"))
        history = result.setdefault(key, [])
        if history:
            if (
                not history[-1].get("attempt_id")
                or run.get("retry_of") != history[-1]["attempt_id"]
                or history[-1]["status"] != "failed"
            ):
                raise ValueError("Invalid recovery chain; never overwrite or skip an attempt")
        elif run.get("retry_of") is not None:
            raise ValueError("Recovery parent is missing")
        history.append(run)
    return result


def recoverable(manifest, attempt):
    if attempt["status"] != "failed" or attempt.get("violation"):
        return False
    if any(c.get("status") not in (None, "completed") for c in attempt.get("tool_calls", [])):
        return False
    category = attempt.get("failure_category")
    if category in {"process_exit", "timeout", "missing_usage"}:
        return True
    # Historical failures lacking structured diagnostics need an explicit, frozen review.
    return (
        category is None
        and manifest.amendment is not None
        and attempt.get("attempt_id") in manifest.amendment.reviewed_process_exits
    )


def summary(manifest, runs):
    grouped = chains(runs)
    retried = [
        {"configuration_id": c, "assignment_id": a, "attempts": len(h)}
        for (c, a), h in grouped.items()
        if len(h) > 1
    ]
    return {
        "retry_attempts": sum(len(h) - 1 for h in grouped.values()),
        "failed_attempts": sum(r["status"] == "failed" for r in runs),
        "unresolved_attempts": sum(h[-1]["status"] != "completed" for h in grouped.values()),
        "retried_episodes": retried,
        "protocol_status": "amended" if manifest.amendment else "original",
        "execution_scope": "includes_retried_episodes" if retried else "uninterrupted",
    }


def admit_recovery(manifest, resources, configuration_id, assignment_id):
    policy, totals, runs = manifest.recovery, resources["totals"], resources["runs"]
    if policy is None:
        raise ValueError("No frozen recovery policy")
    grouped = chains(runs)
    key = (configuration_id, assignment_id)
    unfinished = {k: h for k, h in grouped.items() if h[-1]["status"] != "completed"}
    if any(k != key for k in unfinished):
        raise ValueError("Resolve the pending episode before opening another case")
    if totals["unknown_usage_attempts"] >= policy.stop_at_unknown_usage_attempts:
        raise ValueError("Unknown-usage stop threshold reached")
    history = grouped.get(key, [])
    if not history:
        return None
    if not recoverable(manifest, history[-1]):
        raise ValueError("Attempt is not eligible for recovery; inspect the retained failure")
    if len(history) > policy.max_retries_per_episode:
        raise ValueError("Per-episode recovery limit reached")
    if resources["recovery"]["retry_attempts"] >= policy.max_retries_total:
        raise ValueError("Total recovery limit reached")
    return history[-1]["attempt_id"]


def require_execution(directory, manifest, design, split=None, *, resources=None):
    """Check episode completion separately from completeness of cost accounting."""
    if manifest.response_origin != "agent":
        return
    from epistemics.benchmark.store import accounting

    resources = resources if resources is not None else accounting(directory)
    totals = resources["totals"]
    if totals["unresolved_attempts"]:
        raise ValueError("Unresolved execution records prevent locking or reporting")
    if manifest.recovery is None and totals["unknown_usage_attempts"]:
        raise ValueError("Unknown cost records prevent a complete empirical report")
    if manifest.recovery is not None:
        p = manifest.recovery
        if (
            totals["unknown_usage_attempts"] >= p.stop_at_unknown_usage_attempts
            or resources["recovery"]["retry_attempts"] > p.max_retries_total
        ):
            raise ValueError("Recovery limits prevent locking or reporting")
    grouped = chains(resources["runs"])
    expected = {
        (c.configuration_id, a.assignment_id)
        for c in manifest.configurations
        for a in design.assignments
        if split is None or a.split == split
    }
    if split is None and set(grouped) != expected:
        raise ValueError("Every empirical episode needs a completed execution and usage record")
    for key in expected:
        history = grouped.get(key, [])
        if (
            not history
            or history[-1]["status"] != "completed"
            or history[-1]["usage"] is None
            or not history[-1].get("usage_complete", True)
        ):
            raise ValueError("Every empirical episode needs a completed execution and usage record")
        if len(history) > 1 and (
            manifest.recovery is None
            or len(history) > manifest.recovery.max_retries_per_episode + 1
            or not all(recoverable(manifest, r) for r in history[:-1])
        ):
            raise ValueError("Invalid recovery history")


def snapshot_hashes(directory):
    root = Path(directory)
    paths = sorted(root.rglob("*"))
    if any(p.is_symlink() for p in paths):
        raise ValueError("Snapshot must not contain symlinks")
    return {str(p.relative_to(root)): digest(p.read_bytes()) for p in paths if p.is_file()}


def verify_predecessor(root, amendment):
    raw = (root / "predecessor.sha256.json").read_bytes()
    if digest(raw) != amendment.predecessor_snapshot_sha256:
        raise ValueError("Predecessor snapshot binding changed")
    if snapshot_hashes(root / "predecessor") != json.loads(raw):
        raise ValueError("Predecessor snapshot changed")
    if (
        digest((root / "predecessor" / "benchmark.json").read_bytes())
        != amendment.predecessor_sha256
    ):
        raise ValueError("Predecessor manifest binding changed")


def amend(source, destination, policy, *, reviewed_process_exits, reason):
    """Clone a pre-lock plan and bind a new protocol to an exact predecessor snapshot."""
    from epistemics.benchmark.runner import operator_lock, runner_configuration
    from epistemics.benchmark.store import _load, episode_states, fingerprint, json_bytes

    source, destination = Path(source).resolve(), Path(destination).resolve()
    policy = RecoveryPolicy.model_validate(policy)
    if destination.exists() or source in destination.parents:
        raise ValueError("Use a new destination outside the predecessor directory")
    with operator_lock(source):
        # An amendment explicitly changes benchmark implementation, never the task design.
        old, design, old_hash = _load(source, check_implementation=False)
        if old.amendment or old.recovery or old.purpose != "prediction_pilot":
            raise ValueError("Only a no-recovery prediction plan can be amended once")
        uri = (source / "benchmark.sqlite3").as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as db:
            if db.execute("SELECT payload FROM metadata WHERE id='binding'").fetchone() != (
                old_hash,
            ):
                raise ValueError("Stored predecessor binding changed")
            if db.execute(
                "SELECT 1 FROM metadata WHERE id IN ('prediction_lock','report')"
            ).fetchone():
                raise ValueError("Amend recovery before locking or analyzing responses")
            runs = [json.loads(p) for (p,) in db.execute("SELECT payload FROM runs ORDER BY rowid")]
        if any(r["status"] == "running" for r in runs):
            raise ValueError("A running or abandoned attempt requires inspection first")
        failed = {r["attempt_id"]: r for r in runs if r["status"] == "failed"}
        reviewed = set(reviewed_process_exits)
        if len(reviewed) != len(reviewed_process_exits) or not reviewed <= failed.keys():
            raise ValueError("Review only distinct, existing failed attempt IDs")
        for key in reviewed:
            r = failed[key]
            if (
                r.get("failure_category") is not None
                or r.get("violation")
                or any(c.get("status") not in (None, "completed") for c in r.get("tool_calls", []))
            ):
                raise ValueError("Review cannot override classified failures or task violations")
        later = {a.assignment_id for a in design.assignments if a.split != "profile"}
        for c in old.configurations:
            if set(episode_states(source, c.configuration_id)) & later:
                raise ValueError("Later cases already opened; cannot amend this profile protocol")
            metadata = json.loads(
                (source / "collections" / c.configuration_id / "collection.json").read_bytes()
            )
            expected = digest(json_bytes(runner_configuration(c, old.codex_version)))
            if metadata["participant"]["configuration"]["configuration_sha256"] != expected:
                raise ValueError("Respondent configuration changed; cannot reuse this collection")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".recovery-", dir=destination.parent) as temporary:
            target = Path(temporary) / "run"
            shutil.copytree(source, target)
            shutil.copytree(source, target / "predecessor")
            hashes = json_bytes(snapshot_hashes(target / "predecessor"))
            (target / "predecessor.sha256.json").write_bytes(hashes)
            (target / "predecessor.sha256.json").chmod(0o600)
            value = old.model_dump(mode="json")
            value.update(
                benchmark_version="provenance-benchmark/0.2.0",
                recovery=policy.model_dump(mode="json"),
                amendment=Amendment(
                    predecessor_sha256=old_hash,
                    predecessor_snapshot_sha256=digest(hashes),
                    reviewed_process_exits=sorted(reviewed),
                    reason=reason,
                ).model_dump(mode="json"),
                implementation_sha256=fingerprint(),
                runner_sha256=digest((Path(__file__).parent / "runner.py").read_bytes()),
                created_at=now(),
            )
            value["budget"]["max_attempts"] += policy.max_retries_total
            new = BenchmarkManifest.model_validate(value)
            if any(not recoverable(new, r) for r in failed.values()):
                raise ValueError("Predecessor contains a failure ineligible for recovery")
            chains(runs)
            unknown = sum(r.get("usage") is None or r["status"] != "completed" for r in runs)
            if unknown >= policy.stop_at_unknown_usage_attempts:
                raise ValueError("Predecessor already reaches the unknown-usage stop threshold")
            raw = encoded(new)
            (target / "benchmark.json").write_bytes(raw)
            (target / "benchmark.sha256").write_text(digest(raw) + "\n")
            with closing(sqlite3.connect(target / "benchmark.sqlite3")) as db, db:
                db.execute("UPDATE metadata SET payload=? WHERE id='binding'", (digest(raw),))
            target.rename(destination)
        return new
