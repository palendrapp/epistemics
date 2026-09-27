"""Synthetic respondents driven through the real collection service.

The respondent reports with a known neglect weight and noise, buys the survey when its own
reported probability makes the survey worth more than the price, and updates on a purchased
result by Bayes' rule from its own report. These runs check the pipeline, not any agent.
"""

import math

import numpy as np

from epistemics.research_world import check
from epistemics.research_world.analysis import check_llr
from epistemics.research_world.collection import CollectionService, create, export, world_for
from epistemics.research_world.synthetic import report
from epistemics.research_world.world import logit, sigmoid
from epistemics.source_learning.simulation import PARTICIPANT


def simulate(directory, items, *, arm, check_offered, chi, noise_sd, seed):
    rng = np.random.default_rng(seed)
    manifest = create(
        directory, PARTICIPANT, arm=arm, items=items, check_offered=check_offered, synthetic=True
    )
    service = CollectionService(directory)
    trial, reported = service.get_trial()["trial"], {}
    while trial is not None:
        item = manifest.items[trial["case_number"] - 1]
        world = world_for(item)
        if trial["stage"] == "assessment":
            p = report(world, chi, noise_sd, rng)
            reported[item.case] = p
            answer = {"probability": p, "decision": "invest" if p > world.threshold else "decline"}
            if item.check_price is not None:
                worth = check.expected_value(p, world.threshold) > item.check_price
                answer["check"] = "buy" if worth else "skip"
        else:
            positive, _ = check.draw(world)
            p = sigmoid(logit(min(0.99, max(0.01, reported[item.case]))) + check_llr(positive))
            p = float(min(0.99, max(0.01, round(p, 2))))
            answer = {"probability": p, "decision": "invest" if p > world.threshold else "decline"}
        trial = service.submit(trial["trial_id"], answer)["next_trial"]
    service.finish()
    result = export(directory)
    if not math.isfinite(result.analysis["mean_expected_payoff"]):
        raise ValueError("Non-finite analysis")
    return result
