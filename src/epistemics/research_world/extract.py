"""Recover the evidence ledger from rendered text alone, and audit matched pairs.

The extractor reads only the public dossier. A dossier passes when the atoms it states,
the atoms its stated disclosure rule implies, and the mentions of each atom equal the
private ledger. Matched presentations must also share everything but the manipulation.
"""

import re

from epistemics.research_world.world import PAIRS

KPI = re.compile(
    r"(?P<name>[A-Z][a-z ]+?) came in at (?P<actual>[^,]+), (?P<verb>ahead of|short of) "
    r"guidance of (?P<guidance>.+?)\.(?= |$)"
)
TRACKED = re.compile(r"tracks (?P<count>two|three|four) operating KPIs \((?P<names>[^)]+)\)")
WORDS = {"two": 2, "three": 3, "four": 4}
SELECTIVE = "discusses only the KPIs that met or exceeded guidance"
COMPLETE = re.compile(r"reports (all|each) of them against guidance")
OWN_CHECK = re.compile(
    r"Our channel check of (?P<sample>\d+) resellers of (?P<company>.+?) found (?P<k>\d+) "
    r"reporting (?P<direction>higher|lower) reorders"
)
RELAYED_CHECKS = (
    re.compile(
        r"(?P<company>.+?) resellers are reordering (?:more|less): (?P<k>\d+) of (?P<sample>\d+) "
        r"surveyed by (?P<firm>.+?) reported (?P<direction>higher|lower) reorders than last "
        r"quarter, the firm said in a note on"
    ),
    re.compile(
        r"Worth a look: (?P<firm>.+?)(?:'s|') reseller survey for (?P<company>.+?) \((?P<k>\d+) "
        r"of (?P<sample>\d+) reporting (?P<direction>higher|lower) reorders\)"
    ),
)


def extract(dossier):
    """Return {'shown': {key: favorable}, 'implied': {key: favorable}, 'mentions': {key: n}}."""
    shown, implied, mentions = {}, {}, {}
    tracked, rule = None, None
    for doc in dossier["documents"]:
        text = doc["text"]
        for m in KPI.finditer(text):
            key = ("kpi", m["name"].lower())
            shown[key] = m["verb"] == "ahead of"
            mentions[key] = mentions.get(key, 0) + 1
        if m := TRACKED.search(text):
            tracked = [name.strip() for name in m["names"].split(",")]
            if len(tracked) != WORDS[m["count"]]:
                raise ValueError("Tracked KPI count disagrees with the listed names")
            if SELECTIVE in text:
                rule = "selective"
            elif COMPLETE.search(text):
                rule = "complete"
            else:
                raise ValueError("A tracked-KPI statement must state the disclosure practice")
        for m in OWN_CHECK.finditer(text):
            key = ("check", doc["source"], int(m["sample"]), int(m["k"]), m["direction"])
            shown[key] = m["direction"] == "higher"
            mentions[key] = mentions.get(key, 0) + 1
        for pattern in RELAYED_CHECKS:
            for m in pattern.finditer(text):
                key = ("check", m["firm"], int(m["sample"]), int(m["k"]), m["direction"])
                shown[key] = m["direction"] == "higher"
                mentions[key] = mentions.get(key, 0) + 1
    if tracked is not None:
        stated = {name for kind, name, *_ in shown if kind == "kpi"}
        if not stated <= set(tracked):
            raise ValueError("The letter reports a KPI that is not tracked")
        missing = [name for name in tracked if name not in stated]
        if rule == "selective":
            implied = {("kpi", name): False for name in missing}
        elif missing:
            raise ValueError("A complete-disclosure dossier omits a tracked KPI")
    return {"shown": shown, "implied": implied, "mentions": mentions}


def normalize(summary):
    """Firm names are rendering choices; compare checks by sample, count and direction."""
    return {
        "kpi_shown": {k[1]: v for k, v in summary["shown"].items() if k[0] == "kpi"},
        "kpi_implied": {k[1]: v for k, v in summary["implied"].items() if k[0] == "kpi"},
        "checks": sorted(
            (k[2], k[3], k[4], v, summary["mentions"][k])
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
    """Every dossier matches its ledger; matched pairs share all but the manipulation."""
    for presentation, world in worlds.items():
        if normalize(extract(dossiers[presentation])) != ledger(world):
            raise ValueError(f"Rendered {presentation} dossier does not match its ledger")
    a, b = (dossiers[p] for p in PAIRS[next(iter(worlds.values())).family])
    if a["case"] != b["case"] or len(a["documents"]) != len(b["documents"]):
        raise ValueError("Matched dossiers differ outside the manipulated documents")
    for x, y in zip(a["documents"], b["documents"], strict=True):
        if x["doc_id"] != y["doc_id"] or x["date"] != y["date"]:
            raise ValueError("Matched dossiers must keep document order and dates")
    return True
