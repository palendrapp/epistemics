import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from epistemics.investigation.inference import forecasts
from epistemics.investigation.models import InvestigationAnswer, InvestigationReport
from epistemics.investigation.service import InvestigationService, create, digest, export, load

PARTICIPANT = {"kind": "human", "subject_id": "private:test-participant"}


def response(trial, query="source_audit"):
    p, audit, backlog = [round(float(x), 2) for x in forecasts(trial)]
    return InvestigationAnswer(
        growth_probability=p,
        audit_understatement_probability=audit,
        backlog_high_probability=backlog,
        decision="invest" if (trial.gain + trial.loss) * p > trial.loss else "hold",
        query=query if trial.index == 1 else None,
    )


def finish(service, query="source_audit"):
    while not (current := service.get_trial())["complete"]:
        from epistemics.investigation.models import InvestigationTrial

        trial = InvestigationTrial.model_validate(current["trial"])
        service.submit(trial.trial_id, response(trial, query))
    return service.finish()


def test_collection_retry_resume_branch_privacy_and_immutable_export(tmp_path):
    directory = tmp_path / "study"
    manifest = create(directory, PARTICIPANT, episodes=2, seed=18)
    assignment = manifest.assignments[0]
    service = InvestigationService(directory, assignment.assignment_id)
    with pytest.raises(ValueError, match="every checkpoint"):
        service.finish()
    from epistemics.investigation.models import InvestigationTrial

    t = InvestigationTrial.model_validate(service.get_trial()["trial"])
    a = response(t)
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(lambda _: service.submit(t.trial_id, a), range(2)))
    assert receipts[0] == receipts[1]
    with pytest.raises(ValueError, match="cannot be changed"):
        service.submit(t.trial_id, a.model_copy(update={"growth_probability": 0.99}))
    with pytest.raises(ValueError, match="current trial"):
        service.submit("future:3", a)
    resumed = InvestigationService(directory, assignment.assignment_id)
    assert len(resumed.get_history()["history"]) == 1
    t1 = InvestigationTrial.model_validate(resumed.get_trial()["trial"])
    with pytest.raises(ValueError, match="research option"):
        resumed.submit(t1.trial_id, response(t1).model_copy(update={"query": None}))
    with pytest.raises(ValueError, match="increments"):
        resumed.submit(t1.trial_id, response(t1).model_copy(update={"growth_probability": 0.123}))
    receipt = resumed.submit(t1.trial_id, response(t1, "operations_check"))
    assert resumed.submit(t1.trial_id, response(t1, "operations_check")) == receipt
    assert resumed.get_trial()["trial"]["selected_query"] == "operations_check"
    finish(resumed)
    assert resumed.finish() == resumed.finish()
    exposed = json.dumps([resumed.get_history(), resumed.finish(), resumed.describe()])
    for field in ('"seed"', '"truth"', '"queries"', '"realized_growth_pct"', '"source_bias"'):
        assert field not in exposed
    with pytest.raises(ValueError, match="All planned"):
        export(directory)
    finish(InvestigationService(directory, manifest.assignments[1].assignment_id))
    hashes = export(directory)
    assert hashes == export(directory)
    for name, sha in hashes.items():
        data = (directory / "reports" / name).read_bytes()
        assert digest(data) == sha
        report = InvestigationReport.model_validate_json(data)
        assert report.manifest.response_origin == "human"
    assert "Response origin: **human**" in (directory / "summary.md").read_text()
    assert (directory.stat().st_mode & 0o777) == 0o700
    assert ((directory / "responses.sqlite3").stat().st_mode & 0o777) == 0o600
    with pytest.raises(FileExistsError):
        create(directory, PARTICIPANT, episodes=2)
    (directory / "manifest.json").write_bytes((directory / "manifest.json").read_bytes() + b" ")
    with pytest.raises(ValueError, match="bytes changed"):
        load(directory)
    with pytest.raises(ValueError, match="bytes changed"):
        resumed.get_trial()
