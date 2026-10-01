"""Coherence-set texts (tasks 0.29; docs/screen-coherence-design.md).

Members of a set share the case text (the entity number follows the set) and differ only in
their question. Anchors reuse the screen's anchor texts.
"""

import math

from epistemics.disposition_tasks import screen_texts
from epistemics.dispositions import cohere


def ident(items, i):
    s = int(items["set"][i])
    return 41 + s if s >= 0 else 61 + i


def _bound(value, side):
    """Integer text for a bin edge stored as a half-integer (counts) or an integer."""
    if float(value).is_integer():
        return int(value)
    return math.ceil(value) if side == "low" else math.floor(value)


def _num(items, i, d):
    person, instrument, predicate, fewer = screen_texts.NUMBERS[d["quantity"]]
    if items["kind"][i] == "anchor":
        return screen_texts._num(items, i, d)
    if d["source"] == "instrument":
        lines = [instrument.format(v=d["value"])]
    else:
        lines = [person.format(who=screen_texts.SPEAKERS[d["speaker"]], v=d["value"])]
    lo, hi = d["window"]
    if d.get("span") == "atmost":
        span = f"at most {_bound(hi, 'high')}"
    elif lo <= cohere.LOW:
        span = f"{fewer} than {_bound(hi, 'low') if not float(hi).is_integer() else int(hi)}"
    elif hi >= cohere.HIGH:
        span = f"more than {_bound(lo, 'high') if not float(lo).is_integer() else int(lo)}"
    else:
        span = f"between {_bound(lo, 'low')} and {_bound(hi, 'high')}"
    return lines, f"What is the probability that {predicate.format(range=span)}?"


def _lists(items, i, d):
    if items["kind"][i] == "anchor":
        return screen_texts._lists(items, i, d)
    event, _, manual, _ = screen_texts.LISTS[d["domain"]]
    causes = screen_texts.listed(d)
    source = manual if d["source"] == "manual" else "A colleague suggests these possible causes"
    lines = [event.format(id=ident(items, i)), f"{source}: {screen_texts.listing(causes)}."]
    named = [causes[j] for j in d["named"]]
    joined = (
        named[0] if len(named) == 1 else ", ".join(named[:-1]) + " or " + named[-1] if named else ""
    )
    if d["question"] == "none":
        return lines, "What is the probability that the cause was none of these?"
    if d["question"] == "conditional":
        return lines, (
            f"If the cause was one of the listed causes, what is the probability that it was {joined}?"
        )
    return lines, f"What is the probability that the cause was {joined}?"


# Per surface: "below" predicate (the screen's texts give "above" and "within").
BELOW = {
    0: "it will read below {t} cm after {x} hours",
    1: "it will have fewer than {t} open tickets after {x} days",
    2: "it will use less than {t} GB after {x} weeks",
    3: "it will have fewer than {t} registered users after {x} months",
    4: "it will have processed fewer than {t} orders by the end of hour {x}",
}


def _trend(items, i, d):
    if items["kind"][i] == "anchor":
        return screen_texts._trend(items, i, d)
    readings, above, within, _ = screen_texts.TREND[d["surface"]]
    a, b, c = d["ys"]
    lines = [readings.format(id=ident(items, i), a=a, b=b, c=c)]
    if d["bin"] == "above":
        predicate = above.format(t=d["threshold"], x=d["x"])
    elif d["bin"] == "below":
        predicate = BELOW[d["surface"]].format(t=d["window"][1], x=d["x"])
    else:
        lo, hi = d["window"]
        predicate = within.format(lo=lo, hi=hi, x=d["x"])
    return lines, f"What is the probability that {predicate}?"


RENDER = {"num": _num, "lists": _lists, "trend": _trend}


def trial(items, i, cover, variant):
    return RENDER[str(items["family"][i])](items, i, cohere.data(items, i))
