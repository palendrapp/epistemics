import numpy as np

from epistemics.disposition_tasks import runner
from epistemics.disposition_tasks.render import WORDING_MODULES, render
from epistemics.dispositions import wording


def test_every_item_takes_every_wording_and_the_families_share_a_skeleton():
    levels = {}
    for module in WORDING_MODULES:
        family, form = wording.parse(module)
        offered = wording.levels(family)
        items = wording.design(module)
        assert len(items["item"]) == 24
        for k, level in zip(items["item"], items["wording"], strict=True):
            levels.setdefault((family, int(k)), set()).add(int(level))
        for level in offered:
            at = items["wording"] == level
            assert at.sum() == 24 // len(offered) and items["direction"][at].sum() == 0
    assert len(levels) == 120
    assert all(v == set(wording.levels(f)) for (f, _), v in levels.items())
    assert wording.levels("urn3") == wording.levels("policy3") == (0, 1, 3)
    assert wording.base("policy3") == "policy" and wording.base("report") == "report"
    a, b = wording.design("wording-urn-c"), wording.design("wording-report-c")
    for key in ("prior", "direction", "wording"):
        assert (a[key] == b[key]).all()


def test_the_three_wording_families_differ_only_in_their_phrase_set():
    for family in ("urn", "policy"):
        three = render(f"wording-{family}3-a", "markets", 3, "wording")["case"]
        four = render(f"wording-{family}-a", "markets", 3, "wording")["case"]
        assert "one of three ways" in three and "one of four ways" in four
        head = three[: three.index("“")].replace("three ways", "four ways")
        assert head == four[: four.index("“")]
    assert len(runner.check_groups(runner.PRESETS["wording-phrase-set-policy"])) == 28
    items = wording.design("wording-urn3-b")
    result = wording.session(items, [0.5] * 24)
    assert set(result["mean_weight"]) == {"I think", "plain", "confirmed"}


def test_phrase_sets_reads_a_configuration_that_stands_out_only_with_three(monkeypatch):
    from epistemics.ledger import wording as ledger

    rng = np.random.default_rng(6)

    def weights(top):
        return {"I think": rng.normal(0.5, 0.2, 24), "confirmed": rng.normal(top, 0.2, 24)}

    data = {}
    for c, (three, four) in {"astra": (1.0, 1.5), "sol": (1.2, 2.0), "luna": (1.4, 1.7),
                             "terra": (2.6, 2.2)}.items():  # fmt: skip
        data[(c, "urn3")], data[(c, "urn")] = weights(three), weights(four)
    monkeypatch.setattr(ledger, "cases", lambda roots: data)
    terra = ledger.phrase_sets([])["configurations"]["terra"]
    assert terra["three"]["confirmed_to_others"]["ratio"] > 2
    assert terra["ratio_shift"]["interval_90"][0] > 1


def test_only_the_claims_wording_changes_across_forms():
    cases = [render(f"wording-policy-{f}", "markets", 7, "wording")["case"] for f in "abcd"]
    claims = [c[c.index("“") :] for c in cases]
    assert len({c[: c.index("“")] for c in cases}) == 1
    assert sum("I think" in c for c in claims) == 1
    assert sum("definitely" in c for c in claims) == 2
    assert sum("confirmed" in c for c in claims) == 1


def test_session_recovers_the_weight_of_each_wording():
    rng = np.random.default_rng(3)
    truth = {"w": [0.4, 0.9, 1.6, 2.4], "tau": 0.02}
    means = {w: [] for w in wording.WORDINGS}
    for module in WORDING_MODULES[:4]:
        items = wording.design(module)
        result = wording.session(items, wording.respond(items, truth, rng))
        for w, m in result["mean_weight"].items():
            means[w].append(m)
    for w, target in zip(wording.WORDINGS, truth["w"], strict=True):
        assert abs(np.mean(means[w]) - target) < 0.1
    assert len(runner.check_groups(runner.PRESETS["wording-families"])) == 48


def test_summary_flags_face_value_only_where_confident_claims_move_it_further(monkeypatch):
    from epistemics.ledger import wording as ledger

    rng = np.random.default_rng(5)

    def weights(w):
        return {name: rng.normal(v, 0.2, 24) for name, v in zip(wording.WORDINGS, w, strict=True)}

    data = {
        ("astra", "policy"): weights([0.6, 0.8, 1.0, 1.1]),
        ("sol", "policy"): weights([0.4, 0.8, 1.2, 1.4]),
        ("luna", "policy"): weights([0.3, 0.5, 1.0, 1.3]),
        ("terra", "policy"): weights([0.5, 1.1, 2.0, 2.8]),
    }
    monkeypatch.setattr(ledger, "cases", lambda roots: data)
    table = ledger.summary([])["families"]["policy"]
    assert table["terra"]["face_value"] and not table["sol"]["face_value"]
    assert table["terra"]["confirmed_to_others"]["ratio"] > 2
    assert abs(table["terra"]["confirmed_adds"]["mean"] - 0.8) < 0.2


def test_guide_reads_most_least_and_claim_dependent_wording():
    from epistemics.ledger import guide

    def family(ratio, ceiling=0.0):
        return {"confident": 2.0 * ratio, "tentative": 0.5, "ratio": ratio,
                "interval_90": [ratio - 0.2, ratio + 0.2], "spread": 1.0, "ceiling": ceiling,
                "sessions": 4}  # fmt: skip

    def passport(ratios, least=False, record=1.0, ceiling=0.0):
        fams = {k: family(r, ceiling) for k, r in zip(("urn", "policy", "report"), ratios)}  # noqa: B905
        pooled = float(np.exp(np.mean(np.log(ratios))))
        return {"wording_sensitivity": {"families": fams, "pooled_ratio": pooled,
                                        "least_spread": least, "sessions": 12,
                                        "record_ratio": record}}  # fmt: skip

    more = guide.confident_wording(passport([1.1, 1.75, 1.3], ceiling=0.5))
    assert more["fact"]["value"].startswith("Moved more")
    assert "about as far for an analyst's" in more["claim"] and "economist's" in more["claim"]
    assert "99% or more" in more["claim"] and "exactly" in more["claim"]
    less = guide.confident_wording(passport([0.7, 0.4, 0.55], least=True, record=None))
    assert less["fact"]["value"].startswith("Moved less") and "change least" in less["claim"]
    assert "every kind of claim" in less["claim"] and "exactly" not in less["claim"]
    mixed = guide.confident_wording(passport([0.7, 2.2, 1.4]))
    assert (
        mixed["fact"]["value"].startswith("Depends") and "less for an analyst's" in mixed["claim"]
    )
    assert guide.confident_wording(passport([0.9, 1.1, 1.0]))["fact"]["value"] == "Like the others"
    assert guide.confident_wording({}) is None


def test_caution_carries_the_three_wording_result_per_kind_of_claim():
    from epistemics.ledger import guide

    assert "untested" in guide.phrase_set_note(None)
    urn = {"three": 1.65, "four": 1.0, "shift": 0.08, "shift_interval_90": [-0.5, 0.67]}
    policy = {"three": 1.27, "four": 1.46, "shift": -0.61, "shift_interval_90": [-0.92, -0.32]}
    one = guide.phrase_set_note({"urn": urn})
    assert "no clear change" in one and "1.65 times" in one and "(1.00 with four)" in one
    assert "not the same way" not in one
    both = guide.phrase_set_note({"urn": urn, "policy": policy})
    assert "not the same way for every kind of claim" in both
    assert "for an economist's forecast, it gives" in both and "top of the source's range" in both
    alike = guide.phrase_set_note({"urn": policy, "policy": policy})
    assert "in the same direction for both kinds of claim" in alike
    more = {"three": 0.67, "four": 0.4, "shift": 0.36, "shift_interval_90": [0.23, 0.49]}
    assert "more (+0.36" in guide.phrase_set_note({"policy": more})
