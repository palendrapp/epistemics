import re
from collections import Counter

import numpy as np
import pytest

from epistemics.disposition_tasks import runner, validation
from epistemics.disposition_tasks.render import SCREEN_MODULES, render, stated_percentages
from epistemics.dispositions import screen
from epistemics.ledger import screen as ledger


@pytest.mark.parametrize("family", screen.FAMILIES)
def test_designs_have_twenty_open_items_four_anchors_and_matched_halves(family):
    for form in screen.FORMS:
        items = screen.design(family, form)
        assert Counter(items["kind"].tolist()) == {"open": 20, "anchor": 4}
        anchors = items["kind"] == "anchor"
        assert np.all(np.isfinite(items["answer"][anchors])) and np.all(items["c1"][anchors] == 0)
        for j in (1, 2):
            sign, half = items[f"c{j}"], items[f"h{j}"]
            for s in (1, -1):
                chosen = half[sign == s]
                # Halves alternate within each set, so their sizes differ by at most one.
                assert abs(np.sum(chosen == 0) - np.sum(chosen == 1)) <= 1
        # The two forms are parallel: same structure, different data.
        other = screen.design(family, "b" if form == "a" else "a")
        for key in ("kind", "c1", "c2", "transform"):
            assert items[key].tolist() == other[key].tolist()
        assert items["data"].tolist() != other["data"].tolist()


@pytest.mark.parametrize("family", screen.FAMILIES)
def test_open_items_are_open_and_anchors_determinate(family):
    for form in screen.FORMS:
        openness = screen.openness(family, form)
        anchors = screen.design(family, form)["kind"] == "anchor"
        assert np.median(openness[~anchors]) >= screen.OPEN_MEDIAN
        assert np.all(openness[anchors] == 0)


def test_texts_state_data_only_and_anchors_fix_their_answers():
    cases = 0
    for module in SCREEN_MODULES:
        seen = set()
        for i in range(24):
            trial = render(module, "markets", i, "screen")
            assert stated_percentages(module, i) == [] and "%" not in trial["case"]
            assert validation.screen_case_clean(module, i, trial)
            assert trial["question"].startswith(
                ("What is the probability that", "If the cause was one of the listed causes")
            )
            seen.add((trial["case"], trial["question"]))
            cases += 1
        assert len(seen) == 24
    assert cases == 24 * len(SCREEN_MODULES)
    # Examples of the families' texts.
    gen = render("screen-gen-a", "markets", 0, "screen")
    assert gen["case"].startswith("A process produced these values: 20, 30, 40.")
    assert gen["question"].endswith("could also produce 80?")
    num = render("screen-num-a", "markets", 0, "screen")
    assert re.fullmatch(r"A colleague says the transfer took 30 minutes\.", num["case"])
    assert "between 28 and 32 minutes" in num["question"]
    sharp = render("screen-num-a", "markets", 14, "screen")
    assert "31 minutes" in sharp["case"] and "between 30 and 32 minutes" in sharp["question"]
    choice = render("screen-choice-a", "markets", 0, "screen")
    assert "could have carried out a quick visual check" in choice["case"]
    assert "They did not, and signed B11 off as sound." in choice["case"]


@pytest.mark.parametrize("family", screen.FAMILIES)
def test_contrasts_are_reliable_and_move_with_their_parameters(family):
    items = screen.design(family, "a")
    rng = np.random.default_rng(4)
    for name, (names, sign) in screen.SPEC[family]["drivers"].items():
        line = [
            screen.contrast_scores(
                items, screen.predict(family, items, ledger._at(family, names, q))
            )[name]["score"]
            for q in np.linspace(0, 1, 6)
        ]
        assert np.all(np.diff(line) * sign >= -0.05)
    draws = screen.draw(family, rng, 40)
    noisy = [screen.contrast_scores(items, screen.respond(family, items, p, rng)) for p in draws]
    clean = [screen.contrast_scores(items, screen.predict(family, items, p)) for p in draws]
    for name in screen.SPEC[family]["contrasts"]:
        r = ledger._spearman([s[name]["score"] for s in noisy], [s[name]["score"] for s in clean])
        assert r >= 0.8


def test_stage_a_passes_real_differences_and_not_a_shared_policy():
    rng = np.random.default_rng(9)
    family = "choice"
    same = ledger._simulated_sessions(family, screen.draw(family, rng, 1) * 6, rng, 0.3, 0.0)
    assert not ledger.stage_a_family(family, [r for r in same if r["form"] == "a"])["passed"]
    params = [ledger._at(family, ("rationality",), q) for q in np.linspace(0, 1, 6)]
    differ = ledger._simulated_sessions(family, params, rng, 0.3, 0.0)
    result = ledger.stage_a_family(family, [r for r in differ if r["form"] == "a"])
    assert result["contrasts"]["skip_informativeness"]["passed"] and result["passed"]
    # Identical answers from every configuration: a shared rule, never a pass.
    rows = [dict(r, configuration=str(c)) for c, r in enumerate([same[0]] * 6)]
    shared = ledger.stage_a_family(family, rows)
    assert shared["shared_answer_share"] == 1.0 and not shared["passed"]


def test_icc_permutation_test_is_exact_and_centres_forms():
    rng = np.random.default_rng(3)
    stable = [[x, x + 5.0 + 0.01 * k] for k, x in enumerate((0.0, 1.0, 2.0, 3.0, 4.0, 5.0))]
    value, p = ledger.icc_test(stable, rng, 2000)
    assert value > 0.99 and p < 0.01  # a constant form difference does not dilute the ICC
    assert ledger.holm({"a": 0.01, "b": 0.04}) == {"a": 0.02, "b": 0.04}


def test_screen_preset_and_simulated_session_through_the_service(tmp_path):
    from epistemics.disposition_tasks.simulation import simulate

    runs = runner.check_groups(runner.PRESETS["screen-a"])
    assert len(runs) == 30 and {r[1] for r in runs} == {f"screen-{f}-a" for f in screen.FAMILIES}
    truth = {"params": screen.mid("lists"), "noise": 0.05}
    report = simulate(
        tmp_path / "lists",
        module="screen-lists-b",
        cover="markets",
        order=list(range(24)),
        truth=truth,
        seed=2,
        variant="screen",
    )
    error, ok = validation.estimate("screen-lists-b", report.analysis, truth)
    assert ok and report.analysis["screen"]["anchors_ok"]
    assert runner.headline(report.analysis)["parameter"] == "screen-lists"


@pytest.mark.parametrize("family", ["num", "choice", "trend"])
def test_profile_fit_recovers_separable_parameters(family):
    """The family's Bayesian observer, fitted to both forms, recovers each profile parameter and
    does not mistake it for another (ledger.screen.profile_recovery at a smaller scale)."""
    _, _, result = ledger._profile_family((family, 40, ("a", "b"), 7))
    for name, p in result.items():
        assert p["r"] >= 0.9 and p["coverage_90"] >= 0.7, (name, p)
        assert p["largest_confusion"] <= 0.4, (name, p["confusion"])


def test_num_and_trend_contrasts_track_their_own_parameters():
    rng = np.random.default_rng(11)
    for family in ("num", "trend"):
        items = screen.design(family, "a")
        draws = screen.draw(family, rng, 120)
        clean = [screen.contrast_scores(items, screen.predict(family, items, p)) for p in draws]
        for name, (names, sign) in screen.SPEC[family]["drivers"].items():
            r = ledger._spearman([d[names[0]] for d in draws], [c[name]["score"] for c in clean])
            assert sign * r >= 0.75, (family, name, r)


@pytest.mark.parametrize("family", screen.FIXED_FAMILIES)
def test_fallback_items_are_fixed_at_several_levels_and_read_like_open_items(family):
    items = screen.design(family, screen.FIXED_FORM)
    expected = {"fixed": 12, "open": 8} if family == "trend" else {"fixed": 16, "open": 4}
    assert Counter(items["kind"].tolist()) == {**expected, "anchor": 4}
    openness = screen.openness(family, screen.FIXED_FORM)
    fixed = items["kind"] == "fixed"
    assert np.max(openness[fixed]) <= screen.FIXED_OPENNESS
    levels = set(np.round(screen.predict(family, items, screen.observer_mid(family))[fixed], 1))
    assert len(levels) >= 3
    module = f"screen-{family}-c"
    for i in np.flatnonzero(fixed):
        trial = render(module, "markets", int(i), "screen")
        assert validation.screen_case_clean(module, int(i), trial)
    if family == "lists":
        trial = render(module, "markets", 2, "screen")
        assert trial["question"].startswith("If the cause was one of the listed causes")
        assert " or " in trial["question"]
    if family == "num":
        assert "more than 30 minutes" in render(module, "markets", 0, "screen")["question"]


def test_revised_fit_reads_trust_and_fallback_from_fixed_items():
    """A respondent who falls back heavily: the fit to forms a, b and c finds high trust and its
    fallback answer."""
    from epistemics.ledger import screen_fit

    rng = np.random.default_rng(2)
    truth = {**screen.observer_mid("num"), "trust": 0.6, "fallback": 0.85}
    responses = {
        f: screen_fit.respond("num", screen.design("num", f), truth, rng, 0.2)
        for f in screen.forms("num")
    }
    fitted = screen_fit.fit("num", responses, screen.forms("num"))["parameters"]
    assert fitted["trust"]["mean"] > 0.4 and abs(fitted["fallback"]["mean"] - 0.85) < 0.15
    assert (
        runner.check_groups(runner.PRESETS["screen-c"])
        and len(runner.check_groups(runner.PRESETS["screen-c"])) == 36
    )
