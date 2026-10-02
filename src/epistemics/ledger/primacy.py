"""Exploratory: does a change count less when it comes later (primacy), per configuration, across
the sequence data where order was varied (docs/exploration-log.md, idea 22)?

  statements stage A   each multi-change sequence stepwise in orders A and B (B reverses A): the
                       change first in one order is last in the other, so the same change gives a
                       first-position step and a last-position step.
  correlated changes   each two-change statement in both orders: every change once first and once
                       second.

For each change and configuration, |step later| and |step first| (log-odds); per configuration and
dataset, the ratio of their means with a bootstrap interval over changes. Ratio 1: no position
effect; below 1: primacy; above 1: recency. Stylistic changes are left out.
"""

import numpy as np

from epistemics.dispositions import statements as st
from epistemics.dispositions.screen import logit

BOOTSTRAP = 4000


def statement_pairs(roots):
    from epistemics.ledger import statements as statements_ledger

    out = {}
    for c, v in statements_ledger.by_configuration(statements_ledger.sessions(roots), "a").items():
        by = {}
        for r in v["records"]:
            by.setdefault(r["sid"], {})[r["condition"]] = r
        for conds in by.values():
            if "A" not in conds or "B" not in conds or conds["A"]["n"] < 2:
                continue
            steps = {}
            for order in ("A", "B"):
                r = conds[order]
                z = logit(r["answers"])
                for t, (name, d) in enumerate(r["changes"], 1):
                    steps.setdefault((name, d), {})[order] = (t, float(z[t] - z[t - 1]))
            n = conds["A"]["n"]
            for (name, _), positions in steps.items():
                if name in st.STYLES or len(positions) != 2:
                    continue
                (ta, sa), (tb, sb) = positions["A"], positions["B"]
                if {ta, tb} == {1, n}:  # first in one order, last in the other
                    first, last = (sa, sb) if ta == 1 else (sb, sa)
                    out.setdefault(c, []).append((abs(first), abs(last)))
    return out


def correlated_pairs(roots):
    from epistemics.ledger import correlated as correlated_ledger

    out = {}
    for c, rows in correlated_ledger.items(roots).items():
        by = {}
        for r in rows:
            by.setdefault(r["item"], []).append(r)
        for orders in by.values():
            if len(orders) != 2:
                continue
            first = {tuple(o["first"]): o["step1"] for o in orders}
            for o in orders:
                x = tuple(o["second"])
                if x in first:
                    out.setdefault(c, []).append((abs(first[x]), abs(o["step2"])))
    return out


def ratio(pairs, seed=20261123):
    pairs = np.array(pairs)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(pairs), size=(BOOTSTRAP, len(pairs)))
    boots = pairs[idx, 1].mean(axis=1) / pairs[idx, 0].mean(axis=1)
    return {
        "ratio": float(pairs[:, 1].mean() / pairs[:, 0].mean()),
        "interval_90": [float(np.percentile(boots, 5)), float(np.percentile(boots, 95))],
        "first": float(pairs[:, 0].mean()),
        "later": float(pairs[:, 1].mean()),
        "changes": len(pairs),
    }


def summary(statement_roots, correlated_roots):
    s = statement_pairs(statement_roots)
    c = correlated_pairs(correlated_roots)
    configs = sorted(set(s) | set(c))
    return {
        "schema_version": "epistemics.primacy.v1",
        "configurations": {
            k: {
                "statements": ratio(s[k]) if k in s else None,
                "correlated": ratio(c[k]) if k in c else None,
            }
            for k in configs
        },
        "scope": "Exploratory: the same change later against first; ratio below 1 is primacy.",
    }
