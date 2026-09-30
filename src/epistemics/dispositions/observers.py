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


def mismatch(items, rho, gamma):
    """Abstract third structure: Bayesian observer with prior `rho` that a reading comes from a
    different urn than the one it is filed under.

    A reading from another urn is red or blue with equal chance whatever this urn's state (half of
    all urns are red-majority), so it carries no evidence. Own draws ("own") cannot be misfiled.
    Probes ask for the probability that the reading came from a different urn.
    """
    r = np.clip(rho, EDGE, 1 - EDGE)
    q = perceived(items["accuracy_a"], gamma)
    a1 = _given_high(q, items["report_a"])
    a0 = 1 - a1
    prior = items["prior"]
    forecast = logit(prior) + np.log((1 - r) * a1 + r * 0.5) - np.log((1 - r) * a0 + r * 0.5)
    own = logit(prior) + np.log(a1) - np.log(a0)
    probe = np.log(r * 0.5) - np.log((1 - r) * (prior * a1 + (1 - prior) * a0))
    kind = items["kind"]
    return np.where(kind == "own", own, np.where(kind == "probe", probe, forecast))


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


def cue_observer(model, items, dispositions, gamma):
    """Latent log-odds for a cue module: each description slot has its own disposition.

    Stated base-rate questions ("rate") report the slot's disposition itself; anchors (slot -1)
    do not depend on it.
    """
    slots = items["slot"]
    table = np.asarray(dispositions, dtype=float)
    delta = np.where(slots >= 0, table[np.maximum(slots, 0)], 0.5)
    latent = model(items, delta, gamma)
    stated = logit(np.clip(delta, EDGE, 1 - EDGE))
    return np.where(items["kind"] == "rate", stated, latent)


def _field(items, name, k, default, dtype=float):
    key = f"{name}_{k}"
    if key in items:
        return np.asarray(items[key], dtype=dtype)
    return np.full(len(items["prior"]), default, dtype=dtype)


def _source(items, src):
    """Per case, the logged reading (+1 red, -1 blue) of the sensor `src` names (0 if none)."""
    return np.array([items[f"rep_{s}"][i] if s >= 0 else 0 for i, s in enumerate(src)])


def _applies(cond, source, mode):
    """Whether a relation applies: cond 0 always, 1 when the source reads red, 2 when blue.
    `mode` "unconditional" and "never" are the two misreadings of a condition."""
    if mode == "unconditional":
        return np.ones(np.shape(cond), dtype=bool)
    if mode == "never":
        return cond == 0
    return (cond == 0) | ((cond == 1) & (source > 0)) | ((cond == 2) & (source < 0))


def composite(
    items,
    ignore_copy=False,
    ignore_mis=False,
    conditions="exact",
    mis_conditions="exact",
    ignore_second=False,
):
    """Capacity battery, structural load (models 0.9 and 0.10): posterior log-odds when copying,
    misfiling and their conditions combine among one set of readings.

    Readings are taken in logging order. A sensor that may copy (src >= 0) repeats its source's
    logged reading with probability `rate`, wherever that reading came from; with `cond` 1 (2) it
    copies only in rounds when the source's reading is red (blue). Model 0.10 adds a second
    source (`src2`, `rate2`) and conditional misfiling: with `msrc` >= 0, the misfiling rate
    applies only in rounds when that sensor's reading is blue. Otherwise the sensor reads for
    itself, and a share `mis` of the readings it takes itself come from a different urn. So each
    reading's likelihood depends only on the urn and other logged readings.

    The keyword arguments give the partial answers: ignoring copying, misfiling or the second
    source, or misreading copy or misfiling conditions ("unconditional" or "never").
    """
    total = logit(np.asarray(items["prior"], dtype=float))
    width = sum(1 for key in items if key.startswith("acc_"))
    for k in range(width):
        present = k < np.asarray(items["n"])
        acc = np.asarray(items[f"acc_{k}"], dtype=float)
        rep = np.asarray(items[f"rep_{k}"])
        msrc = _field(items, "msrc", k, -1, int)
        mis_applies = _applies(np.where(msrc >= 0, 2, 0), _source(items, msrc), mis_conditions)
        mis = 0.0 if ignore_mis else np.where(mis_applies, _field(items, "mis", k, 0.0), 0.0)
        p1 = np.clip(np.where(rep > 0, acc, 1 - acc), EDGE, 1 - EDGE)
        own1 = (1 - mis) * p1 + mis / 2
        own0 = (1 - mis) * (1 - p1) + mis / 2
        shares, matches = [], []
        links = [("src", "rate", "cond")] + ([] if ignore_second else [("src2", "rate2", None)])
        for src_name, rate_name, cond_name in links:
            src = _field(items, src_name, k, -1, int)
            source = _source(items, src)
            cond = _field(items, cond_name, k, 0, int) if cond_name else np.zeros(len(src), int)
            copies = (src >= 0) & _applies(cond, source, conditions) & (not ignore_copy)
            shares.append(np.where(copies, _field(items, rate_name, k, 0.0), 0.0))
            matches.append((rep == source).astype(float))
        rest = 1 - sum(shares)
        l1 = sum(c * m for c, m in zip(shares, matches, strict=True)) + rest * own1
        l0 = sum(c * m for c, m in zip(shares, matches, strict=True)) + rest * own0
        total = total + np.where(present, np.log(l1) - np.log(l0), 0.0)
    return total


def composite_partials(items):
    """Each structure's misreadings, as answers: the evidence for attributing an error to it."""
    return {
        "copying ignored": composite(items, ignore_copy=True),
        "misfiling ignored": composite(items, ignore_mis=True),
        "copy condition read as unconditional": composite(items, conditions="unconditional"),
        "copy condition read as never": composite(items, conditions="never"),
        "misfiling condition read as unconditional": composite(
            items, mis_conditions="unconditional"
        ),
        "misfiling condition read as never": composite(items, mis_conditions="never"),
        "second source ignored": composite(items, ignore_second=True),
    }


def load_answers(model, items):
    """Capacity battery, Part A: the exact posterior log-odds of a fully specified case, and the
    answer that neglects the structure (every reading independent and from this urn)."""
    if model == "composite":
        return composite(items), composite(items, ignore_copy=True, ignore_mis=True)
    prior = logit(np.asarray(items["prior"], dtype=float))
    exact, neglect = prior.copy(), prior.copy()
    width = sum(1 for key in items if key.startswith("acc_"))
    for k in range(width):
        acc = np.asarray(items[f"acc_{k}"], dtype=float)
        present = k < np.asarray(items["n"])
        rep = np.asarray(items[f"rep_{k}"])
        p1 = np.where(rep > 0, acc, 1 - acc)
        p1 = np.clip(p1, EDGE, 1 - EDGE)
        p0 = 1 - p1
        independent = np.log(p1) - np.log(p0)
        neglect = neglect + np.where(present, independent, 0.0)
        if model == "dependence":
            src = np.asarray(items[f"src_{k}"])
            rate = np.asarray(items[f"rate_{k}"], dtype=float)
            original = np.array([items[f"rep_{s}"][i] if s >= 0 else 0 for i, s in enumerate(src)])
            match = (rep == original).astype(float)
            term = np.log(rate * match + (1 - rate) * p1) - np.log(rate * match + (1 - rate) * p0)
            step = np.where(src >= 0, term, independent)
        else:
            mis = np.asarray(items[f"mis_{k}"], dtype=float)
            step = np.log((1 - mis) * p1 + mis / 2) - np.log((1 - mis) * p0 + mis / 2)
        exact = exact + np.where(present, step, 0.0)
    return exact, neglect
