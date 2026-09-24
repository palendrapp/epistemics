"use strict";
const content = document.getElementById("content");
const error = document.getElementById("error");
const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has("access")) {
  sessionStorage.setItem("narrative2-access", fragment.get("access"));
  history.replaceState(null, "", location.pathname);
}
const token = sessionStorage.getItem("narrative2-access") || "";
const states = {demand_only: "Demand change only (D, no S)", artifact_only: "Reporting artifact only (S, no D)", both: "Both demand change and artifact", neither: "Neither defined event"};
function node(tag, text, parent = content) {
  const el = document.createElement(tag); el.textContent = text; parent.append(el); return el;
}
async function api(path, body) {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: {Authorization: `Bearer ${token}`, "Content-Type": "application/json", "X-Epistemics-Request": "1"},
    ...(body === undefined ? {} : {body: JSON.stringify(body)})
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
function percent(value) {
  if (!/^\d{1,3}$/.test(value) || Number(value) > 100) throw new Error("Enter a whole percentage from 0 to 100 for every question.");
  return Number(value) / 100;
}
function button(label, action, parent = content) {
  const el = node("button", label, parent); el.type = "button";
  el.onclick = async () => {
    el.disabled = true; error.textContent = "";
    try { await action(); await render(); } catch (e) { error.textContent = e.message; }
    finally { el.disabled = false; }
  }; return el;
}
function inputs(form, prefix) {
  for (const [key, text] of Object.entries(states)) {
    const label = node("label", text, form); const input = document.createElement("input");
    Object.assign(input, {name: `${prefix}_${key}`, type: "number", min: "0", max: "100", step: "1", required: true});
    label.append(input);
  }
}
async function render() {
  const state = await api("/api/state"); content.replaceChildren();
  window.scrollTo(0, 0);
  document.getElementById("progress").textContent = `Case ${state.case_number} of ${state.case_count}${state.synthetic ? " · Synthetic preview" : " · Private participation"}`;
  if (state.complete) { node("h2", "All cases are complete"); node("p", "Your answers are saved privately. The evaluator can now prepare the report. Thank you."); return; }
  if (!state.started) {
    node("p", state.protocol.instructions.replace("Report probabilities from 0 to 1 in increments of 0.01 (whole percentages in the browser). Joint probabilities must sum to 1.", "Report whole percentages from 0 to 100. Joint probabilities must sum to 100%."));
    node("p", "Eight fictional company cases, each with four checkpoints, twenty probability judgments and one research choice. You may pause between cases and resume using this private link. Results stay local and private.");
    button("I understand — begin", () => api("/api/begin", {instructions_accepted: true})); return;
  }
  if (state.current.complete) {
    node("h2", "Case complete");
    button("Save this case and continue", () => api("/api/finish", {assignment_id: state.assignment_id})); return;
  }
  const trial = state.current.trial;
  node("h2", `${trial.company} · ${trial.stage}`);
  node("p", trial.demand_event); node("p", trial.artifact_event); node("p", trial.signal_event);
  const evidence = node("section", "");
  node("h3", trial.checkpoint === 1 ? "Company background" : "New evidence", evidence);
  for (const text of trial.new_documents) node("p", text, evidence);
  if (state.history.length) {
    const details = node("details", ""); node("summary", "Earlier evidence and your accepted answers", details);
    for (const row of state.history) {
      node("h3", row.trial.stage, details);
      for (const text of row.trial.new_documents) node("p", text, details);
      for (const [key, value] of Object.entries(row.answer.joint)) node("p", `${states[key]}: ${Math.round(value * 100)}%`, details);
      if (row.answer.signal_if_state) for (const [key, value] of Object.entries(row.answer.signal_if_state)) node("p", `Signal forecast if ${states[key].toLowerCase()}: ${Math.round(value * 100)}%`, details);
      if (row.answer.query) node("p", `Research: ${row.answer.query.replaceAll("_", " ")}`, details);
    }
  }
  const form = node("form", ""); form.onsubmit = e => e.preventDefault();
  node("h3", "Which combination occurred?", form);
  node("p", "Allocate 100% across the four combinations.", form); inputs(form, "joint");
  const total = node("p", "Total: 0% of 100%", form); total.setAttribute("aria-live", "polite");
  form.oninput = () => { total.textContent = `Total: ${Object.keys(states).reduce((sum, k) => sum + Number(form.elements.namedItem(`joint_${k}`).value), 0)}% of 100%`; };
  if (trial.request_signal_forecasts) {
    node("h3", "What would the dashboard show?", form);
    node("p", "For each combination, forecast the chance that signal E will appear. These are four separate conditional forecasts; they do not need to sum to 100%.", form);
    inputs(form, "signal");
  }
  if (trial.request_query) {
    const label = node("label", "Choose one free check to reduce uncertainty about the joint D/S state", form);
    const select = node("select", "", label); select.name = "query"; select.required = true;
    for (const [value, text] of [["", "Choose a check"], ["demand_audit", "Audit real demand (D only)"], ["pipeline_audit", "Audit reporting pipeline (S only)"], ["stop", "Stop — receive no new evidence"]]) {
      const option = node("option", text, select); option.value = value;
    }
  }
  button("Commit these answers", async () => {
    const read = prefix => Object.fromEntries(Object.keys(states).map(k => [k, percent(form.elements.namedItem(`${prefix}_${k}`).value)]));
    const answer = {joint: read("joint")};
    if (Math.abs(Object.values(answer.joint).reduce((a, b) => a + b, 0) - 1) > 1e-8) throw new Error("Your four joint probabilities must total 100%.");
    if (trial.request_signal_forecasts) answer.signal_if_state = read("signal");
    if (trial.request_query) { answer.query = form.elements.namedItem("query").value; if (!answer.query) throw new Error("Choose an audit or stop."); }
    await api("/api/answers", {assignment_id: state.assignment_id, trial_id: trial.trial_id, answer});
  }, form);
}
render().catch(e => { error.textContent = e.message; });
