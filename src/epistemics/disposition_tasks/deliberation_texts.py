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
    frame = str(items["frame"][i]) if "frame" in items else ""
    if kind == "frame" and frame == "verbal":
        return [line], f"Is it likely or unlikely that {predicate}?"
    if kind == "frame" and frame == "model":
        return [line], (
            "Judging from the three readings, does it grow by about the same amount each step "
            "or by a growing amount each step?"
        )
    if kind == "estimate" and frame in ("comparison-plain", "verbal", "model"):
        return [line, "The previous case asked about the same readings."], (
            f"What is the probability that {predicate}?"
        )
    if kind in ("choice", "frame"):
        return [line, f"Consider {anchor}%, {NO_INFORMATION}."], (
            f"Is the probability that {predicate} above or below {anchor}%?"
        )
    return [
        line,
        f"In the previous case you compared this probability with {anchor}%, {NO_INFORMATION}.",
    ], f"What is the probability that {predicate}?"


def stated(items, i):
    """The anchor a comparison or estimate case displays."""
    kind = str(items["kind"][i])
    frame = str(items["frame"][i]) if "frame" in items else ""
    if kind in ("choice", "frame") and frame in ("", "comparison", "comparison-plain"):
        return [f"{int(items['anchor'][i])}%"]
    if kind == "estimate" and frame in ("", "comparison"):
        return [f"{int(items['anchor'][i])}%"]
    return []
