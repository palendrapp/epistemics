from epistemics.ledger import sweep


def _rows(root, values, cls="open"):
    """values: {configuration: [answers to cases 0, 1, ...]}"""
    return [
        {
            "root": root,
            "configuration": c,
            "case": ("screen-num-a", "markets", "screen", i),
            "repeat": 1,
            "value": v,
            "class": cls,
            "latency": 2.0,
        }
        for c, vs in values.items()
        for i, v in enumerate(vs)
    ]


def test_signatures_rank_boldness_grain_and_departure():
    values = {
        "astra": [0.5, 0.55, 0.45, 0.6],
        "sol": [0.52, 0.57, 0.43, 0.61],
        "terra": [0.5, 0.55, 0.45, 0.6],
        "luna": [0.9, 0.95, 0.1, 0.95],
    }
    table = sweep.signatures(_rows("screen-stage-a-20261001", values), [])
    row = table["screen-stage-a"]
    assert row["luna"]["boldness"] > row["astra"]["boldness"]
    assert row["luna"]["departure"] > row["astra"]["departure"]
    assert row["astra"]["grain"] == 1.0 and row["sol"]["grain"] < 1.0
    assert row["astra"]["grain_by_class"]["open"]["n"] == 4


def test_stability_is_one_when_every_collection_orders_configurations_alike():
    values = {"astra": [0.5] * 4, "sol": [0.55] * 4, "terra": [0.6] * 4, "luna": [0.9] * 4}
    rows = _rows("screen-stage-a-20261001", values) + _rows("cohere-stage-a-20261001", values)
    result = sweep.stability(sweep.signatures(rows, []))
    assert result["extremity"]["mean_rho"] == 1.0
    assert result["extremity"]["mean_rank"]["luna"]["rank"] == 1.0


def test_open_grain_compares_astra_with_sol_at_the_same_effort():
    values = {"astra": [0.5, 0.6], "sol": [0.53, 0.61], "luna": [0.5, 0.5], "terra": [0.5, 0.5]}
    table = sweep.signatures(_rows("screen-stage-a-20261001", values), [])
    result = sweep.open_grain(table)
    assert result["of"] == 1 and result["astra_rounder"] == 1
