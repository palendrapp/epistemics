import json
from pathlib import Path

import numpy as np
import pytest

from epistemics.disposition_tasks.simulation import simulate
from epistemics.ledger import dispositions, roots
from epistemics.ledger.build import passport

SOURCE = Path(__file__).resolve().parents[1] / "src"
ORDER = list(range(23, -1, -1))


def make_root(tmp_path, runs):
    """A frozen-root layout from synthetic collections: plan, collections and executions."""
    root = tmp_path / "disposition-test"
    plan = {"phase": "test", "created_at": "2026-09-28T00:00:00+00:00", "runs": []}
    for run_id, config, kwargs in runs:
        simulate(root / "collections" / run_id, **kwargs)
        usage = {"input_tokens": 1000, "cached_input_tokens": 900, "output_tokens": 10}
        tools = [{"tool": "submit_answer", "status": "completed", "error": None}] * 24
        (root / "collections" / run_id / "execution.json").write_text(
            json.dumps({"status": "completed", "usage": usage, "tools": tools})
        )
        plan["runs"].append({"run_id": run_id, "configuration": config, "repeat": 1})
    (root / "plan.json").write_text(json.dumps(plan))
    return root


def test_facts_and_verified_extraction_from_frozen_layout(tmp_path):
    truth = {"disposition": 0.5, "gamma": 1.0, "bias": 0.0, "report_sd": 0.001}
    cues = {"slots": [0.05, 0.4, 0.5, 0.6, 0.95], "gamma": 1.0, "bias": 0.0, "report_sd": 0.05}
    root = make_root(
        tmp_path,
        [
            (
                "astra-t2",
                "astra",
                dict(module="corroboration", cover="markets", order=ORDER, truth=truth, seed=1),
            ),
            (
                "sol-cues",
                "sol",
                dict(
                    module="corroboration-cues",
                    cover="markets",
                    order=ORDER,
                    truth=cues,
                    seed=2,
                    variant="cues-a",
                ),
            ),
        ],
    )
    facts = roots.facts(root)
    assert facts["status"] == "running"  # No root execution.json yet.
    assert facts["runs_completed"] == 2 and facts["usage"]["input_tokens"] == 2000
    records = dispositions.extract(root, source=SOURCE)
    assert all(r["verified"] for r in records)
    t2, cue = (dispositions.summary(r) for r in records)
    assert t2["disposition"]["mean"] == pytest.approx(0.5, abs=0.05)
    assert t2["exact_indifference"] >= 22
    assert np.allclose(cue["implied"], cues["slots"], atol=0.06)
    assert cue["designed_order_spearman"] == pytest.approx(1.0)
    (root / "collections" / "astra-t2" / "report.json").write_text("{}")
    tampered = dispositions.extract(root, source=SOURCE)
    assert not tampered[0]["verified"] and tampered[1]["verified"]


def test_retest_contrast_and_passport_tables():
    def pair(config, module, variant, implied):
        record = {"configuration": config, "verified": True}
        return record, {"module": module, "variant": variant, "implied": implied}

    first = [pair("sol", "disclosure-cues", "cues-a", [0.2, 0.1, 0.5, 0.7, 0.7])]
    second = [pair("sol", "disclosure-cues", "cues-a", [0.1, 0.1, 0.5, 0.7, 0.8])]
    rows = dispositions.retest(first, second)
    assert rows[0]["mean_absolute_difference"] == pytest.approx(0.04)
    assert dispositions.spearman(range(5), [0.5] * 5) is None
    ranges = [
        pair(
            "astra", "corroboration-range", "range-reassuring", [0.6, 0.6, 0.5, 0.7, 0.7, 0, 0, 0]
        ),
        pair(
            "astra", "corroboration-range", "range-suggestive", [0.4, 0.4, 0.5, 0.5, 0.5, 1, 1, 1]
        ),
    ]
    contrast = dispositions.range_contrast(ranges)
    assert contrast["astra"]["mean"] == pytest.approx(0.16)
    table = passport(first + second + ranges, rows, contrast)
    assert table["sol"]["description_retest_difference"]["mean"] == pytest.approx(0.04)
    assert table["astra"]["relative_judgement_contrast"] == pytest.approx(0.16)
    assert table["sol"]["disclosure_description_mapping"]["cues-a"][0] == pytest.approx(0.15)


def test_variance_estimator_separates_shared_shifts_from_level_noise():
    from epistemics.ledger import variance

    rng = np.random.default_rng(3)
    means = np.array([0.4, 0.5, 0.6])
    shifts = rng.normal(0, 0.1, 40)
    y = means + shifts[:, None] + rng.normal(0, 0.02, (40, 3))
    s = np.full_like(y, 0.015)
    result = variance.estimate(y, s)
    assert result["session_shift_sd"]["estimate"] == pytest.approx(0.1, abs=0.03)
    assert result["level_specific_sd"]["estimate"] < 0.04
    low, high = result["total_sd"]["interval_95"]
    assert low <= np.hypot(0.1, 0.02) <= high
    flat = variance.estimate(np.tile(means, (6, 1)), np.full((6, 3), 0.015))
    assert flat["total_sd"]["estimate"] == 0
    with pytest.raises(ValueError, match="three sessions"):
        variance.estimate(y[:2], s[:2])
    assert variance.standard_errors([[0.5, 0.5], [0.3, 0.63]])[1] == pytest.approx(0.1, abs=1e-3)
