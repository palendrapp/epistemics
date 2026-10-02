"""Analysts'-calls texts (tasks 0.38): an urn, a stated prior, and two analysts' calls without a
record; one call reported, then both."""

from epistemics.disposition_tasks.peers import LAB_PEERS, PHRASING
from epistemics.dispositions import calls


def colour(direction):
    return "red" if direction == 1 else "blue"


def call_text(analyst, direction, phrase):
    return f"analyst {analyst}: “{PHRASING[phrase].format(c=colour(direction))}”"


def trial(items, i, cover, variant):
    spec = calls.items_spec()[int(items["item"][i])]
    urn = f"urn U{spec['id']}"
    lines = [
        f"Urn U{spec['id']} is either red-majority or blue-majority. Before any evidence, the "
        f"probability that it is red-majority is {spec['prior']}%.",
        f"{LAB_PEERS} Two analysts made calls on {urn}; each analyst phrases its calls in one of "
        "three ways.",
    ]
    first = call_text(
        str(items["first"][i]), int(items["first_direction"][i]), int(items["first_phrase"][i])
    )
    if int(items["step"][i]) == 1:
        lines.append(f"One call has been reported so far, from {first}")
    else:
        second = call_text(
            str(items["second"][i]),
            int(items["second_direction"][i]),
            int(items["second_phrase"][i]),
        )
        lines.append(f"This case continues {urn}. Both calls have now been reported:")
        lines.append(f"1. From {first}\n2. From {second}")
    return (
        lines,
        f"Using the calls reported so far, what is the probability that {urn} is red-majority?",
    )


def stated(items, i):
    return [f"{int(items['prior'][i])}%"]
