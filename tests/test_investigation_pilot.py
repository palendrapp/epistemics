import json

import numpy as np
import pytest

from epistemics.investigation.inference import simulate_reports
from epistemics.investigation3 import inference as model
from epistemics.investigation3.models import Trial
from epistemics.investigation3.service import InvestigationService, create, digest, fingerprint
from epistemics.investigation3.simulation import cases, response, synthetic
from epistemics.investigation_pilot.prediction import (
    bound_json,
    commit,
    components,
    ensure_prediction,
    pilot_fingerprint,
    reference_distribution,
)


def test_component_predictions_match_frozen_observer():
    obs = synthetic(cases(219)[0], np.random.default_rng(1))
    for initialization in model.INITIALIZATIONS:
        for coupling, rate in [(0.0, 1.0), (0.5, 0.7), (1.0, 0.2)]:
            c, w = components(
                [o.trial for o in obs],
                model.answer_vector(obs[0].answer),
                {"initialization": initialization, "coupling": coupling, "response_rate": rate},
            )
            expected = model.predictions([obs], coupling, rate, initialization=initialization)
            assert w @ c == pytest.approx(expected, abs=1e-12)


def setup(root):
    manifest = create(
        root / "repeat", {"kind": "human", "subject_id": "private:test"}, seed=219, synthetic=True
    )
    mh = digest((root / "repeat/manifest.json").read_bytes())
    ph = commit(
        root / "run-manifest.json",
        {
            "pilot_sha256": pilot_fingerprint(),
            "implementation_sha256": fingerprint(),
            "manifests": {"repeat": mh},
        },
    )
    commit(
        root / "locked-models.json",
        {
            "plan_sha256": ph,
            "specifications": {
                "fixed_joint": {
                    "initialization": "working_prior",
                    "coupling": 1.0,
                    "response_rate": 1.0,
                }
            },
        },
    )
    return InvestigationService(root / "repeat", manifest.assignments[0].assignment_id)


def test_forecast_commitment_is_idempotent_and_detects_late_creation(tmp_path):
    service = setup(tmp_path)
    t = Trial.model_validate(service.get_trial()["trial"])
    answer = response(t)
    receipt = service.submit(t.trial_id, answer)
    ensure_prediction(tmp_path, "repeat", service)
    p = next((tmp_path / "predictions").glob("*.json"))
    before = p.read_bytes()
    assert service.submit(t.trial_id, answer) == receipt
    ensure_prediction(tmp_path, "repeat", service)
    assert p.read_bytes() == before
    saved, _ = bound_json(p)
    assert set(saved["branches"]) == {
        "source_audit",
        "operations_check",
        "segment_check",
        "calculation",
        "stop",
    }
    t = Trial.model_validate(service.get_trial()["trial"])
    service.submit(t.trial_id, response(t))
    ensure_prediction(tmp_path, "repeat", service)
    p.unlink()
    p.with_suffix(".sha256").unlink()
    with pytest.raises(ValueError, match="after later answers"):
        ensure_prediction(tmp_path, "repeat", service)


def test_predictive_reference_has_expected_coverage_under_its_own_generator():
    values = np.array([[0.1, 0.3, 0.8], [0.5, 0.6, 0.2]])
    weights = np.array([0.4, 0.6])
    reference = reference_distribution(values, weights, 17)
    rng = np.random.default_rng(29)
    new = simulate_reports(values[rng.choice(2, size=2000, p=weights)], rng)
    rmse = np.sqrt(np.mean((new - weights @ values) ** 2, axis=1)) * 100
    ll = model.marginal_log_likelihood(new[:, None, :], values[None, :, :], weights)
    for measured, field in [(rmse, "rmse_pp"), (ll, "log_score")]:
        lo, hi = np.quantile(reference[field], [0.025, 0.975])
        assert 0.91 < np.mean((measured >= lo) & (measured <= hi)) < 0.99


def test_committed_file_bytes_are_not_silently_rewritten(tmp_path):
    p = tmp_path / "frozen.json"
    commit(p, {"value": 1})
    with pytest.raises(FileExistsError):
        commit(p, {"value": 2})
    p.write_text(json.dumps({"value": 2}))
    with pytest.raises(ValueError, match="changed"):
        bound_json(p)
