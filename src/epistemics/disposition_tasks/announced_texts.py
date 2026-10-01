"""Announced-count texts (tasks 0.36): the statement texts of tasks 0.31, one change reported."""

from epistemics.disposition_tasks.statement_texts import OUTCOME, SLOT_TEXT, quoted, statement
from epistemics.dispositions import announced

COLLEAGUE = (
    "A colleague is comparing the new statement with the previous one. The new statement differs "
    "from it in {n}; everything else is unchanged."
)
SAID = " Two of the three only reword a sentence without changing its meaning."


def change_text(spec):
    slot, direction = spec["target"]
    level = spec["levels"][slot]
    old, new = SLOT_TEXT[slot][level], SLOT_TEXT[slot][level + direction]
    return f'"{old.rstrip(".")}" now reads "{new.rstrip(".")}".'


def trial(items, i, cover, variant):
    spec = announced.items_spec()[int(items["item"][i])]
    condition = str(items["condition"][i])
    n = announced.DECLARED[condition]
    colleague = COLLEAGUE.format(n="1 place" if n == 1 else f"{n} places")
    if condition == "three-said":
        colleague += SAID
    if condition == "one":
        report = f"The colleague reports the change: {change_text(spec)}"
    elif condition == "three-said":
        report = (
            f"The colleague has reported the change that is not a rewording: {change_text(spec)}"
        )
    else:
        report = f"The colleague has reported one of them so far: {change_text(spec)}"
    lines = [
        f"Statement {spec['id']}. A central bank's policy committee has published a new statement "
        "after its meeting. Its previous statement read:",
        *quoted(statement(spec["levels"], spec["styles"], spec["background"])),
        f"Before the new statement was published, market pricing implied a {spec['prior']}% "
        f"chance that {OUTCOME}.",
        colleague,
        report,
    ]
    return lines, f"Using what has been reported so far, what is the probability that {OUTCOME}?"


def stated(items, i):
    return [f"{int(items['prior'][i])}%"]
