"""Clef cognitive battery (docs/clef-battery-design.md): classic decision-making tasks on urns,
each mirrored on a central-bank desk, so that a parameter fitted on the urns can be tested on
the desk.

  bookbag  two urns, a stated prior and a sample drawn with replacement (Phillips & Edwards 1966;
           Grether 1980). Fitted: prior weight alpha, evidence weight beta, bias, confirmation
           asymmetry, evidence weight by sample size. Desk: a market-implied probability of a rate
           rise and policymakers' signals with a stated hit rate.
  beads    beads drawn one at a time: decide now or draw again, with a payoff and a cost per draw
           (Huq, Garety & Hemsley 1988). Fitted: the evidence threshold at which deciding
           overtakes drawing (jumping to conclusions), and its slope. Desk: take a position on
           the decision now or wait for the next speaker.
  tone     one report worded hedged, plain or confident, with or without a stated track record.
           Fitted: the weight given to each wording. Desk: a policymaker's remark.

Every item is written in three phrasings; the analysis averages over them. Central-bank
officials are fictional, and the language is generic (no real institution, date or person).
"""

import itertools

import numpy as np

from epistemics.clef.requests import MODELS, digest

VERSION = "clef-battery/0.1.0"
DOMAINS = ("urn", "desk")
PHRASINGS = (0, 1, 2)

# Bookbag: prior x hit rate x sample (n draws, r for urn A / a rise).
PRIORS = (0.1, 0.25, 0.5, 0.75, 0.9)
ACCURACIES = (0.6, 0.7)
SAMPLES = ((1, 1), (1, 0), (3, 3), (3, 2), (3, 1), (3, 0),
           (5, 5), (5, 4), (5, 3), (5, 2), (5, 1), (5, 0))  # fmt: skip

# Beads: two ratios, eight five-draw patterns (four favouring A and their mirror images), every
# prefix. Payoffs: a correct decision +100, a wrong one -100, each further draw -5, at most 10.
RATIOS = (0.85, 0.6)
PATTERNS = ("+++++", "++-++", "+-++-", "-+-++")
WIN, COST, MAX_DRAWS = 100, 5, 10

# Tone: prior x wording x direction x record (none, or 70%).
TONE_PRIORS = (0.3, 0.5, 0.7)
WORDINGS = ("hedged", "plain", "confident")
RECORDS = (None, 0.7)
OFFICIALS = ("Governor Hale", "Deputy Governor Okafor", "Governor Lindqvist")


def logit(p):
    return float(np.log(p / (1 - p)))


def pct(p):
    return f"{round(p * 100)}%"


def _count(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


# ---------- Items ----------


def bookbag_items():
    out = []
    for p, q, (n, r) in itertools.product(PRIORS, ACCURACIES, SAMPLES):
        out.append({"prior": p, "accuracy": q, "n": n, "r": r, "prior_logodds": logit(p),
                    "llr": (2 * r - n) * logit(q)})  # fmt: skip
    return out


def bead_sequences():
    """Every distinct prefix (including the empty one) of the patterns and their mirrors."""
    seqs = {""}
    for pattern in PATTERNS:
        for s in (pattern, pattern.translate(str.maketrans("+-", "-+"))):
            seqs.update(s[:k] for k in range(1, len(s) + 1))
    return sorted(seqs, key=lambda s: (len(s), s))


def beads_items():
    out = []
    for q in RATIOS:
        for seq in bead_sequences():
            k = seq.count("+") - seq.count("-")
            out.append({"ratio": q, "sequence": seq, "draws": len(seq),
                        "posterior_logodds": k * logit(q)})  # fmt: skip
    return out


def tone_items():
    out = []
    for p, w, d, rec in itertools.product(TONE_PRIORS, WORDINGS, (1, -1), RECORDS):
        out.append({"prior": p, "wording": w, "direction": d, "record": rec,
                    "prior_logodds": logit(p),
                    "record_llr": None if rec is None else d * logit(rec)})  # fmt: skip
    return out


ITEMS = {"bookbag": bookbag_items, "beads": beads_items, "tone": tone_items}


def items_digest():
    return digest({task: f() for task, f in ITEMS.items()})


# ---------- Optimal stopping for the beads payoffs ----------


def optimal_policy(q, win=WIN, cost=COST, max_draws=MAX_DRAWS):
    """{(draws so far, net count): (decide?, value)} by backward induction from equal priors."""
    lq = logit(q)
    value = {}
    for t in range(max_draws, -1, -1):
        for k in range(-t, t + 1, 2):
            pa = 1 / (1 + np.exp(-k * lq))
            decide = win * (2 * max(pa, 1 - pa) - 1)
            if t == max_draws:
                value[(t, k)] = (True, decide)
                continue
            p_plus = pa * q + (1 - pa) * (1 - q)
            draw = (
                -cost + p_plus * value[(t + 1, k + 1)][1] + (1 - p_plus) * value[(t + 1, k - 1)][1]
            )
            value[(t, k)] = (decide >= draw, max(decide, draw))
    return value


def optimal_threshold(q):
    """The smallest net count at which deciding is optimal, as log-odds: the first state with
    that count (every draw one colour)."""
    policy = optimal_policy(q)
    for k in range(0, MAX_DRAWS + 1):
        if policy[(k, k)][0]:
            return k * logit(q)
    return MAX_DRAWS * logit(q)


# ---------- Text ----------


def _beads_seq(seq, domain):
    if not seq:
        return "no beads have been drawn yet" if domain == "urn" else "no one has spoken yet"
    names = {"urn": ("red", "blue"), "desk": ("rise", "hold")}[domain]
    return ", ".join(names[0] if c == "+" else names[1] for c in seq)


def bookbag_text(item, domain, phrasing):
    p, q, n, r = (item[k] for k in ("prior", "accuracy", "n", "r"))
    if domain == "urn":
        states = [
            f"There are two urns. Urn A holds {pct(q)} red balls and {pct(1 - q)} blue balls; urn "
            f"B holds {pct(1 - q)} red balls and {pct(q)} blue balls. One urn was chosen: the "
            f"probability that it is urn A is {pct(p)}. {_count(n, 'ball')} were drawn from the "
            f"chosen urn, each put back before the next draw: {r} red and {n - r} blue.",
            f"An urn was picked: with probability {pct(p)} it is urn A ({pct(q)} red balls, "
            f"{pct(1 - q)} blue), otherwise urn B ({pct(1 - q)} red, {pct(q)} blue). Sampling "
            f"with replacement gave {_count(n, 'draw')}: {r} red, {n - r} blue.",
            f"Prior probability of urn A: {pct(p)}. Urn A's balls are {pct(q)} red and "
            f"{pct(1 - q)} blue; urn B's are {pct(1 - q)} red and {pct(q)} blue. Result of "
            f"{_count(n, 'draw')} with replacement from the chosen urn: {r} red, {n - r} blue.",
        ]
        questions = [
            "Is it true that the balls were drawn from urn A?",
            "Was urn A picked?",
            "Is it true that the chosen urn is urn A?",
        ]
    else:
        states = [
            f"Markets price a {pct(p)} chance that the central bank raises its policy rate at "
            f"next week's meeting. Before the meeting, {_count(n, 'policymaker')} spoke "
            f"publicly: {r} signalled a rise and {n - r} signalled no change. Each "
            f"policymaker's pre-meeting signal matches the eventual decision {pct(q)} of the "
            "time, independently of the others.",
            f"Futures imply a {pct(p)} probability of a rate rise at the next policy meeting. In "
            f"the run-up, {_count(n, 'member')} of the rate-setting committee gave speeches: {r} "
            f"pointed to a rise, {n - r} to a hold. A member's signal before a meeting has "
            f"called the decision correctly {pct(q)} of the time, and members' signals are "
            "independent.",
            f"Pricing before the speeches: {pct(p)} chance of a hike at the coming meeting. "
            f"Speeches since: {n}; pointing to a hike: {r}; pointing to a hold: {n - r}. Track "
            f"record: each speaker's signal matches the decision {pct(q)} of the time, "
            "independently.",
        ]
        questions = [
            "Is it true that the central bank will raise its policy rate at the meeting?",
            "Will the committee raise rates at the next meeting?",
            "Is it true that the central bank will hike at the coming meeting?",
        ]
    return states[phrasing], {"answer": {"type": "noul", "instructions": questions[phrasing]}}


BEADS_OPTIONS = {
    "urn": {"a": "Decide now: jar A", "b": "Decide now: jar B", "draw": "Draw another bead first"},
    "desk": {
        "a": "Take a position on a rate rise now",
        "b": "Take a position on a hold now",
        "draw": "Wait for the next policymaker to speak",
    },
}


def beads_text(item, domain, phrasing):
    q, seq = item["ratio"], item["sequence"]
    so_far = _beads_seq(seq, domain)
    if domain == "urn":
        states = [
            f"There are two jars of beads. Jar A holds {pct(q)} red and {pct(1 - q)} blue beads; "
            f"jar B holds {pct(1 - q)} red and {pct(q)} blue. One jar was chosen, each equally "
            "likely. Beads are drawn one at a time from the chosen jar and put back. "
            f"Drawn so far: {so_far}. You can decide now which jar it is, or draw another bead "
            f"first. A correct decision wins {WIN} points and a wrong one loses {WIN}; each "
            f"further bead costs {COST} points. At most {MAX_DRAWS} beads can be drawn.",
            f"Jar A: {pct(q)} red beads, {pct(1 - q)} blue. Jar B: {pct(1 - q)} red, {pct(q)} "
            "blue. A fair coin chose one jar, and beads are being drawn from it with replacement. "
            f"Beads so far: {so_far}. Payoff: +{WIN} points for naming the right jar, -{WIN} for "
            f"the wrong one, -{COST} points for each extra bead (up to {MAX_DRAWS} in all).",
            f"Two jars, equally likely to be the one in use: A is {pct(q)} red and {pct(1 - q)} "
            f"blue, B is {pct(1 - q)} red and {pct(q)} blue. Draws with replacement so far: "
            f"{so_far}. Deciding correctly earns {WIN} points and wrongly costs {WIN}; another "
            f"draw costs {COST} points; no more than {MAX_DRAWS} draws are allowed.",
        ]
    else:
        states = [
            "Markets see a rate rise and a hold at the central bank's next meeting as equally "
            "likely. Policymakers speak one at a time before the meeting; each one's signal "
            f"matches the eventual decision {pct(q)} of the time, independently. Signals so far: "
            f"{so_far}. You can take a position on the decision now, or wait for the next speaker. "
            f"A correct position earns ${WIN}k and a wrong one loses ${WIN}k; waiting for each "
            f"further speaker costs ${COST}k in worse prices. At most {MAX_DRAWS} policymakers "
            "will speak.",
            "Rise or hold at the next policy meeting: priced at even odds. Committee members are "
            f"speaking in turn, and a member's signal calls the decision correctly {pct(q)} of "
            f"the time, independently of the others. Signals heard: {so_far}. A right position "
            f"pays ${WIN}k, a wrong one costs ${WIN}k, and each further speech you wait for costs "
            f"${COST}k (up to {MAX_DRAWS} speeches in all).",
            "A rate rise and a hold are equally likely at the coming meeting. Speakers before the "
            f"meeting signal the right outcome {pct(q)} of the time, each independently. So far: "
            f"{so_far}. Being right earns ${WIN}k and being wrong loses ${WIN}k; waiting for "
            f"another speaker costs ${COST}k; no more than {MAX_DRAWS} will speak.",
        ]
    instructions = {"urn": "What should be done now?", "desk": "What should the desk do now?"}
    decision = {"type": "choice", "instructions": instructions[domain],
                "criteria": dict(BEADS_OPTIONS[domain])}  # fmt: skip
    return states[phrasing], {"decision": decision}


def beads_belief(item, domain):
    """The belief question on the first phrasing's state."""
    state, _ = beads_text(item, domain, 0)
    question = (
        "Is it true that the beads come from jar A?"
        if domain == "urn"
        else "Is it true that the central bank will raise rates at the meeting?"
    )
    return state, {"answer": {"type": "noul", "instructions": question}}


_TONE = {
    "urn": {
        1: {"hedged": "I think it's probably red.", "plain": "It's red.",
            "confident": "It's definitely red. Confirmed."},
        -1: {"hedged": "I think it's probably blue.", "plain": "It's blue.",
             "confident": "It's definitely blue. Confirmed."},
    },
    "desk": {
        1: {"hedged": "I think a rate rise at the next meeting is probably appropriate.",
            "plain": "We will raise rates at the next meeting.",
            "confident": "We will definitely raise rates at the next meeting. That is settled."},
        -1: {"hedged": "I think holding rates at the next meeting is probably appropriate.",
             "plain": "We will hold rates at the next meeting.",
             "confident": "We will definitely hold rates at the next meeting. That is settled."},
    },
}  # fmt: skip


def tone_text(item, domain, phrasing):
    p, w, d, rec = (item[k] for k in ("prior", "wording", "direction", "record"))
    phrase = _TONE[domain][d][w]
    if domain == "urn":
        record = (
            "" if rec is None else f" This observer's reports are correct {pct(rec)} of the time."
        )
        states = [
            f"A ball is drawn from an urn. Before anyone looks, the probability that it is red is "
            f'{pct(p)}. An observer who looked at the ball says: "{phrase}"{record}',
            f"Chance that the ball just drawn is red, before it is inspected: {pct(p)}. The "
            f'person who inspected it reports: "{phrase}"{record}',
            f"An urn's next ball has a {pct(p)} chance of being red. Someone has seen the ball "
            f'and says: "{phrase}"{record}',
        ]
        questions = ["Is it true that the ball is red?", "Is the ball red?",
                     "Is it true that the ball drawn is red?"]  # fmt: skip
    else:
        who = OFFICIALS[phrasing]
        record = (
            "" if rec is None
            else f" {who}'s pre-meeting signals have matched the decision {pct(rec)} of the time."
        )  # fmt: skip
        states = [
            f"Markets price a {pct(p)} chance that the central bank raises rates at its next "
            f'meeting. {who}, a member of the rate-setting committee, said today: "{phrase}"'
            f"{record}",
            f"Futures imply a {pct(p)} probability of a rate rise at the next policy meeting. In "
            f'a speech this morning, {who} said: "{phrase}"{record}',
            f"Pricing ahead of the meeting: {pct(p)} chance of a hike. {who}, who sits on the "
            f'committee, told reporters: "{phrase}"{record}',
        ]
        questions = [
            "Is it true that the central bank will raise rates at its next meeting?",
            "Will the central bank raise rates at the next meeting?",
            "Is it true that the central bank will hike at the meeting?",
        ]
    return states[phrasing], {"answer": {"type": "noul", "instructions": questions[phrasing]}}


# ---------- Calls ----------


def calls(models=tuple(MODELS)):
    """Every call of the battery, in order: (call id, metadata, body)."""
    out = []

    def add(model, task, domain, i, phrasing, state, questions, part=None):
        part = part or task
        call_id = f"{model}/{part}/{domain}/{i}/{phrasing}"
        kinds = {
            k: ("options" if q["type"] == "choice" else q["type"]) for k, q in questions.items()
        }
        meta = {"model": model, "part": part, "task": task, "domain": domain, "item": i,
                "phrasing": phrasing, "questions": kinds}  # fmt: skip
        out.append((call_id, meta, {"model": model, "state": state, "questions": questions}))

    texts = {"bookbag": bookbag_text, "beads": beads_text, "tone": tone_text}
    for model in models:
        for task, make in ITEMS.items():
            for domain in DOMAINS:
                for i, item in enumerate(make()):
                    for phrasing in PHRASINGS:
                        add(model, task, domain, i, phrasing, *texts[task](item, domain, phrasing))
        for domain in DOMAINS:
            for i, item in enumerate(beads_items()):
                add(model, "beads", domain, i, 0, *beads_belief(item, domain), part="belief")
    return out
