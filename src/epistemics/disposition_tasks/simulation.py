"""Synthetic respondents with known parameters, driven through the real collection service.

These runs check the rendering, ordering, answer and analysis pipeline, not any agent.
"""

import numpy as np

from epistemics.disposition_tasks.collection import CollectionService, create, export
from epistemics.disposition_tasks.render import items_for
from epistemics.dispositions import fit, observers
from epistemics.dispositions.response import sample_reports, sample_wtp
from epistemics.source_learning.simulation import PARTICIPANT


def responses(module, truth, rng):
    """One response per design item from a respondent with the given parameters."""
    items = items_for(module)
    if module == "checks":
        decision, gain = observers.check_values(items, truth["function"])
        means = truth["certainty_value"] * gain + truth["decision_weight"] * decision
        return sample_wtp(means, truth["wtp_sd"], rng)
    model = {"corroboration": "dependence", "disclosure": "disclosure"}[module]
    latent = fit.REPORT_MODELS[truth.get("model", model)](
        items, truth["disposition"], truth["gamma"]
    )
    latent = latent + truth["bias"] * (items["kind"] != "probe")
    return sample_reports(latent, truth["report_sd"], rng)


def simulate(directory, *, module, cover, order, truth, seed):
    rng = np.random.default_rng(seed)
    create(directory, PARTICIPANT, module=module, cover=cover, order=order, synthetic=True)
    answers = responses(module, truth, rng)
    service = CollectionService(directory)
    trial = service.get_trial()["trial"]
    while trial is not None:
        value = answers[service.manifest.order[trial["case_number"] - 1]]
        answer = {"points": int(value)} if module == "checks" else {"probability": float(value)}
        trial = service.submit(trial["trial_id"], answer)["next_trial"]
    service.finish()
    return export(directory)
