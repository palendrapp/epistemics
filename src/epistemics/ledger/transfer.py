"""Transfer from the formal description modules to realistic dossiers with the same items.

For each configuration and module, the formal mapping is the mean implied prior per description
level over its random-order set-A sessions, and the dossier mapping is the same over its dossier
sessions. The predictive test scores each dossier probe and forecast against the probability an
exact observer (sensitivity 1, no bias) predicts from three candidate priors: the configuration's
own formal mapping, the mapping pooled over configurations, and 50% at every level.
"""

import numpy as np

from epistemics.dispositions import design, observers
from epistemics.dispositions.response import sigmoid
from epistemics.ledger.dispositions import spearman

PAIRS = {
    "relay": ("corroboration-cues", "corroboration-dossier"),
    "disclosure": ("disclosure-cues", "disclosure-dossier"),
}
ITEMS = {"relay": design.corroboration_cues, "disclosure": design.disclosure_cues}
OBSERVERS = {"relay": observers.corroboration, "disclosure": observers.disclosure}


def predicted(module, priors):
    items = ITEMS[module]()
    return sigmoid(observers.cue_observer(OBSERVERS[module], items, priors, 1.0)), items


def mean_absolute_error(module, priors, record):
    """Mean |predicted − reported| over the dossier's probes and forecasts (not base rates)."""
    probabilities, items = predicted(module, priors)
    evidence = items["kind"] != "rate"
    reported = np.array(record["responses"], dtype=float)
    return float(np.mean(np.abs(probabilities[evidence] - reported[evidence])))


def analyse(records, variant="cues-a"):
    """records: verified extraction records from any roots (formal and dossier)."""
    formal, dossier = {}, {}
    for r in records:
        if not r.get("verified") or r.get("slot_fits") is None:
            continue
        implied = [s["implied"]["mean"] for s in r["slot_fits"]]
        stated = [s["stated"][0] for s in r["slot_fits"]]
        for module, (formal_module, dossier_module) in PAIRS.items():
            key = (r["configuration"], module)
            if (
                r["module"] == formal_module
                and r["variant"] == variant
                and r.get("order_policy", "random") == "random"
            ):
                formal.setdefault(key, []).append((implied, stated))
            elif r["module"] == dossier_module:
                dossier.setdefault(key, []).append((implied, stated, r))
    pooled = {}
    for module in PAIRS:
        rows = [np.mean([i for i, _ in v], axis=0) for (c, m), v in formal.items() if m == module]
        if rows:
            pooled[module] = np.mean(rows, axis=0)
    result = {}
    for (config, module), sessions in sorted(dossier.items()):
        if (config, module) not in formal:
            continue
        own = np.mean([i for i, _ in formal[(config, module)]], axis=0)
        own_stated = np.mean([s for _, s in formal[(config, module)]], axis=0)
        implied = np.mean([i for i, _, _ in sessions], axis=0)
        stated = np.mean([s for _, s, _ in sessions], axis=0)
        errors = {
            name: float(np.mean([mean_absolute_error(module, priors, r) for _, _, r in sessions]))
            for name, priors in (
                ("own_formal", own),
                ("pooled_formal", pooled[module]),
                ("neutral", np.full(len(own), 0.5)),
            )
        }
        result[f"{config}/{module}"] = {
            "formal_sessions": len(formal[(config, module)]),
            "dossier_sessions": len(sessions),
            "formal_mapping": own.tolist(),
            "dossier_mapping": implied.tolist(),
            "mapping_mae": float(np.mean(np.abs(implied - own))),
            "mapping_rank_agreement": spearman(own, implied),
            "stated_mae": float(np.mean(np.abs(stated - own_stated))),
            "prediction_mae": errors,
            "gain_over_neutral": errors["neutral"] - errors["own_formal"],
            "gain_over_pooled": errors["pooled_formal"] - errors["own_formal"],
        }
    return result
