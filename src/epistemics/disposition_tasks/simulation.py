"""Synthetic respondents with known parameters, driven through the real collection service.

These runs check the rendering, ordering, reveal, answer and analysis pipeline, not any agent.
"""

import numpy as np

from epistemics.disposition_tasks.collection import CollectionService, create, export
from epistemics.disposition_tasks.render import items_for
from epistemics.dispositions import fit, observers
from epistemics.dispositions.response import sample_reports, sample_wtp
from epistemics.source_learning.simulation import PARTICIPANT


def responses(module, truth, rng, order=None, revealed=None, variant=None):
    """One response per design item from a respondent with the given parameters.

    A truth with `strength` learns its disposition from revealed structures, starting at
    `start`; a truth with `uptake` applies that fraction of the ideal rate for each audit record
    (the variant's); otherwise the disposition is fixed.
    """
    items = items_for(module)
    if module == "checks":
        decision, gain = observers.check_values(items, truth["function"])
        means = truth["certainty_value"] * gain + truth["decision_weight"] * decision
        return sample_wtp(means, truth["wtp_sd"], rng)
    if "load_sd" in truth:
        from epistemics.disposition_tasks.analysis import LOAD_MODELS

        exact, neglect = observers.load_answers(LOAD_MODELS[module], items)
        level = np.asarray(items["load"])
        eta = np.asarray(truth["load_eta"])[level]
        sd = np.asarray(truth["load_sd"])[level]
        return sample_reports((1 - eta) * exact + eta * neglect + truth["bias"], sd, rng)
    if module in ("advice-peer", "conformity-peer", "relay-peer"):
        from epistemics.dispositions import social

        if module == "advice-peer" and "w0" in truth:
            latent = social.advice_open_answer(
                items, truth["beta_own"], truth["w0"], truth["w_conf"]
            )
        elif module == "conformity-peer" and "rho" in truth:
            latent = social.conformity_open_answer(
                items, truth["beta_own"], truth["v"], truth["rho"]
            )
        elif module == "advice-peer":
            latent = social.advice_answer(
                items, truth["beta_own"], truth["beta_rec"], truth["beta_conf"]
            )
        elif module == "conformity-peer":
            exact, counted, own, conform = social.conformity_terms(items)
            latent = (
                truth["beta_own"] * own
                + (1 - truth["eta"]) * exact
                + truth["eta"] * counted
                + truth["kappa"] * conform
            )
        elif "omega" in truth:
            fidelity = np.asarray(items["fidelity"], dtype=float) ** truth["omega"]
            latent = social.relay_answer(items, fidelity, truth["gamma"])
        else:
            latent = social.relay_answer(items, truth["fidelity"], truth["gamma"])
        return sample_reports(latent + truth["bias"], truth["report_sd"], rng)
    if "uptake" in truth:
        from epistemics.disposition_tasks.analysis import CUE_MODELS
        from epistemics.disposition_tasks.urn import vig_ideals

        ideal = vig_ideals(module, variant, items)
        delta = np.clip(truth["baseline"] + truth["uptake"] * ideal, 0.0, 1.0)
        latent = fit.REPORT_MODELS[CUE_MODELS[module]](items, delta, truth["gamma"])
        forecast = ~np.isin(items["kind"], ("probe", "rate"))
        return sample_reports(latent + truth["bias"] * forecast, truth["report_sd"], rng)
    if "slots" in truth:
        from epistemics.disposition_tasks.analysis import CUE_MODELS

        observer = fit.REPORT_MODELS[CUE_MODELS[module]]
        latent = observers.cue_observer(observer, items, truth["slots"], truth["gamma"])
        forecast = ~np.isin(items["kind"], ("probe", "rate"))
        return sample_reports(latent + truth["bias"] * forecast, truth["report_sd"], rng)
    model = {"corroboration": "dependence", "disclosure": "disclosure"}[module]
    disposition = truth.get("disposition")
    if "strength" in truth:
        successes, trials = observers.revealed_counts(order, revealed)
        disposition = observers.learned(truth["start"], truth["strength"], successes, trials)
    latent = fit.REPORT_MODELS[truth.get("model", model)](items, disposition, truth["gamma"])
    latent = latent + truth["bias"] * (items["kind"] != "probe")
    return sample_reports(latent, truth["report_sd"], rng)


def simulate(directory, *, module, cover, order, truth, seed, variant="paired", reveal_seed=None):
    rng = np.random.default_rng(seed)
    manifest = create(
        directory,
        PARTICIPANT,
        module=module,
        cover=cover,
        order=order,
        variant=variant,
        reveal_seed=reveal_seed,
        synthetic=True,
    )
    answers = responses(module, truth, rng, manifest.order, manifest.revealed, variant)
    service = CollectionService(directory)
    trial = service.get_trial()["trial"]
    while trial is not None:
        value = answers[service.manifest.order[trial["case_number"] - 1]]
        answer = {"points": int(value)} if module == "checks" else {"probability": float(value)}
        trial = service.submit(trial["trial_id"], answer)["next_trial"]
    service.finish()
    return export(directory)
