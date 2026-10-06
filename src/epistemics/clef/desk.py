"""The simulated central-bank desk (docs/clef-desk-demo.md): episodes with a known outcome, for
scoring mitigations of the traits the battery found (sample-size neglect, jumping to
conclusions).

Each episode: a market price p for a rate rise; the outcome drawn from p (so the price is
calibrated); up to MAX_SPEAKERS fictional committee members, each remark pointing to the outcome
with probability Q (stated to the model as a track record). After each prefix of remarks the
model is asked to act (take a position on a rise or a hold, or wait for the next speaker, with
the beads payoffs) and, separately, for its belief; each remark is also classified on its own
(hawkish or not). Lanes are simulated from these answers:

  alone     the model's own act-or-wait choice
  gated     the model's stated belief, acted on at the optimal threshold
  passport  the model classifies each remark; the evidence is added in code at the stated record
            and acted on at the optimal threshold (the mitigation for both traits)
  bayes     the exact posterior at the optimal threshold (reference)
"""

import numpy as np

from epistemics.clef.requests import MODELS, digest

VERSION = "clef-desk/0.1.0"
Q = 0.7
MAX_SPEAKERS = 6
WIN, COST = 100, 5
PRICES = (0.35, 0.5, 0.65)
EPISODES = 60
SEED = 20261007
SPEAKERS = (
    "Governor Hale", "Deputy Governor Okafor", "Governor Lindqvist", "Governor Marchetti",
    "Governor Adeyemi", "Governor Castellanos", "Governor Brandt", "Governor Whitlock",
    "Governor Ishida", "Governor Novak",
)  # fmt: skip
HAWKISH = (
    "Inflation is still running too hot for comfort, and I see a case for tightening further at "
    "our next meeting.",
    "The labour market remains very tight; another increase at the coming meeting would be prudent.",
    "I would support moving rates up again when we meet.",
    "We haven't finished the job on inflation, and I expect we'll need to raise rates at the "
    "coming meeting.",
    "Recent price data argue for one more increase, and soon.",
    "Underlying inflation is proving sticky; I'd lean towards a further rise next time.",
    "Holding steady now would risk falling behind; I favour an increase at the meeting.",
    "Wage growth is still too strong. Another rise is warranted when we meet.",
)
DOVISH = (
    "Policy is already restrictive enough; I'd prefer to hold steady at the next meeting.",
    "I see value in pausing at the coming meeting to assess the effects of past increases.",
    "There's no urgency to move again; holding rates is the right call for now.",
    "Inflation is cooling, and I'd keep rates where they are when we meet.",
    "I'd be comfortable leaving policy unchanged at the coming meeting.",
    "Demand is softening; I see no need for a further increase next time.",
    "The risks are now balanced. I'd hold at the coming meeting and watch the data.",
    "Past increases are still working through. Patience is the right course at our next meeting.",
)


def logit(p):
    return float(np.log(p / (1 - p)))


LQ = logit(Q)


def episodes(n=EPISODES, seed=SEED):
    rng = np.random.default_rng(seed)
    out = []
    for e in range(n):
        p = PRICES[e % len(PRICES)]
        rise = bool(rng.random() < p)
        remarks = []
        for k in range(MAX_SPEAKERS):
            sign = (1 if rise else -1) * (1 if rng.random() < Q else -1)
            pool = HAWKISH if sign > 0 else DOVISH
            remarks.append({"speaker": SPEAKERS[(e + k) % len(SPEAKERS)], "sign": sign,
                            "text": pool[int(rng.integers(len(pool)))]})  # fmt: skip
        out.append({"episode": e, "price": p, "rise": rise, "remarks": remarks})
    return out


def unique_remarks(eps):
    seen = {}
    for ep in eps:
        for r in ep["remarks"]:
            seen.setdefault((r["speaker"], r["text"]), len(seen))
    return seen


def bayes_logodds(ep, t):
    return logit(ep["price"]) + LQ * sum(r["sign"] for r in ep["remarks"][:t])


def items_digest():
    return digest({"episodes": episodes(), "q": Q, "max": MAX_SPEAKERS, "payoffs": [WIN, COST]})


# ---------- Optimal stopping on a log-odds grid ----------

GRID = np.round(np.arange(-12, 12.0001, 0.01), 2)


def _value_tables(q=Q, win=WIN, cost=COST, max_speakers=MAX_SPEAKERS):
    """Per number of speakers heard t: (decide-now value, continue value) on GRID."""
    lq = logit(q)
    pa = 1 / (1 + np.exp(-GRID))
    decide = win * (2 * np.maximum(pa, 1 - pa) - 1)
    tables = {max_speakers: (decide, np.full_like(decide, -np.inf))}
    value = decide
    for t in range(max_speakers - 1, -1, -1):
        p_next_hawk = pa * q + (1 - pa) * (1 - q)
        up = np.interp(GRID + lq, GRID, value)
        down = np.interp(GRID - lq, GRID, value)
        cont = -cost + p_next_hawk * up + (1 - p_next_hawk) * down
        tables[t] = (decide, cont)
        value = np.maximum(decide, cont)
    return tables


TABLES = _value_tables()


def act(t, logodds):
    """The optimal action with `t` speakers heard and posterior log-odds `logodds`: 'rise',
    'hold' or 'wait'."""
    decide, cont = TABLES[t]
    i = int(np.clip(np.searchsorted(GRID, logodds), 0, len(GRID) - 1))
    if decide[i] >= cont[i]:
        return "rise" if logodds > 0 else "hold" if logodds < 0 else "rise"
    return "wait"


# ---------- Text ----------

RECORD = (
    f"Committee members' remarks before a meeting have matched the decision {round(Q * 100)}% of "
    "the time, each independently of the others."
)
OPTIONS = {"a": "Take a position on a rate rise now", "b": "Take a position on a hold now",
           "draw": "Wait for the next committee member to speak"}  # fmt: skip


def state_text(ep, t):
    heard = ep["remarks"][:t]
    lines = (
        "\n".join(f'- {r["speaker"]}: "{r["text"]}"' for r in heard) or "(no one has spoken yet)"
    )
    return (
        f"Markets price a {round(ep['price'] * 100)}% chance that the central bank raises rates "
        f"at next week's meeting. {RECORD} Committee members are speaking one at a time before "
        f"the meeting. Remarks so far:\n{lines}\nYou can take a position on the decision now, or "
        f"wait for the next speaker. A correct position earns ${WIN}k and a wrong one loses "
        f"${WIN}k; waiting for each further speaker costs ${COST}k in worse prices. At most "
        f"{MAX_SPEAKERS} members will speak."
    )


def choice_question():
    return {"decision": {"type": "choice", "instructions": "What should the desk do now?",
                         "criteria": dict(OPTIONS)}}  # fmt: skip


def belief_question():
    return {"answer": {"type": "noul",
                       "instructions": "Is it true that the central bank will raise rates at next week's meeting?"}}  # fmt: skip


def classify_text(speaker, text):
    state = f'{speaker}, a member of the central bank\'s rate-setting committee, said: "{text}"'
    question = {"answer": {"type": "noul",
                           "instructions": "Is this remark signalling a rate rise at the next meeting?"}}  # fmt: skip
    return state, question


def calls(models=tuple(MODELS)):
    eps = episodes()
    uniq = unique_remarks(eps)
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
        for ep in eps:
            for t in range(MAX_SPEAKERS + 1):
                key = f"{ep['episode']}/{t}"
                add(model, "choice", key, state_text(ep, t), choice_question())
                add(model, "belief", key, state_text(ep, t), belief_question())
        for (speaker, text), i in uniq.items():
            add(model, "classify", str(i), *classify_text(speaker, text))
    return out
