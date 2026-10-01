"""Announced count (exploration log idea 1; docs/statement-updating-design.md): the step on one
reported change, by the number of changes the statement is declared to hold.

Per configuration, pooled over the four forms (every case under every condition):
  mean_step     mean signed step from the stated prior, per condition, with a bootstrap interval
                over cases;
  ratios        three / one and six / one;
  restored      (three-said - three) / (one - three): the share of the drop from one change to
                three that disclosing the two rewordings restores. 0: a budget by count; 1: only
                substantive changes count (the pragmatic reading).
"""

import numpy as np

from epistemics.dispositions import announced

BOOTSTRAP = 4000


def cases(roots):
    from epistemics.ledger import dispositions

    out = {}
    for root in roots:
        for record in dispositions.extract(root):
            if not record.get("verified") or "announced" not in record:
                continue
            out.setdefault(record["configuration"], []).extend(record["announced"]["cases"])
    return out


def analyse(rows, seed=20261121):
    by = {}
    for r in rows:
        by.setdefault(r["item"], {})[r["condition"]] = r["step"]
    items = sorted(k for k, v in by.items() if set(v) == set(announced.CONDITIONS))
    matrix = np.array([[by[k][c] for c in announced.CONDITIONS] for k in items])
    rng = np.random.default_rng(seed)
    boots = matrix[rng.integers(0, len(items), size=(BOOTSTRAP, len(items)))].mean(axis=1)

    def interval(values):
        return [float(np.percentile(values, 5)), float(np.percentile(values, 95))]

    index = {c: j for j, c in enumerate(announced.CONDITIONS)}
    means = matrix.mean(axis=0)
    one, three, said, six = (index[c] for c in ("one", "three", "three-said", "six"))

    def restored(m):
        drop = m[..., one] - m[..., three]
        return (m[..., said] - m[..., three]) / np.where(np.abs(drop) > 1e-9, drop, np.nan)

    restored_boot = restored(boots)
    return {
        "cases": len(items),
        "mean_step": {
            c: {"mean": float(means[index[c]]), "interval_90": interval(boots[:, index[c]])}
            for c in announced.CONDITIONS
        },
        "ratio_three_one": float(means[three] / means[one]),
        "ratio_six_one": float(means[six] / means[one]),
        "restored": {
            "mean": float(restored(means)),
            "interval_90": interval(restored_boot[~np.isnan(restored_boot)]),
        },
    }


def by_slot(rows):
    """Mean signed step per kind of change and condition."""
    out = {}
    for r in rows:
        out.setdefault(r["slot"], {}).setdefault(r["condition"], []).append(r["step"])
    return {
        slot: {c: {"mean": float(np.mean(v)), "n": len(v)} for c, v in conditions.items()}
        for slot, conditions in sorted(out.items())
    }


def summary(roots):
    rows = cases(roots)
    return {
        "schema_version": "epistemics.announced-count.v1",
        "configurations": {c: analyse(r) for c, r in sorted(rows.items())},
        "by_slot": by_slot([x for r in rows.values() for x in r]),
        "by_slot_configuration": {c: by_slot(r) for c, r in sorted(rows.items())},
        "scope": "Exploratory: one reported change, the declared number of changes varied; steps "
        "from the stated market prior.",
    }
