"""An auditable source process, with separate public and evaluator-only records."""

from functools import lru_cache
from math import comb
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Rule(Frozen):
    panels: int = Field(ge=1, le=20)
    direction: Literal["random", "maximum", "minimum"]

    @model_validator(mode="after")
    def canonical(self):
        if (self.panels == 1) != (self.direction == "random"):
            raise ValueError("One panel is random; multiple panels require maximum or minimum")
        return self


RANDOM = Rule(panels=1, direction="random")
RULES = (RANDOM,) + tuple(
    Rule(panels=j, direction=d) for j in (4, 10) for d in ("maximum", "minimum")
)


class Source(Frozen):
    source_id: str
    measurement_accuracy: float = Field(ge=0.5, le=1)
    rule: Rule


class World(Frozen):
    panel_size: int = Field(default=5, ge=1, le=20)
    weak_rate: float = Field(default=0.3, gt=0, lt=1)
    strong_rate: float = Field(default=0.7, gt=0, lt=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.weak_rate > self.strong_rate:
            raise ValueError(
                "Strong rate must be at least weak rate; equality is a neutral control"
            )
        return self


class PublicRecord(Frozen):
    source_id: str
    world: World
    count: int = Field(ge=0)
    resolved_strong: bool

    @model_validator(mode="after")
    def count_in_panel(self):
        if self.count > self.world.panel_size:
            raise ValueError("Count exceeds panel size")
        return self


class PrivateRecord(Frozen):
    source: Source
    public: PublicRecord
    true_panels: tuple[tuple[bool, ...], ...]
    measured_panels: tuple[tuple[bool, ...], ...]
    selected_index: int = Field(ge=0)

    @model_validator(mode="after")
    def ledger_consistent(self):
        n, j = self.public.world.panel_size, self.source.rule.panels
        if any(
            len(rows) != j or any(len(row) != n for row in rows)
            for rows in (self.true_panels, self.measured_panels)
        ):
            raise ValueError("Ledger dimensions do not match the source process")
        if self.public.source_id != self.source.source_id or self.selected_index >= j:
            raise ValueError("Source or selected index mismatch")
        counts = [sum(row) for row in self.measured_panels]
        expected = (
            counts.index(max(counts))
            if self.source.rule.direction == "maximum"
            else counts.index(min(counts))
            if self.source.rule.direction == "minimum"
            else 0
        )
        if self.selected_index != expected or self.public.count != counts[expected]:
            raise ValueError("Published count does not match the frozen selection rule")
        return self


def draw_record(rng: np.random.Generator, source: Source, world: World, strong: bool):
    rate = world.strong_rate if strong else world.weak_rate
    true = rng.random((source.rule.panels, world.panel_size)) < rate
    correct = rng.random(true.shape) < source.measurement_accuracy
    measured = np.where(correct, true, ~true)
    counts = measured.sum(axis=1)
    index = (
        int(np.argmax(counts))
        if source.rule.direction == "maximum"
        else int(np.argmin(counts))
        if source.rule.direction == "minimum"
        else 0
    )
    return PrivateRecord(
        source=source,
        public=PublicRecord(
            source_id=source.source_id,
            world=world,
            count=int(counts[index]),
            resolved_strong=strong,
        ),
        true_panels=tuple(tuple(map(bool, row)) for row in true),
        measured_panels=tuple(tuple(map(bool, row)) for row in measured),
        selected_index=index,
    )


@lru_cache(maxsize=2048)
def distribution(world: World, strong: bool, accuracy: float, rule: Rule) -> tuple[float, ...]:
    """Exact report-count distribution: noisy private measurements, then order selection."""
    if not np.isfinite(accuracy) or not 0.5 <= accuracy <= 1:
        raise ValueError("Measurement accuracy must be between 0.5 and 1")
    rate = world.strong_rate if strong else world.weak_rate
    measured = accuracy * rate + (1 - accuracy) * (1 - rate)
    n = world.panel_size
    mass = np.array([comb(n, k) * measured**k * (1 - measured) ** (n - k) for k in range(n + 1)])
    if rule.direction == "maximum":
        cdf = np.cumsum(mass)
        cdf[-1] = 1
        mass = np.diff(np.r_[0, cdf**rule.panels])
    elif rule.direction == "minimum":
        survival = np.cumsum(mass[::-1])[::-1]
        survival[0] = 1
        mass = -np.diff(np.r_[survival**rule.panels, 0])
    # Floating-point CDF subtraction can lose an extremely small tail, never create negatives.
    mass = np.maximum(mass, 0)
    mass /= mass.sum()
    return tuple(map(float, mass))


def sources() -> tuple[Source, ...]:
    """Evaluator-side crossed processes. Names encode no process information."""
    return tuple(
        Source(source_id=f"source-{i}", measurement_accuracy=r, rule=rule)
        for i, (r, rule) in enumerate(
            (r, rule) for rule in (RANDOM, RULES[3], RULES[4]) for r in (0.65, 0.95)
        )
    )


def archive(seed: int, per_source: int = 12) -> tuple[PrivateRecord, ...]:
    if per_source < 2 or per_source % 2:
        raise ValueError("Archive size per source must be positive, even and at least two")
    rng = np.random.default_rng(seed)
    rows = []
    for source in sources():
        # Deliberately balanced resolved archive; inference conditions on each displayed outcome.
        outcomes = np.array([False, True] * (per_source // 2))
        rng.shuffle(outcomes)
        rows.extend(draw_record(rng, source, World(), bool(h)) for h in outcomes)
    return tuple(rows)


class Probe(Frozen):
    source_id: str
    world: World = World()
    count: int = Field(ge=0, le=20)
    prior_strong: float = Field(default=0.5, gt=0, lt=1)
    disclosed_rule: Rule | None = None

    @model_validator(mode="after")
    def count_in_panel(self):
        if self.count > self.world.panel_size:
            raise ValueError("Count exceeds panel size")
        return self


def render(probe: Probe) -> str:
    """Development stimulus with disclosed business control; not a discovery collection UI."""
    p, w = probe, probe.world
    lines = [
        f"Source {p.source_id} reports exactly {p.count} of {w.panel_size} customers expanding.",
        f"The prior probability of strong demand is {p.prior_strong:.0%}.",
        f"In this control world, independent customers expand with probability {w.strong_rate:.0%} "
        f"under strong demand and {w.weak_rate:.0%} under weak demand.",
        "The source measures customers before selecting a panel. Its measurement quality is unknown.",
    ]
    if p.disclosed_rule:
        rule = p.disclosed_rule
        lines.append(
            "A process audit establishes that the source uses one randomly sampled panel."
            if rule.direction == "random"
            else f"A process audit establishes that the source reports the {rule.direction} count "
            f"from {rule.panels} independent panels of the same size."
        )
    else:
        lines.append("The panel-selection process has not been audited.")
    return "\n".join(lines)
