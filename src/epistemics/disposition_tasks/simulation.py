"""Synthetic respondents with known parameters, driven through the real collection service.

These runs check the rendering, ordering, reveal, answer and analysis pipeline, not any agent.
"""

import numpy as np

from epistemics.disposition_tasks.collection import CollectionService, create, export
from epistemics.disposition_tasks.render import items_for
from epistemics.dispositions import fit, observers
from epistemics.dispositions.response import sample_reports, sample_wtp
from epistemics.source_learning.simulation import PARTICIPANT


def responses(module, truth, rng, order=None, revealed=None):
    """One response per design item from a respondent with the given parameters.

    A truth with `strength` learns its disposition from revealed structures, starting at
    `start`; otherwise the disposition is fixed.
    """
    items = items_for(module)
    if module == "checks":
        decision, gain = observers.check_values(items, truth["function"])
        means = truth["certainty_value"] * gain + truth["decision_weight"] * decision
        return sample_wtp(means, truth["wtp_sd"], rng)
    if "slots" in truth:
        observer = fit.REPORT_MODELS[
            {
                "corroboration-cues": "dependence",
                "disclosure-cues": "disclosure",
                "corroboration-range": "dependence",
                "corroboration-dossier": "dependence",
                "disclosure-dossier": "disclosure",
                "corroboration-unprompted": "dependence",
                "disclosure-unprompted": "disclosure",
                "corroboration-asked": "dependence",
                "disclosure-asked": "disclosure",
                "corroboration-probed": "dependence",
            }[module]
        ]
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
    answers = responses(module, truth, rng, manifest.order, manifest.revealed)
    service = CollectionService(directory)
    trial = service.get_trial()["trial"]
    while trial is not None:
        value = answers[service.manifest.order[trial["case_number"] - 1]]
        answer = {"points": int(value)} if module == "checks" else {"probability": float(value)}
        trial = service.submit(trial["trial_id"], answer)["next_trial"]
    service.finish()
    return export(directory)
