"""Independent case marginals; price-pair selection uses visible evidence only."""

from itertools import product

import numpy as np

from epistemics.discovery.world import GROWTH, cdf
from epistemics.investigation.world import generate as generate_original

SOURCES = np.array(list(product((-6.0, -3.0, 0.0, 3.0, 6.0), (1.5, 4.0))))
OFFSETS = np.array([-6.0, 0.0, 6.0])
STATES = np.array(list(product(range(4), range(2), range(2), range(10), range(3))))
F = GROWTH[STATES[:, 0]]
A, K, S = STATES[:, 1], STATES[:, 2], STATES[:, 3]
BIAS, SD = SOURCES[S].T
C = OFFSETS[STATES[:, 4]]
RENEWAL = F - np.where(K == 1, 8, 2) * A
TARGET = cdf((F - 12) / 2)
EVENTS = {
    "source_audit": cdf((-2 - BIAS) / SD),
    "operations_check": cdf((12 + 20 * A - 22) / 6),
    "segment_check": cdf((F - 12) / 1.8),
}

ASSUMPTIONS = {
    "fundamentals_growth_grid_pct": GROWTH.tolist(),
    "source_bias_sd_states": SOURCES.tolist(),
    "priors": "Independent uniform F, disruption, relationship and source states. Unchecked transcription offsets -6, 0, +6 have equal marginal probability per independent episode. Checked cases have offset zero.",
    "measurement": "Rounded Normal(F - (8 if strong relationship else 2)*disruption + source_bias, source_sd), plus offset. Review reveals the same measurement's offset.",
    "archive": "Rounded Normal(source_bias, source_sd) errors; no transcription error.",
    "analogues": "Rounded Normal(F_old - (8 if strong else 2)*disruption_old, 3); backlog Normal(12+20*disruption_old, 6).",
    "queries": "Source audit: independent Normal(bias,sd) error below -2. Backlog: Normal(12+20*disruption,6)>22. Cohort: Normal(F,1.8)>12.",
    "outcome": "Independent Normal(F,2)>12, conditional on shared F.",
    "selection": "Research cases have checked transcription and are selected on visible archives, analogues and operating estimate only. Selection adds no likelihood after conditioning on that full public record. Prices do not depend on hidden states or branch results.",
}


def generate(seed, offset):
    # Preserve the analogue generator, while deliberately widening source support
    # in this new version. Use a separate reproducible stream for new measurements.
    world = generate_original(seed)
    rng = np.random.default_rng(np.random.SeedSequence([seed, 2]))
    bias, sd = SOURCES[int(rng.integers(len(SOURCES)))]
    f = world["truth"]["fundamentals"]
    a, k = world["truth"]["disruption"], world["truth"]["relationship"]
    for row in world["archive"]:
        row["reported_pct"] = round(row["audited_pct"] + float(rng.normal(bias, sd)), 1)
    original = round(f - (8 if k else 2) * a + float(rng.normal(bias, sd)), 1)
    world["reported_growth_pct"] = round(original + offset, 1)
    world["correction_offset_pct"] = float(offset)
    world["queries"] = {
        "source_audit": bool(rng.normal(bias, sd) < -2),
        "operations_check": bool(rng.normal(12 + 20 * a, 6) > 22),
        "segment_check": bool(rng.normal(f, 1.8) > 12),
    }
    growth = float(rng.normal(f, 2))
    world["truth"].update(
        source_bias=float(bias),
        source_sd=float(sd),
        realized_growth_pct=growth,
        growth_event=growth > 12,
    )
    return world
