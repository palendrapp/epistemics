import re
from collections import Counter

import numpy as np
import pytest

from epistemics.disposition_tasks import surfaces, validation
from epistemics.disposition_tasks.presentation import Answer
from epistemics.disposition_tasks.render import render, stated_percentages
from epistemics.dispositions import coherence, decisions
from epistemics.ledger import battery_v31


def test_designs_ask_each_scenario_twice_and_classes_span_the_beliefs():
    for index, letter in enumerate(decisions.DESIGNS):
        items = decisions.design(letter)
        assert Counter(items["kind"].tolist()) == {"stated": 10, "decision": 10, "anchor": 4}
        stated = np.flatnonzero(items["kind"] == "stated")
        decided = np.flatnonzero(items["kind"] == "decision")
        assert items["scenario"][stated].tolist() == items["scenario"][decided].tolist()
        counts = Counter(items["cls"][decided].tolist())
        assert sorted(counts.values()) == [3, 3, 4] and counts[index % 3] == 4
        # Every class has beliefs on both sides of the middle, ranked by ideal belief.
        rows = [{k: items[k][i] for k in items} for i in stated]
        means = coherence.ideal_range(rows)[1]
        for k in range(3):
            chosen = means[items["cls"][stated] == k]
            assert chosen.min() < 0 < chosen.max()
        anchors = np.flatnonzero(items["kind"] == "anchor")
        assert sorted(items["anchor_p"][anchors].round(2).tolist()) == [0.15, 0.35, 0.65, 0.85]
        assert set(items["cls"][anchors].tolist()) == {1}
        ideals = coherence.ideal([{k: items[k][i] for k in items} for i in anchors])
        assert np.allclose(1 / (1 + np.exp(-ideals)), items["anchor_p"][anchors])


def test_decision_texts_state_no_numbers_and_options_do_not_presuppose_the_answer():
    for domain in range(len(coherence.DOMAINS)):
        for text in surfaces.CONSEQUENCES[domain]:
            assert not re.search(r"\d", text)
        assert not re.search(r"\d", surfaces.STAKES_TASKS[domain])
        for option in surfaces.ACTIONS[domain]:
            assert not any(word in option.lower() for word in validation.VERDICTS)
    for letter in decisions.DESIGNS:
        module = f"decision-{letter}"
        items = decisions.design(letter)
        for i in range(24):
            trial = render(module, "markets", i, "v31-standard")
            assert set(re.findall(r"\d+%", trial["case"])) == set(
                stated_percentages(module, i, "v31-standard")
            )
            if items["kind"][i] == "stated":
                assert (
                    trial["response"] == "probability" and "Your own assigned" not in trial["case"]
                )
                continue
            assert trial["response"] == "choice" and len(trial["options"]) == 2
            assert validation.v31_consequences_clean(trial)
            shown, act = surfaces.options(items, i)
            assert trial["options"] == shown and act == 1 - int(items["act_first"][i])
            assert ("Your own assigned task" in trial["case"]) == bool(items["stakes"][i])


def test_choice_answers_must_copy_one_of_the_options():
    trial = {"response": "choice", "options": ["Release the batch", "Hold the batch"]}
    Answer(choice="Hold the batch").validate_trial(trial)
    with pytest.raises(ValueError, match="listed options"):
        Answer(choice="hold the batch").validate_trial(trial)
    with pytest.raises(ValueError, match="asks for choice"):
        Answer(probability=0.4).validate_trial(trial)
    with pytest.raises(ValueError, match="exactly one"):
        Answer(probability=0.4, choice="Hold the batch")


def test_threshold_fit_recovers_ordered_thresholds_from_pooled_sessions():
    truth = {
        "thresholds": [-1.0, 0.25, 1.25],
        "kappa": 6.0,
        "stakes": 0.0,
        "stated_sd": 0.05,
        "default_acc": 0.7,
        "default_rate": 0.4,
    }
    rows = battery_v31.simulate_config(truth, np.random.default_rng(5), 0.0)
    assert len(rows) == 14 * len(decisions.DESIGNS)
    fit = decisions.fit_thresholds(rows)
    assert fit["theta_balanced"]["mean"] == pytest.approx(0.25, abs=0.35)
    assert fit["sensitivity"]["mean"] == pytest.approx(2.25, abs=0.8)
    assert fit["theta_cheap"]["mean"] < fit["theta_balanced"]["mean"] < fit["theta_costly"]["mean"]
    lo, hi = fit["sensitivity"]["interval_90"]
    assert lo <= 2.25 <= hi


def test_factorised_fit_matches_the_joint_grid():
    rng = np.random.default_rng(0)
    rows = []
    for i in range(45):
        s = rng.uniform(-2.5, 2.5)
        p = decisions._phi(np.array(3 * (s - (i % 3 - 1))))
        rows.append(
            {"stated": s, "act": int(rng.random() < p), "cls": i % 3, "stakes": 0, "stakes_dir": 0}
        )
    fit = decisions.fit_thresholds(rows)
    s = np.array([r["stated"] for r in rows])
    act = np.array([r["act"] for r in rows])
    cls = np.array([r["cls"] for r in rows])
    per = []
    for k in range(3):
        z = decisions.KAPPA[None, :, None] * (s[cls == k] - decisions.THETA[:, None, None])
        p = decisions.LAPSE / 2 + (1 - decisions.LAPSE) * decisions._phi(z)
        per.append(np.where(act[cls == k] == 1, np.log(p), np.log1p(-p)).sum(-1))
    total = per[0][:, None, None, :] + per[1][None, :, None, :] + per[2][None, None, :, :]
    post = np.exp(total - total.max())
    post /= post.sum()
    assert fit["theta_cheap"]["mean"] == pytest.approx(post.sum((1, 2, 3)) @ decisions.THETA)
    assert fit["kappa"]["mean"] == pytest.approx(post.sum((0, 1, 2)) @ decisions.KAPPA)
    diff = (decisions.THETA[None, :] - decisions.THETA[:, None]).ravel()
    assert fit["sensitivity"]["mean"] == pytest.approx(post.sum((1, 3)).ravel() @ diff)


def test_stakes_shift_is_recovered_in_the_favoured_direction():
    truth = {
        "thresholds": [-1.0, 0.0, 1.0],
        "kappa": 8.0,
        "stakes": 1.5,
        "stated_sd": 0.05,
        "default_acc": 0.7,
        "default_rate": 0.4,
    }
    rng = np.random.default_rng(11)
    rows = []
    for _ in range(4):
        rows += battery_v31.simulate_config(truth, rng, 0.0)
    fit = decisions.fit_thresholds(rows, stakes=True)
    assert fit["stakes_shift"]["mean"] > 0.5 and fit["stakes_decisions"] == 48


def test_analysis_and_headline_read_choices_as_act_or_hold(tmp_path):
    from epistemics.disposition_tasks.runner import headline
    from epistemics.disposition_tasks.simulation import simulate

    report = simulate(
        tmp_path / "decision",
        module="decision-b",
        cover="markets",
        order=list(np.random.default_rng(2).permutation(24)),
        truth=validation.V31_RESPONDENT,
        seed=4,
        variant="v31-standard",
    )
    rows = report.analysis["decisions"]["trials"]
    assert len(rows) == 14 and sum(r["anchor"] for r in rows) == 4
    anchors = {round(1 / (1 + np.exp(-r["stated"])), 2): r["act"] for r in rows if r["anchor"]}
    assert anchors == {0.15: 0, 0.35: 0, 0.65: 1, 0.85: 1}  # threshold 0, kappa 8
    assert headline(report.analysis)["parameter"] == "thresholds"
