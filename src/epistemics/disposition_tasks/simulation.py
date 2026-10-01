"""Synthetic respondents with known parameters, driven through the real collection service.

These runs check the rendering, ordering, reveal, answer and analysis pipeline, not any agent.
"""

import numpy as np

from epistemics.disposition_tasks.collection import CollectionService, create, export
from epistemics.disposition_tasks.render import items_for  # noqa: F401 (also used in simulate)
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
    if module.startswith("coherence-"):
        return coherence_responses(items, truth, rng)
    if module.startswith(("decision-", "decision2-")):
        return decision_responses(items, truth, rng)
    if module.startswith("cohere-"):
        from epistemics.dispositions import cohere

        return cohere.respond(str(items["family"][0]), items, truth, rng)
    if module.startswith("screen-"):
        from epistemics.dispositions import screen

        return screen.respond(str(items["family"][0]), items, truth["params"], rng, truth["noise"])
    if module in ("advice-peer", "conformity-peer", "relay-peer") or module.startswith("advice-"):
        from epistemics.dispositions import social

        if module.startswith("advice-") and "w0" in truth:
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
        if trial["response"] == "choice":
            from epistemics.disposition_tasks.surfaces import options

            shown, act = options(
                items_for(module), service.manifest.order[trial["case_number"] - 1]
            )
            answer = {"choice": shown[act] if value >= 0.5 else shown[1 - act]}
        elif trial["response"] == "points":
            answer = {"points": int(value)}
        else:
            answer = {"probability": float(value)}
        trial = service.submit(trial["trial_id"], answer)["next_trial"]
    service.finish()
    return export(directory)


def coherence_responses(items, truth, rng):
    """Battery v3 respondent: stated beliefs are the ideal answers with unstated accuracies and
    copy rates completed at the respondent's defaults, plus report noise; revealed beliefs follow
    r = alpha + beta s + noise(tau_c), turned into certainty equivalents through utility x^rho;
    lotteries are answered through the same utility."""
    from epistemics.dispositions import coherence

    kinds = np.asarray(items["kind"])
    out = np.zeros(len(kinds))
    stated = {}
    for i in np.flatnonzero(kinds == "stated"):
        row = {k: items[k][i] for k in items}
        fill = {
            (0, kind, k): truth["default_acc"] if kind == "acc" else truth["default_rate"]
            for kind, k in coherence.unstated(row)
        }
        latent = coherence.observers.composite(coherence._observer_items([row], fill))[0]
        stated[int(items["scenario"][i])] = latent
        out[i] = sample_reports(latent, truth["stated_sd"], rng)
    for i in np.flatnonzero(kinds == "revealed"):
        s = stated[int(items["scenario"][i])]
        r = truth["alpha"] + truth["beta"] * s + rng.normal(0, truth["tau_c"])
        p = 1 / (1 + np.exp(-r))
        out[i] = np.clip(np.round(coherence.certainty_equivalent(p, truth["rho"])), 0, 100)
    for i in np.flatnonzero(kinds == "lottery"):
        ce = coherence.certainty_equivalent(items["lottery_p"][i], truth["rho"])
        out[i] = np.clip(np.round(ce + rng.normal(0, 1.0)), 0, 100)
    return out


def decision_responses(items, truth, rng):
    """Battery v3.1 respondent: stated beliefs as in v3 (defaults for unstated properties, report
    noise); decisions act with probability Phi(kappa (s - theta_class)) on the respondent's own
    belief (the ideal belief for anchors), shifted by `stakes` towards the favoured option."""
    import math

    from epistemics.dispositions import coherence

    kinds = np.asarray(items["kind"])
    out = np.zeros(len(kinds))
    latent = {}
    for i in np.flatnonzero((kinds == "stated") | (kinds == "anchor")):
        row = {k: items[k][i] for k in items}
        fill = {
            (0, kind, k): truth["default_acc"] if kind == "acc" else truth["default_rate"]
            for kind, k in coherence.unstated(row)
        }
        belief = coherence.observers.composite(coherence._observer_items([row], fill))[0]
        latent[int(items["scenario"][i])] = belief
        if kinds[i] == "stated":
            out[i] = sample_reports(belief, truth["stated_sd"], rng)
    for i in np.flatnonzero((kinds == "decision") | (kinds == "anchor")):
        s = latent[int(items["scenario"][i])]
        theta = truth["thresholds"][int(items["cls"][i])]
        if int(items["stakes"][i]):
            theta -= truth.get("stakes", 0.0) * int(items["stakes_dir"][i])
        p = 0.5 * (1 + math.erf(truth["kappa"] * (s - theta) / math.sqrt(2)))
        out[i] = float(rng.random() < p)
    return out
