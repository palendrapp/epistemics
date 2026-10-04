"""Do any traits carry from abstract tasks to finance tasks? (exploration log, 4 October)

A consistency check on data already collected, specified before the finance side was computed.
For each candidate trait, one measure per configuration in abstract (urn) tasks and one in finance
tasks (stories about markets: market newsletters and company disclosure, central-bank statements,
the economist's forecasts); the test is whether the abstract ordering predicts the finance one.

  gap         stated-applied gap: |stated - applied| base rate at levels 1-3. Abstract: battery
              v2's six urn tasks (its published cells). Finance: the description tasks under the
              markets cover (corroboration-cues, disclosure-cues), each module weighted equally.
  confidence  the weight of a "definitely... confirmed" claim minus an "I think..." claim without
              a record (log-odds). Abstract: multi-agent open (an analyst's call), calls in order
              (first calls) and the wording urn families, each source weighted equally. Finance:
              the economist's forecasts (policy and policy3).
  grain       the share of answers at multiples of 0.05, among answers between 0.06 and 0.94 that
              move off the stated prior, on fresh single-claim cases. Abstract: the wording urn
              families. Finance: the economist's forecasts and the announced-count statements.

Per trait: Spearman's rank correlation over the configurations measured in both, with an exact
one-sided permutation p, and how many configurations sit on the same side of the median in both.
"""

import itertools
import json
from pathlib import Path

import numpy as np

from epistemics.dispositions.wording import base

GAP_ROOTS = (
    "output/disposition-cues-20260928",
    "output/disposition-cues-retest-20260928",
    "output/disposition-baseline-20260928",
    "output/disposition-variance-20260928",
    "output/disposition-weaker-cues-20260928",
)
GAP_MODULES = ("corroboration-cues", "disclosure-cues")
BATTERY_V2 = "output/battery-v2-20260929.json"
ADVICE_ROOTS = ("output/multi-agent-open-20260930",)
CALLS_ROOTS = ("output/calls-order-20261002",)
URN_ROOTS = (
    "output/wording-families-20261002",
    "output/wording-phrase-set-20261002",
    "output/wording-sessions-20261004",
)
POLICY_ROOTS = ("output/wording-families-20261002", "output/wording-phrase-set-policy-20261002")
ANNOUNCED_ROOTS = ("output/announced-count-20261001",)
LEVELS = (1, 2, 3)
MID = (0.06, 0.94)


def gap_abstract(path=BATTERY_V2):
    cells = json.loads(Path(path).read_text())["traits"]["stated_applied_gap"]["cells"]
    by = {}
    for key, value in cells.items():
        config, _ = key.split("/")
        by.setdefault(config, []).append(value)
    return {c: float(np.mean(v)) for c, v in by.items()}


def gap_finance(roots=GAP_ROOTS):
    from epistemics.ledger import dispositions

    by = {}
    for root in roots:
        for r in dispositions.extract(root):
            if not r.get("verified") or r.get("module") not in GAP_MODULES:
                continue
            fits = {s["slot"]: s for s in r.get("slot_fits", [])}
            if not all(fits.get(level, {}).get("stated") for level in LEVELS):
                continue
            gap = np.mean(
                [abs(np.mean(fits[k]["stated"]) - fits[k]["implied"]["mean"]) for k in LEVELS]
            )
            by.setdefault(r["configuration"], {}).setdefault(r["module"], []).append(float(gap))
    return {
        c: float(np.mean([np.mean(v) for v in modules.values()]))
        for c, modules in by.items()
        if set(modules) == set(GAP_MODULES)
    }


def _spread(rows):
    """'definitely... confirmed' minus 'I think...' from (wording, weight) pairs."""
    top = [w for k, w in rows if k == "confirmed"]
    low = [w for k, w in rows if k == "I think"]
    return float(np.mean(top) - np.mean(low)) if top and low else None


def confidence_abstract(advice=ADVICE_ROOTS, calls=CALLS_ROOTS, urn=URN_ROOTS):
    from epistemics.ledger import call_reaction, wording

    names = {0: "I think", 1: "plain", 2: "confirmed"}
    sources = {}
    for (c, source), rows in call_reaction.weights(advice).items():
        if source == "advice-peer (no record)":
            sources.setdefault(c, {})["advice"] = [(names[r["phrase"]], r["weight"]) for r in rows]
    for (c, _), rows in call_reaction.call_steps(calls).items():
        sources.setdefault(c, {})["calls"] = [
            (names[r["phrase"]], r["weight"]) for r in rows if r["phrase"] is not None
        ]
    for r in wording.records(urn):
        if base(r["wording"]["family"]) == "urn":
            sources.setdefault(r["configuration"], {}).setdefault("urn", []).extend(
                (x["wording"], x["weight"]) for x in r["wording"]["cases"]
            )
    out = {}
    for c, by in sources.items():
        spreads = {k: _spread(v) for k, v in by.items()}
        if all(s is not None for s in spreads.values()) and len(spreads) == 3:
            out[c] = {"spread": float(np.mean(list(spreads.values()))), "by_source": spreads}
    return out


def confidence_finance(policy=POLICY_ROOTS):
    from epistemics.ledger import wording

    rows = {}
    for r in wording.records(policy):
        if base(r["wording"]["family"]) == "policy":
            rows.setdefault(r["configuration"], []).extend(
                (x["wording"], x["weight"]) for x in r["wording"]["cases"]
            )
    return {c: {"spread": _spread(v)} for c, v in rows.items()}


def _round_share(answers):
    v = [a for a, prior in answers if MID[0] <= a <= MID[1] and round(a, 2) != round(prior, 2)]
    return (float(np.mean([round(a * 100) % 5 == 0 for a in v])), len(v)) if v else (None, 0)


def grain_abstract(urn=URN_ROOTS):
    from epistemics.ledger import wording

    answers = {}
    for r in wording.records(urn):
        if base(r["wording"]["family"]) == "urn":
            answers.setdefault(r["configuration"], []).extend(
                (x["answer"], x["prior"] / 100) for x in r["wording"]["cases"]
            )
    return {c: dict(zip(("share", "n"), _round_share(v), strict=True)) for c, v in answers.items()}


def grain_finance(policy=POLICY_ROOTS, announced=ANNOUNCED_ROOTS):
    from epistemics.ledger import dispositions, wording

    answers = {}
    for r in wording.records(policy):
        if base(r["wording"]["family"]) == "policy":
            answers.setdefault(r["configuration"], []).extend(
                (x["answer"], x["prior"] / 100) for x in r["wording"]["cases"]
            )
    for root in announced:
        for r in dispositions.extract(root):
            if r.get("verified") and "announced" in r:
                answers.setdefault(r["configuration"], []).extend(
                    (x["answer"], x["prior"] / 100) for x in r["announced"]["cases"]
                )
    return {c: dict(zip(("share", "n"), _round_share(v), strict=True)) for c, v in answers.items()}


def _ranks(x):
    order = np.argsort(np.argsort(x, kind="stable"), kind="stable")
    return order.astype(float)


def spearman(a, b):
    ra, rb = _ranks(np.asarray(a, float)), _ranks(np.asarray(b, float))
    return float(np.corrcoef(ra, rb)[0, 1])


def compare(abstract, finance):
    """Spearman's rho over the shared configurations, its exact one-sided permutation p, and how
    many configurations sit on the same side of the median in both."""
    configs = sorted(c for c in abstract if c in finance)
    a = np.array([abstract[c] for c in configs], float)
    b = np.array([finance[c] for c in configs], float)
    rho = spearman(a, b)
    perms = [spearman(a, b[list(p)]) for p in itertools.permutations(range(len(b)))]
    p = float(np.mean([r >= rho - 1e-12 for r in perms]))
    same = int(sum((x > np.median(a)) == (y > np.median(b)) for x, y in zip(a, b, strict=True)))
    return {
        "configurations": configs,
        "abstract": dict(zip(configs, a.tolist(), strict=True)),
        "finance": dict(zip(configs, b.tolist(), strict=True)),
        "rho": rho,
        "p_one_sided": p,
        "same_side_of_median": same,
    }


SWEEP = "output/sweep-20261001.json"
GENERAL = ("cohere-stage-a", "screen-fallback", "screen-stage-a", "screen-stage-b")


def grain_sweep(path=SWEEP):
    """Secondary: the sweep's open-case grain on the general vignettes (screen and coherence sets,
    averaged over the collections each configuration took) against central-bank statements stage A
    (eight configurations; statement steps are follow-ups, which round Astra's answers)."""
    per = json.loads(Path(path).read_text())["open_grain"]["per_collection"]
    general = {}
    for name in GENERAL:
        for c, v in per.get(name, {}).items():
            general.setdefault(c, []).append(v)
    return {c: float(np.mean(v)) for c, v in general.items()}, per["statements-stage-a"]


def summary():
    gap_a, gap_f = gap_abstract(), gap_finance()
    conf_a, conf_f = confidence_abstract(), confidence_finance()
    grain_a, grain_f = grain_abstract(), grain_finance()
    return {
        "schema_version": "epistemics.finance-transfer.v1",
        "traits": {
            "stated_applied_gap": compare(gap_a, gap_f),
            "confidence": {
                **compare(
                    {c: v["spread"] for c, v in conf_a.items()},
                    {c: v["spread"] for c, v in conf_f.items()},
                ),
                "abstract_by_source": {c: v["by_source"] for c, v in conf_a.items()},
            },
            "grain": {
                **compare(
                    {c: v["share"] for c, v in grain_a.items() if v["share"] is not None},
                    {c: v["share"] for c, v in grain_f.items() if v["share"] is not None},
                ),
                "answers": {
                    c: {"abstract": grain_a[c]["n"], "finance": grain_f.get(c, {}).get("n")}
                    for c in grain_a
                },
                "by_finance_task": {
                    "policy": compare(
                        {c: v["share"] for c, v in grain_a.items() if v["share"] is not None},
                        {c: v["share"] for c, v in grain_finance(announced=()).items()},
                    ),
                    "announced": compare(
                        {c: v["share"] for c, v in grain_a.items() if v["share"] is not None},
                        {c: v["share"] for c, v in grain_finance(policy=()).items()},
                    ),
                },
            },
            "grain_sweep": compare(*grain_sweep()),
        },
        "scope": (
            "Exploratory consistency check on existing data: does a configuration's place on a "
            "trait in abstract (urn) tasks predict its place in finance tasks? Specified before "
            "the finance side was computed; the qualitative patterns were already known."
        ),
    }


def critical_rho(n, alpha=0.05):
    """The smallest Spearman rho whose exact one-sided permutation p is at most alpha (n <= 9
    enumerates every ordering; larger n uses 200,000 random orderings, seed 20261004)."""
    base = np.arange(n, dtype=float)
    if n <= 9:
        null = np.array([np.corrcoef(base, p)[0, 1] for p in itertools.permutations(base)])
    else:
        rng = np.random.default_rng(20261004)
        null = np.array([np.corrcoef(base, rng.permutation(base))[0, 1] for _ in range(200000)])
    null = np.sort(null)
    for r in np.unique(null):
        if np.mean(null >= r - 1e-12) <= alpha:
            return float(r)
    return 1.0


def power(
    configurations=(8, 12),
    sessions=(4, 6, 8),
    true_rho=(1.0, 0.76, 0.5, 0.0),
    between=0.17,
    session_sd=0.20,
    datasets=2000,
    seed=20261005,
):
    """Power of the primary test (Spearman over configurations, one-sided alpha 0.05) for round
    readout: true configuration values with between-configuration SD `between` in each domain,
    correlated `true_rho` across domains; each session's share off by N(0, session_sd) (the
    pooled within-configuration session SD of the existing urn, policy and announced sessions);
    a configuration's domain value is the mean of its sessions."""
    rng = np.random.default_rng(seed)
    out = {}
    for n in configurations:
        crit = critical_rho(n)
        for m in sessions:
            for r in true_rho:
                hits = 0
                for _ in range(datasets):
                    a = rng.normal(0, between, n)
                    f = r * a + np.sqrt(1 - r**2) * rng.normal(0, between, n)
                    obs_a = a + rng.normal(0, session_sd / np.sqrt(m), n)
                    obs_f = f + rng.normal(0, session_sd / np.sqrt(m), n)
                    hits += spearman(obs_a, obs_f) >= crit - 1e-12
                out[f"n{n}/m{m}/rho{r}"] = hits / datasets
    return out
