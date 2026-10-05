"""Passport adapter: a mitigation generated from a configuration's passport and bound to its
identity (docs/passport-adapter-design.md).

Phase 1 has one component kind, C1 (structure check), for the two finance-dossier structures that
the passport's structure checks cover: sources repeating another source (relay) and selective
silence (disclosure). Each structure's check gives the lightest prompt that made the configuration
reliably consider it (a rung of the salience ladder). The adapter delivers that dose as standing
instructions:

  rung 1  name the structure
  rung 2  name it, and ask how common it is before forecasting
  rung 3  name it, ask how common it is, and ask about it for each case

A structure whose check is undetermined, not converged or "not reliable" gets rung 3: recommending
too little prompting is the costly error. The generic comparator gives every structure rung 3.

The adapter is a deterministic function of the passport's structure checks and this generator's
version, so the same passport always gives the same adapter. Its digest covers everything else in
the document.
"""

import argparse
import json
from pathlib import Path

from epistemics.source_learning.storage import digest, encoded

VERSION = "passport-adapter/0.1.0"
SCHEMA = "epistemics.passport-adapter.v1"
STRUCTURES = ("relay", "disclosure")
FULL = 3
# The standing instructions per structure and rung. General guidance only: no case, company,
# outlet or answer is ever named.
TEXT = {
    "relay": {
        1: "Some news sources repeat another source's report instead of checking for themselves; "
        "a repeated report adds nothing to the report it repeats.",
        2: "Before forecasting, ask yourself how common that is among sources like the ones in "
        "front of you.",
        3: "Then, for each source whose report matches another's, ask whether it could be "
        "repeating that report rather than checking for itself, and weigh it accordingly.",
    },
    "disclosure": {
        1: "Some companies stay silent about their numbers when the numbers are bad; what a company "
        "leaves out of an update can be informative.",
        2: "Before forecasting, ask yourself how common that is among companies like the one in "
        "front of you.",
        3: "Then, for each update with something left out, ask whether it could have been left out "
        "because it was bad, and weigh the gap accordingly.",
    },
}
PREAMBLE = (
    "Guidance for this session (it applies to every case; read each case on its own evidence):"
)


def configuration_id(configuration):
    """The configuration identity used across the passport: a digest of its definition."""
    return "configuration:" + digest(encoded(configuration))


def dose(check):
    """The rung an adapter gives a structure, from its structure check (FULL when undetermined)."""
    if not check or not check.get("valid"):
        return FULL
    rung = check.get("advice", check.get("recommended_rung"))
    if rung in (None, "rate"):
        return FULL
    return int(rung)


def compile_instructions(components):
    lines = [PREAMBLE]
    for c in components:
        if c["rung"] > 0:
            lines.append(" ".join(TEXT[c["structure"]][r] for r in range(1, c["rung"] + 1)))
    return "\n".join(lines) if len(lines) > 1 else ""


def _finish(document):
    document = dict(document)
    document.pop("adapter_sha256", None)
    document["adapter_sha256"] = digest(encoded(document))
    return document


def generate(label, configuration, checks, passport):
    """The adapter for one configuration from its structure checks.

    checks: {structure: check} as in the ledger's structure_checks model; passport: the source
    passport's identifying fields (guide version, ledger digest)."""
    components = []
    for structure in STRUCTURES:
        check = checks.get(structure)
        rung = dose(check)
        determined = bool(
            check
            and check.get("valid")
            and check.get("advice", check.get("recommended_rung")) not in (None, "rate")
        )
        components.append(
            {
                "id": "C1",
                "structure": structure,
                "rung": rung,
                "reading": f"check-{structure}",
                "basis": f"recommended rung {rung}"
                if determined
                else "check undetermined: full dose",
            }
        )
    return _finish(
        {
            "schema_version": SCHEMA,
            "name": f"adapter-{label}",
            "subject": {
                "label": label,
                "configuration": configuration,
                "configuration_id": configuration_id(configuration),
            },
            "passport": passport,
            "generator": {"version": VERSION},
            "components": components,
            "instructions": compile_instructions(components),
            "tools": [],
        }
    )


def generic(passport):
    """The comparator: every structure at full dose, for any configuration."""
    components = [
        {"id": "C1", "structure": s, "rung": FULL, "reading": None, "basis": "full dose for all"}
        for s in STRUCTURES
    ]
    return _finish(
        {
            "schema_version": SCHEMA,
            "name": "generic",
            "subject": None,
            "passport": passport,
            "generator": {"version": VERSION},
            "components": components,
            "instructions": compile_instructions(components),
            "tools": [],
        }
    )


def from_ledger(ledger_path, labels):
    from epistemics.research_world3.runner import CONFIGURATIONS

    raw = Path(ledger_path).read_bytes()
    ledger = json.loads(raw)
    passport = {
        "guide_version": (ledger.get("guide") or {}).get("guide_version"),
        "ledger_version": ledger.get("ledger_version"),
        "ledger_sha256": digest(raw),
    }
    checks = ((ledger.get("models") or {}).get("structure_checks") or {}).get("checks") or {}
    out = {"generic": generic(passport)}
    for label in labels:
        model, effort = CONFIGURATIONS[label]
        configuration = {"model": model, "reasoning_effort": effort}
        out[f"adapter-{label}"] = generate(label, configuration, checks.get(label, {}), passport)
    return out


def main():
    parser = argparse.ArgumentParser(description="Generate passport adapters from a ledger.")
    parser.add_argument("--ledger", type=Path, default=Path("output/ledger.json"))
    parser.add_argument("--labels", nargs="+", default=["astra", "sol", "luna", "terra"])
    parser.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for name, document in from_ledger(a.ledger, a.labels).items():
        (a.out / f"{name}.json").write_bytes(encoded(document))
        rungs = {c["structure"]: c["rung"] for c in document["components"]}
        print(name, rungs, document["adapter_sha256"][:12])


if __name__ == "__main__":
    main()
