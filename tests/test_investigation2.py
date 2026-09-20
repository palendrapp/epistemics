import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest

from epistemics.investigation2.battery import public_trial
from epistemics.investigation2.design import opportunity, schedule
from epistemics.investigation2.inference import (
    FEATURES,
    best_query,
    expectations,
    initial,
    posterior,
    query_values,
    trajectory,
    values_from_expectations,
)
from epistemics.investigation2.models import Assignment, Manifest, Report, Trial
from epistemics.investigation2.service import InvestigationService, create, digest, export, load
from epistemics.investigation2.simulation import response
from epistemics.investigation2.world import EVENTS, TARGET, C, S, generate

PARTICIPANT = {"kind": "human", "subject_id": "private:test-human"}


def trials(seed=23, offset=6, branch="operations_check"):
    a = Assignment(assignment_id="test", seed=seed, family="review", offset=offset)
    w = generate(seed, offset)
    return [public_trial(a, w, i, branch if i >= 2 else None) for i in range(4)]


def finish(service):
    while not (current := service.get_trial())["complete"]:
        t = Trial.model_validate(current["trial"])
        service.submit(t.trial_id, response(t))
    return service.finish()


def test_balanced_offsets_and_matched_decision_relevant_price_pairs():
    assignments = schedule(219)
    assert sorted(a.offset for a in assignments if a.family == "review") == [-6, -6, 0, 0, 6, 6]
    for query in EVENTS:
        pair = {a.price_condition: a for a in assignments if a.focused_query == query}
        low, high = pair["low"], pair["high"]
        assert low.seed == high.seed and low.pair_id == high.pair_id
        world = generate(low.seed, 0)
        cheap = public_trial(low, world, 1)
        expensive = public_trial(high, world, 1)
        assert cheap.documents == expensive.documents
        assert cheap.source_archive == expensive.source_archive
        assert best_query(query_values(cheap)) == query
        assert best_query(query_values(expensive)) == "stop"
        assert opportunity(cheap, query)
        assert set(cheap.expectation_queries) == set(EVENTS)
        changed = copy.deepcopy(world)
        changed["truth"] = {}
        changed["queries"] = {q: not v for q, v in world["queries"].items()}
        assert opportunity(public_trial(low, changed, 1), query)


@pytest.mark.parametrize("branch", list(EVENTS))
def test_joint_query_probabilities_obey_total_probability(branch):
    ts = trials(branch=branch)
    before = posterior(ts[1])
    p = float(before @ EVENTS[branch])
    future = [posterior(ts[2].model_copy(update={"query_result": v})) for v in (False, True)]
    assert (1 - p) * future[0] + p * future[1] == pytest.approx(before, abs=1e-12)
    e = expectations(ts[1])[branch]
    assert e["yes_probability"] * e["growth_if_yes"] + (1 - e["yes_probability"]) * e[
        "growth_if_no"
    ] == pytest.approx(float(before @ TARGET), abs=1e-12)
    assert abs(query_values(ts[1])[branch]["mixture_minus_current_pp"]) < 1e-8


def test_modular_source_preserves_direct_learning_but_cuts_company_feedback():
    ts = trials(branch="operations_check")
    base = initial(ts[0])
    for t in ts[1:]:
        cut = posterior(t, coupling=0, start=base)
        assert np.bincount(S, weights=cut) == pytest.approx(np.bincount(S, weights=base), abs=1e-12)
    audited = trials(branch="source_audit")[2]
    likelihood = EVENTS["source_audit"] if audited.query_result else 1 - EVENTS["source_audit"]
    expected = base * likelihood
    expected /= expected.sum()
    assert np.bincount(S, weights=posterior(audited, coupling=0, start=base)) == pytest.approx(
        np.bincount(S, weights=expected), abs=1e-12
    )


@pytest.mark.parametrize("offset", [-6, 0, 6])
def test_correction_replaces_measurement_and_preserves_independent_result(offset):
    ts = trials(offset=offset)
    after = posterior(ts[3])
    assert after[C != offset].sum() == 0
    shifted = ts[3].model_copy(
        update={
            "reported_growth_pct": ts[3].reported_growth_pct - offset,
            "correction_offset_pct": 0.0,
        }
    )
    # Offset is independent uniform: conditioning any known offset and shifting
    # the same datum must yield the same substantive event marginals.
    assert after @ FEATURES == pytest.approx(posterior(shifted) @ FEATURES, abs=1e-12)
    for coupling in (0, 0.5, 1):
        p = trajectory(ts, coupling=coupling, response_rate=0.4)
        assert p[2, 2] == p[3, 2] == float(ts[2].query_result)
    stale = trajectory(ts, unretracted=True)
    assert stale[3] == pytest.approx(stale[2])


def test_start_projection_matches_feasible_reports_and_flags_support_limits():
    t = trials()[0]
    p = [0.65, 0.45, 0.4]
    q = initial(t, p)
    assert q @ FEATURES == pytest.approx(p, abs=1e-9)
    for unsupported in ([0, 0, 0], [1, 1, 1]):
        q = initial(t, unsupported)
        assert np.isfinite(q).all() and q.sum() == pytest.approx(1)
        for coupling in (0, 0.5, 1):
            assert np.isfinite(posterior(trials()[1], start=q, coupling=coupling)).all()


def test_future_state_is_not_exposed_and_unselected_results_do_not_change_predictions():
    a = Assignment(assignment_id="a", seed=23, family="review", offset=6)
    world = generate(23, 6)
    changed = copy.deepcopy(world)
    changed["correction_offset_pct"] = -6
    changed["truth"] = {}
    changed["queries"]["segment_check"] = not world["queries"]["segment_check"]
    for i in range(3):
        q = "operations_check" if i == 2 else None
        assert public_trial(a, world, i, q) == public_trial(a, changed, i, q)


def test_subjective_research_arithmetic_keeps_incoherence_visible():
    t = trials()[1]
    e = {q: {"yes_probability": 0.5, "growth_if_yes": 0.9, "growth_if_no": 0.1} for q in EVENTS}
    v = values_from_expectations(t, 0.5, e)
    assert v["source_audit"]["gross_value"] == pytest.approx(0.4)
    assert v["source_audit"]["mixture_minus_current_pp"] == pytest.approx(0)
    incoherent = values_from_expectations(t, 0.9, e)
    assert incoherent["source_audit"]["mixture_minus_current_pp"] == pytest.approx(-40)
    assert incoherent["source_audit"]["gross_value"] < 0  # no silent repair/clipping


def test_shared_service_rounding_expectations_idempotence_resume_and_private_export(tmp_path):
    directory = tmp_path / "study"
    manifest = create(directory, PARTICIPANT, seed=219)
    a = next(a for a in manifest.assignments if a.family == "research")
    service = InvestigationService(directory, a.assignment_id)
    t = Trial.model_validate(service.get_trial()["trial"])
    answer = response(t)
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(lambda _: service.submit(t.trial_id, answer), range(2)))
    assert receipts[0] == receipts[1]
    with pytest.raises(ValueError, match="cannot be changed"):
        service.submit(t.trial_id, answer.model_copy(update={"growth_probability": 0.99}))
    service = InvestigationService(directory, a.assignment_id)
    t = Trial.model_validate(service.get_trial()["trial"])
    answer = response(t)
    with pytest.raises(ValueError, match="research expectations"):
        service.submit(t.trial_id, answer.model_copy(update={"expectations": None}))
    invalid = answer.model_dump()
    invalid["expectations"]["source_audit"]["growth_if_yes"] = 0.123
    with pytest.raises(ValueError, match="increments"):
        service.submit(t.trial_id, invalid)
    service.submit(t.trial_id, answer)
    assert service.get_trial()["trial"]["selected_query"] == answer.query
    finish(service)
    assert service.finish() == service.finish()
    with pytest.raises(ValueError, match="All planned"):
        export(directory)
    for assignment in manifest.assignments:
        finish(InvestigationService(directory, assignment.assignment_id))
    hashes = export(directory)
    assert hashes == export(directory)
    for name, expected in hashes.items():
        raw = (directory / "reports" / name).read_bytes()
        assert digest(raw) == expected
        assert Report.model_validate_json(raw).manifest.response_origin == "human"
    assert json.loads((directory / "analysis.json").read_bytes())["source_report_hashes"] == hashes
    visible = json.dumps([service.describe(), service.get_history(), service.finish()])
    for key in ('"seed"', '"truth"', '"focused_query"', '"pair_id"', '"private_world"'):
        assert key not in visible
    assert (directory.stat().st_mode & 0o777) == 0o700
    assert ((directory / "responses.sqlite3").stat().st_mode & 0o777) == 0o600
    (directory / "manifest.json").write_bytes((directory / "manifest.json").read_bytes() + b" ")
    with pytest.raises(ValueError, match="bytes changed"):
        load(directory)


def test_v2_schema_contracts_are_current():
    for model, name in (
        (Manifest, "investigation.v2.json"),
        (Report, "investigation-report.v2.json"),
        (Trial, "investigation-trial.v2.json"),
    ):
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        assert json.loads((Path("schemas") / name).read_text()) == schema


def test_small_conditional_parameter_and_model_recovery():
    from epistemics.investigation2.simulation import validation

    result = validation(worlds=12, repetitions=2)
    assert result["passed"], result["checks"]
    assert any(r["generating_coupling"] == 0.75 for r in result["parameter_runs"])
