from epistemics.ledger import finance_transfer as ft


def test_compare_reads_a_perfect_ordering_at_the_smallest_attainable_p():
    abstract = {"a": 0.1, "b": 0.2, "c": 0.3, "d": 0.4}
    out = ft.compare(abstract, {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0})
    assert out["rho"] == 1.0 and abs(out["p_one_sided"] - 1 / 24) < 1e-12
    assert out["same_side_of_median"] == 4
    reversed_ = ft.compare(abstract, {"a": 4.0, "b": 3.0, "c": 2.0, "d": 1.0})
    assert reversed_["rho"] == -1.0 and reversed_["p_one_sided"] == 1.0
    assert reversed_["same_side_of_median"] == 0


def test_compare_uses_only_configurations_measured_in_both():
    out = ft.compare({"a": 1, "b": 2, "c": 3}, {"b": 5, "c": 6, "d": 7})
    assert out["configurations"] == ["b", "c"]


def test_round_share_ignores_extremes_and_answers_left_at_the_prior():
    share, n = ft._round_share([(0.55, 0.5), (0.5, 0.5), (0.97, 0.5), (0.63, 0.6)])
    assert n == 2 and share == 0.5
