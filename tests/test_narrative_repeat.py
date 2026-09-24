import pytest

from epistemics.narrative.battery import public_trial
from epistemics.narrative.service import digest, encoded
from epistemics.narrative.simulation import simulate
from epistemics.narrative_repeat import compare


def test_repeat_distances_and_exact_byte_bindings(tmp_path):
    first = simulate(tmp_path / "first", 31)
    repeat = simulate(tmp_path / "repeat", 31)
    first_bytes, repeat_bytes = encoded(first), encoded(repeat)
    result = compare(first_bytes, repeat_bytes)
    assert result["first_report_sha256"] == digest(first_bytes)
    assert result["repeat_report_sha256"] == digest(repeat_bytes)
    assert all(row["maximum"] == 0 for row in result["repeat_distances"].values())
    assert result["research_choice_agreement"] == {"matched": 8, "total": 8}
    a = repeat.manifest.assignments[0]
    data = repeat.model_dump(mode="json")
    joint = data["cases"][a.assignment_id][0]["answer"]["joint"]
    joint["demand_only"] += 0.05
    joint["artifact_only"] -= 0.05
    # Comparison recomputes facts from accepted rows, not the stored analysis dict.
    data["analysis"] = {"untrusted_summary": "all unchanged"}
    result = compare(first_bytes, encoded(data))
    assert result["repeat_distances"]["initial_joint_tv_pp"]["maximum"] == pytest.approx(5)
    assert result["repeat_distances"]["initial_joint_tv_pp"]["mean"] == pytest.approx(5 / 8)


def test_research_branch_changes_are_incomparable_and_protocol_changes_rejected(tmp_path):
    first = simulate(tmp_path / "first", 31)
    a = first.manifest.assignments[0]
    data = first.model_dump(mode="json")
    data["cases"][a.assignment_id][1]["answer"]["query"] = "stop"
    for i in (2, 3):
        data["cases"][a.assignment_id][i]["trial"] = public_trial(a, i, "stop").model_dump(
            mode="json"
        )
    result = compare(encoded(first), encoded(data))
    assert result["repeat_distances"]["post_audit_joint_tv_pp"]["incomparable"] == 1
    assert result["repeat_distances"]["initial_joint_tv_pp"]["count"] == 8
    assert result["research_choice_agreement"]["matched"] == 7
    data["manifest"]["implementation_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="implementation_sha256"):
        compare(encoded(first), encoded(data))
