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


def test_only_the_first_urn_selection_wording_is_kept_out_of_coherence():
    from epistemics.ledger import build

    assert build.confounded({"module": "selection-urn-asked", "variant": "urn-named"})
    assert build.confounded({"module": "selection-urn-probed", "variant": "urn-named"})
    assert not build.confounded({"module": "selection-urn-asked", "variant": "urn2-named"})
    assert not build.confounded({"module": "copying-urn-asked", "variant": "urn-named"})


def test_inclusion_layer_orders_thresholds_and_reports_rungs():
    from epistemics.ledger import inclusion

    rng = np.random.default_rng(3)
    low = inclusion.fit(inclusion.simulate(rng, {"theta": 0.5, "w": 0.3, "sigma": 0.3}))
    high = inclusion.fit(inclusion.simulate(rng, {"theta": 2.5, "w": 0.3, "sigma": 0.3}))
    assert low["parameters"]["theta"]["mean"] < 1.2 < 1.8 < high["parameters"]["theta"]["mean"]
    assert low["inclusion_by_rung"]["relay"]["1"] > high["inclusion_by_rung"]["relay"]["1"]
    assert set(low["mapping"]) == {"relay", "disclosure"}
    split = inclusion.fit(
        inclusion.simulate(rng, {"theta": 0.5, "w": 0.3, "sigma": 0.3}), "theta_by_family"
    )
    assert {"theta_relay", "theta_disclosure", "w", "sigma"} == set(split["parameters"])


def test_joint_inclusion_fit_samples_and_compares_stated_models():
    from epistemics.ledger import inclusion
    from epistemics.ledger import inclusion_joint as joint

    rng = np.random.default_rng(4)
    data = inclusion.simulate(
        rng, {"theta": 0.8, "w": 0.3, "sigma": 0.4}, stated=True, stated_source="applied"
    )
    fits = {
        m: joint.sample(data, "shared", m, chains=2, iterations=1500, burn=500, seed=1)
        for m in ("considered", "applied")
    }
    for f in fits.values():
        assert {"theta", "w", "sigma", "tau"} <= set(f["parameters"])
        assert set(f["mapping"]) == {"relay", "disclosure"}
        assert len(f["waic"]["elpd_pointwise"]) == 40
    diff = joint.compare(fits["applied"], fits["considered"])
    assert diff["difference"] < 0  # The generating hypothesis is preferred.
    split = joint.sample(data, "theta_by_family", "applied", chains=2, iterations=800, burn=300)
    assert {"theta_relay", "theta_disclosure"} <= set(split["parameters"])


def test_fidelity_mixture_estimates_the_share_of_coherent_sessions():
    from epistemics.ledger import inclusion
    from epistemics.ledger import inclusion_joint as joint

    rng = np.random.default_rng(6)
    truth = {"theta": 0.8, "w": 0.3, "sigma": 0.4, "phi": 0.9}
    data = inclusion.simulate(rng, truth, stated=True, stated_source="mixture")
    fit = joint.sample(data, "shared", "mixture", chains=2, iterations=2000, burn=700, seed=2)
    assert fit["parameters"]["phi"]["mean"] > 0.5
    probabilities = [p for ps in fit["session_fidelity"].values() for p in ps if p is not None]
    assert len(probabilities) >= 20 and all(0 <= p <= 1 for p in probabilities)


def test_simulate_takes_per_structure_parameters_and_counts():
    from epistemics.ledger import inclusion

    rng = np.random.default_rng(5)
    truth = {"theta_selection": -0.5, "theta_mismatch": 3.5, "w": 0.0}
    truth |= {"sigma_selection": 0.2, "sigma_mismatch": 0.2, "phi": 1.0}
    counts = {"selection": {0: 2, 3: 1}, "mismatch": {0: 2, 3: 1}}
    rows = inclusion.simulate(rng, truth, stated=True, stated_source="mixture", counts=counts)
    assert {f: len(r) for f, r in rows.items()} == {"selection": 3, "mismatch": 3}
    assert [s for s, _, _ in rows["selection"]] == [0, 0, 3]


def test_hierarchical_thresholds_order_structures_and_read_the_spread():
    from epistemics.ledger import inclusion
    from epistemics.ledger import inclusion_hier as hier

    rng = np.random.default_rng(11)
    truth = {"theta_selection": -0.5, "theta_mismatch": 2.5, "w": 0.2, "sigma": 0.3, "phi": 0.9}
    counts = {f: inclusion.URN_COUNTS[f] for f in ("selection", "mismatch")}
    rows = inclusion.simulate(rng, truth, stated=True, stated_source="mixture", counts=counts)
    result = hier.sample(rows, chains=2, iterations=1500, burn=500)
    thetas = {f: x["parameters"]["theta"]["mean"] for f, x in result["structures"].items()}
    assert thetas["selection"] < 0.5 < 1.5 < thetas["mismatch"]
    assert result["spread_reading"] in ("generalises", "structure-specific", "undetermined")
    lo, hi = result["theta_new_structure"]["interval_90"]
    assert -1 <= lo < hi <= 4
    assert result["structures"]["mismatch"]["format"] == "urn2"


def test_hierarchical_prior_bounds_and_truncated_draws():
    from epistemics.ledger import inclusion_hier as hier

    assert hier.hyper_logprior(np.array([0.0, 1.0]), 5.0, 1.0) == -np.inf
    assert hier.hyper_logprior(np.array([0.0, 1.0]), 0.5, 0.0) == -np.inf
    draws = hier.truncated_normal_draws(
        np.random.default_rng(2), np.full(500, -1.0), np.full(500, 3.0)
    )
    assert draws.min() >= -1 and draws.max() <= 4


def test_ledger_loads_the_latest_hierarchical_fit_with_its_hash(tmp_path):
    import hashlib
    import json

    from epistemics.ledger import models

    assert models.hierarchy(tmp_path) is None
    (tmp_path / "inclusion-hier-fit-20260928.json").write_text(json.dumps({"astra": {"old": 1}}))
    latest = tmp_path / "inclusion-hier-fit-20260929.json"
    latest.write_text(json.dumps({"astra": {"new": 1}}))
    (tmp_path / "inclusion-hier-sensitivity-20260929.json").write_text(json.dumps({"astra": {}}))
    loaded = models.hierarchy(tmp_path)
    assert loaded["fits"] == {"astra": {"new": 1}}
    assert loaded["sha256"] == hashlib.sha256(latest.read_bytes()).hexdigest()
    assert loaded["sensitivity"]["file"] == "inclusion-hier-sensitivity-20260929.json"


def test_reading_guide_reads_carry_over_only_from_a_valid_hierarchical_fit():
    from epistemics.ledger import guide

    fit = {
        "valid": True,
        "spread_reading": "undetermined",
        "theta_new_structure": {"mean": 0.5, "interval_90": [-0.7, 1.9]},
        "tau_theta": {"mean": 0.84, "interval_90": [0.33, 1.65]},
        "structures": {
            f: {"session_fidelity": {f: [None, 0.9, 0.8]}} for f in ("relay", "selection")
        },
    }
    r = guide.carry_over("sol", {"fits": {"sol": fit}})
    assert r["fact"] == {"label": "Noticing carries over between structures", "value": "Not shown"}
    assert "unprompted" in r["claim"] and "base rate" in r["claim"] and r["caution"]
    assert r["sessions"] == 6
    assert guide.carry_over("sol", {"fits": {"sol": {**fit, "valid": False}}}) is None
    assert guide.carry_over("astra", {"fits": {"sol": fit}}) is None
    agrees = guide.carry_over("sol", {"fits": {"sol": {**fit, "spread_reading": "generalises"}}})
    assert agrees["caution"] is None and agrees["fact"]["value"] == "Yes"


def test_reading_guide_turns_structure_checks_into_prompting_advice():
    from epistemics.ledger import guide
    from epistemics.structure_check import CATALOGUE

    def check(rung, means, valid=True, key="mismatch"):
        return {
            "format": CATALOGUE[key]["format"],
            "valid": valid,
            "recommended_rung": rung,
            "sessions": 11,
            "inclusion_by_rung": {str(r): {"mean": m} for r, m in enumerate(means)},
        }

    checks = {
        "checks": {
            "sol": {
                "mismatch": check(2, (0.06, 0.6, 0.97, 0.99)),
                "selection": check(0, (0.9, 1.0, 1.0, 1.0), key="selection"),
                "copying": check(1, (0.4, 0.95, 1.0, 1.0), valid=False, key="copying"),
                "relay": {**check(2, (0.1, 0.5, 0.9, 1.0), key="relay"), "format": "older"},
            }
        }
    }
    readings = {r["key"]: r for r in guide.structure_checks("sol", checks)}
    assert set(readings) == {"check-mismatch", "check-selection"}  # relay: older wording
    mismatch = readings["check-mismatch"]
    assert mismatch["topic"] == "structures" and mismatch["caution"]
    assert "about 6% of cases" in mismatch["claim"] and "ask how common it is" in mismatch["claim"]
    assert mismatch["fact"]["value"] == "Mention it and ask how common it is"
    assert readings["check-selection"]["caution"] is None
    CATALOGUE["mismatch"]["known_issue"] = "The wording was ambiguous."
    try:
        flagged = guide.structure_checks("sol", checks)[0]
    finally:
        del CATALOGUE["mismatch"]["known_issue"]
    assert "Known issue" in flagged["detail"] and "ambiguous" in flagged["caution"]
    assert guide.structure_checks("astra", checks) == []
    high = guide.structure_checks(
        "sol", {"checks": {"sol": {"copying": check(1, (0.9, 1, 1, 1), key="copying")}}}
    )
    assert "about 90% of cases, but not reliably" in high[0]["claim"]
    assert high[0]["caution"].startswith("Sometimes misses")
    assert guide.undetermined_checks("sol", checks) == [
        "whether it considers sources repeating another source unprompted (not yet checked)",
        "whether it considers selective silence unprompted (not yet checked)",
        "whether it considers copied readings unprompted (its check did not converge)",
    ]
    assert guide.undetermined_checks("astra", checks) == []


def test_structure_check_collections_count_as_disposition_runs():
    from epistemics.ledger import build

    assert build.is_disposition("output/disposition-abstract2-20260929")
    assert build.is_disposition("output/structure-check-mismatch3-20260929")
    assert not build.is_disposition("output/research-world3-acceptance")


def test_reading_guide_advises_stating_the_rate_when_prompting_is_not_enough():
    from epistemics.ledger import guide

    base = {
        "format": "urn3",
        "valid": True,
        "recommended_rung": None,
        "sessions": 6,
        "inclusion_by_rung": {str(r): {"mean": m} for r, m in enumerate((0.1, 0.5, 0.8, 0.9))},
    }
    followed = {"followed": 2, "sessions": 2, "reliable": True}
    r = guide.structure_checks(
        "sol", {"checks": {"sol": {"mismatch": {**base, "advice": "rate", "rated": followed}}}}
    )[0]
    assert r["fact"]["value"] == "State how common it is"
    assert "when told how common it is" in r["claim"] and "2 of 2 sessions" in r["claim"]
    ignored = {"followed": 0, "sessions": 2, "reliable": False}
    r = guide.structure_checks(
        "sol", {"checks": {"sol": {"mismatch": {**base, "advice": None, "rated": ignored}}}}
    )[0]
    assert r["fact"]["value"] == "Not reliable" and "did not fix this" in r["claim"]
    assert "followed the stated rates in 0 of 2 sessions" in r["detail"]
