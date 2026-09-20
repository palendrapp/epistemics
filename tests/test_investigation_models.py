import copy

import numpy as np
import pytest

from epistemics.discovery import world as old
from epistemics.investigation.battery import public_trial
from epistemics.investigation.inference import (
    best_query,
    posterior,
    query_values,
    report_log_likelihood,
    trajectory,
)
from epistemics.investigation.models import Assignment
from epistemics.investigation.world import EVENTS, TARGET, A, F, K, generate


def trials(seed=21, branch="source_audit"):
    assignment = Assignment(assignment_id="test", seed=seed)
    world = generate(seed)
    return [public_trial(assignment, world, i, branch if i >= 2 else None) for i in range(4)]


def test_projection_matches_existing_full_joint_enumerator():
    t = trials(branch="stop")[3]
    w = posterior(t)
    # Independently sum the old 6,912-state model, with irrelevant sources and
    # provenance marginalized. Conditioning the known offset reduces to its
    # original source/auxiliary model, using Morrow as the recurring source.
    q = np.zeros(len(old.STATES))
    for row in t.source_archive:
        q += old.log_measurement(row.reported_pct - row.audited_pct, old.BIAS[:, 1], old.SD[:, 1])
    for row in t.analogues:
        q += old.log_measurement(
            row.renewal_growth_pct,
            row.underlying_growth_pct - np.where(old.K == 1, 8, 2) * row.rollout_disruption,
            3,
        )
    q += old.log_measurement(
        t.reported_growth_pct - t.correction_offset_pct, old.RENEWAL + old.BIAS[:, 1], old.SD[:, 1]
    )
    q = old.normalize(q)
    for small, original in (
        (F, old.F),
        (A, old.A),
        (K, old.K),
        (TARGET, old.cdf((old.F - 12) / 2)),
    ):
        assert w @ small == pytest.approx(q @ original, abs=1e-12)


@pytest.mark.parametrize("branch", ["source_audit", "operations_check", "segment_check"])
def test_query_tower_property_and_value_match_enumerated_branches(branch):
    ts = trials(branch=branch)
    before = posterior(ts[1])
    marginal = float(before @ EVENTS[branch])
    posteriors = [
        posterior(ts[2].model_copy(update={"query_result": event})) for event in (False, True)
    ]
    assert (1 - marginal) * posteriors[0] + marginal * posteriors[1] == pytest.approx(before)

    def utility(q):
        return max(0, (ts[1].gain + ts[1].loss) * float(q @ TARGET) - ts[1].loss)

    value = (
        (1 - marginal) * utility(posteriors[0])
        + marginal * utility(posteriors[1])
        - utility(before)
    )
    assert query_values(ts[1])[branch]["gross_value"] == pytest.approx(value, abs=1e-12)


def test_calculation_has_no_new_evidence_and_expensive_research_stops():
    ts = trials(branch="calculation")
    assert posterior(ts[1]) == pytest.approx(posterior(ts[2]))
    values = query_values(ts[1])
    assert values["calculation"]["gross_value"] == 0
    expensive = ts[1].model_copy(deep=True)
    for option in expensive.options:
        if option.query != "stop":
            option.cost = 1000.0
    assert best_query(expensive) == "stop"
    assert query_values(expensive)["stop"]["net_value"] == 0


def test_queries_have_distinct_consequences_and_corrections_preserve_checks():
    trajectories = [trajectory(trials(seed=8, branch=q)) for q in EVENTS]
    assert any(np.max(np.abs(a - b)) > 0.05 for a in trajectories for b in trajectories)
    for branch, channel in (("source_audit", 1), ("operations_check", 2)):
        ts = trials(seed=8, branch=branch)
        p = trajectory(ts)
        assert p[2, channel] == p[3, channel] == float(ts[2].query_result)
        assert (
            "Purchased independent checks and archives are unaffected"
            in ts[3].documents[-1]["text"]
        )
    ts = trials(seed=8, branch="stop")
    stale = trajectory(ts, model="no_retraction")
    assert stale[3] == pytest.approx(stale[2])


def test_hidden_branches_and_future_corrections_cannot_change_public_trial():
    assignment = Assignment(assignment_id="test", seed=8)
    world = generate(8)
    mutated = copy.deepcopy(world)
    mutated["truth"]["fundamentals"] = 999
    mutated["correction_offset_pct"] = 999
    mutated["queries"]["segment_check"] = not world["queries"]["segment_check"]
    for i in range(3):
        query = "source_audit" if i == 2 else None
        assert public_trial(assignment, world, i, query) == public_trial(
            assignment, mutated, i, query
        )
    assert public_trial(assignment, world, 0).reference_assumptions is None
    calibration = assignment.model_copy(update={"mode": "calibration"})
    assert public_trial(calibration, world, 0).reference_assumptions is not None


@pytest.mark.parametrize("p", [0, 0.01, 0.5, 0.99, 1])
def test_rounded_report_likelihood_is_normalized_including_endpoints(p):
    mass = np.exp(report_log_likelihood(np.arange(101) / 100, p))
    assert np.isfinite(mass).all()
    assert mass.sum() == pytest.approx(1.0, abs=1e-12)


def test_small_synthetic_model_and_off_grid_parameter_recovery():
    from epistemics.investigation.simulation import validation

    result = validation(worlds=8, repetitions=3)
    assert result["response_origin"] == "synthetic"
    assert result["passed"], result["checks"]
    matched = result["matched_forecast_attribution_check"]
    assert matched["matched_worlds"] + matched["unmatched_worlds"] == 8
    assert matched["max_matched_growth_gap_pp"] < 1e-6
    assert matched["auxiliary_probe_recovery_rate"] >= 0.8
    assert any(
        abs(row["generating_archive_weight"] * 20 - round(row["generating_archive_weight"] * 20))
        > 1e-5
        for row in result["parameter_runs"]
    )
