import json
from fractions import Fraction as F
from math import comb

import numpy as np
import pytest

from epistemics.source_learning.battery import knowledge
from epistemics.source_learning.models import Answer
from epistemics.source_learning.simulation import memory_manifest
from epistemics.source_learning.storage import encoded, save
from epistemics.source_selective.policy import POLICIES
from epistemics.source_value_audit.core import (
    REPORTERS,
    PublicCase,
    expected_outcome,
    oracle_probability,
    public_probability,
    realized_outcome,
    sample_posterior,
)
from epistemics.source_value_audit.experiment import (
    calibration,
    make_plan,
    public_case,
    run,
    seed_for,
    simulate_world,
)


def rational_expectation(q, p, t, price, policy):
    """Independent exact arithmetic, including purchase assignment and every H/k."""
    q, p, t, price = map(lambda x: F(str(x)), (q, p, t, price))
    masses = [
        [comb(5, k) * r**k * (1 - r) ** (5 - k) for k in range(6)] for r in (F(3, 10), F(7, 10))
    ]
    subjective_after = sum(
        max(0, p * masses[1][k] * (1 - t) - (1 - p) * masses[0][k] * t) for k in range(6)
    )
    buy = policy == "always" or (
        policy == "cost_aware" and subjective_after - max(0, p - t) - price > F(1, 10**12)
    )
    value = F(0)
    for h in (0, 1):
        for k in range(6):
            invest = p * masses[1][k] * (1 - t) > (1 - p) * masses[0][k] * t if buy else p > t
            value += (q if h else 1 - q) * masses[h][k] * ((h - t) * invest - price * buy)
    return float(value), int(buy)


@pytest.mark.parametrize("policy", POLICIES)
def test_expectation_matches_independent_rational_enumeration(policy):
    for q in (0.01, 0.23, 0.5, 0.79, 0.99):
        for p in (0.0, 0.13, 0.33, 0.71, 1.0):
            for threshold in (0.3, 0.7):
                for price in (0.01, 0.04, 0.2):
                    exact, buy = rational_expectation(q, p, threshold, price, policy)
                    result = expected_outcome(q, p, threshold, price, policy)
                    assert result["expected_net"] == pytest.approx(exact, abs=1e-14)
                    assert result["buy"] == buy
                    assert result["purchase_regret"] >= -1e-14
                    assert result["action_regret"] >= -1e-14
                    assert result["total_regret"] == pytest.approx(
                        result["purchase_regret"] + result["action_regret"], abs=1e-14
                    )


def test_expected_value_is_not_realized_value():
    expected = expected_outcome(0.2, 0.2, 0.3, 0.01, "cost_aware")
    unlucky = realized_outcome(0.2, 0.3, 0.01, "cost_aware", strong=False, count=5)
    assert expected["buy"] == 1
    assert expected["expected_gain_over_none"] > 0
    assert expected["total_regret"] == pytest.approx(0, abs=1e-14)
    assert unlucky["realized_gain_over_none"] == pytest.approx(-0.31)


def test_expected_contrast_matches_independent_monte_carlo():
    rng = np.random.default_rng(93621)
    q, p, t, price = 0.42, 0.55, 0.7, 0.01
    expected = expected_outcome(q, p, t, price, "cost_aware")
    assert expected["buy"]
    h = rng.random(100000) < q
    k = rng.binomial(5, np.where(h, 0.7, 0.3))
    odds = (p / (1 - p)) * (7 / 3) ** (2.0 * k - 5)
    changed = (odds > t / (1 - t)).astype(float) - (p > t)
    delta = (h - t) * changed - price
    assert (
        abs(delta.mean() - expected["expected_gain_over_none"])
        < 5 * delta.std() / len(delta) ** 0.5
    )


def test_public_boundary_and_history_timing():
    manifest = memory_manifest(723)
    company = manifest.companies[15]
    original = public_case(manifest, 15, 0.04)
    changed_record = company.record.model_copy(
        update={
            "public": company.record.public.model_copy(
                update={"resolved_strong": not company.record.public.resolved_strong}
            )
        }
    )
    changed_company = company.model_copy(
        update={
            "record": changed_record,
            "independent_panel": company.independent_panel.model_copy(
                update={"count": (company.independent_panel.count + 1) % 6}
            ),
        }
    )
    changed = manifest.model_copy(
        update={"companies": manifest.companies[:15] + [changed_company] + manifest.companies[16:]}
    )
    assert public_case(changed, 15, 0.04) == original
    assert public_probability(public_case(changed, 15, 0.04)) == public_probability(original)
    q = oracle_probability(original.probe, company.record.source)
    assert q == oracle_probability(
        public_case(changed, 15, 0.04).probe, changed_company.record.source
    )
    # At company 16 provisional, 15 earlier companies, not this one, have resolved.
    answers = [
        Answer(
            probability=0.5, decision="decline", query="stop" if i >= 12 and i % 2 == 0 else None
        )
        for i in range(18)
    ]
    history, _, _ = knowledge(manifest, 18, answers)
    assert original.history == history
    assert len(original.history) == 72 + 15
    # Independent evidence adds no process information after the state is disclosed.
    checked = [a.model_copy(update={"query": "customer_panel"}) if a.query else a for a in answers]
    assert knowledge(manifest, 18, checked)[0] == original.history


def test_oracle_is_optimal_and_distortions_have_measurable_cost():
    gaps = {r.name: [] for r in REPORTERS}
    for q in np.linspace(0.01, 0.99, 99):
        for reporter in REPORTERS:
            result = expected_outcome(
                float(q), reporter.report(float(q), float(q)), 0.3, 0.04, "cost_aware"
            )
            gaps[reporter.name].append(result["total_regret"])
    assert max(gaps["oracle"]) < 1e-12
    for name in ("underconfident", "overconfident", "optimistic", "pessimistic"):
        assert np.mean(gaps[name]) > 0.003


def test_seed_channels_reproducible_distinct_and_world_prices_balanced():
    assert seed_for(3, 4, "world") == seed_for(3, 4, "world")
    assert (
        len({seed_for(b, i, c) for b in (3, 4) for i in range(10) for c in ("world", "price")})
        == 40
    )
    cases, world = simulate_world(3, 0)
    assert [sum(r["price"] == p for r in cases) for p in (0.01, 0.04, 0.2)] == [4, 4, 4]
    assert world["cells"]["oracle"]["cost_aware"]["total_regret"] < 1e-12
    assert (cases, world) == simulate_world(3, 0)
    reliabilities = calibration(cases + simulate_world(3, 1)[0])
    assert reliabilities["oracle"]["expected_binned_absolute_gap"] == 0
    assert reliabilities["oracle_rounded"]["expected_binned_absolute_gap"] <= 0.005
    for name in ("underconfident", "overconfident", "optimistic", "pessimistic"):
        assert reliabilities[name]["expected_binned_absolute_gap"] > 0.03


def test_frozen_plan_exact_bytes_idempotence_and_drift(tmp_path):
    plan = make_plan([129, 943], 2)
    save(tmp_path / "plan.json", encoded(plan))
    first = run(tmp_path)
    assert first["world_count"] == 4 and first["case_count"] == 48
    assert first["pooled"]["oracle"]["cost_aware"]["two_world_realized_losses"]["pairs"] == 2
    assert first == run(tmp_path)
    assert json.loads((tmp_path / "summary.json").read_bytes()) == first
    with pytest.raises(ValueError, match="refuse overwrite"):
        save(tmp_path / "plan.json", encoded(make_plan([129, 943], 4)))
    plan["implementation_sha256"] = "0" * 64
    (tmp_path / "plan.json").write_bytes(encoded(plan))
    with pytest.raises(ValueError, match="differs"):
        run(tmp_path)


@pytest.mark.parametrize("seeds,n", [([1], 3), ([1, 1], 2), ([True], 2), ([], 2), ([1], 8192)])
def test_invalid_plans(seeds, n):
    with pytest.raises(ValueError):
        make_plan(seeds, n)


def test_invalid_inputs_and_endpoints():
    for p, count in ((float("nan"), 2), (-0.1, 1), (0.5, 6), (0.5, True)):
        with pytest.raises(ValueError):
            sample_posterior(p, count)
    assert sample_posterior(0, 5) == 0
    assert sample_posterior(1, 0) == 1
    case = public_case(memory_manifest(10), 12, 0.01)
    with pytest.raises(ValueError):
        PublicCase(case.history, case.probe, case.threshold, float("nan"))
