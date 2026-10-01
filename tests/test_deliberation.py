import random

import numpy as np
import pytest

from epistemics.disposition_tasks import runner
from epistemics.disposition_tasks.render import DELIBERATION_MODULES, render, stated_percentages
from epistemics.dispositions import deliberation as dl
from epistemics.dispositions import screen


def test_ladders_rise_in_threshold_and_fall_in_the_observers_answers():
    for s in range(len(dl.SERIES)):
        ts = dl.thresholds(s)
        assert len(ts) == 6 and all(b > a for a, b in zip(ts, ts[1:], strict=False))
        for params in (dl.BROAD, screen.observer_mid("trend")):
            p = [dl.observer(s, t, params) for t in ts]
            assert all(b < a for a, b in zip(p, p[1:], strict=False))
        broad = [dl.observer(s, t, dl.BROAD) for t in ts]
        assert np.allclose(np.diff(broad), -0.05, atol=0.012)


@pytest.mark.parametrize("module", DELIBERATION_MODULES)
def test_cases_render_with_their_anchor_and_options(module):
    items = dl.design(module)
    keys = set()
    for i in range(24):
        case = render(module, "markets", i, "deliberation")
        keys.add((case["case"], case["question"]))
        for p in stated_percentages(module, i):
            assert p in case["case"] + case["question"]
        if items["kind"][i] == "choice":
            assert case["options"] == [
                f"Above {items['anchor'][i]}%",
                f"Below {items['anchor'][i]}%",
            ]
        if module == "deliberation-ladder":
            assert "%" not in case["case"]
    assert len(keys) == 24


def test_forms_swap_every_anchor_side():
    a, b = dl.design("deliberation-anchor-a"), dl.design("deliberation-anchor-b")
    choice = a["kind"] == "choice"
    assert np.array_equal(a["threshold"][choice], b["threshold"][choice])
    assert all(x != y for x, y in zip(a["side"][choice], b["side"][choice], strict=True))
    assert sorted(a["side"][choice].tolist()).count("low") == 6


def test_orders_keep_ladders_apart_and_pairs_together():
    items = dl.design("deliberation-ladder")
    for rng in (random.Random(3), np.random.default_rng(3)):
        order = dl.ladder_order(items, rng)
        assert sorted(order) == list(range(24))
        for s in range(4):
            spots = [p for p, i in enumerate(order) if items["series"][i] == s]
            assert np.all(np.diff(spots) == 4)
    assert len(runner.check_groups(runner.PRESETS["deliberation-pilot"])) == 24
    group = {
        "configurations": ["astra"],
        "modules": ["deliberation-anchor-a"],
        "contexts": [("deliberation", "markets", 1)],
    }
    with pytest.raises(ValueError, match="sequences"):
        runner.check_groups([group])


def test_simulated_grain_and_anchoring_are_recovered():
    rng = np.random.default_rng(5)
    truth = {"params": screen.observer_mid("trend"), "rho": 1.0, "a": 0.4, "tau": 0.05}
    pairs, probability = [], []
    for module in dl.MODULES:
        items = dl.design(module)
        answers = dl.respond(items, truth, rng)
        s = dl.session(items, answers)
        pairs += s.get("pairs", [])
        probability += [
            v for v, r in zip(answers, items["response"], strict=True) if r == "probability"
        ]
        if module == "deliberation-ladder":
            assert s["violations"] == 0
        else:
            assert s["consistency"] == 1.0
    assert dl.grain(probability)["share_5"] == 1.0
    assert abs(dl.anchoring(pairs)["a"]["mean"] - 0.4) < 0.08


def test_bare_module_asks_every_anchored_threshold_directly():
    bare = dl.design(dl.BARE)
    anchor = dl.design("deliberation-anchor-a")
    asked = set(zip(bare["series"].tolist(), bare["threshold"].tolist(), strict=True))
    choice = anchor["kind"] == "choice"
    anchored = set(
        zip(anchor["series"][choice].tolist(), anchor["threshold"][choice].tolist(), strict=True)
    )
    assert len(asked) == 24 and anchored <= asked
    for i in range(24):
        case = render(dl.BARE, "markets", i, "deliberation")
        assert "%" not in case["case"] and "previous case" not in case["case"]
    assert len(runner.check_groups(runner.PRESETS["deliberation-bare"])) == 8
