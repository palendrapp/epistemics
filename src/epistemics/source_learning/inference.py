"""Public-history observers and calibration-only parameter freezing."""

import numpy as np

from epistemics.source_inference.measurement import (
    GAINS,
    fit,
    log_likelihood,
    logsumexp,
    sample_reports,
    sigmoid,
)
from epistemics.source_inference.observers import FAMILIES, entropy, learned_weights, states
from epistemics.source_inference.world import RANDOM, distribution
from epistemics.source_learning.battery import knowledge, location


def posterior(manifest, index, answers, family):
    c, stage = location(index)
    company = manifest.companies[c]
    source_id = company.record.public.source_id
    history, selection, accuracy = knowledge(manifest, index, answers)
    support = states(family)
    weights = np.array(learned_weights(history, source_id, family))
    if family == "joint_process" and source_id in selection:
        weights *= [s.rule == selection[source_id] for s in support]
    if family != "fixed_discount" and source_id in accuracy:
        weights *= [s.accuracy == accuracy[source_id] for s in support]
    world, count = company.record.public.world, company.record.public.count
    likelihood = np.array(
        [
            [distribution(world, h, s.accuracy, s.rule)[count] for s in support]
            for h in (False, True)
        ]
    )
    if stage == "revision" and answers[index - 1].query == "customer_panel":
        panel = np.array(
            [
                distribution(world, h, 1.0, RANDOM)[company.independent_panel.count]
                for h in (False, True)
            ]
        )
        likelihood *= panel[:, None]
    if family == "fixed_discount":
        logit = np.log(company.prior_strong / (1 - company.prior_strong)) + 0.35 * np.log(
            likelihood[1, 0] / likelihood[0, 0]
        )
        p = float(sigmoid(logit))
        return np.array([[1 - p], [p]]), support
    joint = (
        likelihood * weights * np.array([1 - company.prior_strong, company.prior_strong])[:, None]
    )
    if joint.sum() <= 0:
        raise ValueError("Public evidence is outside observer support")
    return joint / joint.sum(), support


def raw_predictions(manifest, index, answers):
    result = {}
    for family in FAMILIES:
        joint, support = posterior(manifest, index, answers, family)
        weights = joint.sum(axis=0)
        result[family] = {
            "logit": float(np.log(joint[1].sum()) - np.log(joint[0].sum())),
            "probability": float(joint[1].sum()),
            "measurement_accuracy": float(weights @ [s.accuracy for s in support]),
            "random_selection_probability": float(weights @ [s.rule == RANDOM for s in support]),
        }
    return result


def research_values(manifest, index, answers, prices):
    """Myopic decision/information policies; future reuse of a source is NOT priced here."""
    c, _ = location(index)
    company = manifest.companies[c]
    joint, support = posterior(manifest, index, answers, "joint_process")
    before_p = float(joint[1].sum())
    value = max(0, before_p - company.threshold)
    branches = {"stop": [(1.0, joint)]}
    for query, key in (
        ("selection_audit", lambda s: s.rule),
        ("measurement_audit", lambda s: s.accuracy),
    ):
        branches[query] = []
        for result in dict.fromkeys(key(s) for s in support):
            branch = joint * np.array([key(s) == result for s in support])[None, :]
            mass = float(branch.sum())
            if mass > 0:
                branches[query].append((mass, branch / mass))
    panel = np.array(
        [distribution(company.record.public.world, h, 1, RANDOM) for h in (False, True)]
    )
    branches["customer_panel"] = []
    for count in range(6):
        branch = joint * panel[:, count, None]
        mass = float(branch.sum())
        if mass > 0:
            branches["customer_panel"].append((mass, branch / mass))
    return {
        query: {
            "net_myopic_value": float(
                sum(p * max(0, float(b[1].sum()) - company.threshold) for p, b in outcomes)
                - value
                - prices[query]
            ),
            "company_information_bits": max(
                0.0,
                entropy(joint.sum(axis=1)) - sum(p * entropy(b.sum(axis=1)) for p, b in outcomes),
            ),
        }
        for query, outcomes in branches.items()
    }


def matrix(locks):
    return np.array([[lock["raw"][f]["logit"] for lock in locks] for f in FAMILIES])


def calibrate(locks, answers):
    if len(locks) != 12 or len(answers) != 12:
        raise ValueError("Freeze parameters after exactly twelve calibration forecasts")
    logits = matrix(locks)
    reports = np.array([a.probability for a in answers])
    blocks = [f"company-{i + 1:02d}" for i in range(12)]
    result = fit(logits, reports, blocks)
    likelihood = log_likelihood(logits[:, None, :] * GAINS[None, :, None], reports, blocks)
    result["gain_probabilities"] = {
        f: np.exp(row - logsumexp(row)).tolist()
        for f, row in zip(FAMILIES, likelihood, strict=True)
    }
    result["baseline_mean"] = float(reports.mean())
    result["baseline_last"] = float(reports[-1])
    result["scope"] = "Frozen after calibration; no heldout response updates model weights or gains"
    return result


def forecast(raw, frozen):
    means = {}
    for family in FAMILIES:
        means[family] = float(
            np.asarray(frozen["gain_probabilities"][family]) @ sigmoid(GAINS * raw[family]["logit"])
        )
    return {
        "family_means": means,
        "mixture_mean": sum(
            means[f] * frozen["families"][f]["conditional_model_probability"] for f in FAMILIES
        ),
        "target": "Noiseless response probability, integrating calibration gain uncertainty",
    }


def analyze(manifest, observations, locks, frozen):
    reports = np.array([row.answer.probability for row in observations[12:]])
    logits = matrix(locks[12:])
    blocks = [row.trial.company_id for row in observations[12:]]
    # Treat the public path as given; no choice likelihood or selection correction is fitted.
    likelihood = log_likelihood(logits[:, None, :] * GAINS[None, :, None], reports, blocks)
    family_scores, adequacy = {}, {}
    rng = np.random.default_rng(42019)  # Analysis-only Monte Carlo, never a world seed.
    for i, family in enumerate(FAMILIES):
        posterior_gain = np.array(frozen["gain_probabilities"][family])
        with np.errstate(divide="ignore"):
            family_scores[family] = float(logsumexp(likelihood[i] + np.log(posterior_gain)))
        mean = np.array([lock["forecast"]["family_means"][family] for lock in locks[12:]])
        observed = float(100 * np.sqrt(np.mean((mean - reports) ** 2)))
        simulated_errors = []
        for _ in range(256):
            gain = float(rng.choice(GAINS, p=posterior_gain))
            simulated = sample_reports(logits[i], gain, blocks, rng)
            simulated_errors.append(float(100 * np.sqrt(np.mean((mean - simulated) ** 2))))
        boundary = float(np.quantile(simulated_errors, 0.99))
        adequacy[family] = {
            "heldout_rmse_pp": observed,
            "conditional_99_percent_simulation_boundary_pp": boundary,
            "outside_simulation_boundary": observed > boundary,
        }
    with np.errstate(divide="ignore"):
        log_weights = np.log(
            [frozen["families"][f]["conditional_model_probability"] for f in FAMILIES]
        )
    mixture_score = float(logsumexp(np.array([family_scores[f] for f in FAMILIES]) + log_weights))
    predictions = {
        "frozen_mixture": [row["forecast"]["mixture_mean"] for row in locks[12:]],
        "fixed_joint_observer": [row["raw"]["joint_process"]["probability"] for row in locks[12:]],
        "calibration_mean": [frozen["baseline_mean"]] * 24,
        "last_calibration_report": [frozen["baseline_last"]] * 24,
    }
    errors = {
        key: float(100 * np.sqrt(np.mean((np.array(values) - reports) ** 2)))
        for key, values in predictions.items()
    }
    decisions = []
    final = []
    research = []
    for i, row in enumerate(observations):
        c, stage = location(i)
        company = manifest.companies[c]
        p, threshold = row.answer.probability, company.threshold
        consistent = abs(p - threshold) < 1e-9 or (row.answer.decision == "invest") == (
            p > threshold
        )
        decisions.append(consistent)
        if stage == "research":
            values = locks[i]["myopic_research_values"]
            sets = {}
            for field in ("net_myopic_value", "company_information_bits"):
                maximum = max(v[field] for v in values.values())
                sets[field] = sorted(
                    q for q, v in values.items() if abs(v[field] - maximum) < 1e-10
                )
            research.append(
                {
                    "company_id": company.company_id,
                    "chosen": row.answer.query,
                    "optimal_sets": sets,
                    "myopic_value_gap": max(v["net_myopic_value"] for v in values.values())
                    - values[row.answer.query]["net_myopic_value"],
                    "scope": "One-company observer comparison; excludes the value of learning for later companies",
                }
            )
        if stage in ("forecast", "revision"):
            research_cost = (
                0
                if stage == "forecast"
                else observations[i - 1].trial.research_costs[observations[i - 1].answer.query]
            )
            truth = company.record.public.resolved_strong
            payoff = (
                float(truth) - threshold if row.answer.decision == "invest" else 0
            ) - research_cost
            final.append(
                {"company_id": company.company_id, "brier": (p - truth) ** 2, "payoff": payoff}
            )
    return {
        "response_origin": manifest.response_origin,
        "model_parameters_are_passport_traits": False,
        "condition": manifest.condition,
        "checkpoints": 36,
        "initial_forecasts": 24,
        "revised_forecasts": 12,
        "diagnostic_reports": 48 if manifest.condition == "dense" else 0,
        "heldout_behavior_rmse_pp": errors,
        "heldout_report_log_predictive_likelihood": {
            "frozen_mixture": mixture_score,
            **family_scores,
        },
        "conditional_adequacy": adequacy,
        "all_candidates_inadequate": all(
            r["outside_simulation_boundary"] for r in adequacy.values()
        ),
        "decision_consistency": {"consistent": sum(decisions), "denominator": 36},
        "final_outcome_scores": final,
        "mean_final_brier": float(np.mean([row["brier"] for row in final])),
        "total_realized_payoff": float(sum(row["payoff"] for row in final)),
        "research_counts": {
            q: sum(row.answer.query == q for row in observations)
            for q in ("customer_panel", "selection_audit", "measurement_audit", "stop")
        },
        "research_policy_comparisons": research,
        "uncertainty_scope": "Conditional simulation envelope, not a calibrated composite test; 6 recurring sources, not 36 independent participants",
    }
