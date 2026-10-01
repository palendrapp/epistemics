"""Correlated-changes texts (tasks 0.37): a statement that differs in two places; one change
reported, then both."""

from epistemics.disposition_tasks.statement_texts import OUTCOME, SLOT_TEXT, quoted, statement
from epistemics.dispositions import correlated

COLLEAGUE = (
    "A colleague is comparing the new statement with the previous one. The new statement differs "
    "from it in 2 places; everything else is unchanged."
)


def change_text(spec, slot, direction):
    level = spec["levels"][slot]
    old, new = SLOT_TEXT[slot][level], SLOT_TEXT[slot][level + direction]
    return f'"{old.rstrip(".")}" now reads "{new.rstrip(".")}".'


def trial(items, i, cover, variant):
    spec = correlated.items_spec()[int(items["item"][i])]
    first = change_text(spec, str(items["first"][i]), int(items["first_direction"][i]))
    lines = [
        f"Statement {spec['id']}. A central bank's policy committee has published a new statement "
        "after its meeting. Its previous statement read:",
        *quoted(statement(spec["levels"], spec["styles"], spec["background"])),
        f"Before the new statement was published, market pricing implied a {spec['prior']}% "
        f"chance that {OUTCOME}.",
        COLLEAGUE,
    ]
    if int(items["step"][i]) == 1:
        lines.append(f"The colleague has reported one of them so far: {first}")
    else:
        second = change_text(spec, str(items["second"][i]), int(items["second_direction"][i]))
        lines.append(
            f"This case continues statement {spec['id']}. The colleague has now reported both:"
        )
        lines.append(f"1. {first}\n2. {second}")
    return lines, f"Using what has been reported so far, what is the probability that {OUTCOME}?"


def stated(items, i):
    return [f"{int(items['prior'][i])}%"]
