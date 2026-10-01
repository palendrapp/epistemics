"""Observers v3 for the open-inference screen (docs/open-inference-screen-design.md, "Observers
v3"): developed on the fallback round's findings, analysis-side only.

1. Uncertainty-triggered fallback. The fallback round showed configurations hedge towards a
   default only on open items (trust <= 0.11 on fixed-answer items against 0.2-0.8 on open ones).
   On item i the reported probability is (1 - m g_i) p_i + m g_i d, where g_i = o_i / (o_i + 1)
   and o_i is the item's openness under the observer (the spread of its answer across the
   plausible parameters; a design property). Fixed items get no fallback; open items up to m.
2. F5, deterministic processes. With prior probability `determinism` the configuration takes the
   process to be exact: every series in the screen is fitted exactly by some function family, and
   the prediction is a point mass at that family's projection ("above" is strictly false at the
   projection itself). Otherwise the noisy observer of model 0.18 applies.
"""

import functools
import math

import numpy as np

from epistemics.dispositions import screen
from epistemics.ledger import screen_fit as v2

TRUST = v2.TRUST
FALLBACK = v2.FALLBACK
REPORT_NOISE = v2.REPORT_NOISE
FAMILIES = screen.FIXED_FAMILIES
GRID = {
    "num": v2.GRID["num"],
    "lists": v2.GRID["lists"],
    "trend": {
        "linear_weight": np.linspace(0.2, 0.9, 11),
        "noise": np.geomspace(0.01, 0.3, 11),
        "determinism": np.linspace(0.0, 1.0, 6),
    },
}
PARAMS = {
    "num": screen.OBSERVER_PARAMS["num"],
    "lists": screen.OBSERVER_PARAMS["lists"],
    "trend": {**screen.OBSERVER_PARAMS["trend"], "determinism": (0.0, 1.0)},
}
PROFILE = {
    "num": ("person_exact", "instrument_exact", "precision"),
    "lists": ("residual_manual", "residual_colleague"),
    "trend": ("linear_weight", "noise", "determinism"),
}
MIXTURE = ("trust", "fallback")
TRIGGER_SCALE = 1.0  # log-odds of openness at which half the trust applies
# GATED: the fallback applies in proportion to openness (v3); False: on every non-anchor item, as
# in v2 (the hybrid keeps v2's constant fallback and adds the deterministic-process prior).
GATED = True


def _exact_projection(d):
    """The projection of the function family that fits the readings exactly (the best fit if
    none does)."""
    fits = screen._trend_fits(d["xs"], d["ys"])
    best, best_ssr = None, math.inf
    for name in screen.TREND_FAMILIES:
        design, target, coef, log = fits[name]
        ssr = float(np.sum((target - design @ coef) ** 2)) / max(float(np.mean(target**2)), 1e-12)
        if ssr < best_ssr - 1e-12:
            best, best_ssr = name, ssr
    return screen.trend_projection(d["xs"], d["ys"], d["x"], best)


def _deterministic(d):
    value = _exact_projection(d)
    tolerance = 1e-6 * max(abs(value), 1.0)
    if d["question"] == "above":
        return 1.0 if value > d["threshold"] + tolerance else 0.0
    lo, hi = d["window"]
    return 1.0 if lo - tolerance <= value <= hi + tolerance else 0.0


def observer(family, d, p):
    if family == "trend":
        noisy = screen.OBSERVERS["trend"](d, p)
        delta = p.get("determinism", 0.0)
        return delta * _deterministic(d) + (1 - delta) * noisy
    return screen.OBSERVERS[family](d, p)


@functools.cache
def triggers(family, form):
    """g_i for the non-anchor items: openness under the model 0.18 observer (no determinism)."""
    items = screen._design(family, form)
    rng = np.random.default_rng(20261107 + screen.FAMILIES.index(family))
    draws = screen.observer_draw(family, rng, 200)
    rows = [i for i in range(len(items["kind"])) if items["kind"][i] != "anchor"]
    preds = np.array(
        [[screen.OBSERVERS[family](screen.data(items, i), p) for i in rows] for p in draws]
    )
    z = screen.logit(preds)
    openness = np.percentile(z, 90, axis=0) - np.percentile(z, 10, axis=0)
    if not GATED:
        return np.ones_like(openness)
    return openness / (openness + TRIGGER_SCALE)


def predict(family, items, params):
    out = np.zeros(len(items["kind"]))
    for i in range(len(out)):
        if items["kind"][i] == "anchor":
            out[i] = items["answer"][i]
        else:
            out[i] = observer(family, screen.data(items, i), params)
    return out


def mixed(family, form, p, trust, fallback):
    """Reported probability on the non-anchor items of a form."""
    g = triggers(family, form)
    return (1 - trust * g) * p + trust * g * fallback


def respond(family, form, params, rng, noise=0.3):
    items = screen.design(family, form)
    p = predict(family, items, params)
    rows = np.asarray(items["kind"]) != "anchor"
    out = p.copy()
    q = mixed(family, form, p[rows], params["trust"], params["fallback"])
    out[rows] = screen._sigmoid(screen.logit(q) + rng.normal(0, noise, int(rows.sum())))
    return np.clip(np.round(out, 2), 0, 1)


@functools.cache
def _table(family, forms):
    grid = GRID[family]
    names = list(grid)
    mesh = np.meshgrid(*[grid[n] for n in names], indexing="ij")
    points = {n: m.ravel() for n, m in zip(names, mesh, strict=True)}
    size = len(points[names[0]])
    columns, gates = [], []
    for form in forms:
        items = screen._design(family, form)
        rows = [i for i in range(len(items["kind"])) if items["kind"][i] != "anchor"]
        table = np.empty((size, len(rows)))
        for g in range(size):
            params = {n: float(points[n][g]) for n in names}
            table[g] = [observer(family, screen.data(items, i), params) for i in rows]
        columns.append(table)
        gates.append(triggers(family, form))
    return points, np.concatenate(columns, axis=1), np.concatenate(gates)


def fit(family, responses, forms):
    points, table, g = _table(family, tuple(forms))
    z = v2._observed(family, responses, forms)
    weight = TRUST[None, :, None, None] * g[None, None, None, :]
    probs = (1 - weight) * table[:, None, None, :] + weight * FALLBACK[None, None, :, None]
    loglik = v2._loglik(z, probs)  # (grid, trust, fallback, noise)
    top = loglik.max()
    post = np.exp(loglik - top)
    evidence = float(top + np.log(post.mean()))
    post /= post.sum()
    by_point = post.reshape(post.shape[0], -1).sum(axis=1)
    out = {"evidence": evidence, "parameters": {}}
    for name, values in GRID[family].items():
        log = PARAMS[family][name][0] == "log"
        probs_ = np.array([by_point[points[name] == v].sum() for v in values])
        out["parameters"][name] = {
            "mean": float(np.exp(probs_ @ np.log(values))) if log else float(probs_ @ values),
            "interval_90": v2._interval(probs_, values),
        }
    for name, values, axis in (("trust", TRUST, 1), ("fallback", FALLBACK, 2)):
        probs_ = post.sum(axis=tuple(a for a in range(post.ndim) if a != axis))
        out["parameters"][name] = {
            "mean": float(probs_ @ values),
            "interval_90": v2._interval(probs_, values),
        }
    out["report_noise"] = float(post.sum(axis=(0, 1, 2)) @ REPORT_NOISE)
    return out


def predict_form(family, fitted, form):
    items = screen._design(family, form)
    params = {k: v["mean"] for k, v in fitted["parameters"].items()}
    p = predict(family, items, params)
    rows = np.asarray(items["kind"]) != "anchor"
    return mixed(family, form, p[rows], params["trust"], params["fallback"])


def draw(family, rng, n):
    out = [{} for _ in range(n)]
    for name, spec in PARAMS[family].items():
        if spec[0] == "log":
            values = np.exp(rng.uniform(math.log(spec[1]), math.log(spec[2]), n))
        else:
            values = rng.uniform(spec[0], spec[1], n)
        for k in range(n):
            out[k][name] = float(values[k])
    for k in range(n):
        out[k]["trust"] = float(rng.uniform(0.0, 0.9))
        out[k]["fallback"] = float(rng.uniform(0.1, 0.95))
    return out


def _recovery_family(args):
    family, configs, forms, seed = args
    rng = np.random.default_rng(seed)
    truths = draw(family, rng, configs)
    noises = rng.uniform(0.1, 0.5, configs)
    fits = []
    for truth, noise in zip(truths, noises, strict=True):
        responses = {f: respond(family, f, truth, rng, noise) for f in forms}
        fits.append(fit(family, responses, forms))
    names = list(PARAMS[family]) + list(MIXTURE)
    out = {}
    for name in list(PROFILE[family]) + list(MIXTURE):
        log = name in PARAMS[family] and PARAMS[family][name][0] == "log"
        scale = np.log if log else np.asarray
        estimate = scale(np.array([f["parameters"][name]["mean"] for f in fits]))
        truth = scale(np.array([t[name] for t in truths]))
        inside = [
            f["parameters"][name]["interval_90"][0] - 1e-9
            <= t[name]
            <= f["parameters"][name]["interval_90"][1] + 1e-9
            for f, t in zip(fits, truths, strict=True)
        ]
        confusion = {}
        for other in names:
            other_log = other in PARAMS[family] and PARAMS[family][other][0] == "log"
            values = np.array([t[other] for t in truths])
            confusion[other] = float(
                np.corrcoef(estimate, np.log(values) if other_log else values)[0, 1]
            )
        r = float(np.corrcoef(estimate, truth)[0, 1])
        off = max(abs(v) for k, v in confusion.items() if k != name)
        out[name] = {
            "r": r,
            "coverage_90": float(np.mean(inside)),
            "largest_confusion": off,
            "confusion": confusion,
            "passed": r >= 0.8 and float(np.mean(inside)) >= 0.8 and off <= 0.3,
        }
    return family, "+".join(forms), out


def recovery(configs=200, seed=20261108):
    from concurrent.futures import ProcessPoolExecutor

    seeds = np.random.SeedSequence(seed).spawn(len(FAMILIES))
    jobs = [(f, configs, screen.forms(f), seeds[k]) for k, f in enumerate(FAMILIES)]
    with ProcessPoolExecutor(3) as pool:
        results = list(pool.map(_recovery_family, jobs))
    out = {family: params for family, _, params in results}
    return {
        "schema_version": "epistemics.screen-observers-v3-recovery.v1",
        "configs": configs,
        "families": out,
        "passed": all(p["passed"] for v in out.values() for p in v.values()),
    }


def compare(roots):
    """Observers v2 (constant fallback) against v3 on the collected sessions: report noise and
    evidence with all three forms, and held-out prediction of each of forms a and b from the
    other two forms (log-odds RMSE)."""
    from epistemics.ledger import dispositions

    by = {}
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "screen" not in record:
                continue
            s = record["screen"]
            if s["family"] in FAMILIES:
                by.setdefault((s["family"], record["configuration"]), {})[s["form"]] = np.asarray(
                    record["responses"], dtype=float
                )
    out = {}
    for (family, config), responses in sorted(by.items()):
        forms = screen.forms(family)
        if not all(f in responses for f in forms):
            continue
        entry = {}
        full2 = v2.fit(family, responses, forms)
        full3 = fit(family, responses, forms)
        entry["v2"] = {
            "report_noise": full2["report_noise"],
            "evidence": full2["evidence"],
            "parameters": {k: v["mean"] for k, v in full2["parameters"].items()},
        }
        entry["v3"] = {
            "report_noise": full3["report_noise"],
            "evidence": full3["evidence"],
            "parameters": {k: v["mean"] for k, v in full3["parameters"].items()},
            "intervals": {k: v["interval_90"] for k, v in full3["parameters"].items()},
        }
        for held in ("a", "b"):
            train = tuple(f for f in forms if f != held)
            items = screen._design(family, held)
            rows = np.asarray(items["kind"]) != "anchor"
            observed = screen.logit(responses[held][rows])
            f2 = v2.fit(family, responses, train)
            f3 = fit(family, responses, train)
            p2 = v2.predict_form(family, f2, held)
            p3 = predict_form(family, f3, held)
            entry["v2"][f"held_out_{held}"] = float(
                np.sqrt(np.mean((screen.logit(p2) - observed) ** 2))
            )
            entry["v3"][f"held_out_{held}"] = float(
                np.sqrt(np.mean((screen.logit(p3) - observed) ** 2))
            )
        out.setdefault(family, {})[config] = entry
    return out
