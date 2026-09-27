"""Private research worlds (0.3): register versus validity of survey reports.

Every dossier synthesizes several reseller surveys. In the validity family a polished report
may be internally impossible, hence fabricated and uninformative; in the register family a valid
report may be written up informally. Evidence patterns are chosen by design; demand is then drawn
from its exact posterior given every genuine survey, so a fabricated report never touches demand.
"""

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from epistemics.models import Model
from epistemics.research_world3 import VERSION

Family = Literal["validity", "register"]
Presentation = Literal["omitted", "invalid", "valid", "polished", "sloppy", "absent"]
PAIRS = {"validity": ("omitted", "invalid"), "register": ("polished", "sloppy")}
ANCHORS = {"validity": "valid", "register": "absent"}
CHECK_RATES = (0.70, 0.30)
PRIORS = (0.2, 0.5, 0.8)
THRESHOLDS = (0.3, 0.7)
MARKERS = ("counts", "percentages", "dates", "margin")


class Atom(Model):
    atom_id: str
    kind: Literal["survey"]
    name: str
    favorable: bool
    p_favorable_strong: float = Field(gt=0, lt=1)
    p_favorable_weak: float = Field(gt=0, lt=1)
    detail: dict

    def log_likelihood_ratio(self):
        if self.favorable:
            return math.log(self.p_favorable_strong / self.p_favorable_weak)
        return math.log((1 - self.p_favorable_strong) / (1 - self.p_favorable_weak))


class World(Model):
    schema_version: Literal["epistemics.research-world.v3"] = "epistemics.research-world.v3"
    version: Literal["research-world/0.3.0"] = VERSION
    world_id: str
    pair_seed: int = Field(ge=0)
    family: Family
    presentation: Presentation
    prior_strong: float = Field(gt=0, lt=1)
    threshold: float = Field(gt=0, lt=1)
    atoms: list[Atom] = Field(min_length=1)
    shown: list[str]
    implied: list[str]
    mentions: dict[str, int]
    invalid: list[str] = []
    discounted: list[str] = []
    strong: bool

    @model_validator(mode="after")
    def coherent(self):
        ids = [a.atom_id for a in self.atoms]
        if len(set(ids)) != len(ids) or set(self.shown) & set(self.implied):
            raise ValueError("Atoms must be unique and either shown or implied")
        if not set(self.shown) | set(self.implied) <= set(ids):
            raise ValueError("Shown and implied atoms must exist in the world")
        if set(self.mentions) != set(self.shown) or min(self.mentions.values()) < 1:
            raise ValueError("Every shown atom has at least one document mention")
        if not set(self.invalid) | set(self.discounted) <= set(self.shown):
            raise ValueError("Invalid and discounted reports must be shown")
        if set(self.invalid) & set(self.discounted):
            raise ValueError("A report is either fabricated or informally written, not both")
        if self.presentation not in (*PAIRS[self.family], ANCHORS[self.family]):
            raise ValueError("Presentation does not belong to this family")
        return self

    def atom(self, atom_id):
        return next(a for a in self.atoms if a.atom_id == atom_id)


def logit(p):
    return math.log(p / (1 - p))


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def normative_logit(world):
    """Posterior log-odds for a reader who checks figures and ignores register."""
    return logit(world.prior_strong) + sum(
        world.atom(i).log_likelihood_ratio()
        for i in (*world.shown, *world.implied)
        if i not in world.invalid
    )


def naive_logit(world):
    """Takes every report at face value, but drops one that is written up informally."""
    return logit(world.prior_strong) + sum(
        world.mentions[i] * world.atom(i).log_likelihood_ratio()
        for i in world.shown
        if i not in world.discounted
    )


def _survey(rng, index, favorable, marker=None):
    """Counts of higher, flat and lower reorders; an optional impossibility marker."""
    sample = int(rng.choice((24, 30, 36, 40)))
    while True:
        higher = int(rng.integers(0, sample + 1))
        lower = int(rng.integers(0, sample - higher + 1))
        flat = sample - higher - lower
        if (higher > lower) == favorable and abs(higher - lower) >= 3 and flat >= 2:
            break
    start = int(rng.integers(0, 10))
    return Atom(
        atom_id=f"survey-{index + 1}",
        kind="survey",
        name=f"survey-{index + 1}",
        favorable=favorable,
        p_favorable_strong=CHECK_RATES[0],
        p_favorable_weak=CHECK_RATES[1],
        detail={
            "sample": sample,
            "higher": higher,
            "flat": flat,
            "lower": lower,
            "field_start": start,
            "field_days": int(rng.integers(6, 15)),
            "marker": marker,
            "excess": int(rng.integers(5, 10)),
        },
    )


def _world(pair_seed, family, presentation, prior, threshold, atoms, invalid, discounted, rng):
    draft = World(
        world_id=f"rw3-{pair_seed}-{presentation}",
        pair_seed=pair_seed,
        family=family,
        presentation=presentation,
        prior_strong=prior,
        threshold=threshold,
        atoms=atoms,
        shown=[a.atom_id for a in atoms],
        implied=[],
        mentions={a.atom_id: 1 for a in atoms},
        invalid=invalid,
        discounted=discounted,
        strong=False,
    )
    # Demand depends only on genuine surveys; a fabricated report is independent of it.
    genuine = logit(prior) + sum(
        a.log_likelihood_ratio() for a in atoms if a.atom_id not in invalid
    )
    return draft.model_copy(update={"strong": bool(rng.random() < sigmoid(genuine))})


def generate(pair_seed, family):
    """Matched presentations sharing one world, plus the family's scale anchor."""
    if not isinstance(pair_seed, int) or isinstance(pair_seed, bool) or pair_seed < 0:
        raise ValueError("Seed must be a nonnegative integer")
    if family not in PAIRS:
        raise ValueError("Unknown family")
    rng = np.random.default_rng([pair_seed, 3, 0 if family == "validity" else 1])
    prior = float(rng.choice(PRIORS))
    threshold = float(rng.choice(THRESHOLDS))
    base = [_survey(rng, i, bool(rng.random() < 0.5)) for i in range(2)]
    marker = MARKERS[int(rng.integers(len(MARKERS)))] if family == "validity" else None
    report = _survey(rng, 2, bool(rng.random() < 0.5), marker)
    worlds = {}
    if family == "validity":
        for presentation, atoms, invalid in (
            ("omitted", base, []),
            ("invalid", [*base, report], [report.atom_id]),
        ):
            worlds[presentation] = _world(
                pair_seed, family, presentation, prior, threshold, atoms, invalid, [],
                np.random.default_rng([pair_seed, 3, 2]),
            )  # fmt: skip
        genuine = report.model_copy(update={"detail": {**report.detail, "marker": None}})
        worlds["valid"] = _world(
            pair_seed, family, "valid", prior, threshold, [*base, genuine], [], [],
            np.random.default_rng([pair_seed, 3, 3]),
        )  # fmt: skip
    else:
        for presentation, discounted in (("polished", []), ("sloppy", [report.atom_id])):
            worlds[presentation] = _world(
                pair_seed, family, presentation, prior, threshold, [*base, report], [],
                discounted, np.random.default_rng([pair_seed, 3, 2]),
            )  # fmt: skip
        worlds["absent"] = _world(
            pair_seed, family, "absent", prior, threshold, base, [], [],
            np.random.default_rng([pair_seed, 3, 3]),
        )  # fmt: skip
    a, b = PAIRS[family]
    if worlds[a].strong != worlds[b].strong or not math.isclose(
        normative_logit(worlds[a]), normative_logit(worlds[b])
    ):
        raise ValueError("Matched presentations must share one world and posterior")
    return worlds
