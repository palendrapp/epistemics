"""Coherence-set analyses (docs/screen-coherence-design.md).

Per configuration and family: the Bayesian sampler's shrinkage d (incoherent bias) and report noise
tau (variance), fitted from the open sets and from the computable sets (dispositions.cohere.fit),
and the model-free residual of each law.

Stage A (form d), preregistered:
  H1 systematic incoherence: some configurations' open-set d has its 90% interval above 0;
  H2 open against computable: open-set d exceeds computable-set d for most configurations;
  H4 directional: Luna and Terra have a larger open-set d than every GPT-6 configuration, in each
     family.
Stage B (forms d and e): H3, the consistency ICC of open-set d across forms (each form centred,
labels permuted within forms) at least 0.5 with p_holm < 0.05 across the families, retest r > 0.
"""

import numpy as np

from epistemics.dispositions import cohere, screen
from epistemics.ledger import screen as screen_ledger

GPT56 = ("luna", "terra")


def sessions(roots):
    from epistemics.ledger import dispositions

    out = []
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "cohere" not in record:
                continue
            c = record["cohere"]
            out.append(
                {
                    "configuration": record["configuration"],
                    "family": c["family"],
                    "form": c["form"],
                    "open": c["open"],
                    "computable": c["computable"],
                    "all": c["all"],
                    "sets": c["sets"],
                    "anchors_ok": c["anchors_ok"],
                    "anchor_errors": c["anchor_errors"],
                }
            )
    return out


def _residuals(rows):
    """Mean model-free residual by law (and partition size)."""
    out = {}
    for r in rows:
        for s in r["sets"]:
            if s["computable"]:
                key = f"computable {s['law']} ({s['members']})"
            else:
                key = f"{s['law']} ({s['members']})" if s["law"] == "partition" else s["law"]
            out.setdefault(key, []).append(s["residual"])
    return {k: float(np.mean(v)) for k, v in sorted(out.items())}


def stage_a(roots, form="d"):
    rows = [r for r in sessions(roots) if r["form"] == form]
    result = {"schema_version": "epistemics.cohere-stage-a.v1", "families": {}}
    for family in cohere.FAMILIES:
        chosen = [r for r in rows if r["family"] == family]
        if not chosen:
            continue
        configs = {}
        for r in chosen:
            configs[r["configuration"]] = {
                "d_open": r["open"]["d"],
                "d_computable": r["computable"]["d"],
                "tau_open": r["open"]["tau"]["mean"],
                "residuals": _residuals([r]),
                "anchors_ok": r["anchors_ok"],
            }
        h1 = [c for c, v in configs.items() if v["d_open"]["interval_90"][0] > 0]
        h2 = [c for c, v in configs.items() if v["d_open"]["mean"] > v["d_computable"]["mean"]]
        gpt6 = [v["d_open"]["mean"] for c, v in configs.items() if c not in GPT56]
        h4 = {
            c: bool(gpt6) and configs[c]["d_open"]["mean"] > max(gpt6)
            for c in GPT56
            if c in configs
        }
        result["families"][family] = {
            "configurations": configs,
            "residuals": _residuals(chosen),
            "H1_incoherent": h1,
            "H2_open_above_computable": {
                "count": len(h2),
                "of": len(configs),
                "holds": len(h2) > len(configs) / 2,
            },
            "H4_gpt56_above_gpt6": {"by_configuration": h4, "holds": bool(h4) and all(h4.values())},
            "anchor_failures": [c for c, v in configs.items() if not v["anchors_ok"]],
        }
    return result


def stage_b(roots, seed=20261112):
    rows = sessions(roots)
    rng = np.random.default_rng(seed)
    out, ps = {}, {}
    for family in cohere.FAMILIES:
        by = {}
        for r in rows:
            if r["family"] == family:
                by.setdefault(r["configuration"], {})[r["form"]] = r["open"]["d"]["mean"]
        paired = sorted(c for c, v in by.items() if "d" in v and "e" in v)
        if len(paired) < 3:
            continue
        matrix = [[by[c]["d"], by[c]["e"]] for c in paired]
        value, p = screen_ledger.icc_test(matrix, rng)
        a, b = np.array(matrix).T
        retest = float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else 0.0
        out[family] = {
            "configurations": paired,
            "d_open": dict(zip(paired, matrix, strict=True)),
            "icc": value,
            "p": p,
            "retest_r": retest,
        }
        ps[family] = p
    for family, p_holm in screen_ledger.holm(ps).items():
        e = out[family]
        e["p_holm"] = p_holm
        e["passed"] = e["icc"] >= 0.5 and p_holm < 0.05 and e["retest_r"] > 0
    return {
        "schema_version": "epistemics.cohere-stage-b.v1",
        "families": out,
        "passed": [f for f, v in out.items() if v.get("passed")],
    }


# Validation before collection.
def _simulate(family, form, truth, rng):
    items = cohere.design(family, form)
    return items, cohere.respond(family, items, truth, rng)


def _recovery_family(args):
    family, configs, seed = args
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(configs):
        params = screen.observer_draw(family, rng, 1)[0]
        truth = {
            "params": params,
            "d": float(rng.uniform(0, 0.25)),
            "tau": float(rng.uniform(0.05, 0.5)),
        }
        items, responses = _simulate(family, "d", truth, rng)
        fitted = cohere.fit(items, responses, ("open",))
        rows.append((truth, fitted))
    d_true = np.array([t["d"] for t, _ in rows])
    d_est = np.array([f["d"]["mean"] for _, f in rows])
    tau_true = np.array([t["tau"] for t, _ in rows])
    tau_est = np.array([f["tau"]["mean"] for _, f in rows])
    inside = np.mean(
        [
            f["d"]["interval_90"][0] - 1e-9 <= t["d"] <= f["d"]["interval_90"][1] + 1e-9
            for t, f in rows
        ]
    )
    # Calibration: coherent respondents (d = 0) at report noise up to 0.5.
    false = 0
    for _ in range(configs):
        params = screen.observer_draw(family, rng, 1)[0]
        truth = {"params": params, "d": 0.0, "tau": float(rng.uniform(0.05, 0.5))}
        items, responses = _simulate(family, "d", truth, rng)
        false += cohere.fit(items, responses, ("open",))["d"]["interval_90"][0] > 0
    return family, {
        "d": {
            "r": float(np.corrcoef(d_true, d_est)[0, 1]),
            "coverage_90": float(inside),
            "confusion_with_tau": float(np.corrcoef(d_est, tau_true)[0, 1]),
        },
        "tau": {"r": float(np.corrcoef(tau_true, tau_est)[0, 1])},
        "false_incoherence": false / configs,
    }


def validation(configs=150, seed=20261113):
    """Recovery of d and tau from one session's open sets (respondents whose latent beliefs come
    from the family observers, not the fit's Dirichlet prior), and the rate at which coherent
    respondents are called incoherent (H1's test), which must stay at or below 10%."""
    from concurrent.futures import ProcessPoolExecutor

    seeds = np.random.SeedSequence(seed).spawn(len(cohere.FAMILIES))
    with ProcessPoolExecutor(3) as pool:
        results = dict(
            pool.map(
                _recovery_family,
                [(f, configs, s) for f, s in zip(cohere.FAMILIES, seeds, strict=True)],
            )
        )
    passed = all(
        v["d"]["r"] >= 0.8
        and v["d"]["coverage_90"] >= 0.8
        and abs(v["d"]["confusion_with_tau"]) <= 0.3
        and v["false_incoherence"] <= 0.10
        for v in results.values()
    )
    return {
        "schema_version": "epistemics.cohere-validation.v1",
        "configs": configs,
        "families": results,
        "passed": passed,
    }
