"""Correlated changes (exploration log idea 21; docs/statement-updating-design.md).

Per configuration, pooling both orders of each item: step2(X) = a step1(X) + b step1(other),
with a bootstrap over items. Independent evidence: a = 1, b = 0. Correlated changes: b < 0.
Averaging: a = b + 1 = 1/2. Also the mean |step| of a change first and second, for agreeing and
disagreeing items, and the order law (the answer after both changes in either order)."""

import numpy as np

from epistemics.dispositions import correlated

BOOTSTRAP = 4000


def items(roots, key="correlated"):
    """key: "correlated" (statement changes) or "calls" (analysts' calls, the same rows)."""
    from epistemics.ledger import dispositions

    out = {}
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or key not in record:
                continue
            out.setdefault(record["configuration"], []).extend(record[key]["items"])
    return out


def analyse(rows, seed=20261122):
    fitted = correlated.fit(rows)
    if fitted is None:
        return None
    X, y, agree = fitted["rows"]
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(BOOTSTRAP):
        idx = rng.integers(0, len(y), len(y))
        boots.append(np.linalg.lstsq(X[idx], y[idx], rcond=None)[0])
    boots = np.array(boots)

    def interval(v):
        return [float(np.percentile(v, 5)), float(np.percentile(v, 95))]

    def magnitude(mask, column):
        return float(np.mean(np.abs(X[mask, column] if column is not None else y[mask])))

    by = {}
    for r in rows:
        by.setdefault(r["item"], []).append(r)
    order_gaps = [
        abs(orders[0]["total"] - orders[1]["total"]) for orders in by.values() if len(orders) == 2
    ]
    return {
        "a": {"mean": fitted["a"], "interval_90": interval(boots[:, 0])},
        "b": {"mean": fitted["b"], "interval_90": interval(boots[:, 1])},
        "changes": fitted["n"],
        "first_step": {"agree": magnitude(agree, 0), "disagree": magnitude(~agree, 0)},
        "second_step": {"agree": magnitude(agree, None), "disagree": magnitude(~agree, None)},
        "order_gap": float(np.mean(order_gaps)) if order_gaps else None,
    }


def summary(roots, key="correlated"):
    return {
        "schema_version": "epistemics.correlated-changes.v1",
        "evidence": key,
        "configurations": {c: analyse(r) for c, r in sorted(items(roots, key).items())},
        "scope": "Exploratory: one change, then both; independent evidence a = 1, b = 0; "
        "correlated changes b < 0; averaging a = 1/2, b = -1/2.",
    }
