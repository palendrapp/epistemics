import random
from collections import Counter

import numpy as np
import pytest

from epistemics.disposition_tasks import runner, validation
from epistemics.disposition_tasks.render import COHERE_MODULES, render
from epistemics.dispositions import cohere, screen


@pytest.mark.parametrize("module", COHERE_MODULES)
def test_sets_share_a_case_and_obey_their_laws_under_the_observer(module):
    _, family, form = module.split("-")
    items = cohere.design(family, form)
    assert Counter(items["kind"].tolist()) == {"member": 20, "anchor": 4}
    predicted = cohere.predict(family, items, screen.observer_mid(family))
    for _, idx, _, _, law in cohere.sets(items):
        cases = [render(module, "markets", i, "cohere") for i in idx]
        assert len({c["case"] for c in cases}) == 1 and len({c["question"] for c in cases}) == len(
            idx
        )
        assert all("%" not in c["case"] for c in cases)
        p = predicted[idx]
        # The observer is a probability model, so every law holds exactly under it.
        if law in ("partition", "complement"):
            assert p.sum() == pytest.approx(1, abs=0.02)
        elif law == "disjunction":
            assert p[0] + p[1] == pytest.approx(p[2], abs=1e-6)
        elif law == "identity":
            assert p[0] + p[1] - p[2] - p[3] == pytest.approx(0, abs=0.02)
        else:
            assert p[0] <= p[1] + 1e-9
    openness = cohere.openness(family, form)
    fixed = (items["computable"] == 1) & (items["kind"] == "member")
    assert np.max(openness[fixed]) <= screen.FIXED_OPENNESS


def test_sets_order_keeps_members_apart_with_either_generator():
    items = cohere.design("lists", "d")
    for rng in (random.Random(5), np.random.default_rng(5)):
        order = cohere.sets_order(items, rng)
        assert sorted(order) == list(range(24))
        position = {item: k for k, item in enumerate(order)}
        for _, idx, _, _, _ in cohere.sets(items):
            assert min(abs(position[a] - position[b]) for a in idx for b in idx if a != b) >= 4
    groups = [
        {
            "configurations": ["astra"],
            "modules": ["cohere-num-d"],
            "contexts": [("cohere", "markets", 1)],
        }
    ]
    with pytest.raises(ValueError, match="sets"):
        runner.check_groups(groups)
    assert len(runner.check_groups([{**groups[0], "order": "sets"}])) == 1
    assert len(runner.check_groups(runner.PRESETS["cohere-a"])) == 24
    assert sorted(runner.arrange("cohere-trend-e", "sets", random.Random(2))) == list(range(24))


def test_sampler_partitions_sum_to_one_plus_k_minus_two_times_d():
    """With little report noise, a k-part partition's answers sum to about 1 + (k - 2) d."""
    rng = np.random.default_rng(3)
    items = cohere.design("trend", "d")
    truth = {"params": screen.observer_mid("trend"), "d": 0.1, "tau": 0.02}
    excess = {}
    for _ in range(20):
        for s in cohere.descriptives(items, cohere.respond("trend", items, truth, rng)):
            if s["law"] == "partition" and not s["computable"]:
                excess.setdefault(s["members"], []).append(s["residual"])
    for k, values in excess.items():
        assert np.mean(values) == pytest.approx((k - 2) * 0.1, abs=0.04)


def test_fit_recovers_shrinkage_and_does_not_invent_it():
    rng = np.random.default_rng(8)
    items = cohere.design("num", "e")
    shrunk = cohere.respond(
        "num", items, {"params": screen.observer_mid("num"), "d": 0.12, "tau": 0.1}, rng
    )
    fitted = cohere.fit(items, shrunk, ("open",))["d"]
    assert fitted["mean"] == pytest.approx(0.12, abs=0.05) and fitted["interval_90"][0] > 0
    coherent = cohere.respond(
        "num", items, {"params": screen.observer_mid("num"), "d": 0.0, "tau": 0.1}, rng
    )
    assert cohere.fit(items, coherent, ("open",))["d"]["interval_90"][0] <= 1e-9


def test_simulated_session_through_the_service(tmp_path):
    from epistemics.disposition_tasks.simulation import simulate

    items = cohere.design("lists", "e")
    truth = {"params": screen.observer_mid("lists"), "d": 0.08, "tau": 0.05}
    report = simulate(
        tmp_path / "cohere",
        module="cohere-lists-e",
        cover="markets",
        order=cohere.sets_order(items, random.Random(4)),
        truth=truth,
        seed=6,
        variant="cohere",
    )
    error, ok = validation.estimate("cohere-lists-e", report.analysis, truth)
    assert ok and report.analysis["cohere"]["anchors_ok"]
    assert runner.headline(report.analysis)["parameter"] == "cohere-lists"
