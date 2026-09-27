"""Bayesian observers whose environmental assumptions are free parameters, and heuristic rivals.

Observers return latent log-odds per item: of high demand for forecasts, or of the queried
structure (a relay, a selective sender) for probes. Stated likelihoods are perceived with
evidence sensitivity gamma: a stated probability q of being correct is treated as
sigmoid(gamma * logit(q)). Items are dicts of equal-length arrays (see design.columns).
"""

import numpy as np

from epistemics.dispositions.response import logit, sigmoid

EDGE = 1e-6  # Boundary priors are evaluated just inside [0, 1] so contradictions stay finite.


def perceived(probability, gamma):
    return sigmoid(gamma * logit(probability))


def _given_high(accuracy, report):
    """P(report | high demand) for a source stated correct with probability `accuracy`."""
    return np.where(report > 0, accuracy, 1 - accuracy)


def corroboration(items, delta, gamma):
    """T2: Bayesian observer with prior `delta` that a matching report relays the first.

    A relay repeats the first report exactly, so it can never conflict with it. The wording cue
    has stated log-likelihood ratio `cue` for relay against independent observation.
    """
    d = np.clip(delta, EDGE, 1 - EDGE)
    qa = perceived(items["accuracy_a"], gamma)
    qb = perceived(items["accuracy_b"], gamma)
    a1 = _given_high(qa, items["report_a"])
    a0 = 1 - a1
    b1 = _given_high(qb, items["report_b"])
    b0 = 1 - b1
    match = (items["report_a"] == items["report_b"]).astype(float)
    relay = d * np.exp(gamma * items["cue"] / 2)
    independent = (1 - d) * np.exp(-gamma * items["cue"] / 2)
    prior = items["prior"]
    with np.errstate(divide="ignore"):
        pair = (
            logit(prior)
            + np.log(a1 * (relay * match + independent * b1))
            - np.log(a0 * (relay * match + independent * b0))
        )
        single = logit(prior) + np.log(a1) - np.log(a0)
        probe = np.log(relay * match * (prior * a1 + (1 - prior) * a0)) - np.log(
            independent * (prior * a1 * b1 + (1 - prior) * a0 * b0)
        )
    kind = items["kind"]
    return np.where(kind == "single", single, np.where(kind == "probe", probe, pair))


def fixed_discount(items, weight, gamma):
    """T2 rival: the second report gets a constant weight, blind to the cue and to conflict."""
    evidence = items["report_a"] * logit(items["accuracy_a"])
    second = items["report_b"] * logit(items["accuracy_b"])
    second = np.where(items["kind"] == "single", 0.0, second)
    return logit(items["prior"]) + gamma * (evidence + weight * second)


def disclosure(items, sigma, gamma):
    """T3: Bayesian observer with prior `sigma` that the sender is selective.

    A selective sender shares every good item and withholds every bad one. Otherwise each item
    is withheld at the stated random rate, whatever its value. Each item is good with stated
    probability `good` under high demand and 1 - `good` under low demand.
    """
    s = np.clip(sigma, EDGE, 1 - EDGE)
    g = perceived(items["good"], gamma)
    m, j, k = items["shared_good"], items["shared_bad"], items["withheld"]
    rate = items["omission"]
    possible = (j == 0).astype(float)
    selective1 = possible * g**m * (1 - g) ** k
    selective0 = possible * (1 - g) ** m * g**k
    common = rate**k * (1 - rate) ** (m + j)
    random1 = common * g**m * (1 - g) ** j
    random0 = common * (1 - g) ** m * g**j
    prior = items["prior"]
    with np.errstate(divide="ignore"):
        forecast = (
            logit(prior)
            + np.log(s * selective1 + (1 - s) * random1)
            - np.log(s * selective0 + (1 - s) * random0)
        )
        probe = np.log(s * (prior * selective1 + (1 - prior) * selective0)) - np.log(
            (1 - s) * (prior * random1 + (1 - prior) * random0)
        )
    return np.where(items["kind"] == "probe", probe, forecast)


def linear_skepticism(items, weight, gamma):
    """T3 rival: each withheld item counts as `weight` of a bad item, whatever else is shared."""
    count = items["shared_good"] - items["shared_bad"] - weight * items["withheld"]
    return logit(items["prior"]) + gamma * logit(items["good"]) * count


def certainty(p, function):
    p = np.asarray(p, dtype=float)
    if function == "linear":
        return np.abs(2 * p - 1)
    if function == "entropy":
        with np.errstate(divide="ignore", invalid="ignore"):
            h = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
        return 1 - np.nan_to_num(h, nan=0.0)
    raise ValueError(f"Unknown certainty function: {function}")


def check_values(items, function):
    """T5: decision value and expected certainty gain of a check with stated posteriors.

    Investing pays `gain` under high demand and loses `loss` under low demand; passing pays zero.
    The check's outcome probabilities follow from the stated posteriors (a martingale).
    """
    prior, high, low = items["prior"], items["high"], items["low"]
    if np.any((low >= prior) | (prior >= high)):
        raise ValueError("Each check needs low < prior < high")
    p_high = (prior - low) / (high - low)

    def best(p):
        return np.maximum(p * items["gain"] - (1 - p) * items["loss"], 0)

    decision = p_high * best(high) + (1 - p_high) * best(low) - best(prior)
    gain = (
        p_high * certainty(high, function)
        + (1 - p_high) * certainty(low, function)
        - certainty(prior, function)
    )
    return decision, gain


STRUCTURES = {"corroboration": corroboration, "disclosure": disclosure}


def structure_posterior(module, items, rate):
    """P(relay) or P(selective sender) per item given its evidence, under base rate `rate`.

    Items without a second report have no structure to reveal and return NaN.
    """
    probed = {**items, "kind": np.where(items["kind"] == "single", "single", "probe")}
    posterior = sigmoid(STRUCTURES[module](probed, rate, 1.0))
    return np.where(items["kind"] == "single", np.nan, posterior)


def revealed_counts(order, revealed):
    """Revealed structures (1, 0 or None) shown before each item, aligned with item index.

    `order` lists item indices in presentation order; `revealed` is aligned with item index and
    each case's structure is revealed after it is answered.
    """
    successes, trials = np.zeros(len(order)), np.zeros(len(order))
    seen, hits = 0, 0
    for index in order:
        successes[index], trials[index] = hits, seen
        if revealed[index] is not None:
            seen += 1
            hits += int(revealed[index])
    return successes, trials


def learned(start, strength, successes, trials):
    """Posterior mean base rate from a Beta prior with mean `start` and strength `strength`."""
    return (np.asarray(start) * strength + successes) / (strength + trials)
