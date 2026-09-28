"""Model views for the dashboard: grid posteriors, posterior predictive checks and recovery.

The verified reports keep each fit's posterior means and 90% intervals only. This module
recomputes the full grid posteriors from each session's responses and its own item design (as
collected), using the current model code. It mirrors `fit.fit_reports`, `fit.fit_checks` and
`fit.fit_cues` and records, per session, the largest difference between the recomputed posterior
means and the report's own. They agree unless the model changed after collection.

Posterior predictive distributions mix the whole-percentage (or whole-point) report likelihood
over the joint grid posterior. The recovery sample fits synthetic respondents drawn from the
validation study's generating priors; it is cached by the model fingerprint.
"""

import json
from pathlib import Path

import numpy as np

from epistemics.dispositions import design, fit, observers, validation
from epistemics.dispositions.response import (
    interval_mass,
    logsumexp,
    report_edges,
    wtp_edges,
    wtp_log_likelihood,
)

PERCENT = np.arange(101) / 100
POINTS = np.arange(0, 201, dtype=float)
QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)
KEEP = 1e-9  # Joint grid cells below this posterior weight are dropped from predictive mixtures.
REPORT_MODULES = {"corroboration": "dependence", "disclosure": "disclosure"}
CUE_MODELS = {
    "corroboration-cues": "dependence",
    "corroboration-dossier": "dependence",
    "disclosure-cues": "disclosure",
    "disclosure-dossier": "disclosure",
    "corroboration-unprompted": "dependence",
    "disclosure-unprompted": "disclosure",
    "corroboration-asked": "dependence",
    "disclosure-asked": "disclosure",
    "corroboration-probed": "dependence",
}
CUE_NAMES = {round(v, 12): k for k, v in design.CUES.items()}
REPORT_RECOVERY = {"disposition": fit.DISPOSITION, "gamma": fit.GAMMA, "report_sd": fit.REPORT_SD}
CHECK_RECOVERY = {
    "certainty_value": fit.CERTAINTY_VALUE,
    "decision_weight": fit.DECISION_WEIGHT,
    "wtp_sd": fit.WTP_SD,
}
RECOVERY_SEED = 20260928
RECOVERY_RESPONDENTS = 100


def arrays(raw):
    return {k: np.asarray(v, dtype=object if k == "kind" else float) for k, v in raw.items()} | {
        k: np.asarray(v).astype(int)
        for k, v in raw.items()
        if k in ("shared_good", "shared_bad", "withheld", "slot")
    }


def normalise(log_likelihood):
    return np.exp(log_likelihood - logsumexp(log_likelihood))


def marginals(posterior, names):
    return {
        name: posterior.sum(axis=tuple(j for j in range(posterior.ndim) if j != axis))
        for axis, name in enumerate(names)
    }


def quantiles(pmf, support):
    cdf = np.cumsum(pmf) / pmf.sum()
    index = np.minimum(np.searchsorted(cdf, QUANTILES), len(support) - 1)
    return support[index]


def mixture(weights, means, sds, lower, upper):
    """Predictive pmf over report bins for a weighted set of latent means and noise SDs."""
    keep = weights > KEEP
    w, m, s = weights[keep], means[keep], sds[keep]
    mass = interval_mass(lower[None, :], upper[None, :], m[:, None], s[:, None])
    pmf = w @ mass
    return pmf / pmf.sum()


def predictive(pmfs, observed, support):
    q = np.array([quantiles(p, support) for p in pmfs])
    observed = np.asarray(observed, dtype=float)
    inside = (observed >= q[:, 0] - 1e-9) & (observed <= q[:, -1] + 1e-9)
    return {
        "observed": observed.tolist(),
        "quantiles": q.tolist(),
        "inside_90": int(inside.sum()),
        "items": len(observed),
    }


def report_session(module, items, reports):
    """Base relay or disclosure session: posterior over (prior, gamma, bias, noise)."""
    model = REPORT_MODULES[module]
    grid = fit._report_grid(model, items, reports, fit.DISPOSITION[:, None, None])
    posterior = normalise(grid)
    names = ("disposition", "gamma", "bias", "report_sd")
    latent = fit.REPORT_MODELS[model](
        items, fit.DISPOSITION[:, None, None], fit.GAMMA[None, :, None]
    )
    forecast = (items["kind"] != "probe").astype(float)
    lower, upper = report_edges(PERCENT)
    shape = posterior.shape
    pmfs = []
    for i in range(len(reports)):
        means = latent[:, :, None, None, i] + fit.BIAS[None, None, :, None] * forecast[i]
        means = np.broadcast_to(means, shape)
        sds = np.broadcast_to(fit.REPORT_SD, shape)
        pmfs.append(mixture(posterior.ravel(), means.ravel(), sds.ravel(), lower, upper))
    return marginals(posterior, names), predictive(pmfs, reports, PERCENT)


def check_session(items, wtp):
    """Checks session under the linear certainty function: (value, decision weight, noise)."""
    decision, gain = observers.check_values(items, "linear")
    means = (
        fit.CERTAINTY_VALUE[:, None, None] * gain + fit.DECISION_WEIGHT[None, :, None] * decision
    )
    grid = np.stack([wtp_log_likelihood(means, wtp, sd) for sd in fit.WTP_SD], axis=-1)
    posterior = normalise(grid)
    names = ("certainty_value", "decision_weight", "wtp_sd")
    lower, upper = wtp_edges(POINTS)
    upper = upper.copy()
    upper[-1] = np.inf
    shape = posterior.shape
    pmfs = []
    for i in range(len(wtp)):
        m = np.broadcast_to(means[:, :, None, i], shape)
        s = np.broadcast_to(fit.WTP_SD, shape)
        pmfs.append(mixture(posterior.ravel(), m.ravel(), s.ravel(), lower, upper))
    return marginals(posterior, names), predictive(pmfs, wtp, POINTS)


def cue_session(module, items, reports):
    """Description session: a prior per description level with shared (gamma, bias, noise)."""
    model = CUE_MODELS[module]
    slots, kinds = items["slot"], items["kind"]
    evidence = kinds != "rate"

    def part(mask):
        return {k: v[mask] for k, v in items.items()}, reports[mask]

    anchor = fit._report_grid(model, *part(evidence & (slots < 0)), 0.5)[0]
    levels = sorted(set(slots[slots >= 0].tolist()))
    per_slot = np.stack(
        [
            fit._report_grid(model, *part(evidence & (slots == s)), fit.DISPOSITION[:, None, None])
            for s in levels
        ]
    )
    slot_evidence = logsumexp(per_slot, axis=1)
    shared = anchor + (slot_evidence - np.log(len(fit.DISPOSITION))).sum(axis=0)
    posterior = normalise(shared)
    conditional = np.exp(per_slot - slot_evidence[:, None])
    joint = conditional * posterior[None, None]
    slot_marginals = joint.sum(axis=(2, 3, 4))
    result = {"slots": slot_marginals} | marginals(posterior, ("gamma", "bias", "report_sd"))

    observer = fit.REPORT_MODELS[model]
    latent = observer(items, fit.DISPOSITION[:, None, None], fit.GAMMA[None, :, None])
    forecast = (~np.isin(kinds, ("probe", "rate"))).astype(float)
    lower, upper = report_edges(PERCENT)
    shape = joint.shape[1:]
    middle = int(np.argmin(np.abs(fit.DISPOSITION - 0.5)))
    stated_logit = np.log(np.clip(fit.DISPOSITION, 1e-6, 1 - 1e-6)) - np.log1p(
        -np.clip(fit.DISPOSITION, 1e-6, 1 - 1e-6)
    )
    pmfs = []
    for i in range(len(reports)):
        s = slots[i]
        if s < 0:
            weights = np.zeros(shape)
            weights[middle] = posterior
        else:
            weights = joint[levels.index(s)]
        if kinds[i] == "rate":
            means = np.broadcast_to(stated_logit[:, None, None, None], shape)
        else:
            means = latent[:, :, None, None, i] + fit.BIAS[None, None, :, None] * forecast[i]
            means = np.broadcast_to(means, shape)
        sds = np.broadcast_to(fit.REPORT_SD, shape)
        pmfs.append(mixture(weights.ravel(), means.ravel(), sds.ravel(), lower, upper))
    return result, predictive(pmfs, reports, PERCENT)


def mean_on(weights, grid):
    return float(np.asarray(weights) @ grid)


def rounded(values, digits=5):
    return np.round(np.asarray(values, dtype=float), digits).tolist()


def item_label(module, items, i):
    """A short description of one case, for tooltips and row labels."""
    kind = str(items["kind"][i]) if "kind" in items else "check"
    if "accuracy_a" in items:
        if kind == "rate":
            return "stated base rate"
        prior = f"prior {items['prior'][i]:.0%}"
        calls = {1: "high", -1: "low"}
        a = f"A {items['accuracy_a'][i]:.0%} says {calls[int(items['report_a'][i])]}"
        if kind == "single":
            return f"one outlet · {prior} · {a}"
        b = f"B {items['accuracy_b'][i]:.0%} says {calls[int(items['report_b'][i])]}"
        cue = CUE_NAMES.get(round(float(items["cue"][i]), 12), "none").replace("_", " ")
        wording = "no wording cue" if cue == "none" else f"{cue} wording"
        head = "probe" if kind == "probe" else "two outlets"
        return f"{head} · {prior} · {a}, {b} · {wording}"
    if "good" in items:
        if kind == "rate":
            return "stated base rate"
        m, j, k = (int(items[f][i]) for f in ("shared_good", "shared_bad", "withheld"))
        head = "probe" if kind == "probe" else f"prior {items['prior'][i]:.0%}"
        return (
            f"{head} · {m} on target, {j} below, {k} withheld · "
            f"random omission {items['omission'][i]:.0%}"
        )
    return (
        f"prior {items['prior'][i]:.0%} → {items['high'][i]:.0%} or {items['low'][i]:.0%} · "
        f"gain {items['gain'][i]:.0f}, loss {items['loss'][i]:.0f}"
    )


def item_group(module, items, i):
    kind = str(items["kind"][i]) if "kind" in items else "check"
    if kind in ("probe", "rate", "single"):
        return kind
    if "accuracy_a" in items:
        return "agree" if items["report_a"][i] == items["report_b"][i] else "conflict"
    if "good" in items:
        if items["shared_bad"][i] > 0 or items["withheld"][i] == 0:
            return "control"
        return "withheld"
    return "check"


class Designs:
    """Distinct item designs, referenced by id from each session."""

    def __init__(self):
        self.table, self.ids = [], {}

    def add(self, module, raw):
        key = json.dumps([module, raw], sort_keys=True)
        if key not in self.ids:
            items = arrays(raw)
            self.ids[key] = f"d{len(self.table)}"
            family = (
                "relay" if "accuracy_a" in items else "disclosure" if "good" in items else "checks"
            )
            entry = {
                "id": self.ids[key],
                "family": family,
                "items": raw,
                "labels": [item_label(module, items, i) for i in range(len(items["prior"]))],
                "groups": [item_group(module, items, i) for i in range(len(items["prior"]))],
            }
            if family in ("relay", "disclosure") and "slot" not in items:
                observer = observers.corroboration if family == "relay" else observers.disclosure
                # Reference values for the page's own port of the observers.
                entry["reference"] = [
                    {
                        "disposition": d,
                        "gamma": g,
                        "latent": rounded(observer(items, d, g), 12),
                    }
                    for d, g in ((0.3, 0.8), (0.9, 1.2), (0.0, 1.0))
                ]
            self.table.append(entry)
        return self.ids[key]


def session(record, experiment, designs):
    """One verified session's posteriors, predictive check and agreement with its report."""
    module = record["module"]
    items = arrays(record["items"])
    responses = np.asarray(record["responses"], dtype=float)
    base = {
        "id": f"{record['root']}/{record['run_id']}",
        "run_id": record["run_id"],
        "root": record["root"],
        "experiment": experiment,
        "configuration": record["configuration"],
        "module": module,
        "variant": record["variant"],
        "order_policy": record.get("order_policy", "random"),
        "repeat": record.get("repeat"),
        "design": designs.add(module, record["items"]),
    }
    differences = []
    if module in REPORT_MODULES:
        posterior, ppc = report_session(module, items, responses)
        grids = {
            "disposition": fit.DISPOSITION,
            "gamma": fit.GAMMA,
            "bias": fit.BIAS,
            "report_sd": fit.REPORT_SD,
        }
        recorded = {k: record["fit"][k]["mean"] for k in grids}
    elif module == "checks":
        posterior, ppc = check_session(items, responses)
        grids = {
            "certainty_value": fit.CERTAINTY_VALUE,
            "decision_weight": fit.DECISION_WEIGHT,
            "wtp_sd": fit.WTP_SD,
        }
        recorded = {k: record["fits"]["linear"][k]["mean"] for k in grids}
    elif module in CUE_MODELS:
        posterior, ppc = cue_session(module, items, responses)
        grids = {"gamma": fit.GAMMA, "bias": fit.BIAS, "report_sd": fit.REPORT_SD}
        recorded = {k: record["shared"][k]["mean"] for k in grids}
        slot_means = [mean_on(w, fit.DISPOSITION) for w in posterior["slots"]]
        slot_recorded = [s["implied"]["mean"] for s in record["slot_fits"]]
        base["slots"] = [rounded(w) for w in posterior["slots"]]
        base["stated"] = [s["stated"] for s in record["slot_fits"]]
        base["slot_means"] = rounded(slot_means, 4)
        differences = [abs(a - b) for a, b in zip(slot_means, slot_recorded, strict=True)]
    else:
        return None
    means = {k: mean_on(posterior[k], grid) for k, grid in grids.items()}
    differences += [
        abs(means[k] - recorded[k]) / (grid.max() - grid.min()) for k, grid in grids.items()
    ]
    return base | {
        "posterior": {k: rounded(posterior[k]) for k in grids},
        "means": {k: round(v, 4) for k, v in means.items()},
        "recorded_difference": float(max(differences)),
        "ppc": ppc,
    }


def cell_interval(grid, interval):
    """A grid interval widened to the edges of its end cells, as in the validation study."""
    lower, upper = validation.cell_edges(grid)
    lo, hi = (int(np.argmin(np.abs(grid - x))) for x in interval)
    return [round(float(lower[lo]), 4), round(float(upper[hi]), 4)]


def recovery_row(truth, fitted, grids):
    return {
        name: [round(truth[name], 4), round(fitted[name]["mean"], 4)]
        + cell_interval(grid, fitted[name]["interval_90"])
        for name, grid in grids.items()
    }


def recovery_sample(cache_dir="output", seed=RECOVERY_SEED, respondents=RECOVERY_RESPONDENTS):
    """Synthetic respondents from the validation priors, fitted by the real fits (cached)."""
    key = f"{validation.fingerprint()[:16]}-{seed}-{respondents}"
    cache = Path(cache_dir) / f"ledger-recovery-v2-{key}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    rng = np.random.default_rng(seed)
    result = {"seed": seed, "respondents": respondents, "model_fingerprint": key.split("-")[0]}
    for family, (model, build) in {
        "relay": ("dependence", design.corroboration),
        "disclosure": ("disclosure", design.disclosure),
    }.items():
        items = build(probes=True)
        rows = []
        for _ in range(respondents):
            truth = validation.draw(rng, validation.REPORT_PRIOR)
            reports = validation.simulate_reports(model, items, truth, rng)
            fitted = fit.fit_reports(model, items, reports)["parameters"]
            rows.append(recovery_row(truth, fitted, REPORT_RECOVERY))
        result[family] = rows
    items = design.checks()
    prior = {
        **validation.CHECK_PRIOR,
        "certainty_value": validation.CHECK_PRIOR["certainty_value"]["linear"],
    }
    rows = []
    for _ in range(respondents):
        truth = validation.draw(rng, prior)
        wtp = validation.simulate_checks("linear", items, truth, rng)
        fitted = fit.fit_checks("linear", items, wtp)["parameters"]
        rows.append(recovery_row(truth, fitted, CHECK_RECOVERY))
    result["checks"] = rows
    result["scope"] = (
        "Synthetic respondents drawn uniformly from the validation study's generating ranges and "
        "fitted with the recorded grids; relay and disclosure use the probe designs; checks use "
        "the linear certainty function. Each row is [truth, posterior mean, 90% interval widened "
        "to the edges of its end grid cells, as in the validation study]."
    )
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result))
    return result


def descriptors():
    """Description sentences per module and set, with the subject replaced by a generic noun."""
    from epistemics.disposition_tasks.render import CUE_DESCRIPTORS

    nouns = {
        "corroboration": ("The outlet", "The outlet's"),
        "disclosure": ("The company", "The company's"),
    }
    result = {}
    for (base, variant), sentences in CUE_DESCRIPTORS.items():
        name, own = nouns[base]
        family = "relay" if base == "corroboration" else "disclosure"
        result.setdefault(family, {})[variant] = [s.format(name=name, own=own) for s in sentences]
    return result


def build(sessions_by_root, experiment_for, cache_dir="output"):
    """The dashboard's model block from verified extraction records, keyed by root."""
    designs = Designs()
    sessions = []
    for root, records in sessions_by_root.items():
        for record in records:
            if not record.get("verified") or "items" not in record:
                continue
            row = session({**record, "root": Path(root).name}, experiment_for.get(root), designs)
            if row is not None:
                sessions.append(row)
    return {
        "schema_version": "epistemics.ledger-models.v1",
        "grids": {
            "disposition": fit.DISPOSITION.tolist(),
            "gamma": fit.GAMMA.tolist(),
            "bias": fit.BIAS.tolist(),
            "report_sd": fit.REPORT_SD.tolist(),
            "certainty_value": fit.CERTAINTY_VALUE.tolist(),
            "decision_weight": fit.DECISION_WEIGHT.tolist(),
            "wtp_sd": fit.WTP_SD.tolist(),
        },
        "levels": list(design.CUE_LEVELS),
        "descriptors": descriptors(),
        "designs": designs.table,
        "sessions": sessions,
        "recovery": recovery_sample(cache_dir),
        "scope": (
            "Grid posteriors recomputed with the current model from each session's responses and "
            "its collected design; recorded_difference is the largest gap to the verified "
            "report's posterior means (as a share of each grid's range). Predictive intervals mix "
            "the report likelihood over the joint grid posterior."
        ),
    }
