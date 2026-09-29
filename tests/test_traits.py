import numpy as np

from epistemics.ledger import traits


def test_tasks_and_rungs_follow_structure_and_format():
    assert traits.task_of("corroboration", "paired") == ("relay · paired", "named")
    assert traits.task_of("corroboration", "open") == ("relay · paired", "open")
    assert traits.task_of("disclosure-cues", "cues-a") == ("disclosure · formal", "named")
    assert traits.task_of("corroboration-unprompted", "named-a") == ("relay · dossier", "open")
    assert traits.task_of("corroboration-asked", "named-a") == ("relay · dossier", "named")
    assert traits.task_of("copying-urn-asked", "urn2-named") == ("copying · urn", "named")
    assert traits.task_of("copying-urn-asked", "urn-named") == ("copying · urn", "open")
    assert traits.task_of("mismatch-urn-probed", "urn3-named") == ("mismatch · urn", "named")
    assert traits.task_of("mismatch-urn", "urn3-rated") == (None, None)
    assert traits.task_of("checks", "paired") == (None, None)


def synthetic(rng, trait_sd, interaction_sd, configs=5, tasks=6, sessions=3):
    rows = []
    effect = rng.normal(0, trait_sd, configs)
    task_effect = rng.normal(0, 1.0, tasks)
    for c in range(configs):
        for t in range(tasks):
            cell = effect[c] + task_effect[t] + rng.normal(0, interaction_sd)
            for _ in range(sessions):
                rows.append(
                    {
                        "configuration": f"c{c}",
                        "task": f"t{t}",
                        "value": cell + rng.normal(0, 0.2),
                        "se": None,
                    }
                )
    return rows


def test_a_consistent_trait_transfers_and_task_specific_noise_does_not():
    rng = np.random.default_rng(3)
    trait = synthetic(rng, trait_sd=1.0, interaction_sd=0.1)
    noise = synthetic(rng, trait_sd=0.0, interaction_sd=1.0)
    g_trait = traits.gstudy(trait, iterations=3000, burn=1000, chains=2)
    g_noise = traits.gstudy(noise, iterations=3000, burn=1000, chains=2)
    assert g_trait["consistency"]["mean"] > 0.8 > 0.4 > g_noise["consistency"]["mean"]
    assert traits.loto(trait)["gain"] > 0.8 and traits.loto(noise)["gain"] < 0.2


def test_session_values_read_priors_only_where_the_structure_is_named():
    base = {"means": {"report_sd": 0.1, "gamma": 1.0}, "order_policy": "random"}
    named = {
        **base,
        "module": "copying-urn-asked",
        "variant": "urn2-named",
        "slot_means": [0.1, 0.2, 0.5, 0.7, 0.9],
        "stated": [[0.1], [0.2], [0.5], [0.8], [0.9]],
    }
    task, values = traits.session_values(named)
    assert task == "copying · urn"
    assert np.isclose(values["missing_rate_default"], 0.0)
    assert np.isclose(values["stated_applied_gap"], 0.1 / 3)
    plain = {**named, "module": "copying-urn", "variant": "urn2-plain"}
    assert set(traits.session_values(plain)[1]) == {"precision", "evidence_weight"}
