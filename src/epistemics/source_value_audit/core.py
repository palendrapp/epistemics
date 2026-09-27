"""Separate public inference, privileged reference, purchase policy and realization.

All sample expectations enumerate both company states and all six panel counts.
The known-process reference sees source parameters, but never current truth or the
check realization. Public inference receives a deliberately narrower input type.
"""

from dataclasses import dataclass
from math import comb, exp, isfinite, log

from epistemics.source_inference.observers import predict
from epistemics.source_inference.world import Probe, PublicRecord, Source, World, distribution
from epistemics.source_selective.policy import choose

PANEL = tuple(
    tuple(comb(5, k) * rate**k * (1 - rate) ** (5 - k) for k in range(6)) for rate in (0.3, 0.7)
)


@dataclass(frozen=True)
class PublicCase:
    history: tuple[PublicRecord, ...]
    probe: Probe
    threshold: float
    price: float

    def __post_init__(self):
        if self.probe.world != World() or self.probe.disclosed_rule is not None:
            raise ValueError("Audit is scoped to the existing unaudited five-customer task")
        if not isfinite(self.threshold) or not 0 < self.threshold < 1:
            raise ValueError("Threshold must be between zero and one")
        if not isfinite(self.price) or self.price < 0:
            raise ValueError("Price must be finite and nonnegative")


def public_probability(case: PublicCase) -> float:
    return predict(case.history, case.probe, "joint_process")


def oracle_probability(probe: Probe, source: Source) -> float:
    """Upper-information reference; the source process is privileged information."""
    if source.source_id != probe.source_id:
        raise ValueError("Source does not match probe")
    masses = [
        prior * distribution(probe.world, h, source.measurement_accuracy, source.rule)[probe.count]
        for h, prior in ((False, 1 - probe.prior_strong), (True, probe.prior_strong))
    ]
    if sum(masses) <= 0:
        raise ValueError("Report is impossible under the source process")
    return masses[1] / sum(masses)


@dataclass(frozen=True)
class Reporter:
    name: str
    reference: str
    gain: float = 1.0
    offset: float = 0.0
    rounded: bool = False

    def report(self, oracle: float, public: float) -> float:
        p = oracle if self.reference == "oracle" else public
        if self.gain != 1 or self.offset != 0:
            # Endpoint limits are well-defined for these strictly positive gains.
            if 0 < p < 1:
                z = self.gain * (log(p) - log(1 - p)) + self.offset
                p = 1 / (1 + exp(-z)) if z >= 0 else exp(z) / (1 + exp(z))
        return round(p, 2) if self.rounded else p


REPORTERS = (
    Reporter("oracle", "oracle"),
    Reporter("oracle_rounded", "oracle", rounded=True),
    Reporter("public", "public"),
    Reporter("public_rounded", "public", rounded=True),
    Reporter("underconfident", "oracle", gain=0.6),
    Reporter("overconfident", "oracle", gain=1.6),
    Reporter("optimistic", "oracle", offset=0.8),
    Reporter("pessimistic", "oracle", offset=-0.8),
)


def sample_posterior(probability: float, count: int) -> float:
    _probability(probability)
    if type(count) is not int or not 0 <= count <= 5:
        raise ValueError("Panel count must be an integer from zero to five")
    strong = probability * PANEL[1][count]
    return strong / (strong + (1 - probability) * PANEL[0][count])


def _probability(p):
    if not isfinite(p) or not 0 <= p <= 1:
        raise ValueError("Probability must be finite and between zero and one")


def expected_outcome(q: float, report: float, threshold: float, price: float, policy: str):
    """q is the reference conditional probability; report drives all behavior.

    No realized company state or sample can enter assignment or this expectation.
    Actions use the unrounded posterior, with decline on exact payoff ties.
    """
    for p in (q, report, threshold):
        _probability(p)
    buy = choose(policy, report, threshold, price) == "customer_panel"
    before = (q - threshold) * (report > threshold)
    after = sum(
        (q * PANEL[1][k] * (1 - threshold) - (1 - q) * PANEL[0][k] * threshold)
        * (sample_posterior(report, k) > threshold)
        for k in range(6)
    )
    optimal_before = max(0.0, q - threshold)
    optimal_after = sum(
        max(0.0, q * PANEL[1][k] * (1 - threshold) - (1 - q) * PANEL[0][k] * threshold)
        for k in range(6)
    )
    optimal = max(optimal_before, optimal_after - price)
    same_purchase_optimal_actions = optimal_after - price if buy else optimal_before
    net = after - price if buy else before
    return {
        "buy": int(buy),
        "cost": price if buy else 0.0,
        "expected_net": net,
        "expected_gain_over_none": net - before,
        "purchase_regret": optimal - same_purchase_optimal_actions,
        "action_regret": same_purchase_optimal_actions - net,
        "total_regret": optimal - net,
        "starting_excess_brier": (report - q) ** 2,
        "starting_signed_error": report - q,
    }


def realized_outcome(report, threshold, price, policy, *, strong, count):
    """Separate realized ledger, paired with that reporter's own no-check baseline."""
    if type(strong) is not bool:
        raise ValueError("Strong demand must be a boolean")
    revised = sample_posterior(report, count)
    buy = choose(policy, report, threshold, price) == "customer_panel"
    before = (int(strong) - threshold) * (report > threshold)
    net = (int(strong) - threshold) * ((revised if buy else report) > threshold)
    net -= price if buy else 0.0
    return {"realized_net": net, "realized_gain_over_none": net - before}
