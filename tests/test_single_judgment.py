import numpy as np

from epistemics.ledger import single_judgment as sj


def _rows(diff_abstract, diff_finance, seed=0, luna_diff=0.4):
    rng = np.random.default_rng(seed)
    rows = []
    for _family, (first, second), d_a, d_f in (
        ("GPT-6", ("astra", "sol"), diff_abstract, diff_finance),
        ("GPT-5.6", ("luna", "terra"), luna_diff, luna_diff),
    ):
        for domain, d, m in (("abstract", d_a, 5), ("finance", d_f, 12)):
            for v, shift in ((first, d / 2), (second, -d / 2)):
                for k, e in enumerate(sj.EFFORTS):
                    for _ in range(m):
                        rows.append({"configuration": sj.configuration(v, e), "domain": domain,
                                     "round_share": 0.5 + shift + 0.01 * k + rng.normal(0, 0.1),
                                     "module": "x", "run": "r", "answers": 20})  # fmt: skip
    return rows


def test_configuration_names_round_trip():
    assert sj.configuration("astra", "medium") == "astra"
    assert sj.configuration("terra", "high") == "terra-high"
    assert sj.split("luna-low") == ("luna", "low") and sj.split("sol") == ("sol", "medium")


def test_contrast_detects_a_variant_difference_and_not_its_absence():
    rng = np.random.default_rng(1)
    present = sj.contrast(_rows(0.3, 0.2), "GPT-6", "finance", rng, 2000)
    assert present["p_one_sided"] < 0.01 and set(present["by_effort"]) == set(sj.EFFORTS)
    nulls = [
        sj.contrast(_rows(0.0, 0.0, seed=s), "GPT-6", "finance", rng, 500)["p_one_sided"]
        for s in range(10, 30)
    ]
    assert sum(p < 0.05 for p in nulls) <= 3 and 0.3 < np.mean(nulls) < 0.7


def test_preregistered_requires_both_domains(monkeypatch):
    monkeypatch.setattr(sj, "sessions", lambda roots: _rows(0.3, 0.0, seed=3))
    out = sj.preregistered([], permutations=2000)
    assert not out["primary"]["H1"]["pass"] and out["primary"]["H2"]["pass"]
    monkeypatch.setattr(sj, "sessions", lambda roots: _rows(0.3, 0.2, seed=4))
    out = sj.preregistered([], permutations=2000)
    assert out["primary"]["H1"]["pass"]
    assert out["secondary"]["within_family_configurations"]["mean_rho"] > 0


def test_preset_gives_five_abstract_and_twelve_finance_sessions():
    from epistemics.disposition_tasks import runner

    runs = runner.check_groups(runner.PRESETS["single-judgment-transfer"])
    assert len(runs) == 204
    for config in ("astra", "terra-high"):
        mine = [r for r in runs if r[0] == config]
        assert sum(r[1] in sj.ABSTRACT_MODULES for r in mine) == 5
        assert sum(r[1] in sj.FINANCE_MODULES for r in mine) == 12
