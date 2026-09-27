"""Fixed item designs for the first three identification modules (T2, T3, T5).

Each module has 24 checkpoints. Forecast designs use only forecasts. Probe designs replace six
of the most redundant forecasts with structure probes (relay, selective sender), so the two
designs can be compared at equal length.
"""

import numpy as np

# Wording cues: relayed reports reuse the original's wording at the first rate, independent
# reports at the second. Identical wording has log LR log(x / y); different, log((1-x)/(1-y)).
CUE_RATES = {"strong": (0.9, 0.1), "moderate": (0.8, 0.2), "weak": (2 / 3, 1 / 3)}
CUES = {
    **{f"{name}_identical": float(np.log(x / y)) for name, (x, y) in CUE_RATES.items()},
    **{f"{name}_different": float(np.log((1 - x) / (1 - y))) for name, (x, y) in CUE_RATES.items()},
    "none": 0.0,
}

# kind, prior, accuracy_a, report_a, accuracy_b, report_b, cue
_SINGLE = [
    ("single", 0.5, 0.65, 1, 0.5, 0, "none"),
    ("single", 0.5, 0.8, -1, 0.5, 0, "none"),
    ("single", 0.3, 0.7, 1, 0.5, 0, "none"),
    ("single", 0.7, 0.7, -1, 0.5, 0, "none"),
]
# A relay cannot contradict its source, so conflicting pairs are independent whatever the cue.
_CONFLICT = [
    ("pair", 0.5, 0.8, 1, 0.65, -1, "strong_identical"),
    ("pair", 0.5, 0.65, -1, 0.8, 1, "moderate_different"),
    ("pair", 0.4, 0.75, 1, 0.75, -1, "moderate_identical"),
    ("pair", 0.6, 0.7, -1, 0.7, 1, "none"),
]
_MATCHING_CUES = [
    "strong_identical",
    "moderate_identical",
    "weak_identical",
    "none",
    "none",
    "weak_different",
    "moderate_different",
    "strong_different",
]
# Priors lean against the reports so relay and independent readings sit either side of 50%.
_MATCHING = [
    ("pair", prior, 0.75, r, 0.85, r, cue)
    for r, prior in ((1, 0.35), (-1, 0.65))
    for cue in _MATCHING_CUES
]
_PROBE_CUES = [
    ("moderate_identical", 1),
    ("weak_identical", -1),
    ("none", 1),
    ("none", -1),
    ("weak_different", 1),
    ("moderate_different", -1),
]
_CORROBORATION_PROBES = [("probe", 0.5, 0.75, r, 0.85, r, cue) for cue, r in _PROBE_CUES]
_KEPT_MATCHING = {
    "strong_identical",
    "moderate_identical",
    "none",
    "moderate_different",
    "strong_different",
}

# kind, prior, good, omission, shared_good, shared_bad, withheld
_SELECTIVE_PRIORS = {(3, 1): 0.3, (2, 2): 0.4, (1, 3): 0.5, (0, 4): 0.8}
_INFORMATIVE = [
    ("forecast", _SELECTIVE_PRIORS[(m, k)] if g == 0.75 else 0.5, g, rate, m, 0, k)
    for g in (0.75, 0.65)
    for rate in (0.25, 0.5)
    for m, k in _SELECTIVE_PRIORS
]
# Sharing a bad item shows the sender is not selective, so its omissions carry no signal.
_CONTROLS = [
    ("forecast", 0.5, 0.75, 0.25, 3, 1, 0),
    ("forecast", 0.5, 0.7, 0.25, 1, 3, 0),
    ("forecast", 0.7, 0.75, 0.25, 2, 2, 0),
    ("forecast", 0.3, 0.65, 0.25, 4, 0, 0),
    ("forecast", 0.5, 0.75, 0.5, 2, 1, 1),
    ("forecast", 0.5, 0.75, 0.25, 1, 1, 2),
    ("forecast", 0.6, 0.65, 0.25, 2, 1, 1),
    ("forecast", 0.6, 0.7, 0.5, 1, 2, 1),
]
_DISCLOSURE_PROBES = [
    ("probe", 0.5, 0.7, rate, m, 0, k)
    for rate, (m, k) in (
        (0.5, (3, 1)),
        (0.25, (2, 2)),
        (0.5, (2, 2)),
        (0.25, (1, 3)),
        (0.5, (1, 3)),
        (0.5, (0, 4)),
    )
]

# prior, high, low, gain, loss. Investing pays gain or loses loss; the threshold is
# loss / (gain + loss). Four groups of six: zero decision value with outcomes on both sides of
# 50%; zero decision value with outcomes on one side; positive decision value; and strong
# checks with zero decision value.
_CHECKS = [
    # Zero decision value, outcomes straddle 50%.
    (0.5, 0.65, 0.35, 30, 70),
    (0.45, 0.6, 0.3, 30, 70),
    (0.55, 0.68, 0.4, 30, 70),
    (0.5, 0.65, 0.35, 70, 30),
    (0.55, 0.7, 0.4, 70, 30),
    (0.45, 0.6, 0.32, 70, 30),
    # Zero decision value, outcomes on one side of 50%.
    (0.8, 0.9, 0.6, 50, 50),
    (0.2, 0.4, 0.1, 50, 50),
    (0.85, 0.95, 0.7, 50, 50),
    (0.75, 0.97, 0.52, 50, 50),
    (0.25, 0.48, 0.03, 50, 50),
    (0.8, 0.96, 0.55, 70, 30),
    # Positive decision value.
    (0.55, 0.8, 0.3, 50, 50),
    (0.4, 0.7, 0.2, 50, 50),
    (0.35, 0.6, 0.15, 70, 30),
    (0.65, 0.85, 0.45, 30, 70),
    (0.5, 0.9, 0.1, 30, 70),
    (0.5, 0.75, 0.25, 50, 50),
    # Strong checks, zero decision value.
    (0.6, 0.95, 0.35, 70, 30),
    (0.4, 0.65, 0.05, 30, 70),
    (0.65, 0.97, 0.4, 70, 30),
    (0.85, 0.99, 0.6, 50, 50),
    (0.15, 0.4, 0.01, 50, 50),
    (0.75, 0.98, 0.55, 70, 30),
]


def columns(rows, names):
    table = {name: np.array([row[i] for row in rows]) for i, name in enumerate(names)}
    for name, values in table.items():
        if values.dtype.kind in "iu" and name not in {"shared_good", "shared_bad", "withheld"}:
            table[name] = values.astype(float)
    return table


def _corroboration(rows):
    table = columns(
        rows, ("kind", "prior", "accuracy_a", "report_a", "accuracy_b", "report_b", "cue")
    )
    table["cue"] = np.array([CUES[c] for c in table["cue"]])
    return table


def _disclosure(rows):
    return columns(
        rows, ("kind", "prior", "good", "omission", "shared_good", "shared_bad", "withheld")
    )


def corroboration(probes=False):
    if not probes:
        return _corroboration(_SINGLE + _CONFLICT + _MATCHING)
    kept = {}
    for row in _MATCHING:
        if row[-1] in _KEPT_MATCHING:
            kept.setdefault((row[3], row[-1]), row)  # One uninformative-cue pair per direction.
    return _corroboration(_SINGLE + _CONFLICT + list(kept.values()) + _CORROBORATION_PROBES)


def disclosure(probes=False):
    if not probes:
        return _disclosure(_INFORMATIVE + _CONTROLS)
    kept = [row for row in _INFORMATIVE if row[2] == 0.75]
    kept += [row for row in _INFORMATIVE if row[2] == 0.65 and row[3] == 0.5 and row[6] in (2, 3)]
    return _disclosure(kept + _CONTROLS + _DISCLOSURE_PROBES)


def checks():
    return columns(_CHECKS, ("prior", "high", "low", "gain", "loss"))
