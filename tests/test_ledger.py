import json
from pathlib import Path

import numpy as np
import pytest

from epistemics.disposition_tasks.simulation import simulate
from epistemics.ledger import dispositions, models, roots
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


def test_transfer_scores_own_pooled_and_neutral_priors():
    from epistemics.dispositions import design, observers
    from epistemics.dispositions.response import sigmoid
    from epistemics.ledger import transfer

    items = design.corroboration_cues()

    def record(config, module, variant, priors, noise=0.0):
        responses = sigmoid(observers.cue_observer(observers.corroboration, items, priors, 1.0))
        slot_fits = [
            {"slot": s, "implied": {"mean": p, "interval_90": [p, p]}, "stated": [p]}
            for s, p in enumerate(priors)
        ]
        return {
            "verified": True,
            "configuration": config,
            "module": module,
            "variant": variant,
            "order_policy": "random",
            "responses": list(np.round(responses + noise, 2)),
            "slot_fits": slot_fits,
        }

    astra = [0.05, 0.5, 0.5, 0.5, 0.95]
    sol = [0.05, 0.3, 0.4, 0.6, 0.9]
    records = [
        record("astra", "corroboration-cues", "cues-a", astra),
        record("sol", "corroboration-cues", "cues-a", sol),
        record("astra", "corroboration-dossier", "dossier-a", astra),
        record("sol", "corroboration-dossier", "dossier-a", sol),
    ]
    result = transfer.analyse(records)
    for config in ("astra", "sol"):
        row = result[f"{config}/relay"]
        assert row["mapping_mae"] == pytest.approx(0, abs=1e-9)
        assert row["prediction_mae"]["own_formal"] < 0.006
        assert row["gain_over_neutral"] > 0.03
        assert row["gain_over_pooled"] > 0


def test_model_views_reproduce_recorded_fits_and_bracket_the_data(tmp_path):
    report = {"disposition": 0.3, "gamma": 0.9, "bias": 0.1, "report_sd": 0.3}
    cues = {"slots": [0.1, 0.35, 0.5, 0.7, 0.9], "gamma": 1.0, "bias": 0.0, "report_sd": 0.2}
    check = {"function": "linear", "certainty_value": 20.0, "decision_weight": 1.0, "wtp_sd": 3.0}
    root = make_root(
        tmp_path,
        [
            (
                "t2",
                "astra",
                dict(module="corroboration", cover="markets", order=ORDER, truth=report, seed=3),
            ),
            (
                "t3",
                "astra",
                dict(module="disclosure", cover="markets", order=ORDER, truth=report, seed=4),
            ),
            ("t5", "sol", dict(module="checks", cover="markets", order=ORDER, truth=check, seed=5)),
            (
                "cues",
                "sol",
                dict(
                    module="disclosure-cues",
                    cover="markets",
                    order=ORDER,
                    truth=cues,
                    seed=6,
                    variant="cues-a",
                ),
            ),
        ],
    )
    records = dispositions.extract(root, source=SOURCE)
    designs = models.Designs()
    sessions = [models.session({**r, "root": root.name}, "test", designs) for r in records]
    for s in sessions:
        # The recomputed grid posterior is the fit the verified report recorded.
        assert s["recorded_difference"] < 1e-6
        for weights in s["posterior"].values():
            assert sum(weights) == pytest.approx(1.0, abs=1e-4)
        q = np.array(s["ppc"]["quantiles"])
        assert q.shape == (24, 5) and np.all(np.diff(q, axis=1) >= 0)
        assert s["ppc"]["inside_90"] >= 18
    assert len(sessions[3]["slots"]) == 5
    assert np.allclose(sessions[3]["slot_means"], cues["slots"], atol=0.15)
    assert {d["family"] for d in designs.table} == {"relay", "disclosure", "checks"}
    relay = next(d for d in designs.table if d["family"] == "relay")
    assert len(relay["labels"]) == 24 and len(relay["reference"]) == 3
    assert set(relay["groups"]) == {"single", "conflict", "agree", "probe"}


def test_noticing_compares_unprompted_with_prompted_dossiers(tmp_path):
    from epistemics.ledger import transfer

    prompted = {
        "slots": [0.05, 0.45, 0.5, 0.55, 0.95],
        "gamma": 1.0,
        "bias": 0.0,
        "report_sd": 0.05,
    }
    unprompted = {"slots": [0.0, 0.0, 0.0, 0.3, 0.8], "gamma": 1.0, "bias": 0.0, "report_sd": 0.05}
    root = make_root(
        tmp_path,
        [
            (
                f"astra-{module}",
                "astra",
                dict(
                    module=module,
                    cover="markets",
                    order=ORDER,
                    truth=truth,
                    seed=seed,
                    variant="dossier-a",
                ),
            )
            for seed, (module, truth) in enumerate(
                [("corroboration-dossier", prompted), ("corroboration-unprompted", unprompted)]
            )
        ]
        + [
            (
                "astra-probed",
                "astra",
                dict(
                    module="corroboration-probed",
                    cover="markets",
                    order=ORDER,
                    truth=prompted,
                    seed=13,
                    variant="named-a",
                ),
            ),
            (
                "astra-asked",
                "astra",
                dict(
                    module="corroboration-asked",
                    cover="markets",
                    order=ORDER,
                    truth=prompted,
                    seed=10,
                    variant="named-a",
                ),
            ),
            (
                "astra-named",
                "astra",
                dict(
                    module="corroboration-unprompted",
                    cover="markets",
                    order=ORDER,
                    truth=prompted,
                    seed=9,
                    variant="named-a",
                ),
            ),
        ],
    )
    records = dispositions.extract(root, source=SOURCE)
    summaries = {r["run_id"]: dispositions.summary(r) for r in records}
    unprompted_summary = summaries["astra-corroboration-unprompted"]
    assert unprompted_summary["stated"] is None
    assert unprompted_summary["stated_minus_implied_max"] is None
    row = transfer.noticing(records)["astra/relay"]
    assert row["unprompted_sessions"] == 1 and row["prompted_sessions"] == 1
    assert row["unprompted_range"] == pytest.approx(0.8, abs=0.1)
    assert row["unprompted_irrelevant"] < 0.1 and row["prompted_irrelevant"] == pytest.approx(
        0.5, abs=0.06
    )
    asked = row["asked"]
    assert asked["sessions"] == 1 and asked["coherent_sessions"] == 1
    assert asked["irrelevant"] == pytest.approx(0.5, abs=0.08) and asked["to_prompted_mae"] < 0.1
    assert asked["prediction_mae"]["prompted"] < asked["prediction_mae"]["neglect"]
    probed = row["probed"]
    assert probed["sessions"] == 1 and "asked" in probed["prediction_mae"]
    session = probed["per_session"][0]
    assert np.allclose(session["probe_implied"], prompted["slots"], atol=0.08)
    assert np.allclose(session["forecast_only"], prompted["slots"], atol=0.15)
    # Named sessions are reported apart from the unprompted ones.
    assert row["unprompted_sessions"] == 1 and row["named"]["sessions"] == 1
    assert row["named"]["to_prompted_mae"] < 0.1 and row["named"]["irrelevant"] > 0.4
    assert row["named"]["prediction_mae"]["prompted"] < row["named"]["prediction_mae"]["unprompted"]
    errors = row["prediction_mae"]
    assert errors["neglect"] < errors["indifference"] and errors["neglect"] < errors["prompted"]
    # Unprompted sessions do not enter the formal-to-dossier transfer.
    assert transfer.analyse(records) == {}


def test_reading_guide_turns_the_passport_into_scoped_readings():
    from epistemics.ledger import guide, models

    exact = {
        "relay_default": {"mean": 0.5, "contexts": 4},
        "silence_default": {"mean": 0.5, "contexts": 4},
        "evidence_sensitivity": {"mean": 1.0, "contexts": 16},
        "report_noise_median": 0.05,
        "checks_priced_at_decision_value": [72, 72],
        "relay_description_mapping": {"cues-a": [0.05, 0.49, 0.49, 0.47, 0.93]},
        "relay_description_sessions": {"cues-a": 12},
        "ambiguous_description_session_sd": {
            "estimate": 0.09,
            "interval_95": [0.07, 0.14],
            "sessions": 8,
        },
        "description_coherence": [18, 18],
        "contexts": 47,
    }
    noisy = {
        "evidence_sensitivity": {"mean": 0.8, "contexts": 2},
        "report_noise_median": 0.4,
        "ambiguous_description_session_sd": {
            "estimate": 0.01,
            "interval_95": [0.0, 0.16],
            "sessions": 3,
        },
        "description_coherence": [1, 6],
        "contexts": 9,
    }
    analyses = {
        "noticing": {
            "exact/relay": {
                "unprompted_mapping": [0.0, 0.02, 0.03, 0.05, 0.08],
                "unprompted_sessions": 3,
            }
        }
    }
    result = guide.guide(
        {"passport": {"exact": exact, "noisy": noisy}, "analyses": analyses}, models.descriptors()
    )
    exact_readings = {r["key"]: r for r in result["configurations"]["exact"]["readings"]}
    assert exact_readings["defaults"]["claim"].endswith("treats it as 50/50.")
    assert exact_readings["descriptions-relay"]["fact"]["value"] == "5% → 93%"
    assert "treats every report as independent" in exact_readings["noticing-relay"]["claim"]
    assert exact_readings["precision"]["fact"]["value"] == "±1 point"
    assert exact_readings["coherence"]["caution"] is None
    noisy_readings = {r["key"]: r for r in result["configurations"]["noisy"]["readings"]}
    assert "counts as about 75%" in noisy_readings["reliability"]["claim"]
    assert noisy_readings["precision"]["fact"]["value"] == "±10 points"
    assert "not yet pinned down" in noisy_readings["sessions"]["claim"]
    assert (
        noisy_readings["coherence"]["caution"]
        and noisy_readings["coherence"]["strength"] == "several sessions"
    )
    assert (
        "how fast it learns base rates from experience"
        in result["configurations"]["noisy"]["not_yet_measured"]
    )


def test_reading_guide_flags_a_coherence_gap_confined_to_one_condition():
    from epistemics.ledger import guide

    p = {
        "description_coherence": [25, 30],
        "description_coherence_by_condition": {
            "corroboration-cues/cues-a": [11, 12, 0],
            "corroboration-asked/named-a": [1, 6, 2],
            "disclosure-asked/named-a": [3, 3, 0],
        },
    }
    r = guide.coherence(p)
    assert r["caution"] and "ask for its rate" in r["claim"]
    assert "2 of 6" in r["claim"] and "2 of 6" in r["detail"]
    p["description_coherence_by_condition"]["corroboration-asked/named-a"] = [1, 6, 1]
    assert guide.coherence(p)["caution"] is None
    del p["description_coherence_by_condition"]["corroboration-asked/named-a"]
    assert guide.coherence(p)["caution"] is None
