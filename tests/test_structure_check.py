import numpy as np

from epistemics import structure_check as sc
from epistemics.disposition_tasks import runner


def test_every_structure_and_protocol_plans_a_valid_collection():
    for protocol, counts in sc.PROTOCOLS.items():
        groups = sc.plan(("astra", "sol"), tuple(sc.CATALOGUE), protocol)
        planned = runner.check_groups(groups)
        assert len(planned) == 2 * len(sc.CATALOGUE) * sum(counts.values())


def test_rated_rung_is_planned_separately_and_off_the_ladder():
    from epistemics.ledger import inclusion

    groups = sc.plan(("sol",), ("mismatch",), "minimal", rungs=(), rated=True)
    assert groups == (
        {
            "configurations": ("sol",),
            "modules": ("mismatch-urn",),
            "contexts": (("urn3-rated", "markets", 1),),
        },
    )
    assert len(runner.check_groups(groups)) == 1
    assert inclusion.rung("mismatch-urn", "urn3-rated") is None
    assert sc.plan(("sol",), ("copying",), "minimal", rungs=(), rated=True) == ()


def test_follows_rule_and_rated_check():
    rates = sc.stated_rates("mismatch")
    assert sc.follows(rates, rates)["follows"]
    assert not sc.follows(sc.IGNORED["judged rare"], rates)["follows"]
    assert not sc.follows(sc.IGNORED["judged, applied"], rates)["follows"]
    near = [r + 0.08 for r in rates]
    assert sc.follows(near, rates)["follows"]
    models = {
        "sessions": [
            {
                "id": "a",
                "configuration": "sol",
                "module": "mismatch-urn",
                "variant": "urn3-rated",
                "slot_means": list(rates),
            },
            {
                "id": "b",
                "configuration": "sol",
                "module": "mismatch-urn",
                "variant": "urn3-rated",
                "slot_means": list(sc.IGNORED["judged rare"]),
            },
            {
                "id": "c",
                "configuration": "sol",
                "module": "mismatch-urn",
                "variant": "urn3-named",
                "slot_means": list(rates),
            },
        ]
    }
    rated = sc.rated_check(models, "sol", "mismatch")
    assert rated["sessions"] == 2 and rated["followed"] == 1 and not rated["reliable"]
    assert sc.rated_check(models, "astra", "mismatch") is None
    assert sc.rated_check(models, "sol", "copying") is None


def test_ladder_modules_sit_on_their_rungs():
    from epistemics.ledger import inclusion

    for key, entry in sc.CATALOGUE.items():
        for rung, (module, variant) in entry["ladder"].items():
            assert inclusion.rung(module, variant) == rung
            assert inclusion.family(module) == key


def test_recommendation_outcomes_weigh_unsafe_errors():
    assert sc.rung_needed([0.1, 0.5, 0.85, 0.99]) == 2
    assert sc.rung_needed([0.1, 0.2, 0.3, 0.5]) is None
    assert sc.outcome(2, 2) == "exact" and sc.excess(2, 2) == 0
    assert sc.outcome(3, 2) == "conservative" and sc.excess(None, 3) == 1
    assert sc.outcome(1, 2) == "unsafe" and sc.outcome(3, None) == "unsafe"
    by_rung = {
        str(r): {"mean": m, "interval_90": [lo, 1.0]}
        for r, (m, lo) in enumerate(((0.3, 0.1), (0.85, 0.7), (0.97, 0.9), (1.0, 0.99)))
    }
    assert sc.recommend(by_rung) == 2


def test_true_inclusion_rises_with_rung_and_falls_with_threshold():
    low, high = sc.true_inclusion(0.0, 0.3), sc.true_inclusion(2.5, 0.3)
    assert np.all(np.diff(low) >= 0) and low[0] > high[0]
    assert sc.rung_needed(low) <= 1 and sc.rung_needed(high) == 3


def test_a_check_recommends_prompting_for_a_structure_it_misses():
    from epistemics.ledger import inclusion

    rng = np.random.default_rng(4)
    truth = {"theta": 1.4, "w": 0.1, "sigma": 0.2, "phi": 0.9}
    counts = {"mismatch": {0: 3, 1: 3, 2: 3, 3: 2}}
    rows = inclusion.simulate(rng, truth, stated=True, stated_source="mixture", counts=counts)
    sc.CHAINS, saved = (4000, 1500), sc.CHAINS
    try:
        result = sc.fit_structure(rows, chains=2)
    finally:
        sc.CHAINS = saved
    assert result["inclusion_by_rung"]["0"]["mean"] < 0.3
    assert result["sessions_by_rung"] == {"0": 3, "1": 3, "2": 3, "3": 2}


def test_default_budget_leaves_room_for_the_runners_admission_reserve():
    from epistemics.disposition_tasks import runner

    assert sc.RUNNER_RESERVE == 800000 and sc.RUNNER_CONCURRENCY == 2
    source = runner.prepare.__code__.co_consts
    assert 800000 in source and 2 in source
    for sessions in (2, 4, 6, 11):
        before_last = (sessions - sc.RUNNER_CONCURRENCY) * 0.55e6
        assert before_last + sc.RUNNER_CONCURRENCY * sc.RUNNER_RESERVE <= sc.budget_for(sessions)
