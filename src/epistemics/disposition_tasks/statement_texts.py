"""Statement texts (tasks 0.30; docs/statement-updating-design.md).

Composite policy statements of an unnamed central bank, in the style of FOMC statements (US
government works). Each slot has a hawkish (-1), neutral (0) and dovish (+1) wording; each style
has two wordings with the same meaning. No dates, rate levels or named events appear.
"""

from epistemics.dispositions import statements as st

SLOT_TEXT = {
    "activity": {
        -1: "economic activity has been rising at a solid rate.",
        0: "economic activity has been rising at a moderate rate.",
        1: "growth of economic activity has slowed.",
    },
    "inflation": {
        -1: "Inflation has moved up and is running somewhat above the committee's longer-run "
        "objective.",
        0: "Inflation has remained near the committee's longer-run objective.",
        1: "Inflation has declined and is running somewhat below the committee's longer-run "
        "objective.",
    },
    "risks": {
        -1: "The committee judges that the risks to the inflation outlook are tilted to the upside.",
        0: "The committee judges that the risks to the economic outlook are roughly balanced.",
        1: "The committee judges that downside risks to the economic outlook have increased.",
    },
    "guidance": {
        -1: "The committee anticipates that some further increases in the target range may be "
        "appropriate.",
        0: "In determining the timing and size of future adjustments to the target range, the "
        "committee will assess realized and expected economic conditions.",
        1: "The committee will closely monitor incoming information and will act as appropriate "
        "to sustain the expansion.",
    },
    "vote": {
        -1: "All members voted for the policy action except one, who preferred to raise the "
        "target range.",
        0: "All members voted for the policy action.",
        1: "All members voted for the policy action except one, who preferred to lower the "
        "target range.",
    },
}
# Stylistic pairs: the same meaning in two wordings (the content law's audited list).
STYLE_TEXT = {
    "opening": (
        "Recent information indicates that",
        "Information received since the committee's last meeting indicates that",
    ),
    "mandate": (
        "The committee seeks to achieve maximum employment and stable prices over the longer run.",
        "Consistent with its mandate, the committee seeks to foster maximum employment and price "
        "stability.",
    ),
    "action": (
        "The committee decided to maintain the target range for its policy rate.",
        "The committee decided to leave the target range for its policy rate unchanged.",
    ),
}
LOWER = "The committee decided to lower the target range for its policy rate."
SPENDING = (
    "Household spending has continued to grow, while business investment has been soft.",
    "Business investment has picked up, and household spending has been steady.",
    "Growth in household spending has moderated, and business investment has been flat.",
    "Household spending and business investment have both grown at a steady pace.",
)
JOBS = (
    "Job gains have been solid, and the unemployment rate has remained low.",
    "Job gains have moderated but remain solid, and the unemployment rate has stayed low.",
    "The unemployment rate has been little changed, and job gains have been steady.",
)
OUTCOME = "the committee lowers the target range for its policy rate at its next meeting"


def statement(levels, styles, background, action=None):
    """The statement's three paragraphs."""
    spending, jobs = background
    if action == "lower":
        decision = LOWER
    else:
        decision = STYLE_TEXT["action"][styles["action"]]
    return [
        " ".join(
            [
                STYLE_TEXT["opening"][styles["opening"]],
                SLOT_TEXT["activity"][levels["activity"]],
                SPENDING[spending],
                JOBS[jobs],
                SLOT_TEXT["inflation"][levels["inflation"]],
            ]
        ),
        " ".join(
            [
                STYLE_TEXT["mandate"][styles["mandate"]],
                decision,
                SLOT_TEXT["guidance"][levels["guidance"]],
                SLOT_TEXT["risks"][levels["risks"]],
            ]
        ),
        SLOT_TEXT["vote"][levels["vote"]],
    ]


def updated(spec):
    """The new statement's levels and styles: every change applied."""
    levels, styles = dict(spec["levels"]), dict(spec["styles"])
    for name, d in spec["changes"]:
        if name in st.STYLES:
            styles[name] = 1 - styles[name]
        else:
            levels[name] += d
    return levels, styles


def wording(spec, c):
    """Change c as quoted before and after."""
    name, d = spec["changes"][c]
    if name in st.STYLES:
        style = spec["styles"][name]
        old, new = STYLE_TEXT[name][style], STYLE_TEXT[name][1 - style]
    else:
        level = spec["levels"][name]
        old, new = SLOT_TEXT[name][level], SLOT_TEXT[name][level + d]
    return f'"{old.rstrip(".")}" now reads "{new.rstrip(".")}".'


def quoted(paragraphs):
    return [f"> {p}" for p in paragraphs]


def _header(spec):
    n = spec["n"]
    return [
        f"Statement {spec['id']}. A central bank's policy committee has published a new statement "
        "after its meeting. Its previous statement read:",
        *quoted(statement(spec["levels"], spec["styles"], spec["background"])),
        f"Before the new statement was published, market pricing implied a {spec['prior']}% "
        f"chance that {OUTCOME}.",
        "A colleague is comparing the new statement with the previous one. The new statement "
        f"differs from it in {n} {'place' if n == 1 else 'places'}; everything else is unchanged.",
    ]


def _sequence_case(items, i):
    spec = st.FORM_SPECS[str(items["form"][i])][int(items["sequence"][i])]
    kind, n = str(items["kind"][i]), spec["n"]
    lines = _header(spec)
    if kind == "prior":
        lines.append("The colleague has not reported any of the changes yet.")
        return lines, f"Before any change is reported, what is the probability that {OUTCOME}?"
    if kind == "whole":
        if n == 1:
            lines.append(f"The colleague reports the change: {wording(spec, 0)}")
        else:
            lines.append(f"The colleague reports all {n} changes at once:")
            lines.append("\n".join(f"{c + 1}. {wording(spec, c)}" for c in range(n)))
        return lines, f"Using all the changes, what is the probability that {OUTCOME}?"
    t = int(items["step"][i])
    lines.append(
        f"This case continues statement {spec['id']}. The colleague reports the changes one at a "
        "time; any earlier changes appeared in the preceding cases and still apply."
    )
    lines.append(f"Change {t} of {n}: {wording(spec, int(items['change'][i]))}")
    return lines, (
        f"Using every change reported so far for statement {spec['id']}, what is the probability "
        f"that {OUTCOME}?"
    )


def _anchor_case(items, i):
    a = st.anchor_spec(str(items["form"][i]), int(items["rotation"][i]), int(items["step"][i]))
    lines = [
        f"Statement {a['id']}. A central bank's policy committee published this statement after "
        "its meeting:",
        *quoted(statement(a["levels"], a["styles"], a["background"], a["action"])),
    ]
    return lines, (
        "What is the probability that the committee changed the target range for its policy rate "
        "at the meeting this statement reports?"
    )


def _probe_case(items, i):
    spec = st.FORM_SPECS[str(items["form"][i])][int(items["sequence"][i])]
    levels, styles = updated(spec)
    lines = [
        "Two consecutive policy statements from a central bank's policy committee.",
        "Earlier statement:",
        *quoted(statement(spec["levels"], spec["styles"], spec["background"])),
        "Later statement:",
        *quoted(statement(levels, styles, spec["background"])),
    ]
    period = st.PERIODS[int(items["period"][i])]
    return lines, (
        "Judging from their wording, what is the probability that statements like these were "
        f"written {period}?"
    )


def trial(items, i, cover, variant):
    kind = str(items["kind"][i])
    if kind == "period":
        return _probe_case(items, i)
    if kind == "anchor":
        return _anchor_case(items, i)
    return _sequence_case(items, i)


def stated(items, i):
    """The percentage a sequence case must display: its market prior."""
    if str(items["kind"][i]) in ("prior", "step", "whole"):
        return [f"{int(items['prior'][i])}%"]
    return []
