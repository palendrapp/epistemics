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
