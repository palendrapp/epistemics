import numpy as np

from epistemics.disposition_tasks import runner
from epistemics.disposition_tasks.render import ANNOUNCED_MODULES, render
from epistemics.dispositions import announced
from epistemics.dispositions import statements as st
from epistemics.ledger import announced as ledger


def test_every_case_meets_every_condition_and_declares_what_it_holds():
    seen = {}
    for module in ANNOUNCED_MODULES:
        items = announced.design(module)
        assert sorted(items["condition"].tolist()).count("one") == 6
        for i in range(24):
            k, condition = int(items["item"][i]), str(items["condition"][i])
            seen.setdefault(k, set()).add(condition)
            held = announced.changes(announced.items_spec()[k], condition)
            assert len(held) == announced.DECLARED[condition]
            if condition == "three-said":
                assert all(name in st.STYLES for name, _ in held[1:])
            case = render(module, "markets", i, "announced")["case"]
            declared = announced.DECLARED[condition]
            assert f"differs from it in {declared} place" in case
    assert all(v == set(announced.CONDITIONS) for v in seen.values()) and len(seen) == 24
    assert len(runner.check_groups(runner.PRESETS["announced-count"])) == 16


def _rows(truth, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for module in ANNOUNCED_MODULES:
        items = announced.design(module)
        rows += announced.session(items, announced.respond(items, truth, rng))["cases"]
    return rows


def test_budget_and_pragmatic_respondents_are_told_apart():
    w = {s: 1.0 for s in st.SLOTS}
    budget = ledger.analyse(_rows({"w": w, "k": 0.5, "rewordings": 1.0, "tau": 0.05}))
    pragmatic = ledger.analyse(_rows({"w": w, "k": 0.5, "rewordings": 0.0, "tau": 0.05}))
    assert budget["ratio_six_one"] < 0.5 and abs(budget["restored"]["mean"]) < 0.2
    assert pragmatic["restored"]["mean"] > 0.8
