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
# Their cues never claim identical wording, which would describe an impossible story.
_CONFLICT = [
    ("pair", 0.5, 0.8, 1, 0.65, -1, "strong_different"),
    ("pair", 0.5, 0.65, -1, 0.8, 1, "moderate_different"),
    ("pair", 0.4, 0.75, 1, 0.75, -1, "weak_different"),
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
# checks with zero decision value. Every stated prior is the whole-percentage mixture of the two
# stated posteriors, so the chance of a positive result is itself a whole percentage. Decision
# values are whole points, so the optimal whole-point price (the floor of the value) equals the
# nearest whole point for a respondent who values checks only for their decision value.
_CHECKS = [
    # Zero decision value, outcomes straddle 50%.
    (0.5, 0.65, 0.35, 30, 70),
    (0.45, 0.6, 0.3, 30, 70),
    (0.54, 0.68, 0.4, 30, 70),
    (0.5, 0.65, 0.35, 70, 30),
    (0.55, 0.7, 0.4, 70, 30),
    (0.46, 0.6, 0.32, 70, 30),
    # Zero decision value, outcomes on one side of 50%.
    (0.78, 0.9, 0.6, 50, 50),
    (0.22, 0.4, 0.1, 50, 50),
    (0.85, 0.95, 0.7, 50, 50),
    (0.75, 0.97, 0.53, 50, 50),
    (0.25, 0.48, 0.02, 50, 50),
    (0.8, 0.96, 0.56, 70, 30),
    # Positive decision value.
    (0.55, 0.8, 0.3, 50, 50),
    (0.4, 0.7, 0.2, 50, 50),
    (0.35, 0.6, 0.1, 70, 30),
    (0.65, 0.86, 0.44, 30, 70),
    (0.5, 0.9, 0.1, 30, 70),
    (0.5, 0.76, 0.24, 50, 50),
    # Strong checks, zero decision value.
    (0.65, 0.95, 0.35, 70, 30),
    (0.41, 0.65, 0.05, 30, 70),
    (0.68, 0.97, 0.39, 70, 30),
    (0.8, 0.99, 0.61, 50, 50),
    (0.2, 0.39, 0.01, 50, 50),
    (0.75, 0.98, 0.52, 70, 30),
]


def columns(rows, names):
    table = {name: np.array([row[i] for row in rows]) for i, name in enumerate(names)}
    for name, values in table.items():
        if values.dtype.kind in "iu" and name not in {
            "shared_good",
            "shared_bad",
            "withheld",
            "slot",
        }:
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


# Cue modules. Five description levels (slots), from strongly reassuring to strongly suggestive,
# with an irrelevant description in the middle. Each slot has a stated base-rate question
# ("rate"), a structure probe and two forecasts; four anchors carry no description and fix
# evidence sensitivity, bias and noise.
CUE_LEVELS = (
    "strong-reassuring",
    "mild-reassuring",
    "irrelevant",
    "mild-suggestive",
    "strong-suggestive",
)


def _relay_slot(slot):
    r = 1 if slot % 2 == 0 else -1
    prior = 0.35 if r > 0 else 0.65
    return [
        ("rate", 0.5, 0.75, r, 0.85, r, "none", slot),
        ("probe", 0.5, 0.75, r, 0.85, r, "none", slot),
        ("pair", prior, 0.75, r, 0.85, r, "none", slot),
        ("pair", 1 - prior, 0.75, -r, 0.85, -r, "weak_different", slot),
    ]


_RELAY_ANCHORS = [
    ("single", 0.5, 0.65, 1, 0.5, 0, "none", -1),
    ("single", 0.3, 0.7, 1, 0.5, 0, "none", -1),
    ("pair", 0.5, 0.8, 1, 0.65, -1, "strong_different", -1),
    ("pair", 0.6, 0.7, -1, 0.7, 1, "none", -1),
]


def _disclosure_slot(slot):
    return [
        ("rate", 0.5, 0.75, 0.5, 0, 0, 4, slot),
        ("probe", 0.5, 0.75, 0.5, 2, 0, 2, slot),
        ("forecast", 0.3, 0.75, 0.5, 3, 0, 1, slot),
        ("forecast", 0.5, 0.75, 0.5, 1, 0, 3, slot),
    ]


_DISCLOSURE_ANCHORS = [
    ("forecast", 0.5, 0.75, 0.25, 3, 1, 0, -1),
    ("forecast", 0.3, 0.65, 0.25, 4, 0, 0, -1),
    ("forecast", 0.5, 0.75, 0.5, 2, 1, 1, -1),
    ("forecast", 0.5, 0.75, 0.25, 1, 1, 2, -1),
]


def corroboration_cues():
    rows = [row for s in range(len(CUE_LEVELS)) for row in _relay_slot(s)] + _RELAY_ANCHORS
    table = columns(
        rows, ("kind", "prior", "accuracy_a", "report_a", "accuracy_b", "report_b", "cue", "slot")
    )
    table["cue"] = np.array([CUES[c] for c in table["cue"]])
    return table


def disclosure_cues():
    rows = [row for s in range(len(CUE_LEVELS)) for row in _disclosure_slot(s)]
    return columns(
        rows + _DISCLOSURE_ANCHORS,
        ("kind", "prior", "good", "omission", "shared_good", "shared_bad", "withheld", "slot"),
    )


# Relative-judgement module (relay). Five fixed target descriptions (slots 0-4: two mildly
# reassuring, the irrelevant one, two mildly suggestive) are judged after a comparison set of
# three outlets (slots 5-7) that is either all strongly reassuring or all strongly suggestive.
# Targets get a base-rate question, a probe and a forecast; comparisons a base-rate question and
# a probe; three anchors carry no description.
RANGE_TARGETS = 5
RANGE_COMPARISONS = 3


def _range_target(slot):
    r = 1 if slot % 2 == 0 else -1
    prior = 0.35 if r > 0 else 0.65
    return [
        ("rate", 0.5, 0.75, r, 0.85, r, "none", slot),
        ("probe", 0.5, 0.75, r, 0.85, r, "none", slot),
        ("pair", prior, 0.75, r, 0.85, r, "none", slot),
    ]


def _range_comparison(slot):
    r = 1 if slot % 2 == 0 else -1
    return [
        ("rate", 0.5, 0.75, r, 0.85, r, "none", slot),
        ("probe", 0.5, 0.75, r, 0.85, r, "none", slot),
    ]


def corroboration_range():
    rows = [row for s in range(RANGE_TARGETS) for row in _range_target(s)]
    rows += [
        row
        for s in range(RANGE_TARGETS, RANGE_TARGETS + RANGE_COMPARISONS)
        for row in _range_comparison(s)
    ]
    rows += _RELAY_ANCHORS[:3]
    table = columns(
        rows, ("kind", "prior", "accuracy_a", "report_a", "accuracy_b", "report_b", "cue", "slot")
    )
    table["cue"] = np.array([CUES[c] for c in table["cue"]])
    return table


# Unprompted dossiers: the description modules without the mechanism. Forecasts only: no stated
# base-rate questions, no structure probes and no wording cues, so a relay or a selective sender is
# never named. Each description level has four forecasts whose relay (selective) and independent
# (random) readings differ; the anchors, which no relay or selective sender can explain, fix
# sensitivity, bias and noise. An implied prior of zero at every level is full neglect.
def _relay_unprompted_slot(slot):
    # Accurate second outlets and priors leaning against the reports spread the relay and
    # independent readings (a relay leaves only the first outlet's evidence).
    return [
        ("pair", 0.3, 0.75, 1, 0.9, 1, "none", slot),
        ("pair", 0.7, 0.75, -1, 0.9, -1, "none", slot),
        ("pair", 0.25, 0.7, 1, 0.95, 1, "none", slot),
        ("pair", 0.75, 0.7, -1, 0.95, -1, "none", slot),
    ]


_RELAY_UNPROMPTED_ANCHORS = [
    ("single", 0.5, 0.65, 1, 0.5, 0, "none", -1),
    ("single", 0.3, 0.7, 1, 0.5, 0, "none", -1),
    ("pair", 0.5, 0.8, 1, 0.65, -1, "none", -1),
    ("pair", 0.6, 0.7, -1, 0.7, 1, "none", -1),
]


def _disclosure_unprompted_slot(slot):
    return [
        ("forecast", 0.3, 0.75, 0.5, 3, 0, 1, slot),
        ("forecast", 0.5, 0.75, 0.5, 2, 0, 2, slot),
        ("forecast", 0.5, 0.75, 0.5, 1, 0, 3, slot),
        ("forecast", 0.7, 0.75, 0.5, 0, 0, 4, slot),
    ]


def corroboration_unprompted():
    rows = [row for s in range(len(CUE_LEVELS)) for row in _relay_unprompted_slot(s)]
    table = columns(
        rows + _RELAY_UNPROMPTED_ANCHORS,
        ("kind", "prior", "accuracy_a", "report_a", "accuracy_b", "report_b", "cue", "slot"),
    )
    table["cue"] = np.array([CUES[c] for c in table["cue"]])
    return table


def disclosure_unprompted():
    rows = [row for s in range(len(CUE_LEVELS)) for row in _disclosure_unprompted_slot(s)]
    return columns(
        rows + _DISCLOSURE_ANCHORS,
        ("kind", "prior", "good", "omission", "shared_good", "shared_bad", "withheld", "slot"),
    )


# Asked dossiers (default induction): the unprompted forecasts, three per description level,
# plus that level's stated base-rate question, as in the description modules. The implied prior
# is still fitted from forecasts only, so asking for the rate can be compared with applying it.
def corroboration_asked():
    rows = [
        row
        for s in range(len(CUE_LEVELS))
        # The three most informative of the four forecasts (recovery correlation 0.93 on three
        # pilot seeds, against 0.92 for the first three).
        for row in [("rate", 0.5, 0.75, 1, 0.85, 1, "none", s), *_relay_unprompted_slot(s)[1:]]
    ]
    table = columns(
        rows + _RELAY_UNPROMPTED_ANCHORS,
        ("kind", "prior", "accuracy_a", "report_a", "accuracy_b", "report_b", "cue", "slot"),
    )
    table["cue"] = np.array([CUES[c] for c in table["cue"]])
    return table


def disclosure_asked():
    rows = [
        row
        for s in range(len(CUE_LEVELS))
        for row in [("rate", 0.5, 0.75, 0.5, 0, 0, 4, s), *_disclosure_unprompted_slot(s)[:3]]
    ]
    return columns(
        rows + _DISCLOSURE_ANCHORS,
        ("kind", "prior", "good", "omission", "shared_good", "shared_bad", "withheld", "slot"),
    )


# Probed dossiers: the asked relay design with each level's structure probe added, which leaves
# two forecasts per level. The probe asks whether the second outlet relayed the first.
def corroboration_probed():
    rows = []
    for s in range(len(CUE_LEVELS)):
        r = 1 if s % 2 == 0 else -1
        rows += [
            ("rate", 0.5, 0.75, 1, 0.85, 1, "none", s),
            ("probe", 0.5, 0.75, r, 0.9, r, "none", s),
            *_relay_unprompted_slot(s)[2:],
        ]
    table = columns(
        rows + _RELAY_UNPROMPTED_ANCHORS,
        ("kind", "prior", "accuracy_a", "report_a", "accuracy_b", "report_b", "cue", "slot"),
    )
    table["cue"] = np.array([CUES[c] for c in table["cue"]])
    return table


# Abstract urn tasks. Copying and selection reuse the relay and disclosure designs above; the third
# structure, mismatch (a reading filed under the wrong urn), has its own. Each description level
# has sensor readings whose weight depends on the mismatch prior; the anchors are the respondent's
# own draws, which cannot be misfiled.
# kind, prior, accuracy_a, report_a, slot
_MISMATCH_FORECASTS = [
    ("single", 0.3, 0.9, 1),
    ("single", 0.7, 0.9, -1),
    ("single", 0.25, 0.95, 1),
    ("single", 0.75, 0.95, -1),
]
_MISMATCH_ANCHORS = [
    ("own", 0.5, 0.65, 1, -1),
    ("own", 0.3, 0.7, 1, -1),
    ("own", 0.5, 0.8, -1, -1),
    ("own", 0.6, 0.7, 1, -1),
]
MISMATCH_COLUMNS = ("kind", "prior", "accuracy_a", "report_a", "slot")


def _mismatch(rows):
    return columns(rows, MISMATCH_COLUMNS)


def mismatch_urn():
    """Forecast-only: four sensor readings per level and four own-draw anchors."""
    rows = [(*row, s) for s in range(len(CUE_LEVELS)) for row in _MISMATCH_FORECASTS]
    return _mismatch(rows + _MISMATCH_ANCHORS)


def mismatch_urn_asked():
    """Each level's stated base-rate question and three readings."""
    rows = [
        row
        for s in range(len(CUE_LEVELS))
        for row in [("rate", 0.5, 0.9, 1, s), *[(*f, s) for f in _MISMATCH_FORECASTS[1:]]]
    ]
    return _mismatch(rows + _MISMATCH_ANCHORS)


def mismatch_urn_probed():
    """Each level's base-rate question, structure probe and two readings."""
    rows = []
    for s in range(len(CUE_LEVELS)):
        r = 1 if s % 2 == 0 else -1
        rows += [
            ("rate", 0.5, 0.9, 1, s),
            ("probe", 0.5, 0.9, r, s),
            *[(*f, s) for f in _MISMATCH_FORECASTS[2:]],
        ]
    return _mismatch(rows + _MISMATCH_ANCHORS)


# Capacity battery, Part A (design 0.9): fully specified cases, mechanism and rates stated, whose
# exact answer needs more computation as the number of readings grows (docs/capacity-battery-
# design.md). Seven cases at each of three load levels, then one repeat per level: the same
# numbers under new names, which measures response noise without the model. Each case must
# separate the exact answer from neglecting the structure by at least 0.25 on the log-odds scale,
# and keep the exact answer within 5-95%.
LOAD_READINGS = {"dependence": (2, 4, 8), "mismatch": (1, 3, 6)}
LOAD_WIDTH = {"dependence": 8, "mismatch": 6}
_LOAD_SEEDS = {"dependence": 20261003, "mismatch": 20261004}
_LOAD_COPIERS = {2: 1, 4: 2, 8: 3}


def _load_case(model, rng, n):
    prior = float(rng.choice([0.3, 0.4, 0.5, 0.6, 0.7]))
    rep = rng.choice([-1, 1], n)
    if model == "dependence":
        acc = rng.choice([0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9], n)
        src, rate = np.full(n, -1), np.zeros(n)
        for idx in sorted(rng.choice(np.arange(1, n), _LOAD_COPIERS[n], replace=False)):
            src[idx] = int(rng.integers(0, idx))
            rate[idx] = float(rng.choice([0.2, 0.3, 0.4, 0.5, 0.6]))
        return {"prior": prior, "acc": acc, "rep": rep, "src": src, "rate": rate}
    acc = rng.choice([0.7, 0.75, 0.8, 0.85, 0.9, 0.95], n)
    mis = rng.choice([0.05, 0.1, 0.2, 0.3, 0.4, 0.5], n)
    return {"prior": prior, "acc": acc, "rep": rep, "mis": mis}


def _load_table(model, cases, loads, repeats, width=None):
    width = width or LOAD_WIDTH[model]
    fields = {
        "dependence": ("acc", "rep", "src", "rate"),
        "mismatch": ("acc", "rep", "mis"),
        "composite": ("acc", "rep", "mis", "src", "rate", "cond"),
        "composite-deep": ("acc", "rep", "mis", "src", "rate", "cond", "src2", "rate2", "msrc"),
    }[model]
    table = {
        "kind": np.array(["forecast"] * len(cases)),
        "prior": np.array([c["prior"] for c in cases], dtype=float),
        "load": np.array(loads, dtype=int),
        "n": np.array([len(c["acc"]) for c in cases], dtype=int),
        "repeat_of": np.array(repeats, dtype=int),
    }
    for field in fields:
        pad = -1 if field in ("src", "src2", "msrc") else 0
        for k in range(width):
            values = [c[field][k] if k < len(c["acc"]) else pad for c in cases]
            dtype = int if field in ("rep", "src", "cond", "src2", "msrc") else float
            table[f"{field}_{k}"] = np.array(values, dtype=dtype)
    return table


def load_design(model):
    """Twenty-four fully specified cases on three load levels, with three repeats."""
    from epistemics.dispositions import observers

    rng = np.random.default_rng(_LOAD_SEEDS[model])
    cases, loads = [], []
    for level, n in enumerate(LOAD_READINGS[model]):
        found = 0
        while found < 7:
            case = _load_case(model, rng, n)
            probe = _load_table(model, [case], [level], [-1])
            exact, neglect = observers.load_answers(model, probe)
            if abs(exact[0]) <= 2.94 and abs(exact[0] - neglect[0]) >= 0.25:
                cases.append(case)
                loads.append(level)
                found += 1
    repeats = [-1] * len(cases)
    for level in range(3):
        first = loads.index(level)
        cases.append(cases[first])
        loads.append(level)
        repeats.append(first)
    return _load_table(model, cases, loads, repeats)


# Design 0.10 (after capacity pilot 2): four load levels, the top one twice the pilot's, so the
# ladder can reach GPT-6 (at or near ceiling at 8 readings). Five cases per level and one repeat,
# the level's typical case (median separation of exact and neglect answers), not its first.
# Misfiling readings are balanced for per-reading difficulty: each reading's gap between its
# neglect and exact log-likelihood ratios is at most MISFILING_GAP, and each case's mean gap lies
# in MISFILING_BAND at every level, so levels differ in how many readings there are, not in how
# hard each one is. (In the pilot, one reading correct 95% of the time and misfiled 50% of the
# time, gap 1.97, made the middle level the hardest for every configuration.)
LONG_READINGS = {"dependence": (2, 4, 8, 16), "mismatch": (1, 3, 6, 12)}
LONG_WIDTH = {"dependence": 16, "mismatch": 12}
_LONG_SEEDS = {"dependence": 20261005, "mismatch": 20261006}
_LONG_COPIERS = {2: 1, 4: 2, 8: 3, 16: 5}
LONG_CASES = 5
MISFILING_GAP = 1.0
MISFILING_BAND = (0.3, 0.7)


def misfiling_gaps(acc, mis):
    """Per reading: |log-likelihood ratio if never misfiled - log-likelihood ratio given the
    stated misfiling rate|, the part of each reading a neglecting answer gets wrong."""
    acc, mis = np.asarray(acc, dtype=float), np.asarray(mis, dtype=float)
    independent = np.log(acc) - np.log1p(-acc)
    effective = (1 - mis) * acc + mis / 2
    return np.abs(independent - (np.log(effective) - np.log1p(-effective)))


def _long_case(model, rng, n):
    if model == "dependence":
        prior = float(rng.choice([0.3, 0.4, 0.5, 0.6, 0.7]))
        rep = rng.choice([-1, 1], n)
        acc = rng.choice([0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9], n)
        src, rate = np.full(n, -1), np.zeros(n)
        for idx in sorted(rng.choice(np.arange(1, n), _LONG_COPIERS[n], replace=False)):
            src[idx] = int(rng.integers(0, idx))
            rate[idx] = float(rng.choice([0.2, 0.3, 0.4, 0.5, 0.6]))
        return {"prior": prior, "acc": acc, "rep": rep, "src": src, "rate": rate}
    case = _load_case(model, rng, n)
    gaps = misfiling_gaps(case["acc"], case["mis"])
    if gaps.max() > MISFILING_GAP or not MISFILING_BAND[0] <= gaps.mean() <= MISFILING_BAND[1]:
        return None
    return case


def long_load_design(model):
    """Twenty-four fully specified cases on four load levels: five per level plus one repeat."""
    from epistemics.dispositions import observers

    rng = np.random.default_rng(_LONG_SEEDS[model])
    cases, loads, separations = [], [], []
    for level, n in enumerate(LONG_READINGS[model]):
        found = 0
        while found < LONG_CASES:
            case = _long_case(model, rng, n)
            if case is None:
                continue
            probe = _load_table(model, [case], [level], [-1], LONG_WIDTH[model])
            exact, neglect = observers.load_answers(model, probe)
            if abs(exact[0]) <= 2.94 and abs(exact[0] - neglect[0]) >= 0.25:
                cases.append(case)
                loads.append(level)
                separations.append(abs(exact[0] - neglect[0]))
                found += 1
    repeats = [-1] * len(cases)
    for level in range(len(LONG_READINGS[model])):
        members = [i for i, lv in enumerate(loads[: len(separations)]) if lv == level]
        typical = sorted(members, key=lambda i: separations[i])[len(members) // 2]
        cases.append(cases[typical])
        loads.append(level)
        repeats.append(typical)
    return _load_table(model, cases, loads, repeats, LONG_WIDTH[model])


# Design 0.11 (after pilot 3, where GPT-6 computed 16 readings exactly at every effort):
# structural load. Every case has five readings, so the arithmetic stays about the same, and the
# level sets how much structure the evidence has:
#   0: one copy relation;
#   1: one copy relation and, on another reading, misfiling;
#   2: a copy relation whose source and copier may both be misfiled, and a conditional copy
#      relation elsewhere (the copier copies only when its source reads red);
#   3: a chain (B copies A, C copies B), one link conditional, with misfiling on A, C and one
#      further reading.
# Every structure a case states must move its exact answer by at least COMPOSITE_BEARING
# log-odds: ignoring copying, ignoring misfiling, or misreading a condition (as unconditional
# when the source reads blue, as never copying when it reads red). Within a level, conditional
# sources alternate red and blue, so neither misreading of the condition is right in general.
COMPOSITE_READINGS = 5
COMPOSITE_LEVELS = 4
COMPOSITE_BEARING = 0.1
_COMPOSITE_SEED = 20261009
_COMPOSITE_ACC = (0.65, 0.7, 0.75, 0.8, 0.85, 0.9)
_COMPOSITE_MIS = (0.2, 0.3, 0.4, 0.5)
_COMPOSITE_RATE = (0.3, 0.4, 0.5, 0.6, 0.7)


def _composite_case(rng, level, red_source):
    n = COMPOSITE_READINGS
    case = {
        "prior": float(rng.choice([0.3, 0.4, 0.5, 0.6, 0.7])),
        "acc": rng.choice(_COMPOSITE_ACC, n),
        "rep": rng.choice([-1, 1], n),
        "mis": np.zeros(n),
        "src": np.full(n, -1),
        "rate": np.zeros(n),
        "cond": np.zeros(n, dtype=int),
    }

    def copy(k, s, cond=0):
        case["src"][k], case["rate"][k], case["cond"][k] = s, rng.choice(_COMPOSITE_RATE), cond
        if cond:
            case["rep"][s] = 1 if red_source else -1

    if level == 0:
        s, k = sorted(rng.choice(n, 2, replace=False))
        copy(k, s)
    elif level == 1:
        s, k, j = rng.choice(n, 3, replace=False)
        s, k = sorted((s, k))
        copy(k, s)
        case["mis"][j] = rng.choice(_COMPOSITE_MIS)
    elif level == 2:
        a, b, c, d = rng.choice(n, 4, replace=False)
        s, k = sorted((a, b))
        copy(k, s)
        case["mis"][s], case["mis"][k] = rng.choice(_COMPOSITE_MIS, 2)
        s2, k2 = sorted((c, d))
        copy(k2, s2, cond=1)
    else:
        a, b, c, d = sorted(rng.choice(n, 4, replace=False))
        first = int(rng.integers(2))
        copy(b, a, cond=first)
        copy(c, b, cond=1 - first)
        case["mis"][a], case["mis"][c], case["mis"][d] = rng.choice(_COMPOSITE_MIS, 3)
    return case


def composite_bearing(items):
    """Per case, how far each stated structure moves the exact answer (NaN where absent)."""
    from epistemics.dispositions import observers

    exact = observers.composite(items)
    partial = observers.composite_partials(items)
    width = sum(1 for key in items if key.startswith("acc_"))

    def some(name, test):
        keys = [f"{name}_{k}" for k in range(width) if f"{name}_{k}" in items]
        if not keys:
            return np.zeros(len(exact), dtype=bool)
        return np.any([test(np.asarray(items[key])) for key in keys], axis=0)

    def moved(*names):
        return np.max([np.abs(partial[name] - exact) for name in names], axis=0)

    has = {
        "copy": some("src", lambda v: v >= 0) | some("src2", lambda v: v >= 0),
        "mis": some("mis", lambda v: v > 0),
        "cond": some("cond", lambda v: v > 0),
        "mcond": some("msrc", lambda v: v >= 0),
        "second": some("src2", lambda v: v >= 0),
    }
    values = {
        "copy": moved("copying ignored"),
        "mis": moved("misfiling ignored"),
        "cond": moved("copy condition read as unconditional", "copy condition read as never"),
        "mcond": moved(
            "misfiling condition read as unconditional", "misfiling condition read as never"
        ),
        "second": moved("second source ignored"),
    }
    return {name: np.where(has[name], values[name], np.nan) for name in has if has[name].any()}


def composite_load_design():
    """Twenty-four fully specified cases on four structural levels: five per level plus the
    level's typical case repeated."""
    from epistemics.dispositions import observers

    rng = np.random.default_rng(_COMPOSITE_SEED)
    cases, loads, separations = [], [], []
    for level in range(COMPOSITE_LEVELS):
        found = 0
        while found < LONG_CASES:
            case = _composite_case(rng, level, red_source=found % 2 == 0)
            probe = _load_table("composite", [case], [level], [-1], COMPOSITE_READINGS)
            exact, neglect = observers.load_answers("composite", probe)
            bearing = [v[0] for v in composite_bearing(probe).values() if not np.isnan(v[0])]
            if (
                abs(exact[0]) <= 2.94
                and abs(exact[0] - neglect[0]) >= 0.25
                and min(bearing) >= COMPOSITE_BEARING
            ):
                cases.append(case)
                loads.append(level)
                separations.append(abs(exact[0] - neglect[0]))
                found += 1
    repeats = [-1] * len(cases)
    for level in range(COMPOSITE_LEVELS):
        members = [i for i, lv in enumerate(loads[: len(separations)]) if lv == level]
        typical = sorted(members, key=lambda i: separations[i])[len(members) // 2]
        cases.append(cases[typical])
        loads.append(level)
        repeats.append(typical)
    return _load_table("composite", cases, loads, repeats, COMPOSITE_READINGS)


# Design 0.12 (after the structural pilot, where only Astra below high effort erred, once per
# level at the top): the structural ladder extended upward, five readings throughout.
#   0: one copy relation and misfiling on another reading (the first ladder's level 1);
#   1: a chain (B copies A, C copies B) with one link conditional on red or blue, misfiling on A,
#      C and D (the first ladder's top level, with either colour of condition);
#   2: a chain with both links conditional on opposite colours, misfiling on A and C, and
#      misfiling on D that applies only in rounds when B reads blue;
#   3: level 2 plus a fifth sensor that copies A in some rounds and C in others.
# Every stated structure must bear on the answer (COMPOSITE_BEARING), including each condition
# and the second source. Each condition applies in some cases of its level and not in others:
# A's and B's readings are set so that the conditions they govern alternate across cases (at
# levels 2 and 3 cycling through first link only, second only, both).
_DEEP_SEED = 20261010
_DEEP_SECOND_RATE = (0.2, 0.3, 0.4)


def _deep_case(rng, level, found):
    n = COMPOSITE_READINGS
    case = {
        "prior": float(rng.choice([0.3, 0.4, 0.5, 0.6, 0.7])),
        "acc": rng.choice(_COMPOSITE_ACC, n),
        "rep": rng.choice([-1, 1], n),
        "mis": np.zeros(n),
        "src": np.full(n, -1),
        "rate": np.zeros(n),
        "cond": np.zeros(n, dtype=int),
        "src2": np.full(n, -1),
        "rate2": np.zeros(n),
        "msrc": np.full(n, -1),
    }

    def copy(k, s, cond=0):
        case["src"][k], case["rate"][k], case["cond"][k] = s, rng.choice(_COMPOSITE_RATE), cond

    def set_applies(s, cond, applies):
        # The source's reading decides whether a relation conditioned on it applies.
        red = (cond == 1) == applies
        case["rep"][s] = 1 if red else -1

    if level == 0:
        s, k, j = rng.choice(n, 3, replace=False)
        s, k = sorted((s, k))
        copy(k, s)
        case["mis"][j] = rng.choice(_COMPOSITE_MIS)
        return case
    a, b, c, d = sorted(rng.choice(n, 4, replace=False)) if level == 1 else (0, 1, 2, 3)
    first = int(rng.integers(1, 3))
    if level == 1:
        conditional = int(rng.integers(2))
        copy(b, a, cond=first if conditional == 0 else 0)
        copy(c, b, cond=first if conditional == 1 else 0)
        set_applies((a, b)[conditional], first, found % 2 == 0)
        case["mis"][a], case["mis"][c], case["mis"][d] = rng.choice(_COMPOSITE_MIS, 3)
        return case
    copy(b, a, cond=first)
    copy(c, b, cond=3 - first)
    # Each link applies in some cases and not others, never neither (copying must bear).
    applies = ((True, False), (False, True), (True, True))[found % 3]
    set_applies(a, first, applies[0])
    set_applies(b, 3 - first, applies[1])
    case["mis"][a], case["mis"][c], case["mis"][d] = rng.choice(_COMPOSITE_MIS, 3)
    case["msrc"][d] = b
    if level == 3:
        e = 4
        case["src"][e], case["rate"][e] = a, rng.choice(_DEEP_SECOND_RATE)
        case["src2"][e], case["rate2"][e] = c, rng.choice(_DEEP_SECOND_RATE)
    return case


def composite_deep_design():
    """Twenty-four fully specified cases on the extended structural ladder: five per level plus
    the level's typical case repeated."""
    from epistemics.dispositions import observers

    rng = np.random.default_rng(_DEEP_SEED)
    cases, loads, separations = [], [], []
    for level in range(COMPOSITE_LEVELS):
        found = 0
        while found < LONG_CASES:
            case = _deep_case(rng, level, found)
            probe = _load_table("composite-deep", [case], [level], [-1], COMPOSITE_READINGS)
            exact, neglect = observers.load_answers("composite", probe)
            bearing = [v[0] for v in composite_bearing(probe).values() if not np.isnan(v[0])]
            if (
                abs(exact[0]) <= 2.94
                and abs(exact[0] - neglect[0]) >= 0.25
                and min(bearing) >= COMPOSITE_BEARING
            ):
                cases.append(case)
                loads.append(level)
                separations.append(abs(exact[0] - neglect[0]))
                found += 1
    repeats = [-1] * len(cases)
    for level in range(COMPOSITE_LEVELS):
        members = [i for i, lv in enumerate(loads[: len(separations)]) if lv == level]
        typical = sorted(members, key=lambda i: separations[i])[len(members) // 2]
        cases.append(cases[typical])
        loads.append(level)
        repeats.append(typical)
    return _load_table("composite-deep", cases, loads, repeats, COMPOSITE_READINGS)


def dependence_load():
    return load_design("dependence")


def mismatch_load():
    return load_design("mismatch")
