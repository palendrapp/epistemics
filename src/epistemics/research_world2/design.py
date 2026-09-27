"""Balanced context designs: matched presentations of every world go to separate contexts.

Context type A shows disclosure as full letters and shared-origin evidence as relays; type B
shows disclosure letters selectively and shared-origin evidence once. Each context therefore
carries one manipulated family and one control family, never both presentations of a family.
Anchors join the context whose presentation of that family cannot contrast with them:
silent-control letters with full letters (A), independent surveys with single surveys (B).
"""

import math

import numpy as np

from epistemics.research_world2.check import PRICES
from epistemics.research_world2.render import company_name
from epistemics.research_world2.world import (
    ANCHORS,
    PAIRS,
    generate,
    naive_logit,
    normative_logit,
    sigmoid,
)

TYPES = {
    "A": {"disclosure": "full", "shared_origin": "relayed", "anchor": "disclosure"},
    "B": {"disclosure": "selected", "shared_origin": "single", "anchor": "shared_origin"},
}


MEASURABLE = (0.03, 0.97)


def measurable(pair_seed, family):
    """Normative and naive readings both stay where whole-percent reports can show them.

    Selection uses only the public evidence pattern and prior, never demand, so outcome
    scoring remains valid for the generated distribution.
    """
    low, high = MEASURABLE
    worlds = generate(pair_seed, family)
    for world in (*(worlds[p] for p in PAIRS[family]), worlds[ANCHORS[family]]):
        for x in (normative_logit(world), naive_logit(world)):
            if not low <= sigmoid(x) <= high:
                return False
    return True


def design(seed, worlds_per_family, per_family_per_context, anchors_per_context, check_offered):
    if worlds_per_family % per_family_per_context:
        raise ValueError("Worlds per family must divide evenly into contexts")
    rng = np.random.default_rng(seed)
    names, used = set(), set()

    def draw(family):
        # Every world in a design gets a distinct company name, so no context repeats one.
        while True:
            s = int(rng.integers(2**31))
            name = company_name(s, family)
            if s not in used and name not in names and measurable(s, family):
                used.add(s)
                names.add(name)
                return s

    seeds = {
        family: [draw(family) for _ in range(worlds_per_family)]
        for family in ("disclosure", "shared_origin")
    }
    # One price per world, so matched presentations offer the same check at the same price.
    prices = {
        (family, s): float(rng.choice(PRICES)) for family, group in seeds.items() for s in group
    }
    contexts = []
    blocks = worlds_per_family // per_family_per_context
    for kind, spec in TYPES.items():
        for b in range(blocks):
            items = []
            for family in ("disclosure", "shared_origin"):
                for s in seeds[family][
                    b * per_family_per_context : (b + 1) * per_family_per_context
                ]:
                    items.append({"pair_seed": s, "family": family, "presentation": spec[family]})
            for _ in range(anchors_per_context):
                family = spec["anchor"]
                s = draw(family)
                prices[(family, s)] = float(rng.choice(PRICES))
                items.append({"pair_seed": s, "family": family, "presentation": ANCHORS[family]})
            order = rng.permutation(len(items))
            items = [items[int(i)] for i in order]
            for item in items:
                item["check_price"] = (
                    prices[(item["family"], item["pair_seed"])] if check_offered else None
                )
            contexts.append({"context_type": kind, "block": b + 1, "items": items})
    return contexts


def cases_per_context(per_family_per_context, anchors_per_context):
    return 2 * per_family_per_context + anchors_per_context


def contexts_needed(worlds_per_family, per_family_per_context):
    return 2 * math.ceil(worlds_per_family / per_family_per_context)
