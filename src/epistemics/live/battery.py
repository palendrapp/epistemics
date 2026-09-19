"""Discovery first, then balanced calibration; only current materials are public."""

import hashlib
from pathlib import Path

from epistemics.battery import BATTERY_SHA256, json_bytes
from epistemics.battery import generate_battery as belief_battery
from epistemics.discovery import battery as discovery
from epistemics.live import PROTOCOL_VERSION
from epistemics.live.models import CoreTrial

GUIDE = {
    "title": "How do you use evidence?",
    "description": "Assess a fictional company as information arrives, then answer short probability questions. The same tasks and scoring are used for human and agent participants.",
    "sections": [
        {
            "name": "Company discovery",
            "checkpoints": 10,
            "description": "Use source histories and new documents to update your assessment.",
        },
        {
            "name": "Probability calibration",
            "checkpoints": 24,
            "description": "Combine a starting probability with one observation in each independent case.",
        },
    ],
    "instructions": [
        "Use the supplied material. Give your own assessment; no explanation of private reasoning is required.",
        "Probabilities range from 0 to 100%. The MCP interface represents the same scale as 0 to 1.",
        "For growth forecasts, give the 10th, 50th and 90th percentiles. These are values of growth, not confidence ratings.",
        "The 10th percentile means a 10% chance growth falls below that value; the median means 50%, and the 90th percentile means 90%.",
        "Accepted answers are final. You can pause, return later and review your previous answers.",
        "The full discovery history remains available. Calibration questions concern separate cases, with no carryover between their hypotheses.",
        "There is no time limit. Declare any tools or assistance you use. Your results and answers are saved locally and remain private.",
        "Outcomes and scoring are revealed only after all 34 checkpoints are complete.",
    ],
    "practice": {
        "prompt": "Practice the probability scale: if an event happens in 25 out of 100 comparable cases, what probability would you enter?",
        "answer_percent": 25,
        "explanation": "Enter 25% in the browser, or 0.25 through MCP. This example is not scored.",
    },
}


def instructions_digest():
    return hashlib.sha256(json_bytes(GUIDE)).hexdigest()


def protocol_digest():
    root = Path(__file__).parent
    package = root.parent
    dependencies = [
        package / name
        for name in [
            "analysis.py",
            "battery.py",
            "models.py",
            "participants.py",
            "company/models.py",
        ]
    ]
    dependencies += list((package / "discovery").glob("*.py"))
    dependencies += list((package / "passport").glob("*.py"))
    sources = {
        str(path.relative_to(package)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted([*root.rglob("*"), *dependencies])
        if path.suffix in {".py", ".js", ".css", ".html"}
    }
    return hashlib.sha256(
        json_bytes(
            {
                "version": PROTOCOL_VERSION,
                "guide": GUIDE,
                "order": ["discovery:10", "calibration:24"],
                "belief": BATTERY_SHA256,
                "discovery": discovery.battery_sha256(),
                "sources": sources,
            }
        )
    ).hexdigest()


def describe():
    return {
        "protocol_version": PROTOCOL_VERSION,
        "protocol_sha256": protocol_digest(),
        "total_trials": 34,
        "guide": GUIDE,
        "instructions_sha256": instructions_digest(),
    }


def module_seed(seed, name):
    return int.from_bytes(hashlib.sha256(f"{seed}:{name}".encode()).digest()[:6], "big")


def discovery_instructions(target):
    event = "exceeds 12%" if target == "growth_above_12" else "is at or below 12%"
    return (
        f"Estimate the probability that next-year revenue growth {event}. "
        "Your three growth percentiles always describe revenue growth itself. "
        "Invest pays +2 if growth exceeds 12%, otherwise −1; hold pays zero. "
        "Choose the action with the highest expected payoff, using linear utility. Hold on a tie. "
        "There are no switching costs or accumulated positions. "
        "For each requested source, estimate the chance its next comparable raw estimate is within "
        "2 percentage points of a later audit, without correcting its bias. "
        "When asked about no disruption, estimate the chance growth exceeds 12% assuming a reliable "
        "inspection establishes no implementation disruption, regardless of the main event wording. "
        "For extraction questions, renewal_estimate_pct means the figure in Morrow's renewal note; "
        "model_projection_pct means the stated broker-model output. Copy the stated figure. "
        "Select the available documents you used. An alternative explanation is optional."
    )


def generate(seed):
    if type(seed) is not int or not 0 <= seed < 2**52:
        raise ValueError("Seed must be an evaluator-side integer in [0, 2**52)")
    discovery_rows = discovery.generate_battery(module_seed(seed, "discovery"))
    calibration_rows = belief_battery(module_seed(seed, "calibration"))[:24]
    rows = []
    for index, row in enumerate(discovery_rows + calibration_rows):
        payload = row["trial"].copy()
        if index < 10:
            payload["instructions"] = discovery_instructions(payload["target_event"])
        else:
            payload["instructions"] = (
                "This is an independent case. H is either true (1) or false (0). "
                "The starting probability of H being true is given below. A sensor reports the "
                "correct value with the stated accuracy for either value of H. After seeing its "
                "signal, what is the probability that H is true?"
            )
        trial = CoreTrial(
            trial_id=f"core-{index:02d}",
            index=index,
            module="discovery" if index < 10 else "calibration",
            module_index=index if index < 10 else index - 10,
            payload=payload,
        )
        rows.append({"trial": trial.model_dump(mode="json"), "truth": row["truth"]})
    return rows
