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

import functools
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


@functools.cache
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


# Preregistered test (docs/finance-transfer-preregistration.md): fresh sessions in one root.
ABSTRACT_MODULES = tuple(f"wording-urn-{f}" for f in "abcd") + (
    "copying-urn-asked",
    "selection-urn-asked",
)
FINANCE_MODULES = (
    tuple(f"wording-policy-{f}" for f in "abcd")
    + ("corroboration-cues", "disclosure-cues")
    + ("announced-a", "announced-b")
)
GAP_STRUCTURES = {
    "abstract": ("copying-urn-asked", "selection-urn-asked"),
    "finance": ("corroboration-cues", "disclosure-cues"),
}
GPT6 = ("astra-low", "astra", "astra-high", "sol-low", "sol", "sol-high")
GPT56 = ("luna-low", "luna", "luna-high", "terra-low", "terra", "terra-high")
MIN_SESSIONS = {"abstract": 6, "finance": 8}
MIN_ANSWERS = 5
MIN_CONFIGS = 10
PERMUTATIONS = 200000
SEED = 20261006


# Questions about a source's behaviour (its copying or withholding rate), not about the outcome
# whose prior the case states: their answers are never excluded as "at the stated prior".
RATE_KINDS = ("rate", "probe")


def _answers(record):
    """(answer, stated prior of the outcome asked about, or None) for every probability answer of
    a session."""
    if "wording" in record:
        return [(c["answer"], c["prior"] / 100) for c in record["wording"]["cases"]]
    if "announced" in record:
        return [(c["answer"], c["prior"] / 100) for c in record["announced"]["cases"]]
    items = record["items"]
    out = []
    for i, v in enumerate(record["responses"]):
        if v is None or ("response" in items and items["response"][i] != "probability"):
            continue
        asks_outcome = "prior" in items and str(items["kind"][i]) not in RATE_KINDS
        out.append((float(v), float(items["prior"][i]) if asks_outcome else None))
    return out


def _gap(record):
    fits = {s["slot"]: s for s in record.get("slot_fits", [])}
    if not all(fits.get(level, {}).get("stated") for level in LEVELS):
        return None
    return float(
        np.mean([abs(np.mean(fits[k]["stated"]) - fits[k]["implied"]["mean"]) for k in LEVELS])
    )


def sessions(root):
    """Per verified session: configuration, domain, module, its round-readout share (None below
    MIN_ANSWERS qualifying answers), its stated-applied gap where it asks base rates, and its
    wording weights where it is a wording session."""
    from epistemics.ledger import dispositions

    out = []
    for r in dispositions.extract(root):
        if not r.get("verified"):
            continue
        module = r["module"]
        domain = "abstract" if module in ABSTRACT_MODULES else (
            "finance" if module in FINANCE_MODULES else None
        )  # fmt: skip
        if domain is None:
            continue
        answers = [(a, p if p is not None else -1.0) for a, p in _answers(r)]
        share, n = _round_share(answers)
        out.append(
            {
                "configuration": r["configuration"],
                "domain": domain,
                "module": module,
                "run": r["run_id"],
                "round_share": share if n >= MIN_ANSWERS else None,
                "round_answers": n,
                "gap": _gap(r) if module in GAP_STRUCTURES[domain] else None,
                "wording": [(c["wording"], c["weight"]) for c in r["wording"]["cases"]]
                if "wording" in r
                else None,
            }
        )
    return out


def _permutation_p(a, b, rng, permutations=PERMUTATIONS):
    rho = spearman(a, b)
    n = len(a)
    if n <= 9:
        null = [spearman(a, np.asarray(b)[list(p)]) for p in itertools.permutations(range(n))]
    else:
        b = np.asarray(b, float)
        null = [spearman(a, b[rng.permutation(n)]) for _ in range(permutations)]
    return rho, float(np.mean(np.asarray(null) >= rho - 1e-12))


def holm(ps):
    order = sorted(ps, key=ps.get)
    out, running = {}, 0.0
    for k, name in enumerate(order):
        running = max(running, min(1.0, ps[name] * (len(ps) - k)))
        out[name] = running
    return out


def preregistered(roots, permutations=PERMUTATIONS, seed=SEED):
    """H1-H4 of the preregistration from the collection's sessions: the first root and its
    continuation or top-up roots (a single root may be passed as a string or path)."""
    rng = np.random.default_rng(seed)
    if isinstance(roots, (str, Path)):
        roots = [roots]
    rows = [s for root in roots for s in sessions(root)]
    counts, values = {}, {}
    for s in rows:
        counts.setdefault(s["configuration"], {"abstract": 0, "finance": 0})[s["domain"]] += 1
    included = sorted(
        c for c, n in counts.items() if all(n[d] >= MIN_SESSIONS[d] for d in MIN_SESSIONS)
    )
    for c in included:
        mine = [s for s in rows if s["configuration"] == c]
        entry = {}
        for d in ("abstract", "finance"):
            shares = [
                s["round_share"] for s in mine if s["domain"] == d and s["round_share"] is not None
            ]
            gaps = [
                float(np.mean(v))
                for m in GAP_STRUCTURES[d]
                if (v := [s["gap"] for s in mine if s["module"] == m and s["gap"] is not None])
            ]
            wording = [w for s in mine if s["domain"] == d and s["wording"] for w in s["wording"]]
            entry[d] = {
                "round_readout": float(np.mean(shares)) if shares else None,
                "round_sessions": len(shares),
                "round_session_sd": float(np.std(shares, ddof=1)) if len(shares) > 1 else None,
                "gap": float(np.mean(gaps)) if len(gaps) == 2 else None,
                "confidence": _spread(wording),
            }
        entry["far_round_readout"] = (
            float(np.mean(v))
            if (v := [s["round_share"] for s in mine if s["module"].startswith("announced-") and s["round_share"] is not None])
            else None
        )  # fmt: skip
        values[c] = entry

    def test(trait, configs, abstract_key=None):
        pairs = [
            (c, values[c]["abstract"][trait], values[c]["finance"][trait])
            for c in configs
            if c in values
            and values[c]["abstract"][trait] is not None
            and values[c]["finance"][trait] is not None
        ]
        if len(pairs) < 4:
            return None
        names, a, b = zip(*pairs, strict=True)
        rho, p = _permutation_p(np.array(a), np.array(b), rng, permutations)
        same = int(sum((x > np.median(a)) == (y > np.median(b)) for x, y in zip(a, b, strict=True)))
        return {"configurations": list(names), "rho": rho, "p_one_sided": p,
                "critical_rho": critical_rho(len(names)), "same_side_of_median": same}  # fmt: skip

    # H1 runs on every included configuration; below MIN_CONFIGS it is flagged, with the
    # critical rho for the number included (the design's fallback).
    h1 = test("round_readout", included)
    if h1:
        h1["below_minimum"] = len(h1["configurations"]) < MIN_CONFIGS
        h1["pass"] = bool(h1["rho"] > 0 and h1["p_one_sided"] < 0.05)
    secondary = {
        "H2a": test("round_readout", [c for c in included if c in GPT6]),
        "H2b": test("round_readout", [c for c in included if c in GPT56]),
        "H3": test("gap", included),
        "H4": test("confidence", included),
    }
    adjusted = holm({k: v["p_one_sided"] for k, v in secondary.items() if v})
    for k, v in secondary.items():
        if v:
            v["p_holm"] = adjusted[k]
            v["pass"] = bool(v["rho"] > 0 and adjusted[k] < 0.05)
    far = None
    names = sorted(c for c, v in values.items() if v["far_round_readout"] is not None)
    if len(names) >= 4:
        a = np.array([values[c]["abstract"]["round_readout"] for c in names])
        b = np.array([values[c]["far_round_readout"] for c in names])
        rho, p = _permutation_p(a, b, rng, permutations)
        far = {"configurations": names, "rho": rho, "p_one_sided": p}
    return {
        "schema_version": "epistemics.finance-transfer-preregistered.v1",
        "sessions": {c: counts[c] for c in sorted(counts)},
        "included": included,
        "values": values,
        "H1": h1,
        "secondary": secondary,
        "reported": {"far_round_readout": far},
        "scope": (
            "Preregistered (docs/finance-transfer-preregistration.md): does a configuration's "
            "round readout in abstract urn tasks predict its round readout in finance tasks?"
        ),
    }


def power_gap(
    families=((6, 6), (6, 2)),
    true_rho=(1.0, 0.76, 0.0),
    sessions=4,
    datasets=2000,
    seed=20261007,
):
    """Power of H3 (Spearman over configurations, one-sided alpha 0.05) for the stated-applied
    gap: GPT-6 gaps |N(0.02, 0.015)| with session SD 0.02, GPT-5.6 gaps |N(0.10, 0.05)| with
    session SD 0.08; finance values correlated `true_rho` with abstract on a 0.6 scale; four
    rate-asking sessions per domain."""
    rng = np.random.default_rng(seed)
    out = {}
    for n6, n5 in families:
        n = n6 + n5
        crit = critical_rho(n)
        for r in true_rho:
            hits = 0
            for _ in range(datasets):
                a = np.r_[np.abs(rng.normal(0.02, 0.015, n6)), np.abs(rng.normal(0.10, 0.05, n5))]
                z = (a - a.mean()) / a.std()
                f = a.mean() + (r * z + np.sqrt(1 - r**2) * rng.normal(0, 1, n)) * a.std() * 0.6
                sd = np.r_[np.full(n6, 0.02), np.full(n5, 0.08)] / np.sqrt(sessions)
                hits += spearman(a + rng.normal(0, sd), f + rng.normal(0, sd)) >= crit - 1e-12
            out[f"n{n}/gpt56_{n5}/rho{r}"] = hits / datasets
    return out
