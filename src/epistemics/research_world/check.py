"""A priced independent end-customer survey: genuinely new evidence about demand.

The result is drawn from the world's demand, so matched presentations of one world share it.
Its expected decision value depends on the reader's posterior, so a reader who over-weights
relayed or selectively disclosed evidence can undervalue it exactly when it matters.
"""

from datetime import timedelta

import numpy as np

from epistemics.research_world.render import check_document, names
from epistemics.research_world.world import ANCHORS

P_POSITIVE_STRONG = 0.8
P_POSITIVE_WEAK = 0.2
SAMPLE = 20
PRICES = (0.02, 0.05, 0.10)
DESCRIPTION = (
    "An independent survey of 20 of the company's end customers, commissioned for you. It reads "
    f"positive (a majority increasing spend) {P_POSITIVE_STRONG:.0%} of the time when demand is "
    f"strong and {P_POSITIVE_WEAK:.0%} when it is weak. It shares no sources with the dossier."
)


def draw(world):
    anchor = world.presentation == ANCHORS[world.family]
    family = 0 if world.family == "disclosure" else 1
    rng = np.random.default_rng([world.pair_seed, 20, family, int(anchor)])
    positive = bool(rng.random() < (P_POSITIVE_STRONG if world.strong else P_POSITIVE_WEAK))
    count = int(rng.integers(11, 17)) if positive else int(rng.integers(3, 10))
    return positive, count


def document(world):
    positive, count = draw(world)
    day = names(world.pair_seed, world.family)["start"] + timedelta(days=6)
    return check_document(positive, SAMPLE, count, day)


def expected_value(probability, threshold):
    """Expected gain in investment payoff from seeing the survey before deciding."""
    if not (0 <= probability <= 1 and 0 < threshold < 1):
        raise ValueError("Probability and threshold must lie in [0, 1] and (0, 1)")
    after = 0.0
    for q_strong, q_weak in (
        (P_POSITIVE_STRONG, P_POSITIVE_WEAK),
        (1 - P_POSITIVE_STRONG, 1 - P_POSITIVE_WEAK),
    ):
        after += max(
            0.0, probability * q_strong * (1 - threshold) - (1 - probability) * q_weak * threshold
        )
    return max(0.0, after - max(0.0, probability - threshold))
