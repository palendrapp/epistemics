"""Open-inference screen (model 0.16, design 0.17; docs/open-inference-screen-design.md).

Five families of items whose answers depend on a model the item does not state: a hypothesis
space (gen), a model of the speaker (num), a model of another agent (choice), the completeness of
a list of causes (lists) and a family of functions (trend). Each family has a rational model with
prior parameters, used for three things:
  - openness: the spread (10th to 90th percentile, log-odds) of an item's predicted answer across
    the plausible range of the parameters; open items must be open, anchors are determinate;
  - contrast signs: each contrast is a difference of mean log-odds between items that the
    family's parameter moves in opposite directions (or a level, with no minus set);
  - simulated respondents, for validation and calibration.
Contrasts are computed without fitting. Sessions have 20 open items and 4 anchors.
"""

import functools
import json
import math

import numpy as np

FAMILIES = ("gen", "num", "choice", "lists", "trend")
FORMS = ("a", "b")
CLIP = 0.01
VOI = 0.25  # choice: value of checking for an uncertain agent, in units of the decision's stakes

SPEC = {
    "gen": {
        "params": {"rule_weight": (0.1, 0.9), "sampling": (0.0, 1.0), "interval_scale": (5, 20)},
        "contrasts": ("rule_reliance", "tightening"),
        "drivers": {"rule_reliance": (("rule_weight",), 1), "tightening": (("sampling",), 1)},
    },
    "num": {
        # Speaker model: a person's (or an instrument's) number is exact with prior probability
        # person_exact (instrument_exact), otherwise rounded to its unit (10 below 100, else 100);
        # an exact report carries measurement noise with SD precision x value.
        "params": {
            "person_exact": (0.1, 0.9),
            "instrument_exact": (0.4, 1.0),
            "precision": ("log", 0.002, 0.03),
        },
        "contrasts": ("halo_people", "halo_instruments"),
        "drivers": {
            "halo_people": (("person_exact",), -1),
            "halo_instruments": (("instrument_exact",), -1),
        },
    },
    "choice": {
        "params": {
            "rationality": ("log", 0.5, 30.0),
            "knowledge_prior": (0.2, 0.8),
            "cost_trivial": (0.01, 0.05),
            "cost_moderate": (0.08, 0.2),
            "cost_large": (0.3, 0.6),
        },
        "contrasts": ("skip_informativeness", "knowledge_attribution"),
        "drivers": {
            "skip_informativeness": (("rationality",), 1),
            "knowledge_attribution": (("knowledge_prior",), 1),
        },
    },
    "lists": {
        "params": {"residual_manual": (0.0, 0.4), "residual_colleague": (0.05, 0.6)},
        "contrasts": ("residual", "source"),
        "drivers": {
            "residual": (("residual_manual", "residual_colleague"), 1),
            "source": (("residual_colleague",), 1),
        },
    },
    "trend": {
        # Bayesian model averaging over linear, power and exponential functions, with prior
        # linear_weight on linear and the rest split equally, and a likelihood weight: the
        # log-likelihood of the readings is multiplied by it (below 1 the readings constrain the
        # curve less, as in conservatism; above 1, more).
        "params": {"linear_weight": (0.2, 0.9), "likelihood_weight": ("log", 0.2, 5.0)},
        "contrasts": ("linearity", "conservatism"),
        "drivers": {
            "linearity": (("linear_weight",), 1),
            "conservatism": (("likelihood_weight",), -1),
        },
    },
}
# The first contrast of each family, signed so that + means committing more to the simplest model
# (the rule, the literal reading, a fully rational other agent, a closed list, the straight line).
COMMITMENT = {"gen": 1, "num": -1, "choice": 1, "lists": -1, "trend": 1}
# The guard's meaningful difference: the score change from moving a contrast's driving parameters
# (in the direction that raises the score) by this fraction of their plausible range (log range
# where marked).
CHANGE_FRACTION = 0.125
# Audit thresholds (log-odds).
OPEN_MEDIAN = 1.0
ANCHOR_TOLERANCE = 0.05  # probability


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), CLIP, 1 - CLIP)
    return np.log(p / (1 - p))


def _phi(x):
    return 0.5 * (1 + np.vectorize(math.erf)(np.asarray(x, dtype=float) / math.sqrt(2)))


def _sigmoid(x):
    return 1 / (1 + np.exp(-np.asarray(x, dtype=float)))


# Parameters.
def mid(family):
    out = {}
    for name, spec in SPEC[family]["params"].items():
        if spec[0] == "log":
            out[name] = float(math.sqrt(spec[1] * spec[2]))
        else:
            out[name] = (spec[0] + spec[1]) / 2
    return out


def draw(family, rng, n):
    """n parameter sets drawn uniformly (log-uniformly where marked) from the plausible range."""
    out = [{} for _ in range(n)]
    for name, spec in SPEC[family]["params"].items():
        if spec[0] == "log":
            values = np.exp(rng.uniform(math.log(spec[1]), math.log(spec[2]), n))
        else:
            values = rng.uniform(spec[0], spec[1], n)
        for k in range(n):
            out[k][name] = float(values[k])
    return out


def changed(family, params, names, sign, fraction=CHANGE_FRACTION):
    out = dict(params)
    for name in names:
        spec = SPEC[family]["params"][name]
        if spec[0] == "log":
            out[name] = out[name] * math.exp(sign * fraction * math.log(spec[2] / spec[1]))
        else:
            out[name] = out[name] + sign * fraction * (spec[1] - spec[0])
    return out


# Family models: predicted probability for one open item's data under one parameter set.
@functools.cache
def _hypotheses():
    numbers = np.arange(1, 101)
    rules = [numbers % 2 == 1, numbers % 2 == 0]
    rules.append(np.isin(numbers, [k * k for k in range(1, 11)]))
    rules.append(np.isin(numbers, [k**3 for k in range(1, 5)]))
    primes = [n for n in range(2, 101) if all(n % d for d in range(2, int(n**0.5) + 1))]
    rules.append(np.isin(numbers, primes))
    rules += [numbers % k == 0 for k in range(3, 11)]
    rules += [np.isin(numbers, [k**j for j in range(8) if k**j <= 100]) for k in (2, 3, 4, 5, 10)]
    rules += [numbers % 10 == d for d in range(10)]
    a, b = np.triu_indices(100)
    intervals = (numbers[None, :] - 1 >= a[:, None]) & (numbers[None, :] - 1 <= b[:, None])
    return np.array(rules), intervals


def _gen(d, p):
    rules, intervals = _hypotheses()
    x = np.array(d["examples"]) - 1
    y = d["probe"] - 1
    n = len(x)
    rule_size = rules.sum(axis=1)
    interval_size = intervals.sum(axis=1)
    sigma = p["interval_scale"]
    erlang = interval_size / sigma**2 * np.exp(-interval_size / sigma)
    log_prior = np.concatenate(
        [
            np.full(len(rules), math.log(p["rule_weight"] / len(rules))),
            np.log(1 - p["rule_weight"]) + np.log(erlang / erlang.sum()),
        ]
    )
    members = np.concatenate([rules, intervals])
    size = np.concatenate([rule_size, interval_size])
    consistent = members[:, x].all(axis=1)
    log_post = np.where(consistent, log_prior - p["sampling"] * n * np.log(size), -np.inf)
    w = np.exp(log_post - log_post.max())
    return float(w[members[:, y]].sum() / w.sum())


NUM_UNIT_ROUNDING = 1.0  # a rounded report comes from anywhere in its unit's bin


def _num(d, p):
    u = d["value"]
    lo, hi = d["window"]
    sd = max(p["precision"] * u, 1e-9)
    literal = float(_phi((hi - u) / sd) - _phi((lo - u) / sd))
    if d["sharp"]:
        return literal
    exact = p["instrument_exact"] if d["source"] == "instrument" else p["person_exact"]
    width = NUM_UNIT_ROUNDING * d["unit"]
    overlap = max(0.0, min(hi, u + width / 2) - max(lo, u - width / 2)) / width
    return exact * literal + (1 - exact) * overlap


def _choice(d, p):
    beta, kappa = p["rationality"], p["knowledge_prior"]
    cost = p[("cost_trivial", "cost_moderate", "cost_large")[d["cost"]]]
    knower = float(_sigmoid(-beta * cost))  # a knower checks only by chance
    unsure = float(_sigmoid(beta * (VOI - cost)))
    if d["action"] == "skipped":
        a, b = kappa * (1 - knower), (1 - kappa) * (1 - unsure)
    else:
        a, b = kappa * knower, (1 - kappa) * unsure
    return a / (a + b)


def _lists(d, p):
    if d["question"] == "conditional":
        return d["parts"] / d["k"]  # given a listed cause, by symmetry
    rho = p["residual_colleague"] if d["source"] == "colleague" else p["residual_manual"]
    return rho if d["question"] == "none" else (1 - rho) / d["k"]


TREND_FAMILIES = ("linear", "power", "exponential")


def _trend_fits(xs, ys):
    """Least-squares fits of each function family on its own scale: (design, target, log)."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    out = {}
    for name, design, target, log in (
        ("linear", np.column_stack([np.ones_like(xs), xs]), ys, False),
        ("power", np.column_stack([np.ones_like(xs), np.log(xs)]), np.log(ys), True),
        ("exponential", np.column_stack([np.ones_like(xs), xs]), np.log(ys), True),
    ):
        coef, *_ = np.linalg.lstsq(design, target, rcond=None)
        out[name] = (design, target, coef, log)
    return out


def trend_projection(xs, ys, x_star, name):
    design, _, coef, log = _trend_fits(xs, ys)[name]
    row = np.array([1.0, math.log(x_star) if name == "power" else x_star])
    value = float(row @ coef)
    return math.exp(value) if log else value


TREND_NOISE = 0.15  # the process noise assumed for every series (relative)


def _trend(d, p):
    """Posterior predictive with a tempered likelihood (weight b): family weights use b x the
    log-likelihood, and parameter uncertainty grows as 1/b (a flat prior on each family's
    coefficients)."""
    xs, ys, x_star = d["xs"], d["ys"], d["x"]
    b = p["likelihood_weight"]
    fits = _trend_fits(xs, ys)
    weights, probs = [], []
    for name in TREND_FAMILIES:
        design, target, coef, log = fits[name]
        sd = TREND_NOISE if log else TREND_NOISE * float(np.mean(ys))
        ssr = float(np.sum((target - design @ coef) ** 2))
        prior = p["linear_weight"] if name == "linear" else (1 - p["linear_weight"]) / 2
        weights.append(math.log(prior) - b * ssr / (2 * sd**2))
        row = np.array([1.0, math.log(x_star) if name == "power" else x_star])
        leverage = float(row @ np.linalg.inv(design.T @ design) @ row)
        spread = sd * math.sqrt(1 + leverage / b)
        mean = float(row @ coef)
        scale = (lambda v: math.log(v)) if log else (lambda v: v)
        if d["question"] == "above":
            prob = 1 - float(_phi((scale(d["threshold"]) - mean) / spread))
        else:
            lo, hi = d["window"]
            prob = float(_phi((scale(hi) - mean) / spread) - _phi((scale(lo) - mean) / spread))
        probs.append(prob)
    w = np.exp(np.array(weights) - max(weights))
    return float(w @ np.array(probs) / w.sum())


MODELS = {"gen": _gen, "num": _num, "choice": _choice, "lists": _lists, "trend": _trend}


# Revised observers (model 0.18; docs/open-inference-screen-design.md, "Revised observers"): F2
# rounds in proportion to the number; F5's process noise is a parameter. The answer reported on
# a non-anchor item is (1 - trust) x the observer's probability + trust x fallback (fitted in
# ledger.screen_fit), so a configuration can fall back on a default when a case is open.
NUM_GRAIN = 0.2


def _num_revised(d, p):
    u = d["value"]
    lo, hi = d["window"]
    sd = max(p["precision"] * u, 1e-9)
    literal = float(_phi((hi - u) / sd) - _phi((lo - u) / sd))
    if d["sharp"]:
        return literal
    exact = p["instrument_exact"] if d["source"] == "instrument" else p["person_exact"]
    width = NUM_GRAIN * u
    overlap = max(0.0, min(hi, u + width / 2) - max(lo, u - width / 2)) / width
    return exact * literal + (1 - exact) * overlap


def _trend_revised(d, p):
    xs, ys, x_star = d["xs"], d["ys"], d["x"]
    b, noise = p.get("likelihood_weight", 1.0), p["noise"]
    fits = _trend_fits(xs, ys)
    weights, probs = [], []
    for name in TREND_FAMILIES:
        design, target, coef, log = fits[name]
        sd = noise if log else noise * float(np.mean(ys))
        ssr = float(np.sum((target - design @ coef) ** 2))
        prior = p["linear_weight"] if name == "linear" else (1 - p["linear_weight"]) / 2
        weights.append(math.log(prior) - b * ssr / (2 * sd**2))
        row = np.array([1.0, math.log(x_star) if name == "power" else x_star])
        leverage = float(row @ np.linalg.inv(design.T @ design) @ row)
        spread = sd * math.sqrt(1 + leverage / b)
        mean = float(row @ coef)
        scale = math.log if log else (lambda v: v)
        if d["question"] == "above":
            prob = 1 - float(_phi((scale(d["threshold"]) - mean) / spread))
        else:
            lo, hi = d["window"]
            prob = float(_phi((scale(hi) - mean) / spread) - _phi((scale(lo) - mean) / spread))
        probs.append(prob)
    w = np.exp(np.array(weights) - max(weights))
    return float(w @ np.array(probs) / w.sum())


OBSERVERS = {**MODELS, "num": _num_revised, "trend": _trend_revised}
OBSERVER_PARAMS = {
    **{f: dict(spec["params"]) for f, spec in SPEC.items()},
    # F5's diagnosticity is the assumed process noise alone (the likelihood weight is 1): with both
    # free, the two were not separable (revised recovery, forms a+b+c: likelihood weight r 0.35).
    "trend": {"linear_weight": (0.2, 0.9), "noise": ("log", 0.01, 0.3)},
}
# Form c (tasks 0.28): fallback items for F2, F4 and F5. Their observer answer is fixed whatever
# the parameters (openness at most FIXED_OPENNESS), at several levels, so what a configuration
# answers on them shows how much it falls back on a default.
FIXED_FORM = "c"
FIXED_FAMILIES = ("num", "lists", "trend")
FIXED_OPENNESS = 0.3


def forms(family):
    return FORMS + ((FIXED_FORM,) if family in FIXED_FAMILIES else ())


def observer_draw(family, rng, n):
    out = [{} for _ in range(n)]
    for name, spec in OBSERVER_PARAMS[family].items():
        if spec[0] == "log":
            values = np.exp(rng.uniform(math.log(spec[1]), math.log(spec[2]), n))
        else:
            values = rng.uniform(spec[0], spec[1], n)
        for k in range(n):
            out[k][name] = float(values[k])
    return out


def observer_mid(family):
    out = {}
    for name, spec in OBSERVER_PARAMS[family].items():
        out[name] = (
            float(math.sqrt(spec[1] * spec[2])) if spec[0] == "log" else (spec[0] + spec[1]) / 2
        )
    return out


# Designs.
def _pairs_halves(rows):
    """Alternate halves within each contrast's plus and minus sets, in design order."""
    for contrast in ("c1", "c2"):
        for sign in (1, -1):
            chosen = [r for r in rows if r[contrast] == sign]
            for j, r in enumerate(chosen):
                r[f"h{contrast[1]}"] = j % 2
    return rows


def _row(kind, surface, data, c1=0, c2=0, transform="logit", answer=float("nan")):
    return {
        "kind": kind,
        "surface": surface,
        "c1": c1,
        "c2": c2,
        "h1": -1,
        "h2": -1,
        "transform": transform,
        "k": int(data.get("k", 0)),
        "answer": answer,
        "data": data,
    }


GEN = {
    "a": {
        "surfaces": (0, 1),
        "sets": [
            ((20, 30, 40), 80, 33),
            ((25, 36, 49), 81, 40),
            ((12, 15, 18), 42, 16),
            ((70, 75, 85), 15, 78),
            ((8, 16, 32), 64, 21),
            ((44, 48, 52), 12, 49),
        ],
        "pairs": [
            ((60, 80, 10, 30), 52),
            ((16, 8, 2, 64), 10),
            ((81, 25, 4, 36), 45),
            ((35, 55, 15, 95), 70),
        ],
        "anchors": [
            ("multiples of 4 from 4 to 100", (12, 36, 88), 44, 1.0),
            ("multiples of 4 from 4 to 100", (88, 12, 36), 50, 0.0),
            ("whole numbers from 30 to 60", (34, 51, 47), 45, 1.0),
            ("whole numbers from 30 to 60", (47, 34, 51), 70, 0.0),
        ],
    },
    "b": {
        "surfaces": (2, 3),
        "sets": [
            ((40, 50, 60), 10, 47),
            ((16, 25, 36), 100, 30),
            ((21, 24, 27), 6, 25),
            ((35, 40, 50), 90, 37),
            ((60, 66, 72), 18, 65),
            ((49, 64, 81), 16, 70),
        ],
        "pairs": [
            ((30, 90, 60, 10), 42),
            ((4, 16, 64, 1), 36),
            ((27, 3, 9, 81), 33),
            ((50, 20, 90, 70), 44),
        ],
        "anchors": [
            ("multiples of 6 from 6 to 96", (18, 42, 78), 54, 1.0),
            ("multiples of 6 from 6 to 96", (78, 18, 42), 52, 0.0),
            ("whole numbers from 20 to 50", (23, 41, 36), 30, 1.0),
            ("whole numbers from 20 to 50", (36, 23, 41), 60, 0.0),
        ],
    },
}


def _gen_rows(form):
    spec = GEN[form]
    s0, s1 = spec["surfaces"]
    rows = []
    # The two probes of a set (and the two sizes of a pair) are shown on different surfaces.
    for j, (examples, rule_probe, near_probe) in enumerate(spec["sets"]):
        surface = (s0, s1)[j % 2]
        other = s0 + s1 - surface
        rows.append(_row("open", surface, {"examples": examples, "probe": rule_probe}, c1=1))
        rows.append(_row("open", other, {"examples": examples, "probe": near_probe}, c1=-1))
    for j, (examples, probe) in enumerate(spec["pairs"]):
        surface = (s1, s0)[j % 2]
        other = s0 + s1 - surface
        rows.append(_row("open", surface, {"examples": examples[:1], "probe": probe}, c2=1))
        rows.append(_row("open", other, {"examples": examples, "probe": probe}, c2=-1))
    for j, (rule, examples, probe, answer) in enumerate(spec["anchors"]):
        data = {"examples": examples, "probe": probe, "rule": rule}
        rows.append(_row("anchor", (s0, s1)[j % 2], data, answer=answer))
    return rows


# num: (value, quantity); quantities index screen_texts.NUMBERS. Round numbers get windows of +/-0.2
# of their unit (wide against measurement noise, narrow against rounding), so they measure the
# speaker model; sharp numbers get +/-1% windows, which measure the assumed precision.
NUM = {
    "a": {
        "person": [(30, 0), (40, 1), (60, 2), (200, 3), (500, 4), (300, 5), (70, 0)],
        "instrument": [(40, 0), (60, 1), (30, 2), (500, 3), (300, 4), (200, 5), (80, 1)],
        "sharp": [(31, 0), (43, 1), (58, 2), (196, 3), (488, 4), (291, 5)],
        "anchors": [
            ("rounds", 40, 1, ("between", 34, 46), 1.0),
            ("rounds", 40, 1, ("above", 50), 0.0),
            ("exact", 31, 3, ("between", 30, 32), 1.0),
            ("exact", 31, 3, ("below", 25), 0.0),
        ],
    },
    "b": {
        "person": [(20, 0), (50, 1), (80, 2), (300, 3), (400, 4), (600, 5), (90, 0)],
        "instrument": [(50, 0), (80, 1), (20, 2), (400, 3), (600, 4), (300, 5), (70, 1)],
        "sharp": [(21, 0), (47, 1), (83, 2), (304, 3), (391, 4), (587, 5)],
        "anchors": [
            ("rounds", 80, 4, ("between", 74, 86), 1.0),
            ("rounds", 80, 4, ("above", 90), 0.0),
            ("exact", 47, 3, ("between", 46, 48), 1.0),
            ("exact", 47, 3, ("below", 40), 0.0),
        ],
    },
}


def _unit(value):
    return 10 if value < 100 else 100


def _window(value, width=0.01):
    half = max(1, round(width * value))
    return (value - half, value + half)


def _unit_window(value):
    half = round(0.2 * _unit(value))
    return (value - half, value + half)


def _num_rows(form):
    spec = NUM[form]
    rows = []
    for j, (value, quantity) in enumerate(spec["person"]):
        data = {
            "value": value,
            "sharp": False,
            "source": "person",
            "quantity": quantity,
            "unit": _unit(value),
            "window": _unit_window(value),
            "speaker": j % 4,
        }
        rows.append(_row("open", quantity, data, c1=-1))
    for value, quantity in spec["instrument"]:
        data = {
            "value": value,
            "sharp": False,
            "source": "instrument",
            "quantity": quantity,
            "unit": _unit(value),
            "window": _unit_window(value),
        }
        rows.append(_row("open", quantity, data, c2=-1))
    for j, (value, quantity) in enumerate(spec["sharp"]):
        data = {
            "value": value,
            "sharp": True,
            "source": "person",
            "quantity": quantity,
            "unit": _unit(value),
            "window": _window(value),
            "speaker": (j + 2) % 4,
        }
        rows.append(_row("open", quantity, data))
    for kind, value, quantity, bounds, answer in spec["anchors"]:
        data = {"value": value, "anchor": kind, "quantity": quantity, "bounds": bounds}
        rows.append(_row("anchor", quantity, data, answer=answer))
    return rows


def _choice_rows(form):
    offset = 0 if form == "a" else 1
    rows = []
    cells = (
        ("skipped", 0, 1, 0),  # (action, cost, c1, c2)
        ("skipped", 2, -1, 0),
        ("skipped", 1, 0, 1),
        ("taken", 1, 0, 1),
    )
    for c, (action, cost, c1, c2) in enumerate(cells):
        for domain in range(5):
            actor = (domain + c + offset) % 2  # 0 a person, 1 an agent
            data = {"domain": domain, "action": action, "cost": cost, "actor": actor, "form": form}
            rows.append(_row("open", domain, data, c1=c1, c2=c2))
    for j, (domain, answer) in enumerate(((0, 1.0), (1, 0.0), (3, 1.0), (4, 0.0))):
        data = {
            "domain": domain,
            "actor": (j + offset) % 2,
            "form": form,
            "action": "skipped" if answer else "taken",
            "cost": 0 if answer else 1,
        }
        rows.append(_row("anchor", domain, data, answer=answer))
    return rows


LISTS = {
    # (domain, source, question, k), in cells of five.
    "a": [
        *[(d, "manual", "listed", k) for d, k in zip(range(5), (2, 3, 5, 2, 3), strict=True)],
        *[(d, "manual", "none", k) for d, k in zip(range(5), (3, 5, 2, 5, 3), strict=True)],
        *[(d, "colleague", "listed", k) for d, k in zip(range(5), (3, 5, 2, 3, 5), strict=True)],
        *[(d, "colleague", "none", k) for d, k in zip(range(5), (2, 3, 5, 2, 3), strict=True)],
    ],
    "b": [
        *[(d, "manual", "listed", k) for d, k in zip(range(5), (5, 2, 3, 3, 2), strict=True)],
        *[(d, "manual", "none", k) for d, k in zip(range(5), (2, 3, 5, 3, 5), strict=True)],
        *[(d, "colleague", "listed", k) for d, k in zip(range(5), (2, 3, 5, 5, 3), strict=True)],
        *[(d, "colleague", "none", k) for d, k in zip(range(5), (3, 5, 2, 5, 2), strict=True)],
    ],
}


def _lists_rows(form):
    rows = []
    for j, (domain, source, question, k) in enumerate(LISTS[form]):
        data = {
            "domain": domain,
            "source": source,
            "question": question,
            "k": k,
            "rotate": j % 5,
            "form": form,
        }
        transform = "residual" if question == "listed" else "logit"
        rows.append(
            _row(
                "open",
                domain,
                data,
                c1=1,
                c2=1 if source == "colleague" else -1,
                transform=transform,
            )
        )
    for domain, k, question, answer in (
        (0, 3, "listed", 1 / 3),
        (0, 3, "none", 0.0),
        (3, 2, "listed", 0.5),
        (3, 2, "none", 0.0),
    ):
        data = {
            "domain": domain,
            "k": k,
            "question": question,
            "exhaustive": True,
            "rotate": 0,
            "form": form,
            "source": "record",
        }
        rows.append(_row("anchor", domain, data, answer=answer))
    return rows


# trend: linearity items are accelerating (geometric) series, asked whether the reading at 8 will
# exceed 1.5x the linear projection (the exponential projection is far above it, so the answer
# turns on how much weight the straight line keeps: exponential growth bias); conservatism items
# are exact proportional lines, asked for +/-10% windows around the projection at 5 and 10 (only
# the spread matters: the families agree on these lines).
TREND = {
    "a": {
        "accelerating": [
            (4, 8, 16),
            (8, 12, 18),
            (3, 6, 12),
            (12, 18, 27),
            (5, 10, 20),
            (16, 24, 36),
            (6, 12, 24),
            (20, 30, 45),
            (2, 4, 8),
            (4, 6, 9),
        ],
        "near": [(10, 20, 30), (15, 30, 45), (8, 16, 24), (12, 24, 36), (25, 50, 75)],
        "far": [(6, 12, 18), (20, 40, 60), (14, 28, 42), (30, 60, 90), (9, 18, 27)],
        "anchors": [
            (0, (10, 15, 20), 8, 40, 1.0),
            (0, (10, 15, 20), 8, 50, 0.0),
            (1, (12, 16, 20), 10, 40, 1.0),
            (1, (12, 16, 20), 10, 50, 0.0),
        ],
    },
    "b": {
        "accelerating": [
            (7, 14, 28),
            (28, 42, 63),
            (9, 18, 36),
            (32, 48, 72),
            (11, 22, 44),
            (36, 54, 81),
            (13, 26, 52),
            (40, 60, 90),
            (15, 30, 60),
            (24, 36, 54),
        ],
        "near": [(11, 22, 33), (16, 32, 48), (7, 14, 21), (13, 26, 39), (35, 70, 105)],
        "far": [(5, 10, 15), (18, 36, 54), (40, 80, 120), (24, 48, 72), (17, 34, 51)],
        "anchors": [
            (2, (30, 36, 42), 8, 70, 1.0),
            (2, (30, 36, 42), 8, 80, 0.0),
            (3, (100, 110, 120), 10, 180, 1.0),
            (3, (100, 110, 120), 10, 200, 0.0),
        ],
    },
}


def _nice(value):
    step = 1 if value < 50 else 5 if value < 500 else 10
    return int(step * round(value / step))


def _trend_rows(form):
    spec = TREND[form]
    rows = []
    for j, ys in enumerate(spec["accelerating"]):
        linear = trend_projection((1, 2, 3), ys, 8, "linear")
        data = {
            "xs": (1, 2, 3),
            "ys": ys,
            "x": 8,
            "question": "above",
            "threshold": _nice(1.5 * linear),
            "surface": j % 5,
        }
        rows.append(_row("open", j % 5, data, c1=-1))
    for key, x_star in (("near", 5), ("far", 10)):
        for surface, ys in enumerate(spec[key]):
            linear = trend_projection((1, 2, 3), ys, x_star, "linear")
            window = (_nice(0.9 * linear), _nice(1.1 * linear))
            data = {
                "xs": (1, 2, 3),
                "ys": ys,
                "x": x_star,
                "question": "within",
                "window": window,
                "surface": surface,
            }
            rows.append(_row("open", surface, data, c2=-1))
    for surface, ys, x_star, threshold, answer in spec["anchors"]:
        data = {
            "xs": (1, 2, 3),
            "ys": ys,
            "x": x_star,
            "question": "above",
            "threshold": threshold,
            "surface": surface,
            "exact": True,
        }
        rows.append(_row("anchor", surface, data, answer=answer))
    return rows


# Form c: fallback items. Each row: (value, quantity, kind, window or None for "more than").
NUM_C = {
    "fixed": [
        # 0.5: "more than the stated value" (symmetric under the observer)
        (30, 0, "person", None),
        (200, 3, "person", None),
        (50, 4, "person", None),
        (47, 1, "sharp", None),
        (60, 1, "instrument", None),
        (400, 2, "instrument", None),
        # about 1: windows of +/-50%
        (40, 0, "person", (20, 60)),
        (300, 5, "person", (150, 450)),
        (80, 2, "instrument", (40, 120)),
        (58, 3, "sharp", (29, 87)),
        (600, 4, "person", (300, 900)),
        # about 0: windows far from the stated value
        (30, 2, "person", (45, 55)),
        (500, 3, "instrument", (800, 900)),
        (43, 4, "sharp", (20, 30)),
        (70, 5, "person", (100, 120)),
        (90, 0, "instrument", (130, 150)),
    ],
    "open": [(20, 1, "person"), (400, 3, "person"), (60, 4, "person"), (300, 0, "instrument")],
    "anchors": [
        ("rounds", 60, 1, ("between", 54, 66), 1.0),
        ("rounds", 60, 1, ("above", 70), 0.0),
        ("exact", 53, 3, ("between", 52, 54), 1.0),
        ("exact", 53, 3, ("below", 45), 0.0),
    ],
}
MORE_THAN = 1e9  # the upper bound of a "more than" window


def _num_rows_c():
    rows = []
    for j, (value, quantity, kind, window) in enumerate(NUM_C["fixed"]):
        data = {
            "value": value,
            "sharp": kind == "sharp",
            "source": "instrument" if kind == "instrument" else "person",
            "quantity": quantity,
            "unit": _unit(value),
            "window": window if window else (value, MORE_THAN),
            "speaker": j % 4,
        }
        rows.append(_row("fixed", quantity, data))
    for j, (value, quantity, source) in enumerate(NUM_C["open"]):
        data = {
            "value": value,
            "sharp": False,
            "source": source,
            "quantity": quantity,
            "unit": _unit(value),
            "window": _unit_window(value),
            "speaker": (j + 1) % 4,
        }
        rows.append(_row("open", quantity, data))
    for kind, value, quantity, bounds, answer in NUM_C["anchors"]:
        data = {"value": value, "anchor": kind, "quantity": quantity, "bounds": bounds}
        rows.append(_row("anchor", quantity, data, answer=answer))
    return rows


# (k, parts): the probability that a listed cause was one of `parts` named ones, given that the
# cause was listed, is parts / k.
LISTS_C = [
    (5, 1),
    (3, 1),
    (5, 2),
    (2, 1),
    (5, 3),
    (3, 2),
    (5, 4),
    (4, 1),
    (4, 3),
    (4, 2),
    (5, 1),
    (3, 2),
    (2, 1),
    (5, 4),
    (3, 1),
    (5, 3),
]


def _lists_rows_c():
    rows = []
    for j, (k, parts) in enumerate(LISTS_C):
        data = {
            "domain": j % 5,
            "source": ("manual", "colleague")[j % 2],
            "question": "conditional",
            "k": k,
            "parts": parts,
            "rotate": (j * 2) % 5,
            "form": "c",
        }
        rows.append(_row("fixed", j % 5, data))
    for domain, source, question, k in (
        (0, "manual", "listed", 3),
        (1, "colleague", "none", 2),
        (2, "manual", "none", 5),
        (3, "colleague", "listed", 2),
    ):
        data = {
            "domain": domain,
            "source": source,
            "question": question,
            "k": k,
            "rotate": domain,
            "form": "c",
        }
        rows.append(
            _row("open", domain, data, transform="residual" if question == "listed" else "logit")
        )
    for domain, k, question, answer in (
        (1, 3, "listed", 1 / 3),
        (1, 3, "none", 0.0),
        (4, 2, "listed", 0.5),
        (4, 2, "none", 0.0),
    ):
        data = {
            "domain": domain,
            "k": k,
            "question": question,
            "exhaustive": True,
            "rotate": 0,
            "form": "c",
            "source": "record",
        }
        rows.append(_row("anchor", domain, data, answer=answer))
    return rows


TREND_C = {
    # (series, time, threshold, surface): about 1, about 0, about 0.5 (proportional lines asked
    # about their own projection at 3.5)
    "fixed": [
        ((4, 8, 16), 8, 10, 0),
        ((3, 6, 12), 8, 8, 1),
        ((10, 20, 30), 5, 20, 2),
        ((6, 12, 24), 8, 15, 3),
        ((4, 8, 16), 8, 5000, 1),
        ((6, 12, 24), 8, 8000, 2),
        ((10, 20, 30), 5, 500, 3),
        ((20, 30, 45), 8, 20000, 4),
        ((10, 20, 30), 3.5, 35, 0),
        ((12, 24, 36), 3.5, 42, 1),
        ((8, 16, 24), 3.5, 28, 2),
        ((20, 40, 60), 3.5, 70, 3),
    ],
    # Linearity items: geometric series asked about 1.5x (as in forms a and b) and 2x the linear
    # projection at 8.
    "open": [
        ((17, 34, 68), 1.5),
        ((44, 66, 99), 1.5),
        ((19, 38, 76), 1.5),
        ((52, 78, 117), 1.5),
        ((5, 10, 20), 2.0),
        ((8, 12, 18), 2.0),
        ((3, 6, 12), 2.0),
        ((16, 24, 36), 2.0),
    ],
    "anchors": [
        (4, (20, 25, 30), 8, 50, 1.0),
        (4, (20, 25, 30), 8, 60, 0.0),
        (2, (14, 21, 28), 10, 70, 1.0),
        (2, (14, 21, 28), 10, 80, 0.0),
    ],
}


def _trend_rows_c():
    rows = []
    for ys, x_star, threshold, surface in TREND_C["fixed"]:
        data = {
            "xs": (1, 2, 3),
            "ys": ys,
            "x": x_star,
            "question": "above",
            "threshold": threshold,
            "surface": surface,
        }
        rows.append(_row("fixed", surface, data))
    for j, (ys, factor) in enumerate(TREND_C["open"]):
        linear = trend_projection((1, 2, 3), ys, 8, "linear")
        data = {
            "xs": (1, 2, 3),
            "ys": ys,
            "x": 8,
            "question": "above",
            "threshold": _nice(factor * linear),
            "surface": (j + 1) % 5,
        }
        rows.append(_row("open", (j + 1) % 5, data))
    for surface, ys, x_star, threshold, answer in TREND_C["anchors"]:
        data = {
            "xs": (1, 2, 3),
            "ys": ys,
            "x": x_star,
            "question": "above",
            "threshold": threshold,
            "surface": surface,
            "exact": True,
        }
        rows.append(_row("anchor", surface, data, answer=answer))
    return rows


FIXED_ROWS = {"num": _num_rows_c, "lists": _lists_rows_c, "trend": _trend_rows_c}

ROWS = {
    "gen": _gen_rows,
    "num": _num_rows,
    "choice": _choice_rows,
    "lists": _lists_rows,
    "trend": _trend_rows,
}


def design(family, form):
    return {k: v.copy() for k, v in _design(family, form).items()}


@functools.cache
def _design(family, form):
    rows = _pairs_halves(FIXED_ROWS[family]() if form == FIXED_FORM else ROWS[family](form))
    assert len(rows) == 24 and sum(r["kind"] == "anchor" for r in rows) == 4
    items = {k: np.array([r[k] for r in rows]) for k in rows[0] if k != "data"}
    items["data"] = np.array([json.dumps(r["data"]) for r in rows])
    items["family"] = np.array([family] * len(rows))
    items["form"] = np.array([form] * len(rows))
    items["response"] = np.array(["probability"] * len(rows))
    return items


def data(items, i):
    return json.loads(str(items["data"][i]))


def predict(family, items, params):
    """Predicted probability for every item (anchors: their determinate answers). Form c is
    predicted by the revised observers; forms a and b by the observers they were designed with."""
    models = OBSERVERS if str(items["form"][0]) == FIXED_FORM else MODELS
    out = np.zeros(len(items["kind"]))
    for i in range(len(out)):
        if items["kind"][i] == "anchor":
            out[i] = items["answer"][i]
        else:
            out[i] = models[family](data(items, i), params)
    return out


@functools.cache
def _openness(family, form, draws=200):
    items = _design(family, form)
    rng = np.random.default_rng(20261101 + FAMILIES.index(family))
    sampler = observer_draw if form == FIXED_FORM else draw
    preds = np.array([predict(family, items, p) for p in sampler(family, rng, draws)])
    z = logit(preds)
    return np.percentile(z, 90, axis=0) - np.percentile(z, 10, axis=0)


def openness(family, form):
    return _openness(family, form).copy()


# Scoring.
def transformed(items, responses):
    y = np.asarray(responses, dtype=float)
    k = np.asarray(items["k"], dtype=float)
    residual = np.asarray(items["transform"]) == "residual"
    return np.where(residual, logit(1 - k * y), logit(y))


def contrast_scores(items, responses):
    """Each contrast's score (mean log-odds of the plus set minus that of the minus set) and its
    split-half standard error (half the difference between the two matched halves)."""
    family = str(items["family"][0])
    z = transformed(items, responses)
    out = {}
    for j, name in enumerate(SPEC[family]["contrasts"], start=1):
        sign = np.asarray(items[f"c{j}"])
        half = np.asarray(items[f"h{j}"])

        def score(mask, sign=sign):
            plus = z[mask & (sign == 1)]
            minus = z[mask & (sign == -1)]
            return float(
                (plus.mean() if len(plus) else 0.0) - (minus.mean() if len(minus) else 0.0)
            )

        full = score(np.ones(len(z), dtype=bool))
        halves = [score(half == h) for h in (0, 1)]
        out[name] = {"score": full, "halves": halves, "se": abs(halves[0] - halves[1]) / 2}
    return out


def delta(family, form="a"):
    """Per contrast: the change in its noiseless score produced by moving its driving parameters by
    CHANGE_FRACTION of their plausible range, from the middle of the range."""
    items = _design(family, form)
    base = mid(family)
    reference = contrast_scores(items, predict(family, items, base))
    out = {}
    for name in SPEC[family]["contrasts"]:
        names, sign = SPEC[family]["drivers"][name]
        moved = changed(family, base, names, sign)
        score = contrast_scores(items, predict(family, items, moved))[name]["score"]
        out[name] = abs(score - reference[name]["score"])
    return out


def session(items, responses):
    family = str(items["family"][0])
    responses = np.asarray(responses, dtype=float)
    anchors = np.asarray(items["kind"]) == "anchor"
    errors = np.abs(responses[anchors] - np.asarray(items["answer"], dtype=float)[anchors])
    return {
        "family": family,
        "form": str(items["form"][0]),
        "contrasts": contrast_scores(items, responses),
        "anchor_errors": [float(e) for e in errors],
        "anchors_ok": bool(np.all(errors <= ANCHOR_TOLERANCE + 1e-9)),
        "open_responses": [float(v) for v in responses[np.asarray(items["kind"]) == "open"]],
        "fixed_responses": [float(v) for v in responses[np.asarray(items["kind"]) == "fixed"]],
    }


def respond(family, items, params, rng, noise=0.3):
    """A simulated respondent: the family's model, log-odds report noise, whole percentages."""
    prediction = predict(family, items, params)
    anchors = np.asarray(items["kind"]) == "anchor"
    z = logit(prediction) + rng.normal(0, noise, len(prediction))
    out = np.where(anchors, prediction, _sigmoid(z))
    return np.clip(np.round(out, 2), 0, 1)


# Profile fit: each family's Bayesian observer fitted to a configuration's sessions (both forms), by
# a grid posterior over its parameters and the report noise (flat priors). Responses are modelled as
# logit(y) ~ Normal(logit(prediction), report_noise).
FIT_GRID = {
    "gen": {
        "rule_weight": np.linspace(0.1, 0.9, 9),
        "sampling": np.linspace(0.0, 1.0, 9),
        "interval_scale": np.array([5.0, 10.0, 15.0, 20.0]),
    },
    "num": {
        "person_exact": np.linspace(0.1, 0.9, 9),
        "instrument_exact": np.linspace(0.4, 1.0, 9),
        "precision": np.geomspace(0.002, 0.03, 7),
    },
    "choice": {
        "rationality": np.geomspace(0.5, 30.0, 10),
        "knowledge_prior": np.linspace(0.2, 0.8, 9),
        "cost_trivial": np.array([0.01, 0.03, 0.05]),
        "cost_moderate": np.array([0.08, 0.14, 0.2]),
        "cost_large": np.array([0.3, 0.45, 0.6]),
    },
    "lists": {
        "residual_manual": np.linspace(0.0, 0.4, 11),
        "residual_colleague": np.linspace(0.05, 0.6, 12),
    },
    "trend": {
        "linear_weight": np.linspace(0.2, 0.9, 11),
        "likelihood_weight": np.geomspace(0.2, 5.0, 11),
    },
}
REPORT_NOISE = np.array([0.1, 0.2, 0.3, 0.5, 0.8])
# The parameters a profile reports (the rest are nuisance, marginalised).
PROFILE = {
    "gen": ("rule_weight", "sampling"),
    "num": ("person_exact", "instrument_exact", "precision"),
    "choice": ("rationality", "knowledge_prior"),
    "lists": ("residual_manual", "residual_colleague"),
    "trend": ("linear_weight", "likelihood_weight"),
}


@functools.cache
def _fit_table(family, forms):
    grid = FIT_GRID[family]
    names = list(grid)
    mesh = np.meshgrid(*[grid[n] for n in names], indexing="ij")
    points = {n: m.ravel() for n, m in zip(names, mesh, strict=True)}
    size = len(points[names[0]])
    columns = []
    for form in forms:
        items = _design(family, form)
        open_items = [i for i in range(len(items["kind"])) if items["kind"][i] == "open"]
        table = np.empty((size, len(open_items)))
        for g in range(size):
            params = {n: float(points[n][g]) for n in names}
            table[g] = [MODELS[family](data(items, i), params) for i in open_items]
        columns.append(logit(table))
    return points, np.concatenate(columns, axis=1)


def _cell_edges(values):
    values = np.asarray(values, dtype=float)
    mids = (values[1:] + values[:-1]) / 2
    return np.concatenate([[values[0]], mids]), np.concatenate([mids, [values[-1]]])


def _marginal(weights, points, values, log):
    probs = np.array([weights[points == v].sum() for v in values])
    probs /= probs.sum()
    scale = np.log(values) if log else values
    mean = float(probs @ scale)
    cdf = np.cumsum(probs)
    lo, hi = np.searchsorted(cdf, [0.05, 0.95])
    lower, upper = _cell_edges(values)
    return {
        "mean": float(np.exp(mean)) if log else mean,
        "interval_90": [
            float(lower[min(lo, len(values) - 1)]),
            float(upper[min(hi, len(values) - 1)]),
        ],
    }


def fit_profile(family, responses, forms=FORMS):
    """responses: {form: 24 responses in design order}. Posterior summaries of every parameter of
    the family's observer and of the report noise."""
    points, table = _fit_table(family, tuple(forms))
    observed = []
    for form in forms:
        items = _design(family, form)
        y = np.asarray(responses[form], dtype=float)
        observed.append(logit(y[np.asarray(items["kind"]) == "open"]))
    z = np.concatenate(observed)
    squares = ((table - z[None, :]) ** 2).sum(axis=1)
    n = len(z)
    loglik = (
        -squares[:, None] / (2 * REPORT_NOISE[None, :] ** 2) - n * np.log(REPORT_NOISE)[None, :]
    )
    post = np.exp(loglik - loglik.max())
    post /= post.sum()
    by_point = post.sum(axis=1)
    out = {}
    for name, values in FIT_GRID[family].items():
        log = SPEC[family]["params"][name][0] == "log"
        out[name] = _marginal(by_point, points[name], values, log)
    noise = post.sum(axis=0)
    out["report_noise"] = {"mean": float(noise @ REPORT_NOISE)}
    return out
