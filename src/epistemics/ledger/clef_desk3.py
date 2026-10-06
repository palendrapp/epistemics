"""The confirmation desk: the preregistered test (docs/clef-desk3-preregistration.md).

Primary, per model (Clef, Clef-flash), on the held-out test meetings:
  H1  passport lane > generic recalibration fitted on PRIMARY_K meetings of the model's own
      forecast record (P&L per meeting averaged over DRAWS random draws from the pool)
  H2  passport lane > the model alone
Each by the mean paired per-meeting P&L difference, one-sided p from a sign-flip permutation
test (PERMUTATIONS, fixed seed), Holm across the four tests, pass if Holm p < 0.05.

Secondary: recalibration at every k, the gated lane, the oracle gap, classification by
strength, positions taken with nothing heard. Thresholds for every lane except alone use the
optimal policy for the committee's mean estimated record (from the domain scorecard).

Elicited outputs of a trained head, not direct access to beliefs.
"""

import numpy as np

from epistemics.clef import desk, desk2, desk3, pilot
from epistemics.clef.answers import parse
from epistemics.clef.client import ClefError

CLIP = 0.0005
PERMUTATIONS = 100000
SEED = 20261014
ALPHA = 0.05


def _z(p):
    p = float(np.clip(p, CLIP, 1 - CLIP))
    return float(np.log(p / (1 - p)))


def load(root):
    document, _ = pilot.load(root)
    if document.get("design") != "desk3":
        raise ClefError(f"{root} is not a confirmation-desk root")
    if document["items"]["desk3"] != desk3.items_digest():
        raise ClefError("The confirmation-desk meetings have changed since the plan was frozen")
    records = pilot.answered(root)
    values = {c["id"]: parse(records[c["id"]]["response"], c["questions"])
              for c in document["calls"] if c["id"] in records}  # fmt: skip
    return document, values


def logistic(X, y, iters=50, ridge=1e-3):
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X @ w)))
        g = X.T @ (p - y) + ridge * w
        H = X.T @ (X * (p * (1 - p))[:, None]) + ridge * np.eye(len(w))
        w -= np.linalg.solve(H, g)
    return w


def sign_flip_p(d, permutations=PERMUTATIONS, seed=SEED):
    """One-sided p that the mean paired difference exceeds 0 (sign-flip permutation)."""
    d = np.asarray(d, dtype=float)
    observed = d.mean()
    rng = np.random.default_rng(seed)
    count, done = 0, 0
    while done < permutations:
        n = min(10000, permutations - done)
        signs = rng.choice((-1.0, 1.0), size=(n, len(d)))
        count += int(np.sum((signs @ d) / len(d) >= observed - 1e-12))
        done += n
    return (count + 1) / (permutations + 1)


def holm(ps):
    order = sorted(ps, key=ps.get)
    out, running = {}, 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, (len(order) - i) * ps[k]))
        out[k] = running
    return out


def _pnl(m, action, t):
    right = (action == "rise") == m["rise"]
    return (desk2.WIN if right else -desk2.WIN) - desk2.COST * t


def _play(m, logodds_at, tables):
    for t in range(desk3.PER_MEETING + 1):
        action = desk.act(t, logodds_at(t), tables)
        if action != "wait":
            return _pnl(m, action, t), t
    raise AssertionError("the policy always decides at the last speaker")


def _alone(m, choice_at):
    last = desk3.PER_MEETING
    for t in range(last + 1):
        c = choice_at(t)
        action = {"a": "rise", "b": "hold", "draw": "wait"}[max(c, key=c.get)]
        if action == "wait" and t == last:
            action = "rise" if c["a"] >= c["b"] else "hold"
        if action != "wait":
            return _pnl(m, action, t), t


def _summary(x):
    x = np.asarray(x, dtype=float)
    return {"mean": float(x.mean()), "se": float(x.std(ddof=1) / np.sqrt(len(x)))}


def summary(root, k_values=None, draws=None):
    document, values = load(root)
    k_values = k_values or desk3.K_VALUES
    draws = draws or desk3.DRAWS
    card = desk3.scorecard()
    est = desk2.estimated_reliability(card)
    qbar = float(np.mean(list(est.values())))
    tables = desk._value_tables(q=qbar, max_speakers=desk3.PER_MEETING)
    pool, test = desk3.meetings("pool"), desk3.meetings("test")
    uniq = desk2.unique_remarks(test)
    out, ps = {}, {}
    for model in document["models"]:

        def belief(kind, m, t, model=model):
            part = "pool-belief" if kind == "pool" else "belief"
            return _z(values[f"{model}/{part}/{m['meeting']}/{t}"]["answer"])

        def hawk(m, k, model=model):
            r = m["remarks"][k]
            return values[f"{model}/classify/{uniq[(r['speaker'], r['text'])]}"]["answer"]

        lanes, heard = {}, {}
        rows = [_play(m, lambda t, m=m: desk2.logit(m["price"]) + sum(
            (2 * hawk(m, k) - 1) * desk2.logit(est[m["remarks"][k]["index"]]) for k in range(t)), tables)
            for m in test]  # fmt: skip
        lanes["passport"], heard["passport"] = [r[0] for r in rows], [r[1] for r in rows]
        rows = [
            _alone(
                m,
                lambda t, m=m, model=model: values[f"{model}/choice/{m['meeting']}/{t}"][
                    "decision"
                ],
            )
            for m in test
        ]
        lanes["alone"], heard["alone"] = [r[0] for r in rows], [r[1] for r in rows]
        rows = [_play(m, lambda t, m=m: belief("test", m, t), tables) for m in test]
        lanes["gated"], heard["gated"] = [r[0] for r in rows], [r[1] for r in rows]
        rows = [_play(m, lambda t, m=m: desk2.oracle_logodds(m, t), tables) for m in test]
        lanes["oracle"], heard["oracle"] = [r[0] for r in rows], [r[1] for r in rows]
        rng = np.random.default_rng(desk3.DRAW_SEED)
        for k in k_values:
            per_draw = []
            subsets = [np.arange(len(pool))] if k >= len(pool) else [
                rng.choice(len(pool), k, replace=False) for _ in range(draws)]  # fmt: skip
            for idx in subsets:
                X = np.array([[1.0, belief("pool", pool[i], t), desk2.logit(pool[i]["price"])]
                              for i in idx for t in range(desk3.PER_MEETING + 1)])  # fmt: skip
                y = np.array(
                    [float(pool[i]["rise"]) for i in idx for t in range(desk3.PER_MEETING + 1)]
                )
                w = logistic(X, y)
                per_draw.append([_play(m, lambda t, m=m, w=w: float(
                    w @ [1.0, belief("test", m, t), desk2.logit(m["price"])]), tables)[0] for m in test])  # fmt: skip
            lanes[f"recalibrated_{k}"] = list(np.mean(per_draw, axis=0))
        d1 = np.array(lanes["passport"]) - np.array(lanes[f"recalibrated_{desk3.PRIMARY_K}"])
        d2 = np.array(lanes["passport"]) - np.array(lanes["alone"])
        tests = {"H1": d1, "H2": d2}
        primary = {}
        for h, d in tests.items():
            p = sign_flip_p(d)
            ps[f"{model}/{h}"] = p
            primary[h] = {"difference": _summary(d), "p_one_sided": p}
        classification = {}
        for strength, _ in desk2.STRENGTH:
            items = [(hawk(m, k), r["sign"]) for m in test for k, r in enumerate(m["remarks"])
                     if r["strength"] == strength]  # fmt: skip
            classification[strength] = float(np.mean([(p > 0.5) == (s > 0) for p, s in items]))
        out[model] = {
            "primary": primary,
            "lanes": {k: _summary(v) for k, v in lanes.items()},
            "nothing_heard": {k: float(np.mean([t == 0 for t in v])) for k, v in heard.items()},
            "speakers_heard": {k: float(np.mean(v)) for k, v in heard.items()},
            "classification_accuracy": classification,
            "oracle_minus_passport": _summary(
                np.array(lanes["oracle"]) - np.array(lanes["passport"])
            ),
        }
    adjusted = holm(ps)
    for key, p in adjusted.items():
        model, h = key.split("/")
        out[model]["primary"][h]["p_holm"] = p
        out[model]["primary"][h]["pass"] = bool(
            p < ALPHA and out[model]["primary"][h]["difference"]["mean"] > 0
        )
    return {
        "schema_version": "epistemics.clef-desk3.v1",
        "version": document["version"],
        "plan_digest": document["plan_digest"],
        "meetings": {k: len(desk3.meetings(k)) for k in desk3.SEEDS},
        "test_rises": int(sum(m["rise"] for m in test)),
        "mean_estimated_record": qbar,
        "primary_k": desk3.PRIMARY_K, "draws": draws, "k_values": list(k_values),
        "models": out,
        "scope": (
            "Preregistered (docs/clef-desk3-preregistration.md). P&L per held-out meeting: +100 or "
            "-100, minus 5 per speaker waited. Passport and every threshold use only the domain "
            "scorecard; recalibration also uses k meetings of the model's own forecasts. One-sided "
            "sign-flip permutation p, Holm over four tests. Elicited outputs of a trained head, "
            "not direct access to beliefs."
        ),
    }  # fmt: skip
