"""Facts common to every frozen collection root: plan, execution, usage and tool errors."""

import hashlib
import json
from pathlib import Path

USAGE = ("input_tokens", "cached_input_tokens", "output_tokens")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).exists() else None


def run_execution(directory):
    path = Path(directory) / "execution.json"
    if not path.exists():
        return {"status": "not_started" if not Path(directory).exists() else "running"}
    execution = json.loads(path.read_text())
    tools = execution.get("tools", [])
    return {
        "status": execution.get("status"),
        "elapsed_seconds": execution.get("elapsed_seconds"),
        "usage": execution.get("usage"),
        "tool_calls": len(tools),
        "tool_errors": sum(
            bool(t.get("result_is_error")) or t.get("status") != "completed" or bool(t.get("error"))
            for t in tools
        ),
        "started_at": execution.get("started_at"),
        "finished_at": execution.get("finished_at"),
    }


def facts(root):
    """Plan, execution and per-run facts for one collection root."""
    root = Path(root)
    plan = json.loads((root / "plan.json").read_text())
    runs = {e["run_id"]: e for e in plan["runs"]}
    per_run = {run_id: run_execution(root / "collections" / run_id) for run_id in runs}
    execution_path = root / "execution.json"
    execution = json.loads(execution_path.read_text()) if execution_path.exists() else None
    usage = {k: 0 for k in USAGE}
    for row in per_run.values():
        for k in USAGE:
            usage[k] += (row.get("usage") or {}).get(k, 0)
    completed = sum(r["status"] == "completed" for r in per_run.values())
    failed = sum(r["status"] == "failed" for r in per_run.values())
    if execution is None:
        status = "running"
    elif execution["status"] == "completed":
        status = "completed"
    elif completed == len(runs):
        status = "completed_with_summary_error"
    else:
        status = "stopped"
    return {
        "root": str(root),
        "phase": plan.get("phase"),
        "created_at": plan.get("created_at"),
        "implementation_sha256": plan.get("implementation_sha256"),
        "configurations": sorted({e["configuration"] for e in runs.values()}),
        "runs_planned": len(runs),
        "runs_completed": completed,
        "runs_failed": failed,
        "tool_errors": sum(r.get("tool_errors", 0) for r in per_run.values()),
        "usage": usage,
        "status": status,
        "runner_error": execution.get("error") if execution else None,
        "finished_at": execution.get("finished_at") if execution else None,
        "sha256": {
            name: sha256(root / name)
            for name in ("plan.json", "execution.json", "summary.json")
            if (root / name).exists()
        },
        "per_run": per_run,
    }
