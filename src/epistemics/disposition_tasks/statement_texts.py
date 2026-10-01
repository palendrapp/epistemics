"""Statement texts (tasks 0.31; docs/statement-updating-design.md).

Composite policy statements of an unnamed central bank in generic central-bank language. Each slot
has a hawkish (-1), neutral (0) and dovish (+1) wording; each style has two wordings with the same
meaning. No dates, rate levels or named events appear. Tasks 0.30 adapted FOMC sentences; the
datability probe placed every statement in 2013-2019, so 0.31 removes the Fed's and the period's
signature phrases (target range, longer-run objective, maximum employment, realized and expected
economic conditions, sustain the expansion).
"""

from epistemics.dispositions import statements as st

SLOT_TEXT = {
    "activity": {
        -1: "the economy has grown at a strong pace.",
        0: "the economy has grown at a moderate pace.",
        1: "economic growth has slowed.",
    },
    "inflation": {
        -1: "Inflation has risen and is somewhat above the committee's target.",
        0: "Inflation is close to the committee's target.",
        1: "Inflation has fallen and is somewhat below the committee's target.",
    },
    "risks": {
        -1: "The committee sees the risks to inflation as tilted upwards.",
        0: "The committee sees the risks to the outlook as broadly balanced.",
        1: "The committee sees increased risks that growth will be weaker than expected.",
    },
    "guidance": {
        -1: "The committee expects that a further rise in the policy rate may be needed.",
        0: "The committee will set the policy rate according to incoming data and the outlook.",
        1: "The committee is prepared to lower the policy rate if the outlook weakens.",
    },
    "vote": {
        -1: "The decision was taken by a majority; one member preferred to raise the policy rate.",
        0: "The decision was unanimous.",
        1: "The decision was taken by a majority; one member preferred to lower the policy rate.",
    },
}
# Stylistic pairs: the same meaning in two wordings (the content law's audited list).
STYLE_TEXT = {
    "opening": (
        "Recent data show that",
        "Data published since the committee's last meeting show that",
    ),
    "mandate": (
        "The committee's aim is to keep inflation low and stable while supporting sustainable "
        "growth in output and employment.",
        "The committee seeks to keep inflation low and stable and to support sustainable growth "
        "in output and employment.",
    ),
    "action": (
        "The committee decided to keep its policy rate unchanged.",
        "The committee decided to hold its policy rate at its current level.",
    ),
}
LOWER = "The committee decided to lower its policy rate."
SPENDING = (
    "Household spending has continued to grow, while business investment has been soft.",
    "Business investment has picked up, and household spending has been steady.",
    "Growth in household spending has moderated, and business investment has been flat.",
    "Household spending and business investment have both grown at a steady pace.",
)
JOBS = (
    "Employment has continued to rise, and unemployment remains low.",
    "Employment growth has eased but remains firm, and unemployment remains low.",
    "Unemployment has changed little, and employment has grown steadily.",
)
OUTCOME = "the committee lowers its policy rate at its next meeting"


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
        "What is the probability that the committee changed its policy rate at the meeting this "
        "statement reports?"
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
