import numpy as np

from epistemics.ledger import battery_v2 as b2


def trait_matrix(rng, trait_sd, interaction_sd=0.05):
    c, t = len(b2.CONFIGURATIONS), len(b2.TASKS)
    return (
        rng.normal(0, trait_sd, (c, 1))
        + rng.normal(0, 1, (1, t))
        + rng.normal(0, interaction_sd, (c, t))
    )


def test_tasks_pair_surfaces_within_cores():
    assert list(b2.TASKS) == ["copying", "echo", "selection", "hub", "mismatch", "stale"]
    assert [list(b2.TASKS)[j] for j in b2.TWIN] == [
        "echo",
        "copying",
        "hub",
        "selection",
        "stale",
        "mismatch",
    ]
    assert b2.family_of("hub-urn-asked") == "hub" and b2.family_of("corroboration-asked") is None


def test_a_consistent_trait_passes_and_shuffled_noise_does_not():
    rng = np.random.default_rng(1)
    strong = b2.test(trait_matrix(rng, 1.0), rng, permutations=300)
    assert strong["task"]["gain"] > 0.8 and strong["task"]["p"] < 0.01
    assert strong["core"]["gain"] > 0.8 and strong["twin"]["gain"] > 0.8
    none = b2.test(trait_matrix(rng, 0.0, interaction_sd=1.0), rng, permutations=300)
    assert none["task"]["p"] > 0.05


def test_missing_cells_are_skipped_not_imputed():
    rng = np.random.default_rng(2)
    y = trait_matrix(rng, 1.0)
    y[0, 0] = y[3, 5] = np.nan
    g = b2.gains(y)
    assert g["task"]["cells"] == y.size - 2 and g["task"]["gain"] > 0.8


def test_holm_adjustment_and_session_filter():
    assert b2.holm({"a": 0.01, "b": 0.04}) == {"a": 0.02, "b": 0.04}
    assert b2.holm({"a": 0.03, "b": 0.02}) == {"b": 0.04, "a": 0.04}
    base = {"configuration": "sol", "means": {"report_sd": 0.1}}
    models = {
        "sessions": [
            {**base, "module": "mismatch-urn", "variant": "urn3-named"},
            {**base, "module": "mismatch-urn", "variant": "urn2-named"},
            {
                **base,
                "module": "echo-urn-asked",
                "variant": "urn2-named",
                "slot_means": [0.1, 0.2, 0.5, 0.7, 0.9],
                "stated": [[0.1], [0.3], [0.5], [0.7], [0.9]],
            },
            {**base, "module": "corroboration", "variant": "paired"},
        ]
    }
    rows = b2.session_rows(models)
    assert [(r[1], r[2]) for r in rows] == [
        ("mismatch", "precision"),
        ("echo", "precision"),
        ("echo", "stated_applied_gap"),
    ]
    assert np.isclose(rows[-1][3], 0.1 / 3)
