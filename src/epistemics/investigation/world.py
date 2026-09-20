"""Bounded projection of the existing discovery world: F, A, K and one source.

Add one explicit transcription offset. Every possible query result is drawn before
the participant acts; branches never resample or select a result after a choice.
"""

from itertools import product

import numpy as np

from epistemics.discovery.models import Analogue, ArchiveRow
from epistemics.discovery.world import GROWTH, SOURCE_STATES, cdf

OFFSETS = np.array([-6.0, 0.0, 6.0])
OFFSET_PRIOR = np.array([1 / 6, 2 / 3, 1 / 6])
STATES = np.array(list(product(range(4), range(2), range(2), range(6), range(3))))
F = GROWTH[STATES[:, 0]]
A, K = STATES[:, 1], STATES[:, 2]
BIAS, SD = SOURCE_STATES[STATES[:, 3]].T
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
    "source_bias_sd_states": SOURCE_STATES.tolist(),
    "priors": "Uniform independent F, A, K and source state; offset independent as below.",
    "transcription_offsets_pct": OFFSETS.tolist(),
    "transcription_offset_probabilities": OFFSET_PRIOR.tolist(),
    "renewal_measurement": "Normal(F - (8 if K=1 else 2)*A + source_bias, source_sd), rounded to 0.1; then add transcription offset C. Correction reveals C, not a new draw.",
    "analogue_measurement": "Normal(F_old - (8 if K=1 else 2)*A_old, 3), rounded to 0.1.",
    "archive_errors": "Normal(source_bias, source_sd), rounded to 0.1; no transcription error.",
    "source_audit": "A new independent archive error is below -2 percentage points; same source state. Binary observation of an unrounded error.",
    "operations_check": "An independent backlog reading Normal(12+20*A, 6) exceeds 22.",
    "segment_check": "An independent unaffected-cohort reading Normal(F, 1.8) exceeds 12.",
    "calculation": "Display current reported figure + 2; deterministic, no new measurement.",
    "target": "Next-year growth Normal(F, 2) exceeds 12; unrounded outcome.",
    "dependence": "Archive, analogue, operating, query and outcome noises are conditionally independent given their shared latent variables. Documents derived from a reading add no likelihood.",
}


def generate(seed):
    rng = np.random.default_rng(seed)
    f = float(rng.choice(GROWTH))
    a, k = (int(rng.integers(2)) for _ in range(2))
    bias, sd = SOURCE_STATES[int(rng.integers(6))]
    offset = float(rng.choice(OFFSETS, p=OFFSET_PRIOR))
    archive = []
    for i in range(2):
        actual = float(rng.choice(GROWTH))
        archive.append(
            ArchiveRow(
                case_id=f"archive-{i}",
                audited_pct=actual,
                reported_pct=round(actual + rng.normal(bias, sd), 1),
            )
        )
    analogues = []
    for i, old_a in enumerate((0, 1)):
        old_f = float(rng.choice(GROWTH))
        analogues.append(
            Analogue(
                case_id=f"analogue-{i}",
                underlying_growth_pct=old_f,
                rollout_disruption=bool(old_a),
                backlog_score=round(float(rng.normal(12 + 20 * old_a, 6)), 1),
                renewal_growth_pct=round(
                    old_f - (8 if k else 2) * old_a + float(rng.normal(0, 3)), 1
                ),
            )
        )
    measurement = round(f - (8 if k else 2) * a + float(rng.normal(bias, sd)), 1)
    queries = {
        "source_audit": bool(rng.normal(bias, sd) < -2),
        "operations_check": bool(rng.normal(12 + 20 * a, 6) > 22),
        "segment_check": bool(rng.normal(f, 1.8) > 12),
    }
    growth = float(rng.normal(f, 2))
    return {
        "archive": [r.model_dump() for r in archive],
        "analogues": [r.model_dump() for r in analogues],
        "reported_growth_pct": round(measurement + offset, 1),
        "correction_offset_pct": offset,
        "queries": queries,
        "truth": {
            "fundamentals": f,
            "disruption": a,
            "relationship": k,
            "source_bias": float(bias),
            "source_sd": float(sd),
            "realized_growth_pct": growth,
            "growth_event": growth > 12,
        },
    }
