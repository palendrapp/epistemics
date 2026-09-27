"""Synthetic validation bound to the implementation fingerprint.

Passing requires: every audited dossier pair matches its ledger; complete simulated collections
through the real service in every arm; and panel neglect estimates within tolerance of the
known synthetic weights. It validates measurement machinery, not any respondent.
"""

import tempfile
from pathlib import Path

from epistemics.research_world.analysis import panel
from epistemics.research_world.collection import fingerprint
from epistemics.research_world.design import design
from epistemics.research_world.extract import audit
from epistemics.research_world.presentation import ARMS
from epistemics.research_world.render import render
from epistemics.research_world.simulation import simulate
from epistemics.research_world.world import PAIRS, generate

TOLERANCE = 0.15


def validate(seed, audited_seeds=500, worlds_per_family=12):
    for s in range(seed, seed + audited_seeds):
        for family in PAIRS:
            worlds = generate(s, family)
            audit(worlds, {p: render(w) for p, w in worlds.items()})
    contexts = design(seed, worlds_per_family, worlds_per_family // 2, 1, check_offered=True)
    truths = dict(zip(ARMS, (1.0, 0.5, 0.0), strict=True))
    estimates = {}
    with tempfile.TemporaryDirectory() as tmp:
        for arm, chi in truths.items():
            reports = [
                simulate(
                    Path(tmp) / f"{arm}-{i}",
                    c["items"],
                    arm=arm,
                    check_offered=True,
                    chi=chi,
                    noise_sd=0.02,
                    seed=seed + i,
                )
                for i, c in enumerate(contexts)
            ]
            estimates.update(panel(reports))
    recovered = {
        key: abs(value["chi"] - truths[key.split("/")[0]]) <= TOLERANCE
        for key, value in estimates.items()
    }
    return {
        "schema_version": "epistemics.research-world-validation.v1",
        "seed": seed,
        "implementation_sha256": fingerprint(),
        "audited_pairs": audited_seeds * len(PAIRS),
        "contexts_per_arm": len(contexts),
        "true_neglect_by_arm": truths,
        "estimates": estimates,
        "recovered": recovered,
        "passed": len(recovered) == len(ARMS) * len(PAIRS) and all(recovered.values()),
        "scope": "Ledger audit, complete synthetic collections through the service with priced checks, and cross-context neglect recovery at 2-point report noise; no respondent behavior is validated",
    }
