"""Passport adapter evaluation (docs/passport-adapter-design.md): sessions on the evident-structure
modules, by configuration and arm.

Per configuration and arm: the mean absolute log-odds error against the correct forecast (all
cases, present, absent and control), the fitted structure use (present cases) and false structure
(absent cases), sessions, and the adapter's extra instruction length. Per configuration, the three
contrasts of the design, each as the error difference (positive means the adapter is better):

  M1  alone      - adapter
  M2  generic    - adapter   (overall, and on absent cases, where overcorrection shows)
  M3  mismatched - adapter
"""

import numpy as np

ARMS = ("alone", "generic", "adapter", "mismatched")


def arm_of(config, variant, mismatch):
    if variant in ("alone", "generic"):
        return variant
    if variant == f"adapter-{config}":
        return "adapter"
    if variant == f"adapter-{mismatch.get(config)}":
        return "mismatched"
    return None


def sessions(roots):
    from epistemics.disposition_tasks.runner import ADAPTER_MISMATCH
    from epistemics.ledger import dispositions

    out = []
    for root in roots:
        for r in dispositions.extract(root):
            if not r.get("verified") or "evident" not in r:
                continue
            arm = arm_of(r["configuration"], r["variant"], ADAPTER_MISMATCH)
            if arm is None:
                continue
            e = r["evident"]
            out.append({"configuration": r["configuration"], "arm": arm, "variant": r["variant"],
                        "module": r["module"], "error": e["error"], **{f"error_{t}": v for t, v in
                        e["error_by_type"].items()}, "structure_use": e["structure_use"],
                        "false_structure": e["false_structure"], "run": r["run_id"]})  # fmt: skip
    return out


def summary(roots):
    from epistemics.disposition_tasks.presentation import instructions

    rows = sessions(roots)
    standard = len(instructions("relay-evident", "alone"))
    table = {}
    for c in sorted({r["configuration"] for r in rows}):
        arms = {}
        for arm in ARMS:
            mine = [r for r in rows if r["configuration"] == c and r["arm"] == arm]
            if not mine:
                continue
            variant = mine[0]["variant"]
            arms[arm] = {
                "variant": variant,
                "sessions": len(mine),
                **{
                    k: float(np.mean([r[k] for r in mine]))
                    for k in (
                        "error",
                        "error_present",
                        "error_absent",
                        "error_control",
                        "structure_use",
                        "false_structure",
                    )
                },  # fmt: skip
                "extra_instruction_characters": len(instructions("relay-evident", variant))
                - standard,
            }
        contrasts = {}
        if "adapter" in arms:
            a = arms["adapter"]
            for name, other in (("M1", "alone"), ("M2", "generic"), ("M3", "mismatched")):
                if other in arms:
                    contrasts[name] = {"error": arms[other]["error"] - a["error"],
                                       "error_absent": arms[other]["error_absent"] - a["error_absent"],
                                       "error_present": arms[other]["error_present"] - a["error_present"]}  # fmt: skip
        table[c] = {"arms": arms, "contrasts": contrasts}
    return {
        "schema_version": "epistemics.adapter-eval.v1",
        "configurations": table,
        "scope": (
            "Error is the mean absolute log-odds difference from the correct forecast on the "
            "evident-structure dossiers; contrasts are the other arm's error minus the adapter's, "
            "so positive means the adapter is better."
        ),
    }


# Redesign (tasks 0.45): hinted-structure dossiers, scored against each configuration's own
# considered answers (its reference arm: mechanism stated in the case, generic full guidance).
HINTED_ARMS = ("alone", "generic", "adapter", "mismatched", "reference")
CLIP = 0.01


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), CLIP, 1 - CLIP)
    return np.log(p / (1 - p))


def hinted_sessions(roots):
    from epistemics.disposition_tasks.render import HINTED_MODULES
    from epistemics.disposition_tasks.runner import ADAPTER_MISMATCH
    from epistemics.ledger import dispositions

    out = []
    for root in roots:
        for r in dispositions.extract(root):
            if not r.get("verified") or r.get("module") not in HINTED_MODULES:
                continue
            variant = r["variant"]
            arm = (
                "reference"
                if variant == "reference"
                else arm_of(r["configuration"], variant, ADAPTER_MISMATCH)
            )
            if arm is None:
                continue
            slots = np.asarray(r["items"]["slot"])
            out.append({"configuration": r["configuration"], "module": r["module"], "arm": arm,
                        "variant": variant, "run": r["run_id"],
                        "z": _logit([np.nan if v is None else v for v in r["responses"]]),
                        "described": slots >= 0,
                        "implied": [s["implied"]["mean"] for s in r.get("slot_fits", [])]})  # fmt: skip
    return out


def _exact_p(a, b):
    """One-sided p that arm a's mean deviation exceeds arm b's, over every split of the pooled
    sessions."""
    import itertools

    pooled = np.r_[a, b]
    observed = np.mean(a) - np.mean(b)
    n = len(a)
    diffs = [
        pooled[list(idx)].mean() - np.delete(pooled, list(idx)).mean()
        for idx in itertools.combinations(range(len(pooled)), n)
    ]
    return float(np.mean(np.array(diffs) >= observed - 1e-12))


def hinted_summary(roots):
    rows = hinted_sessions(roots)
    out = {}
    for c in sorted({r["configuration"] for r in rows}):
        mine = [r for r in rows if r["configuration"] == c]
        targets, mappings = {}, {}
        for m in {r["module"] for r in mine}:
            ref = [r for r in mine if r["module"] == m and r["arm"] == "reference"]
            if not ref:
                continue
            targets[m] = np.nanmean([r["z"] for r in ref], axis=0)
            mappings[m] = np.mean([r["implied"] for r in ref if r["implied"]], axis=0)

        def deviation(r, target, targets=targets):
            t = targets[r["module"]] if target is None else target
            d = r["described"]
            return float(np.nanmean(np.abs(r["z"][d] - t[d])))

        devs = {arm: [] for arm in HINTED_ARMS}
        maps = {arm: [] for arm in HINTED_ARMS}
        for r in mine:
            if r["module"] not in targets:
                continue
            if r["arm"] == "reference":
                # Leave one out: the reference sessions' own spread, a noise floor.
                others = [o["z"] for o in mine if o["module"] == r["module"] and o["arm"] ==
                          "reference" and o["run"] != r["run"]]  # fmt: skip
                if others:
                    devs["reference"].append(deviation(r, np.nanmean(others, axis=0)))
            else:
                devs[r["arm"]].append(deviation(r, None))
            if r["implied"] is not None and len(r["implied"]) == len(mappings[r["module"]]):
                maps[r["arm"]].append(
                    float(np.mean(np.abs(np.array(r["implied"]) - mappings[r["module"]])))
                )
        arms = {
            arm: {"deviation": float(np.mean(v)), "sessions": len(v),
                  "mapping_distance": float(np.mean(maps[arm])) if maps[arm] else None}
            for arm, v in devs.items() if v
        }  # fmt: skip
        contrasts = {}
        if devs["adapter"]:
            for name, other in (("M1", "alone"), ("M2", "generic"), ("M3", "mismatched")):
                if devs[other]:
                    contrasts[name] = {
                        "difference": float(np.mean(devs[other]) - np.mean(devs["adapter"])),
                        "p_one_sided": _exact_p(np.array(devs[other]), np.array(devs["adapter"])),
                    }
        out[c] = {
            "arms": arms,
            "contrasts": contrasts,
            "reference_mapping": {m: [float(x) for x in v] for m, v in mappings.items()},
        }
    return {
        "schema_version": "epistemics.adapter-hinted.v1",
        "configurations": out,
        "scope": (
            "Deviation: mean absolute log-odds distance of a session's forecasts on described "
            "cases from the configuration's own reference answers (mean of its reference sessions, "
            "same module); the reference arm's own value is leave-one-out, a noise floor. Mapping "
            "distance: mean absolute difference of implied structure priors per description from "
            "the reference's. Contrasts: other arm minus adapter (positive favours the adapter), "
            "exact one-sided p over session splits."
        ),
    }
