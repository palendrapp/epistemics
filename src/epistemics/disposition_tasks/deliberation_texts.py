"""Deliberation-style texts (tasks 0.32; docs/deliberation-style-design.md).

The screen's trend surfaces. Ladder cases ask one threshold each; anchor pairs first compare the
probability with a number chosen for the exercise (stated to carry no information), then ask for
the probability.
"""

from epistemics.disposition_tasks.screen_texts import TREND
from epistemics.dispositions import deliberation

NO_INFORMATION = "a number chosen for this exercise. It carries no information about this case"


def _parts(items, i):
    s = int(items["series"][i])
    surface, (a, b, c), x, ident = deliberation.ALL_SERIES[s]
    readings, above, _, _ = TREND[surface]
    line = readings.format(id=ident, a=a, b=b, c=c)
    return line, above.format(t=int(items["threshold"][i]), x=x)


def trial(items, i, cover, variant):
    line, predicate = _parts(items, i)
    kind = str(items["kind"][i])
    if kind in ("ladder", "bare"):
        return [line], f"What is the probability that {predicate}?"
    anchor = int(items["anchor"][i])
    if kind == "choice":
        return [line, f"Consider {anchor}%, {NO_INFORMATION}."], (
            f"Is the probability that {predicate} above or below {anchor}%?"
        )
    return [
        line,
        f"In the previous case you compared this probability with {anchor}%, {NO_INFORMATION}.",
    ], f"What is the probability that {predicate}?"


def stated(items, i):
    """The anchor a comparison or estimate case displays."""
    if str(items["kind"][i]) in ("choice", "estimate"):
        return [f"{int(items['anchor'][i])}%"]
    return []
