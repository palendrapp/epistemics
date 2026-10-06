"""The robustness desk (docs/clef-desk-demo.md, "Robustness test"): the passport mitigation when
the world departs from its assumptions and its parameters must be learned.

Departures from the first desk (epistemics.clef.desk):
  - ten speakers with different true reliabilities (0.55 to 0.85), never stated;
  - two speakers usually echo the previous speaker (with probability ECHO they repeat the last
    direction heard, whatever the truth); nobody is told, and the passport lane assumes
    independence;
  - remarks come strong, mild or mixed, so classifying them is not trivial;
  - every lane sees the same scorecard from HISTORY past meetings ("Governor Hale: 17 of 23"),
    from which the passport lane estimates each speaker's weight; scoring is on held-out
    meetings.

Lanes (ledger/clef_desk2.py): alone (the model's choice), gated (its belief at the threshold),
recalibrated (its belief recalibrated on the past meetings' outcomes: a generic fix with no
passport), passport (classify each remark, weight by the speaker's estimated record, add in code,
threshold), passport_flat (the same with one pooled weight), oracle (the exact posterior under
the true reliabilities and echoes).
"""

import numpy as np

from epistemics.clef import desk
from epistemics.clef.requests import MODELS, digest

VERSION = "clef-desk2/0.1.0"
SPEAKERS = desk.SPEAKERS
RELIABILITY = (0.85, 0.80, 0.75, 0.72, 0.70, 0.68, 0.62, 0.58, 0.60, 0.60)
ECHOERS = (8, 9)  # Governor Ishida, Governor Novak
ECHO = 0.8
PER_MEETING = 6
HISTORY, TEST = 40, 60
SEEDS = {"history": 20261008, "test": 20261009}
STRENGTH = (("strong", 0.45), ("mild", 0.40), ("mixed", 0.15))
WIN, COST = desk.WIN, desk.COST

POOLS = {
    (1, "strong"): desk.HAWKISH,
    (1, "mild"): (
        "I could see a case for a modest further increase, depending on the next data.",
        "I'm open to another small rise if inflation doesn't ease soon.",
        "On balance I'd lean towards nudging rates up once more.",
        "There's an argument for a bit more tightening, though I'm not wedded to it.",
        "A further small increase would not be unreasonable at this stage.",
        "I'd be inclined to support a small increase, but it's a close call.",
    ),
    (1, "mixed"): (
        "The data are mixed; growth is cooling, but I'm still slightly more worried about inflation.",
        "It's finely balanced. If I had to choose today, I'd tilt towards tightening.",
        "Risks run both ways, though the inflation side weighs a little more for me.",
        "I can see arguments for holding, but on net I lean very slightly towards a rise.",
    ),
    (-1, "strong"): desk.DOVISH,
    (-1, "mild"): (
        "I'd be inclined to wait a little before doing anything more.",
        "My preference, narrowly, is to leave rates unchanged this time.",
        "I don't see a pressing need for another increase at the moment.",
        "On balance I'd hold, though I'm watching inflation closely.",
        "A pause seems sensible to me, but I'm not ruling anything out.",
        "I lean towards keeping policy steady at the coming meeting.",
    ),
    (-1, "mixed"): (
        "The data are mixed; inflation is sticky, but I'm slightly more worried about growth.",
        "It's finely balanced. If I had to choose today, I'd tilt towards holding.",
        "Risks run both ways, though the growth side weighs a little more for me.",
        "I can see arguments for a rise, but on net I lean very slightly towards holding.",
    ),
}


def logit(p):
    return float(np.log(p / (1 - p)))


def meetings(kind):
    rng = np.random.default_rng(SEEDS[kind])
    n = HISTORY if kind == "history" else TEST
    out = []
    for e in range(n):
        p = desk.PRICES[e % len(desk.PRICES)]
        rise = bool(rng.random() < p)
        truth = 1 if rise else -1
        order = rng.permutation(len(SPEAKERS))[:PER_MEETING]
        remarks, last = [], None
        for j in (int(x) for x in order):
            if j in ECHOERS and last is not None and rng.random() < ECHO:
                sign, echoed = last, True
            else:
                sign = truth if rng.random() < RELIABILITY[j] else -truth
                echoed = False
            u, acc, strength = rng.random(), 0.0, "strong"
            for name, prob in STRENGTH:
                acc += prob
                if u < acc:
                    strength = name
                    break
            pool = POOLS[(sign, strength)]
            remarks.append({"speaker": SPEAKERS[j], "index": j, "sign": sign, "strength": strength,
                            "echoed": echoed, "text": pool[int(rng.integers(len(pool)))]})  # fmt: skip
            last = sign
        out.append({"meeting": e, "kind": kind, "price": p, "rise": rise, "remarks": remarks})
    return out


def scorecard(history=None):
    """{speaker index: (matches, appearances)} over the past meetings."""
    history = history or meetings("history")
    card = {j: [0, 0] for j in range(len(SPEAKERS))}
    for m in history:
        truth = 1 if m["rise"] else -1
        for r in m["remarks"]:
            card[r["index"]][1] += 1
            card[r["index"]][0] += int(r["sign"] == truth)
    return {j: tuple(v) for j, v in card.items()}


def estimated_reliability(card):
    """Laplace-smoothed hit rate per speaker."""
    return {j: (m + 1) / (n + 2) for j, (m, n) in card.items()}


def items_digest():
    return digest({"history": meetings("history"), "test": meetings("test"),
                   "reliability": RELIABILITY, "echoers": ECHOERS, "echo": ECHO})  # fmt: skip


def oracle_logodds(m, t):
    """Exact posterior log-odds of a rise after t remarks, under the true reliabilities and echo."""
    ll = {1: 0.0, -1: 0.0}
    for truth in (1, -1):
        last = None
        for r in m["remarks"][:t]:
            q = RELIABILITY[r["index"]]
            independent = q if r["sign"] == truth else 1 - q
            if r["index"] in ECHOERS and last is not None:
                prob = ECHO * (r["sign"] == last) + (1 - ECHO) * independent
            else:
                prob = independent
            ll[truth] += np.log(prob)
            last = r["sign"]
    return logit(m["price"]) + ll[1] - ll[-1]


def card_text(card):
    lines = [f"{SPEAKERS[j]} {m} of {n}" for j, (m, n) in sorted(card.items())]
    return "; ".join(lines)


def state_text(m, t, card):
    heard = m["remarks"][:t]
    lines = (
        "\n".join(f'- {r["speaker"]}: "{r["text"]}"' for r in heard) or "(no one has spoken yet)"
    )
    return (
        f"Markets price a {round(m['price'] * 100)}% chance that the central bank raises rates at "
        "next week's meeting. Committee members' records before past meetings (pre-meeting "
        f"signals that matched the decision): {card_text(card)}. Committee members are speaking "
        f"one at a time before the meeting. Remarks so far:\n{lines}\nYou can take a position on "
        f"the decision now, or wait for the next speaker. A correct position earns ${WIN}k and a "
        f"wrong one loses ${WIN}k; waiting for each further speaker costs ${COST}k in worse "
        f"prices. At most {PER_MEETING} members will speak."
    )


def unique_remarks(test):
    seen = {}
    for m in test:
        for r in m["remarks"]:
            seen.setdefault((r["speaker"], r["text"]), len(seen))
    return seen


def calls(models=tuple(MODELS)):
    history, test = meetings("history"), meetings("test")
    card = scorecard(history)
    uniq = unique_remarks(test)
    out = []

    def add(model, part, key, state, questions):
        kinds = {
            k: ("options" if q["type"] == "choice" else q["type"]) for k, q in questions.items()
        }
        meta = {"model": model, "part": part, "key": key, "questions": kinds}
        out.append(
            (
                f"{model}/{part}/{key}",
                meta,
                {"model": model, "state": state, "questions": questions},
            )
        )

    for model in models:
        for m in history:
            for t in range(PER_MEETING + 1):
                add(
                    model,
                    "history-belief",
                    f"{m['meeting']}/{t}",
                    state_text(m, t, card),
                    desk.belief_question(),
                )
        for m in test:
            for t in range(PER_MEETING + 1):
                key = f"{m['meeting']}/{t}"
                add(model, "choice", key, state_text(m, t, card), desk.choice_question())
                add(model, "belief", key, state_text(m, t, card), desk.belief_question())
        for (speaker, text), i in uniq.items():
            add(model, "classify", str(i), *desk.classify_text(speaker, text))
    return out
