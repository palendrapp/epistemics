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

Battery v2 (tasks 0.14) adds a second surface story for each formal core, with the same item
designs and observers as its twin (TWIN) and the per-round wording of urn2: "echo" (observers who
may repeat what another observer told them; dependence, as copying), "hub" (a hub
that may forward every red reading and drop every blue one; withholding, as selection) and
"stale" (readings that may date from before the urn was emptied and refilled; uninformative
evidence, as mismatch). They take urn2-plain and urn2-named.

"urn3-rated" (tasks 0.13, the forecast-only mismatch module) adds the consumer action beyond the
ladder: the named sentence, and after each sensor's record the rate for sensors with that record
(RATES). It measures whether a configuration uses a rate it is given, not whether it raises the
structure. The rates are monotone in the records but far from the mappings the configurations
judged for themselves, so using them can be told apart from judging.
"""

import numpy as np

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
    "echo": (
        "Record for {x}: over the last 200 rounds in which both reported on the same urn, "
        "{x}'s report agreed with {a}'s in 128.",
        "Record for {x}: over the last 200 rounds in which both reported on the same urn, "
        "{x}'s report agreed with {a}'s in 142.",
        "Record for {x}: they work on the second floor.",
        "Record for {x}: over the last 200 rounds in which both reported on the same urn, "
        "{x}'s report agreed with {a}'s in 164.",
        "Record for {x}: over the last 200 rounds in which both reported on the same urn, "
        "{x}'s report agreed with {a}'s in 198.",
    ),
    "hub": (
        "Record for {x}: of the last 200 readings it forwarded, 94 were blue.",
        "Record for {x}: of the last 200 readings it forwarded, 70 were blue.",
        "Record for {x}: it is housed in building 4.",
        "Record for {x}: of the last 200 readings it forwarded, 30 were blue.",
        "Record for {x}: of the last 200 readings it forwarded, 1 was blue.",
    ),
    "stale": (
        "Record for {x}: it takes a fresh reading every round.",
        "Record for {x}: it takes a fresh reading every 2 rounds.",
        "Record for {x}: it has a green casing.",
        "Record for {x}: it takes a fresh reading every 10 rounds.",
        "Record for {x}: it takes a fresh reading every 50 rounds, and its clock often drifts.",
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
    # Battery v2 surfaces (tasks 0.14).
    "echo": (
        "In any round, an observer may repeat what another observer told them instead of looking "
        "at the urn; a repeated report is the same as the original, and an observer's stated "
        "accuracy applies when they look at the urn themselves."
    ),
    "hub": (
        "In any round, a hub may forward every red reading it receives and drop every blue one; "
        "in other rounds it drops readings at random."
    ),
    "stale": (
        "In any round, a reading on file may date from before the urn was last emptied and "
        "refilled; a sensor's stated accuracy applies only when the reading was taken after the "
        "refill, and a reading from before the refill says nothing about the urn now."
    ),
}
# Battery v2: each new surface shares its twin's formal core, item design and observer.
TWIN = {"echo": "copying", "hub": "selection", "stale": "mismatch"}
NAMED3 = {
    "mismatch": (
        "In any round, a reading on file may come from a different urn than the one it is filed "
        "under; a sensor's stated accuracy applies only when the reading does come from that "
        "urn, and a reading from a different urn says nothing about this one."
    ),
}
# Stated misfiling rates per record level (urn3-rated), strongly reassuring to strongly suggestive.
RATES = {"mismatch": (0.05, 0.20, 0.30, 0.40, 0.60)}
LAB = "Half of all urns in the lab are red-majority."


def rated(variant):
    return variant.endswith("rated")


def rate_line(family, slot, x):
    return (
        f"Among sensors with a record like {x}'s, {base.percent(RATES[family][slot])} of the "
        "readings on file come from a different urn than the one they are filed under."
    )


def background(family, variant):
    """The variant's one named sentence, or None in a plain variant."""
    if not variant.endswith(("named", "rated")):
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
        if vigilance(variant):
            lines.append(vig_record("copying", items, i, slot, n, variant))
        else:
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
        if vigilance(variant):
            lines.append(vig_record("selection", items, i, slot, n, variant))
        else:
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
        if slot >= 0 and vigilance(variant):
            lines.append(vig_record("mismatch", items, i, slot, n, variant))
        elif slot >= 0:
            lines.append(record("mismatch", slot, n["s"]))
            if rated(variant):
                lines.append(rate_line("mismatch", slot, n["s"]))
    if kind == "probe":
        question = (
            f"What is the probability that the reading on file for {n['urn']} came from a "
            "different urn?"
        )
    else:
        question = f"What is the probability that {n['urn']} is red-majority?"
    return lines, question


# Battery v2 surfaces (tasks 0.14). Each mirrors its twin's renderer with its own story.


def names_v2(i):
    return {
        "urn": f"urn U{101 + i}",
        "a": f"observer O{11 + i}",
        "b": f"observer O{41 + i}",
        "s": f"sensor K{61 + i}",
        "r": f"hub H{21 + i}",
    }


def echo(items, i, cover, variant):
    """Dependence, second surface: observers who may repeat what another observer told them."""
    n, kind, slot = names_v2(i), items["kind"][i], int(items["slot"][i])
    sentence = background("echo", variant)
    if kind == "rate":
        lines = [
            f"This case concerns {n['b']}, who reports on urns alongside other observers. {LAB}"
            + (f" Background: {sentence}" if sentence else ""),
            record("echo", slot, n["b"], n["a"]),
        ]
        question = (
            f"Among the rounds of observers with a record like {n['b']}'s, in what proportion do "
            "they repeat another observer's report instead of looking at the urn?"
        )
        return lines, question
    lines = [brief(n, items["prior"][i], sentence, "any reports")]
    rates = [
        f"{cap(n['a'])}'s reports are correct {base.percent(items['accuracy_a'][i])} of the time."
    ]
    log = [f"{n['a']}: {colour(items['report_a'][i])}"]
    if kind != "single":
        rates.append(
            f"{cap(n['b'])}'s reports are correct "
            f"{base.percent(items['accuracy_b'][i])} of the time."
        )
        log.append(f"{n['b']}: {colour(items['report_b'][i])}")
    lines += [" ".join(rates), "Reports in the order they were made: " + "; ".join(log) + "."]
    if slot >= 0 and kind != "single":
        lines.append(record("echo", slot, n["b"], n["a"]))
    if kind == "probe":
        question = (
            f"What is the probability that in this round {n['b']} repeated {n['a']}'s report "
            "instead of looking at the urn?"
        )
    else:
        question = f"What is the probability that {n['urn']} is red-majority?"
    return lines, question


def hub(items, i, cover, variant):
    """Withholding, second surface: a hub that may drop every blue reading."""
    n, kind, slot = names_v2(i), items["kind"][i], int(items["slot"][i])
    sentence = background("hub", variant)
    omission = base.percent(items["omission"][i])
    if kind == "rate":
        lines = [
            f"This case concerns {n['r']}, which forwards sensor readings to the lab. Across the "
            f"lab, a hub drops a reading {omission} of the time. {LAB}"
            + (f" Background: {sentence}" if sentence else ""),
            record("hub", slot, n["r"]),
        ]
        question = (
            f"Among the rounds of hubs with a record like {n['r']}'s, in what proportion "
            "do they forward every red reading and drop every blue one, rather than dropping "
            "readings at random?"
        )
        return lines, question
    good, bad = base.percent(items["good"][i]), base.percent(1 - items["good"][i])
    m, j, k = (int(items[f][i]) for f in ("shared_good", "shared_bad", "withheld"))
    lines = [
        brief(n, items["prior"][i], sentence, "the readings arrive"),
        f"A sensor reading a red-majority urn reads red with probability {good}; reading a "
        f"blue-majority urn, with probability {bad}. Across the lab, a hub drops a "
        f"reading {omission} of the time.",
    ]
    forwarded = ["red"] * m + ["blue"] * j
    shown = (
        f"{len(forwarded)} of the 4 readings: " + ", ".join(forwarded)
        if forwarded
        else "none of the 4 readings"
    )
    lines.append(
        f"Four sensors each read {n['urn']} once and send their readings through "
        f"{n['r']}, which forwarded {shown}."
    )
    if slot >= 0:
        lines.append(record("hub", slot, n["r"]))
    if kind == "probe":
        question = (
            f"What is the probability that in this round {n['r']} forwarded every red reading it "
            "received and dropped every blue one?"
        )
    else:
        question = f"What is the probability that {n['urn']} is red-majority?"
    return lines, question


def stale(items, i, cover, variant):
    """Uninformative evidence, second surface: readings from before the urn was refilled."""
    n, kind, slot = names_v2(i), items["kind"][i], int(items["slot"][i])
    sentence = background("stale", variant)
    if kind == "rate":
        lines = [
            f"This case concerns {n['s']}, which files readings for urns. {LAB}"
            + (f" Background: {sentence}" if sentence else ""),
            record("stale", slot, n["s"]),
        ]
        question = (
            f"Among sensors like {n['s']}, what proportion of the readings they file date from "
            "before the urn was last emptied and refilled?"
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
            lines.append(record("stale", slot, n["s"]))
    if kind == "probe":
        question = (
            f"What is the probability that the reading on file for {n['urn']} dates from before "
            "the urn was last emptied and refilled?"
        )
    else:
        question = f"What is the probability that {n['urn']} is red-majority?"
    return lines, question


# Capacity battery, Part B (tasks 0.15): "urn2-vig" is urn2-plain with each record replaced by an
# audit whose likelihood ratio for the (never named) structure is matched across structures: 1,
# 2, 4, 8 and 16 at levels 0-4, for a reference rate of 0.2 of rounds with the structure. K is
# solved per case from the case's own accuracies or omission rate.
VIG_LR = (1, 2, 4, 8, 16)
VIG_N = 100
VIG_RATE = 0.2
# Pilot 2 (tasks 0.16): the first range sat at floor, so "urn2-vig2" spans 1 to 65,536 in steps of
# 16, over 200 audited rounds so every structure can reach the top ratio.
VIG_SCALES = {"urn2-vig": (VIG_LR, VIG_N), "urn2-vig2": ((1, 16, 256, 4096, 65536), 200)}


def vigilance(variant):
    return variant in VIG_SCALES


def vig_rates(family, items, i):
    """Signature frequency without and with the structure, for this case."""
    r = VIG_RATE
    if family == "copying":
        a, b = float(items["accuracy_a"][i]), float(items["accuracy_b"][i])
        f0 = a * b + (1 - a) * (1 - b)
        return f0, (1 - r) * f0 + r
    if family == "selection":
        w = float(items["omission"][i])
        return 0.5, (1 - r) * 0.5 * (1 - w) / ((1 - r) * (1 - w) + 0.5 * r)
    a = float(items["accuracy_a"][i])
    return a, (1 - r) * a + r / 2


def vig_signature(family, items, i, r):
    """Signature frequency when the structure acts in a share r of rounds (r may be an array)."""
    r = np.asarray(r, dtype=float)
    if family == "copying":
        a, b = float(items["accuracy_a"][i]), float(items["accuracy_b"][i])
        return (1 - r) * (a * b + (1 - a) * (1 - b)) + r
    if family == "selection":
        w = float(items["omission"][i])
        return (1 - r) * 0.5 * (1 - w) / ((1 - r) * (1 - w) + 0.5 * r)
    a = float(items["accuracy_a"][i])
    return (1 - r) * a + r / 2


# Tasks 0.17: the ideal observer's reading of an audit record, the reference for the uptake fit.
# Its prior puts half its weight on no structure and spreads the rest uniformly over the rate.
# Records matched on the likelihood ratio for the reference rate also carry rate estimates that
# rise with the count, so the ideal rate grows with the level for two reasons.
VIG_ABSENT = 0.5
VIG_GRID = np.linspace(0, 1, 1001)


def vig_ideal(family, items, i, slot, variant):
    """The ideal observer's posterior mean rate of the structure, given case i's audit record."""
    _, total = VIG_SCALES[variant]
    k = vig_count(family, items, i, slot, variant)
    f = np.clip(vig_signature(family, items, i, VIG_GRID), 1e-12, 1 - 1e-12)
    log_like = k * np.log(f) + (total - k) * np.log1p(-f)
    like = np.exp(log_like - log_like.max())
    slab = like.mean()
    present = (1 - VIG_ABSENT) * slab / ((1 - VIG_ABSENT) * slab + VIG_ABSENT * like[0])
    return float(present * (like * VIG_GRID).mean() / slab)


def vig_ideals(module, variant, items):
    """Per design item: the ideal rate for cases with an audit record, 0 for the rest (anchors,
    and single readings in copying, which no copy can affect)."""
    family = module.split("-", 1)[0]
    skip = ("rate", "single") if family == "copying" else ("rate",)
    values = np.zeros(len(items["kind"]))
    for i, slot in enumerate(np.asarray(items["slot"])):
        if slot >= 0 and items["kind"][i] not in skip:
            values[i] = vig_ideal(family, items, i, int(slot), variant)
    return values


def vig_count(family, items, i, slot, variant="urn2-vig"):
    """The count K of N whose likelihood ratio is closest to the level's target."""
    import math

    levels, total = VIG_SCALES[variant]
    f0, f1 = vig_rates(family, items, i)
    per_hit = math.log(f1 / f0)
    per_miss = math.log((1 - f1) / (1 - f0))
    target = math.log(levels[slot])
    best = min(
        range(total + 1),
        key=lambda k: abs(k * per_hit + (total - k) * per_miss - target),
    )
    return best


def vig_ratio(family, items, i, slot, variant="urn2-vig"):
    import math

    _, total = VIG_SCALES[variant]
    f0, f1 = vig_rates(family, items, i)
    k = vig_count(family, items, i, slot, variant)
    return math.exp(k * math.log(f1 / f0) + (total - k) * math.log((1 - f1) / (1 - f0)))


def vig_record(family, items, i, slot, n, variant="urn2-vig"):
    _, total = VIG_SCALES[variant]
    k = vig_count(family, items, i, slot, variant)
    if family == "copying":
        return (
            f"Audit of {n['b']}: in the last {total} rounds in which {n['b']} and {n['a']} read "
            f"the same urn, {n['b']}'s reading matched {n['a']}'s in {k}."
        )
    if family == "selection":
        return f"Audit of {n['r']}: of the last {total} balls it reported, {k} were blue."
    return (
        f"Audit of {n['s']}: of the last {total} of its filed readings that were checked, {k} "
        "agreed with the later-verified majority of the urn they were filed under."
    )


# Capacity battery, Part A (tasks 0.15): fully specified load cases.
def load_names(i, count):
    return [f"sensor {chr(65 + k)}{i + 11}" for k in range(count)]


def copying_load(items, i, cover, variant):
    n = names(i)
    count = int(items["n"][i])
    sensors = load_names(i, count)
    lines = [
        brief(n, items["prior"][i], None, "any readings"),
        "Some sensors copy another sensor's logged reading instead of reading the urn; a copied "
        "reading repeats the original, and a sensor's stated accuracy applies when it reads the urn "
        "itself.",
        "Stated accuracies: "
        + "; ".join(f"{s} {base.percent(items[f'acc_{k}'][i])}" for k, s in enumerate(sensors))
        + ".",
    ]
    copies = [
        f"{cap(sensors[k])} copies {sensors[int(items[f'src_{k}'][i])]}'s logged reading in "
        f"{base.percent(items[f'rate_{k}'][i])} of rounds."
        for k in range(count)
        if int(items[f"src_{k}"][i]) >= 0
    ]
    lines.append(" ".join(copies) + " Every other sensor always reads the urn itself.")
    log = [f"{s}: {colour(items[f'rep_{k}'][i])}" for k, s in enumerate(sensors)]
    lines.append("Readings in the order they were logged: " + "; ".join(log) + ".")
    return lines, f"What is the probability that {n['urn']} is red-majority?"


def mismatch_load(items, i, cover, variant):
    n = names(i)
    count = int(items["n"][i])
    sensors = load_names(i, count)
    lines = [
        brief(n, items["prior"][i], None, "any evidence"),
        "A reading on file may come from a different urn than the one it is filed under; a "
        "reading from a different urn says nothing about this one, and a sensor's stated accuracy "
        "applies only when the reading does come from this urn.",
    ]
    entries = [
        f"{s} (correct {base.percent(items[f'acc_{k}'][i])} of the time; "
        f"{base.percent(items[f'mis_{k}'][i])} of its filed readings come from a different urn): "
        f"{colour(items[f'rep_{k}'][i])}"
        for k, s in enumerate(sensors)
    ]
    lines.append(f"Readings on file for {n['urn']}: " + "; ".join(entries) + ".")
    return lines, f"What is the probability that {n['urn']} is red-majority?"


def composite_load(items, i, cover, variant):
    """Structural load (tasks 0.18): copying, misfiling and conditional copying among five
    readings, every relation stated."""
    n = names(i)
    count = int(items["n"][i])
    sensors = load_names(i, count)
    lines = [
        brief(n, items["prior"][i], None, "any readings"),
        "Some sensors copy another sensor's logged reading instead of reading the urn, and some "
        "readings are filed under the wrong urn. A copied reading repeats the original's logged "
        "reading exactly, wherever that reading came from. A sensor's stated accuracy applies "
        "when it reads this urn itself, and a reading from a different urn says nothing about "
        "this one.",
        "Stated accuracies: "
        + "; ".join(f"{s} {base.percent(items[f'acc_{k}'][i])}" for k, s in enumerate(sensors))
        + ".",
    ]

    def value(name, k, default=-1):
        key = f"{name}_{k}"
        return items[key][i] if key in items else default

    relations = []
    for k in range(count):
        source = int(items[f"src_{k}"][i])
        if source < 0:
            continue
        copied = (
            f"{cap(sensors[k])} copies {sensors[source]}'s logged reading in "
            f"{base.percent(items[f'rate_{k}'][i])} of rounds"
        )
        second = int(value("src2", k))
        if second >= 0:
            # Tasks 0.19: a second source.
            copied += (
                f" and {sensors[second]}'s in {base.percent(value('rate2', k))} of rounds; in "
                "the other rounds it reads the urn itself"
            )
        condition = int(items[f"cond_{k}"][i])
        if condition:
            when, other = ("red", "blue") if condition == 1 else ("blue", "red")
            copied += (
                f", but only in rounds when {sensors[source]}'s logged reading is {when}; when it "
                f"is {other}, {sensors[k]} always reads the urn itself"
            )
        relations.append(copied + ".")
    for k in range(count):
        if float(items[f"mis_{k}"][i]) > 0:
            share = base.percent(items[f"mis_{k}"][i])
            governed = int(value("msrc", k))
            if governed >= 0:
                # Tasks 0.19: misfiling that applies only when another reading is blue.
                relations.append(
                    f"In rounds when {sensors[governed]}'s logged reading is blue, {share} of the "
                    f"readings {sensors[k]} takes itself come from a different urn than the one "
                    "they are filed under; in other rounds all of them are filed under the right "
                    "urn."
                )
            else:
                relations.append(
                    f"{share} of the readings {sensors[k]} takes itself come from a different urn "
                    "than the one they are filed under."
                )
    lines.append(" ".join(relations))
    lines.append(
        "Every other sensor always reads the urn itself, and every other reading is filed under "
        "the right urn."
    )
    log = [f"{s}: {colour(items[f'rep_{k}'][i])}" for k, s in enumerate(sensors)]
    lines.append("Readings in the order they were logged: " + "; ".join(log) + ".")
    return lines, f"What is the probability that {n['urn']} is red-majority?"


def load_percentages(family, items, i):
    count = int(items["n"][i])
    values = [items["prior"][i]]
    for k in range(count):
        values.append(items[f"acc_{k}"][i])
        if family in ("copying", "composite") and int(items[f"src_{k}"][i]) >= 0:
            values.append(items[f"rate_{k}"][i])
        if family == "composite" and f"src2_{k}" in items and int(items[f"src2_{k}"][i]) >= 0:
            values.append(items[f"rate2_{k}"][i])
        if family == "mismatch" or (family == "composite" and float(items[f"mis_{k}"][i]) > 0):
            values.append(items[f"mis_{k}"][i])
    return sorted({base.percent(v) for v in values})
