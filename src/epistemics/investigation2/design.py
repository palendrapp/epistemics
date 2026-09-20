"""Balanced review slots and matched prices; never select on future answers/outcomes."""

import random
from uuid import uuid4

from epistemics.investigation2.battery import public_trial
from epistemics.investigation2.inference import query_values
from epistemics.investigation2.models import MEASUREMENTS, Assignment
from epistemics.investigation2.world import generate


def opportunity(trial, query):
    # Measurable with the operating record alone, not the actual query result,
    # company outcome, hidden offset or any participant response.
    return query_values(trial)[query]["gross_value"] >= 0.025


def schedule(seed, mode="discovery"):
    rng = random.Random(seed)
    offsets = [-6, 0, 6] * 2
    rng.shuffle(offsets)
    assignments = [
        Assignment(
            assignment_id=str(uuid4()),
            seed=rng.randrange(2**40),
            mode=mode,
            family="review",
            offset=offset,
        )
        for offset in offsets
    ]
    for query in MEASUREMENTS:
        pair = str(uuid4())
        for attempt in range(1, 10001):
            assignment = Assignment(
                assignment_id=str(uuid4()),
                seed=rng.randrange(2**40),
                mode=mode,
                family="research",
                offset=0,
                focused_query=query,
                price_condition="low",
                pair_id=pair,
                selection_attempts=attempt,
            )
            world = generate(assignment.seed, 0)
            if opportunity(public_trial(assignment, world, 1), query):
                break
        else:
            raise ValueError(f"No {query} opportunity in 10000 draws; no partial design was saved")
        assignments.extend(
            [
                assignment,
                assignment.model_copy(
                    update={"assignment_id": str(uuid4()), "price_condition": "high"}
                ),
            ]
        )
    rng.shuffle(assignments)
    return assignments
