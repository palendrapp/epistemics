"""Clef cognitive battery analysis (docs/clef-battery-design.md).

Per model and domain (urn, desk), from answers averaged over the three phrasings (log-odds for
probabilities, probabilities for choices):

  bookbag  Grether regression z = alpha*prior + beta*evidence + bias (log-odds); with confirmation
           asymmetry delta (extra evidence weight when the sample agrees with the prior's
           leaning); and evidence weight by sample size (1, 3, 5 draws), from the regression and
           from unanimous samples only (which need no regression: the prior cancels)
  beads    P(decide now) = sigmoid(kappa * (|posterior log-odds| - theta)) per ratio, against the
           optimal threshold for the payoffs; expected draws before deciding along each pattern;
           belief slope from the belief questions
  tone     the shift from the prior (log-odds, towards the reported side) per wording, with and
           without a stated record; tone index = confident minus hedged without a record

Transfer, per model: the urn parameters against the desk's, and how well the urn parameters
predict the desk answers, against an ideal Bayesian, the other model's urn parameters
(mismatched) and the desk's own fit (in-sample ceiling). Mitigation: the desk answers inverted
through the urn-fitted Grether map (recover the evidence weight, re-apply it at 1), with the
model's own and with the other model's parameters.

Answers are elicited outputs of a trained head, not direct access to beliefs.
"""

import numpy as np

from epistemics.clef import battery, pilot
from epistemics.clef.answers import parse
from epistemics.clef.client import ClefError

# Clef reports probabilities to four decimals; clip just inside them. Weights are fitted on items
# whose Bayesian answer lies within FIT_RANGE log-odds (a selection on the design, not on the
# answers, so it does not bias the slopes); beyond it answers saturate at the clip.
CLIP = 0.0005
FIT_RANGE = 4.0
BOOT = 1000
SEED = 20261006


def _z(p):
    p = np.clip(np.asarray(p, dtype=float), CLIP, 1 - CLIP)
    return np.log(p / (1 - p))


ZMAX = float(_z(1 - CLIP))


def load(root):
    document, _ = pilot.load(root)
    if document.get("design") != "battery":
        raise ClefError(f"{root} is not a battery root")
    if document["items"]["battery"] != battery.items_digest():
        raise ClefError("The battery items have changed since the plan was frozen")
    records = pilot.answered(root)
    values = {c["id"]: parse(records[c["id"]]["response"], c["questions"])
              for c in document["calls"] if c["id"] in records}  # fmt: skip
    return document, values


def _phrased(values, model, part, domain, n, field="answer", transform=_z):
    """Per item: the mean over phrasings of the transformed answer, and its SD (None if any
    phrasing is missing)."""
    means, sds = [], []
    for i in range(n):
        got = [values.get(f"{model}/{part}/{domain}/{i}/{ph}") for ph in battery.PHRASINGS]
        if any(g is None for g in got):
            return None, None
        x = np.array([transform(g[field]) for g in got], dtype=float)
        means.append(x.mean())
        sds.append(x.std())
    return np.array(means), np.array(sds)


def _lstsq(X, y):
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    r2 = 1 - ((y - pred) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-12)
    return coef, float(r2)


def _boot(X, y, rng):
    n = len(y)
    draws = [_lstsq(X[idx], y[idx])[0] for idx in (rng.integers(0, n, n) for _ in range(BOOT))]
    return np.percentile(draws, [5, 95], axis=0)


def _design_matrices(items):
    lp = np.array([it["prior_logodds"] for it in items])
    llr = np.array([it["llr"] for it in items])
    n = np.array([it["n"] for it in items])
    agree = np.sign(lp) * np.sign(llr)
    one = np.ones(len(items))
    basic = np.c_[lp, llr, one]
    asym = np.c_[lp, llr, llr * agree, one]
    by_n = np.c_[lp, *[llr * (n == k) for k in (1, 3, 5)], one]
    return lp, llr, basic, asym, by_n


def unanimous(items, z):
    """Sample-size compression from unanimous samples only: per prior and hit rate, half the
    difference between n draws all for A and all for B (the prior cancels), in units of one
    draw's Bayesian weight; averaged, then as ratios of n to 1 (Bayes: 3 and 5)."""
    index = {(it["prior"], it["accuracy"], it["n"], it["r"]): k for k, it in enumerate(items)}
    weight = {}
    for n in (1, 3, 5):
        weight[n] = float(np.mean([(z[index[(p, q, n, n)]] - z[index[(p, q, n, 0)]]) / 2 / battery.logit(q)
                                   for p in battery.PRIORS for q in battery.ACCURACIES]))  # fmt: skip
    return {"single_weight": weight[1], "ratio_3_to_1": weight[3] / weight[1],
            "ratio_5_to_1": weight[5] / weight[1]}  # fmt: skip


def bookbag(values, model, domain):
    items = battery.bookbag_items()
    z, sd = _phrased(values, model, "bookbag", domain, len(items))
    if z is None:
        return None
    lp, llr, basic, asym, by_n = _design_matrices(items)
    fit = np.abs(lp + llr) <= FIT_RANGE
    rng = np.random.default_rng(SEED)
    (a, b, c), r2 = _lstsq(basic[fit], z[fit])
    lo, hi = _boot(basic[fit], z[fit], rng)
    asym_coef, _ = _lstsq(asym[fit], z[fit])
    alo, ahi = _boot(asym[fit], z[fit], rng)
    n_coef, _ = _lstsq(by_n[fit], z[fit])
    bayes = lp + llr
    return {
        "unanimous": unanimous(items, z),
        "items_fitted": int(fit.sum()),
        "alpha": float(a), "alpha_90": [float(lo[0]), float(hi[0])],
        "beta": float(b), "beta_90": [float(lo[1]), float(hi[1])],
        "bias": float(c), "bias_90": [float(lo[2]), float(hi[2])],
        "r2": r2,
        "confirmation_delta": float(asym_coef[2]), "confirmation_delta_90": [float(alo[2]), float(ahi[2])],
        "with_asymmetry": {k: float(v) for k, v in zip(("alpha", "beta", "delta", "bias"), asym_coef, strict=True)},
        "beta_by_draws": {str(k): float(v) for k, v in zip((1, 3, 5), n_coef[1:4], strict=True)},
        "error_vs_bayes": float(np.mean(np.abs(z[fit] - bayes[fit]))),
        "phrasing_sd": float(sd.mean()),
        "_z": z,
    }  # fmt: skip


def _fit_threshold(abs_l, p_dec):
    """Least-squares theta, kappa for P(decide) = sigmoid(kappa * (|L| - theta))."""
    best = (None, None, np.inf)
    for theta in np.arange(0, 8.0001, 0.05):
        for kappa in (0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8, 12):
            pred = 1 / (1 + np.exp(-kappa * (abs_l - theta)))
            err = float(np.mean((p_dec - pred) ** 2))
            if err < best[2]:
                best = (float(theta), float(kappa), err)
    return best


def _decide(choice):
    return choice["a"] + choice["b"]


def beads(values, model, domain):
    items = battery.beads_items()
    p_dec, sd = _phrased(values, model, "beads", domain, len(items), "decision", _decide)
    if p_dec is None:
        return None
    sides = []
    for i, it in enumerate(items):
        got = [values[f"{model}/beads/{domain}/{i}/{ph}"]["decision"] for ph in battery.PHRASINGS]
        favoured = "a" if it["posterior_logodds"] > 0 else "b"
        if it["posterior_logodds"] != 0:
            sides.append(np.mean([g[favoured] / max(_decide(g), 1e-9) for g in got]))
    out = {"phrasing_sd": float(sd.mean()), "decide_on_favoured_side": float(np.mean(sides)),
           "ratios": {}, "_p_dec": p_dec}  # fmt: skip
    for q in battery.RATIOS:
        idx = [i for i, it in enumerate(items) if it["ratio"] == q]
        abs_l = np.abs([items[i]["posterior_logodds"] for i in idx])
        theta, kappa, err = _fit_threshold(abs_l, p_dec[idx])
        optimal = battery.optimal_threshold(q)
        by_seq = {items[i]["sequence"]: p_dec[i] for i in idx}
        draws, optimal_draws = [], []
        policy = battery.optimal_policy(q)
        for pattern in battery.PATTERNS:
            for s in (pattern, pattern.translate(str.maketrans("+-", "-+"))):
                cont, expected = 1.0, 0.0
                for t in range(len(s)):
                    cont *= 1 - by_seq[s[:t]]
                    expected += cont
                draws.append(expected)
                k_net = [s[:t].count("+") - s[:t].count("-") for t in range(len(s) + 1)]
                stop = next((t for t in range(len(s) + 1) if policy[(t, k_net[t])][0]), len(s))
                optimal_draws.append(stop)
        out["ratios"][str(q)] = {
            "theta": theta, "theta_draws": theta / battery.logit(q), "kappa": kappa,
            "fit_mse": err, "optimal_theta": optimal,
            "optimal_draws": optimal / battery.logit(q),
            "decide_before_any_draw": float(by_seq[""]),
            "expected_draws": float(np.mean(draws)),
            "optimal_expected_draws": float(np.mean(optimal_draws)),
        }  # fmt: skip
    beliefs = [values.get(f"{model}/belief/{domain}/{i}/0") for i in range(len(items))]
    if all(b is not None for b in beliefs):
        lstar = np.array([it["posterior_logodds"] for it in items])
        zb = _z([b["answer"] for b in beliefs])
        fit = np.abs(lstar) <= FIT_RANGE
        out["belief_slope"] = float(np.polyfit(lstar[fit], zb[fit], 1)[0])
    return out


def tone(values, model, domain):
    items = battery.tone_items()
    z, sd = _phrased(values, model, "tone", domain, len(items))
    if z is None:
        return None
    shift = np.array(
        [it["direction"] * (zi - it["prior_logodds"]) for it, zi in zip(items, z, strict=True)]
    )
    table = {}
    for rec in battery.RECORDS:
        key = "no_record" if rec is None else f"record_{round(rec * 100)}"
        table[key] = {w: float(np.mean([s for it, s in zip(items, shift, strict=True)
                                         if it["wording"] == w and it["record"] == rec]))
                      for w in battery.WORDINGS}  # fmt: skip
    record_llr = battery.logit(battery.RECORDS[1])
    return {
        "shift": table,
        "tone_index": table["no_record"]["confident"] - table["no_record"]["hedged"],
        "tone_index_with_record": table["record_70"]["confident"] - table["record_70"]["hedged"],
        "record_weight": {w: v / record_llr for w, v in table["record_70"].items()},
        "phrasing_sd": float(sd.mean()),
        "_z": z,
    }


def _rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def _transfer(models, results):
    """Per model: urn against desk, and prediction of the desk from urn parameters."""
    items_b = battery.bookbag_items()
    lp, llr, basic, *_ = _design_matrices(items_b)
    fit = np.abs(lp + llr) <= FIT_RANGE
    lp, llr = lp[fit], llr[fit]
    bayes = lp + llr
    tone_items = battery.tone_items()
    out = {}
    for m in models:
        other = [o for o in models if o != m]
        r = results[m]
        t = {}
        urn, desk = r["bookbag"]["urn"], r["bookbag"]["desk"]
        if urn and desk:

            def pred(p, lp=lp, llr=llr):
                return p["alpha"] * lp + p["beta"] * llr + p["bias"]

            z = desk["_z"][fit]
            t["bookbag"] = {
                "parameters": {k: {"urn": urn[k], "desk": desk[k]}
                               for k in ("alpha", "beta", "bias", "confirmation_delta")},
                "desk_rmse": {
                    "from_urn": _rmse(z, pred(urn)),
                    "bayes": _rmse(z, lp + llr),
                    "desk_fit_in_sample": _rmse(z, pred(desk)),
                    **{f"from_{o}_urn": _rmse(z, pred(results[o]["bookbag"]["urn"]))
                       for o in other if results[o]["bookbag"]["urn"]},
                },
            }  # fmt: skip

            def invert(p, z=z, lp=lp):
                return lp + (z - p["alpha"] * lp - p["bias"]) / p["beta"]

            t["inversion"] = {
                "desk_error_vs_bayes": {
                    "raw": float(np.mean(np.abs(z - bayes))),
                    "inverted_own_urn": float(np.mean(np.abs(invert(urn) - bayes))),
                    **{f"inverted_{o}_urn": float(np.mean(np.abs(invert(results[o]["bookbag"]["urn"]) - bayes)))
                       for o in other if results[o]["bookbag"]["urn"]},
                },
            }  # fmt: skip
        bu, bd = r["beads"]["urn"], r["beads"]["desk"]
        if bu and bd:
            items = battery.beads_items()
            per = {}
            for q in battery.RATIOS:
                key = str(q)
                idx = [i for i, it in enumerate(items) if it["ratio"] == q]
                abs_l = np.abs([items[i]["posterior_logodds"] for i in idx])

                def curve(p, abs_l=abs_l):
                    return 1 / (1 + np.exp(-p["kappa"] * (abs_l - p["theta"])))

                actual = bd["_p_dec"][idx]
                optimal = (abs_l >= bu["ratios"][key]["optimal_theta"] - 1e-9).astype(float)
                per[key] = {
                    "theta": {"urn": bu["ratios"][key]["theta"], "desk": bd["ratios"][key]["theta"],
                              "optimal": bu["ratios"][key]["optimal_theta"]},
                    "desk_error": {
                        "from_urn": float(np.mean(np.abs(actual - curve(bu["ratios"][key])))),
                        "optimal_policy": float(np.mean(np.abs(actual - optimal))),
                        "desk_fit_in_sample": float(np.mean(np.abs(actual - curve(bd["ratios"][key])))),
                        **{f"from_{o}_urn": float(np.mean(np.abs(actual - curve(results[o]["beads"]["urn"]["ratios"][key]))))
                           for o in other if results[o]["beads"]["urn"]},
                    },
                }  # fmt: skip
            t["beads"] = per
        tu, td = r["tone"]["urn"], r["tone"]["desk"]
        if tu and td:

            def tone_pred(shifts, items=tone_items):
                return np.array([it["prior_logodds"] + it["direction"] * shifts[
                    "no_record" if it["record"] is None else "record_70"][it["wording"]] for it in items])  # fmt: skip

            blind = {
                k: {w: float(np.mean(list(v.values()))) for w in v} for k, v in tu["shift"].items()
            }
            t["tone"] = {
                "tone_index": {"urn": tu["tone_index"], "desk": td["tone_index"]},
                "desk_rmse": {
                    "from_urn": _rmse(td["_z"], tone_pred(tu["shift"])),
                    "wording_blind_urn": _rmse(td["_z"], tone_pred(blind)),
                    "desk_fit_in_sample": _rmse(td["_z"], tone_pred(td["shift"])),
                    **{f"from_{o}_urn": _rmse(td["_z"], tone_pred(results[o]["tone"]["urn"]["shift"]))
                       for o in other if results[o]["tone"]["urn"]},
                },
            }  # fmt: skip
        out[m] = t
    return out


def _public(x):
    if isinstance(x, dict):
        return {k: _public(v) for k, v in x.items() if not k.startswith("_")}
    return x


def summary(root):
    document, values = load(root)
    models = list(document["models"])
    results = {
        m: {task: {d: f(values, m, d) for d in battery.DOMAINS}
            for task, f in (("bookbag", bookbag), ("beads", beads), ("tone", tone))}
        for m in models
    }  # fmt: skip
    planned = {m: sum(c["model"] == m for c in document["calls"]) for m in models}
    answered = {
        m: sum(c["model"] == m and c["id"] in values for c in document["calls"]) for m in models
    }
    return {
        "schema_version": "epistemics.clef-battery.v1",
        "version": document["version"],
        "plan_digest": document["plan_digest"],
        "calls": {m: {"planned": planned[m], "answered": answered[m]} for m in models},
        "models": _public(results),
        "transfer": _transfer(models, results),
        "optimal_theta": {str(q): battery.optimal_threshold(q) for q in battery.RATIOS},
        "scope": (
            "Answers averaged over three phrasings (log-odds for probabilities, probabilities "
            "for choices), clipped at 0.5% and 99.5%. Grether weights by least squares with 90% "
            "bootstrap intervals over items. Desk predictions use the urn parameters; 'in "
            "sample' rows are fits to the desk itself (a ceiling, not a test). Elicited outputs "
            "of a trained head, not direct access to beliefs."
        ),
    }
