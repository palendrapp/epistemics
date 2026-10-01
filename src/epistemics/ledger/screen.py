"""Open-inference screen analyses (docs/open-inference-screen-design.md).

Stage A (spread; form a, one session per configuration), per contrast:
  1. spread: the between-configuration SD of the score is at least twice its noise, estimated
     from the split halves as the SD across configurations of the half-differences, divided by 2
     (a fixed difference between the halves' items cancels; configuration-by-item variation only
     makes the estimate conservative);
  2. guard: at least three configurations depart from the median by more than the contrast's
     meaningful difference (screen.delta: an eighth of its parameters' plausible range);
  3. no shared rule: fewer than 80% of open items get the same answer (within 2 points) from all
     configurations.
A family passes when either contrast passes and every configuration's anchors are within 5 points
(otherwise its texts are broken, and it is reported, not passed).

Stage B (reliability; forms a and b), per contrast of the families that passed stage A:
  1. the intraclass correlation of configurations' scores across the two sessions (each form
     centred across configurations) is at least 0.5, with a permutation p (configuration labels
     shuffled within each form) below 0.05, Holm across the contrasts entering stage B;
  2. the retest correlation is positive.
"""

import numpy as np

from epistemics.dispositions import screen

SHARED = 0.02  # "the same answer": within 2 points
SHARED_SHARE = 0.8
SPREAD_FACTOR = 2.0
DEPARTING = 3
ICC_MIN = 0.5
PERMUTATIONS = 5000
CONFIGURATIONS = ("astra", "sol", "astra-low", "sol-low", "luna", "terra")


def sessions(roots):
    """Verified screen sessions: configuration, family, form, contrasts, anchors, responses."""
    from epistemics.ledger import dispositions

    out = []
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "screen" not in record:
                continue
            s = record["screen"]
            out.append(
                {
                    "root": str(root),
                    "run_id": record["run_id"],
                    "configuration": record["configuration"],
                    "family": s["family"],
                    "form": s["form"],
                    "contrasts": s["contrasts"],
                    "anchors_ok": s["anchors_ok"],
                    "anchor_errors": s["anchor_errors"],
                    "open_responses": s["open_responses"],
                }
            )
    return out


def stage_a_family(family, rows):
    """rows: one form-a session per configuration."""
    configs = [r["configuration"] for r in rows]
    deltas = screen.delta(family, "a")
    responses = np.array([r["open_responses"] for r in rows])
    same = np.ptp(responses, axis=0) <= SHARED + 1e-9
    shared = float(same.mean())
    contrasts = {}
    for name in screen.SPEC[family]["contrasts"]:
        scores = np.array([r["contrasts"][name]["score"] for r in rows])
        halves = np.array([r["contrasts"][name]["halves"] for r in rows])
        noise = float(np.std(halves[:, 0] - halves[:, 1], ddof=1) / 2)
        spread = float(np.std(scores, ddof=1)) if len(scores) > 1 else 0.0
        median_se = float(np.median([r["contrasts"][name]["se"] for r in rows]))
        departing = int(np.sum(np.abs(scores - np.median(scores)) > deltas[name]))
        checks = {
            "spread": spread >= SPREAD_FACTOR * noise and spread > 0,
            "guard": departing >= DEPARTING,
            "no_shared_rule": shared < SHARED_SHARE,
        }
        contrasts[name] = {
            "scores": dict(zip(configs, scores.round(4).tolist(), strict=True)),
            "spread": spread,
            "noise": noise,
            "median_se": median_se,
            "delta": deltas[name],
            "departing": departing,
            "checks": checks,
            "passed": all(checks.values()),
        }
    anchors_ok = all(r["anchors_ok"] for r in rows)
    openness = screen.openness(family, "a")[screen.design(family, "a")["kind"] == "open"]
    z = screen.logit(responses)
    return {
        "configurations": configs,
        "anchors_ok": anchors_ok,
        "anchor_failures": [r["configuration"] for r in rows if not r["anchors_ok"]],
        "shared_answer_share": shared,
        "contrasts": contrasts,
        "passed": anchors_ok and any(c["passed"] for c in contrasts.values()),
        # Per open item: the family model's openness against the observed spread (log-odds SD
        # across configurations).
        "items": [
            {"openness": float(o), "spread": float(s)}
            for o, s in zip(openness, np.std(z, axis=0), strict=True)
        ],
    }


def stage_a(roots):
    rows = [r for r in sessions(roots) if r["form"] == "a"]
    families = {}
    for family in screen.FAMILIES:
        chosen = [r for r in rows if r["family"] == family]
        if len(chosen) >= 3:
            families[family] = stage_a_family(family, chosen)
    passed = [f for f, v in families.items() if v["passed"]]
    return {
        "schema_version": "epistemics.screen-stage-a.v1",
        "sessions": len(rows),
        "families": families,
        "passed": passed,
        "stage_b_groups": [
            {
                "configurations": sorted(
                    {c for f in passed for c in families[f]["configurations"]}
                ),
                "modules": [f"screen-{f}-b" for f in passed],
                "contexts": [["screen", "markets", 1]],
            }
        ]
        if passed
        else [],
        "commitment": commitment(rows),
    }


def icc(matrix):
    """Consistency ICC for a configurations x forms matrix: each form's scores are centred across
    configurations (removing the fixed difference between the forms' items), then the one-way
    random-effects ICC(1) is computed."""
    matrix = np.asarray(matrix, dtype=float)
    matrix = matrix - matrix.mean(axis=0, keepdims=True)
    n, k = matrix.shape
    msb = k * np.sum(matrix.mean(axis=1) ** 2) / (n - 1)
    msw = np.sum((matrix - matrix.mean(axis=1, keepdims=True)) ** 2) / (n * (k - 1))
    denominator = msb + (k - 1) * msw
    return float((msb - msw) / denominator) if denominator > 0 else 0.0


def icc_test(matrix, rng, permutations=PERMUTATIONS):
    """ICC and its permutation p: configuration labels are shuffled within each form, which is
    exact under no configuration differences."""
    matrix = np.asarray(matrix, dtype=float)
    observed = icc(matrix)
    count = 0
    for _ in range(permutations):
        shuffled = np.column_stack([rng.permutation(col) for col in matrix.T])
        count += icc(shuffled) >= observed - 1e-12
    return observed, (1 + count) / (1 + permutations)


def holm(ps):
    order = sorted(ps, key=ps.get)
    out, running = {}, 0.0
    for i, key in enumerate(order):
        running = max(running, min(1.0, (len(order) - i) * ps[key]))
        out[key] = running
    return out


def stage_b(roots, seed=20261102, families=screen.FAMILIES):
    """Holm runs across the contrasts of `families` (the fallback round restricts them to F2, F4
    and F5)."""
    rows = sessions(roots)
    rng = np.random.default_rng(seed)
    results, ps = {}, {}
    for family in families:
        by_config = {}
        for r in rows:
            if r["family"] == family:
                by_config.setdefault(r["configuration"], {})[r["form"]] = r
        paired = {c: v for c, v in by_config.items() if "a" in v and "b" in v}
        if len(paired) < 3:
            continue
        configs = sorted(paired)
        entry = {"configurations": configs, "contrasts": {}}
        for name in screen.SPEC[family]["contrasts"]:
            matrix = [
                [paired[c][form]["contrasts"][name]["score"] for form in ("a", "b")]
                for c in configs
            ]
            value, p = icc_test(matrix, rng)
            a, b = np.array(matrix).T
            retest = float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else 0.0
            entry["contrasts"][name] = {
                "scores": {c: m for c, m in zip(configs, matrix, strict=True)},
                "icc": value,
                "p": p,
                "retest_r": retest,
            }
            ps[f"{family}/{name}"] = p
        entry["anchors_ok"] = all(v["b"]["anchors_ok"] for v in paired.values())
        results[family] = entry
    adjusted = holm(ps)
    for key, p_holm in adjusted.items():
        family, name = key.split("/")
        c = results[family]["contrasts"][name]
        c["p_holm"] = p_holm
        c["passed"] = c["icc"] >= ICC_MIN and p_holm < 0.05 and c["retest_r"] > 0
    for entry in results.values():
        entry["passed"] = entry["anchors_ok"] and any(
            c.get("passed") for c in entry["contrasts"].values()
        )
    return {
        "schema_version": "epistemics.screen-stage-b.v1",
        "families": results,
        "passed": [f for f, v in results.items() if v["passed"]],
    }


def commitment(rows):
    """Exploratory: each configuration's commitment score per family (the first contrast, signed so
    that + commits more to the simplest model), and their correlations across families."""
    scores = {}
    for r in rows:
        name = screen.SPEC[r["family"]]["contrasts"][0]
        value = screen.COMMITMENT[r["family"]] * r["contrasts"][name]["score"]
        scores.setdefault(r["family"], {})[r["configuration"]] = value
    families = sorted(scores)
    correlations = {}
    for i, f in enumerate(families):
        for g in families[i + 1 :]:
            common = sorted(set(scores[f]) & set(scores[g]))
            if len(common) >= 4:
                x = np.array([scores[f][c] for c in common])
                y = np.array([scores[g][c] for c in common])
                if np.std(x) > 0 and np.std(y) > 0:
                    correlations[f"{f}~{g}"] = float(np.corrcoef(x, y)[0, 1])
    return {"scores": scores, "correlations": correlations}


# Validation before collection: contrast recovery and the screen's calibration.
DRIVERS = {family: spec["drivers"] for family, spec in screen.SPEC.items()}


def _spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def _at(family, names, q):
    params = screen.mid(family)
    for name in names:
        spec = screen.SPEC[family]["params"][name]
        if spec[0] == "log":
            params[name] = float(np.exp(np.log(spec[1]) + q * (np.log(spec[2]) - np.log(spec[1]))))
        else:
            params[name] = spec[0] + q * (spec[1] - spec[0])
    return params


def recovery(respondents=200, noise=0.3, seed=20261103):
    """Per contrast: reliability (rank correlation of scores at report noise with noiseless
    scores, parameters drawn from the plausible range), monotonicity in its driving parameters
    (largest decrease along the range, others at their middle), and the rank correlation with the
    driving parameter when the other parameters vary (descriptive: how far nuisance parameters
    confound the contrast)."""
    out = {}
    for family in screen.FAMILIES:
        for form in screen.FORMS:
            rng = np.random.default_rng(seed + screen.FAMILIES.index(family))
            items = screen.design(family, form)
            draws = screen.draw(family, rng, respondents)
            noisy, clean = {}, {}
            for p in draws:
                s = screen.contrast_scores(items, screen.respond(family, items, p, rng, noise))
                c = screen.contrast_scores(items, screen.predict(family, items, p))
                for name in s:
                    noisy.setdefault(name, []).append(s[name]["score"])
                    clean.setdefault(name, []).append(c[name]["score"])
            for name, (names, sign) in DRIVERS[family].items():
                line = [
                    screen.contrast_scores(
                        items, screen.predict(family, items, _at(family, names, q))
                    )[name]["score"]
                    for q in np.linspace(0, 1, 11)
                ]
                driver = [float(np.mean([p[n] for n in names])) for p in draws]
                out[f"{family}-{form}/{name}"] = {
                    "reliability": _spearman(noisy[name], clean[name]),
                    "largest_decrease": float(max(0.0, -np.min(np.diff(line) * sign))),
                    "driver_rank": sign * _spearman(driver, clean[name]),
                }
    passed = all(v["reliability"] >= 0.8 and v["largest_decrease"] <= 0.05 for v in out.values())
    return {
        "schema_version": "epistemics.screen-recovery.v1",
        "noise": noise,
        "respondents": respondents,
        "contrasts": out,
        "passed": passed,
    }


def _jitter(family, params, rng, scale):
    out = dict(params)
    for name, spec in screen.SPEC[family]["params"].items():
        if spec[0] == "log":
            lo, hi = np.log(spec[1]), np.log(spec[2])
            out[name] = float(
                np.exp(np.clip(np.log(out[name]) + rng.normal(0, scale * (hi - lo)), lo, hi))
            )
        else:
            lo, hi = spec
            out[name] = float(np.clip(out[name] + rng.normal(0, scale * (hi - lo)), lo, hi))
    return out


def _simulated_sessions(family, config_params, rng, noise, state):
    rows = []
    for c, params in enumerate(config_params):
        for form in screen.FORMS:
            items = screen.design(family, form)
            session_params = _jitter(family, params, rng, state) if state else params
            s = screen.session(items, screen.respond(family, items, session_params, rng, noise))
            rows.append({"configuration": str(c), **s})
    return rows


def _calibration_cell(args):
    family, scenario, datasets, configs, noise, state, seed = args
    rng = np.random.default_rng(seed)
    a_passes = b_passes = 0
    for _ in range(datasets):
        if scenario == "differences":
            params = screen.draw(family, rng, configs)
        else:
            params = screen.draw(family, rng, 1) * configs
        rows = _simulated_sessions(
            family, params, rng, noise, state if scenario == "states" else 0.0
        )
        a_passes += stage_a_family(family, [r for r in rows if r["form"] == "a"])["passed"]
        ps, checks = {}, {}
        for name in screen.SPEC[family]["contrasts"]:
            matrix = [
                [
                    next(
                        r["contrasts"][name]["score"]
                        for r in rows
                        if r["configuration"] == str(c) and r["form"] == form
                    )
                    for form in screen.FORMS
                ]
                for c in range(configs)
            ]
            value, ps[name] = icc_test(matrix, rng, 500)
            a, b = np.array(matrix).T
            checks[name] = value >= ICC_MIN and float(np.corrcoef(a, b)[0, 1]) > 0
        adjusted = holm(ps)
        b_passes += any(adjusted[n] < 0.05 and checks[n] for n in ps)
    return family, scenario, a_passes / datasets, b_passes / datasets


WORKERS = 8


def calibration(datasets=200, configs=6, noise=0.3, state=0.1, seed=20261104):
    """Pass rates of stages A and B per family, for six simulated configurations:
    none (one shared parameter set, report noise only), states (shared parameters with
    session-to-session jitter, sd `state` of each parameter's range) and differences (each
    configuration draws its own parameters from the plausible range).
    Criteria: stage A passes at most 10% with none; stage B is not significantly above 5% with
    states (at most 5% plus two binomial standard errors; its permutation test is exact); stage A
    passes at least 80% with differences."""
    from concurrent.futures import ProcessPoolExecutor

    scenarios = ("none", "states", "differences")
    seeds = np.random.SeedSequence(seed).spawn(len(screen.FAMILIES) * len(scenarios))
    jobs = [
        (family, scenario, datasets, configs, noise, state, seeds[i * len(scenarios) + j])
        for i, family in enumerate(screen.FAMILIES)
        for j, scenario in enumerate(scenarios)
    ]
    with ProcessPoolExecutor(WORKERS) as pool:
        cells = list(pool.map(_calibration_cell, jobs))
    result = {}
    for family, scenario, a, b in cells:
        result.setdefault(family, {})[scenario] = {"stage_a": a, "stage_b": b}
    b_limit = 0.05 + 2 * float(np.sqrt(0.05 * 0.95 / datasets))
    passed = all(
        v["none"]["stage_a"] <= 0.10
        and v["states"]["stage_b"] <= b_limit
        and v["differences"]["stage_a"] >= 0.8
        for v in result.values()
    )
    return {
        "schema_version": "epistemics.screen-calibration.v1",
        "datasets": datasets,
        "configs": configs,
        "noise": noise,
        "state": state,
        "stage_b_limit": b_limit,
        "result": result,
        "passed": passed,
    }


# Profile recovery: can each family's observer parameters be recovered, and told apart, from a
# configuration's sessions? Criteria, per profile parameter: recovery correlation at least 0.8,
# 90% coverage at least 0.8, and its estimate correlated at most 0.3 (absolute) with every other
# true parameter of the family (the confusion matrix is near-diagonal).
PROFILE_R = 0.8
PROFILE_COVERAGE = 0.8
PROFILE_CONFUSION = 0.3


def _scale(family, name, values):
    log = screen.SPEC[family]["params"][name][0] == "log"
    return np.log(values) if log else np.asarray(values, dtype=float)


def _profile_family(args):
    family, configs, forms, seed = args
    rng = np.random.default_rng(seed)
    truths = screen.draw(family, rng, configs)
    noises = rng.uniform(0.1, 0.5, configs)
    fits = []
    for truth, noise in zip(truths, noises, strict=True):
        responses = {
            form: screen.respond(family, screen.design(family, form), truth, rng, noise)
            for form in forms
        }
        fits.append(screen.fit_profile(family, responses, forms))
    names = list(screen.SPEC[family]["params"])
    out = {}
    for name in screen.PROFILE[family]:
        estimate = _scale(family, name, [f[name]["mean"] for f in fits])
        truth = _scale(family, name, [t[name] for t in truths])
        inside = [
            f[name]["interval_90"][0] - 1e-9 <= t[name] <= f[name]["interval_90"][1] + 1e-9
            for f, t in zip(fits, truths, strict=True)
        ]
        confusion = {
            other: float(
                np.corrcoef(estimate, _scale(family, other, [t[other] for t in truths]))[0, 1]
            )
            for other in names
        }
        off = max(abs(v) for k, v in confusion.items() if k != name)
        out[name] = {
            "r": float(np.corrcoef(estimate, truth)[0, 1]),
            "coverage_90": float(np.mean(inside)),
            "confusion": confusion,
            "largest_confusion": off,
            "passed": bool(
                np.corrcoef(estimate, truth)[0, 1] >= PROFILE_R
                and np.mean(inside) >= PROFILE_COVERAGE
                and off <= PROFILE_CONFUSION
            ),
        }
    return family, "+".join(forms), out


def profile_recovery(configs=100, seed=20261105):
    """Profile recovery per family with both forms (the screen's stage A and B sessions), and,
    descriptively, with form a only (stage A)."""
    from concurrent.futures import ProcessPoolExecutor

    jobs = []
    seeds = np.random.SeedSequence(seed).spawn(2 * len(screen.FAMILIES))
    for k, family in enumerate(screen.FAMILIES):
        jobs.append((family, configs, ("a", "b"), seeds[2 * k]))
        jobs.append((family, configs, ("a",), seeds[2 * k + 1]))
    with ProcessPoolExecutor(WORKERS) as pool:
        results = list(pool.map(_profile_family, jobs))
    out = {}
    for family, forms, params in results:
        out.setdefault(family, {})[forms] = params
    passed = all(p["passed"] for v in out.values() for p in v["a+b"].values())
    return {
        "schema_version": "epistemics.screen-profile-recovery.v1",
        "configs": configs,
        "criteria": {
            "r": PROFILE_R,
            "coverage_90": PROFILE_COVERAGE,
            "confusion": PROFILE_CONFUSION,
        },
        "families": out,
        "passed": passed,
    }
