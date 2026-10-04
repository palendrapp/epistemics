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


def test_critical_rho_matches_the_exact_null():
    assert ft.critical_rho(4) == 1.0
    assert abs(ft.critical_rho(8) - 0.643) < 0.001


def test_power_is_calibrated_without_transfer_and_high_with_full_transfer():
    p = ft.power(configurations=(8,), sessions=(8,), true_rho=(1.0, 0.0), datasets=400)
    assert p["n8/m8/rho0.0"] < 0.1 and p["n8/m8/rho1.0"] > 0.7


def test_preregistered_analysis_reads_transfer_and_applies_the_inclusion_rule(monkeypatch):
    import numpy as np

    rng = np.random.default_rng(3)
    configs = ft.GPT6 + ft.GPT56
    level = dict(zip(configs, np.linspace(0.3, 0.95, len(configs)), strict=True))
    rows = []
    for c in configs:
        for domain, modules in (("abstract", ft.ABSTRACT_MODULES), ("finance", ft.FINANCE_MODULES)):
            for m in modules:
                for _ in range(2 if m.endswith(("-asked", "-cues")) else 1):
                    gap = 0.02 + 0.1 * (c in ft.GPT56) if m in ft.GAP_STRUCTURES[domain] else None
                    wording = None
                    if m.startswith("wording-"):
                        wording = [("confirmed", 1.0 + level[c]), ("I think", 0.4)]
                    rows.append({"configuration": c, "domain": domain, "module": m, "run": m,
                                 "round_share": level[c] + rng.normal(0, 0.02),
                                 "round_answers": 20, "gap": gap, "wording": wording})  # fmt: skip
    # One configuration misses the finance minimum (8 of 10).
    rows = [
        r
        for r in rows
        if not (r["configuration"] == "terra-high" and r["module"].startswith("wording-policy"))
    ]
    monkeypatch.setattr(ft, "sessions", lambda root: rows)
    out = ft.preregistered("root", permutations=2000)
    assert "terra-high" not in out["included"] and len(out["included"]) == 11
    assert out["H1"]["pass"] and out["H1"]["rho"] > 0.9 and not out["H1"]["below_minimum"]
    assert out["secondary"]["H2a"]["configurations"] == sorted(ft.GPT6)
    assert out["secondary"]["H4"]["pass"]
    assert out["reported"]["far_round_readout"]["rho"] > 0.9


def test_holm_is_monotone_and_capped():
    adjusted = ft.holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.5})
    assert adjusted == {"a": 0.04, "c": 0.09, "b": 0.09, "d": 0.5}


def test_preset_gives_every_configuration_eight_abstract_and_ten_finance_sessions():
    from collections import Counter

    from epistemics.disposition_tasks import runner

    runs = runner.check_groups(runner.PRESETS["finance-transfer"])
    assert len(runs) == 216
    for config in ft.GPT6 + ft.GPT56:
        mine = [r for r in runs if r[0] == config]
        domains = Counter("abstract" if r[1] in ft.ABSTRACT_MODULES else "finance" for r in mine)
        assert domains == {"abstract": 8, "finance": 10}
        assert all(r[1] in ft.ABSTRACT_MODULES + ft.FINANCE_MODULES for r in mine)


def test_rate_questions_keep_answers_that_equal_the_placeholder_prior():
    record = {
        "items": {"kind": ["rate", "probe", "pair"], "prior": [0.5, 0.5, 0.35]},
        "responses": [0.5, 0.5, 0.35],
    }
    answers = ft._answers(record)
    assert answers == [(0.5, None), (0.5, None), (0.35, 0.35)]
