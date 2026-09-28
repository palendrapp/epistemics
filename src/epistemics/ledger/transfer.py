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
UNPROMPTED = {"relay": "corroboration-unprompted", "disclosure": "disclosure-unprompted"}
UNPROMPTED_ITEMS = {
    "relay": design.corroboration_unprompted,
    "disclosure": design.disclosure_unprompted,
}
OBSERVERS = {"relay": observers.corroboration, "disclosure": observers.disclosure}


def predicted(module, priors, items=None):
    items = ITEMS[module]() if items is None else items
    return sigmoid(observers.cue_observer(OBSERVERS[module], items, priors, 1.0)), items


def mean_absolute_error(module, priors, record, items=None):
    """Mean |predicted − reported| over the dossier's probes and forecasts (not base rates)."""
    probabilities, items = predicted(module, priors, items)
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
        if not all(s["stated"] for s in r["slot_fits"]):
            continue  # Unprompted sessions: see noticing().
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


def noticing(records):
    """Unprompted dossiers (no mechanism stated) against the prompted dossiers, same descriptions.

    Per configuration and module: both mappings, the suggestive-minus-reassuring range, the
    irrelevant level, per-session unprompted mappings with their lower 90% bounds, and the error of
    predicting the unprompted forecasts from the prompted mapping, from full neglect (no relays or
    selective senders at any level) and from indifference (50% at every level).

    Salience sessions ("named-a": the same dossiers plus one sentence naming the mechanism without
    its rate) are reported beside them under "named", with the unprompted mapping as a further
    candidate prior.
    """
    prompted, unprompted, named = {}, {}, {}
    for r in records:
        if not r.get("verified") or r.get("slot_fits") is None:
            continue
        implied = [s["implied"]["mean"] for s in r["slot_fits"]]
        for module in PAIRS:
            key = (r["configuration"], module)
            if r["module"] == PAIRS[module][1]:
                prompted.setdefault(key, []).append(implied)
            elif r["module"] == UNPROMPTED[module]:
                lower = [s["implied"]["interval_90"][0] for s in r["slot_fits"]]
                target = named if r.get("variant") == "named-a" else unprompted
                target.setdefault(key, []).append((implied, lower, r))
    result = {}
    for (config, module), sessions in sorted(unprompted.items()):
        mapping = np.mean([i for i, _, _ in sessions], axis=0)
        row = {
            "unprompted_sessions": len(sessions),
            "unprompted_mapping": mapping.tolist(),
            "unprompted_range": float(mapping[-1] - mapping[0]),
            "unprompted_irrelevant": float(mapping[2]),
            "sessions": [
                {"run_id": r["run_id"], "implied": i, "lower_90": lo} for i, lo, r in sessions
            ],
        }
        items = UNPROMPTED_ITEMS[module]()
        candidates = {"neglect": np.zeros(5), "indifference": np.full(5, 0.5)}
        if (config, module) in prompted:
            reference = np.mean(prompted[(config, module)], axis=0)
            row |= {
                "prompted_sessions": len(prompted[(config, module)]),
                "prompted_mapping": reference.tolist(),
                "prompted_range": float(reference[-1] - reference[0]),
                "prompted_irrelevant": float(reference[2]),
            }
            candidates["prompted"] = reference
        row["prediction_mae"] = {
            name: float(
                np.mean([mean_absolute_error(module, priors, r, items) for _, _, r in sessions])
            )
            for name, priors in candidates.items()
        }
        if (config, module) in named:
            given = named[(config, module)]
            mapping_named = np.mean([i for i, _, _ in given], axis=0)
            candidates["unprompted"] = mapping
            row["named"] = {
                "sessions": len(given),
                "mapping": mapping_named.tolist(),
                "range": float(mapping_named[-1] - mapping_named[0]),
                "irrelevant": float(mapping_named[2]),
                "to_prompted_mae": float(np.mean(np.abs(mapping_named - candidates["prompted"])))
                if "prompted" in candidates
                else None,
                "to_unprompted_mae": float(np.mean(np.abs(mapping_named - mapping))),
                "per_session": [
                    {"run_id": r["run_id"], "implied": i, "lower_90": lo} for i, lo, r in given
                ],
                "prediction_mae": {
                    name: float(
                        np.mean(
                            [mean_absolute_error(module, priors, r, items) for _, _, r in given]
                        )
                    )
                    for name, priors in candidates.items()
                },
            }
        result[f"{config}/{module}"] = row
    return result
