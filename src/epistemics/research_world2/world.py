"""Private research worlds (0.2): binary evidence atoms, provenance and disclosure rules.

Evidence patterns are chosen by design. Demand is then drawn from its exact posterior given
every atom in the world, including undisclosed ones, so outcome scores remain valid for the
generated distribution. Matched presentations share atoms and demand; anchors do not.
"""

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from epistemics.models import Model
from epistemics.research_world2 import VERSION

Family = Literal["disclosure", "shared_origin"]
Presentation = Literal["full", "selected", "silent_control", "single", "relayed", "independent"]
PAIRS = {"disclosure": ("full", "selected"), "shared_origin": ("single", "relayed")}
ANCHORS = {"disclosure": "silent_control", "shared_origin": "independent"}

# Higher values are better for every KPI in this version; a beat means actual >= guidance.
KPIS = (
    ("net revenue retention", "%", (108, 118)),
    ("new enterprise customers", "", (40, 90)),
    ("gross margin", "%", (60, 75)),
    ("pipeline coverage", "x", (2.5, 4.0)),
    ("active reseller count", "", (300, 900)),
    ("average contract value", "$k", (40, 120)),
)
KPI_RATES = ((0.75, 0.35), (0.70, 0.30), (0.80, 0.40), (0.70, 0.35))
CHECK_RATES = (0.70, 0.30)
PRIORS = (0.2, 0.5, 0.8)
THRESHOLDS = (0.3, 0.7)


class Atom(Model):
    atom_id: str
    kind: Literal["kpi", "channel_check"]
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
    schema_version: Literal["epistemics.research-world.v2"] = "epistemics.research-world.v2"
    version: Literal["research-world/0.2.0"] = VERSION
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
    """Posterior log-odds for a reader who knows the stated rules and provenance."""
    return logit(world.prior_strong) + sum(
        world.atom(i).log_likelihood_ratio() for i in (*world.shown, *world.implied)
    )


def naive_logit(world):
    """Counts every mention as new evidence and ignores what a disclosure rule implies."""
    return logit(world.prior_strong) + sum(
        world.mentions[i] * world.atom(i).log_likelihood_ratio() for i in world.shown
    )


def _kpi(rng, index, spec, rates, favorable):
    name, unit, (low, high) = spec
    step = 0.1 if unit == "x" else 1
    guidance = round(float(rng.uniform(low, high)) / step) * step
    delta = step * int(rng.integers(1, 6))
    actual = guidance + delta if favorable else guidance - delta
    return Atom(
        atom_id=f"kpi-{index + 1}",
        kind="kpi",
        name=name,
        favorable=favorable,
        p_favorable_strong=rates[0],
        p_favorable_weak=rates[1],
        detail={"unit": unit, "guidance": round(guidance, 1), "actual": round(actual, 1)},
    )


def _check(rng, index, favorable):
    sample = int(rng.choice((24, 30, 36, 40)))
    share = rng.uniform(0.62, 0.8) if favorable else rng.uniform(0.2, 0.38)
    return Atom(
        atom_id=f"check-{index + 1}",
        kind="channel_check",
        name=f"check-{index + 1}",
        favorable=favorable,
        p_favorable_strong=CHECK_RATES[0],
        p_favorable_weak=CHECK_RATES[1],
        detail={"sample": sample, "count": round(sample * share)},
    )


def _world(pair_seed, family, presentation, prior, threshold, atoms, shown, implied, mentions, rng):
    draft = World(
        world_id=f"rw-{pair_seed}-{presentation}",
        pair_seed=pair_seed,
        family=family,
        presentation=presentation,
        prior_strong=prior,
        threshold=threshold,
        atoms=atoms,
        shown=shown,
        implied=implied,
        mentions=mentions,
        strong=False,
    )
    # Demand depends on every atom in the world, including any that go undisclosed.
    everything = logit(prior) + sum(a.log_likelihood_ratio() for a in atoms)
    return draft.model_copy(update={"strong": bool(rng.random() < sigmoid(everything))})


def generate(pair_seed, family):
    """Matched presentations sharing one world, plus the family's scale anchor."""
    if not isinstance(pair_seed, int) or isinstance(pair_seed, bool) or pair_seed < 0:
        raise ValueError("Seed must be a nonnegative integer")
    rng = np.random.default_rng([pair_seed, 0 if family == "disclosure" else 1])
    prior = float(rng.choice(PRIORS))
    threshold = float(rng.choice(THRESHOLDS))
    worlds = {}
    if family == "disclosure":
        specs = [KPIS[int(i)] for i in rng.permutation(len(KPIS))[:4]]
        rates = [KPI_RATES[int(i)] for i in rng.permutation(len(KPI_RATES))]
        misses = int(rng.choice((1, 2)))
        missing = set(int(i) for i in rng.permutation(4)[:misses])
        atoms = [_kpi(rng, i, specs[i], rates[i], i not in missing) for i in range(4)]
        beats = [a.atom_id for a in atoms if a.favorable]
        for presentation in PAIRS[family]:
            selected = presentation == "selected"
            worlds[presentation] = _world(
                pair_seed,
                family,
                presentation,
                prior,
                threshold,
                atoms,
                beats if selected else [a.atom_id for a in atoms],
                [a.atom_id for a in atoms if not a.favorable] if selected else [],
                {i: 1 for i in (beats if selected else [a.atom_id for a in atoms])},
                np.random.default_rng([pair_seed, 2]),
            )
        anchor_atoms = [a for a in atoms if a.favorable]
        worlds["silent_control"] = _world(
            pair_seed,
            family,
            "silent_control",
            prior,
            threshold,
            anchor_atoms,
            beats,
            [],
            {i: 1 for i in beats},
            np.random.default_rng([pair_seed, 3]),
        )
    elif family == "shared_origin":
        favorable = bool(rng.random() < 0.5)
        first = _check(rng, 0, favorable)
        relays = int(rng.choice((2, 3, 4)))
        for presentation in PAIRS[family]:
            worlds[presentation] = _world(
                pair_seed,
                family,
                presentation,
                prior,
                threshold,
                [first],
                [first.atom_id],
                [],
                {first.atom_id: 1 + relays if presentation == "relayed" else 1},
                np.random.default_rng([pair_seed, 2]),
            )
        others = [_check(rng, i, favorable) for i in (1, 2)]
        worlds["independent"] = _world(
            pair_seed,
            family,
            "independent",
            prior,
            threshold,
            [first, *others],
            [a.atom_id for a in (first, *others)],
            [],
            {a.atom_id: 1 for a in (first, *others)},
            np.random.default_rng([pair_seed, 3]),
        )
    else:
        raise ValueError("Unknown family")
    a, b = PAIRS[family]
    if (
        worlds[a].atoms != worlds[b].atoms
        or worlds[a].strong != worlds[b].strong
        or not math.isclose(normative_logit(worlds[a]), normative_logit(worlds[b]))
    ):
        raise ValueError("Matched presentations must share one world and posterior")
    return worlds
