"""Recover the evidence ledger from rendered text alone (0.3), and audit matched pairs.

Validity is judged only from each report's own figures: answer counts against respondents,
percentage shares against one hundred and against the counts, fieldwork dates, and whether the
stated margin of error is possible at that sample size. Register is read from the report form.
"""

import math
import re
from datetime import datetime

from epistemics.research_world3.render import BACKGROUND, MARGIN_CONSTANT
from epistemics.research_world3.world import PAIRS

POLISHED = re.compile(
    r"fielded a reseller survey for .+? from (?P<d1>[A-Z][a-z]+ \d{1,2}) to "
    r"(?P<d2>[A-Z][a-z]+ \d{1,2})\. Of (?P<n>\d+) resellers who responded, (?P<a>\d+) "
    r"\((?P<pa>\d+)%\) reported higher reorders than last quarter, (?P<b>\d+) \((?P<pb>\d+)%\) "
    r"flat and (?P<c>\d+) \((?P<pc>\d+)%\) lower\. At this sample size the margin of error is "
    r"about ±(?P<moe>\d+) points at 95% confidence\."
)
INFORMAL = re.compile(
    r"heard back from (?P<n>\d+) resellers between (?P<d1>[A-Z][a-z]{2} \d{1,2}) and "
    r"(?P<d2>[A-Z][a-z]{2} \d{1,2})\. (?P<a>\d+) say reorders up vs last qtr, (?P<b>\d+) flat, "
    r"(?P<c>\d+) down\."
)


def day(text, style):
    return datetime.strptime(f"{text} 2026", "%B %d %Y" if style == "polished" else "%b %d %Y")


def consistent(fields, style):
    n, counts = int(fields["n"]), [int(fields[k]) for k in ("a", "b", "c")]
    if sum(counts) != n or day(fields["d2"], style) < day(fields["d1"], style):
        return False
    if style == "polished":
        shares = [int(fields[k]) for k in ("pa", "pb", "pc")]
        if abs(sum(shares) - 100) > 2:
            return False
        if any(abs(s - 100 * c / n) > 1 for s, c in zip(shares, counts, strict=True)):
            return False
        if int(fields["moe"]) < 0.8 * MARGIN_CONSTANT / math.sqrt(n):
            return False
    return True


def extract(dossier):
    """Every survey report as (sample, register, valid, favorable), sorted."""
    if any(line not in dossier["case"] for line in BACKGROUND):
        raise ValueError("Every case brief states the same background facts")
    reports = []
    for doc in dossier["documents"]:
        for style, pattern in (("polished", POLISHED), ("informal", INFORMAL)):
            for m in pattern.finditer(doc["text"]):
                reports.append(
                    (
                        int(m["n"]),
                        style,
                        consistent(m.groupdict(), style),
                        int(m["a"]) > int(m["c"]),
                    )
                )
    return sorted(reports)


def ledger(world):
    reports = []
    for i in world.shown:
        atom = world.atom(i)
        reports.append(
            (
                atom.detail["sample"],
                "informal" if i in world.discounted else "polished",
                i not in world.invalid,
                atom.favorable,
            )
        )
    return sorted(reports)


def audit(worlds, dossiers):
    """Every dossier matches its ledger; matched pairs differ only in the report slot."""
    for presentation, world in worlds.items():
        if extract(dossiers[presentation]) != ledger(world):
            raise ValueError(f"Rendered {presentation} dossier does not match its ledger")
    family = next(iter(worlds.values())).family
    a, b = (dossiers[p] for p in PAIRS[family])
    if a["case"] != b["case"] or len(a["documents"]) != len(b["documents"]):
        raise ValueError("Matched dossiers differ outside the manipulated documents")
    differing = [x for x, y in zip(a["documents"], b["documents"], strict=True) if x != y]
    if len(differing) > 1:
        raise ValueError("Matched dossiers differ in more than the report slot")
    return True
