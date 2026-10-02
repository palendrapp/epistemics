"""Pipeline validation bound to the implementation fingerprint.

Passing requires every rendered case in every variant to display its design's probabilities,
the two-way sentence exactly in the paired variant, no private labels in public checkpoints,
and recovery of known parameters from complete synthetic collections through the real service:
every module and cover in the paired variant, every other variant in the markets cover, and a
learning respondent in both learning variants. It validates measurement machinery, not any
respondent.
"""

import json
import re
import tempfile
from pathlib import Path

import numpy as np

from epistemics.disposition_tasks.collection import CASES, fingerprint, load_report, public_trial
from epistemics.disposition_tasks.render import (
    ANNOUNCED_MODULES,
    ANNOUNCED_VARIANTS,
    ASKED_MODULES,
    ASKED_VARIANTS,
    CALLS_MODULES,
    CALLS_VARIANTS,
    COHERE_MODULES,
    COHERE_VARIANTS,
    CORRELATED_MODULES,
    CORRELATED_VARIANTS,
    COVERS,
    CUE_MODULES,
    CUE_VARIANTS,
    DELIBERATION_ANCHOR,
    DELIBERATION_FRAMES,
    DELIBERATION_MODULES,
    DELIBERATION_VARIANTS,
    DOSSIER_MODULES,
    DOSSIER_VARIANTS,
    FOLLOWUP_MODULES,
    FOLLOWUP_VARIANTS,
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
    SCREEN_MODULES,
    SCREEN_VARIANTS,
    STATEMENT_MODULES,
    STATEMENT_PROBE_MODULES,
    STATEMENT_VARIANTS,
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
    V3_MODULES,
    V3_VARIANTS,
    V31_MODULES,
    V31_VARIANTS,
    V32_MODULES,
    V32_VARIANTS,
    VARIANTS,
    VIG_VARIANTS,
    WORDING_MODULES,
    WORDING_VARIANTS,
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
    # Battery v3 (tasks 0.23): coherence slope from 10 pairs, risk exponent from 4 lotteries.
    "v3_beta": 0.25,
    "v3_rho": 0.2,
    # Battery v3.1: the balanced threshold within 0.6 log-odds from one session's decisions.
    "v31_theta": 0.6,
    # Battery v3.2: share of a session's 14 decisions agreeing with the respondent's thresholds.
    "v32_agreement": 0.85,
    # Open-inference screen: each contrast within 0.3 log-odds of the respondent's noiseless score
    # at report noise 0.05 (log-odds), anchors within 5 points.
    "screen_contrast": 0.3,
    # Coherence sets: the shrinkage d within 0.05 of the respondent's from one session (low noise).
    "cohere_d": 0.05,
    # Statements: each slot's mean step (beta times its reading) within 0.25 log-odds of the
    # respondent's from one session at report noise 0.05; stylistic steps within 0.1 on average.
    "statement_step": 0.25,
    "statement_content": 0.1,
    # Statement probe: each period's probability as answered.
    "statement_probe": 0.011,
    # Deliberation: the readout grain from one session within 0.35 (24 answers), the anchoring
    # weight from one anchor session within 0.1 (against the respondent's own answers).
    "deliberation_rho": 0.35,
    "deliberation_a": 0.1,
    # Announced count: each condition's mean step within 0.15 log-odds of the respondent's.
    "announced_step": 0.15,
    # Correlated changes: the mean first step within 0.15 log-odds of the respondent's (one form
    # holds each item in one order only, so the regression needs a configuration's sessions).
    "correlated_step": 0.15,
    # Confident wording: each case's weight within 0.15 log-odds of the respondent's, on average.
    "wording_weight": 0.15,
}
WORDING_RESPONDENT = {"w": [0.5, 1.0, 1.5, 2.0], "tau": 0.05}
CALLS_RESPONDENT = {"w": [0.5, 1.0, 1.5], "p": 0.8, "tau": 0.05}
CORRELATED_RESPONDENT = {
    "w": {"activity": 0.8, "inflation": 1.0, "risks": 0.8, "guidance": 1.6, "vote": 0.8},
    "c": 0.4,
    "tau": 0.05,
}
# A Bayesian combiner with distinct readings per slot (the pipeline check).
STATEMENT_RESPONDENT = {
    "w": {"activity": 0.6, "inflation": 0.8, "risks": 0.5, "guidance": 1.0, "vote": 0.4},
    "tilt": 0.0,
    "c": 0.0,
    "gamma": 1.0,
    "eta": 0.0,
    "beta": 1.0,
    "alpha": 1.0,
    "tau": 0.05,
}
PROBE_RESPONDENT = {"periods": [0.15, 0.3, 0.35, 0.2]}
# Deliberation style: a respondent with the screen's middle trend observer, half its answers
# rounded to 5 points, anchoring weight 0.3, low report noise.
DELIBERATION_RESPONDENT = {"rho": 0.5, "a": 0.3, "tau": 0.05}
# Follow-up rounding: fresh answers to the point, follow-ups rounded to 5 points.
FOLLOWUP_RESPONDENT = {"rho_fresh": 0.0, "rho_followup": 1.0, "tau": 0.05}
# Announced count: a budget by count (k 0.5, rewordings counted).
ANNOUNCED_RESPONDENT = {
    "w": {"activity": 0.8, "inflation": 1.0, "risks": 0.8, "guidance": 1.6, "vote": 0.8},
    "k": 0.5,
    "rewordings": 1.0,
    "tau": 0.05,
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
# Battery v3 (tasks 0.23): a respondent with known coherence and risk attitude.
V3_RESPONDENT = {
    "alpha": 0.2,
    "beta": 0.8,
    "tau_c": 0.15,
    "rho": 0.8,
    "stated_sd": 0.05,
    "default_acc": 0.7,
    "default_rate": 0.4,
}
# Battery v3.1 (tasks 0.24): a respondent with known thresholds and decisiveness.
V31_RESPONDENT = {
    "thresholds": [-1.0, 0.0, 1.0],
    "kappa": 8.0,
    "stakes": 0.0,
    "stated_sd": 0.05,
    "default_acc": 0.7,
    "default_rate": 0.4,
}
# Battery v3.2 (tasks 0.25): thresholds for mildly cheap, balanced, mildly costly, welfare_act
# and welfare_hold (welfare weight 0.5, no action offset in the welfare classes).
V32_RESPONDENT = {**V31_RESPONDENT, "thresholds": [-0.7, 0.0, 0.7, -0.5, 0.5]}
# Verdict words that an option's label must not contain (it would presuppose the answer).
VERDICTS = (
    "faulty",
    "working",
    "defective",
    "sound",
    "present",
    "down",
    "high demand",
    "low demand",
)
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


def v31_consequences_clean(case):
    """Battery v3.1: the paragraphs after the evidence (consequences, stakes) state no number once
    the option labels, which name the entity, are removed."""
    paragraphs = case["case"].split("\n\n")
    last = max(i for i, p in enumerate(paragraphs) if p.startswith(("Evidence", "Also on file")))
    tail = "\n\n".join(paragraphs[last + 1 :])
    for option in case["options"]:
        tail = tail.replace(option, "")
    return len(paragraphs) > last + 1 and not re.search(r"\d", tail)


def v32_consequences_match(module, index, case):
    """Battery v3.2: the decision shows its class's text for its domain, and no text states a
    quantity in number words."""
    from epistemics.disposition_tasks import surfaces

    items = items_for(module)
    text = surfaces.CONSEQUENCES_V32[int(items["domain"][index])][int(items["cls"][index])]
    words = re.compile(r"\b(" + "|".join(surfaces.NUMBER_WORDS) + r")\b", re.IGNORECASE)
    return text in case["case"] and not words.search(text)


# Open-inference screen: words that would state a rate or likelihood in a case (tasks 0.26 audit).
SCREEN_FORBIDDEN = ("probability", "likely", "likelihood", "percent", "rate", "accura", "chance")


def screen_case_clean(module, index, case):
    """The case (not the question) states no percentage and no rate or likelihood word; anchors
    state the sentence that fixes their answer."""
    text = case["case"].lower()
    items = items_for(module)
    anchor = items["kind"][index] == "anchor"
    if "%" in text or (not anchor and any(re.search(rf"\b{w}", text) for w in SCREEN_FORBIDDEN)):
        return False
    if anchor:
        return any(
            w in text
            for w in (
                "exactly",
                "rounds to",
                "had tested",
                "had pressure-tested",
                "had run",
                "had surveyed",
                "had received",
                "no information",
            )
        )
    return True


def screen_audit():
    """Openness per family and form: open items open (median at least OPEN_MEDIAN log-odds),
    anchors determinate (openness 0); form c's fallback items fixed under the revised observers
    (at most FIXED_OPENNESS)."""
    from epistemics.dispositions import screen

    out = {}
    for family in screen.FAMILIES:
        for form in screen.FORMS:
            items = screen.design(family, form)
            openness = screen.openness(family, form)
            anchors = items["kind"] == "anchor"
            median = float(np.median(openness[~anchors]))
            if median < screen.OPEN_MEDIAN or np.any(openness[anchors] > 1e-9):
                raise ValueError(f"screen-{family}-{form} fails the openness audit ({median:.2f})")
            out[f"{family}-{form}"] = round(median, 3)
    for family in screen.FIXED_FAMILIES:
        items = screen.design(family, screen.FIXED_FORM)
        openness = screen.openness(family, screen.FIXED_FORM)
        fixed = items["kind"] == "fixed"
        if np.max(openness[fixed]) > screen.FIXED_OPENNESS or np.any(
            openness[items["kind"] == "anchor"] > 1e-9
        ):
            raise ValueError(f"screen-{family}-c has a fallback item that is not fixed")
        out[f"{family}-c (largest fixed)"] = round(float(np.max(openness[fixed])), 3)
    return out


def cohere_audit():
    """Coherence sets: members of a set share their case text and differ in their question; the
    computable sets are fixed under the family observers (openness at most FIXED_OPENNESS); a
    "sets" order keeps members at least MIN_DISTANCE apart."""
    import random

    from epistemics.dispositions import cohere, screen

    out = {}
    for module in COHERE_MODULES:
        _, family, form = module.split("-")
        items = cohere.design(family, form)
        for _, idx, _, _, _ in cohere.sets(items):
            cases = [render(module, "markets", i, "cohere") for i in idx]
            if len({c["case"] for c in cases}) != 1 or len({c["question"] for c in cases}) != len(
                idx
            ):
                raise ValueError(f"{module}: a set's members do not share one case")
        openness = cohere.openness(family, form)
        computable = (items["computable"] == 1) & (items["kind"] == "member")
        if np.max(openness[computable]) > screen.FIXED_OPENNESS:
            raise ValueError(f"{module}: a computable set is not fixed")
        order = cohere.sets_order(items, random.Random(1))
        position = {item: k for k, item in enumerate(order)}
        for _, idx, _, _, _ in cohere.sets(items):
            gap = min(abs(position[a] - position[b]) for a in idx for b in idx if a != b)
            if gap < cohere.MIN_DISTANCE:
                raise ValueError(f"{module}: set members too close in a sets order")
        out[module] = round(
            float(np.median(openness[(items["computable"] == 0) & (items["kind"] == "member")])), 3
        )
    return out


def statement_audit():
    """Statements: the Latin square (every sequence in every condition once per form); in a
    "sequences" order each sequence's cases are consecutive and in step order; a stepwise case
    shows exactly its one change and a whole case all of them; no case names a year or a rate
    level; the probe's four questions about a statement share its case text."""
    import random

    from epistemics.dispositions import statements

    for form in statements.FORMS:
        seen = {}
        for r in statements.ROTATIONS:
            items = statements.design(form, r)
            for k, c in set(
                zip(items["sequence"].tolist(), items["condition"].tolist(), strict=True)
            ):
                if k >= 0:
                    seen.setdefault(k, []).append(c)
        if any(sorted(v) != sorted(statements.CONDITIONS) for v in seen.values()) or len(seen) != 6:
            raise ValueError(f"Statements form {form}: not a Latin square")
    for module in STATEMENT_MODULES:
        items = items_for(module)
        order = statements.sequences_order(items, random.Random(1))
        for k in set(items["sequence"].tolist()) - {-1}:
            spots = [p for p, i in enumerate(order) if items["sequence"][i] == k]
            steps = [int(items["step"][order[p]]) for p in spots]
            if spots != list(range(spots[0], spots[0] + len(spots))) or steps != sorted(steps):
                raise ValueError(f"{module}: a sequence is split or out of step order")
        for i in range(CASES):
            case = render(module, "markets", i, "statement")
            text = case["case"]
            shown = len(re.findall(r"now reads", text))
            expected = {"step": 1, "whole": int(items["n"][i])}.get(str(items["kind"][i]), 0)
            if shown != expected:
                raise ValueError(f"{module}/{i}: shows {shown} changes, not {expected}")
            if re.search(r"\b(19|20)\d\d\b", text) or "percent" in text.lower():
                raise ValueError(f"{module}/{i}: names a year or a rate level")
    for module in STATEMENT_PROBE_MODULES:
        items = items_for(module)
        for k in range(6):
            idx = np.flatnonzero(items["sequence"] == k)
            if len({render(module, "markets", int(i), "statement")["case"] for i in idx}) != 1:
                raise ValueError(f"{module}: a statement's questions do not share its case")
    from epistemics.disposition_tasks.statement_texts import STYLE_TEXT

    return {"latin_square": True, "stylistic_pairs": {k: list(v) for k, v in STYLE_TEXT.items()}}


def deliberation_audit():
    """Ladders: thresholds rising and the broad and middle observers' answers falling along each;
    a "sets" order keeps a series' questions at least 4 cases apart. Anchors: every anchored
    threshold low in one form and high in the other; each pair consecutive in a "sequences" order;
    every anchor described as chosen for the exercise and carrying no information."""
    import random

    from epistemics.dispositions import deliberation, screen, statements

    mid = screen.observer_mid("trend")
    for s in range(len(deliberation.SERIES)):
        ts = deliberation.thresholds(s)
        for params in (deliberation.BROAD, mid):
            p = [deliberation.observer(s, t, params) for t in ts]
            if any(b >= a for a, b in zip(p, p[1:], strict=False)):
                raise ValueError(f"Deliberation series {s}: the observer's ladder is not falling")
    items = items_for("deliberation-ladder")
    order = deliberation.ladder_order(items, random.Random(1))
    position = {i: k for k, i in enumerate(order)}
    for s in range(len(deliberation.SERIES)):
        idx = [int(i) for i in np.flatnonzero(items["series"] == s)]
        if min(abs(position[a] - position[b]) for a in idx for b in idx if a != b) < 4:
            raise ValueError("Deliberation ladder: a series' questions too close")
    sides = {}
    for module in DELIBERATION_ANCHOR:
        items = items_for(module)
        order = statements.sequences_order(items, random.Random(1))
        for k in set(items["sequence"].tolist()):
            spots = [p for p, i in enumerate(order) if items["sequence"][i] == k]
            if spots != [spots[0], spots[0] + 1] or items["kind"][order[spots[0]]] != "choice":
                raise ValueError(f"{module}: an anchor pair is split or out of order")
        for i in range(CASES):
            case = render(module, "markets", i, "deliberation")["case"]
            if "chosen for this exercise" not in case or "carries no information" not in case:
                raise ValueError(f"{module}/{i}: the anchor is not described as uninformative")
            if items["kind"][i] == "choice":
                key = (int(items["series"][i]), int(items["rank"][i]))
                sides.setdefault(key, set()).add(str(items["side"][i]))
    if any(v != {"low", "high"} for v in sides.values()):
        raise ValueError("Deliberation anchors: a threshold lacks a low or a high anchor")
    bare = items_for("deliberation-bare")
    asked = {(int(s), int(t)) for s, t in zip(bare["series"], bare["threshold"], strict=True)}
    anchored = {
        (int(s), int(t))
        for s, t, k in zip(items["series"], items["threshold"], items["kind"], strict=True)
        if k == "choice"
    }
    if not anchored <= asked or len(asked) != CASES:
        raise ValueError("Deliberation bare: not the anchored thresholds asked once each")
    frames = {}
    for module in DELIBERATION_FRAMES:
        items = items_for(module)
        order = statements.sequences_order(items, random.Random(1))
        for k in set(items["sequence"].tolist()):
            spots = [p for p, i in enumerate(order) if items["sequence"][i] == k]
            if spots != [spots[0], spots[0] + 1] or items["kind"][order[spots[0]]] != "frame":
                raise ValueError(f"{module}: a frame pair is split or out of order")
        first = items["kind"] == "frame"
        counts = {f: int(np.sum(items["frame"][first] == f)) for f in deliberation.FRAMES}
        if set(counts.values()) != {3}:
            raise ValueError(f"{module}: frames are not balanced")
        for i in np.flatnonzero(first):
            frames.setdefault(int(items["threshold"][i]), []).append(str(items["frame"][i]))
            if str(items["frame"][i]).startswith("comparison"):
                case = render(module, "markets", int(i), "deliberation")["case"]
                if "chosen for this exercise" not in case or "carries no information" not in case:
                    raise ValueError(f"{module}/{i}: the anchor is not described as uninformative")
    if any(sum(f.startswith("comparison") for f in v) != 1 for v in frames.values()):
        raise ValueError(
            "Deliberation frames: a threshold lacks one comparison and one other frame"
        )
    return {
        "thresholds": {
            s: list(deliberation.thresholds(s)) for s in range(len(deliberation.SERIES))
        },
        "anchored": len(sides),
    }


def announced_audit():
    """Announced count: every case under every condition once across the four forms; the count a
    case declares is the number of changes its new statement holds, each a valid move of a slot
    or a rewording, and the three-said cases' other two changes are rewordings."""
    from epistemics.disposition_tasks.announced_texts import SAID
    from epistemics.dispositions import announced
    from epistemics.dispositions import statements as st

    seen = {}
    for module in ANNOUNCED_MODULES:
        items = items_for(module)
        for i in range(CASES):
            k, condition = int(items["item"][i]), str(items["condition"][i])
            seen.setdefault(k, []).append(condition)
            spec = announced.items_spec()[k]
            held = announced.changes(spec, condition)
            if len(held) != int(items["declared"][i]) or len({name for name, _ in held}) != len(
                held
            ):
                raise ValueError(f"{module}/{i}: the declared count is not the changes held")
            for name, d in held:
                if name in st.STYLES:
                    if d != 0:
                        raise ValueError(f"{module}/{i}: a rewording with a direction")
                elif d not in (-1, 1) or not -1 <= spec["levels"][name] + d <= 1:
                    raise ValueError(f"{module}/{i}: an invalid change")
            if condition == "three-said" and any(name not in st.STYLES for name, _ in held[1:]):
                raise ValueError(f"{module}/{i}: a disclosed rewording is not a rewording")
            case = render(module, "markets", i, "announced")["case"]
            if (SAID in case) != (condition == "three-said"):
                raise ValueError(f"{module}/{i}: the rewording disclosure is wrong")
    if any(sorted(v) != sorted(announced.CONDITIONS) for v in seen.values()) or len(seen) != 24:
        raise ValueError("Announced count: not a Latin square")
    return {"cases": len(seen)}


def correlated_audit():
    """Correlated changes: each item in both orders across a pair of forms, its two changes valid
    moves of different slots that agree or disagree as declared; each pair of cases consecutive in
    a "sequences" order, the first reporting one change and the second both."""
    import random

    from epistemics.dispositions import correlated, statements

    orders = {}
    for module in CORRELATED_MODULES:
        items = items_for(module)
        order = statements.sequences_order(items, random.Random(1))
        for k in set(items["item"].tolist()):
            spots = [p for p, i in enumerate(order) if items["item"][i] == k]
            if spots != [spots[0], spots[0] + 1]:
                raise ValueError(f"{module}: a pair is split")
        for i in range(CASES):
            k = int(items["item"][i])
            spec = correlated.items_spec()[k]
            (a, da), (b, db) = spec["changes"]
            if a == b or (da == db) != spec["agree"]:
                raise ValueError(f"{module}/{i}: changes do not agree or disagree as declared")
            for slot, d in spec["changes"]:
                if not -1 <= spec["levels"][slot] + d <= 1:
                    raise ValueError(f"{module}/{i}: an invalid change")
            case = render(module, "markets", i, "correlated")["case"]
            if case.count("now reads") != int(items["step"][i]):
                raise ValueError(f"{module}/{i}: shows the wrong number of changes")
            orders.setdefault(k, set()).add(str(items["first"][i]))
    if any(len(v) != 2 for v in orders.values()) or len(orders) != 24:
        raise ValueError("Correlated changes: an item is not asked in both orders")
    return {"items": len(orders)}


def calls_audit():
    """Analysts' calls: each item in both orders across a pair of forms, its calls agreeing or
    disagreeing as declared; each pair consecutive in a "sequences" order, the first case showing
    one call and the second both; no record or rate stated."""
    import random

    from epistemics.dispositions import calls, statements

    orders = {}
    for module in CALLS_MODULES:
        items = items_for(module)
        order = statements.sequences_order(items, random.Random(1))
        for k in set(items["item"].tolist()):
            spots = [p for p, i in enumerate(order) if items["item"][i] == k]
            if spots != [spots[0], spots[0] + 1]:
                raise ValueError(f"{module}: a pair is split")
        for i in range(CASES):
            k = int(items["item"][i])
            spec = calls.items_spec()[k]
            (_, d1, _), (_, d2, _) = spec["calls"]
            if (d1 == d2) != spec["agree"]:
                raise ValueError(f"{module}/{i}: calls do not agree or disagree as declared")
            case = render(module, "markets", i, "calls")["case"]
            if case.count("“") != int(items["step"][i]):
                raise ValueError(f"{module}/{i}: shows the wrong number of calls")
            if any(w in case for w in ("right in", "record", "correct")):
                raise ValueError(f"{module}/{i}: states a record")
            orders.setdefault(k, set()).add(str(items["first"][i]))
    if any(len(v) != 2 for v in orders.values()) or len(orders) != 24:
        raise ValueError("Analysts' calls: an item is not asked in both orders")
    return {"items": len(orders)}


def wording_audit():
    """Confident wording: in each family every item at every wording the family offers across its
    forms, the same number of items at each wording in a form with directions balanced; the same
    skeleton (prior, direction, wording) in every four-wording family; urn3 the urn family's texts
    with three wordings; one quoted claim whose markers match its wording; no record stated."""
    from epistemics.dispositions import wording

    seen = {}
    skeleton = {}
    for module in WORDING_MODULES:
        family, form = wording.parse(module)
        offered = wording.levels(family)
        items = items_for(module)
        for level in offered:
            at = items["wording"] == level
            if at.sum() != CASES // len(offered) or items["direction"][at].sum() != 0:
                raise ValueError(f"{module}: wording {level} is not a balanced share of items")
        for i in range(CASES):
            k, level = int(items["item"][i]), int(items["wording"][i])
            row = (int(items["prior"][i]), int(items["direction"][i]), level)
            if len(offered) == len(wording.WORDINGS) and skeleton.setdefault((form, k), row) != row:
                raise ValueError(f"{module}/{i}: the families differ beyond their texts")
            case = render(module, "markets", i, "wording")["case"]
            claim = case[case.index("“") :]
            if case.count("“") != 1:
                raise ValueError(f"{module}/{i}: does not show exactly one claim")
            markers = ("I think" in claim, "definitely" in claim, "confirmed" in claim)
            if markers != (level == 0, level >= 2, level == 3):
                raise ValueError(f"{module}/{i}: the claim's wording does not match its level")
            if any(w in case for w in ("right in", "record", "correct", "accura")):
                raise ValueError(f"{module}/{i}: states a record")
            if wording.base(family) != family:
                ways = "one of three ways"
                twin = render(f"wording-{wording.base(family)}-{form}", "markets", i, "wording")[
                    "case"
                ]
                if (
                    ways not in case
                    or case[: case.index("“")].replace(ways, "one of four ways")
                    != twin[: twin.index("“")]
                ):
                    raise ValueError(f"{module}/{i}: differs from its family beyond the set")
            seen.setdefault((family, k), set()).add(level)
    families = {f for f, _ in seen}
    if len(seen) != 24 * len(families) or any(
        v != set(wording.levels(f)) for (f, _), v in seen.items()
    ):
        raise ValueError("Confident wording: an item is not asked at every wording")
    return {"items": len(seen)}


def followup_audit():
    """Follow-up modules: each pair consecutive in a "sequences" order and its first case the
    likely-or-unlikely form of the follow-up's question; every base case fresh in one form and a
    follow-up in the other."""
    import random

    from epistemics.disposition_tasks.followup_texts import ASK, FIRST
    from epistemics.dispositions import followup, statements

    kinds = {}
    for module in FOLLOWUP_MODULES:
        items = items_for(module)
        variant, form = followup.parse(module)
        order = statements.sequences_order(items, random.Random(1))
        for k in set(items["sequence"].tolist()):
            idx = [i for i in order if items["sequence"][i] == k]
            spots = [order.index(i) for i in idx]
            if spots != list(range(spots[0], spots[0] + len(spots))):
                raise ValueError(f"{module}: a follow-up pair is split")
            if len(idx) == 2:
                first = render(module, "markets", idx[0], "followup")
                second = render(module, "markets", idx[1], "followup")
                if first["question"] != FIRST + second["question"][len(ASK) :]:
                    raise ValueError(f"{module}: a first question does not match its follow-up")
        for i in range(CASES):
            if items["kind"][i] != "first":
                kinds.setdefault((variant, int(items["base"][i])), set()).add(str(items["kind"][i]))
    if any(v != {"fresh", "followup"} for v in kinds.values()):
        raise ValueError("Follow-up modules: a case is not asked fresh and as a follow-up")
    return {"cases": len(kinds)}


def variants_of(module):
    if module in CALLS_MODULES:
        return CALLS_VARIANTS
    if module in WORDING_MODULES:
        return WORDING_VARIANTS
    if module in CORRELATED_MODULES:
        return CORRELATED_VARIANTS
    if module in ANNOUNCED_MODULES:
        return ANNOUNCED_VARIANTS
    if module in FOLLOWUP_MODULES:
        return FOLLOWUP_VARIANTS
    if module in DELIBERATION_MODULES:
        return DELIBERATION_VARIANTS
    if module in STATEMENT_MODULES + STATEMENT_PROBE_MODULES:
        return STATEMENT_VARIANTS
    if module in COHERE_MODULES:
        return COHERE_VARIANTS
    if module in SCREEN_MODULES:
        return SCREEN_VARIANTS
    if module in V31_MODULES:
        return V31_VARIANTS
    if module in V32_MODULES:
        return V32_VARIANTS
    if module in V3_MODULES:
        return V3_VARIANTS
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
        + V3_MODULES
        + V31_MODULES
        + V32_MODULES
        + SCREEN_MODULES
        + COHERE_MODULES
        + STATEMENT_MODULES
        + STATEMENT_PROBE_MODULES
        + DELIBERATION_MODULES
        + FOLLOWUP_MODULES
        + ANNOUNCED_MODULES
        + CORRELATED_MODULES
        + CALLS_MODULES
        + WORDING_MODULES
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
                # Battery v3 shows each scenario twice, with different questions.
                keys = {
                    (c["case"], c["question"])
                    if module
                    in V3_MODULES
                    + V31_MODULES
                    + V32_MODULES
                    + SCREEN_MODULES
                    + COHERE_MODULES
                    + STATEMENT_PROBE_MODULES
                    + DELIBERATION_MODULES
                    + FOLLOWUP_MODULES
                    else c["case"]
                    for c in cases
                }
                if len(keys) != CASES:
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
                    if module in COHERE_MODULES and (
                        "%" in case["case"]
                        or (
                            items_for(module)["kind"][i] != "anchor"
                            and any(
                                re.search(rf"\b{w}", case["case"].lower()) for w in SCREEN_FORBIDDEN
                            )
                        )
                    ):
                        raise ValueError(f"{where} states a rate, a percentage or a probability")
                    if module in SCREEN_MODULES and not screen_case_clean(module, i, case):
                        raise ValueError(f"{where} states a rate, a percentage or a probability")
                    if module in V31_MODULES + V32_MODULES and case["response"] == "choice":
                        if not v31_consequences_clean(case):
                            raise ValueError(f"{where} states a number in its consequences")
                        if module in V32_MODULES and not v32_consequences_match(module, i, case):
                            raise ValueError(f"{where} shows the wrong consequences")
                        if any(w in o.lower() for o in case["options"] for w in VERDICTS):
                            raise ValueError(f"{where} has an option that presupposes a verdict")
                    if module in V3_MODULES + V31_MODULES + V32_MODULES:
                        shown = set(re.findall(r"\d+%", case["case"]))
                        if shown - set(stated_percentages(module, i, variant)):
                            raise ValueError(f"{where} shows a percentage it should not")
                        if (
                            variant == "v3-loaded"
                            and kinds[i] == "revealed"
                            and "Evidence" in case["case"]
                        ):
                            raise ValueError(f"{where} re-shows the evidence")
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
    # Battery v3: unstated properties and stakes favour neither hypothesis across the battery.
    from epistemics.dispositions import coherence

    for name, (against, towards) in coherence.balance().items():
        if abs(against - towards) > max(2, 0.15 * (against + towards)):
            raise ValueError(f"Battery v3 {name} balance {against}/{towards}")
    return {
        "modules": len(MODULES),
        "covers": len(COVERS),
        "cases": count,
        "screen_openness": screen_audit(),
        "cohere_openness": cohere_audit(),
        "statements": statement_audit(),
        "deliberation": deliberation_audit(),
        "followup": followup_audit(),
        "announced": announced_audit(),
        "correlated": correlated_audit(),
        "calls": calls_audit(),
        "wording": wording_audit(),
    }


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
    for module in V3_MODULES:
        for variant in V3_VARIANTS:
            yield module, "markets", variant, V3_RESPONDENT
    for module in V31_MODULES:
        yield module, "markets", "v31-standard", V31_RESPONDENT
    for module in V32_MODULES:
        yield module, "markets", "v32-standard", V32_RESPONDENT
    from epistemics.dispositions import screen

    for module in COHERE_MODULES:
        family = module.split("-")[1]
        truth = {"params": screen.observer_mid(family), "d": 0.08, "tau": 0.05}
        yield module, "markets", "cohere", truth
    for module in STATEMENT_MODULES:
        yield module, "markets", "statement", STATEMENT_RESPONDENT
    for module in STATEMENT_PROBE_MODULES:
        yield module, "markets", "statement", PROBE_RESPONDENT
    for module in DELIBERATION_MODULES:
        truth = {**DELIBERATION_RESPONDENT, "params": screen.observer_mid("trend")}
        yield module, "markets", "deliberation", truth
    for module in FOLLOWUP_MODULES:
        yield module, "markets", "followup", FOLLOWUP_RESPONDENT
    for module in ANNOUNCED_MODULES:
        yield module, "markets", "announced", ANNOUNCED_RESPONDENT
    for module in CORRELATED_MODULES:
        yield module, "markets", "correlated", CORRELATED_RESPONDENT
    for module in CALLS_MODULES:
        yield module, "markets", "calls", CALLS_RESPONDENT
    for module in WORDING_MODULES:
        yield module, "markets", "wording", WORDING_RESPONDENT
    for module in SCREEN_MODULES:
        family = module.split("-")[1]
        if module.endswith("-c"):
            params = screen.observer_mid(family)
        else:
            params = screen.mid(family)
        yield module, "markets", "screen", {"params": params, "noise": 0.05}


def estimate(module, analysis, truth):
    if "wording" in analysis:
        # Each case's weight against the respondent's weight for its wording.
        rows = analysis["wording"]["cases"]
        from epistemics.dispositions.wording import WORDINGS

        error = float(np.mean([abs(r["weight"] - truth["w"][WORDINGS.index(r["wording"])])
                               for r in rows]))  # fmt: skip
        return error, bool(error <= TOLERANCE["wording_weight"])
    if "calls" in analysis:
        # Each item's first step against the respondent's lambda for its first call.
        items = items_for(module)
        rows = analysis["calls"]["items"]
        errors = []
        for r in rows:
            i = int(np.flatnonzero((items["item"] == r["item"]) & (items["step"] == 1))[0])
            lam = truth["w"][int(items["first_phrase"][i])] * int(items["first_direction"][i])
            errors.append(abs(r["step1"] - lam))
        error = float(np.mean(errors))
        return error, bool(error <= TOLERANCE["correlated_step"])
    if "correlated" in analysis:
        # Each item's first step against the respondent's lambda for its first change.
        rows = analysis["correlated"]["items"]
        errors = [abs(r["step1"] - truth["w"][r["first"][0]] * r["first"][1]) for r in rows]
        error = float(np.mean(errors))
        return error, bool(error <= TOLERANCE["correlated_step"])
    if "announced" in analysis:
        # Each condition's mean step against the respondent's noiseless steps.
        from epistemics.dispositions import announced

        items = items_for(module)
        expected = {}
        for i in range(CASES):
            spec = announced.items_spec()[int(items["item"][i])]
            slot, _ = spec["target"]
            condition = str(items["condition"][i])
            n = announced.DECLARED[condition]
            if condition == "three-said":
                n = 1 + (n - 1) * truth["rewordings"]
            expected.setdefault(condition, []).append(truth["w"][slot] / (1 + truth["k"] * (n - 1)))
        means = analysis["announced"]["mean_step"]
        error = max(abs(means[c] - float(np.mean(v))) for c, v in expected.items())
        return float(error), bool(error <= TOLERANCE["announced_step"])
    if "followup" in analysis:
        # Follow-ups rounded and fresh answers not, as simulated; the stated variant's fresh
        # answers within 0.2 log-odds of the exact answers on average.
        f = analysis["followup"]
        g = f["grain"]
        gap = g["followup"]["share_5"] - g["fresh"]["share_5"]
        errors = [r["error"] for r in f["answers"] if r["kind"] == "fresh" and "error" in r]
        ok = gap >= 0.5 and (not errors or float(np.mean(errors)) <= 0.2)
        return float(gap), bool(ok)
    if "deliberation" in analysis:
        # Ladders: the readout grain; anchors: the anchoring weight against the respondent's own
        # (noiseless) answers, and every comparison consistent with its estimate.
        from epistemics.dispositions import deliberation

        d = analysis["deliberation"]
        if d["module"] == "frames":
            error = abs(d["grain"]["rho"]["mean"] - truth["rho"])
            consistent = all(r["consistent"] for r in d["pairs"] if "consistent" in r)
            return float(error), bool(error <= TOLERANCE["deliberation_rho"] and consistent)
        if d["module"] == "bare":
            error = abs(d["grain"]["rho"]["mean"] - truth["rho"])
            return float(error), bool(error <= TOLERANCE["deliberation_rho"])
        if d["module"] == "ladder":
            error = abs(d["grain"]["rho"]["mean"] - truth["rho"])
            return float(error), bool(
                error <= TOLERANCE["deliberation_rho"] and d["violations"] == 0
            )
        own = [
            {
                "series": s,
                "thresholds": list(deliberation.thresholds(s)),
                "answers": [
                    deliberation.observer(s, t, truth["params"]) for t in deliberation.thresholds(s)
                ],
            }
            for s in range(len(deliberation.SERIES))
        ]
        a = deliberation.anchoring_on_own(d["pairs"], own)
        error = abs(a - truth["a"])
        return float(error), bool(error <= TOLERANCE["deliberation_a"] and d["consistency"] == 1)
    if "statement" in analysis:
        # A Bayesian combiner's mean step on each slot's changes is its reading (beta 1, tilt 0);
        # stylistic changes move nothing; anchors at their answers.
        s = analysis["statement"]
        errors = [abs(v - truth["w"][slot]) for slot, v in s["step_readings"].items()]
        content = float(np.mean(np.abs(s["stylistic_steps"]))) if s["stylistic_steps"] else 0.0
        ok = (
            s["anchors_ok"]
            and len(errors) == len(truth["w"])
            and max(errors) <= TOLERANCE["statement_step"]
            and content <= TOLERANCE["statement_content"]
        )
        return float(max(errors)), bool(ok)
    if "statement_probe" in analysis:
        errors = [
            abs(p - truth["periods"][k])
            for row in analysis["statement_probe"]["statements"]
            for k, p in enumerate(row["periods"].values())
        ]
        return float(max(errors)), bool(max(errors) <= TOLERANCE["statement_probe"])
    if "cohere" in analysis:
        # The respondent's shrinkage recovered from all its sets, anchors at their answers.
        from epistemics.dispositions import cohere

        c = analysis["cohere"]
        items = items_for(module)
        responses = [float(v) for v in c.get("responses", [])]
        fitted = cohere.fit(items, responses) if responses else c["open"]
        error = abs(fitted["d"]["mean"] - truth["d"])
        return float(error), bool(c["anchors_ok"] and error <= TOLERANCE["cohere_d"])
    if "screen" in analysis:
        # Anchors at their answers, and each contrast within tolerance of the respondent's
        # noiseless score (the pipeline check: items, texts, order and scoring line up).
        from epistemics.dispositions import screen

        s = analysis["screen"]
        items = items_for(module)
        if s["form"] == screen.FIXED_FORM:
            # Fallback items: answers within tolerance of the observer's fixed predictions.
            fixed = np.asarray(items["kind"]) == "fixed"
            predicted = screen.predict(s["family"], items, truth["params"])[fixed]
            error = float(
                np.max(np.abs(screen.logit(s["fixed_responses"]) - screen.logit(predicted)))
            )
            return error, bool(s["anchors_ok"] and error <= TOLERANCE["screen_contrast"])
        clean = screen.contrast_scores(items, screen.predict(s["family"], items, truth["params"]))
        error = max(abs(c["score"] - clean[n]["score"]) for n, c in s["contrasts"].items())
        return float(error), bool(s["anchors_ok"] and error <= TOLERANCE["screen_contrast"])
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
    if "decisions" in analysis and analysis["decisions"]["fit"]["scheme"] == "v32":
        # Five classes leave two or three decisions per class in a session: check instead that
        # the decisions agree with the respondent's thresholds applied to its stated beliefs,
        # which fails if choices, classes or anchors are mapped wrongly.
        rows = analysis["decisions"]["trials"]
        agree = np.mean(
            [(r["stated"] > truth["thresholds"][r["cls"]]) == bool(r["act"]) for r in rows]
        )
        return float(agree), bool(agree >= TOLERANCE["v32_agreement"])
    if "decisions" in analysis:
        # One session has 14 decisions, 7-8 of them balanced (the anchors pin that threshold);
        # the ordering of classes needs pooled sessions and is checked by recovery.
        error = abs(analysis["decisions"]["fit"]["theta_balanced"]["mean"] - truth["thresholds"][1])
        return error, error <= TOLERANCE["v31_theta"]
    if "coherence" in analysis:
        c = analysis["coherence"]
        errors = [
            abs(c["beta"] - truth["beta"]),
            abs(c["calibration"]["rho"]["mean"] - truth["rho"]),
        ]
        return max(errors), errors[0] <= TOLERANCE["v3_beta"] and errors[1] <= TOLERANCE["v3_rho"]
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
