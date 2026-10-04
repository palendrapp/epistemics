"""Single-judgment transfer (docs/single-judgment-preregistration.md; exploration log idea 36).

The preregistered abstract-to-finance test passed only as a difference between model families. Its
abstract round readout mixed base-rate questions, which everyone answers fine-grained, with urn
calls, which GPT-5.6 often gives no weight. This test uses single open judgments only:

  abstract  the open-inference screen vignettes (number processes, durations, inspections, pumps,
            tanks), open cases only
  finance   the economist's forecasts (wording-policy) and the central-bank statements (announced)

Round readout per session: the share of answers at multiples of 0.05 among answers between 0.06
and 0.94 (and, in the finance cases, off the stated prior); sessions with fewer than five such
answers have no value.

Co-primary, each in both domains (an intersection-union test: both domains must pass):
  H1  within GPT-6, Astra rounds more than Sol;
  H2  within GPT-5.6, Luna rounds more than Terra.
Statistic: the mean over effort levels of (mean session readout of the first variant - of the
second); one-sided p from permuting variant labels among each effort level's sessions. H1 and H2
are Holm-adjusted together.
Secondary: the configuration-level transfer, the mean of the two within-family Spearman rhos
between abstract and finance readout (exact null), and Spearman over all twelve.
"""

import itertools

import numpy as np

from epistemics.ledger.finance_transfer import MID, MIN_ANSWERS, holm, spearman

ABSTRACT_MODULES = tuple(
    f"screen-{family}-{form}"
    for family in ("gen", "num", "choice", "lists", "trend")
    for form in "a"
)
FINANCE_MODULES = tuple(f"wording-policy-{f}" for f in "abcd") + tuple(
    f"announced-{f}" for f in "abcd"
)
EFFORTS = ("low", "medium", "high")
VARIANTS = {"GPT-6": ("astra", "sol"), "GPT-5.6": ("luna", "terra")}
PERMUTATIONS = 20000
SEED = 20261008


def configuration(variant, effort):
    return variant if effort == "medium" else f"{variant}-{effort}"


def split(config):
    variant, _, effort = config.partition("-")
    return variant, effort or "medium"


def _share(values):
    v = [a for a in values if MID[0] <= a <= MID[1]]
    if len(v) < MIN_ANSWERS:
        return None, len(v)
    return float(np.mean([round(a * 100) % 5 == 0 for a in v])), len(v)


def sessions(roots):
    """Per verified session: configuration, domain, module and round-readout share."""
    from epistemics.ledger import dispositions
    from epistemics.ledger.sweep import case_class

    out = []
    for root in roots:
        for r in dispositions.extract(root):
            if not r.get("verified") or r.get("responses") is None:
                continue
            module = r["module"]
            if module in ABSTRACT_MODULES:
                items = {k: np.asarray(v) for k, v in r["items"].items()}
                values = [
                    float(v)
                    for i, v in enumerate(r["responses"])
                    if v is not None and case_class(module, items, i) == "open"
                ]
                domain = "abstract"
            elif module in FINANCE_MODULES:
                cases = (r.get("wording") or r.get("announced") or {}).get("cases", [])
                values = [
                    c["answer"]
                    for c in cases
                    if round(c["answer"], 2) != round(c["prior"] / 100, 2)
                ]
                domain = "finance"
            else:
                continue
            share, n = _share(values)
            out.append({"configuration": r["configuration"], "domain": domain, "module": module,
                        "run": r["run_id"], "round_share": share, "answers": n})  # fmt: skip
    return out


def contrast(rows, family, domain, rng, permutations=PERMUTATIONS):
    """Mean over efforts of (first variant - second variant) mean session readout, with a
    one-sided permutation p shuffling variant labels within each effort level."""
    first, second = VARIANTS[family]
    strata = []
    for effort in EFFORTS:
        a = [s["round_share"] for s in rows if s["domain"] == domain and s["round_share"] is not None
             and s["configuration"] == configuration(first, effort)]  # fmt: skip
        b = [s["round_share"] for s in rows if s["domain"] == domain and s["round_share"] is not None
             and s["configuration"] == configuration(second, effort)]  # fmt: skip
        if a and b:
            strata.append((effort, np.array(a), np.array(b)))
    if not strata:
        return None

    def stat(pairs):
        return float(np.mean([a.mean() - b.mean() for a, b in pairs]))

    observed = stat([(a, b) for _, a, b in strata])
    null = []
    for _ in range(permutations):
        shuffled = []
        for _, a, b in strata:
            pooled = rng.permutation(np.r_[a, b])
            shuffled.append((pooled[: len(a)], pooled[len(a) :]))
        null.append(stat(shuffled))
    return {
        "difference": observed,
        "p_one_sided": float(np.mean(np.array(null) >= observed - 1e-12)),
        "by_effort": {effort: float(a.mean() - b.mean()) for effort, a, b in strata},
        "sessions": {effort: [len(a), len(b)] for effort, a, b in strata},
    }


def _within_null():
    base = np.arange(6.0)
    null6 = np.array([spearman(base, np.array(p)) for p in itertools.permutations(base)])
    return np.add.outer(null6, null6).ravel() / 2


def pooled_within(values):
    """Mean of the two within-family Spearman rhos (six configurations each) between abstract
    and finance readout, with its exact one-sided p."""
    rhos = {}
    for family, (first, second) in VARIANTS.items():
        configs = [configuration(v, e) for v in (first, second) for e in EFFORTS]
        if any(values.get(c, {}).get(d) is None for c in configs for d in ("abstract", "finance")):
            return None
        rhos[family] = spearman(
            [values[c]["abstract"] for c in configs], [values[c]["finance"] for c in configs]
        )
    mean = float(np.mean(list(rhos.values())))
    return {"rho": rhos, "mean_rho": mean,
            "p_one_sided": float(np.mean(_within_null() >= mean - 1e-12))}  # fmt: skip


def preregistered(roots, permutations=PERMUTATIONS, seed=SEED):
    from epistemics.ledger.finance_transfer import _permutation_p

    rng = np.random.default_rng(seed)
    rows = sessions(roots)
    values = {}
    for s in rows:
        values.setdefault(s["configuration"], {"abstract": [], "finance": []})
        if s["round_share"] is not None:
            values[s["configuration"]][s["domain"]].append(s["round_share"])
    means = {
        c: {d: (float(np.mean(v)) if v else None) for d, v in by.items()}
        | {f"{d}_sessions": len(v) for d, v in by.items()}
        for c, by in values.items()
    }
    primary = {}
    for name, family in (("H1", "GPT-6"), ("H2", "GPT-5.6")):
        tests = {d: contrast(rows, family, d, rng, permutations) for d in ("abstract", "finance")}
        p = max(t["p_one_sided"] for t in tests.values()) if all(tests.values()) else 1.0
        primary[name] = {"family": family, "variants": VARIANTS[family], "domains": tests,
                         "p_intersection_union": p}  # fmt: skip
    adjusted = holm({k: v["p_intersection_union"] for k, v in primary.items()})
    for k, v in primary.items():
        v["p_holm"] = adjusted[k]
        v["pass"] = bool(
            adjusted[k] < 0.05 and all(t["difference"] > 0 for t in v["domains"].values() if t)
        )
    complete = {
        c: m for c, m in means.items() if m["abstract"] is not None and m["finance"] is not None
    }
    names = sorted(complete)
    rho, p = _permutation_p(
        np.array([complete[c]["abstract"] for c in names]),
        np.array([complete[c]["finance"] for c in names]),
        rng,
        permutations,
    )
    return {
        "schema_version": "epistemics.single-judgment-transfer.v1",
        "values": means,
        "primary": primary,
        "secondary": {
            "within_family_configurations": pooled_within(
                {c: {"abstract": m["abstract"], "finance": m["finance"]} for c, m in means.items()}
            ),
            "all_configurations": {"configurations": names, "rho": rho, "p_one_sided": p},
        },
        "scope": (
            "Preregistered (docs/single-judgment-preregistration.md): within each model family, "
            "does the variant that rounds its open single judgments more in abstract vignettes "
            "also round more in finance judgments?"
        ),
    }


def power(
    differences=((0.36, 0.17), (0.25, 0.12), (0.0, 0.0)),
    sessions=((5, 8), (5, 12)),
    session_sd=0.21,
    configuration_sd=0.05,
    datasets=1000,
    seed=20261009,
):
    """Power of one co-primary hypothesis: both domains' one-sided p below alpha. Holm over the two
    co-primaries tests the smaller p at 0.025 and the larger at 0.05, so power is reported at both.
    A true variant difference (abstract, finance) in round readout; configuration-level SD within a
    variant; session SD (0.21, the pooled within-configuration SD of the finance single-judgment
    sessions of output/finance-transfer-20261004*); sessions per configuration per domain. The
    defaults' first difference is the post hoc estimate for Astra against Sol."""
    rng = np.random.default_rng(seed)
    out = {}
    for m_a, m_f in sessions:
        for d_a, d_f in differences:
            hits = {0.025: 0, 0.05: 0}
            for _ in range(datasets):
                rows = []
                for domain, d, m in (("abstract", d_a, m_a), ("finance", d_f, m_f)):
                    for v, shift in (("astra", d / 2), ("sol", -d / 2)):
                        for e in EFFORTS:
                            level = 0.5 + shift + rng.normal(0, configuration_sd)
                            for _ in range(m):
                                rows.append({"configuration": configuration(v, e), "domain": domain,
                                             "round_share": level + rng.normal(0, session_sd)})  # fmt: skip
                worst = max(
                    contrast(rows, "GPT-6", d, rng, 400)["p_one_sided"]
                    for d in ("abstract", "finance")
                )
                for alpha in hits:
                    hits[alpha] += worst < alpha
            for alpha, h in hits.items():
                out[f"sessions{m_a}+{m_f}/diff{d_a}+{d_f}/alpha{alpha}"] = h / datasets
    return out


EXPERIMENTS = ("single-judgment-transfer",)


def passport(roots):
    """Per configuration, for the passport: its round readout on open single judgments in each
    domain; its variant's difference from the other variant of its family (this variant minus
    the other), overall and at its own effort; whether the difference had the same sign at every
    effort in both domains; the preregistered verdict; and the configuration-level transfer p."""
    run = preregistered(roots)
    every = {}
    for h in run["primary"].values():
        efforts = [e for t in h["domains"].values() if t for e in t["by_effort"].values()]
        every[h["family"]] = bool(efforts) and (
            all(e > 0 for e in efforts) or all(e < 0 for e in efforts)
        )
    out = {}
    for c, m in run["values"].items():
        if m["abstract"] is None or m["finance"] is None:
            continue
        variant, effort = split(c)
        family = next(f for f, vs in VARIANTS.items() if variant in vs)
        first, second = VARIANTS[family]
        sign = 1 if variant == first else -1
        h = next(v for v in run["primary"].values() if v["family"] == family)
        out[c] = {
            "abstract": m["abstract"],
            "finance": m["finance"],
            "sessions": m["abstract_sessions"] + m["finance_sessions"],
            "variant": variant,
            "partner": second if variant == first else first,
            "effort": effort,
            "family": family,
            "difference": {d: sign * t["difference"] for d, t in h["domains"].items() if t},
            "at_effort": {
                d: sign * t["by_effort"][effort]
                for d, t in h["domains"].items()
                if t and effort in t["by_effort"]
            },
            "every_effort": every[family],
            "p_holm": h["p_holm"],
            "transfer_pass": h["pass"],
            "configuration_transfer_p": (
                run["secondary"]["within_family_configurations"] or {}
            ).get("p_one_sided"),
        }
    return out
