import re
from collections import Counter

import numpy as np
import pytest

from epistemics.disposition_tasks import runner
from epistemics.disposition_tasks.render import render, stated_percentages
from epistemics.dispositions import coherence


def test_designs_cover_every_surface_twice_at_two_strengths():
    seen = {}
    for letter in coherence.DESIGNS:
        items = coherence.design(letter)
        assert Counter(items["kind"].tolist()) == {"stated": 10, "revealed": 10, "lottery": 4}
        stated = items["kind"] == "stated"
        assert items["strength"][stated].tolist() == list(coherence.STRENGTHS)
        assert items["stakes"][stated].tolist() == [0] * 6 + [1, 1, 0, 0]
        for i in np.flatnonzero(stated):
            key = (int(items["domain"][i]), int(items["source"][i]))
            seen.setdefault(key, []).append((letter, int(items["strength"][i])))
    assert len(seen) == len(coherence.SURFACES)
    for appearances in seen.values():
        assert len(appearances) == 2
        assert appearances[0][0] != appearances[1][0] and appearances[0][1] != appearances[1][1]


def test_strength_grades_how_much_unstated_properties_matter_and_balance_holds():
    spans = {0: [], 1: [], 2: []}
    for row in coherence._battery().values():
        low, _, high = (v[0] for v in coherence.ideal_range([row]))
        spans[row["strength"]].append(high - low)
        for k in range(coherence.WIDTH):
            source = row[f"src_{k}"]
            if source >= 0 and not row[f"rate_stated_{k}"]:
                assert row[f"rep_{k}"] == row[f"rep_{source}"]
    assert (
        max(spans[0]) < 1e-9 and min(spans[1]) > 0.1 and np.median(spans[2]) > np.median(spans[1])
    )
    for against, towards in coherence.balance().values():
        assert abs(against - towards) <= max(2, 0.15 * (against + towards))


def test_texts_show_exactly_the_stated_numbers_and_loaded_trials_refer_back():
    for letter in coherence.DESIGNS:
        module = f"coherence-{letter}"
        items = coherence.design(letter)
        for i in range(24):
            for variant in ("v3-standard", "v3-loaded"):
                trial = render(module, "markets", i, variant)
                shown = set(re.findall(r"\d+%", trial["case"]))
                assert shown == set(stated_percentages(module, i, variant))
                assert trial["response"] == items["response"][i]
            loaded = render(module, "markets", i, "v3-loaded")["case"]
            assert "Unrelated system log" in loaded
            if items["kind"][i] == "revealed":
                assert "Evidence" not in loaded and "Earlier in this session" in loaded


def test_calibration_and_coherence_fits_recover_a_known_respondent():
    items = coherence.design("a")
    rho, alpha, beta = 0.7, 0.3, 0.8
    reports = np.zeros(24)
    stated = {}
    for i in np.flatnonzero(items["kind"] == "stated"):
        s = float(np.clip(1 / (1 + np.exp(-(i / 5 - 2))), 0.05, 0.95))
        reports[i] = round(s, 2)
        stated[int(items["scenario"][i])] = np.log(reports[i] / (1 - reports[i]))
    for i in np.flatnonzero(items["kind"] == "revealed"):
        p = 1 / (1 + np.exp(-(alpha + beta * stated[int(items["scenario"][i])])))
        reports[i] = round(float(coherence.certainty_equivalent(p, rho)))
    for i in np.flatnonzero(items["kind"] == "lottery"):
        reports[i] = round(float(coherence.certainty_equivalent(items["lottery_p"][i], rho)))
    fit = coherence.fit_coherence(items, reports)
    assert fit["calibration"]["rho"]["mean"] == pytest.approx(rho, abs=0.06)
    assert fit["beta"] == pytest.approx(beta, abs=0.1) and fit["alpha"] == pytest.approx(
        alpha, abs=0.15
    )


def test_loaded_order_puts_each_revealed_trial_6_to_12_after_its_stated_trial():
    rng = np.random.default_rng(3)
    items = coherence.design("c")
    for _ in range(20):
        order = runner.refer_back_order("coherence-c", rng)
        assert sorted(order) == list(range(24))
        position = {item: k for k, item in enumerate(order)}
        for s in range(10):
            a = int(np.flatnonzero((items["kind"] == "stated") & (items["scenario"] == s))[0])
            b = int(np.flatnonzero((items["kind"] == "revealed") & (items["scenario"] == s))[0])
            assert 6 <= position[b] - position[a] <= 12
    group = {"configurations": ["astra"], "modules": ["coherence-c"]}
    with pytest.raises(ValueError, match="refer-back"):
        runner.check_groups([{**group, "contexts": [("v3-loaded", "markets", 1)]}])
    with pytest.raises(ValueError, match="refer-back"):
        runner.check_groups(
            [{**group, "contexts": [("v3-standard", "markets", 1)], "order": "refer-back"}]
        )
