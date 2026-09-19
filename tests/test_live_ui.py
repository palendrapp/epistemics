import subprocess
from pathlib import Path


def test_browser_conversion_preserves_canonical_answer_contract():
    """Exercise the actual shipped JS conversion functions without a browser dependency."""
    result = subprocess.run(
        [
            "node",
            "--input-type=commonjs",
            "-e",
            r"""
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const source = fs.readFileSync("src/epistemics/live/assets/app.js", "utf8").replace(/init\(\);\s*$/, "");
const context = vm.createContext({document: {querySelector: () => ({})}});
vm.runInContext(source, context);
context.form = {
  elements: {namedItem: name => ({value: context.values[name]}), decision: {value: "hold"}, alternative: {value: ""}},
  querySelectorAll: () => [{value: "d1"}],
};
for (const [value, expected] of [["0",0], ["100",1], ["25",.25], ["0.1",.001]]) {
  context.values = {p: value};
  assert.equal(vm.runInContext('percent(form, "p")', context), expected);
}
for (const value of ["", " ", "NaN", "Infinity", "-1", "101"]) {
  context.values = {p:value};
  assert.throws(() => vm.runInContext('percent(form, "p")', context));
}
context.values = {target_probability: "37.5", q10:"-2", q50:"8", q90:"20", source_beacon:"70", conditional:"60", extract_renewal_estimate_pct:"9.2"};
context.trial = {module:"discovery", payload: {source_probe_ids:["beacon"], conditional_probe:true, extraction_keys:["renewal_estimate_pct"]}};
const answer = JSON.parse(vm.runInContext("JSON.stringify(buildAnswer(form, trial))", context));
assert.deepEqual(answer, {target_probability:.375, growth_quantiles_pct:{p10:-2,p50:8,p90:20}, decision:"hold", evidence_ids:["d1"], source_accuracy:{beacon:.7}, conditional_growth_probability:.6, extracted_values:{renewal_estimate_pct:9.2}, alternative_explanation:null});
context.values.q10 = "21";
assert.throws(() => vm.runInContext("buildAnswer(form, trial)", context));
""",
        ],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
