import numpy as np

from epistemics.disposition_tasks import render, runner, urn
from epistemics.disposition_tasks.render import items_for
from epistemics.dispositions import design, fit, observers
from epistemics.dispositions.response import sample_reports


def test_long_load_designs_have_four_levels_balanced_misfiling_and_typical_repeats():
    for module, model, readings in (
        ("copying-long-load", "dependence", (2, 4, 8, 16)),
        ("mismatch-long-load", "mismatch", (1, 3, 6, 12)),
    ):
        items = items_for(module)
        assert np.bincount(items["load"]).tolist() == [6, 6, 6, 6]
        assert [int(items["n"][items["load"] == k][0]) for k in range(4)] == list(readings)
        exact, neglect = observers.load_answers(model, items)
        assert np.all(np.abs(exact - neglect) >= 0.25) and np.all(np.abs(exact) <= 2.95)
        separation = np.abs(exact - neglect)
        repeats = [(i, int(j)) for i, j in enumerate(items["repeat_of"]) if j >= 0]
        assert len(repeats) == 4
        for i, j in repeats:
            assert exact[i] == exact[j]
            level = items["load"] == items["load"][j]
            originals = separation[level & (items["repeat_of"] < 0)]
            assert separation[j] == np.sort(originals)[len(originals) // 2]
        top = int(np.flatnonzero(items["load"] == 3)[0])
        case = render.render(module, "markets", top, "load-a")["case"]
        for p in render.stated_percentages(module, top):
            assert p in case
        if model == "mismatch":
            for i in range(len(exact)):
                n = int(items["n"][i])
                gaps = design.misfiling_gaps(
                    [items[f"acc_{k}"][i] for k in range(n)],
                    [items[f"mis_{k}"][i] for k in range(n)],
                )
                assert gaps.max() <= design.MISFILING_GAP
                assert design.MISFILING_BAND[0] <= gaps.mean() <= design.MISFILING_BAND[1]


def test_pilot_load_designs_are_unchanged():
    items = items_for("mismatch-load")
    assert np.bincount(items["load"]).tolist() == [8, 8, 8]
    assert int(items["repeat_of"][22]) == 7


def test_ideal_audit_rate_rises_with_the_likelihood_ratio_and_skips_the_anchors():
    for module in ("copying-urn", "selection-urn", "mismatch-urn"):
        items = items_for(module)
        ideal = urn.vig_ideals(module, "urn2-vig2", items)
        assert np.all(ideal[items["slot"] < 0] == 0)
        by_level = [ideal[(items["slot"] == s) & (ideal > 0)].mean() for s in range(5)]
        assert all(a < b for a, b in zip(by_level, by_level[1:], strict=False))
        assert 0 < by_level[0] < 0.06
    top = urn.vig_ideals("selection-urn", "urn2-vig2", items_for("selection-urn"))
    assert abs(top[items_for("selection-urn")["slot"] == 4].mean() - 0.366) < 0.01


def test_uptake_fit_recovers_a_low_noise_respondent_and_an_ignoring_one():
    rng = np.random.default_rng(1)
    module, variant = "mismatch-urn", "urn2-vig2"
    items = items_for(module)
    ideal = urn.vig_ideals(module, variant, items)
    for uptake in (0.0, 0.6):
        delta = np.clip(0.05 + uptake * ideal, 0, 1)
        latent = fit.REPORT_MODELS["mismatch"](items, delta, 1.0)
        reports = sample_reports(latent, 0.03, rng)
        result = fit.fit_uptake("mismatch", items, reports, ideal)
        assert abs(result["parameters"]["uptake"]["mean"] - uptake) <= 0.1
        assert (result["ignores_probability"] > 0.5) == (uptake == 0)


def test_load_curve_recovers_a_rising_noise_and_neglect_over_pooled_sessions():
    from epistemics.ledger.capacity import pooled

    rng = np.random.default_rng(2)
    items = items_for("copying-long-load")
    exact, neglect = observers.load_answers("dependence", items)
    level = np.asarray(items["load"])
    sd = 0.03 * np.exp(0.6 * level)
    eta = 0.1 * level
    means = (1 - eta) * exact + eta * neglect
    reports = np.concatenate([sample_reports(means, sd, rng) for _ in range(3)])
    curve = fit.fit_load_curve("dependence", pooled(items, 3), reports)["parameters"]
    assert abs(curve["load_slope"]["mean"] - 0.6) <= 0.2
    assert abs(curve["eta_slope"]["mean"] - 0.1) <= 0.03


def test_vigilance_headline_is_the_uptake():
    headline = runner.headline(
        {
            "module": "selection-urn",
            "cues": {},
            "uptake": {
                "parameters": {"uptake": {"mean": 0.5, "interval_90": [0.35, 0.6]}},
                "ignores_probability": 0.0,
            },
        }
    )
    assert headline["parameter"] == "audit_uptake" and headline["mean"] == 0.5


def _enumerated(items, i):
    """Posterior log-odds by summing over every sensor's hidden state: copied, read this urn, or
    read another urn."""
    import itertools

    n = int(items["n"][i])
    rep = [int(items[f"rep_{k}"][i]) for k in range(n)]
    odds = []
    for h in (1, 0):
        total = 0.0
        for states in itertools.product(range(3), repeat=n):
            p = 1.0
            for k, z in enumerate(states):
                acc, mis = float(items[f"acc_{k}"][i]), float(items[f"mis_{k}"][i])
                src, rate = int(items[f"src_{k}"][i]), float(items[f"rate_{k}"][i])
                can = src >= 0 and (not int(items[f"cond_{k}"][i]) or rep[src] > 0)
                c = rate if can else 0.0
                if z == 0:
                    p *= c * float(rep[k] == rep[src]) if can else 0.0
                elif z == 1:
                    right = acc if (rep[k] > 0) == (h == 1) else 1 - acc
                    p *= (1 - c) * (1 - mis) * right
                else:
                    p *= (1 - c) * mis * 0.5
            total += p
        odds.append(total)
    prior = float(items["prior"][i])
    return np.log(prior / (1 - prior)) + np.log(odds[0]) - np.log(odds[1])


def test_structural_load_observer_matches_full_enumeration():
    items = items_for("composite-load")
    exact, _ = observers.load_answers("composite", items)
    for i in range(len(exact)):
        assert abs(exact[i] - _enumerated(items, i)) < 1e-9


def test_structural_load_design_holds_readings_fixed_and_every_structure_bears():
    items = items_for("composite-load")
    assert np.bincount(items["load"]).tolist() == [6, 6, 6, 6]
    assert set(items["n"].tolist()) == {design.COMPOSITE_READINGS}
    exact, neglect = observers.load_answers("composite", items)
    assert np.all(np.abs(exact - neglect) >= 0.25) and np.all(np.abs(exact) <= 2.95)
    bearing = design.composite_bearing(items)
    present = {name: ~np.isnan(v) for name, v in bearing.items()}
    for name, values in bearing.items():
        assert np.all(values[present[name]] >= design.COMPOSITE_BEARING)
    level = items["load"]
    assert not present["mis"][level == 0].any() and not present["cond"][level <= 1].any()
    assert present["cond"][level >= 2].all() and present["mis"][level >= 1].all()
    # Conditional copies' sources read red in some cases and blue in others at each level.
    for lv in (2, 3):
        reds = []
        for i in np.flatnonzero((level == lv) & (items["repeat_of"] < 0)):
            for k in range(5):
                if int(items[f"cond_{k}"][i]):
                    reds.append(int(items[f"rep_{int(items[f'src_{k}'][i])}"][i]) > 0)
        assert 0 < sum(reds) < len(reds)
    for i in range(24):
        case = render.render("composite-load", "markets", i, "load-a")["case"]
        for p in render.stated_percentages("composite-load", i):
            assert p in case
        assert "Readings in the order they were logged" in case
