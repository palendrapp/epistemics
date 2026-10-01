import random
from collections import Counter

import numpy as np
import pytest

from epistemics.disposition_tasks import runner
from epistemics.disposition_tasks.render import (
    STATEMENT_MODULES,
    STATEMENT_PROBE_MODULES,
    render,
    stated_percentages,
)
from epistemics.dispositions import statements as st

BAYESIAN = {
    "w": {"activity": 0.6, "inflation": 0.8, "risks": 0.5, "guidance": 1.0, "vote": 0.4},
    "tilt": 0.0,
    "c": 0.0,
    "gamma": 1.0,
    "eta": 0.0,
    "beta": 1.0,
    "alpha": 1.0,
    "tau": 0.05,
}


@pytest.mark.parametrize("form", st.FORMS)
def test_forms_balance_slots_directions_and_sizes(form):
    specs = st.FORM_SPECS[form]
    assert sorted(s["n"] for s in specs) == [1, 2, 3, 4, 5, 6]
    substantive = [(name, d) for s in specs for name, d in s["changes"] if name in st.SLOTS]
    assert len(substantive) == 15
    for slot in st.SLOTS:
        assert sorted(d for name, d in substantive if name == slot) in ([-1, -1, 1], [-1, 1, 1])
    assert sum(name in st.STYLES for s in specs for name, _ in s["changes"]) == 6
    assert len({s["id"] for s in specs}) == 6


@pytest.mark.parametrize("form", st.FORMS)
def test_latin_square_puts_every_sequence_in_every_condition(form):
    seen = {}
    for r in st.ROTATIONS:
        items = st.design(form, r)
        assert Counter(items["kind"].tolist()) == {"prior": 6, "step": 14, "whole": 2, "anchor": 2}
        for k, c in set(zip(items["sequence"].tolist(), items["condition"].tolist(), strict=True)):
            if k >= 0:
                seen.setdefault(k, []).append(c)
    assert all(sorted(v) == sorted(st.CONDITIONS) for v in seen.values()) and len(seen) == 6


@pytest.mark.parametrize("module", STATEMENT_MODULES)
def test_cases_show_one_change_per_step_and_the_market_prior(module):
    items = st.module_design(module)
    texts = set()
    for i in range(24):
        case = render(module, "markets", i, "statement")
        texts.add(case["case"])
        kind = str(items["kind"][i])
        shown = case["case"].count("now reads")
        assert shown == {"step": 1, "whole": int(items["n"][i])}.get(kind, 0)
        for p in stated_percentages(module, i):
            assert p in case["case"]
        if kind == "anchor":
            assert "%" not in case["case"]
    assert len(texts) == 24


def test_sequences_order_keeps_each_sequence_together_with_either_generator():
    items = st.design("b", 2)
    for rng in (random.Random(4), np.random.default_rng(4)):
        order = st.sequences_order(items, rng)
        assert sorted(order) == list(range(24))
        for k in range(6):
            spots = [p for p, i in enumerate(order) if items["sequence"][i] == k]
            if not spots:
                continue
            assert spots == list(range(spots[0], spots[0] + len(spots)))
            assert [int(items["step"][order[p]]) for p in spots] == sorted(
                int(items["step"][order[p]]) for p in spots
            )
    group = {
        "configurations": ["astra"],
        "modules": ["statement-a1"],
        "contexts": [("statement", "markets", 1)],
    }
    with pytest.raises(ValueError, match="sequences"):
        runner.check_groups([group])
    assert len(runner.check_groups([{**group, "order": "sequences"}])) == 1
    assert len(runner.check_groups(runner.PRESETS["statements-a"])) == 24
    assert len(runner.check_groups(runner.PRESETS["statements-probe-a"])) == 2


def _records(form, truth, seed):
    rng = np.random.default_rng(seed)
    records = []
    for r in st.ROTATIONS:
        items = st.design(form, r)
        records += st.sequences(items, st.respond(items, truth, rng))
    return records


def test_a_bayesian_combiner_is_recovered_and_obeys_the_laws():
    records = _records("a", BAYESIAN, 1)
    fitted = st.fit(records)
    for slot, w in BAYESIAN["w"].items():
        assert abs(fitted[f"w_{slot}"]["mean"] - w) < 0.1
    assert abs(fitted["beta"]["mean"] - 1) < 0.1 and fitted["alpha"]["mean"] > 0.9
    assert fitted["eta"]["mean"] < 0.1 and abs(fitted["gamma"]["mean"] - 1) < 0.05
    laws = st.laws(records)
    assert laws["path"] < 0.2 and laws["content"] < 0.05


def test_fading_and_averaging_show_in_the_fit_and_the_laws():
    fading = st.laws(_records("a", {**BAYESIAN, "alpha": 0.5}, 2))
    averaging = _records("a", {**BAYESIAN, "eta": 0.8}, 3)
    assert fading["recency"] > 0.2 and fading["path"] > 0.2
    assert st.fit(averaging)["eta"]["mean"] > 0.5
    # Averaging leaves the steps alone, so steps overshoot the whole-statement answer.
    assert st.laws(averaging)["overshoot"] > 0.2


@pytest.mark.parametrize("module", STATEMENT_PROBE_MODULES)
def test_probe_shares_each_statements_case_across_its_four_periods(module):
    items = st.module_design(module)
    for k in range(6):
        idx = np.flatnonzero(items["sequence"] == k)
        cases = [render(module, "markets", int(i), "statement") for i in idx]
        assert len({c["case"] for c in cases}) == 1 and len({c["question"] for c in cases}) == 4
    answers = st.respond_probe(items, {"periods": [0.1, 0.7, 0.1, 0.1]}, None)
    flagged = st.probe_session(items, answers)["flagged"]
    assert flagged == [s["id"] for s in st.FORM_SPECS[module[-1]]]
