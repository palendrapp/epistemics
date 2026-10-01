"""Revised observers for the open-inference screen (docs/open-inference-screen-design.md, "Revised
observers").

Stage A showed that the family observers (dispositions.screen, model 0.17) describe F3 and partly
F4, but not F1, F2 or F5: answers fall back on a default when a case leaves the model open
(0.50 for a single example; a constant 0.85 or 1.00 for Luna; GPT-6's extrapolations compressed
into 0.55-0.80). The revision, analysis-side only (the collected tasks are unchanged):

1. Model trust, every family: on open items the reported probability is
   (1 - m) * p_observer + m * d, Bayesian model averaging over "the family's model applies" and an
   uninformative model whose answer is the fallback d. Anchors state their model and are not
   fitted. Low m commits to the family's model.
2. F2: a rounded report comes from a bin proportional to the number's size (width
   NUM_GRAIN x value), not a fixed unit.
3. F5: the assumed process noise is a parameter (log 0.01-0.3), so certain extrapolation (Luna)
   can be expressed.

Fits are grid posteriors with flat priors; the report noise (log-odds) is fitted and marginalised.
"""

import functools
import math

import numpy as np

from epistemics.dispositions import screen

# Mixture grids fine enough that true values between grid points do not bias the family
# parameters (with 6 x 6, F5's noise coverage fell to 0.70).
TRUST = np.round(np.linspace(0.0, 1.0, 11), 2)
FALLBACK = np.array([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 0.99])
REPORT_NOISE = np.array([0.1, 0.2, 0.3, 0.5, 0.8])

# The revised observers are canonical in dispositions.screen (model 0.18).
MODELS = screen.OBSERVERS
GRID = {
    **screen.FIT_GRID,
    "trend": {"linear_weight": np.linspace(0.2, 0.9, 15), "noise": np.geomspace(0.01, 0.3, 15)},
}
PARAMS = screen.OBSERVER_PARAMS
PROFILE = {
    **screen.PROFILE,
    "trend": ("linear_weight", "noise"),
}
MIXTURE = ("trust", "fallback")


def predict(family, items, params):
    """Observer probabilities for every item (anchors: their answers), before the mixture."""
    out = np.zeros(len(items["kind"]))
    for i in range(len(out)):
        if items["kind"][i] == "anchor":
            out[i] = items["answer"][i]
        else:
            out[i] = MODELS[family](screen.data(items, i), params)
    return out


def respond(family, items, params, rng, noise=0.3):
    """A simulated respondent of the revised observer: the mixture on open items, log-odds report
    noise, whole percentages."""
    p = predict(family, items, params)
    anchors = np.asarray(items["kind"]) == "anchor"
    mixed = (1 - params["trust"]) * p + params["trust"] * params["fallback"]
    z = screen.logit(np.where(anchors, p, mixed)) + rng.normal(0, noise, len(p))
    out = np.where(anchors, p, screen._sigmoid(z))
    return np.clip(np.round(out, 2), 0, 1)


@functools.cache
def _table(family, forms, revised=True):
    """Observer probabilities over the parameter grid for the open items of the given forms."""
    grid = GRID[family] if revised else screen.FIT_GRID[family]
    models = MODELS if revised else screen.MODELS
    names = list(grid)
    mesh = np.meshgrid(*[grid[n] for n in names], indexing="ij")
    points = {n: m.ravel() for n, m in zip(names, mesh, strict=True)}
    size = len(points[names[0]])
    columns = []
    for form in forms:
        items = screen._design(family, form)
        rows = [i for i in range(len(items["kind"])) if items["kind"][i] != "anchor"]
        table = np.empty((size, len(rows)))
        for g in range(size):
            params = {n: float(points[n][g]) for n in names}
            table[g] = [models[family](screen.data(items, i), params) for i in rows]
        columns.append(table)
    return points, np.concatenate(columns, axis=1)


def _observed(family, responses, forms):
    z = []
    for form in forms:
        items = screen._design(family, form)
        y = np.asarray(responses[form], dtype=float)
        z.append(screen.logit(y[np.asarray(items["kind"]) != "anchor"]))
    return np.concatenate(z)


def _loglik(z, probs):
    """log p(z | grid point, report noise) for probabilities probs (..., n)."""
    squares = ((screen.logit(probs) - z) ** 2).sum(axis=-1)
    n = len(z)
    noise = REPORT_NOISE.reshape((1,) * squares.ndim + (-1,))
    return (
        -squares[..., None] / (2 * noise**2) - n * np.log(noise) - n * 0.5 * math.log(2 * math.pi)
    )


def _interval(probs, values):
    cdf = np.cumsum(probs)
    lo, hi = np.searchsorted(cdf, [0.05, 0.95])
    lower, upper = screen._cell_edges(values)
    return [float(lower[min(lo, len(values) - 1)]), float(upper[min(hi, len(values) - 1)])]


def fit(family, responses, forms=screen.FORMS, revised=True):
    """Grid posterior of the (revised) observer. Returns parameter summaries, the report noise, the
    log evidence (flat priors over the grid) and the posterior predictive mean per open item."""
    points, table = _table(family, tuple(forms), revised)
    z = _observed(family, responses, forms)
    if revised:
        mixed = (1 - TRUST[None, :, None, None]) * table[:, None, None, :] + TRUST[
            None, :, None, None
        ] * FALLBACK[None, None, :, None]
        loglik = _loglik(z, mixed)  # (grid, trust, fallback, noise)
    else:
        loglik = _loglik(z, table)  # (grid, noise)
    top = loglik.max()
    post = np.exp(loglik - top)
    evidence = float(top + np.log(post.mean()))
    post /= post.sum()
    by_point = post.reshape(post.shape[0], -1).sum(axis=1)
    grid = GRID[family] if revised else screen.FIT_GRID[family]
    params = PARAMS[family] if revised else screen.SPEC[family]["params"]
    out = {"evidence": evidence, "parameters": {}}
    for name, values in grid.items():
        log = params[name][0] == "log"
        probs = np.array([by_point[points[name] == v].sum() for v in values])
        out["parameters"][name] = {
            "mean": float(np.exp(probs @ np.log(values))) if log else float(probs @ values),
            "interval_90": _interval(probs, values),
        }
    if revised:
        for name, values, axis in (("trust", TRUST, 1), ("fallback", FALLBACK, 2)):
            probs = post.sum(axis=tuple(a for a in range(post.ndim) if a != axis))
            out["parameters"][name] = {
                "mean": float(probs @ values),
                "interval_90": _interval(probs, values),
            }
        expected = (post.sum(axis=3)[..., None] * mixed).sum(axis=(0, 1, 2))
    else:
        expected = (post.sum(axis=1)[:, None] * table).sum(axis=0)
    noise = post.sum(axis=tuple(range(post.ndim - 1)))
    out["report_noise"] = float(noise @ REPORT_NOISE)
    out["predicted"] = [float(v) for v in expected]
    return out


def predict_form(family, fitted, form):
    """Posterior predictive for another form's open items, from a fit's posterior means (a plug-in
    prediction for held-out evaluation)."""
    items = screen._design(family, form)
    params = {k: v["mean"] for k, v in fitted["parameters"].items()}
    p = predict(family, items, params)
    rows = np.asarray(items["kind"]) != "anchor"
    return (1 - params["trust"]) * p[rows] + params["trust"] * params["fallback"]


def draw(family, rng, n):
    out = [{} for _ in range(n)]
    for name, spec in PARAMS[family].items():
        if spec[0] == "log":
            values = np.exp(rng.uniform(math.log(spec[1]), math.log(spec[2]), n))
        else:
            values = rng.uniform(spec[0], spec[1], n)
        for k in range(n):
            out[k][name] = float(values[k])
    trust = rng.uniform(0.0, 0.8, n)
    fallback = rng.uniform(0.1, 0.95, n)
    for k in range(n):
        out[k]["trust"], out[k]["fallback"] = float(trust[k]), float(fallback[k])
    return out


# Recovery of the revised profiles: as ledger.screen.profile_recovery, with the mixture.
def _recovery_family(args):
    family, configs, forms, seed = args
    rng = np.random.default_rng(seed)
    truths = draw(family, rng, configs)
    noises = rng.uniform(0.1, 0.5, configs)
    fits = []
    for truth, noise in zip(truths, noises, strict=True):
        responses = {f: respond(family, screen.design(family, f), truth, rng, noise) for f in forms}
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
            other_truth = np.array([t[other] for t in truths])
            confusion[other] = float(
                np.corrcoef(estimate, np.log(other_truth) if other_log else other_truth)[0, 1]
            )
        r = float(np.corrcoef(estimate, truth)[0, 1])
        off = max(abs(v) for k, v in confusion.items() if k != name)
        out[name] = {
            "r": r,
            "coverage_90": float(np.mean(inside)),
            "confusion": confusion,
            "largest_confusion": off,
            "passed": r >= 0.8 and float(np.mean(inside)) >= 0.8 and off <= 0.3,
        }
    return family, "+".join(forms), out


def recovery(configs=150, seed=20261106, families=screen.FIXED_FAMILIES):
    """Revised-observer recovery with forms a, b and c (the gate for collecting form c), and with
    a and b only for comparison."""
    from concurrent.futures import ProcessPoolExecutor

    seeds = np.random.SeedSequence(seed).spawn(2 * len(families))
    jobs = []
    for k, family in enumerate(families):
        jobs.append((family, configs, screen.forms(family), seeds[2 * k]))
        jobs.append((family, configs, screen.FORMS, seeds[2 * k + 1]))
    with ProcessPoolExecutor(8) as pool:
        results = list(pool.map(_recovery_family, jobs))
    out = {}
    for family, forms, params in results:
        out.setdefault(family, {})[forms] = params
    full = {f: "+".join(screen.forms(f)) for f in families}
    return {
        "schema_version": "epistemics.screen-revised-recovery.v2",
        "configs": configs,
        "families": out,
        "passed": all(p["passed"] for f, v in out.items() for p in v[full[f]].values()),
    }


def profiles(roots, fit_forms=("a",), predict_form_=None, families=screen.FAMILIES):
    """Fits of the original and revised observers to each configuration's sessions on the given
    forms: evidence, report noise, parameters; with predict_form_, the held-out prediction error
    (log-odds RMSE) of each model on that form's non-anchor items. The original observers are
    fitted only to forms a and b."""
    from epistemics.ledger import dispositions

    by = {}
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "screen" not in record:
                continue
            s = record["screen"]
            by.setdefault((s["family"], record["configuration"]), {})[s["form"]] = np.asarray(
                record["responses"], dtype=float
            )
    out = {}
    for (family, config), responses in sorted(by.items()):
        if family not in families or not all(f in responses for f in fit_forms):
            continue
        entry = {}
        for label, revised in (("original", False), ("revised", True)):
            if not revised and screen.FIXED_FORM in fit_forms:
                continue
            fitted = fit(family, responses, fit_forms, revised)
            result = {
                "evidence": fitted["evidence"],
                "report_noise": fitted["report_noise"],
                "parameters": {k: v["mean"] for k, v in fitted["parameters"].items()},
                "intervals": {k: v["interval_90"] for k, v in fitted["parameters"].items()},
            }
            if predict_form_ and predict_form_ in responses:
                items = screen._design(family, predict_form_)
                rows = np.asarray(items["kind"]) != "anchor"
                observed = screen.logit(responses[predict_form_][rows])
                if revised:
                    predicted = predict_form(family, fitted, predict_form_)
                else:
                    params = {k: v["mean"] for k, v in fitted["parameters"].items()}
                    predicted = screen.predict(family, items, params)[rows]
                result["held_out_rmse"] = float(
                    np.sqrt(np.mean((screen.logit(predicted) - observed) ** 2))
                )
            entry[label] = result
        out.setdefault(family, {})[config] = entry
    return out


def fallback_test(roots):
    """Preregistered (fallback round): per configuration and family, trust and fallback fitted to
    form c's fallback items alone (the observer's answer there is fixed, so only the mixture and
    the report noise are fitted), against the trust fitted to forms a and b under the revised
    observer. Constant fallback: the fixed-item trust's 90% interval lies above 0.1 where forms a
    and b show trust above 0.25. Triggered by open cases: fixed-item trust near 0 (interval
    reaching 0) while forms a and b show trust above 0.25."""
    from epistemics.ledger import dispositions

    by = {}
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "screen" not in record:
                continue
            s = record["screen"]
            if s["family"] in screen.FIXED_FAMILIES:
                by.setdefault((s["family"], record["configuration"]), {})[s["form"]] = np.asarray(
                    record["responses"], dtype=float
                )
    out = {}
    for (family, config), responses in sorted(by.items()):
        if not all(f in responses for f in screen.forms(family)):
            continue
        items = screen.design(family, screen.FIXED_FORM)
        fixed = np.asarray(items["kind"]) == "fixed"
        p = screen.predict(family, items, screen.observer_mid(family))[fixed]
        z = screen.logit(responses[screen.FIXED_FORM][fixed])
        mixed = (1 - TRUST[:, None, None]) * p[None, None, :] + TRUST[:, None, None] * FALLBACK[
            None, :, None
        ]
        loglik = _loglik(z, mixed)  # (trust, fallback, noise)
        post = np.exp(loglik - loglik.max())
        post /= post.sum()
        trust = post.sum(axis=(1, 2))
        fallback = post.sum(axis=(0, 2))
        ab = fit(family, responses, screen.FORMS)["parameters"]["trust"]
        fixed_trust = {"mean": float(trust @ TRUST), "interval_90": _interval(trust, TRUST)}
        verdict = "no fallback on open items"
        if ab["mean"] > 0.25:
            if fixed_trust["interval_90"][0] > 0.1:
                verdict = "constant"
            elif fixed_trust["interval_90"][0] <= 0.0 + 1e-9:
                verdict = "triggered by open cases"
            else:
                verdict = "undetermined"
        out.setdefault(family, {})[config] = {
            "fixed_items": {
                "trust": fixed_trust,
                "fallback": {"mean": float(fallback @ FALLBACK)},
                "report_noise": float(post.sum(axis=(0, 1)) @ REPORT_NOISE),
                "answers": [float(v) for v in responses[screen.FIXED_FORM][fixed]],
                "observer": [float(v) for v in p],
            },
            "forms_ab_trust": ab,
            "verdict": verdict,
        }
    return out
