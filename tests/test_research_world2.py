import copy
import math

import numpy as np
import pytest

from epistemics.research_world2.extract import audit, extract, ledger, normalize
from epistemics.research_world2.render import render
from epistemics.research_world2.synthetic import collect_pairs, paired_estimate
from epistemics.research_world2.world import (
    ANCHORS,
    PAIRS,
    generate,
    logit,
    naive_logit,
    normative_logit,
    sigmoid,
)
from epistemics.source_learning.storage import encoded

FAMILIES = sorted(PAIRS)


@pytest.mark.parametrize("family", FAMILIES)
def test_matched_presentations_share_world_and_posterior(family):
    for seed in range(60):
        worlds = generate(seed, family)
        a, b = (worlds[p] for p in PAIRS[family])
        anchor = worlds[ANCHORS[family]]
        assert a.atoms == b.atoms and a.strong == b.strong
        assert math.isclose(normative_logit(a), normative_logit(b))
        assert math.isclose(naive_logit(a), normative_logit(a))
        assert naive_logit(b) != pytest.approx(normative_logit(b))
        assert anchor.prior_strong == a.prior_strong and anchor.threshold == a.threshold
        assert generate(seed, family) == worlds
    with pytest.raises(ValueError):
        generate(-1, family)


def test_naive_readings_match_their_definitions():
    for seed in range(40):
        s = generate(seed, "shared_origin")
        llr = s["single"].atoms[0].log_likelihood_ratio()
        relays = s["relayed"].mentions[s["relayed"].shown[0]] - 1
        assert relays in (2, 3, 4)
        assert naive_logit(s["relayed"]) == pytest.approx(
            normative_logit(s["single"]) + relays * llr
        )
        d = generate(seed, "disclosure")
        # Ignoring a selective rule reads the dossier like one whose company tracks only beats.
        assert naive_logit(d["selected"]) == pytest.approx(normative_logit(d["silent_control"]))


@pytest.mark.parametrize("family", FAMILIES)
def test_every_rendered_dossier_matches_its_ledger_and_hides_private_state(family):
    for seed in range(150):
        worlds = generate(seed, family)
        dossiers = {p: render(w) for p, w in worlds.items()}
        assert audit(worlds, dossiers)
        for dossier in dossiers.values():
            text = encoded(dossier).decode()
            for secret in ('strong": ', "atom_id", "kpi-", "check-", "p_favorable", "pair_seed"):
                assert secret not in text
        assert render(worlds[PAIRS[family][0]]) == dossiers[PAIRS[family][0]]


def test_audit_rejects_altered_evidence_or_mismatched_pairs():
    worlds = generate(5, "disclosure")
    dossiers = {p: render(w) for p, w in worlds.items()}
    flipped = copy.deepcopy(dossiers)
    letter = next(d for d in flipped["full"]["documents"] if d["kind"] == "shareholder letter")
    letter["text"] = (
        letter["text"].replace("ahead of", "short of", 1)
        if "ahead of" in letter["text"]
        else letter["text"].replace("short of", "ahead of", 1)
    )
    with pytest.raises(ValueError):
        audit(worlds, flipped)
    shifted = copy.deepcopy(dossiers)
    distractor = next(
        i for i, d in enumerate(shifted["selected"]["documents"]) if d["title"] == "Sector roundup"
    )
    shifted["selected"]["documents"][distractor]["date"] = "2026-12-31"
    with pytest.raises(ValueError):
        audit(worlds, shifted)
    s = generate(5, "shared_origin")
    relays = {p: render(w) for p, w in s.items()}
    relayed = relays["relayed"]["documents"]
    relayed.pop(
        next(
            i
            for i, d in enumerate(relayed)
            if "reorders" in d["text"] and d["kind"] != "analyst note"
        )
    )
    with pytest.raises(ValueError):
        audit(s, relays)


def test_extraction_counts_relays_once_and_implies_withheld_misses():
    s = generate(9, "shared_origin")
    relayed = normalize(extract(render(s["relayed"])))
    assert len(relayed["checks"]) == 1
    assert relayed["checks"][0][-1] == s["relayed"].mentions[s["relayed"].shown[0]]
    assert relayed == ledger(s["relayed"])
    d = generate(9, "disclosure")
    selected = normalize(extract(render(d["selected"])))
    assert selected["kpi_implied"] and not any(selected["kpi_implied"].values())
    assert set(selected["kpi_shown"]) | set(selected["kpi_implied"]) == {
        a.name for a in d["full"].atoms
    }


@pytest.mark.parametrize("family", FAMILIES)
def test_demand_is_drawn_from_the_complete_posterior(family):
    control = PAIRS[family][0]
    strong, posterior = [], []
    for seed in range(3000):
        world = generate(seed, family)[control]
        strong.append(world.strong)
        posterior.append(sigmoid(normative_logit(world)))
    assert abs(np.mean(strong) - np.mean(posterior)) < 0.03


@pytest.mark.parametrize("family", FAMILIES)
def test_paired_estimator_recovers_known_neglect(family):
    rng = np.random.default_rng(1)
    for chi in (0.0, 0.5, 1.0):
        estimate = paired_estimate(collect_pairs(family, range(40), chi, 0.0, rng))
        assert estimate["chi"] == pytest.approx(chi, abs=0.08)
    with pytest.raises(ValueError):
        paired_estimate([])
    assert logit(0.5) == 0


def test_harder_cues_leave_structure_to_inference():
    from epistemics.research_world2.render import BACKGROUND, names

    for seed in range(80):
        s = generate(seed, "shared_origin")
        relayed = render(s["relayed"])
        analyst = names(seed, "shared_origin")["analysts"][0]
        relays = [d for d in relayed["documents"] if d["kind"] != "analyst note"]
        survey_relays = [d for d in relays if "reorders" in d["text"]]
        assert len(survey_relays) == s["relayed"].mentions[s["relayed"].shown[0]] - 1
        assert all(analyst not in d["text"] and analyst != d["source"] for d in survey_relays)
        assert len(relayed["documents"]) == 10
        d = generate(seed, "disclosure")
        for presentation in ("full", "selected"):
            text = " ".join(x["text"] for x in render(d[presentation])["documents"])
            assert "only the KPIs that met" not in text and "discusses only" not in text
        assert (
            render(d["full"])["case"].split("Background:")[1]
            == render(s["single"])["case"].split("Background:")[1]
        )
        assert all(line in render(d["selected"])["case"] for line in BACKGROUND)
