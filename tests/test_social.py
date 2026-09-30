import itertools

import numpy as np

from epistemics.disposition_tasks import runner
from epistemics.disposition_tasks.render import render, stated_percentages
from epistemics.dispositions import social
from epistemics.dispositions.response import sample_reports


def logit(p):
    return np.log(p / (1 - p))


def test_advice_design_crosses_records_phrases_and_own_readings():
    items = social.advice_design()
    assert len(items["prior"]) == 24
    combos = {
        (
            int(items[f"hits_{items['phrase'][i]}"][i]),
            int(items["phrase"][i]),
            bool(items["own"][i]),
        )
        for i in range(24)
    }
    assert len(combos) == 24
    exact = social.advice_answer(items)
    assert np.all(np.abs(exact) <= 2.95)
    # The ideal answer uses only the record of the phrase used.
    for i in range(24):
        h = int(items["phrase"][i])
        q = items[f"hits_{h}"][i] / 40  # model 0.12: the hit rate
        own = items["own"][i] * logit(items["own_acc"][i])
        expected = logit(items["prior"][i]) + own + items["call"][i] * logit(q)
        assert abs(exact[i] - expected) < 1e-12


def test_conformity_answers_follow_the_status_of_the_majority():
    items = social.conformity_design()
    assert len(items["prior"]) == 24
    assert int(np.sum(items["n"] == 0)) == 6
    exact, counted = social.conformity_answers(items)
    for i in range(24):
        n, status = int(items["n"][i]), int(items["status"][i])
        base = logit(items["prior"][i]) + items["own"][i] * logit(items["own_acc"][i])
        reading = -items["own"][i] * logit(items["peer_acc"][i])
        expected = base + {0: n * reading, 1: (n > 0) * reading, 2: 0.0}[status]
        assert abs(exact[i] - expected) < 1e-12
        assert abs(counted[i] - (base + (0 if status == 2 else n * reading))) < 1e-12
    assert np.all(np.abs(exact) <= 2.95)


def test_relay_accuracy_matches_enumeration_of_garbles():
    for acc, fidelity, hops in itertools.product((0.8, 0.9), (0.6, 0.8), range(4)):
        correct = 0.0
        # Each relay keeps the call (f) or replaces it by a coin flip (1 - f, then right half the
        # time whatever it received).
        for kept in itertools.product((True, False), repeat=hops):
            p = np.prod([fidelity if k else 1 - fidelity for k in kept])
            correct += p * (acc if all(kept) else 0.5)
        assert abs(social.relay_accuracy(acc, hops, fidelity) - correct) < 1e-12


def test_peer_texts_show_every_number_and_state_fidelity_only_when_asked():
    for module, variant in (
        ("advice-peer", "peer-a"),
        ("advice-peer", "peer-open"),
        ("conformity-peer", "peer-a"),
        ("conformity-peer", "peer-open"),
        ("relay-peer", "chain-stated"),
        ("relay-peer", "chain-open"),
        ("copying-peer", "urn2-vig2"),
    ):
        for i in range(24):
            case = render(module, "markets", i, variant)["case"]
            for p in stated_percentages(module, i, variant):
                assert p in case, (module, variant, i, p)
    items = social.relay_design()
    for i in range(24):
        stated = render("relay-peer", "markets", i, "chain-stated")["case"]
        open_ = render("relay-peer", "markets", i, "chain-open")["case"]
        hops = int(items["hops"][i])
        assert ("coin flip" in stated) == (hops > 0)
        assert "coin flip" not in open_
        assert stated.count("→") == (hops + 1 if hops else 0)


def test_social_fits_recover_low_noise_respondents():
    rng = np.random.default_rng(4)
    advice = social.advice_design()
    reports = sample_reports(social.advice_answer(advice, 0.9, 0.6, 0.5), 0.02, rng)
    fit = social.fit_advice(advice, reports)["parameters"]
    assert abs(fit["beta_rec"]["mean"] - 0.6) < 0.1 and abs(fit["beta_conf"]["mean"] - 0.5) < 0.1
    items = social.conformity_design()
    exact, counted, own, conform = social.conformity_terms(items)
    means = own + 0.3 * exact + 0.7 * counted + 0.6 * conform
    fit = social.fit_conformity(items, sample_reports(means, 0.02, rng))["parameters"]
    assert abs(fit["kappa"]["mean"] - 0.6) < 0.1 and abs(fit["eta"]["mean"] - 0.7) < 0.15
    relay = social.relay_design()
    reports = sample_reports(social.relay_answer(relay, 0.7, 1.0), 0.02, rng)
    assert (
        abs(social.fit_relay(relay, reports, False)["parameters"]["fidelity"]["mean"] - 0.7) < 0.05
    )


def test_social_headline_is_the_fitted_parameter():
    analysis = {
        "module": "advice-peer",
        "social": {
            "headline": "beta_conf",
            "parameters": {"beta_conf": {"mean": 0.4, "interval_90": [0.3, 0.5]}},
        },
    }
    assert runner.headline(analysis) == {
        "parameter": "beta_conf",
        "mean": 0.4,
        "interval_90": [0.3, 0.5],
    }


def test_runner_accepts_every_module_variant_and_cover_the_audit_renders():
    from epistemics.disposition_tasks.render import MODULES
    from epistemics.disposition_tasks.validation import covers_of, variants_of

    for module in MODULES:
        for variant in variants_of(module):
            for cover in covers_of(module):
                group = {"configurations": ["astra"], "modules": [module]}
                if variant == "v3-loaded":
                    group["order"] = "refer-back"
                runner.check_groups([{**group, "contexts": [(variant, cover, 1)]}])


def test_open_variants_hide_the_record_and_the_majoritys_evidence_and_fit_defaults():
    for i in range(24):
        advice = render("advice-peer", "markets", i, "peer-open")["case"]
        assert "right in" not in advice and "record" not in advice
        analysts = render("conformity-peer", "markets", i, "peer-open")["case"].split("\n\n")[-1]
        if "Analysts in the lab" in analysts:
            for hidden in ("read the urn", "guess", "passed on", "sensor", "correct"):
                assert hidden not in analysts
    rng = np.random.default_rng(6)
    items = social.advice_design()
    reports = sample_reports(social.advice_open_answer(items, 1.0, 1.5, 0.6), 0.02, rng)
    fit = social.fit_advice_open(items, reports)["parameters"]
    assert abs(fit["w0"]["mean"] - 1.5) < 0.1 and abs(fit["w_conf"]["mean"] - 0.6) < 0.1
    items = social.conformity_design()
    reports = sample_reports(social.conformity_open_answer(items, 1.0, 0.8, 0.3), 0.02, rng)
    fit = social.fit_conformity_open(items, reports)["parameters"]
    assert abs(fit["v"]["mean"] - 0.8) < 0.1 and abs(fit["rho"]["mean"] - 0.3) < 0.1


def test_confidence_surfaces_share_the_advice_cases_and_never_price_confidence():
    from epistemics.disposition_tasks.render import items_for

    base = items_for("advice-peer")
    for module in ("advice-relay", "advice-sensor", "advice-agent"):
        items = items_for(module)
        assert all(np.array_equal(items[k], base[k]) for k in base)
        for i in range(24):
            case = render(module, "markets", i, "peer-open")["case"]
            source = case.split("Your own sensor")[0].split("\n\n", 1)[1]
            assert "%" not in source and "correct" not in source
    relay = render("advice-relay", "markets", 0, "peer-open")["case"]
    assert "did not read the urn" in relay and "no information" in relay


def test_leave_one_surface_out_gain_rewards_a_shared_configuration_effect():
    from epistemics.ledger import confidence

    rng = np.random.default_rng(7)
    shared = np.repeat(np.linspace(0, 1, 8)[:, None], 4, axis=1) + rng.normal(0, 0.02, (8, 4))
    assert confidence.gain(shared)["gain"] > 0.9
    unrelated = np.column_stack([rng.permutation(np.linspace(0, 1, 8)) for _ in range(4)])
    assert confidence.gain(unrelated)["gain"] < 0.5
