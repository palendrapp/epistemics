import numpy as np

from epistemics.disposition_tasks import evident_texts, presentation, runner
from epistemics.dispositions import evident
from epistemics.passport import adapter


def _check(rung, valid=True):
    return {"valid": valid, "advice": rung, "recommended_rung": rung}


def test_dose_follows_the_check_and_defaults_to_full():
    assert adapter.dose(_check(1)) == 1 and adapter.dose(_check(2)) == 2
    assert adapter.dose(_check(None)) == adapter.FULL
    assert adapter.dose(_check("rate")) == adapter.FULL
    assert adapter.dose(_check(1, valid=False)) == adapter.FULL
    assert adapter.dose(None) == adapter.FULL


def test_adapter_is_deterministic_bound_and_names_no_case():
    configuration = {"model": "gpt-6-astra", "reasoning_effort": "medium"}
    checks = {"relay": _check(2), "disclosure": _check(None)}
    passport = {"guide_version": "g", "ledger_sha256": "x"}
    one = adapter.generate("astra", configuration, checks, passport)
    two = adapter.generate("astra", configuration, checks, passport)
    assert one == two and one["adapter_sha256"] == two["adapter_sha256"]
    assert one["subject"]["configuration_id"] == adapter.configuration_id(configuration)
    assert [c["rung"] for c in one["components"]] == [2, 3]
    assert adapter.TEXT["relay"][3] not in one["instructions"]
    assert adapter.TEXT["disclosure"][3] in one["instructions"]
    other = adapter.generate("astra", configuration, {"relay": _check(3)}, passport)
    assert other["adapter_sha256"] != one["adapter_sha256"]
    names = evident_texts.COMPANIES + evident_texts.OUTLETS_A + evident_texts.OUTLETS_B
    assert not any(n in one["instructions"] for n in names)


def test_frozen_adapters_deliver_their_instructions():
    standard = presentation.instructions("relay-evident", "alone")
    for arm in ("generic", "adapter-astra", "adapter-sol", "adapter-luna", "adapter-terra"):
        frozen = presentation.adapter(arm)
        assert frozen["schema_version"] == adapter.SCHEMA
        assert presentation.instructions("relay-evident", arm) == (
            standard + "\n\n" + frozen["instructions"]
        )
    assert presentation.adapter("adapter-sol")["components"][1]["rung"] == 2


def test_evident_cases_are_balanced_and_scored_against_the_correct_forecast():
    rng = np.random.default_rng(2)
    for module in evident.MODULES:
        items = evident.design(module)
        assert all((items["type"] == t).sum() == 8 for t in evident.TYPES)
        exact = 1 / (1 + np.exp(-evident.correct(module, items)))
        perfect = evident.session(module, items, np.round(exact, 2))
        assert perfect["error"] < 0.05
        neglect = evident.respond(module, items, {"use": 0.0, "false": 0.0, "tau": 0.0}, rng)
        result = evident.session(module, items, neglect)
        assert result["error_by_type"]["present"] > 1.0 and result["structure_use"] == 0.0
        assert result["error_by_type"]["absent"] < 0.1  # rounding to whole percentages


def test_pilot_preset_gives_every_configuration_four_arms_on_both_modules():
    runs = runner.check_groups(runner.PRESETS["adapter-pilot"])
    assert len(runs) == 32
    for config, other in runner.ADAPTER_MISMATCH.items():
        arms = {r[2] for r in runs if r[0] == config}
        assert arms == {"alone", "generic", f"adapter-{config}", f"adapter-{other}"}


def test_adapter_eval_reads_arms_and_contrasts(monkeypatch):
    from epistemics.ledger import adapter_eval

    rows = []
    for arm, err in (("alone", 1.5), ("generic", 0.6), ("adapter", 0.4), ("mismatched", 0.7)):
        rows.append({"configuration": "sol", "arm": arm,
                     "variant": {"adapter": "adapter-sol", "mismatched": "adapter-astra"}.get(arm, arm),
                     "module": "relay-evident", "error": err, "error_present": err,
                     "error_absent": err / 2, "error_control": 0.1, "structure_use": 0.5,
                     "false_structure": 0.1, "run": arm})  # fmt: skip
    monkeypatch.setattr(adapter_eval, "sessions", lambda roots: rows)
    out = adapter_eval.summary([])["configurations"]["sol"]
    assert abs(out["contrasts"]["M1"]["error"] - 1.1) < 1e-9
    assert abs(out["contrasts"]["M2"]["error_absent"] - 0.1) < 1e-9
    assert out["arms"]["generic"]["extra_instruction_characters"] > 0


def test_implementation_snapshot_carries_the_adapters_and_reproduces_the_fingerprint(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    from epistemics.disposition_tasks.collection import fingerprint
    from epistemics.source_learning.storage import save

    src = Path(runner.__file__).resolve().parents[2]
    files = runner.snapshot_sources(src)
    assert any(p.parent.name == "adapters" and p.suffix == ".json" for p in files)
    snapshot = tmp_path / "src"
    for source in files:
        target = snapshot / source.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        save(target, source.read_bytes())
    actual = subprocess.check_output(
        [sys.executable, "-c",
         "from epistemics.disposition_tasks.collection import fingerprint; print(fingerprint())"],
        cwd=tmp_path, env={**os.environ, "PYTHONPATH": str(snapshot)}, text=True,
    ).strip()  # fmt: skip
    assert actual == fingerprint()


def test_hinted_summary_scores_arms_against_the_reference(monkeypatch):
    from epistemics.ledger import adapter_eval

    rng = np.random.default_rng(4)
    target = rng.normal(0, 1, 24)
    described = np.arange(24) < 20
    rows = []
    for arm, shift in (("alone", 1.5), ("generic", 0.4), ("adapter", 0.3), ("mismatched", 0.9),
                       ("reference", 0.0)):  # fmt: skip
        for k in range(3):
            z = target + shift * described + rng.normal(0, 0.05, 24)
            rows.append({"configuration": "sol", "module": "relay-hinted", "arm": arm,
                         "variant": arm, "run": f"{arm}{k}", "z": z, "described": described,
                         "implied": [0.1, 0.2, 0.5, 0.6 + shift / 5, 0.7]})  # fmt: skip
    monkeypatch.setattr(adapter_eval, "hinted_sessions", lambda roots: rows)
    out = adapter_eval.hinted_summary([])["configurations"]["sol"]
    assert out["arms"]["reference"]["deviation"] < 0.15
    assert abs(out["arms"]["alone"]["deviation"] - 1.5) < 0.1
    assert out["contrasts"]["M1"]["difference"] > 1 and out["contrasts"]["M1"]["p_one_sided"] < 0.06
    assert out["contrasts"]["M3"]["difference"] > 0.4


def test_hinted_preset_has_five_arms_three_sessions_each():
    runs = runner.check_groups(runner.PRESETS["adapter-hinted"])
    assert len(runs) == 120
    for config, other in runner.ADAPTER_MISMATCH.items():
        arms = {r[2] for r in runs if r[0] == config}
        assert arms == {"alone", "generic", f"adapter-{config}", f"adapter-{other}", "reference"}
        assert {r[4] for r in runs if r[0] == config} == {1, 2, 3}
