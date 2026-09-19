import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from epistemics.baselines import answer_trial
from epistemics.models import AgentDescriptor, Answer, Report, Trial
from epistemics.service import EvaluationService


@pytest.fixture
def agent():
    return AgentDescriptor(
        agent_id="test", model="fixture", model_version="v1", configuration_sha256="0" * 64
    )


def test_session_boundary_retry_resume_and_export(tmp_path, agent):
    db = tmp_path / "sessions.sqlite3"
    service = EvaluationService(db)
    session = service.start(agent, seed=42)
    session_id = session["session_id"]
    with pytest.raises(ValueError, match="Complete every"):
        service.finish(session_id)
    assert "seed" not in session
    first = service.get_trial(session_id)
    assert first == service.get_trial(session_id)
    assert not any(
        word in json.dumps(first) for word in ['"truth"', '"reference"', '"regime"', '"seed"']
    )
    with pytest.raises(ValueError, match="current trial"):
        service.submit(session_id, "t001", Answer(probability=0.5))
    receipt = service.submit(session_id, "t000", Answer(probability=0.5))
    assert "outcome" not in receipt
    assert receipt == service.submit(session_id, "t000", Answer(probability=0.5))
    with pytest.raises(ValueError, match="cannot be changed"):
        service.submit(session_id, "t000", Answer(probability=0.6))
    service = EvaluationService(db)
    assert service.get_trial(session_id)["answered"] == 1
    while not (current := service.get_trial(session_id))["complete"]:
        trial = Trial.model_validate(current["trial"])
        answer = answer_trial(trial)
        if trial.task == "source_reliability":
            with pytest.raises(ValueError, match="source_probability"):
                service.submit(session_id, trial.trial_id, Answer(probability=0.5))
        service.submit(session_id, trial.trial_id, answer)
    report = service.finish(session_id)
    assert len(report.observations) == 88
    assert report == service.finish(session_id)
    assert report.seed == 42
    assert receipt == service.submit(session_id, "t000", Answer(probability=0.5))
    with pytest.raises(ValueError, match="Unknown session"):
        service.get_trial("unknown")


def test_concurrent_retries_accept_only_one_answer(tmp_path, agent):
    service = EvaluationService(tmp_path / "sessions.sqlite3")
    session_id = service.start(agent)["session_id"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = list(
            pool.map(
                lambda _: service.submit(session_id, "t000", Answer(probability=0.7)), range(8)
            )
        )
    assert all(r == receipts[0] for r in receipts)
    assert service.get_trial(session_id)["answered"] == 1


def test_schema_is_current():
    expected = Report.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert json.loads(Path("schemas/report.v1.json").read_text()) == expected
