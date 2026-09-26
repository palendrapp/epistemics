"""A fixed one-step decision-value rule; inputs are public reported probability and terms."""

import math
import random

POLICIES = ("none", "always", "cost_aware")
PRICES = (0.01, 0.04, 0.20)
RULE = {
    "id": "binomial-five-evsi.v1",
    "sample_size": 5,
    "expansion_given_strong": 0.7,
    "expansion_given_weak": 0.3,
    "buy_if": "expected_value_of_sample - offered_price > 1e-12",
    "ties": "no check",
    "scope": "Myopic expected decision value using the provisional reported probability; assumes Bayesian sample use and a payoff-maximizing final action; no fitted profile or internal-belief claim",
}


def expected_value(probability, threshold):
    """Integrate positive posterior investment value over all six possible panel counts."""
    if not all(math.isfinite(x) and 0 <= x <= 1 for x in (probability, threshold)):
        raise ValueError("Probability and threshold must be finite values from zero to one")
    after = 0.0
    for k in range(6):
        strong = math.comb(5, k) * 0.7**k * 0.3 ** (5 - k)
        weak = math.comb(5, k) * 0.3**k * 0.7 ** (5 - k)
        after += max(
            0.0, probability * strong * (1 - threshold) - (1 - probability) * weak * threshold
        )
    return max(0.0, after - max(0.0, probability - threshold))


def choose(policy, probability, threshold, price):
    if policy not in POLICIES or not math.isfinite(price) or price < 0:
        raise ValueError("Unknown policy or invalid price")
    buy = policy == "always" or (
        policy == "cost_aware" and expected_value(probability, threshold) - price > 1e-12
    )
    return "customer_panel" if buy else "stop"


def offers(manifest, price_seed):
    """Randomize prices within public prior/threshold strata, without reading outcomes.

    Each prior gets all three prices, with a randomly assigned duplicated price. Each
    threshold gets two of each price. The duplicated price is permuted across priors;
    neither prior nor threshold determines price. Twelve companies cannot fully cross
    3 priors x 2 thresholds x 3 prices; this is a balanced incomplete crossing.
    """
    if not isinstance(price_seed, int) or isinstance(price_seed, bool) or price_seed < 0:
        raise ValueError("Price seed must be a nonnegative integer")
    rng = random.Random(price_seed)
    prices = list(PRICES)
    rng.shuffle(prices)
    direction = rng.choice((-1, 1))
    assigned = {}
    for i, prior in enumerate((0.2, 0.5, 0.8)):
        for j, threshold in enumerate((0.3, 0.7)):
            companies = [
                c
                for c in manifest.companies[12:]
                if c.prior_strong == prior and c.threshold == threshold
            ]
            if len(companies) != 2:
                raise ValueError("Price design requires two companies in every public stratum")
            rng.shuffle(companies)
            assigned[companies[0].company_id] = prices[i]
            assigned[companies[1].company_id] = prices[(i + direction * (1 if j == 0 else -1)) % 3]
    return [
        {"company_id": c.company_id, "available_check_cost": assigned[c.company_id]}
        for c in manifest.companies[12:]
    ]


def price_for(binding, company_id):
    return next(
        o["available_check_cost"] for o in binding["offers"] if o["company_id"] == company_id
    )
