"""Pipeline validation bound to the implementation fingerprint.

Passing requires every rendered case in every variant to display its design's probabilities,
the two-way sentence exactly in the paired variant, no private labels in public checkpoints,
and recovery of known parameters from complete synthetic collections through the real service:
every module and cover in the paired variant, every other variant in the markets cover, and a
learning respondent in both learning variants. It validates measurement machinery, not any
respondent.
"""

import json
import tempfile
from pathlib import Path

import numpy as np

from epistemics.disposition_tasks.collection import CASES, fingerprint, load_report, public_trial
from epistemics.disposition_tasks.render import (
    ASKED_MODULES,
    ASKED_VARIANTS,
    COVERS,
    CUE_MODULES,
    CUE_VARIANTS,
    DOSSIER_MODULES,
    DOSSIER_VARIANTS,
    LEARNING_RATES,
    LOAD_MODULES,
    LOAD_VARIANTS,
    LONG_LOAD_MODULES,
    MODULES,
    PEER_MODULES,
    PEER_VARIANTS,
    PROBED_MODULES,
    RANGE_MODULES,
    RANGE_VARIANTS,
    STRUCTURE_LOAD_MODULES,
    UNPROMPTED_MODULES,
    UNPROMPTED_VARIANTS,
    URN2_VARIANTS,
    URN3_MODULES,
    URN3_RATED_MODULES,
    URN3_RATED_VARIANTS,
    URN3_VARIANTS,
    URN_ASKED_MODULES,
    URN_MODULES,
    URN_PROBED_MODULES,
    URN_VARIANTS,
    V2_ASKED_MODULES,
    V2_MODULES,
    V2_PROBED_MODULES,
    VARIANTS,
    VIG_VARIANTS,
    items_for,
    render,
    stated_percentages,
    urn_family,
)
from epistemics.disposition_tasks.simulation import simulate

# Description-level priors: the mean level error must meet the recovery gate (0.10) and no level
# may miss by more than 0.20. Until tasks 0.10 the criterion was the largest level error at most
# 0.15; at report noise 0.15 the forecast-only relay designs miss that by chance (their recovery
# MAE is 0.08), which the urn contexts showed (docs/disposition-abstract-2026-09-28.md).
TOLERANCE = {
    "disposition": 0.15,
    "certainty_value": 15.0,
    "start": 0.15,
    "cue_mean": 0.10,
    "cue_largest": 0.20,
    # Load modules, a pipeline check on eight cases per level: the noise slope over load within
    # 0.6 of the truth, and the neglect weight rising by at least 0.1 from the lowest to the
    # highest level (true rise 0.5). Per-level tolerances failed by chance in 8-20% of contexts,
    # because noise and neglect trade off with eight cases, and noise below about 0.05 is only
    # partly identified from whole percentages; these fail in about 2%.
    "load_slope": 0.6,
    "load_eta_rise": 0.1,
    # Audit uptake (tasks 0.17): the fraction of the ideal revision, one context at low noise.
    "uptake": 0.2,
    # Multi-agent Stage 1 (tasks 0.20): every weight, conformity and exponent within 0.25 of
    # the truth; implied fidelity within 0.1.
    "social": 0.25,
    "fidelity": 0.1,
}
LOAD_RESPONDENT = {"load_sd": [0.1, 0.2, 0.5], "load_eta": [0.0, 0.2, 0.5], "bias": 0.0}
# The four-level ladders: the same noise and neglect range, over four levels.
LONG_LOAD_RESPONDENT = {
    "load_sd": [0.1, 0.15, 0.25, 0.5],
    "load_eta": [0.0, 0.1, 0.25, 0.5],
    "bias": 0.0,
}
UPTAKE_RESPONDENT = {"baseline": 0.05, "uptake": 0.6, "gamma": 1.0, "bias": 0.0, "report_sd": 0.05}
# Multi-agent battery, Stage 1 (tasks 0.20): respondents with known social parameters.
SOCIAL_RESPONDENTS = {
    ("advice-peer", "peer-a"): {
        "beta_own": 1.0,
        "beta_rec": 0.8,
        "beta_conf": 0.4,
        "bias": 0.0,
        "report_sd": 0.05,
    },
    ("conformity-peer", "peer-a"): {
        "beta_own": 1.0,
        "eta": 0.5,
        "kappa": 0.4,
        "bias": 0.0,
        "report_sd": 0.05,
    },
    ("relay-peer", "chain-stated"): {"omega": 0.5, "gamma": 1.0, "bias": 0.0, "report_sd": 0.05},
    # Tasks 0.21: default weights where nothing is stated.
    ("advice-peer", "peer-open"): {
        "beta_own": 1.0,
        "w0": 1.2,
        "w_conf": 0.5,
        "bias": 0.0,
        "report_sd": 0.05,
    },
    **{
        (module, "peer-open"): {
            "beta_own": 1.0,
            "w0": 1.2,
            "w_conf": 0.5,
            "bias": 0.0,
            "report_sd": 0.05,
        }
        for module in ("advice-relay", "advice-sensor", "advice-agent")
    },
    ("conformity-peer", "peer-open"): {
        "beta_own": 1.0,
        "v": 0.6,
        "rho": 0.5,
        "bias": 0.0,
        "report_sd": 0.05,
    },
    ("relay-peer", "chain-open"): {"fidelity": 0.7, "gamma": 1.0, "bias": 0.0, "report_sd": 0.05},
}
# The copying-peer texts must never describe copying or passing on calls.
PEER_MECHANISM = ("copy", "copies", "pass on", "passes on", "passed on", "repeat", "relay")
# Confidence surfaces (tasks 0.22): nothing may say what a confidence level is worth, and the
# relayer must be said to have no information of its own.
ACCURACY_WORDS = ("correct", "accura", "right in", "record", "reliab", "%")
REPORT_TRUTHS = [
    {"disposition": 0.15, "gamma": 0.9, "bias": 0.1, "report_sd": 0.15},
    {"disposition": 0.5, "gamma": 1.1, "bias": -0.1, "report_sd": 0.15},
    {"disposition": 0.85, "gamma": 1.0, "bias": 0.0, "report_sd": 0.15},
]
CHECK_TRUTHS = [
    {"function": "linear", "certainty_value": 0.0, "decision_weight": 1.0, "wtp_sd": 3.0},
    {"function": "linear", "certainty_value": 50.0, "decision_weight": 0.9, "wtp_sd": 3.0},
    {"function": "entropy", "certainty_value": 100.0, "decision_weight": 1.1, "wtp_sd": 3.0},
]
# A learner starting at indifference. Strength 8 keeps the start identifiable (the recovery
# study scores the start only from strength 8) while learning remains detectable.
LEARNER = {"start": 0.5, "strength": 8.0, "gamma": 1.0, "bias": 0.0, "report_sd": 0.1}
# Low report noise, as the validation's scope states: this is a pipeline check, and design
# precision is established by the recovery study. Until tasks 0.11 this respondent had noise 0.15,
# at which the forecast-only relay designs miss single-context tolerances by sampling error alone
# (docs/disposition-abstract2-2026-09-29.md).
CUE_RESPONDENT = {"slots": [0.1, 0.3, 0.5, 0.7, 0.9], "gamma": 1.0, "bias": 0.0, "report_sd": 0.05}
# A relative judge: targets sit higher among well-staffed outlets than among aggregators.
RANGE_RESPONDENTS = {
    "range-reassuring": {
        "slots": [0.45, 0.5, 0.55, 0.7, 0.75, 0.05, 0.05, 0.1],
        "gamma": 1.0,
        "bias": 0.0,
        "report_sd": 0.15,
    },
    "range-suggestive": {
        "slots": [0.2, 0.25, 0.4, 0.45, 0.5, 0.9, 0.95, 0.9],
        "gamma": 1.0,
        "bias": 0.0,
        "report_sd": 0.15,
    },
}
PRIVATE = (
    "disposition",
    "probe",
    "delta",
    "sigma",
    "gamma",
    "discount",
    "skepticism",
    "entropy",
    "certainty",
    "selective",
    "prior that",
    "item",
    "variant",
    "suggestive",
    "reassuring",
)
TWO_WAY = (" may have ", "could be either kind")
# Unprompted dossiers must not name or describe relaying or selective withholding.
MECHANISM = (
    "relay",
    "withh",
    "selective",
    "repeat",
    "copies",
    "copied",
    "for itself",
    "for themselves",
    "at random",
    "on purpose",
    "strategic",
)


def variants_of(module):
    if module in PEER_MODULES:
        return PEER_VARIANTS[module]
    if module in CUE_MODULES:
        return CUE_VARIANTS
    if module in RANGE_MODULES:
        return RANGE_VARIANTS
    if module in DOSSIER_MODULES:
        return DOSSIER_VARIANTS
    if module in UNPROMPTED_MODULES:
        return UNPROMPTED_VARIANTS
    if module in ASKED_MODULES + PROBED_MODULES:
        return ASKED_VARIANTS
    extra = (URN3_VARIANTS if module in URN3_MODULES else ()) + (
        URN3_RATED_VARIANTS if module in URN3_RATED_MODULES else ()
    )
    if module in LOAD_MODULES:
        return LOAD_VARIANTS
    if module in URN_MODULES:
        return URN_VARIANTS + URN2_VARIANTS + VIG_VARIANTS + extra
    if module in URN_ASKED_MODULES + URN_PROBED_MODULES:
        return ("urn-named", "urn2-named") + extra
    if module in V2_MODULES:
        return URN2_VARIANTS
    if module in V2_ASKED_MODULES + V2_PROBED_MODULES:
        return ("urn2-named",)
    return ("paired",) if module == "checks" else VARIANTS


def covers_of(module):
    return (
        ("markets",)
        if module
        in CUE_MODULES
        + RANGE_MODULES
        + DOSSIER_MODULES
        + UNPROMPTED_MODULES
        + ASKED_MODULES
        + PROBED_MODULES
        + URN_MODULES
        + URN_ASKED_MODULES
        + URN_PROBED_MODULES
        + V2_MODULES
        + V2_ASKED_MODULES
        + V2_PROBED_MODULES
        + LOAD_MODULES
        + PEER_MODULES
        else COVERS
    )


def states_only_the_named(module, variant, case):
    """Unprompted cases never state the mechanism; named cases state exactly its one sentence."""
    from epistemics.disposition_tasks.dossier import NAMED

    text = case["case"]
    if variant == "named-a":
        sentence = NAMED["relay" if module.startswith("corroboration") else "disclosure"]
        if text.count(sentence) != 1:
            return False
        text = text.replace(sentence, "")
    shown = json.dumps({**case, "case": text}).lower()
    return not any(word in shown for word in MECHANISM)


# Urn cases in the plain variant must not name or describe their structure.
URN_MECHANISM = {
    "copying": ("copy", "copies", "copied", "relay", "repeats"),
    "selection": ("hold back", "holds back", "withh", "selective", "every red"),
    "mismatch": ("different urn", "another urn", "wrong urn"),
    "echo": ("repeat", "told", "copy", "relay"),
    "hub": ("every red", "every blue", "selective", "withh", "hold back"),
    "stale": ("refill", "emptied", "before the urn", "out of date", "stale"),
}


def urn_states_only_the_named(module, variant, case):
    """Plain cases never state the structure; named cases state its one sentence exactly once.
    Only the question of a base-rate or probe case may mention it again."""
    import re

    from epistemics.disposition_tasks.urn import background, rated

    family = urn_family(module)
    text = case["case"]
    sentence = background(family, variant)
    if sentence:
        if text.count(sentence) != 1:
            return False
        text = text.replace(sentence, "")
    if rated(variant):
        # A stated rate follows a record, once; nowhere else.
        lines = re.findall(r"Among sensors with a record like [^.]*\.", text)
        if len(lines) != text.count("Record for "):
            return False
        for line in lines:
            text = text.replace(line, "")
    words = URN_MECHANISM[family] + MECHANISM
    return not any(word in text.lower() for word in words)


def audit():
    """Rendering audit over every module, cover, variant and item."""
    count = 0
    for module in MODULES:
        kinds = items_for(module).get("kind")
        for cover in covers_of(module):
            for variant in variants_of(module):
                cases = [render(module, cover, i, variant) for i in range(CASES)]
                if len({c["case"] for c in cases}) != CASES:
                    raise ValueError(f"Duplicate case text in {module}/{cover}/{variant}")
                for i, case in enumerate(cases):
                    where = f"{module}/{cover}/{variant}/{i}"
                    for p in stated_percentages(module, i, variant):
                        if p not in case["case"]:
                            raise ValueError(f"{where} does not display {p}")
                    if any(word in json.dumps(case).lower() for word in PRIVATE):
                        raise ValueError(f"{where} shows a private label")
                    if module in UNPROMPTED_MODULES and not states_only_the_named(
                        module, variant, case
                    ):
                        raise ValueError(f"{where} states the mechanism beyond its variant")
                    # Asked cases: the case text names the mechanism once; only a base-rate
                    # question mentions it again.
                    urn = module in (
                        URN_MODULES
                        + URN_ASKED_MODULES
                        + URN_PROBED_MODULES
                        + V2_MODULES
                        + V2_ASKED_MODULES
                        + V2_PROBED_MODULES
                    )
                    if urn and not urn_states_only_the_named(module, variant, case):
                        raise ValueError(f"{where} states the mechanism beyond its variant")
                    if module in ("advice-relay", "advice-sensor", "advice-agent"):
                        source = "\n\n".join(
                            part
                            for part in case["case"].split("\n\n")[1:]
                            if not part.startswith("Your own sensor")
                        )
                        if any(word in source.lower() for word in ACCURACY_WORDS):
                            raise ValueError(f"{where} says what confidence is worth")
                        if module == "advice-relay" and "did not read the urn" not in source:
                            raise ValueError(f"{where} does not say the relayer did not read it")
                    if module == "copying-peer" and any(
                        word in case["case"].lower() for word in PEER_MECHANISM
                    ):
                        raise ValueError(f"{where} describes copying")
                    if module in ASKED_MODULES + PROBED_MODULES and not states_only_the_named(
                        module, variant, {"case": case["case"]}
                    ):
                        raise ValueError(f"{where} states the mechanism beyond its variant")
                    if module != "checks" and kinds[i] != "single":
                        two_way = any(phrase in case["case"] for phrase in TWO_WAY)
                        if two_way != (variant == "paired"):
                            raise ValueError(f"{where} has the wrong framing")
                count += CASES
    return {"modules": len(MODULES), "covers": len(COVERS), "cases": count}


def contexts_to_validate():
    for module in CUE_MODULES:
        for variant in CUE_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in RANGE_MODULES:
        for variant in RANGE_VARIANTS:
            yield module, "markets", variant, RANGE_RESPONDENTS[variant]
    for module in DOSSIER_MODULES:
        for variant in DOSSIER_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in ("corroboration", "disclosure", "checks"):
        truths = CHECK_TRUTHS if module == "checks" else REPORT_TRUTHS
        for cover in COVERS:
            for truth in truths:
                yield module, cover, "paired", truth
        if module == "checks":
            continue
        for variant in ("open", "suggestive", "reassuring"):
            yield module, "markets", variant, REPORT_TRUTHS[0]
        for variant in LEARNING_RATES:
            yield module, "markets", variant, LEARNER
    # Appended last, so earlier contexts keep the random draws of earlier battery versions.
    for variant in UNPROMPTED_VARIANTS:
        for module in UNPROMPTED_MODULES:
            yield module, "markets", variant, CUE_RESPONDENT
    for variant in ASKED_VARIANTS:
        for module in ASKED_MODULES:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in PROBED_MODULES:
        yield module, "markets", "named-a", CUE_RESPONDENT
    for module in URN_MODULES:
        for variant in URN_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in URN_ASKED_MODULES + URN_PROBED_MODULES:
        yield module, "markets", "urn-named", CUE_RESPONDENT
    for module in URN_MODULES:
        for variant in URN2_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in URN_ASKED_MODULES + URN_PROBED_MODULES:
        yield module, "markets", "urn2-named", CUE_RESPONDENT
    for module in URN3_MODULES:
        for variant in URN3_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in URN3_RATED_MODULES:
        for variant in URN3_RATED_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in V2_MODULES:
        for variant in URN2_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in V2_ASKED_MODULES + V2_PROBED_MODULES:
        yield module, "markets", "urn2-named", CUE_RESPONDENT
    for module in URN_MODULES:
        for variant in VIG_VARIANTS:
            yield module, "markets", variant, CUE_RESPONDENT
    for module in LOAD_MODULES:
        for variant in LOAD_VARIANTS:
            long = module in LONG_LOAD_MODULES + STRUCTURE_LOAD_MODULES
            yield module, "markets", variant, LONG_LOAD_RESPONDENT if long else LOAD_RESPONDENT
    for module in URN_MODULES:
        yield module, "markets", "urn2-vig2", UPTAKE_RESPONDENT
    for (module, variant), truth in SOCIAL_RESPONDENTS.items():
        yield module, "markets", variant, truth
    yield "copying-peer", "markets", "urn2-vig2", UPTAKE_RESPONDENT


def estimate(module, analysis, truth):
    if "load_sd" in truth:
        levels = analysis["load"]["levels"]
        slope = analysis["load"]["load_slope"]
        true_slope = float(np.polyfit(range(len(truth["load_sd"])), np.log(truth["load_sd"]), 1)[0])
        rise = levels[-1]["eta"]["mean"] - levels[0]["eta"]["mean"]
        ok = (
            abs(slope - true_slope) <= TOLERANCE["load_slope"]
            and rise >= TOLERANCE["load_eta_rise"]
        )
        return slope, bool(ok)
    if "social" in analysis:
        parameters = analysis["social"]["parameters"]
        checked = [k for k in truth if k in parameters and k not in ("bias", "report_sd")]
        errors = [abs(parameters[k]["mean"] - truth[k]) for k in checked]
        tolerance = TOLERANCE["fidelity"] if "fidelity" in truth else TOLERANCE["social"]
        return max(errors), max(errors) <= tolerance
    if "uptake" in truth:
        row = analysis["uptake"]["parameters"]["uptake"]
        return row["mean"], abs(row["mean"] - truth["uptake"]) <= TOLERANCE["uptake"]
    if module == "checks":
        row = analysis["fits"][truth["function"]]["parameters"]["certainty_value"]
        error = abs(row["mean"] - truth["certainty_value"])
        return row["mean"], error <= TOLERANCE["certainty_value"]
    if "slots" in truth:
        if "range" in analysis:
            summary = analysis["range"]
            implied = summary["targets_implied"] + summary["comparisons_implied"]
        else:
            implied = analysis["cues"]["implied"]
        errors = [abs(a - b) for a, b in zip(implied, truth["slots"], strict=True)]
        largest, mean = max(errors), sum(errors) / len(errors)
        return largest, mean <= TOLERANCE["cue_mean"] and largest <= TOLERANCE["cue_largest"]
    if "strength" in truth:
        learning = analysis["learning"]
        row = learning["parameters"]["start"]
        # As in the recovery study, learning must be detected only where it is visible: when the
        # revealed rate differs from the starting value by at least 0.25.
        visible = abs(analysis["revealed_rate"] - truth["start"]) >= 0.25
        detected = learning["learning_probability"] > 0.5 or not visible
        # How well one context pins the start depends on its order (how many informative cases
        # precede the reveals), so the check is coverage by the 90% interval, widened by half a
        # grid step, rather than a fixed tolerance on the posterior mean.
        low, high = row["interval_90"]
        covered = low - 0.025 <= truth["start"] <= high + 0.025
        return row["mean"], detected and covered
    row = analysis["fit"]["parameters"]["disposition"]
    return row["mean"], abs(row["mean"] - truth["disposition"]) <= TOLERANCE["disposition"]


def validate(seed):
    audited = audit()
    rng = np.random.default_rng(seed)
    contexts = []
    with tempfile.TemporaryDirectory() as tmp:
        for n, (module, cover, variant, truth) in enumerate(contexts_to_validate()):
            directory = Path(tmp) / f"{n:02d}-{module}-{cover}-{variant}"
            order = rng.permutation(CASES).tolist()
            report = simulate(
                directory,
                module=module,
                cover=cover,
                order=order,
                truth=truth,
                seed=int(rng.integers(2**31)),
                variant=variant,
                reveal_seed=int(rng.integers(2**31)) if variant in LEARNING_RATES else None,
            )
            reloaded = load_report(directory)
            shown = [public_trial(reloaded.manifest, i) for i in range(CASES)]
            value, recovered = estimate(module, report.analysis, truth)
            contexts.append(
                {
                    "module": module,
                    "cover": cover,
                    "variant": variant,
                    "truth": truth,
                    "estimate": value,
                    "recovered": recovered,
                    "reloaded": reloaded == report
                    and [o.trial for o in report.observations] == shown,
                    "reveals_shown": sum("previous_case" in t for t in shown),
                }
            )
    reveals = all(
        c["reveals_shown"] == (CASES - 1 if c["variant"] in LEARNING_RATES else 0) for c in contexts
    )
    return {
        "schema_version": "epistemics.disposition-task-validation.v5",
        "seed": seed,
        "implementation_sha256": fingerprint(),
        "audit": audited,
        "tolerance": TOLERANCE,
        "contexts": contexts,
        "passed": reveals and all(c["recovered"] and c["reloaded"] for c in contexts),
        "scope": "Rendering audit and complete synthetic collections through the service at low report noise; no respondent behavior is validated",
    }
