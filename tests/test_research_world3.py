import copy
import math

import numpy as np
import pytest

from epistemics.research_world3.extract import audit, extract, ledger
from epistemics.research_world3.render import BACKGROUND, names, render, structure_note
from epistemics.research_world3.synthetic import collect_pairs, paired_estimate
from epistemics.research_world3.world import (
    ANCHORS,
    PAIRS,
    generate,
    naive_logit,
    normative_logit,
    sigmoid,
)
from epistemics.source_learning.storage import encoded

FAMILIES = sorted(PAIRS)


@pytest.mark.parametrize("family", FAMILIES)
def test_matched_presentations_share_demand_and_posterior(family):
    for seed in range(80):
        worlds = generate(seed, family)
        a, b = (worlds[p] for p in PAIRS[family])
        assert a.strong == b.strong
        assert math.isclose(normative_logit(a), normative_logit(b))
        assert math.isclose(naive_logit(a), normative_logit(a))
        assert not math.isclose(naive_logit(b), normative_logit(b))
        anchor = worlds[ANCHORS[family]]
        assert (anchor.prior_strong, anchor.threshold) == (a.prior_strong, a.threshold)
        assert generate(seed, family) == worlds
    with pytest.raises(ValueError):
        generate(-1, family)


def test_naive_readings_take_fabrications_at_face_value_and_drop_informal_reports():
    for seed in range(60):
        v = generate(seed, "validity")
        report = v["invalid"].atom(v["invalid"].invalid[0])
        assert naive_logit(v["invalid"]) == pytest.approx(
            normative_logit(v["omitted"]) + report.log_likelihood_ratio()
        )
        assert normative_logit(v["valid"]) == pytest.approx(naive_logit(v["invalid"]))
        r = generate(seed, "register")
        informal = r["sloppy"].atom(r["sloppy"].discounted[0])
        assert naive_logit(r["sloppy"]) == pytest.approx(
            normative_logit(r["polished"]) - informal.log_likelihood_ratio()
        )
        assert normative_logit(r["absent"]) == pytest.approx(naive_logit(r["sloppy"]))


@pytest.mark.parametrize("family", FAMILIES)
def test_every_dossier_matches_its_ledger_and_hides_private_state(family):
    for seed in range(200):
        worlds = generate(seed, family)
        dossiers = {p: render(w) for p, w in worlds.items()}
        assert audit(worlds, dossiers)
        for dossier in dossiers.values():
            text = encoded(dossier).decode()
            for secret in ('strong": ', "atom_id", "survey-", "marker", "pair_seed", "excess"):
                assert secret not in text
            assert all(line in dossier["case"] for line in BACKGROUND)
            assert len(dossier["documents"]) == 10


def test_fabricated_reports_are_polished_and_informal_reports_are_valid():
    for seed in range(100):
        v = generate(seed, "validity")
        reports = extract(render(v["invalid"]))
        assert [r[1] for r in reports] == ["polished"] * 3
        assert sum(not r[2] for r in reports) == 1
        r = generate(seed, "register")
        informal = [x for x in extract(render(r["sloppy"])) if x[1] == "informal"]
        assert len(informal) == 1 and informal[0][2]
        firm = names(seed, "register")["firms"][0]
        assert firm in structure_note(r["sloppy"]) or firm.rstrip("s") in structure_note(
            r["sloppy"]
        )


def test_audit_rejects_repaired_fabrications_and_changed_register():
    for seed in range(40):
        v = generate(seed, "validity")
        if v["invalid"].atom(v["invalid"].invalid[0]).detail["marker"] == "margin":
            break
    dossiers = {p: render(w) for p, w in v.items()}
    repaired = copy.deepcopy(dossiers)
    for doc in repaired["invalid"]["documents"]:
        doc["text"] = doc["text"].replace("about ±1 points", "about ±16 points")
    with pytest.raises(ValueError):
        audit(v, repaired)
    r = generate(3, "register")
    swapped = {p: render(w) for p, w in r.items()}
    swapped["sloppy"] = copy.deepcopy(swapped["polished"])
    with pytest.raises(ValueError):
        audit(r, swapped)
    assert extract(render(r["sloppy"])) == ledger(r["sloppy"])


@pytest.mark.parametrize("family", FAMILIES)
def test_demand_is_drawn_from_the_genuine_posterior(family):
    control = PAIRS[family][0]
    strong, posterior = [], []
    for seed in range(3000):
        world = generate(seed, family)[control]
        strong.append(world.strong)
        posterior.append(sigmoid(normative_logit(world)))
    assert abs(np.mean(strong) - np.mean(posterior)) < 0.03


@pytest.mark.parametrize("family", FAMILIES)
def test_paired_estimator_recovers_known_weights(family):
    from epistemics.research_world3.design import measurable

    rng = np.random.default_rng(1)
    seeds = [s for s in range(400) if measurable(s, family)][:40]
    for chi in (0.0, 0.5, 1.0):
        estimate = paired_estimate(collect_pairs(family, seeds, chi, 0.0, rng))
        assert estimate["chi"] == pytest.approx(chi, abs=0.08)
