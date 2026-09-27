"""Compact public contracts, information-equivalent to source-verification 0.2.

Each checkpoint carries only the fields that vary; fixed protocol text, world constants and
field definitions travel once in describe(). expand() regenerates the exact 0.2 public trial,
and present() refuses any checkpoint whose compact form does not expand back to it.
"""

from epistemics.source_compact import VERSION
from epistemics.source_delivery.presentation import STAGES as DELIVERY_STAGES
from epistemics.source_selective import VERSION as SELECTIVE_VERSION
from epistemics.source_selective.presentation import LABELS, Answer
from epistemics.source_selective.presentation import describe as describe_v2
from epistemics.source_selective.presentation import present as present_v2

__all__ = ["Answer", "describe", "expand", "present"]

WORLD = {"panel_size": 5, "strong_rate": 0.7, "weak_rate": 0.3}
CONSTANTS = {
    "customers_per_panel": 5,
    "expansion_probability_given_strong_demand": 0.7,
    "expansion_probability_given_weak_demand": 0.3,
}
STAGES = {
    "forecast": "Final forecast and decision. Demand is revealed after this answer.",
    "provisional": "Provisional forecast and decision before the assigned check. Do not choose a check.",
    "revision": "Final forecast and decision. Demand is revealed after this answer.",
}
FIELDS = {
    "source_report": "How many of five customers the reporting source says are expanding.",
    "source_history": (
        "Every resolved record from this source, oldest first. Each entry is the reported count "
        "of five customers expanding, followed by S if demand later proved strong or W if weak. "
        "The first twelve entries are the balanced archive; later entries are companies "
        "completed in this collection."
    ),
    "prior_strong": "Probability of strong demand before the source report.",
    "decision_threshold": (
        "Investing earns 1 minus this threshold if demand is strong and loses the threshold if "
        "weak. Declining earns zero."
    ),
    "check": (
        "available_check_cost is the independent-sample price offered for this company. "
        "charged_cost is what you pay: null until your provisional answer determines it under "
        "the cost-aware policy. check_supplied says whether an independent sample arrived. A "
        "charged cost is deducted even if you decline."
    ),
    "independent_sample": (
        "How many of five customers expanded in the independent sample: an accurately recorded "
        "fresh random panel sharing no customers or measurement errors with the source's panels. "
        "Present only when a check was supplied."
    ),
}
WORKFLOW = (
    "Call get_trial once to begin. Each submit_answer receipt includes any company resolved by "
    "that answer and next_trial, the checkpoint now awaiting your answer, so get_trial is only "
    "needed to recover. get_history restores earlier checkpoints and your accepted answers."
)
REPORT = ("", " reports exactly ", " of five customers expanding.")
SAMPLE = (
    "The independent check accurately records a fresh random panel: ",
    " of five customers expanded. It shares no customers or measurement errors with the "
    "source's panels.",
)
NO_CHECK = "The assigned policy supplied no check; there is no additional company evidence."
SAMPLE_COST = "The assigned sample costs {:.2f} points, including if you decline."
NO_CHECK_COST = "No check was assigned: no new evidence has arrived and the check cost is zero."


def describe(base, policy):
    result = describe_v2(base, policy)
    result.update(
        battery_version=VERSION,
        delivery="compact",
        constants=CONSTANTS,
        field_definitions=FIELDS,
        stage_instructions=STAGES,
        workflow=WORKFLOW,
    )
    return result


def _history(full):
    entries = []
    for row in full["archive"]:
        if row["source_id"] != full["source_id"] or row["world"] != WORLD:
            raise ValueError("Compact history requires one source and the disclosed world")
        entries.append(f"{row['count']}{'S' if row['resolved_strong'] else 'W'}")
    return " ".join(entries)


def _count(text, prefix, suffix):
    if not (text.startswith(prefix) and text.endswith(suffix)):
        raise ValueError("Unexpected public document")
    return int(text[len(prefix) : len(text) - len(suffix)])


def _compact(full):
    if (
        full["known_selection"] is not None
        or full["known_measurement_accuracy"] is not None
        or full["request_diagnostics"]
    ):
        raise ValueError("Compact delivery covers the sparse assigned-check protocol only")
    result = {
        "trial_id": full["trial_id"],
        "checkpoint": full["checkpoint"],
        "company_id": full["company_id"],
        "stage": full["stage"],
        "instruction": STAGES[full["stage"]],
        "source_id": full["source_id"],
        "prior_strong": full["prior_strong"],
        "decision_threshold": full["decision_threshold"],
        "source_report": _count(full["documents"][0], full["source_id"] + REPORT[1], REPORT[2]),
        "source_history": _history(full),
    }
    if "assigned_verification" in full:
        v = full["assigned_verification"]
        result["check"] = {
            k: v[k] for k in ("available_check_cost", "charged_cost", "check_supplied") if k in v
        }
    if len(full["documents"]) == 4 and full["documents"][3] != NO_CHECK:
        result["independent_sample"] = _count(full["documents"][3], *SAMPLE)
    return result


def expand(trial, policy):
    """Regenerate the complete 0.2 public trial from a compact checkpoint."""
    stage, threshold = trial["stage"], trial["decision_threshold"]
    documents = [
        f"{trial['source_id']}{REPORT[1]}{trial['source_report']}{REPORT[2]}",
        f"Before this report, the probability of strong demand is {trial['prior_strong']:.0%}.",
        f"Investing earns {1 - threshold:.2f} points for strong demand and loses "
        f"{threshold:.2f} for weak demand. Declining earns zero, before research costs.",
    ]
    full = {
        "schema_version": "epistemics.source-selective-trial.v1",
        "battery_version": SELECTIVE_VERSION,
        "trial_id": trial["trial_id"],
        "checkpoint": trial["checkpoint"],
        "company_id": trial["company_id"],
        "stage": stage,
        "source_id": trial["source_id"],
        "prior_strong": trial["prior_strong"],
        "decision_threshold": threshold,
        "documents": documents,
        "archive": [
            {
                "count": int(entry[:-1]),
                "resolved_strong": {"S": True, "W": False}[entry[-1]],
                "source_id": trial["source_id"],
                "world": dict(WORLD),
            }
            for entry in trial["source_history"].split()
        ],
        "known_selection": None,
        "known_measurement_accuracy": None,
        "request_diagnostics": False,
        "research_costs": {},
        "research_options": {},
        "diagnostic_definitions": {},
    }
    check = trial.get("check")
    if stage == "forecast":
        full["stage_instruction"] = DELIVERY_STAGES["forecast"]
    elif stage == "provisional":
        full["stage_instruction"] = (
            "Commit your best provisional forecast and decision before the assigned check. "
            "Do not submit a research choice. Demand remains hidden until your final answer."
        )
        full["assigned_verification"] = {
            "policy": policy,
            "available_check_cost": check["available_check_cost"],
            "charged_cost": check["charged_cost"],
            "description": LABELS[policy],
        }
    else:
        supplied = check["check_supplied"]
        full["stage_instruction"] = (
            "Commit your final forecast and decision. Demand is revealed only after this answer. "
            + (SAMPLE_COST.format(check["available_check_cost"]) if supplied else NO_CHECK_COST)
        )
        full["assigned_verification"] = {
            "policy": policy,
            "available_check_cost": check["available_check_cost"],
            "charged_cost": check["charged_cost"],
            "check_supplied": supplied,
            "description": "Independent sample supplied." if supplied else "No check supplied.",
        }
        documents.append(
            f"{SAMPLE[0]}{trial['independent_sample']}{SAMPLE[1]}" if supplied else NO_CHECK
        )
    return full


def present(trial, binding):
    full = present_v2(trial, binding)
    result = _compact(full)
    if expand(result, binding["policy"]) != full:
        raise ValueError("Compact presentation must preserve every 0.2 public field")
    return result
