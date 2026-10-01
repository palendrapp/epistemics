import numpy as np

from epistemics.disposition_tasks import runner
from epistemics.disposition_tasks.render import FOLLOWUP_MODULES, render
from epistemics.dispositions import followup


def test_every_case_is_asked_fresh_in_one_form_and_as_a_follow_up_in_the_other():
    for variant in followup.VARIANTS:
        a = followup.design(f"followup-advice-{variant}-a")
        b = followup.design(f"followup-advice-{variant}-b")
        for items in (a, b):
            assert sum(items["kind"] == "fresh") == 8 and sum(items["kind"] == "followup") == 8
        fresh_a = set(a["base"][a["kind"] == "fresh"].tolist())
        follow_b = set(b["base"][b["kind"] == "followup"].tolist())
        assert fresh_a == follow_b and len(fresh_a) == 8


def test_first_questions_ask_likely_or_unlikely_and_follow_ups_refer_back():
    for module in FOLLOWUP_MODULES:
        items = followup.design(module)
        for i in np.flatnonzero(items["kind"] == "first"):
            first = render(module, "markets", int(i), "followup")
            second = render(module, "markets", int(i) + 1, "followup")
            assert first["question"].startswith("Is it likely or unlikely that")
            assert first["options"] == ["Likely", "Unlikely"]
            assert "The previous case asked about the same urn." in second["case"]
    assert len(runner.check_groups(runner.PRESETS["followup-advice"])) == 24


def test_simulated_rounding_and_exact_errors_are_measured():
    rng = np.random.default_rng(3)
    items = followup.design("followup-advice-stated-a")
    truth = {"rho_fresh": 0.0, "rho_followup": 1.0, "tau": 0.0}
    s = followup.session(items, followup.respond(items, truth, rng))
    assert s["grain"]["followup"]["share_5"] == 1.0
    assert s["grain"]["fresh"]["share_5"] < 0.5
    assert max(r["error"] for r in s["answers"] if r["kind"] == "fresh") < 0.05


def test_guide_reads_the_split_from_the_frame_sensitivity():
    from epistemics.ledger import guide

    def frames(fresh, follow, direct, follow_distance):
        return {
            "frame_sensitivity": {
                "fresh": {"share_5": fresh, "n": 24},
                "follow_up": {"share_5": follow, "n": 40},
                "distance_direct": direct,
                "distance_follow_up": follow_distance,
                "retest_follow_up": 0.3,
                "sessions": 10,
                "computed_error": {"fresh": 0.01, "follow_up": 0.01},
            }
        }

    readout = guide.framing(frames(0.25, 0.85, 0.6, 0.22))
    assert readout["topic"] == "framing" and "round numbers" in readout["claim"]
    assert "exact either way" in readout["caution"]
    content = guide.framing(frames(0.2, 0.2, 0.5, 1.2))
    assert content["fact"]["value"] == "Same precision; answers move"
    assert guide.framing(frames(0.2, 0.25, 0.5, 0.55))["fact"]["value"] == "Unchanged"
    assert guide.framing({}) is None
