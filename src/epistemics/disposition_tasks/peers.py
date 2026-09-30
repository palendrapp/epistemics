"""Multi-agent battery, Stage 1 texts (tasks 0.20): scripted peers (docs/multi-agent-design.md).

Other lab analysts send calls about an urn ("It is red-majority"). The respondent reports the
probability that the urn is red-majority.
"""

from epistemics.disposition_tasks import render as base
from epistemics.disposition_tasks.urn import VIG_SCALES, brief, cap, colour, vig_count
from epistemics.dispositions.social import RECORD_CALLS

LAB_PEERS = (
    "Analysts in the lab make calls on urns. A call names the colour the analyst believes is in "
    "the majority."
)
PHRASING = {
    0: "I think it is {c}-majority.",
    1: "It is {c}-majority.",
    2: "It is definitely {c}-majority — confirmed.",
}
PHRASE_NAMES = {0: '"I think…"', 1: "plain", 2: '"definitely… confirmed"'}


def analysts(i):
    return [f"analyst {letter}{31 + i}" for letter in "PQRSTU"]


def urn(i):
    return f"urn U{101 + i}"


def own_line(items, i):
    if not int(items["own"][i]):
        return []
    return [
        f"Your own sensor, whose readings are correct {base.percent(items['own_acc'][i])} of the "
        f"time, reads {colour(items['own'][i])}."
    ]


def advice(items, i, cover, variant):
    """T1: one analyst's call with a confidence phrase, and its record for each phrase."""
    who = analysts(i)[0]
    record = "; ".join(
        f"{PHRASE_NAMES[h]} calls right in {int(items[f'hits_{h}'][i])} of its last {RECORD_CALLS}"
        for h in (2, 1, 0)
    )
    call = PHRASING[int(items["phrase"][i])].format(c=colour(items["call"][i]))
    # Tasks 0.21: "peer-open" gives no record, so the phrase and the call are the only cues.
    about = (
        f"{LAB_PEERS} {cap(who)} phrases each call in one of three ways, and the lab keeps its "
        f"record for each: {record}."
        if variant == "peer-a"
        else f"{LAB_PEERS} {cap(who)} phrases each call in one of three ways."
    )
    lines = [
        brief({"urn": urn(i)}, items["prior"][i], None, "any evidence"),
        about,
        *own_line(items, i),
        f"{cap(who)}'s call on {urn(i)}: “{call}”",
    ]
    return lines, f"What is the probability that {urn(i)} is red-majority?"


def _list(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def conformity(items, i, cover, variant):
    """T3: the respondent's own reading against n analysts who all call the opposite colour."""
    n = int(items["n"][i])
    status = int(items["status"][i])
    names = analysts(i)[:n]
    against = colour(-int(items["own"][i]))
    accuracy = base.percent(items["peer_acc"][i])
    lines = [brief({"urn": urn(i)}, items["prior"][i], None, "any evidence"), *own_line(items, i)]
    if n and variant == "peer-open":
        # Tasks 0.21: the majority's evidence is not described.
        everyone = {2: "both", 3: "all three", 4: "all four", 5: "all five"}.get(n, "")
        text = (
            f"{cap(_list(names))} each made a call on the urn, and {everyone} called it "
            f"{against}-majority."
            if n > 1
            else f"{cap(names[0])} made a call on the urn and called it {against}-majority."
        )
        lines.append(f"{LAB_PEERS} {text}")
    elif n:
        everyone = {2: "both", 3: "all three", 4: "all four", 5: "all five"}.get(n, "")
        if status == 0:
            text = (
                f"{cap(_list(names))} each read the urn with a sensor of their own, correct "
                f"{accuracy} of the time, and each called it {against}-majority."
                if n > 1
                else f"{cap(names[0])} read the urn with a sensor of its own, correct {accuracy} "
                f"of the time, and called it {against}-majority."
            )
        elif status == 1:
            text = (
                f"{cap(names[0])} read the urn with a sensor correct {accuracy} of the time and "
                f"called it {against}-majority. {cap(_list(names[1:]))} did not read the urn; "
                f"each passed on {names[0]}'s call, so {everyone} called it "
                f"{against}-majority."
                if n > 1
                else f"{cap(names[0])} read the urn with a sensor correct {accuracy} of the time "
                f"and called it {against}-majority."
            )
        else:
            text = (
                f"{cap(_list(names))} did not read the urn and had no other information about "
                f"it; each guessed, and {everyone} called it {against}-majority."
                if n > 1
                else f"{cap(names[0])} did not read the urn and had no other information about "
                f"it; it guessed, and called it {against}-majority."
            )
        lines.append(f"{LAB_PEERS} {text}")
    return lines, f"What is the probability that {urn(i)} is red-majority?"


def relay(items, i, cover, variant):
    """T4: a call that reaches the respondent through a chain of relays."""
    hops = int(items["hops"][i])
    names = analysts(i)[: hops + 1]
    origin = names[0]
    lines = [
        brief({"urn": urn(i)}, items["prior"][i], None, "any evidence"),
        f"{LAB_PEERS} {cap(origin)} reads urns with a sensor that is correct "
        f"{base.percent(items['acc'][i])} of the time, and calls the colour its sensor shows.",
    ]
    if hops and variant == "chain-stated":
        lines.append(
            "When an analyst passes on a call it was told, it passes it on unchanged in "
            f"{base.percent(items['fidelity'][i])} of rounds; in the other rounds it passes on a "
            "coin flip instead."
        )
    received = colour(items["call"][i])
    if hops == 0:
        lines.append(f"{cap(origin)} gave you its call on {urn(i)} directly: {received}-majority.")
    else:
        chain = " \u2192 ".join(names + ["you"])
        lines.append(
            f"{cap(origin)} made a call on {urn(i)}. It reached you through analysts who each "
            f"passed on what they were told: {chain}. The call as it reached you: "
            f"{received}-majority."
        )
    return lines, f"What is the probability that {urn(i)} is red-majority?"


def copying_peer(items, i, cover, variant):
    """T2: the copying design with analysts in place of sensors, and matched-strength audits."""
    names = analysts(i)
    p, q = names[0], names[1]
    kind, slot = items["kind"][i], int(items["slot"][i])
    lines = [brief({"urn": urn(i)}, items["prior"][i], None, "any calls")]
    rates = [
        f"{cap(p)} reads urns with a sensor that is correct "
        f"{base.percent(items['accuracy_a'][i])} of the time."
    ]
    calls = [f"{p}: {colour(items['report_a'][i])}-majority"]
    if kind != "single":
        rates.append(
            f"{cap(q)} reads urns with a sensor that is correct "
            f"{base.percent(items['accuracy_b'][i])} of the time."
        )
        calls.append(f"{q}: {colour(items['report_b'][i])}-majority")
    lines += [
        f"{LAB_PEERS} " + " ".join(rates),
        "Calls on this urn, in the order they were made: " + "; ".join(calls) + ".",
    ]
    if slot >= 0 and kind != "single":
        _, total = VIG_SCALES[variant]
        k = vig_count("copying", items, i, slot, variant)
        lines.append(
            f"Audit of {q}: in the last {total} rounds in which {q} and {p} both made calls on "
            f"the same urn, {q}'s call matched {p}'s in {k}."
        )
    return lines, f"What is the probability that {urn(i)} is red-majority?"


def percentages(module, items, i, variant=None):
    """Every probability a case must display, for the rendering audit."""
    values = [items["prior"][i]]
    if module == "advice-peer":
        if int(items["own"][i]):
            values.append(items["own_acc"][i])
    elif module == "conformity-peer":
        values.append(items["own_acc"][i])
        stated = variant != "peer-open"
        if stated and int(items["n"][i]) and int(items["status"][i]) < 2:
            values.append(items["peer_acc"][i])
    elif module == "relay-peer":
        values.append(items["acc"][i])
    else:
        values.append(items["accuracy_a"][i])
        if items["kind"][i] != "single":
            values.append(items["accuracy_b"][i])
    return sorted({base.percent(v) for v in values})
