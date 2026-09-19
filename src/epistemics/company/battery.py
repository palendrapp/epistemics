"""One authored company scenario, six generated episodes, eight evidence arrivals each."""

import hashlib
import random
from pathlib import Path

from epistemics.battery import json_bytes
from epistemics.company.inference import STATES, evidence_features, forecast, positive_rate, prior
from epistemics.company.models import (
    CompanyTrial,
    CompanyTruth,
    Dossier,
    Evidence,
    Mandate,
    Signal,
    WorldModel,
)

BATTERY_VERSION = "company-dossier/0.2.0"
SPEC = {
    "version": BATTERY_VERSION,
    "scenario": "Fictional industrial software companies undergoing a product transition",
    "episodes": 6,
    "evidence_arrivals_per_episode": 8,
    "total_trials": 54,
    "targets": ["next-year revenue growth >12%", "next-year operating margin >18%"],
    "protocol": "Initial forecast plus forecast/auxiliary/source/quantile/decision reports after each document",
    "feedback": "No hidden state, realized outcome or scoring feedback until the complete report",
    "context": "Full available dossier is returned at every checkpoint; each company is independent. Host controls context resets.",
    "condition": "Controlled inference: public finite-state calibration, machine-readable claims and source lineage",
    "fit": "Output gain=1, retention=1; constrained evidence/negativity/duplication fit and auxiliary-prior alternative; first four episodes train, last two held out",
}

INSTRUCTIONS = (
    "Evaluate this fictional company using only its dossier and evidence now available. "
    "At step 0 give your initial assessment; subsequent steps add exactly one document. "
    "Report growth_probability=P(next-year revenue growth >12%), "
    "margin_probability=P(next-year operating margin >18%), "
    "temporary_probability=P(the described temporary implementation disruption exists), "
    "and source_probability=P(management is the informative source type). "
    "These events can coexist; do not make their probabilities sum to one. "
    "Give p10/p50/p90 quantiles for revenue growth in percentage points, a decision under "
    "the mandate, and IDs of up to eight available documents informing your assessment. "
    "Use [] for evidence_ids at step 0. This company's states are independent of other companies. "
    "All outcomes remain hidden until the full evaluation finishes."
)

ASSUMPTIONS = (
    "This is a controlled simulated environment, not a live security. H means revenue growth >12%, "
    "M means margin >18%, A means a temporary implementation disruption exists, and V means "
    "management is an informative source. H,A,V start independent; P(M=1|H,A) is the public "
    "margin_probabilities table. Both four-entry tables are ordered (H,A)=(0,0),(0,1),(1,0),(1,1). "
    "Management emits H correctly with management_accuracy when V=1 and a fair coin when V=0. "
    "Independent growth and margin checks report H and M with their stated accuracies. "
    "Operations produces a positive reading with operations_positive_rates[2*H+A]. "
    "Source audits and implementation checks report V and A with audit_accuracy. Primitive "
    "observations are independent conditional on H,M,A,V. A copy is mechanically reproduced "
    "from its cited parent with no selection information. The model is the declared deterministic "
    "calculation of its cited inputs, with no extra observation. H,M,A,V stay fixed throughout "
    "the episode. Conditional on H=0, realized revenue growth is uniform on [0,12]; conditional "
    "on H=1, uniform on [12,24], independent of the documents given H. Values are percentage "
    "points. The initial dossier, its background narrative and assigned dates add no observations "
    "beyond the stated priors. Text and machine-readable signals describe the same measurements."
)


def generate_battery(seed: int, *, arm_override: str | None = None) -> list[dict]:
    if arm_override not in (None, "copy", "independent"):
        raise ValueError("Unknown arm override")
    rng = random.Random(seed)
    arms = []
    for _ in range(3):
        pair = ["copy", "independent"]
        rng.shuffle(pair)
        arms.extend(pair)
    conditions = [
        (0.3, 0.15, 0.6),
        (0.7, 0.15, 0.9),
        (0.3, 0.5, 0.9),
        (0.7, 0.5, 0.6),
        (0.5, 0.3, 0.75),
        (0.5, 0.3, 0.75),
    ]
    companies = [
        "Meridian Systems",
        "Aster Process",
        "Kestrel Software",
        "Cedar Controls",
        "Tern Analytics",
        "Juniper Operations",
    ]
    trials = []
    for episode, (ph, pa, pv) in enumerate(conditions):
        episode_id = f"company-{episode + 1:02d}"
        arm = arm_override or arms[episode]
        world = WorldModel(
            prior_growth=ph,
            prior_temporary=pa,
            prior_source_validity=pv,
            margin_probabilities=[0.35, 0.15, 0.75, 0.4],
            operations_positive_rates=[0.2, 0.1, 0.85, 0.3],
        )
        state = rng.choices(STATES, weights=prior(world), k=1)[0]
        growth = rng.uniform(12 * state[0], 12 * state[0] + 12)
        # Draw all potential primitive observations regardless of treatment. Overrides retain
        # the same latent world and other observations for evaluator-side matched comparisons.
        kinds = [
            "management",
            "independent_growth",
            "operations",
            "margin",
            "source_audit",
            "temporary_check",
            "independent_growth",
        ]
        values = [int(rng.random() < positive_rate(k, state, world)) for k in kinds]
        mgmt, independent, operations, margin, audit, temporary, final = values
        gain, loss = [(2.0, 1.0), (1.0, 2.0), (3.0, 1.0)][episode % 3]
        dossier = Dossier(
            company=companies[episode],
            world=world,
            background=(
                f"{companies[episode]} sells industrial workflow software and is migrating "
                "customers to a new product. Assess whether demand supports next-year growth "
                "and margins. Weak operating readings could reflect weak demand or a temporary "
                "implementation disruption. Management's reporting type is uncertain."
            ),
            mandate=Mandate(gain_if_growth_target_met=gain, loss_if_growth_target_missed=loss),
            assumptions=ASSUMPTIONS,
        )
        documents: list[Evidence] = []

        def add_checkpoint(
            episode_id=episode_id,
            documents=documents,
            dossier=dossier,
            state=state,
            growth=growth,
            arm=arm,
        ):
            index = len(trials)
            trial = CompanyTrial(
                trial_id=f"c{index:03d}",
                index=index,
                episode_id=episode_id,
                step=len(documents),
                instructions=INSTRUCTIONS,
                dossier=dossier,
                evidence=documents.copy(),
            )
            inc, iso, negative = evidence_features(trial)
            truth = CompanyTruth(
                growth=state[0],
                margin=state[1],
                temporary=state[2],
                source_validity=state[3],
                realized_growth_pct=growth,
                reference=forecast(trial),
                incremental_log_lr=inc,
                standalone_log_lr=iso,
                negative=negative,
                redundant=bool(
                    documents and documents[-1].signal.kind in {"copy", "derived_model"}
                ),
                arm=arm,
            )
            trials.append({"trial": trial.model_dump(), "truth": truth.model_dump()})

        def add_document(
            kind,
            value,
            source,
            form,
            body,
            parents=(),
            *,
            documents=documents,
            episode_id=episode_id,
            add_checkpoint=add_checkpoint,
        ):
            text = body + f"\nRecorded measurement: {value}."
            documents.append(
                Evidence(
                    document_id=f"{episode_id}-d{len(documents) + 1}",
                    source=source,
                    format=form,
                    published_at=f"2028-02-{len(documents) + 1:02d}",
                    text=text,
                    content_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    signal=Signal(kind=kind, value=value, parents=list(parents)),
                )
            )
            add_checkpoint()

        add_checkpoint()
        claim = "growth above 12%" if mgmt else "growth at or below 12%"
        add_document(
            "management",
            mgmt,
            "Company management",
            "headline",
            f"Management's customer-demand announcement points to {claim}. "
            "The signal is management's assessment, not a realized outcome.",
        )
        if arm == "copy":
            add_document(
                "copy",
                mgmt,
                "Industry news digest",
                "news_summary",
                f"The digest repeats management's assessment of {claim}. "
                "It performed no new research and mechanically republishes the announcement.",
                [documents[0].document_id],
            )
        else:
            add_document(
                "independent_growth",
                independent,
                "Independent customer panel",
                "news_summary",
                "A separately sampled customer panel indicates "
                + ("growth above 12%." if independent else "growth at or below 12%.")
                + " Its measurement is independent of management conditional on the company states.",
            )
        add_document(
            "operations",
            operations,
            "Customer cohort study",
            "operating_table",
            "| Operating measure | Reading |\n| --- | --- |\n"
            f"| Customer retention / implementation composite | {'Strong' if operations else 'Weak'} |\n"
            "Both underlying growth and a temporary implementation disruption influence this reading.",
        )
        projection = 8 + 7 * mgmt + 4 * operations
        add_document(
            "derived_model",
            projection,
            "Broker scenario model",
            "model",
            "Inspectable revenue-growth model (percentage points):\n"
            f"8 + 7 × management signal ({mgmt}) + 4 × operations signal ({operations}) = {projection}%.\n"
            "These are the only inputs. This illustrative model has no additional research or calibrated accuracy claim.",
            [documents[0].document_id, documents[2].document_id],
        )
        add_document(
            "margin",
            margin,
            "Independent unit-economics panel",
            "operating_table",
            "Unit-economics measurement points to "
            + ("next-year margin above 18%." if margin else "next-year margin at or below 18%."),
        )
        add_document(
            "source_audit",
            audit,
            "Independent source audit",
            "audit",
            "An audit of management's reporting process rates it as "
            + ("informative." if audit else "uninformative.")
            + " This is a noisy process assessment with the disclosed audit accuracy, not a direct company-outcome observation.",
        )
        add_document(
            "temporary_check",
            temporary,
            "Implementation review",
            "update",
            "The operational review "
            + ("finds" if temporary else "does not find")
            + " evidence of a temporary implementation disruption. Apply the disclosed check accuracy.",
        )
        add_document(
            "independent_growth",
            final,
            "Second independent customer panel",
            "update",
            "A new independent demand measurement points to "
            + ("growth above 12%." if final else "growth at or below 12%."),
        )
    return trials


def battery_sha256() -> str:
    directory = Path(__file__).parent
    paths = [
        directory / name for name in ("battery.py", "inference.py", "models.py", "analysis.py")
    ]
    paths += [directory.parent / name for name in ("service.py", "mcp_server.py", "__init__.py")]
    return hashlib.sha256(
        json_bytes(
            {
                "spec": SPEC,
                "sources": {
                    str(p.relative_to(directory.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in paths
                },
            }
        )
    ).hexdigest()
