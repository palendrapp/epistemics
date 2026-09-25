import hashlib
import json
from itertools import product
from math import exp, pi, sqrt

import numpy as np
import pytest
from pydantic import ValidationError

from epistemics.source_inference.design import choose_design, predictions, worked_example
from epistemics.source_inference.measurement import (
    BLOCK_SD,
    INDEPENDENT_SD,
    bin_edges,
    expected_model_information,
    fit,
    log_likelihood,
    normal_bin_probability,
)
from epistemics.source_inference.observers import (
    FAMILIES,
    best_actions,
    posterior,
    predict,
    research_values,
    source_summary,
)
from epistemics.source_inference.report import fingerprint, run
from epistemics.source_inference.world import (
    RANDOM,
    RULES,
    PrivateRecord,
    Probe,
    PublicRecord,
    Rule,
    Source,
    World,
    archive,
    distribution,
    draw_record,
    render,
)


@pytest.mark.parametrize("direction", ["minimum", "maximum"])
def test_order_distribution_against_enumerated_true_and_noisy_private_records(direction):
    # Independent enumeration of all true panels and measurement errors, not CDF arithmetic.
    w = World(panel_size=2)
    accuracy = 0.8
    expected = np.zeros(3)
    for true in product((0, 1), repeat=4):
        true_mass = np.prod([0.7 if x else 0.3 for x in true])
        for correct in product((0, 1), repeat=4):
            error_mass = np.prod([accuracy if x else 1 - accuracy for x in correct])
            measured = [x if c else 1 - x for x, c in zip(true, correct, strict=True)]
            counts = [sum(measured[:2]), sum(measured[2:])]
            k = min(counts) if direction == "minimum" else max(counts)
            expected[k] += true_mass * error_mass
    actual = distribution(w, True, accuracy, Rule(panels=2, direction=direction))
    assert actual == pytest.approx(expected, abs=1e-14)


def test_selection_example_and_no_information_boundary():
    assert [round(100 * r["posterior_strong"], 2) for r in worked_example()] == [
        92.70,
        79.93,
        39.30,
    ]
    for rule in RULES:
        assert distribution(World(), True, 0.5, rule) == pytest.approx(
            distribution(World(), False, 0.5, rule)
        )
        weak = distribution(World(), False, 0.95, rule)
        assert sum(weak) == pytest.approx(1)
        assert min(weak) >= 0
    for i in (1, 3):
        maximum = distribution(World(), True, 0.8, RULES[i])
        minimum = distribution(World(), False, 0.8, RULES[i + 1])
        assert maximum == pytest.approx(minimum[::-1])


def test_generated_records_match_exact_distribution_and_validate_selected_ledger():
    source = Source(source_id="s", measurement_accuracy=0.85, rule=RULES[1])
    rng = np.random.default_rng(342)
    counts = np.zeros(6)
    for _ in range(5000):
        row = draw_record(rng, source, World(), False)
        counts[row.public.count] += 1
    assert counts / 5000 == pytest.approx(distribution(World(), False, 0.85, RULES[1]), abs=0.025)
    bad = row.model_dump()
    bad["public"]["count"] = (row.public.count + 1) % 6
    with pytest.raises(ValidationError, match="Published count"):
        PrivateRecord.model_validate(bad)


def test_contracts_reject_invalid_rules_counts_private_fields_and_nonfinite_values():
    with pytest.raises(ValidationError, match="One panel"):
        Rule(panels=1, direction="maximum")
    with pytest.raises(ValidationError, match="One panel"):
        Rule(panels=4, direction="random")
    with pytest.raises(ValidationError, match="Count exceeds"):
        Probe(source_id="s", count=6)
    with pytest.raises(ValidationError):
        Source(source_id="s", measurement_accuracy=float("nan"), rule=RANDOM)
    with pytest.raises(ValidationError):
        PublicRecord(
            source_id="s", world=World(), count=3, resolved_strong=True, measurement_accuracy=0.9
        )
    with pytest.raises(ValueError):
        archive(1, 3)


def test_public_history_is_the_only_source_of_learning_and_source_names_are_exchangeable():
    private = archive(17)
    history = tuple(r.public for r in private)
    probe = Probe(source_id="source-3", count=4)
    before = [predict(history, probe, f) for f in FAMILIES]
    renamed = tuple(r.model_copy(update={"source_id": "alias-" + r.source_id}) for r in history)
    renamed_probe = probe.model_copy(update={"source_id": "alias-" + probe.source_id})
    assert [predict(renamed, renamed_probe, f) for f in FAMILIES] == pytest.approx(before)
    # No private source parameters, candidate panels or truth for the unresolved probe are serialized.
    public_json = json.dumps([r.model_dump(mode="json") for r in history])
    for key in (
        "measurement_accuracy",
        "true_panels",
        "measured_panels",
        "selected_index",
        "direction",
    ):
        assert key not in public_json
    assert "unconfirmed" not in render(probe)
    assert "not been audited" in render(probe)
    learned = source_summary(history, probe.source_id, "joint_process")["rule_probabilities"]
    assert learned["maximum:10"] > learned["random:1"]
    assert learned != source_summary((), probe.source_id, "joint_process")["rule_probabilities"]


def test_random_sampling_audit_makes_joint_and_flat_identical_but_selected_audit_does_not():
    history = tuple(r.public for r in archive(23))
    for source in ("source-0", "source-3", "source-5"):
        for count in (1, 4):
            probe = Probe(source_id=source, count=count, disclosed_rule=RANDOM)
            assert predict(history, probe, "joint_process") == pytest.approx(
                predict(history, probe, "flat_accuracy")
            )
    probe = Probe(source_id="source-3", count=4, disclosed_rule=RULES[3])
    assert (
        abs(predict(history, probe, "joint_process") - predict(history, probe, "flat_accuracy"))
        > 0.1
    )
    unsupported = probe.model_copy(update={"disclosed_rule": Rule(panels=2, direction="maximum")})
    with pytest.raises(ValueError, match="outside"):
        posterior(history, unsupported, "joint_process")


def test_report_bins_normalize_including_endpoints_and_tail_probabilities():
    lower, upper = bin_edges(np.arange(101) / 100)
    for mean in (-30, -2, 0, 2, 30):
        p = normal_bin_probability(lower, upper, mean, 0.2)
        assert p.sum() == pytest.approx(1, abs=1e-12)
        assert np.min(p) >= 0
    assert normal_bin_probability(np.array([8.0]), np.array([9.0]), 0, 1)[0] > 0
    with pytest.raises(ValueError, match="whole percentages"):
        bin_edges([0.351])
    with pytest.raises(ValueError, match="finite"):
        bin_edges([np.nan])


def test_correlated_response_likelihood_matches_independent_numerical_integration():
    means, reports = np.array([0.2, -0.3]), np.array([0.6, 0.45])
    lower, upper = bin_edges(reports)
    offsets = np.linspace(-1.2, 1.2, 10001)
    mass = normal_bin_probability(lower, upper, means + offsets[:, None], INDEPENDENT_SD).prod(
        axis=1
    )
    density = np.exp(-0.5 * (offsets / BLOCK_SD) ** 2) / (sqrt(2 * pi) * BLOCK_SD)
    expected = float(np.trapezoid(mass * density, offsets))
    assert exp(float(log_likelihood(means, reports, ["s", "s"]))) == pytest.approx(
        expected, rel=1e-6
    )
    independent = float(log_likelihood(means, reports, ["s1", "s2"]))
    assert abs(independent - float(log_likelihood(means, reports, ["s", "s"]))) > 0.01


def test_uninformative_data_leave_models_and_gains_unidentified():
    result = fit(np.zeros((3, 8)), np.full(8, 0.5), ["s"] * 8)
    assert result["decision"] == "ambiguous"
    for row in result["families"].values():
        assert row["conditional_model_probability"] == pytest.approx(1 / 3)
        assert len(row["tied_gains"]) == 13
    assert expected_model_information(np.zeros((3, 2))) == pytest.approx([0, 0])


def test_research_accounts_for_price_payoffs_and_irrelevant_information():
    history = tuple(r.public for r in archive(41))
    p = Probe(source_id="source-0", count=2)
    cheap = {
        "customer_panel": 0.001,
        "selection_audit": 0.001,
        "measurement_audit": 0.001,
        "unrelated_audit": 0.001,
        "stop": 0,
    }
    values = research_values(history, p, costs=cheap)
    assert "stop" not in best_actions(values, "net_decision_value")
    assert values["unrelated_audit"]["company_information_bits"] == pytest.approx(0, abs=1e-12)
    assert values["unrelated_audit"]["total_information_bits"] == 1
    assert values["unrelated_audit"]["gross_decision_value"] == pytest.approx(0)
    expensive = {q: 2 if q != "stop" else 0 for q in cheap}
    assert best_actions(research_values(history, p, costs=expensive), "net_decision_value") == [
        "stop"
    ]
    with pytest.raises(ValueError, match="cost"):
        research_values(history, p, costs={**cheap, "stop": 0.1})


def test_design_is_deterministic_balanced_and_keeps_confirmation_templates_separate():
    history = tuple(r.public for r in archive(8))
    a, b = choose_design(history, 4), choose_design(history, 4)
    assert a["indices"] == b["indices"]
    assert len(a["probes"]) == 648
    diagnostic, comparator, heldout = (
        a["indices"][n] for n in ("diagnostic", "matched_random", "heldout")
    )
    assert len(diagnostic) == len(comparator) == 24
    assert len(heldout) == 32 and not set(heldout) & set(diagnostic + comparator)
    assert len(set(diagnostic)) == 24
    assert all(
        sum(a["probes"][i].source_id == f"source-{s}" for i in diagnostic) == 4 for s in range(6)
    )
    assert sum(r["anchor"] for r in a["summaries"]) == 12
    assert np.all(np.isfinite(predictions(history, a["probes"])))


def test_complete_design_run_binds_plan_and_predictions_and_exposes_failures(tmp_path):
    directory = tmp_path / "design"
    result = run(directory, seed=20260925, repetitions=4)
    assert result["gates"]["passed"], result["gates"]
    assert result["implementation_sha256"] == fingerprint()
    assert result["controls"]["direction_reversal"]["all_candidates_inadequate"]
    assert (
        result["controls"]["representative_audit_equivalence"][
            "maximum_joint_flat_logit_difference"
        ]
        < 1e-9
    )
    assert not result["participant_collection_ready"]
    assert not result["empirical_predictive_validation"]
    assert result["research_policy_contrasts"]["decision_and_company_information_disagree"] > 0
    for name, digest in result["artifact_sha256"].items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest
    assert (directory / "prediction-lock.json").stat().st_mtime_ns <= (
        directory / "report.json"
    ).stat().st_mtime_ns
    with pytest.raises(ValueError, match="immutable"):
        run(directory, seed=20260925, repetitions=4)
    # Fully deterministic rerun, including model summaries and private-byte commitments.
    run(tmp_path / "repeat", seed=20260925, repetitions=4)
    assert (directory / "report.json").read_bytes() == (
        tmp_path / "repeat/report.json"
    ).read_bytes()
