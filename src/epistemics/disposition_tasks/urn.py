"""Abstract urn cases: contentless versions of the relay and disclosure modules, and a third
structure, mismatch (a reading filed under the wrong urn).

Each case concerns an urn that is either red-majority or blue-majority. Sensors read urns, and a
reporter draws balls and reports some of them. The graded cues that replace the dossiers'
descriptions are records, not descriptions:
- copying: how often sensor B's reading has matched sensor A's;
- selection: how many of the balls the reporter reported were blue;
- mismatch: how many urns the sensor serves.

The "urn-plain" variant never names the hidden structure. "urn-named" adds one background
sentence naming it, without a rate. Base-rate questions and structure probes, where the design
has them, name it in the question only.

"urn2-plain" and "urn2-named" (tasks 0.11) correct two flaws found in the first run
(docs/disposition-abstract-2026-09-28.md). The structures are stated per round, as the observers
assume, so a record showing a few blue balls is compatible with a mostly selective reporter. And
the named sentence says what the stated accuracies cover, so accuracy cannot be read as already
including copying or misfiling. The plain texts of the two versions are identical.

"urn3-named" (tasks 0.12, mismatch only) rewords that clause. "Applies to readings of the urn it
is filed under" was read as covering misfiled readings (docs/disposition-abstract2-2026-09-29.md);
the new sentence says accuracy applies only when a reading does come from the urn it is filed
under, and that a reading from a different urn says nothing about this one. Its plain cases are
urn2-plain's.
"""

from epistemics.disposition_tasks import render as base

NAMED = {
    "copying": (
        "Some sensors copy another sensor's logged reading instead of reading the urn; a copied "
        "reading simply repeats the original."
    ),
    "selection": "Some reporters report every red ball they draw and hold back every blue one.",
    "mismatch": "Some readings on file come from a different urn than the one they are filed under.",
}
# Record lines per level, strongly reassuring to strongly suggestive; {x} is the sensor or reporter
# and {a} the first sensor.
RECORDS = {
    "copying": (
        "Record for {x}: over the last 200 rounds in which both read the same urn, its reading "
        "matched {a}'s in 128.",
        "Record for {x}: over the last 200 rounds in which both read the same urn, its reading "
        "matched {a}'s in 142.",
        "Record for {x}: it is mounted on rack 4.",
        "Record for {x}: over the last 200 rounds in which both read the same urn, its reading "
        "matched {a}'s in 164.",
        "Record for {x}: over the last 200 rounds in which both read the same urn, its reading "
        "matched {a}'s in 198.",
    ),
    "selection": (
        "Record for {x}: of the last 200 balls it reported, 94 were blue.",
        "Record for {x}: of the last 200 balls it reported, 70 were blue.",
        "Record for {x}: it works at station 4.",
        "Record for {x}: of the last 200 balls it reported, 30 were blue.",
        "Record for {x}: of the last 200 balls it reported, 1 was blue.",
    ),
    "mismatch": (
        "Record for {x}: it is fixed to one urn and reads no other.",
        "Record for {x}: it is shared by 2 urns.",
        "Record for {x}: it is painted grey.",
        "Record for {x}: it is shared by 10 urns.",
        "Record for {x}: it is shared by 50 urns and moves between them during the session.",
    ),
}
# Corrected versions: per round, with what the stated accuracies cover.
NAMED2 = {
    "copying": (
        "In any round, a sensor may copy another sensor's logged reading instead of reading the "
        "urn; a copied reading repeats the original, and a sensor's stated accuracy applies when "
        "it reads the urn itself."
    ),
    "selection": (
        "In any round, a reporter may report every red ball it drew and hold back every blue one; "
        "in other rounds it leaves balls unreported at random."
    ),
    "mismatch": (
        "In any round, a reading on file may come from a different urn than the one it is filed "
        "under; a sensor's stated accuracy applies to readings of the urn it is filed under."
    ),
}
NAMED3 = {
    "mismatch": (
        "In any round, a reading on file may come from a different urn than the one it is filed "
        "under; a sensor's stated accuracy applies only when the reading does come from that "
        "urn, and a reading from a different urn says nothing about this one."
    ),
}
LAB = "Half of all urns in the lab are red-majority."


def background(family, variant):
    """The variant's one named sentence, or None in a plain variant."""
    if not variant.endswith("named"):
        return None
    if variant.startswith("urn3"):
        return NAMED3[family]
    return (NAMED2 if variant.startswith("urn2") else NAMED)[family]


def corrected(variant):
    """Per-round wording (tasks 0.11 onwards)."""
    return variant.startswith(("urn2", "urn3"))


def names(i):
    return {
        "urn": f"urn U{101 + i}",
        "a": f"sensor A{11 + i}",
        "b": f"sensor B{41 + i}",
        "s": f"sensor S{61 + i}",
        "r": f"reporter R{21 + i}",
    }


def cap(text):
    """Capitalise the first letter only (identifiers keep their case)."""
    return text[:1].upper() + text[1:]


def colour(report):
    return "red" if report > 0 else "blue"


def record(family, slot, x, a=""):
    return RECORDS[family][slot].format(x=x, a=a)


def brief(n, prior, sentence, before="any readings"):
    text = (
        f"{cap(n['urn'])} is either red-majority or blue-majority. Before {before}, the "
        f"probability that it is red-majority is {base.percent(prior)}. {LAB}"
    )
    if sentence:
        text += f" Background: {sentence}"
    return text


def copying(items, i, cover, variant):
    n, kind, slot = names(i), items["kind"][i], int(items["slot"][i])
    sentence = background("copying", variant)
    if kind == "rate":
        lines = [
            f"This case concerns {n['b']}, which reads urns alongside other sensors. {LAB}"
            + (f" Background: {sentence}" if sentence else ""),
            record("copying", slot, n["b"], n["a"]),
        ]
        question = (
            f"Among the rounds of sensors with a record like {n['b']}'s, in what proportion do "
            "they copy another sensor's reading instead of reading the urn?"
            if corrected(variant)
            else f"Among sensors with a record like {n['b']}'s, what proportion copy another "
            "sensor's reading instead of reading the urn?"
        )
        return lines, question
    lines = [brief(n, items["prior"][i], sentence)]
    rates = [
        f"{cap(n['a'])}'s readings are correct {base.percent(items['accuracy_a'][i])} of the time."
    ]
    log = [f"{n['a']}: {colour(items['report_a'][i])}"]
    if kind != "single":
        rates.append(
            f"{cap(n['b'])}'s readings are correct "
            f"{base.percent(items['accuracy_b'][i])} of the time."
        )
        log.append(f"{n['b']}: {colour(items['report_b'][i])}")
    lines += [" ".join(rates), "Readings in the order they were logged: " + "; ".join(log) + "."]
    if slot >= 0 and kind != "single":
        lines.append(record("copying", slot, n["b"], n["a"]))
    if kind == "probe":
        question = (
            f"What is the probability that in this round {n['b']} copied {n['a']}'s reading "
            "instead of reading the urn?"
            if corrected(variant)
            else f"What is the probability that {n['b']} copied {n['a']}'s reading instead of "
            "reading the urn?"
        )
    else:
        question = f"What is the probability that {n['urn']} is red-majority?"
    return lines, question


def selection(items, i, cover, variant):
    n, kind, slot = names(i), items["kind"][i], int(items["slot"][i])
    sentence = background("selection", variant)
    omission = base.percent(items["omission"][i])
    if kind == "rate":
        lines = [
            f"This case concerns {n['r']}, which draws balls from urns and reports some of them. "
            f"Across the lab, a drawn ball goes unreported {omission} of the time. {LAB}"
            + (f" Background: {sentence}" if sentence else ""),
            record("selection", slot, n["r"]),
        ]
        question = (
            f"Among the rounds of reporters with a record like {n['r']}'s, in what proportion do "
            "they report every red ball they drew and hold back every blue one, rather than "
            "leaving balls unreported at random?"
            if corrected(variant)
            else f"Among reporters with a record like {n['r']}'s, what proportion report every "
            "red ball they draw and hold back every blue one, rather than leaving balls "
            "unreported at random?"
        )
        return lines, question
    good, bad = base.percent(items["good"][i]), base.percent(1 - items["good"][i])
    m, j, k = (int(items[f][i]) for f in ("shared_good", "shared_bad", "withheld"))
    lines = [
        brief(n, items["prior"][i], sentence, "the report"),
        f"A ball drawn from a red-majority urn is red with probability {good}; from a "
        f"blue-majority urn, with probability {bad}. Across the lab, a drawn ball goes unreported "
        f"{omission} of the time.",
    ]
    reported = ["red"] * m + ["blue"] * j
    shown = f"{len(reported)}: " + ", ".join(reported) if reported else "none of them"
    lines.append(f"{cap(n['r'])} drew 4 balls from {n['urn']} and reported {shown}.")
    if slot >= 0:
        lines.append(record("selection", slot, n["r"]))
    if kind == "probe":
        question = (
            f"What is the probability that in this round {n['r']} reported every red ball it drew "
            "and held back every blue one?"
            if corrected(variant)
            else f"What is the probability that {n['r']} is a reporter that reports every red "
            "ball it draws and holds back every blue one?"
        )
    else:
        question = f"What is the probability that {n['urn']} is red-majority?"
    return lines, question


def mismatch(items, i, cover, variant):
    n, kind, slot = names(i), items["kind"][i], int(items["slot"][i])
    sentence = background("mismatch", variant)
    if kind == "rate":
        lines = [
            f"This case concerns {n['s']}, which files readings for urns. {LAB}"
            + (f" Background: {sentence}" if sentence else ""),
            record("mismatch", slot, n["s"]),
        ]
        question = (
            f"Among sensors like {n['s']}, what proportion of the readings they file come from a "
            "different urn than the one they are filed under?"
        )
        return lines, question
    accuracy = base.percent(items["accuracy_a"][i])
    lines = [brief(n, items["prior"][i], sentence, "any evidence")]
    if kind == "own":
        miss = base.percent(1 - items["accuracy_a"][i])
        lines.append(
            f"You draw one ball from {n['urn']} yourself. A ball drawn from a red-majority urn is "
            f"red with probability {accuracy}, and from a blue-majority urn with probability "
            f"{miss}. Your ball is {colour(items['report_a'][i])}."
        )
    else:
        lines.append(
            f"{cap(n['s'])}'s readings are correct {accuracy} of the time. Reading on file "
            f"for {n['urn']}, from {n['s']}: {colour(items['report_a'][i])}."
        )
        if slot >= 0:
            lines.append(record("mismatch", slot, n["s"]))
    if kind == "probe":
        question = (
            f"What is the probability that the reading on file for {n['urn']} came from a "
            "different urn?"
        )
    else:
        question = f"What is the probability that {n['urn']} is red-majority?"
    return lines, question
