"""Open-inference screen texts (tasks 0.26; docs/open-inference-screen-design.md).

Renders dispositions.screen items. Open items state only data (examples, a reported number, what
another agent did, a list of causes, a few readings); anchors add the sentence that fixes the
answer. No case states a rate, an accuracy or a percentage.
"""

from epistemics.dispositions import screen


def ident(i):
    return 11 + i


def listing(parts):
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


# F1. (intro for several values, intro for one, verb, rule sentence for anchors, noun)
GEN = {
    0: (
        "A process produced these values",
        "A process produced this value",
        "produce",
        "It produces exactly the {rule}, and nothing else.",
        "values",
    ),
    1: (
        "A door lock accepted these codes",
        "A door lock accepted this code",
        "accept the code",
        "It accepts exactly the {rule}, and nothing else.",
        "codes",
    ),
    2: (
        "A system issued these ticket numbers",
        "A system issued this ticket number",
        "issue ticket number",
        "It issues exactly the {rule}, and nothing else.",
        "ticket numbers",
    ),
    3: (
        "A sensor reported on these channels",
        "A sensor reported on this channel",
        "report on channel",
        "It reports on exactly the {rule}, and nothing else.",
        "channels",
    ),
}


def _gen(items, i, d):
    many, one, verb, rule, noun = GEN[int(items["surface"][i])]
    values = ", ".join(str(v) for v in d["examples"])
    lines = [
        f"{many if len(d['examples']) > 1 else one}: {values}.",
        f"All {noun} are whole numbers from 1 to 100.",
    ]
    if "rule" in d:
        lines.append(rule.format(rule=d["rule"]))
    return lines, f"What is the probability that it could also {verb} {d['probe']}?"


# F2. (person report, instrument report, question predicate, "fewer" or "less")
NUMBERS = {
    0: (
        "{who} says the transfer took {v} minutes.",
        "The job timer shows the transfer took {v} minutes.",
        "the transfer actually took {range} minutes",
        "less",
    ),
    1: (
        "{who} says the crate weighs {v} kg.",
        "The scale shows the crate weighs {v} kg.",
        "the crate actually weighs {range} kg",
        "less",
    ),
    2: (
        "{who} says the route is {v} km long.",
        "The vehicle's odometer shows the route is {v} km long.",
        "the route is actually {range} km long",
        "less",
    ),
    3: (
        "{who} says there are {v} boxes in the store.",
        "The inventory counter shows {v} boxes in the store.",
        "there are actually {range} boxes in the store",
        "fewer",
    ),
    4: (
        "{who} says the tank holds {v} litres.",
        "The flow meter shows the tank holds {v} litres.",
        "the tank actually holds {range} litres",
        "less",
    ),
    5: (
        "{who} says {v} people attended the open day.",
        "The door counter recorded {v} people at the open day.",
        "{range} people actually attended the open day",
        "fewer",
    ),
}
SPEAKERS = ("A colleague", "The site manager", "A contractor", "Another analyst")
ROUNDING = {
    1: "The scale rounds to the nearest 10 kg.",
    4: "The flow meter rounds to the nearest 10 litres.",
}
EXACT = {
    3: "The inventory system records every box scanned in or out, and nothing has moved since."
}


def _num(items, i, d):
    person, instrument, predicate, fewer = NUMBERS[d["quantity"]]
    if "anchor" in d:
        kind, *bounds = d["bounds"]
        if d["anchor"] == "rounds":
            lines = [ROUNDING[d["quantity"]], instrument.format(v=d["value"])]
        else:
            lines = [EXACT[d["quantity"]], instrument.format(v=f"exactly {d['value']}")]
        span = {
            "between": lambda: f"between {bounds[0]} and {bounds[1]}",
            "above": lambda: f"more than {bounds[0]}",
            "below": lambda: f"{fewer} than {bounds[0]}",
        }[kind]()
    else:
        if d["source"] == "instrument":
            lines = [instrument.format(v=d["value"])]
        else:
            lines = [person.format(who=SPEAKERS[d["speaker"]], v=d["value"])]
        lo, hi = d["window"]
        span = f"between {lo} and {hi}"
    return lines, f"What is the probability that {predicate.format(range=span)}?"


# F3. Per domain: actors (person, agent), object, predicate, decision, checks by form (trivial,
# moderate, large), and the sentence that establishes knowledge (anchors).
CHOICE = {
    0: {
        "actors": ("The inspector", "Agent K7"),
        "object": "shipment batch B{id}",
        "predicate": "was sound",
        "decision": "signed B{id} off as sound",
        "checks": {
            "a": (
                "a quick visual check of B{id} on the way to the loading bay",
                "a sample test of B{id} that would have taken the rest of the afternoon",
                "a full laboratory test of B{id} that would have delayed the shipment by a week",
            ),
            "b": (
                "a quick check of B{id}'s seals while passing",
                "a sample test of B{id} that would have taken most of the day",
                "an external laboratory test of B{id} that would have held the shipment for a week",
            ),
        },
        "knew": "had tested B{id} an hour earlier and recorded it as sound",
    },
    1: {
        "actors": ("The engineer", "Agent R2"),
        "object": "pump P{id}",
        "predicate": "was working",
        "decision": "signed P{id} off as working",
        "checks": {
            "a": (
                "a quick check of P{id}'s pressure gauge while passing",
                "a pressure test of P{id} that would have taken the rest of the afternoon",
                "a strip-down inspection that would have taken P{id} out of service for a week",
            ),
            "b": (
                "a quick vibration check of P{id} on the way past",
                "a flow test of P{id} that would have taken most of the day",
                "a full overhaul inspection that would have stopped P{id} for a week",
            ),
        },
        "knew": "had pressure-tested P{id} an hour earlier and recorded it as working",
    },
    2: {
        "actors": ("The ecologist", "Agent E4"),
        "object": "survey site S{id}",
        "predicate": "had no otters present",
        "decision": "approved the works at S{id}",
        "checks": {
            "a": (
                "a quick check for tracks on the riverbank at S{id} on the way",
                "a camera survey of S{id} that would have taken the rest of the afternoon to set up",
                "a full survey of S{id} that would have delayed the works by a week",
            ),
            "b": (
                "a quick check along the bank at S{id} while passing",
                "a survey for droppings at S{id} that would have taken most of the day",
                "a licensed survey of S{id} that would have held up the works for a week",
            ),
        },
        "knew": "had surveyed S{id} an hour earlier and recorded no otters present",
    },
    3: {
        "actors": ("The on-call engineer", "Agent N9"),
        "object": "server X{id}",
        "predicate": "was healthy",
        "decision": "marked X{id} as healthy",
        "checks": {
            "a": (
                "a quick check of X{id}'s status page",
                "a diagnostic run on X{id} that would have taken the rest of the afternoon",
                "a full hardware audit that would have kept X{id} offline for a week",
            ),
            "b": (
                "a quick check of X{id}'s dashboard",
                "a load test of X{id} that would have taken most of the day",
                "a vendor audit that would have kept X{id} out of service for a week",
            ),
        },
        "knew": "had run a full diagnostic on X{id} an hour earlier and recorded it as healthy",
    },
    4: {
        "actors": ("The planner", "Agent P3"),
        "object": "product line R{id}",
        "predicate": "would see high demand",
        "decision": "placed the large production order for R{id}",
        "checks": {
            "a": (
                "a quick check of this week's orders for R{id}",
                "a customer survey on R{id} that would have taken the rest of the afternoon",
                "a market study of R{id} that would have delayed the order by a week",
            ),
            "b": (
                "a quick check of R{id}'s recent sales",
                "a phone survey of key customers about R{id} that would have taken most of the day",
                "a commissioned market study of R{id} that would have held the order for a week",
            ),
        },
        "knew": "had received confirmed orders an hour earlier showing that R{id} would see high demand",
    },
}


def _choice(items, i, d):
    spec = CHOICE[d["domain"]]
    k = ident(i)
    actor = spec["actors"][d["actor"]]
    lower = actor if d["actor"] else actor[0].lower() + actor[1:]
    pronoun = ("They", "It")[d["actor"]]
    obj = spec["object"].format(id=k)
    check = spec["checks"][d["form"]][d["cost"]].format(id=k)
    decision = spec["decision"].format(id=k)
    lines = [f"{actor} had to decide whether {obj} {spec['predicate']}."]
    if items["kind"][i] == "anchor" and d["action"] == "skipped":
        lines.insert(0, f"{actor} {spec['knew'].format(id=k)}.")
        lines[1] = f"Now {lower} had to decide again whether {obj} {spec['predicate']}."
    if d["action"] == "skipped":
        lines += [
            f"{pronoun} could have carried out {check}.",
            f"{pronoun} did not, and {decision}.",
        ]
        when = "before deciding"
    else:
        if items["kind"][i] == "anchor":
            lines.append(f"{pronoun} had no information at all about {obj} before the check.")
        done = check.replace("would have taken", "took")  # taken checks are the moderate ones
        lines += [f"{pronoun} carried out {done}, and then {decision}."]
        when = "before the check"
    question = (
        f"What is the probability that {lower} already knew that {obj} {spec['predicate']} {when}?"
    )
    return lines, question


# F4. Per domain: event, causes, the manual that lists causes, and the record (anchors).
LISTS = {
    0: (
        "Pump P{id} stopped this morning.",
        (
            "a blocked intake",
            "a failed seal",
            "a power fault",
            "a worn impeller",
            "a control fault",
        ),
        "The maintenance manual lists these causes of a pump stopping",
        "The pump's control system records that exactly one of these causes stopped it, and that each is equally likely",
    ),
    1: (
        "Shipment batch B{id} failed its quality check.",
        (
            "contaminated raw material",
            "a miscalibrated filling machine",
            "the wrong storage temperature",
            "damaged packaging",
            "a labelling error",
        ),
        "The quality handbook lists these causes of a failed check",
        "The quality record shows that exactly one of these causes failed it, and that each is equally likely",
    ),
    2: (
        "No otter signs were found at survey site S{id} this month, after signs every month last year.",
        (
            "the otters moving upstream",
            "flooding washing the signs away",
            "the survey being done too soon after rain",
            "a trail camera failing",
            "disturbance from nearby works",
        ),
        "The survey guidance lists these causes of signs disappearing",
        "The survey record shows that exactly one of these causes explains it, and that each is equally likely",
    ),
    3: (
        "Server X{id} went down overnight.",
        (
            "memory exhaustion",
            "a disk failure",
            "a network partition",
            "a faulty deployment",
            "an expired certificate",
        ),
        "The operations runbook lists these causes of an overnight outage",
        "The server's monitoring records that exactly one of these causes brought it down, and that each is equally likely",
    ),
    4: (
        "Orders for product line R{id} fell sharply this month.",
        (
            "a competitor's price cut",
            "a seasonal dip",
            "a shortage at the main retailer",
            "a rumour of a recall",
            "the loss of a major customer",
        ),
        "The sales playbook lists these causes of a sharp fall in orders",
        "The sales record shows that exactly one of these causes explains it, and that each is equally likely",
    ),
}


def listed(d):
    causes = LISTS[d["domain"]][1]
    r = d["rotate"]
    rotated = causes[r:] + causes[:r]
    return list(rotated[: d["k"]])


def _lists(items, i, d):
    event, _, manual, record = LISTS[d["domain"]]
    causes = listed(d)
    if d.get("exhaustive"):
        source = record
    elif d["source"] == "manual":
        source = manual
    else:
        source = "A colleague suggests these possible causes"
    lines = [event.format(id=ident(i)), f"{source}: {listing(causes)}."]
    if d["question"] == "none":
        return lines, "What is the probability that the cause was none of these?"
    asked = causes[d["rotate"] % d["k"]]
    return lines, f"What is the probability that the cause was {asked}?"


# F5. Per surface: readings sentence, question predicate for "above", for "within", and the
# exact-rule sentence (anchors).
TREND = {
    0: (
        "The level in tank T{id} read {a} cm after one hour, {b} cm after two hours and {c} cm after three hours.",
        "it will read above {t} cm after {x} hours",
        "it will read between {lo} and {hi} cm after {x} hours",
        "The level rises by exactly {step} cm every hour.",
    ),
    1: (
        "Support queue Q{id} had {a} open tickets after one day, {b} after two days and {c} after three days.",
        "it will have more than {t} open tickets after {x} days",
        "it will have between {lo} and {hi} open tickets after {x} days",
        "The queue grows by exactly {step} tickets every day.",
    ),
    2: (
        "Archive A{id} used {a} GB after one week, {b} GB after two weeks and {c} GB after three weeks.",
        "it will use more than {t} GB after {x} weeks",
        "it will use between {lo} and {hi} GB after {x} weeks",
        "Its usage grows by exactly {step} GB every week.",
    ),
    3: (
        "Service V{id} had {a} registered users after one month, {b} after two months and {c} after three months.",
        "it will have more than {t} registered users after {x} months",
        "it will have between {lo} and {hi} registered users after {x} months",
        "It gains exactly {step} registered users every month.",
    ),
    4: (
        "Warehouse W{id} had processed {a} orders by the end of the first hour, {b} by the end of the second and {c} by the end of the third.",
        "it will have processed more than {t} orders by the end of hour {x}",
        "it will have processed between {lo} and {hi} orders by the end of hour {x}",
        "It processes exactly {step} orders every hour.",
    ),
}


def _trend(items, i, d):
    readings, above, within, exact = TREND[d["surface"]]
    a, b, c = d["ys"]
    lines = [readings.format(id=ident(i), a=a, b=b, c=c)]
    if d.get("exact"):
        lines.append(exact.format(step=b - a))
    if d["question"] == "above":
        predicate = above.format(t=d["threshold"], x=d["x"])
    else:
        lo, hi = d["window"]
        predicate = within.format(lo=lo, hi=hi, x=d["x"])
    return lines, f"What is the probability that {predicate}?"


RENDER = {"gen": _gen, "num": _num, "choice": _choice, "lists": _lists, "trend": _trend}


def trial(items, i, cover, variant):
    family = str(items["family"][i])
    return RENDER[family](items, i, screen.data(items, i))
