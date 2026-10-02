import numpy as np

from epistemics.disposition_tasks import runner
from epistemics.disposition_tasks.render import CORRELATED_MODULES
from epistemics.dispositions import correlated
from epistemics.dispositions import statements as st
from epistemics.ledger import correlated as ledger


def test_items_agree_or_disagree_and_appear_in_both_orders():
    specs = correlated.items_spec()
    assert sum(s["agree"] for s in specs) == 12
    orders = {}
    for module in CORRELATED_MODULES:
        items = correlated.design(module)
        for k, first in zip(items["item"], items["first"], strict=True):
            orders.setdefault(int(k), set()).add(str(first))
    assert len(orders) == 24 and all(len(v) == 2 for v in orders.values())
    assert len(runner.check_groups(runner.PRESETS["correlated-changes"])) == 16


def _rows(truth, seed=2):
    rng = np.random.default_rng(seed)
    rows = []
    for module in CORRELATED_MODULES:
        items = correlated.design(module)
        rows += correlated.session(items, correlated.respond(items, truth, rng))["items"]
    return rows


def test_the_regression_tells_independent_correlated_and_averaging_apart():
    w = {s: 0.8 for s in st.SLOTS}
    independent = ledger.analyse(_rows({"w": w, "c": 0.0, "tau": 0.03}))
    correlated_ = ledger.analyse(_rows({"w": w, "c": 0.5, "tau": 0.03}))
    averaging = ledger.analyse(_rows({"w": w, "c": 0.0, "tau": 0.03, "averaging": True}))
    assert abs(independent["a"]["mean"] - 1) < 0.15 and abs(independent["b"]["mean"]) < 0.15
    assert correlated_["b"]["mean"] < -0.3
    assert abs(averaging["a"]["mean"] - 0.5) < 0.15 and abs(averaging["b"]["mean"] + 0.5) < 0.15


def test_primacy_ratio_reads_a_discount_on_later_changes():
    from epistemics.ledger import primacy

    pairs = [(1.0, 0.8), (0.5, 0.4), (0.8, 0.64)]
    r = primacy.ratio(pairs)
    assert abs(r["ratio"] - 0.8) < 1e-9 and r["changes"] == 3
