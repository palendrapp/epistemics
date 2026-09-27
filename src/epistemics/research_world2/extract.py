"""Recover the evidence ledger from rendered text alone (0.2), and audit matched pairs.

Relays carry no firm name. The extractor links each one to the survey it repeats through
sample size, publication date and direction, and requires its figure (exact or rounded) to be
consistent with that survey. Omitted KPIs are implied misses only through the general
background fact that companies never omit a KPI that met or beat guidance.
"""

import re

from epistemics.research_world2.render import BACKGROUND, rounded
from epistemics.research_world2.world import PAIRS

DAY = r"(?P<day>[A-Z][a-z]+ \d{1,2})"
KPI = re.compile(
    r"(?P<name>[A-Z][a-z ]+?) came in at (?P<actual>[^,]+), (?P<verb>ahead of|short of) "
    r"guidance of (?P<guidance>.+?)\.(?= |$)"
)
COVERED = re.compile(
    r"each of its quarterly letters has covered the same (?P<count>two|three|four) KPIs: "
    r"(?P<names>[^.]+)\."
)
WORDS = {"two": 2, "three": 3, "four": 4}
OWN = re.compile(
    rf"Our reseller survey, published {DAY}: of (?P<sample>\d+) resellers of .+?, (?P<k>\d+) "
    r"reported (?P<direction>higher|lower) reorders"
)
RELAYS = (
    re.compile(
        rf"according to a survey of (?P<sample>\d+) resellers published on {DAY}: (?P<k>\d+) "
        r"reported (?P<direction>higher|lower) reorders"
    ),
    re.compile(
        rf"roughly (?P<phrase>[a-z -]+?) of the (?P<sample>\d+) resellers in a survey published "
        rf"{DAY} said reorders were (?P<updown>up|down)"
    ),
    re.compile(
        rf"reseller survey on .+? from {DAY}\? (?P<k>\d+)/(?P<sample>\d+) reporting "
        r"(?P<direction>higher|lower) reorders"
    ),
    re.compile(
        rf"discussed a survey from {DAY} of (?P<sample>\d+) .+? resellers in which roughly "
        r"(?P<phrase>[a-z -]+?) reported (?P<direction>higher|lower) reorders"
    ),
)


def extract(dossier):
    """Return {'shown': {key: favorable}, 'implied': {key: favorable}, 'mentions': {key: n}}."""
    if any(line not in dossier["case"] for line in BACKGROUND):
        raise ValueError("Every case brief states the same background facts")
    shown, implied, mentions, counts = {}, {}, {}, {}
    covered = None
    relays = []
    for doc in dossier["documents"]:
        text = doc["text"]
        for m in KPI.finditer(text):
            key = ("kpi", m["name"].lower())
            shown[key] = m["verb"] == "ahead of"
            mentions[key] = mentions.get(key, 0) + 1
        if m := COVERED.search(text):
            covered = [name.strip() for name in m["names"].split(",")]
            if len(covered) != WORDS[m["count"]]:
                raise ValueError("Covered KPI count disagrees with the listed names")
        for m in OWN.finditer(text):
            key = ("check", m["day"], int(m["sample"]), m["direction"])
            if key in shown:
                raise ValueError("Two surveys share a date, sample and direction")
            shown[key] = m["direction"] == "higher"
            mentions[key] = 1
            counts[key] = int(m["k"])
        for pattern in RELAYS:
            for m in pattern.finditer(text):
                direction = m.groupdict().get("direction") or (
                    "higher" if m["updown"] == "up" else "lower"
                )
                relays.append((m["day"], int(m["sample"]), direction, m.groupdict()))
    for day, sample, direction, groups in relays:
        key = ("check", day, sample, direction)
        if key not in counts:
            raise ValueError("A relay repeats no survey in the dossier")
        k = counts[key]
        if groups.get("k") is not None and int(groups["k"]) != k:
            raise ValueError("A relay's exact figure disagrees with its survey")
        if groups.get("phrase") is not None and groups["phrase"] != rounded(k / sample):
            raise ValueError("A relay's rounded figure disagrees with its survey")
        mentions[key] += 1
    if covered is not None:
        stated = {name for kind, name, *_ in shown if kind == "kpi"}
        if not stated <= set(covered):
            raise ValueError("The letter reports a KPI the company has never covered")
        implied = {("kpi", name): False for name in covered if name not in stated}
    return {"shown": shown, "implied": implied, "mentions": mentions, "counts": counts}


def normalize(summary):
    """Firm names and dates are rendering choices; compare checks by sample, count, direction."""
    return {
        "kpi_shown": {k[1]: v for k, v in summary["shown"].items() if k[0] == "kpi"},
        "kpi_implied": {k[1]: v for k, v in summary["implied"].items() if k[0] == "kpi"},
        "checks": sorted(
            (k[2], summary["counts"][k], k[3], v, summary["mentions"][k])
            for k, v in summary["shown"].items()
            if k[0] == "check"
        ),
    }


def ledger(world):
    """The normalized summary computed from the private world."""
    result = {"kpi_shown": {}, "kpi_implied": {}, "checks": []}
    for i in world.shown:
        atom = world.atom(i)
        if atom.kind == "kpi":
            result["kpi_shown"][atom.name] = atom.favorable
        else:
            d = atom.detail
            k = d["count"] if atom.favorable else d["sample"] - d["count"]
            direction = "higher" if atom.favorable else "lower"
            result["checks"].append((d["sample"], k, direction, atom.favorable, world.mentions[i]))
    for i in world.implied:
        result["kpi_implied"][world.atom(i).name] = world.atom(i).favorable
    result["checks"].sort()
    return result


def audit(worlds, dossiers):
    """Every dossier matches its ledger; matched pairs differ only in manipulated slots."""
    for presentation, world in worlds.items():
        if normalize(extract(dossiers[presentation])) != ledger(world):
            raise ValueError(f"Rendered {presentation} dossier does not match its ledger")
    family = next(iter(worlds.values())).family
    a, b = (dossiers[p] for p in PAIRS[family])
    if a["case"] != b["case"] or len(a["documents"]) != len(b["documents"]):
        raise ValueError("Matched dossiers differ outside the manipulated documents")
    differing = [x for x, y in zip(a["documents"], b["documents"], strict=True) if x != y]
    limit = 1 if family == "disclosure" else 4
    if len(differing) > limit:
        raise ValueError("Matched dossiers differ in more slots than the manipulation")
    return True
