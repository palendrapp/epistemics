"""Coherence sets (model 0.19, design 0.20; docs/screen-coherence-design.md).

A coherence set is a few questions about one unstated model whose answers are tied by a law of
probability that holds whatever the model: a partition sums to 1, a disjunction of disjoint
events equals the sum of its parts, P(A) + P(B) - P(A and B) - P(A or B) = 0, a narrow window
cannot exceed a wide one. Each question is its own case (same text, different question). Sets
are open (their answers depend on the family observer's parameters) or computable (fixed under
it).

The coherence fit uses the laws only, not the family observers: each set's events are sums of
disjoint atoms with a uniform Dirichlet prior over the atom probabilities, and the reported
probability is the Bayesian sampler's expected estimate (1 - 2 d) p + d (Zhu, Sanborn & Chater
2020; shrinkage d = beta / (N + 2 beta)) plus log-odds report noise tau. d is the incoherent bias,
tau the variance; under the sampler a k-part partition sums to 1 + (k - 2) d on average.
"""

import functools
import json
import math

import numpy as np

from epistemics.dispositions import screen

FAMILIES = ("num", "lists", "trend")
FORMS = ("d", "e")
D_GRID = np.round(np.arange(0.0, 0.3001, 0.02), 2)
# Evenness of beliefs over a set's atoms: Dirichlet(alpha, ..., alpha), alpha integrated out (flat
# over this grid). With alpha fixed at 1, coherent beliefs spread evenly over the parts (as over
# listed causes) read as shrinkage: 42% of coherent simulated respondents were called incoherent.
ALPHA_GRID = np.array([0.5, 1.0, 3.0, 10.0, 30.0])
TAU_GRID = np.array([0.05, 0.1, 0.2, 0.3, 0.5, 0.8])
SAMPLES = 2000
LOW, HIGH = -1e9, 1e9
MIN_DISTANCE = 4  # members of a set are at least this many cases apart


def _member(set_id, law, computable, atoms, n_atoms, data):
    return {
        "kind": "member",
        "set": set_id,
        "law": law,
        "computable": computable,
        "atoms": atoms,
        "n_atoms": n_atoms,
        "answer": float("nan"),
        "data": data,
    }


def _anchor(data, answer):
    return {
        "kind": "anchor",
        "set": -1,
        "law": "anchor",
        "computable": 1,
        "atoms": [],
        "n_atoms": 0,
        "answer": answer,
        "data": data,
    }


def _partition(set_id, computable, datas):
    return [
        _member(set_id, "partition", computable, [j], len(datas), d) for j, d in enumerate(datas)
    ]


def _identity(set_id, datas):
    """datas: A, B, A and B, A or B. Atoms: A only, B only, both, neither."""
    atoms = ([0, 2], [1, 2], [2], [0, 1, 2])
    return [_member(set_id, "identity", 0, a, 4, d) for a, d in zip(atoms, datas, strict=True)]


def _nesting(set_id, datas):
    """datas: narrow, wide. Atoms: narrow, wide minus narrow, outside."""
    return [
        _member(set_id, "nesting", 0, a, 3, d) for a, d in zip(([0], [0, 1]), datas, strict=True)
    ]


def _disjunction(set_id, datas):
    """datas: A, B, A or B (disjoint A and B). Atoms: A, B, rest."""
    return [
        _member(set_id, "disjunction", 0, a, 3, d)
        for a, d in zip(([0], [1], [0, 1]), datas, strict=True)
    ]


# F2: (value, quantity, source, sharp, speaker); bins as (lo, hi) with LOW/HIGH for open ends.
def _num_data(value, quantity, source, sharp, speaker, window):
    return {
        "value": value,
        "quantity": quantity,
        "source": source,
        "sharp": sharp,
        "unit": 10 if value < 100 else 100,
        "speaker": speaker,
        "window": list(window),
    }


NUM = {
    "d": {
        "partition3": ((30, 0, "person", False, 0), [(LOW, 28), (28, 32), (32, HIGH)]),
        "partition5": (
            (200, 3, "person", False, 1),
            [(LOW, 179.5), (179.5, 194.5), (194.5, 205.5), (205.5, 220.5), (220.5, HIGH)],
        ),
        "identity": ((60, 2, "person", False, 2), [(56, 61), (59, 64), (59, 61), (56, 64)]),
        "nesting": ((43, 1, "person", True, 3), [(42, 44), (40, 46)]),
        "complement": ((40, 4, "person", False, 0), [(40, HIGH), (LOW, 40)]),
        "computable": (
            (500, 5, "instrument", False, 0),
            [(LOW, 99.5), (99.5, 299.5), (299.5, 700.5), (700.5, HIGH)],
        ),
        "anchors": [
            ("rounds", 40, 1, ("between", 34, 46), 1.0),
            ("rounds", 40, 1, ("above", 50), 0.0),
            ("exact", 31, 3, ("between", 30, 32), 1.0),
            ("exact", 31, 3, ("below", 25), 0.0),
        ],
    },
    "e": {
        "partition3": ((50, 1, "person", False, 1), [(LOW, 47), (47, 53), (53, HIGH)]),
        "partition5": (
            (300, 3, "person", False, 2),
            [(LOW, 269.5), (269.5, 294.5), (294.5, 305.5), (305.5, 330.5), (330.5, HIGH)],
        ),
        "identity": ((80, 0, "person", False, 3), [(75, 81), (79, 85), (79, 81), (75, 85)]),
        "nesting": ((58, 2, "person", True, 0), [(57, 59), (55, 61)]),
        "complement": ((70, 4, "person", False, 1), [(70, HIGH), (LOW, 70)]),
        "computable": (
            (400, 5, "instrument", False, 0),
            [(LOW, 99.5), (99.5, 249.5), (249.5, 550.5), (550.5, HIGH)],
        ),
        "anchors": [
            ("rounds", 80, 4, ("between", 74, 86), 1.0),
            ("rounds", 80, 4, ("above", 90), 0.0),
            ("exact", 47, 3, ("between", 46, 48), 1.0),
            ("exact", 47, 3, ("below", 40), 0.0),
        ],
    },
}


def _num_rows(form):
    spec = NUM[form]
    rows = []

    def datas(key):
        head, windows = spec[key]
        return [_num_data(*head, w) for w in windows]

    rows += _partition(0, 0, datas("partition3"))
    rows += _partition(1, 0, datas("partition5"))
    rows += _identity(2, datas("identity"))
    rows += _nesting(3, datas("nesting"))
    complement = datas("complement")
    complement[1]["span"] = "atmost"  # "40 or less", the complement of "more than 40"
    rows += [_member(4, "complement", 1, [j], 2, d) for j, d in enumerate(complement)]
    rows += _partition(5, 1, datas("computable"))
    for kind, value, quantity, bounds, answer in spec["anchors"]:
        rows.append(
            _anchor(
                {"value": value, "anchor": kind, "quantity": quantity, "bounds": bounds}, answer
            )
        )
    return rows


# F4: (domain, source, k, rotate) per set.
LISTS = {
    "d": {
        "p2": (0, "manual", 2, 0),
        "p3": (1, "colleague", 3, 1),
        "p5": (2, "manual", 5, 0),
        "or": (3, "colleague", 4, 0),
        "conditional": (4, "manual", 4, 1),
    },
    "e": {
        "p2": (2, "colleague", 2, 1),
        "p3": (3, "manual", 3, 0),
        "p5": (4, "colleague", 5, 2),
        "or": (0, "manual", 4, 1),
        "conditional": (1, "colleague", 4, 0),
    },
}


def _lists_data(domain, source, k, rotate, question, named=()):
    return {
        "domain": domain,
        "source": source,
        "k": k,
        "rotate": rotate,
        "question": question,
        "named": list(named),
    }


def _lists_rows(form):
    spec = LISTS[form]
    rows = []
    for set_id, key in enumerate(("p2", "p3", "p5")):
        domain, source, k, rotate = spec[key]
        datas = [_lists_data(domain, source, k, rotate, "listed", [j]) for j in range(k)]
        datas.append(_lists_data(domain, source, k, rotate, "none"))
        rows += _partition(set_id, 0, datas)
    domain, source, k, rotate = spec["or"]
    rows += _disjunction(
        3,
        [
            _lists_data(domain, source, k, rotate, "listed", [0]),
            _lists_data(domain, source, k, rotate, "listed", [1]),
            _lists_data(domain, source, k, rotate, "listed", [0, 1]),
        ],
    )
    domain, source, k, rotate = spec["conditional"]
    rows += _partition(
        4, 1, [_lists_data(domain, source, k, rotate, "conditional", [j]) for j in range(k)]
    )
    for domain, k, question, answer in (
        (0, 3, "listed", 1 / 3),
        (0, 3, "none", 0.0),
        (3, 2, "listed", 0.5),
        (3, 2, "none", 0.0),
    ):
        rows.append(
            _anchor(
                {
                    "domain": domain,
                    "k": k,
                    "question": question,
                    "exhaustive": True,
                    "rotate": 0,
                    "form": form,
                    "source": "record",
                },
                answer,
            )
        )
    return rows


# F5: (series, time, surface) and bins ("below" t, "within" (a, b), "above" t).
TREND = {
    "d": {
        "partition3": (((4, 8, 16), 8, 0), [("below", 70), ("within", (70, 300)), ("above", 300)]),
        "partition5": (
            ((8, 12, 18), 8, 1),
            [
                ("below", 40),
                ("within", (40, 60)),
                ("within", (60, 90)),
                ("within", (90, 130)),
                ("above", 130),
            ],
        ),
        "identity": (
            ((10, 20, 30), 10, 2),
            [
                ("within", (90, 105)),
                ("within", (95, 110)),
                ("within", (95, 105)),
                ("within", (90, 110)),
            ],
        ),
        "nesting": (((12, 24, 36), 6, 3), [("within", (70, 74)), ("within", (60, 84))]),
        "computable1": (
            ((4, 8, 16), 8, 4),
            [("below", 10), ("within", (10, 5000)), ("above", 5000)],
        ),
        "computable2": (
            ((10, 20, 30), 5, 0),
            [("below", 20), ("within", (20, 500)), ("above", 500)],
        ),
        "anchors": [
            (0, (10, 15, 20), 8, 40, 1.0),
            (0, (10, 15, 20), 8, 50, 0.0),
            (1, (12, 16, 20), 10, 40, 1.0),
            (1, (12, 16, 20), 10, 50, 0.0),
        ],
    },
    "e": {
        "partition3": (((3, 6, 12), 8, 1), [("below", 50), ("within", (50, 200)), ("above", 200)]),
        "partition5": (
            ((12, 18, 27), 8, 2),
            [
                ("below", 50),
                ("within", (50, 80)),
                ("within", (80, 120)),
                ("within", (120, 180)),
                ("above", 180),
            ],
        ),
        "identity": (
            ((15, 30, 45), 10, 3),
            [
                ("within", (135, 157)),
                ("within", (143, 165)),
                ("within", (143, 157)),
                ("within", (135, 165)),
            ],
        ),
        "nesting": (((8, 16, 24), 6, 4), [("within", (47, 49)), ("within", (40, 56))]),
        "computable1": (
            ((6, 12, 24), 8, 0),
            [("below", 15), ("within", (15, 8000)), ("above", 8000)],
        ),
        "computable2": (
            ((12, 24, 36), 5, 1),
            [("below", 24), ("within", (24, 600)), ("above", 600)],
        ),
        "anchors": [
            (2, (30, 36, 42), 8, 70, 1.0),
            (2, (30, 36, 42), 8, 80, 0.0),
            (3, (100, 110, 120), 10, 180, 1.0),
            (3, (100, 110, 120), 10, 200, 0.0),
        ],
    },
}


def _trend_data(series, time, surface, bin_):
    kind, value = bin_
    d = {"xs": (1, 2, 3), "ys": series, "x": time, "surface": surface, "bin": kind}
    if kind == "above":
        d.update(question="above", threshold=value)
    elif kind == "below":
        d.update(question="within", window=[1e-9, value])
    else:
        d.update(question="within", window=list(value))
    return d


def _trend_rows(form):
    spec = TREND[form]
    rows = []

    def datas(key):
        (series, time, surface), bins = spec[key]
        return [_trend_data(series, time, surface, b) for b in bins]

    rows += _partition(0, 0, datas("partition3"))
    rows += _partition(1, 0, datas("partition5"))
    rows += _identity(2, datas("identity"))
    rows += _nesting(3, datas("nesting"))
    rows += _partition(4, 1, datas("computable1"))
    rows += _partition(5, 1, datas("computable2"))
    for surface, ys, x_star, threshold, answer in spec["anchors"]:
        rows.append(
            _anchor(
                {
                    "xs": (1, 2, 3),
                    "ys": ys,
                    "x": x_star,
                    "question": "above",
                    "threshold": threshold,
                    "surface": surface,
                    "exact": True,
                },
                answer,
            )
        )
    return rows


ROWS = {"num": _num_rows, "lists": _lists_rows, "trend": _trend_rows}


def design(family, form):
    return {k: v.copy() for k, v in _design(family, form).items()}


@functools.cache
def _design(family, form):
    rows = ROWS[family](form)
    assert len(rows) == 24 and sum(r["kind"] == "anchor" for r in rows) == 4, (family, form)
    items = {
        k: np.array([r[k] for r in rows])
        for k in ("kind", "set", "law", "computable", "n_atoms", "answer")
    }
    items["atoms"] = np.array([json.dumps(r["atoms"]) for r in rows])
    items["data"] = np.array([json.dumps(r["data"]) for r in rows])
    items["family"] = np.array([family] * 24)
    items["form"] = np.array([form] * 24)
    items["response"] = np.array(["probability"] * 24)
    return items


def data(items, i):
    return json.loads(str(items["data"][i]))


def sets(items):
    """[(set id, member indices, member x atom matrix, computable, law)]."""
    out = []
    for s in sorted(set(int(v) for v in items["set"]) - {-1}):
        idx = [int(i) for i in np.flatnonzero(items["set"] == s)]
        n = int(items["n_atoms"][idx[0]])
        matrix = np.zeros((len(idx), n))
        for r, i in enumerate(idx):
            matrix[r, json.loads(str(items["atoms"][i]))] = 1.0
        out.append((s, idx, matrix, int(items["computable"][idx[0]]), str(items["law"][idx[0]])))
    return out


# The family observers' probability for one member (simulated respondents and the audit).
def _lists_observer(d, p):
    if d["question"] == "conditional":
        return len(d["named"]) / d["k"]
    rho = p["residual_colleague"] if d["source"] == "colleague" else p["residual_manual"]
    if d["question"] == "none":
        return rho
    return len(d["named"]) * (1 - rho) / d["k"]


def observer(family, d, p):
    if family == "lists":
        return _lists_observer(d, p)
    return screen.OBSERVERS[family](d, p)


def predict(family, items, params):
    out = np.zeros(len(items["kind"]))
    for i in range(len(out)):
        out[i] = (
            items["answer"][i]
            if items["kind"][i] == "anchor"
            else observer(family, data(items, i), params)
        )
    return out


@functools.cache
def openness(family, form, draws=200):
    items = _design(family, form)
    rng = np.random.default_rng(20261110 + FAMILIES.index(family))
    preds = np.array([predict(family, items, p) for p in screen.observer_draw(family, rng, draws)])
    z = screen.logit(preds)
    return np.percentile(z, 90, axis=0) - np.percentile(z, 10, axis=0)


def respond(family, items, truth, rng):
    """A simulated respondent: the family observer's probabilities (coherent), shrunk by the
    sampler's d, with log-odds report noise tau, in whole percentages."""
    p = predict(family, items, truth["params"])
    anchors = np.asarray(items["kind"]) == "anchor"
    q = (1 - 2 * truth["d"]) * p + truth["d"]
    z = screen.logit(q) + rng.normal(0, truth["tau"], len(p))
    out = np.where(anchors, p, screen._sigmoid(z))
    return np.clip(np.round(out, 2), 0, 1)


@functools.cache
def _atom_draws(n_atoms, alpha, seed=20261111):
    rng = np.random.default_rng(seed + n_atoms + int(10 * alpha))
    return rng.dirichlet(np.full(n_atoms, alpha), SAMPLES)


def set_loglik(matrix, z):
    """log p(z | alpha, d, tau) for one set, over ALPHA_GRID x D_GRID x TAU_GRID, marginalising
    the atoms."""
    out = []
    m = len(z)
    tau = TAU_GRID[None, None, :]
    for alpha in ALPHA_GRID:
        probs = _atom_draws(matrix.shape[1], float(alpha)) @ matrix.T  # (samples, members)
        q = (1 - 2 * D_GRID[:, None, None]) * probs[None] + D_GRID[:, None, None]  # (d, s, m)
        sq = ((screen.logit(q) - z[None, None, :]) ** 2).sum(axis=-1)  # (d, s)
        ll = -sq[..., None] / (2 * tau**2) - m * np.log(tau) - 0.5 * m * math.log(2 * math.pi)
        top = ll.max(axis=1, keepdims=True)
        out.append(top[:, 0, :] + np.log(np.exp(ll - top).mean(axis=1)))  # (d, tau)
    return np.array(out)  # (alpha, d, tau)


def _summary(probs, grid):
    cdf = np.cumsum(probs)
    lo, hi = np.searchsorted(cdf, [0.05, 0.95])
    edges_lo, edges_hi = screen._cell_edges(grid)
    return {
        "mean": float(probs @ grid),
        "interval_90": [
            float(edges_lo[min(lo, len(grid) - 1)]),
            float(edges_hi[min(hi, len(grid) - 1)]),
        ],
    }


def fit(items, responses, kinds=("open", "computable")):
    """Grid posterior of (d, tau) from the sets of the given kinds, flat priors; the evenness
    alpha is shared by the session's sets and integrated out."""
    responses = np.asarray(responses, dtype=float)
    total = np.zeros((len(ALPHA_GRID), len(D_GRID), len(TAU_GRID)))
    used = 0
    for _, idx, matrix, computable, _ in sets(items):
        if ("computable" if computable else "open") not in kinds:
            continue
        total += set_loglik(matrix, screen.logit(responses[idx]))
        used += 1
    post = np.exp(total - total.max())
    post /= post.sum()
    return {
        "d": _summary(post.sum(axis=(0, 2)), D_GRID),
        "tau": _summary(post.sum(axis=(0, 1)), TAU_GRID),
        "alpha": _summary(post.sum(axis=(1, 2)), ALPHA_GRID),
        "sets": used,
    }


def descriptives(items, responses):
    """Model-free: per set, the law's residual (partition and disjunction excess, the identity's
    value, the nesting violation)."""
    responses = np.asarray(responses, dtype=float)
    out = []
    for s, idx, _matrix, computable, law in sets(items):
        y = responses[idx]
        if law in ("partition", "complement"):
            value = float(y.sum() - 1)
        elif law == "disjunction":
            value = float(y[0] + y[1] - y[2])
        elif law == "identity":
            value = float(y[0] + y[1] - y[2] - y[3])
        else:  # nesting: narrow minus wide (positive is a violation)
            value = float(y[0] - y[1])
        out.append(
            {
                "set": s,
                "law": law,
                "computable": computable,
                "members": len(idx),
                "residual": value,
                "answers": [float(v) for v in y],
            }
        )
    return out


def session(items, responses):
    responses = np.asarray(responses, dtype=float)
    anchors = np.asarray(items["kind"]) == "anchor"
    errors = np.abs(responses[anchors] - np.asarray(items["answer"], dtype=float)[anchors])
    return {
        "family": str(items["family"][0]),
        "form": str(items["form"][0]),
        "sets": descriptives(items, responses),
        "open": fit(items, responses, ("open",)),
        "computable": fit(items, responses, ("computable",)),
        "anchor_errors": [float(e) for e in errors],
        "anchors_ok": bool(np.all(errors <= screen.ANCHOR_TOLERANCE + 1e-9)),
        "all": fit(items, responses),
        "responses": [float(v) for v in responses],
    }


def sets_order(items, rng, attempts=500):
    """A random order with the members of each set at least MIN_DISTANCE cases apart. Sets are
    placed largest first, each member at a random free position far enough from its set-mates;
    the rest fill the gaps. Uses only shuffle (numpy and random.Random generators both work)."""
    n = len(items["kind"])
    groups = {}
    for i in range(n):
        groups.setdefault(int(items["set"][i]), []).append(i)
    multi = sorted((g for s, g in groups.items() if s >= 0 and len(g) > 1), key=len, reverse=True)
    singles = [i for s, g in groups.items() for i in g if s < 0 or len(g) == 1]
    for _ in range(attempts):
        slots = [None] * n
        ok = True
        for group in multi:
            members = list(group)
            rng.shuffle(members)
            taken = []
            for item in members:
                free = [
                    k
                    for k in range(n)
                    if slots[k] is None and all(abs(k - t) >= MIN_DISTANCE for t in taken)
                ]
                if not free:
                    ok = False
                    break
                rng.shuffle(free)
                slots[free[0]] = item
                taken.append(free[0])
            if not ok:
                break
        if not ok:
            continue
        rest = list(singles)
        rng.shuffle(rest)
        for k in range(n):
            if slots[k] is None:
                slots[k] = rest.pop()
        return slots
    raise ValueError("No order keeps every set's members apart")
