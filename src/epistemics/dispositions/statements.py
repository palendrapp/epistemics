"""Central-bank statements as sequential evidence (model 0.20, design 0.21;
docs/statement-updating-design.md).

A sequence is a previous policy statement, a stated market prior for a cut at the committee's
next meeting, and the n changes that turn the previous statement into the new one. A change moves
one slot (activity, inflation, risks, forward guidance, the vote) one level in the dovish (+1,
towards a cut) or hawkish (-1) direction, or rewords a sentence without changing its meaning
(stylistic, direction 0).

A form has six sequences, with 1 to 6 changes, in three groups of two ({1, 6}, {2, 5}, {3, 4}:
7 changes each). Module statement-<form><r> is session r of a Latin square: each group is shown
stepwise in order A (one change per case), stepwise in order B (A reversed) or whole (all changes
in one case), rotating over r = 1, 2, 3. A session has 9 + 9 stepwise cases, 4 whole-condition
cases and 2 anchors: 24. Stepwise cases show only the newest change.

Model (answers as log-odds ell; the stated market prior ell0):
  prior case   c + gamma ell0
  whole case   c + gamma ell0 + sum_e lambda_e / (1 + eta (n - 1))
  step t       ell_t - ell_{t-1} = beta lambda_{e_t} - (1 - alpha) (ell_{t-1} - ell_(0))
                                  - zeta ell_{t-1} [stylistic changes only]
where lambda_e = w_slot * direction + tilt for a substantive change and 0 for a stylistic one,
ell_(0) is the agent's own answer before any change, and every answer carries log-odds report
noise tau (steps are conditioned on the agent's own previous answer). zeta is dilution: a pull
towards 50% on a change that carries no information. Bayesian combining is gamma = 1, eta = 0,
beta = 1, alpha = 1, zeta = 0. The readings w, the tilt, zeta, c and gamma enter linearly and are
integrated analytically on a grid over (eta, beta, alpha, tau).

Laws that hold whatever the readings: the final answer after the same changes in orders A and B
is equal (order); the final stepwise answer equals the whole-statement answer (path); a stylistic
change moves nothing (content).
"""

import functools

import numpy as np

from epistemics.dispositions.screen import _sigmoid, logit

SLOTS = ("activity", "inflation", "risks", "guidance", "vote")
STYLES = ("opening", "mandate", "action")
# Statement order of the changeable parts; the whole condition lists changes in this order.
POSITION = ("opening", "activity", "inflation", "mandate", "action", "guidance", "risks", "vote")
FORMS = ("a", "b")
ROTATIONS = (1, 2, 3)
CONDITIONS = ("A", "B", "whole")
GROUPS = ((1, 6), (2, 5), (3, 4))  # sequences by number of changes; 7 changes per group
PERIODS = ("before 2005", "between 2005 and 2012", "between 2013 and 2019", "in 2020 or later")
PROBE_LIMIT = 0.6  # a statement placed in one period above this is rewritten
ANCHOR_TOLERANCE = 0.05


def _sequence(sid, prior, levels, styles, background, changes, order):
    """changes: {slot or style: direction}; order: order A, as names."""
    canonical = sorted(changes, key=POSITION.index)
    for name, direction in changes.items():
        if name in STYLES:
            assert direction == 0, (sid, name)
        else:
            assert direction in (-1, 1) and -1 <= levels[name] + direction <= 1, (sid, name)
    assert sorted(order) == sorted(canonical), sid
    return {
        "id": sid,
        "prior": prior,
        "n": len(changes),
        "levels": dict(levels),
        "styles": dict(styles),
        "background": tuple(background),
        "changes": [(name, changes[name]) for name in canonical],
        "order": [canonical.index(name) for name in order],
    }


def _levels(activity=0, inflation=0, risks=0, guidance=0, vote=0):
    return {"activity": activity, "inflation": inflation, "risks": risks, "guidance": guidance,
            "vote": vote}  # fmt: skip


def _styles(opening=0, mandate=0, action=0):
    return {"opening": opening, "mandate": mandate, "action": action}


# Six sequences per form: n = 1..6; 15 substantive changes, each slot three times and in both
# directions; 6 stylistic changes; stated priors 15-70%; mixed directions in about half. Form a
# leans dovish (9 of 15 changes), form b hawkish (10 of 15).
FORM_SPECS = {
    "a": (
        _sequence(31, 30, _levels(), _styles(), (0, 0), {"guidance": -1}, ["guidance"]),
        _sequence(
            32,
            50,
            _levels(activity=1),
            _styles(mandate=1),
            (1, 1),
            {"inflation": -1, "opening": 0},
            ["opening", "inflation"],
        ),
        _sequence(
            33,
            15,
            _levels(inflation=-1),
            _styles(opening=1, mandate=1),
            (2, 0),
            {"activity": 1, "vote": 1, "mandate": 0},
            ["mandate", "vote", "activity"],
        ),
        _sequence(
            34,
            70,
            _levels(activity=-1, inflation=1, risks=1, guidance=1),
            _styles(action=1),
            (3, 2),
            {"activity": 1, "guidance": -1, "risks": -1, "action": 0},
            ["activity", "action", "risks", "guidance"],
        ),
        _sequence(
            35,
            50,
            _levels(),
            _styles(opening=1),
            (0, 1),
            {"inflation": 1, "vote": -1, "risks": 1, "activity": -1, "opening": 0},
            ["vote", "activity", "opening", "inflation", "risks"],
        ),
        _sequence(
            36,
            30,
            _levels(inflation=-1, risks=-1),
            _styles(action=1),
            (1, 2),
            {"guidance": 1, "inflation": 1, "risks": 1, "vote": 1, "mandate": 0, "action": 0},
            ["mandate", "action", "vote", "guidance", "inflation", "risks"],
        ),
    ),
    "b": (
        _sequence(51, 50, _levels(), _styles(opening=1, action=1), (2, 1), {"vote": -1}, ["vote"]),
        _sequence(
            52,
            30,
            _levels(inflation=-1),
            _styles(mandate=1),
            (3, 0),
            {"risks": 1, "action": 0},
            ["action", "risks"],
        ),
        _sequence(
            53,
            70,
            _levels(activity=1, inflation=1, risks=1, guidance=1),
            _styles(),
            (0, 2),
            {"guidance": -1, "inflation": -1, "opening": 0},
            ["guidance", "inflation", "opening"],
        ),
        _sequence(
            54,
            30,
            _levels(),
            _styles(opening=1),
            (1, 0),
            {"activity": -1, "vote": 1, "inflation": 1, "mandate": 0},
            ["activity", "mandate", "vote", "inflation"],
        ),
        _sequence(
            55,
            50,
            _levels(guidance=-1, vote=1),
            _styles(mandate=1, action=1),
            (2, 2),
            {"guidance": 1, "risks": -1, "activity": 1, "vote": -1, "action": 0},
            ["risks", "vote", "action", "guidance", "activity"],
        ),
        _sequence(
            56,
            70,
            _levels(activity=1, risks=1),
            _styles(),
            (3, 1),
            {
                "guidance": -1,
                "inflation": -1,
                "risks": -1,
                "activity": -1,
                "opening": 0,
                "mandate": 0,
            },  # fmt: skip
            ["opening", "mandate", "activity", "guidance", "risks", "inflation"],
        ),
    ),
}


def anchor_spec(form, rotation, j):
    """Anchor j (0: the statement says the committee held, answer 0; 1: it lowered, answer 1):
    a sequence's previous statement with its background and styles shifted."""
    s = FORM_SPECS[form][(2 * (rotation - 1) + 3 * j) % 6]
    b0, b1 = s["background"]
    return {
        "id": (71 if form == "a" else 81) + 2 * (rotation - 1) + j,
        "levels": s["levels"],
        "styles": {k: 1 - v for k, v in s["styles"].items()},
        "background": ((b0 + 1 + j) % 4, (b1 + 1) % 3),
        "action": ("maintain", "lower")[j],
        "answer": float(j),
    }


def condition_of(group, rotation):
    return CONDITIONS[(group + rotation - 1) % 3]


def _rows(form, rotation):
    specs = FORM_SPECS[form]
    by_n = {s["n"]: k for k, s in enumerate(specs)}
    rows = []
    for g, group in enumerate(GROUPS):
        condition = condition_of(g, rotation)
        for n in group:
            k = by_n[n]
            s = specs[k]
            base = {"sequence": k, "sid": s["id"], "n": n, "condition": condition,
                    "prior": s["prior"], "answer": float("nan")}  # fmt: skip
            rows.append({**base, "kind": "prior", "step": 0, "change": -1})
            if condition == "whole":
                rows.append({**base, "kind": "whole", "step": n, "change": -1})
            else:
                order = s["order"] if condition == "A" else s["order"][::-1]
                for t, c in enumerate(order, 1):
                    rows.append({**base, "kind": "step", "step": t, "change": c})
    for j in (0, 1):
        a = anchor_spec(form, rotation, j)
        rows.append({"sequence": -1, "sid": a["id"], "n": 0, "condition": "", "prior": 0,
                     "answer": a["answer"], "kind": "anchor", "step": j, "change": -1})  # fmt: skip
    return rows


def design(form, rotation):
    return {k: v.copy() for k, v in _design(form, int(rotation)).items()}


@functools.cache
def _design(form, rotation):
    rows = _rows(form, rotation)
    assert len(rows) == 24 and sum(r["kind"] == "anchor" for r in rows) == 2, (form, rotation)
    items = {
        k: np.array([r[k] for r in rows])
        for k in ("kind", "sequence", "sid", "n", "condition", "prior", "step", "change", "answer")
    }
    specs = FORM_SPECS[form]
    names, directions = [], []
    for r in rows:
        if r["kind"] == "step":
            name, direction = specs[r["sequence"]]["changes"][r["change"]]
        else:
            name, direction = "", 0
        names.append(name)
        directions.append(direction)
    items["part"] = np.array(names)  # not "slot": ledger extraction reads that as integers
    items["direction"] = np.array(directions)
    items["form"] = np.array([form] * 24)
    items["rotation"] = np.array([rotation] * 24)
    items["response"] = np.array(["probability"] * 24)
    return items


def module_design(module):
    """statement-<form><rotation> or statement-probe-<form>."""
    tail = module.split("-")[-1]
    if module.startswith("statement-probe-"):
        return probe_design(tail)
    return design(tail[0], int(tail[1]))


def sequences_order(items, rng):
    """Each sequence's cases consecutive and in step order; sequences and anchors in random order.
    Uses only shuffle (numpy and random.Random generators both work)."""
    blocks = {}
    for i in range(len(items["kind"])):
        k = int(items["sequence"][i])
        blocks.setdefault(("sequence", k) if k >= 0 else ("anchor", i), []).append(i)
    keys = list(blocks)
    rng.shuffle(keys)
    return [i for key in keys for i in sorted(blocks[key], key=lambda i: int(items["step"][i]))]


# Simulated respondents and the model.
def reading(name, direction, truth):
    if name in STYLES:
        return 0.0
    return truth["w"][name] * direction + truth.get("tilt", 0.0)


def _report(z):
    return float(np.clip(np.round(_sigmoid(z), 2), 0, 1))


def respond(items, truth, rng):
    """A simulated respondent under the model: truth has w (per slot), tilt, c, gamma, eta, beta,
    alpha, tau and optionally dilution (a pull towards 50% on stylistic changes, for power
    checks of the content law). Answers in whole percentages; anchors at their answers."""
    form = str(items["form"][0])
    specs = FORM_SPECS[form]
    tau = truth["tau"]
    out = np.full(len(items["kind"]), np.nan)
    anchors = items["kind"] == "anchor"
    out[anchors] = items["answer"][anchors]
    for k in sorted(set(int(v) for v in items["sequence"]) - {-1}):
        idx = sorted(np.flatnonzero(items["sequence"] == k), key=lambda i: int(items["step"][i]))
        s = specs[k]
        ell0 = float(logit(s["prior"] / 100))
        p0 = _report(truth["c"] + truth["gamma"] * ell0 + rng.normal(0, tau))
        out[idx[0]] = p0
        if str(items["condition"][idx[0]]) == "whole":
            total = sum(reading(name, d, truth) for name, d in s["changes"])
            divisor = 1 + truth["eta"] * (s["n"] - 1)
            z = truth["c"] + truth["gamma"] * ell0 + total / divisor + rng.normal(0, tau)
            out[idx[1]] = _report(z)
            continue
        own = previous = float(logit(p0))
        for i in idx[1:]:
            name, d = s["changes"][int(items["change"][i])]
            z = (
                previous
                + truth["beta"] * reading(name, d, truth)
                - (1 - truth["alpha"]) * (previous - own)
                + rng.normal(0, tau)
            )
            if name in STYLES:
                z -= truth.get("dilution", 0.0) * previous
            out[i] = _report(z)
            previous = float(logit(out[i]))
    return out


def sequences(items, responses):
    """Per sequence: its condition, stated prior, the answers in step order, and the changes in
    the order revealed (stepwise) or in statement order (whole)."""
    form = str(items["form"][0])
    specs = FORM_SPECS[form]
    out = []
    for k in sorted(set(int(v) for v in items["sequence"]) - {-1}):
        idx = sorted(np.flatnonzero(items["sequence"] == k), key=lambda i: int(items["step"][i]))
        s = specs[k]
        condition = str(items["condition"][idx[0]])
        if condition == "whole":
            changes = s["changes"]
        else:
            changes = [s["changes"][int(items["change"][i])] for i in idx[1:]]
        out.append(
            {
                "sequence": k,
                "sid": s["id"],
                "n": s["n"],
                "prior": s["prior"],
                "condition": condition,
                "answers": [float(responses[i]) for i in idx],
                "changes": [[name, int(d)] for name, d in changes],
            }
        )
    return out


def session(items, responses):
    responses = np.asarray(responses, dtype=float)
    records = sequences(items, responses)
    steps = {slot: [] for slot in SLOTS}
    stylistic = []
    for r in records:
        if r["condition"] == "whole":
            continue
        ell = logit(r["answers"])
        for t, (name, d) in enumerate(r["changes"], 1):
            move = float(ell[t] - ell[t - 1])
            if name in STYLES:
                stylistic.append(move)
            else:
                steps[name].append(move * d)
    anchors = items["kind"] == "anchor"
    errors = np.abs(responses[anchors] - items["answer"][anchors].astype(float))
    return {
        "form": str(items["form"][0]),
        "rotation": int(items["rotation"][0]),
        "sequences": records,
        # Model-free: the mean step on each slot's changes, signed so that the reading of a
        # dovish change is positive (beta times the reading, plus the tilt's sign).
        "step_readings": {s: float(np.mean(v)) for s, v in steps.items() if v},
        "stylistic_steps": stylistic,
        "anchor_errors": [float(e) for e in errors],
        "anchors_ok": bool(np.all(errors <= ANCHOR_TOLERANCE + 1e-9)),
        "responses": [float(v) for v in responses],
    }


# Laws (model-free), over one configuration's three sessions of a form.
def laws(records):
    by = {}
    for r in records:
        by.setdefault(r["sid"], {})[r["condition"]] = r
    order, recency, retest, path, overshoot, content, dilution, prior_var = ([] for _ in range(8))
    for conds in by.values():
        n = next(iter(conds.values()))["n"]
        final = {c: float(logit(r["answers"][-1])) for c, r in conds.items()}
        if "A" in conds and "B" in conds:
            difference = final["A"] - final["B"]
            if n == 1:
                retest.append(difference)  # identical presentations: a retest
            else:
                order.append(difference)
                # Recency: the final answer leans to the last change (A's last is B's first).
                last, first = conds["A"]["changes"][-1][1], conds["A"]["changes"][0][1]
                if last != first:
                    recency.append(difference * np.sign(last - first))
        if "whole" in conds:
            whole = conds["whole"]
            move = final["whole"] - float(logit(whole["answers"][0]))
            for c in ("A", "B"):
                if c in conds:
                    d = final[c] - final["whole"]
                    path.append(d)
                    if abs(move) > 0.05:
                        overshoot.append(d * np.sign(move))
        priors = [float(logit(r["answers"][0])) for r in conds.values()]
        if len(priors) > 1:
            prior_var.append(float(np.var(priors, ddof=1)))
        for c in ("A", "B"):
            if c in conds:
                ell = logit(conds[c]["answers"])
                for t, (name, _) in enumerate(conds[c]["changes"], 1):
                    if name in STYLES:
                        step = float(ell[t] - ell[t - 1])
                        content.append(step)
                        dilution.append(-step * float(np.sign(ell[t - 1])))

    def mean(v, f=lambda x: x):
        return float(np.mean([f(x) for x in v])) if v else None

    return {
        "order": mean(order, abs),
        "recency": mean(recency),
        "path": mean(path, abs),
        "overshoot": mean(overshoot),
        "content": mean(content, abs),
        "dilution": mean(dilution),
        "retest": mean(retest, abs),
        "prior_sd": float(np.sqrt(np.mean(prior_var))) if prior_var else None,
        "counts": {"order": len(order), "path": len(path), "content": len(content)},
    }


# The fit: grid over (eta, beta, alpha, tau); c, gamma, the readings and the tilt analytically.
# Grids fine enough that a sharp posterior is not forced onto a coarse point (validation: with
# alpha in steps of 0.1 its 90% intervals covered the truth 63% of the time); grid intervals are
# widened by half a step.
ETA = np.round(np.arange(0.0, 1.0001, 0.05), 3)
BETA = np.round(np.arange(0.25, 2.0001, 0.0625), 4)
ALPHA = np.round(np.arange(0.4, 1.0001, 0.05), 3)
TAU = np.array([0.05, 0.075, 0.1, 0.125, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2])
NAMES = ("c", "gamma", *(f"w_{s}" for s in SLOTS), "tilt", "dilution")
WIDTH = len(NAMES)
M0 = np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
S0 = np.diag(np.array([1.0, 0.5, 1.5, 1.5, 1.5, 1.5, 1.5, 0.5, 0.3]) ** 2)


def _fit_arrays(records):
    """Prior, whole and step rows. Prior and whole rows have X m0 = ell0 (M0 has gamma 1)."""
    prior_x, prior_r, whole, steps = [], [], [], []
    for r in records:
        ell0 = float(logit(r["prior"] / 100))
        ell = logit(r["answers"])
        prior_x.append([1.0, ell0] + [0.0] * (WIDTH - 2))
        prior_r.append(float(ell[0]) - ell0)
        if r["condition"] == "whole":
            counts = np.zeros(len(SLOTS))
            for name, d in r["changes"]:
                if name in SLOTS:
                    counts[SLOTS.index(name)] += d
            m = sum(name in SLOTS for name, _ in r["changes"])
            whole.append((ell0, counts, m, r["n"], float(ell[1]) - ell0))
            continue
        for t, (name, d) in enumerate(r["changes"], 1):
            x = np.zeros(WIDTH)
            if name in SLOTS:
                x[2 + SLOTS.index(name)] = d
                x[7] = 1.0
            else:
                x[8] = -float(ell[t - 1])  # dilution: a pull towards 50%
            steps.append((x, float(ell[t] - ell[t - 1]), float(ell[t - 1] - ell[0])))
    return np.array(prior_x), np.array(prior_r), whole, steps


def _whole_x(whole, eta):
    rows = []
    for ell0, counts, m, n, _ in whole:
        divisor = 1 + eta * (n - 1)
        rows.append([1.0, ell0, *(counts / divisor), m / divisor, 0.0])
    return np.array(rows).reshape(-1, WIDTH)


def _summary(values, weights):
    """Mean and 90% interval of a grid marginal, the interval widened by half a grid step."""
    order = np.argsort(values)
    v, w = np.asarray(values)[order], np.asarray(weights)[order]
    cdf = np.cumsum(w) / np.sum(w)
    lo = min(np.searchsorted(cdf, 0.05), len(v) - 1)
    hi = min(np.searchsorted(cdf, 0.95), len(v) - 1)
    below = (v[lo] - v[lo - 1]) / 2 if lo > 0 else 0.0
    above = (v[hi + 1] - v[hi]) / 2 if hi < len(v) - 1 else 0.0
    return {
        "mean": float(np.sum(v * w) / np.sum(w)),
        "interval_90": [float(v[lo] - below), float(v[hi] + above)],
    }


def fit(records, draws=4000, seed=20261114):
    prior_x, prior_r, whole, steps = _fit_arrays(records)
    whole_r = np.array([w[4] for w in whole])
    step_x = np.array([s[0] for s in steps]).reshape(-1, WIDTH)
    delta = np.array([s[1] for s in steps])
    dev = np.array([s[2] for s in steps])
    n_rows = len(prior_r) + len(whole_r) + len(delta)
    s0inv = np.linalg.inv(S0)
    logdet_s0 = float(np.linalg.slogdet(S0)[1])
    g_p, h_p, q_p = prior_x.T @ prior_x, prior_x.T @ prior_r, float(prior_r @ prior_r)
    g_s = step_x.T @ step_x
    h_sd, h_sv = step_x.T @ delta, step_x.T @ dev
    dd, dv, vv = float(delta @ delta), float(delta @ dev), float(dev @ dev)
    shape = (len(ETA), len(BETA), len(ALPHA), len(TAU))
    logml = np.empty(shape)
    tau2 = TAU**2
    for i, eta in enumerate(ETA):
        xw = _whole_x(whole, eta)
        g_w, h_w, q_w = xw.T @ xw, xw.T @ whole_r, float(whole_r @ whole_r)
        for j, beta in enumerate(BETA):
            g = g_p + g_w + beta**2 * g_s
            a = s0inv[None] + g[None] / tau2[:, None, None]
            chol = np.linalg.cholesky(a)
            logdet_a = 2 * np.sum(np.log(np.diagonal(chol, axis1=1, axis2=2)), axis=1)
            for k, alpha in enumerate(ALPHA):
                leak = 1 - alpha
                h = h_p + h_w + beta * (h_sd + leak * h_sv)
                q = q_p + q_w + dd + 2 * leak * dv + leak**2 * vv
                b = h[None] / tau2[:, None]
                sol = np.linalg.solve(a, b[..., None])[..., 0]
                quad = q / tau2 - np.sum(b * sol, axis=1)
                logml[i, j, k] = (
                    -0.5 * n_rows * np.log(2 * np.pi * tau2)
                    - 0.5 * logdet_s0
                    - 0.5 * logdet_a
                    - 0.5 * quad
                )
    weights = np.exp(logml - logml.max())
    weights /= weights.sum()
    out = {}
    for name, grid, axes in (
        ("eta", ETA, (1, 2, 3)),
        ("beta", BETA, (0, 2, 3)),
        ("alpha", ALPHA, (0, 1, 3)),
        ("tau", TAU, (0, 1, 2)),
    ):
        out[name] = _summary(grid, weights.sum(axis=axes))
    # The linear parameters: a mixture of Gaussians over the grid, sampled.
    rng = np.random.default_rng(seed)
    flat = weights.ravel()
    picks = rng.choice(flat.size, size=draws, p=flat)
    samples = []
    for point, count in zip(*np.unique(picks, return_counts=True), strict=True):
        i, j, k, m = np.unravel_index(point, shape)
        xw = _whole_x(whole, ETA[i])
        leak = 1 - ALPHA[k]
        g = g_p + xw.T @ xw + BETA[j] ** 2 * g_s
        h = h_p + xw.T @ whole_r + BETA[j] * (h_sd + leak * h_sv)
        cov = np.linalg.inv(s0inv + g / tau2[m])
        mean = M0 + cov @ (h / tau2[m])
        samples.append(rng.multivariate_normal(mean, cov, size=int(count)))
    samples = np.vstack(samples)
    for p, name in enumerate(NAMES):
        v = samples[:, p]
        out[name] = {
            "mean": float(np.mean(v)),
            "interval_90": [float(np.percentile(v, 5)), float(np.percentile(v, 95))],
        }
    out["answers"] = int(n_rows)
    return out


def truth_from_fit(fitted, bayesian=True):
    """Posterior means as a simulated respondent; with bayesian, combining is set to the norm
    (eta 0, beta 1, alpha 1, no dilution): the null of the law tests."""
    t = {
        "w": {s: fitted[f"w_{s}"]["mean"] for s in SLOTS},
        "tilt": fitted["tilt"]["mean"],
        "c": fitted["c"]["mean"],
        "gamma": fitted["gamma"]["mean"],
        "tau": fitted["tau"]["mean"],
    }
    if bayesian:
        return {**t, "eta": 0.0, "beta": 1.0, "alpha": 1.0, "dilution": 0.0}
    return {**t, **{k: fitted[k]["mean"] for k in ("eta", "beta", "alpha", "dilution")}}


# The datability probe: each sequence's previous and new statements, four periods.
def probe_design(form):
    return {k: v.copy() for k, v in _probe_design(form).items()}


@functools.cache
def _probe_design(form):
    rows = [(k, p) for k in range(6) for p in range(len(PERIODS))]
    return {
        "kind": np.array(["period"] * 24),
        "sequence": np.array([k for k, _ in rows]),
        "sid": np.array([FORM_SPECS[form][k]["id"] for k, _ in rows]),
        "period": np.array([p for _, p in rows]),
        "answer": np.full(24, np.nan),
        "form": np.array([form] * 24),
        "response": np.array(["probability"] * 24),
    }


def respond_probe(items, truth, rng):
    """truth["periods"]: one probability per period, for every statement."""
    return np.array([float(np.round(truth["periods"][int(p)], 2)) for p in items["period"]])


def probe_session(items, responses):
    out = []
    for k in range(6):
        idx = sorted(np.flatnonzero(items["sequence"] == k), key=lambda i: int(items["period"][i]))
        probs = [float(responses[i]) for i in idx]
        out.append(
            {
                "sid": int(items["sid"][idx[0]]),
                "periods": dict(zip(PERIODS, probs, strict=True)),
                "sum": float(np.sum(probs)),
                "max": float(np.max(probs)),
                "flagged": bool(np.max(probs) > PROBE_LIMIT),
            }
        )
    return {
        "form": str(items["form"][0]),
        "statements": out,
        "flagged": [s["sid"] for s in out if s["flagged"]],
        "responses": [float(v) for v in responses],
    }
