"""The second confirmation desk: the preregistered test (docs/clef-desk4-preregistration.md).

Primary, per model (Clef, Clef-flash), on the 1,000 held-out test meetings:
  H1  calibrated passport lane > the model alone
  H2  calibrated passport lane > generic recalibration on PRIMARY_K own-forecast meetings
      (per-meeting P&L averaged over DRAWS random draws from the pool)
The calibrated passport lane: the model classifies each remark; its classifier's log-odds are
mapped to the probability of a hawkish remark by a logistic regression fitted on the record
meetings' labelled remarks; evidence (2 * calibrated P - 1) * logit(estimated record) is added to
the price log-odds and acted on at the optimal threshold. Mean paired per-meeting difference,
one-sided sign-flip permutation p (100,000, fixed seed), Holm across the four tests, pass if Holm
p < 0.05 and the mean difference is positive.

Secondary: the uncalibrated passport lane, recalibration at every k, the gated lane, the oracle
gap, positions with nothing heard, classification accuracy raw and calibrated by strength.

Elicited outputs of a trained head, not direct access to beliefs.
"""

import numpy as np

from epistemics.clef import desk, desk2, desk4, pilot
from epistemics.clef.answers import parse
from epistemics.clef.client import ClefError
from epistemics.ledger.clef_desk3 import _alone, _play, _summary, _z, holm, logistic, sign_flip_p

ALPHA = 0.05
SEED = 20261024


def load(root):
    document, _ = pilot.load(root)
    if document.get("design") != "desk4":
        raise ClefError(f"{root} is not a second-confirmation root")
    if document["items"]["desk4"] != desk4.items_digest():
        raise ClefError("The second-confirmation meetings have changed since the plan was frozen")
    records = pilot.answered(root)
    values = {c["id"]: parse(records[c["id"]]["response"], c["questions"])
              for c in document["calls"] if c["id"] in records}  # fmt: skip
    return document, values


def summary(root, k_values=None, draws=None, permutations=100000):
    document, values = load(root)
    k_values = k_values or desk4.K_VALUES
    draws = draws or desk4.DRAWS
    card = desk4.scorecard()
    est = desk2.estimated_reliability(card)
    qbar = float(np.mean(list(est.values())))
    tables = desk._value_tables(q=qbar, max_speakers=desk4.PER_MEETING)
    pool, test = desk4.meetings("pool"), desk4.meetings("test")
    uniq = desk2.unique_remarks(test)
    labelled = desk4.record_remarks()
    out, ps = {}, {}
    for model in document["models"]:
        rz = np.array(
            [_z(values[f"{model}/record-classify/{i}"]["answer"]) for i in range(len(labelled))]
        )
        ry = np.array([float(sign > 0) for _, sign in labelled])
        cal = logistic(np.c_[np.ones(len(rz)), rz], ry)

        def raw(m, model=model):
            return [
                values[f"{model}/classify/{uniq[(r['speaker'], r['text'])]}"]["answer"]
                for r in m["remarks"]
            ]

        def calibrated(m, cal=cal, raw=raw):
            return [1 / (1 + np.exp(-(cal[0] + cal[1] * _z(p)))) for p in raw(m)]

        def passport(m, probs):
            ev = [2 * p - 1 for p in probs]

            def logodds(n_said, m=m, ev=ev):
                return desk2.logit(m["price"]) + sum(
                    ev[k] * desk2.logit(est[m["remarks"][k]["index"]]) for k in range(n_said)
                )

            return _play(m, logodds, tables)

        def belief(part, m, t, model=model):
            return _z(values[f"{model}/{part}/{m['meeting']}/{t}"]["answer"])

        lanes, heard = {}, {}
        for name, rows in (
            ("passport_calibrated", [passport(m, calibrated(m)) for m in test]),
            ("passport_raw", [passport(m, raw(m)) for m in test]),
            ("alone", [_alone(m, lambda t, m=m, model=model: values[f"{model}/choice/{m['meeting']}/{t}"]["decision"])
                       for m in test]),
            ("gated", [_play(m, lambda t, m=m: belief("belief", m, t), tables) for m in test]),
            ("oracle", [_play(m, lambda t, m=m: desk2.oracle_logodds(m, t), tables) for m in test]),
        ):  # fmt: skip
            lanes[name], heard[name] = [r[0] for r in rows], [r[1] for r in rows]
        rng = np.random.default_rng(desk4.DRAW_SEED)
        for k in k_values:
            subsets = [np.arange(len(pool))] if k >= len(pool) else [
                rng.choice(len(pool), k, replace=False) for _ in range(draws)]  # fmt: skip
            per_draw = []
            for idx in subsets:
                X = np.array([[1.0, belief("pool-belief", pool[i], t), desk2.logit(pool[i]["price"])]
                              for i in idx for t in range(desk4.PER_MEETING + 1)])  # fmt: skip
                y = np.array(
                    [float(pool[i]["rise"]) for i in idx for t in range(desk4.PER_MEETING + 1)]
                )
                w = logistic(X, y)
                per_draw.append([_play(m, lambda t, m=m, w=w: float(
                    w @ [1.0, belief("belief", m, t), desk2.logit(m["price"])]), tables)[0] for m in test])  # fmt: skip
            lanes[f"recalibrated_{k}"] = list(np.mean(per_draw, axis=0))
        passport_pnl = np.array(lanes["passport_calibrated"])
        primary = {}
        for h, comparator in (("H1", "alone"), ("H2", f"recalibrated_{desk4.PRIMARY_K}")):
            d = passport_pnl - np.array(lanes[comparator])
            p = sign_flip_p(d, permutations=permutations, seed=SEED)
            ps[f"{model}/{h}"] = p
            primary[h] = {"comparator": comparator, "difference": _summary(d), "p_one_sided": p}
        accuracy = {}
        for strength, _ in desk2.STRENGTH:
            pairs = [(rp, cp, r["sign"]) for m in test for rp, cp, r in zip(raw(m), calibrated(m), m["remarks"], strict=True)
                     if r["strength"] == strength]  # fmt: skip
            accuracy[strength] = {"raw": float(np.mean([(a > 0.5) == (s > 0) for a, _, s in pairs])),
                                  "calibrated": float(np.mean([(c > 0.5) == (s > 0) for _, c, s in pairs]))}  # fmt: skip
        out[model] = {
            "primary": primary,
            "lanes": {k: _summary(v) for k, v in lanes.items()},
            "nothing_heard": {k: float(np.mean([t == 0 for t in v])) for k, v in heard.items()},
            "speakers_heard": {k: float(np.mean(v)) for k, v in heard.items()},
            "classification_accuracy": accuracy,
            "calibration": {
                "intercept": float(cal[0]),
                "slope": float(cal[1]),
                "labelled_remarks": len(labelled),
            },
            "calibrated_minus_raw_passport": _summary(
                passport_pnl - np.array(lanes["passport_raw"])
            ),
            "oracle_minus_passport": _summary(np.array(lanes["oracle"]) - passport_pnl),
        }
    for key, p in holm(ps).items():
        model, h = key.split("/")
        out[model]["primary"][h]["p_holm"] = p
        out[model]["primary"][h]["pass"] = bool(
            p < ALPHA and out[model]["primary"][h]["difference"]["mean"] > 0
        )
    return {
        "schema_version": "epistemics.clef-desk4.v1",
        "version": document["version"],
        "plan_digest": document["plan_digest"],
        "meetings": {k: len(desk4.meetings(k)) for k in desk4.SEEDS},
        "test_rises": int(sum(m["rise"] for m in test)),
        "mean_estimated_record": qbar,
        "models": out,
        "scope": (
            "Preregistered (docs/clef-desk4-preregistration.md), the second confirmation after "
            "desk3's H2 failed. P&L per held-out meeting: +100 or -100, minus 5 per speaker "
            "waited. One-sided sign-flip permutation p, Holm over four tests. Elicited outputs of "
            "a trained head, not direct access to beliefs."
        ),
    }
